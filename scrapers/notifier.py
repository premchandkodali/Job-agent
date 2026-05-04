"""
Telegram notifier: sends filtered jobs as rich messages to your Telegram chat.
"""
import json
import os
import requests
from pathlib import Path
from datetime import datetime

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

def send_message(token: str, chat_id: str, text: str):
    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=10)
    if not resp.ok:
        print(f"  Telegram error: {resp.text}")

def format_job(job: dict, index: int) -> str:
    score = job.get("score", "?")
    reason = job.get("reason", "")
    source = job.get("source", "")
    title = job.get("title", "No title")
    company = job.get("company", "Unknown")
    link = job.get("link", "")

    # score emoji
    if isinstance(score, int):
        if score >= 8:
            badge = "🔥"
        elif score >= 6:
            badge = "⭐"
        else:
            badge = "📌"
    else:
        badge = "📌"

    msg = f"{badge} *{title}*\n"
    msg += f"🏢 {company}  |  📡 {source}\n"
    if score != "?":
        msg += f"🎯 Match score: *{score}/10*"
        if reason:
            msg += f" — _{reason}_"
        msg += "\n"
    if link:
        msg += f"🔗 [Apply here]({link})\n"
    return msg

def run():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("⚠️  TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping notifications")
        return

    jobs_file = Path("filtered_jobs.json")
    if not jobs_file.exists():
        print("No filtered_jobs.json found")
        return

    jobs = json.load(open(jobs_file))
    if not jobs:
        # send a "no new jobs" summary so you know it ran
        today = datetime.now().strftime("%d %b %Y")
        send_message(token, chat_id, f"🤖 *Job Agent Report — {today}*\n\nNo new relevant jobs found today. I'll check again tomorrow!")
        print("No new jobs — sent empty report")
        return

    today = datetime.now().strftime("%d %b %Y")
    header = f"🤖 *Job Agent Report — {today}*\n_{len(jobs)} new relevant job(s) found!_\n\n"
    send_message(token, chat_id, header)

    # send jobs in batches of 5 to avoid message length limits
    for i, job in enumerate(jobs[:20], 1):  # cap at 20 per day
        msg = format_job(job, i)
        send_message(token, chat_id, msg)

    if len(jobs) > 20:
        send_message(token, chat_id, f"_...and {len(jobs)-20} more. Update min\\_score in config.json to filter further._")

    print(f"📨 Sent {min(len(jobs), 20)} job alerts to Telegram")

if __name__ == "__main__":
    run()
