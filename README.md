# 🤖 Job Agent — Daily Job Alerts via Telegram

Runs every morning at 8 AM IST on GitHub Actions. Scrapes LinkedIn, Indeed, and Naukri,
scores each job with Claude AI against your profile, and sends only relevant ones to Telegram.

---

## ⚡ Setup (15 minutes)

### Step 1 — Fork / push this repo to GitHub
Create a new repo on GitHub and push this folder to it.

### Step 2 — Create your Telegram bot
1. Open Telegram, search for **@BotFather**
2. Send `/newbot`, follow the prompts
3. Copy the **Bot Token** (looks like `123456789:ABCdef...`)
4. Send any message to your new bot
5. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
6. Find `"chat":{"id":...}` — that's your **Chat ID**

### Step 3 — Add GitHub Secrets
Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your bot token from Step 2 |
| `TELEGRAM_CHAT_ID` | Your chat ID from Step 2 |
| `ANTHROPIC_API_KEY` | Get free at console.anthropic.com |

### Step 4 — Personalise your profile
Edit **`my_jd.txt`** with your actual skills, education, and preferences.
Edit **`config.json`** to change keywords and location.

### Step 5 — Run manually to test
Go to **Actions tab → Daily Job Agent → Run workflow**
Check your Telegram — you should get a message within ~2 minutes!

---

## 📁 File guide

| File | What to edit |
|---|---|
| `config.json` | Keywords, location, min score threshold |
| `my_jd.txt` | Your skills and what you're looking for |
| `.github/workflows/daily_job_scan.yml` | Change the cron time if needed |

---

## 🕐 Change alert timing
The default is **8:00 AM IST**. To change it, edit the cron line in the workflow:
```
- cron: "30 2 * * *"   # 2:30 UTC = 8:00 AM IST
```
Use https://crontab.guru to calculate UTC times.

---

## 💡 Tips
- Set `"min_score": 7` in config.json if you're getting too many alerts
- Set `"min_score": 4` if you want more results
- You can run the workflow manually any time from the Actions tab
- Check the **Artifacts** in each run to see full job lists (including filtered-out ones)
