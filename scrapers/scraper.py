"""
Job scraper: LinkedIn, Indeed, TimesJobs, Freshersworld
All HTTP calls have explicit timeouts — no hanging.
"""
import json
import time
import hashlib
import feedparser
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

CONFIG_FILE = "config.json"
SEEN_FILE = "seen_jobs.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def load_seen():
    if Path(SEEN_FILE).exists():
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def job_id(title: str, company: str) -> str:
    return hashlib.md5(f"{title.lower().strip()}{company.lower().strip()}".encode()).hexdigest()

def fetch_rss(url: str, timeout: int = 10) -> list:
    """Fetch RSS with timeout — returns feedparser entries or empty list."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        return feed.entries
    except Exception as e:
        print(f"  RSS fetch failed ({url[:60]}...): {e}", flush=True)
        return []

def scrape_indeed(keywords: list[str], location: str) -> list[dict]:
    jobs = []
    for kw in keywords:
        url = (
            f"https://in.indeed.com/rss?q={requests.utils.quote(kw)}"
            f"&l={requests.utils.quote(location)}&sort=date"
        )
        for entry in fetch_rss(url)[:15]:
            jobs.append({
                "title": entry.get("title", ""),
                "company": entry.get("source", {}).get("value", "Unknown"),
                "link": entry.get("link", ""),
                "source": "Indeed",
                "keyword": kw,
                "date": entry.get("published", datetime.now().isoformat()),
            })
        time.sleep(1)
    print(f"  Indeed: {len(jobs)} jobs", flush=True)
    return jobs

def scrape_timesjobs(keywords: list[str]) -> list[dict]:
    jobs = []
    for kw in keywords:
        url = f"https://www.timesjobs.com/jobfeed/rss-jobs.html?keyword={requests.utils.quote(kw)}&locationId=0"
        for entry in fetch_rss(url)[:10]:
            jobs.append({
                "title": entry.get("title", ""),
                "company": entry.get("author", "Unknown"),
                "link": entry.get("link", ""),
                "source": "TimesJobs",
                "keyword": kw,
                "date": entry.get("published", datetime.now().isoformat()),
            })
        time.sleep(1)
    print(f"  TimesJobs: {len(jobs)} jobs", flush=True)
    return jobs

def scrape_freshersworld(keywords: list[str]) -> list[dict]:
    jobs = []
    for kw in keywords:
        url = f"https://www.freshersworld.com/jobs/rss?keyword={requests.utils.quote(kw)}&location=India"
        for entry in fetch_rss(url)[:10]:
            jobs.append({
                "title": entry.get("title", ""),
                "company": entry.get("author", "Unknown"),
                "link": entry.get("link", ""),
                "source": "Freshersworld",
                "keyword": kw,
                "date": entry.get("published", datetime.now().isoformat()),
            })
        time.sleep(1)
    print(f"  Freshersworld: {len(jobs)} jobs", flush=True)
    return jobs

def scrape_linkedin(keywords: list[str], location: str) -> list[dict]:
    jobs = []
    for kw in keywords:
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={requests.utils.quote(kw)}"
            f"&location={requests.utils.quote(location)}"
            f"&f_TPR=r86400&start=0"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            for card in soup.find_all("li")[:10]:
                title_el = card.find("h3")
                company_el = card.find("h4")
                link_el = card.find("a")
                if not title_el:
                    continue
                jobs.append({
                    "title": title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "link": link_el["href"].split("?")[0] if link_el and link_el.get("href") else "",
                    "source": "LinkedIn",
                    "keyword": kw,
                    "date": datetime.now().isoformat(),
                })
        except Exception as e:
            print(f"  LinkedIn skipped ({kw}): {e}", flush=True)
        time.sleep(2)
    print(f"  LinkedIn: {len(jobs)} jobs", flush=True)
    return jobs

def run():
    config = load_config()
    seen = load_seen()
    keywords = config["keywords"]
    location = config.get("location", "India")

    all_jobs = []

    print("🔍 Scraping Indeed...", flush=True)
    all_jobs += scrape_indeed(keywords, location)

    print("🔍 Scraping TimesJobs...", flush=True)
    all_jobs += scrape_timesjobs(keywords)

    print("🔍 Scraping Freshersworld...", flush=True)
    all_jobs += scrape_freshersworld(keywords)

    print("🔍 Scraping LinkedIn...", flush=True)
    all_jobs += scrape_linkedin(keywords, location)

    new_jobs = []
    for job in all_jobs:
        jid = job_id(job["title"], job["company"])
        if jid not in seen:
            seen.add(jid)
            new_jobs.append(job)

    save_seen(seen)
    print(f"✅ {len(new_jobs)} new jobs out of {len(all_jobs)} total", flush=True)

    with open("new_jobs.json", "w") as f:
        json.dump(new_jobs, f, indent=2)

    return new_jobs

if __name__ == "__main__":
    run()