"""
AI filter: uses Groq (free, 14400 req/day) to score jobs against your JD.
Model: Llama 3.1 8B — accurate, fast, free forever.
"""
import json
import os
from pathlib import Path
from groq import Groq


def load_jd() -> str:
    jd_file = Path("my_jd.txt")
    if jd_file.exists():
        return jd_file.read_text()
    return ""


def score_job(client: Groq, job: dict, jd: str) -> tuple[int, str]:
    prompt = f"""You are a job relevance scorer for a fresher software engineer.

My profile:
{jd}

Job to evaluate:
Title: {job['title']}
Company: {job['company']}
Source: {job['source']}

Score this job 0-10 for relevance to my profile.
- 8-10: Strong match, alert me
- 5-7: Decent match
- 0-4: Not relevant, skip

Reply ONLY as JSON: {{"score": <int>, "reason": "<one sentence>"}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        text = response.choices[0].message.content.strip()
        # strip markdown fences if present
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return int(data["score"]), data.get("reason", "")
    except Exception as e:
        print(f"  Scoring error: {e}")
        return 5, "Could not score"


def run():
    config = json.load(open("config.json"))
    threshold = config.get("min_score", 5)
    api_key = os.environ.get("GROQ_API_KEY", "")

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
        print("⚠️  No my_jd.txt — keeping all jobs")
        json.dump(jobs, open("filtered_jobs.json", "w"))
        return jobs

    if not api_key:
        print("⚠️  No GROQ_API_KEY — keeping all jobs unfiltered")
        json.dump(jobs, open("filtered_jobs.json", "w"))
        return jobs

    client = Groq(api_key=api_key)
    filtered = []

    print(f"🤖 Scoring {len(jobs)} jobs with Groq (Llama 3.1)...")
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
    print(f"✅ {len(filtered)}/{len(jobs)} jobs passed (min score: {threshold})")
    return filtered


if __name__ == "__main__":
    run()