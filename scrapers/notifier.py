import json
import os
import requests
from pathlib import Path
from datetime import datetime

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

def send(token: str, method: str, payload: dict):
    url = TELEGRAM_API.format(token=token, method=method)
    resp = requests.post(url, json=payload, timeout=10)
    if not resp.ok:
        print(f"  Telegram error: {resp.text}", flush=True)
    return resp

def format_job_card(job: dict, index: int) -> str:
    score = job.get("score", "?")
    source = job.get("source", "")
    title = job.get("title", "No title")
    company = job.get("company", "Unknown")
    reason = job.get("reason", "")
    keyword = job.get("keyword", "")

    badge = "🔥" if isinstance(score, int) and score >= 9 else "⭐" if isinstance(score, int) and score >= 7 else "📌"

    title_lower = title.lower()
    job_type = "🎓 Internship" if any(x in title_lower for x in ["intern", "internship", "trainee"]) else "💼 Full-time"

    loc_hints = [l.title() for l in ["hyderabad", "bangalore", "chennai", "remote"] if l in title_lower or l in company.lower()]
    location = ", ".join(loc_hints) if loc_hints else "Check listing"

    msg = f"{badge} *{title}*\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🏢 *Company:* {company}\n"
    msg += f"📋 *Type:* {job_type}\n"
    msg += f"📍 *Location:* {location}\n"
    msg += f"💰 *CTC:* Check listing (4 LPA+ filter applied)\n"
    msg += f"🛠 *Matched via:* `{keyword}`\n"
    msg += f"📡 *Source:* {source}\n"
    msg += f"🎯 *AI Score:* {score}/10"
    if reason:
        msg += f" — _{reason}_"
    msg += "\n"
    return msg

def send_job_with_buttons(token: str, chat_id: str, job: dict, index: int):
    text = format_job_card(job, index)
    link = job.get("link", "")
    job_id = f"job_{index}_{abs(hash(job.get('title','')[:20]))}"

    keyboard = {"inline_keyboard": []}
    if link:
        keyboard["inline_keyboard"].append([{"text": "🔗 Apply Now", "url": link}])
    keyboard["inline_keyboard"].append([
        {"text": "✅ Relevant", "callback_data": f"relevant|{job_id}|{job.get('title','')[:30]}"},
        {"text": "❌ Irrelevant", "callback_data": f"irrelevant|{job_id}|{job.get('title','')[:30]}"}
    ])

    send(token, "sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": keyboard
    })

def run():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("⚠️  Telegram credentials missing", flush=True)
        return

    jobs_file = Path("filtered_jobs.json")
    if not jobs_file.exists():
        return

    jobs = json.load(open(jobs_file))
    today = datetime.now().strftime("%d %b %Y")

    if not jobs:
        send(token, "sendMessage", {
            "chat_id": chat_id,
            "text": f"🤖 *Job Agent — {today}*\n\nNo new relevant jobs today. See you tomorrow!",
            "parse_mode": "Markdown"
        })
        return

    send(token, "sendMessage", {
        "chat_id": chat_id,
        "text": (
            f"🤖 *Job Agent Report — {today}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *{len(jobs)} relevant jobs found*\n"
            f"🎯 Min score: 7/10 | 4 LPA+ filter\n"
            f"📍 Hyd • Blr • Chennai • Remote\n\n"
            f"_Tap ✅ Relevant or ❌ Irrelevant to train your filter!_"
        ),
        "parse_mode": "Markdown"
    })

    for i, job in enumerate(jobs[:20], 1):
        send_job_with_buttons(token, chat_id, job, i)

    if len(jobs) > 20:
        send(token, "sendMessage", {
            "chat_id": chat_id,
            "text": f"_...and {len(jobs)-20} more. Raise min\\_score in config.json to reduce._",
            "parse_mode": "Markdown"
        })

    print(f"📨 Sent {min(len(jobs),20)} job cards to Telegram", flush=True)

if __name__ == "__main__":
    run()