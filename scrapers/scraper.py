"""
Job scraper: LinkedIn, Indeed, Naukri
Reads config from config.json, saves new jobs to seen_jobs.json
"""
import json
import os
import time
import hashlib
import feedparser
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

CONFIG_FILE = "config.json"
SEEN_FILE = "seen_jobs.json"

# ── helpers ──────────────────────────────────────────────────────────────────

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

# ── Indeed scraper (RSS) ──────────────────────────────────────────────────────

def scrape_indeed(keywords: list[str], location: str) -> list[dict]:
    jobs = []
    for kw in keywords:
        url = (
            f"https://in.indeed.com/rss?q={requests.utils.quote(kw)}"
            f"&l={requests.utils.quote(location)}&sort=date"
        )
        feed = feedparser.parse(url)
        for entry in feed.entries[:15]:
            jobs.append({
                "title": entry.get("title", ""),
                "company": entry.get("source", {}).get("value", "Unknown"),
                "link": entry.get("link", ""),
                "source": "Indeed",
                "keyword": kw,
                "date": entry.get("published", datetime.now().isoformat()),
            })
        time.sleep(1)
    return jobs

# ── Naukri scraper (RSS) ──────────────────────────────────────────────────────

def scrape_naukri(keywords: list[str]) -> list[dict]:
    jobs = []
    for kw in keywords:
        url = f"https://www.naukri.com/rss/jobs/it-jobs-in-india-0.xml"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                title = entry.get("title", "")
                # filter by keyword relevance
                if not any(k.lower() in title.lower() for k in keywords):
                    continue
                jobs.append({
                    "title": title,
                    "company": entry.get("author", "Unknown"),
                    "link": entry.get("link", ""),
                    "source": "Naukri",
                    "keyword": kw,
                    "date": entry.get("published", datetime.now().isoformat()),
                })
        except Exception as e:
            print(f"Naukri error: {e}")
        time.sleep(1)
    return jobs

# ── LinkedIn scraper (public search, no login needed) ─────────────────────────

def scrape_linkedin(keywords: list[str], location: str) -> list[dict]:
    jobs = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        )
    }
    for kw in keywords:
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={requests.utils.quote(kw)}"
            f"&location={requests.utils.quote(location)}"
            f"&f_TPR=r86400"   # last 24 hours
            f"&start=0"
        )
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("li")
            for card in cards[:10]:
                title_el = card.find("h3")
                company_el = card.find("h4")
                link_el = card.find("a")
                if not title_el:
                    continue
                jobs.append({
                    "title": title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "Unknown",
                    "link": link_el["href"].split("?")[0] if link_el else "",
                    "source": "LinkedIn",
                    "keyword": kw,
                    "date": datetime.now().isoformat(),
                })
        except Exception as e:
            print(f"LinkedIn error for '{kw}': {e}")
        time.sleep(2)
    return jobs

# ── main ─────────────────────────────────────────────────────────────────────

def run():
    config = load_config()
    seen = load_seen()
    keywords = config["keywords"]
    location = config.get("location", "India")

    all_jobs = []
    print(f"🔍 Scraping Indeed...")
    all_jobs += scrape_indeed(keywords, location)
    print(f"🔍 Scraping Naukri...")
    all_jobs += scrape_naukri(keywords)
    print(f"🔍 Scraping LinkedIn...")
    all_jobs += scrape_linkedin(keywords, location)

    new_jobs = []
    for job in all_jobs:
        jid = job_id(job["title"], job["company"])
        if jid not in seen:
            seen.add(jid)
            new_jobs.append(job)

    save_seen(seen)
    print(f"✅ Found {len(new_jobs)} new jobs out of {len(all_jobs)} total")

    # write new jobs for next step to read
    with open("new_jobs.json", "w") as f:
        json.dump(new_jobs, f, indent=2)

    return new_jobs

if __name__ == "__main__":
    run()
