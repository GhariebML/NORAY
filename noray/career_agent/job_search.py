"""
NORAY — Job Search

Multi-portal job discovery with deduplication and fit scoring.
Wraps existing Bun CLI tools and adds web search fallback for non-Danish markets.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass, field

from noray.config import JOB_SCRAPER_DIR, SEARCH_LOOKBACK_DAYS, MAX_SEARCH_RESULTS, JOB_TRACKER_PATH


# ─── Data Models ──────────────────────────────────────────────

@dataclass
class JobPosting:
    """A discovered job posting."""
    title: str = ""
    company: str = ""
    location: str = ""
    url: str = ""
    description: str = ""
    posted_date: str = ""
    deadline: str = ""
    source: str = ""       # jobindex, jobnet, linkedin, google, etc.
    language: str = "en"   # en, da, etc.
    fit_score: int = 0     # 0-100
    fit_level: str = ""    # high, medium, low
    match_reasons: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)


@dataclass
class SearchResult:
    """Result of a job search operation."""
    jobs: list[JobPosting] = field(default_factory=list)
    total_found: int = 0
    new_count: int = 0
    query_used: str = ""
    sources_searched: list[str] = field(default_factory=list)
    search_date: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))


# ─── Public API ───────────────────────────────────────────────

# ─── Public API ───────────────────────────────────────────────

async def search_jobs(
    profile: dict[str, Any],
    focus_area: str = "",
    broad: bool = False,
    max_results: int = MAX_SEARCH_RESULTS,
) -> SearchResult:
    """
    Search multiple job portals for positions matching the profile.
    
    Args:
        profile: Career profile dict (from career_profile.json)
        focus_area: Optional focus (e.g., "data science", "ML engineer")
        broad: If True, run all search categories
        max_results: Maximum number of results to return
    
    Returns:
        SearchResult with discovered and scored jobs
    """
    import asyncio
    import logging
    import time
    from noray.career_agent.providers import provider_registry

    logger = logging.getLogger("noray.career_agent.job_search")
    start_time = time.time()

    # Extract profile data for queries
    target_roles = profile.get("goals", {}).get("target_roles", [])
    primary_skills = profile.get("skills", {}).get("primary", [])
    location = profile.get("identity", {}).get("location", {})
    city = location.get("city", "")
    country = location.get("country", "")
    location_str = f"{city} {country}".strip()

    # Determine query term
    search_term = focus_area
    if not search_term and target_roles:
        search_term = target_roles[0]
    if not search_term:
        search_term = "Software Engineer"

    # Build queries
    queries = _build_queries(target_roles, primary_skills, [], location, focus_area, broad)
    query_used = search_term

    # Load state for deduplication
    seen_jobs = _load_seen_jobs()
    tracker_companies = _load_tracker_companies()

    # Get active/configured providers
    active_providers = provider_registry.get_active_providers()
    provider_names = [p.name for p in active_providers]
    logger.info(f"Starting job search for query '{search_term}' with active providers: {provider_names}")

    # Warn if no providers are active
    if not active_providers:
        logger.warning("No job search providers are currently configured (check API credentials). Only public fallbacks or no results will be available.")

    # Execute searches concurrently
    tasks = []
    for provider in active_providers:
        tasks.append(asyncio.create_task(provider.search(search_term, location=location_str, limit=max_results)))

    # Wait for all providers to complete (timeout after 12.0 seconds)
    all_jobs: list[JobPosting] = []
    if tasks:
        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=12.0)
            for idx, res in enumerate(results):
                provider_name = active_providers[idx].name
                if isinstance(res, Exception):
                    logger.error(f"Provider '{provider_name}' failed with error: {res}", exc_info=True)
                elif isinstance(res, list):
                    logger.info(f"Provider '{provider_name}' returned {len(res)} jobs.")
                    all_jobs.extend(res)
        except asyncio.TimeoutError:
            logger.error("Job search providers timed out after 12 seconds.")
            # Cancel running tasks
            for task in tasks:
                if not task.done():
                    task.cancel()

    # Deduplicate against seen and tracker
    new_jobs = _deduplicate(all_jobs, seen_jobs, tracker_companies)
    logger.info(f"Found {len(all_jobs)} raw jobs, {len(new_jobs)} new jobs after deduplication.")

    # Score fit against profile
    for job in new_jobs:
        _score_job_fit(job, profile)

    # Sort by fit score
    new_jobs.sort(key=lambda j: j.fit_score, reverse=True)

    # Limit results
    new_jobs = new_jobs[:max_results]

    elapsed = time.time() - start_time
    logger.info(f"Job search pipeline completed in {elapsed:.2f} seconds. Returning {len(new_jobs)} jobs.")

    return SearchResult(
        jobs=new_jobs,
        total_found=len(all_jobs),
        new_count=len(new_jobs),
        query_used=query_used,
        sources_searched=provider_names,
    )


def build_search_queries(
    profile: dict[str, Any],
    focus_area: str = "",
    broad: bool = False,
) -> list[dict[str, str]]:
    """
    Build search queries from profile data.
    Returns list of {query, portal, priority} dicts.
    
    This is used by the Claude agent to execute WebSearch calls.
    """
    target_roles = profile.get("goals", {}).get("target_roles", [])
    primary_skills = profile.get("skills", {}).get("primary", [])
    domain = profile.get("skills", {}).get("domain", [])
    location = profile.get("identity", {}).get("location", {})

    return _build_queries(target_roles, primary_skills, domain, location, focus_area, broad)


def record_seen_job(job: JobPosting, status: str = "new") -> None:
    """Record a job as seen for future deduplication."""
    seen = _load_seen_jobs()
    key = _job_key(job)
    seen["seen"][key] = {
        "title": job.title,
        "company": job.company,
        "url": job.url,
        "first_seen": datetime.utcnow().strftime("%Y-%m-%d"),
        "fit": job.fit_level,
        "status": status,
    }
    _save_seen_jobs(seen)


def record_application(job: JobPosting) -> None:
    """Add a job to the application tracker."""
    _append_tracker_row(job)


def score_job_fit(job_text: str, profile: dict[str, Any]) -> tuple[int, str, list[str], list[str]]:
    """
    Score a job posting against the profile.
    
    Returns:
        (score, level, match_reasons, missing_skills)
    """
    # Extract requirements from job text
    required_skills = _extract_skills_from_text(job_text)
    profile_skills = _extract_profile_skills(profile)

    # Calculate match
    matched = []
    missing = []
    for skill in required_skills:
        if _skill_in_profile(skill, profile_skills):
            matched.append(skill)
        else:
            missing.append(skill)

    # Score
    total = len(required_skills) if required_skills else 1
    match_rate = len(matched) / total

    if match_rate >= 0.7:
        score = 80 + int(match_rate * 20)
        level = "high"
    elif match_rate >= 0.4:
        score = 50 + int(match_rate * 30)
        level = "medium"
    else:
        score = int(match_rate * 50)
        level = "low"

    # Build match reasons
    reasons = []
    if matched:
        reasons.append(f"Skills match: {', '.join(matched[:5])}")
    if profile.get("goals", {}).get("target_roles"):
        for role in profile["goals"]["target_roles"]:
            if role.lower() in job_text.lower():
                reasons.append(f"Target role found: {role}")
                score = min(100, score + 5)
                break

    return score, level, reasons, missing


# ─── Query Building ───────────────────────────────────────────

def _build_queries(
    roles: list[str],
    skills: list[str],
    domain: list[str],
    location: dict,
    focus: str,
    broad: bool,
) -> list[dict[str, str]]:
    """Build prioritized search queries from profile data."""
    queries = []
    city = location.get("city", "")
    country = location.get("country", "")
    loc_str = f"{city} {country}".strip()

    # Priority 1: Focus area or top target roles
    if focus:
        queries.append({
            "query": f"{focus} jobs {loc_str}".strip(),
            "priority": "1",
            "category": "focus",
        })
        queries.append({
            "query": f"{focus} site:linkedin.com/jobs {loc_str}".strip(),
            "priority": "1",
            "category": "focus_linkedin",
        })
    else:
        for role in roles[:3]:
            queries.append({
                "query": f"{role} jobs {loc_str}".strip(),
                "priority": "1",
                "category": "target_role",
            })
            queries.append({
                "query": f"{role} site:linkedin.com/jobs {loc_str}".strip(),
                "priority": "1",
                "category": "target_role_linkedin",
            })

    # Priority 2: Skill-based queries
    if skills:
        skill_str = " ".join(skills[:3])
        queries.append({
            "query": f"{skill_str} jobs {loc_str}".strip(),
            "priority": "2",
            "category": "skills",
        })

    # Priority 3: Domain-based queries
    if domain:
        for d in domain[:2]:
            queries.append({
                "query": f"{d} jobs {loc_str}".strip(),
                "priority": "3",
                "category": "domain",
            })

    # Priority 4: Broad queries (only if broad=True)
    if broad:
        for role in roles[3:]:
            queries.append({
                "query": f"{role} {loc_str}".strip(),
                "priority": "4",
                "category": "broad",
            })

        # Adjacent roles
        if roles:
            queries.append({
                "query": f"senior {roles[0]} {loc_str}".strip(),
                "priority": "4",
                "category": "adjacent",
            })

    return queries


# ─── Fit Scoring ──────────────────────────────────────────────

def _score_job_fit(job: JobPosting, profile: dict[str, Any]) -> None:
    """Score a job posting's fit against the profile. Mutates the job in-place."""
    text = f"{job.title} {job.description}".lower()
    score, level, reasons, missing = score_job_fit(text, profile)
    job.fit_score = score
    job.fit_level = level
    job.match_reasons = reasons
    job.missing_skills = missing


def _extract_skills_from_text(text: str) -> list[str]:
    """Extract skill keywords from a job posting text."""
    # Common technical skills to look for
    tech_skills = [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "r", "matlab", "scala", "sql", "nosql", "html", "css",
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "scikit-learn", "keras", "pandas", "numpy",
        "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
        "git", "ci/cd", "jenkins", "github actions",
        "fastapi", "flask", "django", "react", "vue", "angular",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "spark", "hadoop", "airflow", "dbt",
        "data science", "data engineering", "data analysis",
        "agile", "scrum", "project management",
    ]

    text_lower = text.lower()
    found = []
    for skill in tech_skills:
        if skill in text_lower:
            found.append(skill)

    return found


def _extract_profile_skills(profile: dict[str, Any]) -> set[str]:
    """Extract all skills from the profile as a normalized set."""
    skills = set()
    skill_data = profile.get("skills", {})
    for category in ["primary", "secondary", "domain", "tools"]:
        for skill in skill_data.get(category, []):
            skills.add(skill.lower().strip())
    return skills


def _skill_in_profile(skill: str, profile_skills: set[str]) -> bool:
    """Check if a skill is present in the profile (fuzzy match)."""
    skill_lower = skill.lower().strip()
    # For very short skills (1-2 chars), use word boundary match to avoid
    # false positives like 'r' matching 'restaurant'
    if len(skill_lower) <= 2:
        for ps in profile_skills:
            if ps == skill_lower:
                return True
            # Check as whole word in multi-word skills
            if re.search(r'\b' + re.escape(skill_lower) + r'\b', ps):
                return True
        return False
    for ps in profile_skills:
        if skill_lower in ps or ps in skill_lower:
            return True
    return False


# ─── State Management ─────────────────────────────────────────

def _load_seen_jobs() -> dict:
    """Load previously seen jobs for deduplication."""
    seen_file = JOB_SCRAPER_DIR / "seen_jobs.json"
    if seen_file.exists():
        try:
            return json.loads(seen_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            pass
    return {"seen": {}}


def _save_seen_jobs(seen: dict) -> None:
    """Save seen jobs state."""
    JOB_SCRAPER_DIR.mkdir(parents=True, exist_ok=True)
    seen_file = JOB_SCRAPER_DIR / "seen_jobs.json"
    seen_file.write_text(json.dumps(seen, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_tracker_companies() -> set[str]:
    """Load company+role combos from the application tracker."""
    combos = set()
    if JOB_TRACKER_PATH.exists():
        try:
            content = JOB_TRACKER_PATH.read_text(encoding="utf-8")
            for line in content.strip().split("\n")[1:]:  # Skip header
                parts = line.split(",")
                if len(parts) >= 4:
                    company = parts[1].strip().lower()
                    role = parts[3].strip().lower()
                    if company and role:
                        combos.add(f"{company}:{role}")
        except Exception:
            pass
    return combos


def _append_tracker_row(job: JobPosting) -> None:
    """Append a job application to the CSV tracker."""
    header_needed = not JOB_TRACKER_PATH.exists() or JOB_TRACKER_PATH.stat().st_size < 10
    with open(JOB_TRACKER_PATH, "a", encoding="utf-8") as f:
        if header_needed:
            f.write("date,company,sector,role,role_type,channel,status,contact_person,fit_rating,notes,cv_file,cover_letter_file,source\n")
        date = datetime.utcnow().strftime("%Y-%m-%d")
        f.write(f"{date},{job.company},,{job.title},,web,discovered,,{job.fit_score},,{job.source}\n")


# ─── Deduplication ────────────────────────────────────────────

def _job_key(job: JobPosting) -> str:
    """Generate a deduplication key for a job."""
    if job.url:
        return job.url.lower()
    return f"{job.company.lower()}:{job.title.lower()}"


def _deduplicate(
    jobs: list[JobPosting],
    seen: dict,
    tracker: set[str],
) -> list[JobPosting]:
    """Remove already-seen or already-tracked jobs."""
    new_jobs = []
    for job in jobs:
        key = _job_key(job)
        tracker_key = f"{job.company.lower()}:{job.title.lower()}"

        if key in seen.get("seen", {}):
            continue
        if tracker_key in tracker:
            continue

        new_jobs.append(job)
    return new_jobs


# ─── Bun CLI Integration ─────────────────────────────────────

def run_bun_cli_search(
    cli_name: str,
    query: str,
    location: str = "",
    max_results: int = 20,
) -> list[JobPosting]:
    """
    Run a Bun CLI tool for Danish job portal search.
    
    Args:
        cli_name: CLI tool name (jobbank, jobdanmark, jobindex, jobnet)
        query: Search query string
        location: Location filter
        max_results: Max results to return
    
    Returns:
        List of JobPosting objects
    """
    import subprocess

    cli_map = {
        "jobbank": ".agents/skills/jobbank-search/cli",
        "jobdanmark": ".agents/skills/jobdanmark-search/cli",
        "jobindex": ".agents/skills/jobindex-search/cli",
        "jobnet": ".agents/skills/jobnet-search/cli",
    }

    cli_dir = cli_map.get(cli_name)
    if not cli_dir:
        return []

    cli_path = Path(cli_dir)
    if not (cli_path / "node_modules").exists():
        return []  # CLI not installed

    try:
        cmd = ["bun", "run", str(cli_path / "src" / "cli.ts"), query]
        if location:
            cmd.extend(["--location", location])
        cmd.extend(["--limit", str(max_results)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(cli_path),
        )

        if result.returncode != 0:
            return []

        # Parse CLI output (JSON)
        try:
            data = json.loads(result.stdout)
            jobs = []
            for item in data if isinstance(data, list) else data.get("results", []):
                jobs.append(JobPosting(
                    title=item.get("title", ""),
                    company=item.get("company", ""),
                    location=item.get("location", ""),
                    url=item.get("url", ""),
                    description=item.get("description", ""),
                    source=cli_name,
                ))
            return jobs
        except json.JSONDecodeError:
            return []

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def search_danish_portals(
    queries: list[str],
    location: str = "",
) -> list[JobPosting]:
    """
    Search all available Danish job portals.
    
    Args:
        queries: Search query strings
        location: Location filter
    
    Returns:
        List of JobPosting objects from all portals
    """
    all_jobs: list[JobPosting] = []
    portals = ["jobbank", "jobdanmark", "jobindex", "jobnet"]

    for portal in portals:
        for query in queries[:2]:  # Top 2 queries per portal
            jobs = run_bun_cli_search(portal, query, location)
            all_jobs.extend(jobs)

    return all_jobs
