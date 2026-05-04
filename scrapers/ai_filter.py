"""
AI filter: uses Groq (free, 14400 req/day) to score jobs against Premchand's profile.
Model: Llama 3.1 8B
"""
import json
import os
from pathlib import Path
from typing import Optional
from groq import Groq


def load_jd() -> str:
    jd_file = Path("my_jd.txt")
    if jd_file.exists():
        return jd_file.read_text()
    return ""


def score_job(client: Groq, job: dict, jd: str, feedback: Optional[dict] = None) -> tuple[int, str]:
    feedback = feedback or {}
    relevant_titles = feedback.get("relevant", [])
    irrelevant_titles = feedback.get("irrelevant", [])

    prompt = f"""You are a job relevance scorer for a 2026 fresher software engineer in India.

Candidate profile:
{jd}

Past positive signals:
{chr(10).join(f'- {title}' for title in relevant_titles) if relevant_titles else 'None'}

Past negative signals:
{chr(10).join(f'- {title}' for title in irrelevant_titles) if irrelevant_titles else 'None'}

Job to evaluate:
Title: {job['title']}
Company: {job['company']}
Source: {job['source']}

Scoring rules:
- Score 8-10: Strong match — tech role (full-stack/backend/SaaS/AI), fresher/junior/intern level, location matches (Hyderabad/Bangalore/Chennai/Remote), likely 4+ LPA
- Score 5-7: Decent match — tech role but location mismatch OR slightly senior OR frontend only
- Score 0-4: Not relevant — non-tech, sales, HR, medical, legal, senior (3+ years), unpaid, hardware

Penalize heavily for: Senior/Lead/Manager/Director/VP titles, non-tech domains, 3+ years experience, locations outside India with no remote option.

Boost for: Node.js, React, Python, Flask, FastAPI, MongoDB, AWS, Docker, GenAI, Fresher/Junior/Intern/2026 batch, Hyderabad/Bangalore/Chennai/Remote, SaaS/AI roles.

Reply ONLY as JSON: {{"score": <int 0-10>, "reason": "<one sentence max 15 words>"}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1
        )
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return int(data["score"]), data.get("reason", "")
    except Exception as e:
        print(f"  Scoring error: {e}", flush=True)
        return 5, "Could not score"


def run(feedback: Optional[dict] = None):
    config = json.load(open("config.json"))
    threshold = config.get("min_score", 7)
    api_key = os.environ.get("GROQ_API_KEY", "")

    if not Path("new_jobs.json").exists():
        print("No new_jobs.json found, skipping filter", flush=True)
        return []

    jobs = json.load(open("new_jobs.json"))
    if not jobs:
        print("No new jobs to filter", flush=True)
        json.dump([], open("filtered_jobs.json", "w"))
        return []

    jd = load_jd()
    if not jd:
        print("Warning: No my_jd.txt — keeping all jobs", flush=True)
        json.dump(jobs, open("filtered_jobs.json", "w"))
        return jobs

    if not api_key:
        print("Warning: No GROQ_API_KEY — keeping all jobs unfiltered", flush=True)
        json.dump(jobs, open("filtered_jobs.json", "w"))
        return jobs

    client = Groq(api_key=api_key)
    filtered = []

    print(f"Scoring {len(jobs)} jobs with Groq (Llama 3.1)...", flush=True)
    for job in jobs:
        score, reason = score_job(client, job, jd, feedback)
        job["score"] = score
        job["reason"] = reason
        status = "PASS" if score >= threshold else "SKIP"
        print(f"  {status} [{score}/10] {job['title']} @ {job['company']} - {reason}", flush=True)
        if score >= threshold:
            filtered.append(job)

    filtered.sort(key=lambda j: j["score"], reverse=True)
    json.dump(filtered, open("filtered_jobs.json", "w"), indent=2)
    print(f"Result: {len(filtered)}/{len(jobs)} jobs passed (min score: {threshold})", flush=True)
    return filtered


if __name__ == "__main__":
    run()