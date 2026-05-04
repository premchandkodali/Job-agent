import os
import csv
import requests
from datetime import datetime
from pathlib import Path

def run():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("No token — skipping feedback", flush=True)
        return {}

    resp = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates",
        params={"timeout": 5, "allowed_updates": ["callback_query"]},
        timeout=10
    )
    if not resp.ok:
        print(f"Telegram getUpdates failed", flush=True)
        return {}

    updates = resp.json().get("result", [])
    if not updates:
        print("No feedback clicks found", flush=True)
        return {}

    feedback = []
    last_update_id = None

    for update in updates:
        cb = update.get("callback_query", {})
        if not cb:
            continue
        data = cb.get("data", "")
        if "|" not in data:
            continue
        parts = data.split("|")
        if len(parts) < 3:
            continue
        verdict, job_id, title = parts[0], parts[1], parts[2]
        if verdict not in ("relevant", "irrelevant"):
            continue

        feedback.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": title,
            "verdict": verdict,
            "job_id": job_id,
            "timestamp": datetime.now().isoformat()
        })
        last_update_id = update["update_id"]

        requests.post(
            f"https://api.telegram.org/bot{token}/answerCallbackQuery",
            json={"callback_query_id": cb["id"], "text": f"Saved as {verdict}!"},
            timeout=5
        )

    if not feedback:
        print("No valid feedback found", flush=True)
        return {}

    # save to feedback.csv
    csv_file = Path("feedback.csv")
    file_exists = csv_file.exists()
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date","title","verdict","job_id","timestamp"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(feedback)

    # mark as read
    if last_update_id:
        requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={"offset": last_update_id + 1, "timeout": 1},
            timeout=5
        )

    print(f"✅ Saved {len(feedback)} feedback entries to feedback.csv", flush=True)
    return {
        "relevant": [f["title"].lower() for f in feedback if f["verdict"] == "relevant"],
        "irrelevant": [f["title"].lower() for f in feedback if f["verdict"] == "irrelevant"]
    }

if __name__ == "__main__":
    run()