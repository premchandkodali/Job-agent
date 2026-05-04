"""
Job scraper: LinkedIn, RemoteOK, Jobicy
All have open APIs that work on CI servers.
"""
import json
import time
import hashlib
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

def scrape_remoteok(keywords: list[str]) -> list[dict]:
    """RemoteOK public API — no auth, no blocking."""
    jobs = []
    try:
        resp = requests.get(
            "https://remoteok.com/api",
            headers={**HEADERS, "Accept": "application/json"},
            timeout=15
        )
        data = resp.json()
        for item in data[1:]:  # first item is metadata
            title = item.get("position", "")
            company = item.get("company", "Unknown")
            tags = " ".join(item.get("tags", []))
            text = f"{title} {tags}".lower()
            if any(kw.split()[0].lower() in text for kw in keywords):
                jobs.append({
                    "title": title,
                    "company": company,
                    "link": item.get("url", ""),
                    "source": "RemoteOK",
                    "keyword": "remote",
                    "date": item.get("date", datetime.now().isoformat()),
                })
    except Exception as e:
        print(f"  RemoteOK error: {e}", flush=True)
    print(f"  RemoteOK: {len(jobs)} jobs", flush=True)
    return jobs

def scrape_jobicy(keywords: list[str]) -> list[dict]:
    """Jobicy public API — free, no auth needed."""
    jobs = []
    for kw in keywords[:3]:  # limit to avoid rate limit
        try:
            resp = requests.get(
                f"https://jobicy.com/api/v2/remote-jobs?count=20&keyword={requests.utils.quote(kw)}",
                headers=HEADERS,
                timeout=15
            )
            data = resp.json()
            for item in data.get("jobs", []):
                jobs.append({
                    "title": item.get("jobTitle", ""),
                    "company": item.get("companyName", "Unknown"),
                    "link": item.get("url", ""),
                    "source": "Jobicy",
                    "keyword": kw,
                    "date": item.get("pubDate", datetime.now().isoformat()),
                })
        except Exception as e:
            print(f"  Jobicy error ({kw}): {e}", flush=True)
        time.sleep(2)
    print(f"  Jobicy: {len(jobs)} jobs", flush=True)
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

    print("🔍 Scraping RemoteOK...", flush=True)
    all_jobs += scrape_remoteok(keywords)

    print("🔍 Scraping Jobicy...", flush=True)
    all_jobs += scrape_jobicy(keywords)

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