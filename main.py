import sys

# force unbuffered output so GitHub Actions shows logs live
sys.stdout.reconfigure(line_buffering=True)

from scrapers.scraper import run as scrape
from scrapers.ai_filter import run as filter_jobs
from scrapers.notifier import run as notify

def main():
    print("=" * 50, flush=True)
    print("🚀 Job Agent starting...", flush=True)
    print("=" * 50, flush=True)

    print("\n── Step 1: Scraping jobs ──", flush=True)
    new_jobs = scrape()

    print("\n── Step 2: AI filtering ──", flush=True)
    filter_jobs()

    print("\n── Step 3: Sending alerts ──", flush=True)
    notify()

    print("\n✅ Pipeline complete!", flush=True)

if __name__ == "__main__":
    main()