"""
main.py — runs the full pipeline:
  1. Scrape jobs (LinkedIn, Indeed, Naukri)
  2. AI filter (Claude scores each job vs your JD)
  3. Send Telegram alerts
"""
import sys
from scrapers.scraper import run as scrape
from scrapers.ai_filter import run as filter_jobs
from scrapers.notifier import run as notify

def main():
    print("=" * 50)
    print("🚀 Job Agent starting...")
    print("=" * 50)

    print("\n── Step 1: Scraping jobs ──")
    new_jobs = scrape()

    print("\n── Step 2: AI filtering ──")
    filter_jobs()

    print("\n── Step 3: Sending alerts ──")
    notify()

    print("\n✅ Pipeline complete!")

if __name__ == "__main__":
    main()
