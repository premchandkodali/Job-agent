import sys
sys.stdout.reconfigure(line_buffering=True)

from scrapers.scraper import run as scrape
from scrapers.ai_filter import run as filter_jobs
from scrapers.notifier import run as notify
from scrapers.feedback_reader import run as read_feedback

def main():
    print("=" * 50, flush=True)
    print("🚀 Job Agent starting...", flush=True)
    print("=" * 50, flush=True)

    print("\n── Step 0: Reading your feedback ──", flush=True)
    feedback = read_feedback()

    print("\n── Step 1: Scraping jobs ──", flush=True)
    scrape()

    print("\n── Step 2: AI filtering ──", flush=True)
    filter_jobs(feedback)

    print("\n── Step 3: Sending alerts ──", flush=True)
    notify()

    print("\n✅ Pipeline complete!", flush=True)

if __name__ == "__main__":
    main()