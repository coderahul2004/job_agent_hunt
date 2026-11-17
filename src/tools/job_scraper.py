"""Search and rank genuine remote job listings from Remotive.
Supports common entry-level roles including Data Analyst, Python Developer,
AI Engineer, MERN Stack Developer and PHP Developer. Unknown roles also work
through a generic keyword fallback.

Note: this searches Remotive's remote listings only. It does not guarantee
that vacancies exist for a given role or location.
"""
import json
import re
from html import unescape
from typing import Any
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from src.config import JOB_SEARCH_LIMIT, MAX_DESCRIPTION_CHARS
API_URL = "https://remotive.com/api/remote-jobs"
CATEGORIES = ("software-dev", "data", "devops")
ROLE_KEYWORDS = {
    "data analyst": [
        "data analyst",
        "junior data analyst",
        "entry level data analyst",
        "business intelligence analyst",
        "bi analyst",
        "reporting analyst",
        "sql analyst",
        "data analytics",
    ],
    "python developer": [
        "python developer",
        "junior python developer",
        "entry level python developer",
        "python engineer",
        "python programmer",
        "django developer",
        "fastapi developer",
        "backend developer",
    ],
    "ai engineer": [
        "ai engineer",
        "junior ai engineer",
        "machine learning engineer",
        "generative ai engineer",
        "llm engineer",
        "artificial intelligence engineer",
    ],
    "mern stack": [
        "mern stack developer",
        "mern developer",
        "full stack developer",
        "react developer",
        "node.js developer",
        "node developer",
        "javascript developer",
    ],
    "mern stack developer": [
        "mern stack developer",
        "mern developer",
        "full stack developer",
        "react developer",
        "node.js developer",
        "node developer",
        "javascript developer",
    ],
    "php developer": [
        "php developer",
        "junior php developer",
        "entry level php developer",
        "laravel developer",
        "symfony developer",
        "wordpress developer",
        "backend developer",
    ],
}
GENERIC_WORDS = {
    "developer", "engineer", "junior", "senior", "entry", "level",
    "remote", "and", "the", "for", "with",
}
def normalize_role(role: str) -> str:
    """Normalize spaces and case while preserving technology punctuation."""
    return re.sub(r"\s+", " ", (role or "").strip().lower())
def clean_html(value: str) -> str:
    """Convert an HTML job description into readable plain text."""
    value = re.sub(
        r"<(script|style).*?>.*?</\1>",
        " ",
        value or "",
        flags=re.IGNORECASE | re.DOTALL,
    )
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()
def get_keywords(role: str) -> list[str]:
    """Return related title phrases for known roles or a safe fallback."""
    normalized = normalize_role(role)
    phrases = ROLE_KEYWORDS.get(normalized)
    if phrases is None:
        tokens = [
            token for token in re.findall(r"[a-z0-9+#.]+", normalized)
            if token not in GENERIC_WORDS
        ]
        phrases = [normalized]
        if tokens:
            phrases.append(" ".join(tokens))
    return list(dict.fromkeys(
        phrase for phrase in [normalized, *phrases] if phrase
    ))
def _phrase_in_text(phrase: str, text: str) -> bool:
    """Match a phrase without treating punctuation as a word boundary issue."""
    phrase = normalize_role(phrase)
    text = normalize_role(text)
    if not phrase or not text:
        return False
    return phrase in text
def score_job(title: str, description: str, keywords: list[str]) -> int:
    """Score a job, weighting title relevance more than description mentions."""
    title_text = normalize_role(title)
    description_text = normalize_role(description)
    score = 0
    matched_title_phrases = set()
    for phrase in keywords:
        if _phrase_in_text(phrase, title_text):
            score += 12
            matched_title_phrases.add(phrase)
        elif _phrase_in_text(phrase, description_text):
            score += 2
    requested_tokens = {
        token for token in re.findall(r"[a-z0-9+#.]+", normalize_role(keywords[0]))
        if token not in GENERIC_WORDS
    }
    title_tokens = set(re.findall(r"[a-z0-9+#.]+", title_text))
    overlap = requested_tokens & title_tokens
    if overlap and not matched_title_phrases:
        score += 5 * len(overlap)
    return score
def fetch_remotive_jobs(
    role: str,
    limit: int = JOB_SEARCH_LIMIT,
) -> list[dict[str, Any]]:
    """Fetch listings, rank them against the requested role and return top jobs."""
    normalized = normalize_role(role)
    if not normalized:
        raise ValueError("Target job role cannot be empty.")
    if limit < 1:
        raise ValueError("Job search limit must be at least 1.")

    keywords = get_keywords(normalized)
    all_jobs: dict[str, dict[str, Any]] = {}
    successful_requests = 0
    errors: list[str] = []
    for category in CATEGORIES:
        try:
            response = requests.get(
                API_URL,
                params={"category": category, "limit": 100},
                headers={"User-Agent": "JobHuntAgentSquad/1.0"},
                timeout=25,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Unexpected API response format.")
            successful_requests += 1
            for item in payload.get("jobs", []):
                if not isinstance(item, dict):
                    continue
                url = item.get("url")
                title = item.get("title")
                company = item.get("company_name")
                if url and title and company:
                    all_jobs[url] = item
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"{category}: {exc}")
    if successful_requests == 0:
        raise RuntimeError(
            "All Remotive requests failed. " + "; ".join(errors)
        )
    ranked_jobs = []
    for url, item in all_jobs.items():
        title = str(item.get("title", "")).strip()
        description = clean_html(str(item.get("description", "")))
        company = str(item.get("company_name", "")).strip()
        relevance = score_job(title, description, keywords)
        if relevance < 2:
            continue
        ranked_jobs.append({
            "title": title,
            "company": company,
            "url": url,
            "description": description[:MAX_DESCRIPTION_CHARS],
            "search_score": relevance,
        })
    ranked_jobs.sort(
        key=lambda job: (job["search_score"], job["title"].lower()),
        reverse=True,
    )
    return ranked_jobs[:limit]
class JobSearchInput(BaseModel):
    role: str = Field(
        ...,
        min_length=2,
        description="Target job role, for example MERN Stack Developer",
    )
class JobSearchTool(BaseTool):
    name: str = "Remote Job Search"
    description: str = (
        "Search genuine remote job listings from Remotive for a target role. "
        "Supports common developer and analyst roles, plus generic role names. "
        "Returns JSON with search status, job count and real job listings. "
        "Never invent job listings."
    )
    args_schema: type[BaseModel] = JobSearchInput
    def _run(self, role: str) -> str:
        try:
            jobs = fetch_remotive_jobs(role)
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            return json.dumps({
                "status": "api_error",
                "search_role": role,
                "error": str(exc),
                "jobs": [],
            }, ensure_ascii=False)
        if not jobs:
            return json.dumps({
                "status": "no_jobs_found",
                "search_role": role,
                "searched_keywords": get_keywords(role),
                "jobs_retrieved": 0,
                "jobs": [],
                "message": (
                    "The API responded, but no relevant listings were found "
                    "in the categories searched."
                ),
            }, ensure_ascii=False)
        return json.dumps({
            "status": "success",
            "search_role": role,
            "searched_keywords": get_keywords(role),
            "jobs_retrieved": len(jobs),
            "jobs": jobs,
        }, ensure_ascii=False)