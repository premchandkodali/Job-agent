"""
AI filter: uses Claude API to score each job against your JD (0-10).
Filters out anything below the threshold in config.json.
"""
import json
import os
import anthropic
from pathlib import Path

def load_jd() -> str:
    jd_file = Path("my_jd.txt")
    if jd_file.exists():
        return jd_file.read_text()
    return ""

def score_job(client: anthropic.Anthropic, job: dict, jd: str) -> tuple[int, str]:
    """Returns (score 0-10, one-line reason)"""
    prompt = f"""You are a job relevance scorer for a fresher software engineer.

My profile / JD:
{jd}

Job to evaluate:
Title: {job['title']}
Company: {job['company']}
Source: {job['source']}

Score this job from 0 to 10 for relevance to my profile.
- 8-10: Strong match, definitely alert me
- 5-7: Decent match, worth knowing
- 0-4: Not relevant, skip

Respond ONLY as JSON: {{"score": <int>, "reason": "<one sentence>"}}"""

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        data = json.loads(msg.content[0].text.strip())
        return int(data["score"]), data.get("reason", "")
    except Exception as e:
        print(f"  Scoring error: {e}")
        return 5, "Could not score"  # default: keep it

def run():
    config = json.load(open("config.json"))
    threshold = config.get("min_score", 5)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not Path("new_jobs.json").exists():
        print("No new_jobs.json found, skipping filter")
        return []

    jobs = json.load(open("new_jobs.json"))
    if not jobs:
        print("No new jobs to filter")
        json.dump([], open("filtered_jobs.json", "w"))
        return []

    jd = load_jd()
    if not jd:
        print("⚠️  No my_jd.txt found — skipping AI scoring, keeping all jobs")
        json.dump(jobs, open("filtered_jobs.json", "w"))
        return jobs

    if not api_key:
        print("⚠️  No ANTHROPIC_API_KEY — skipping AI scoring, keeping all jobs")
        json.dump(jobs, open("filtered_jobs.json", "w"))
        return jobs

    client = anthropic.Anthropic(api_key=api_key)
    filtered = []

    print(f"🤖 Scoring {len(jobs)} jobs with Claude...")
    for job in jobs:
        score, reason = score_job(client, job, jd)
        job["score"] = score
        job["reason"] = reason
        status = "✅" if score >= threshold else "❌"
        print(f"  {status} [{score}/10] {job['title']} @ {job['company']} — {reason}")
        if score >= threshold:
            filtered.append(job)

    filtered.sort(key=lambda j: j["score"], reverse=True)
    json.dump(filtered, open("filtered_jobs.json", "w"), indent=2)
    print(f"✅ {len(filtered)}/{len(jobs)} jobs passed the filter (min score: {threshold})")
    return filtered

if __name__ == "__main__":
    run()
