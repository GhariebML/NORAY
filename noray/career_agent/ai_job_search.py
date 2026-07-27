"""
NORAY — AI-Powered Job Search Engine

Intent-driven multi-source job discovery with AI extraction,
query expansion, cross-provider aggregation, and profile-aware AI scoring.
Every request flows through the SmartRouter, never calls providers directly.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("noray.career_agent.ai_job_search")

INTENT_EXTRACTION_PROMPT = """You are a job search intent analyzer. Extract structured information from the user's job search query.

User query: "{query}"

Return ONLY a JSON object with these fields (no markdown, no code fences):
{{
  "role": "normalized job title",
  "skills": ["skill1", "skill2"],
  "experience_level": "entry|mid|senior|lead|any",
  "country": "country or empty string",
  "remote": true|false,
  "salary_range": "e.g. $80k-$120k or empty string",
  "company_preference": "company name or empty string",
  "employment_type": "full-time|part-time|contract|internship|any",
  "expanded_queries": ["role1", "role2", "role3", "role4", "role5"]
}}"""

AI_SCORING_PROMPT = """You are an AI job fit analyzer. Score this job against the user's profile.

JOB:
Title: {title}
Company: {company}
Location: {location}
Description: {description}

PROFILE SKILLS: {profile_skills}
TARGET ROLES: {target_roles}
EXPERIENCE: {experience}

Return ONLY a JSON object (no markdown, no code fences):
{{
  "overall_match": 0-100,
  "skill_match": 0-100,
  "role_alignment": 0-100,
  "ats_estimate": 0-100,
  "strengths": ["strength1", "strength2"],
  "gaps": ["gap1", "gap2"],
  "missing_skills": ["skill1", "skill2"],
  "recommendation": "strong apply|consider|weak|skip",
  "summary": "1-sentence explanation"
}}"""


@dataclass
class ParsedIntent:
    role: str = ""
    skills: list[str] = field(default_factory=list)
    experience_level: str = "any"
    country: str = ""
    remote: bool = False
    salary_range: str = ""
    company_preference: str = ""
    employment_type: str = "any"
    expanded_queries: list[str] = field(default_factory=list)


@dataclass
class AIJobScore:
    overall_match: float = 0.0
    skill_match: float = 0.0
    role_alignment: float = 0.0
    ats_estimate: float = 0.0
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    recommendation: str = "consider"
    summary: str = ""


@dataclass
class AIJobResult:
    company: str = ""
    role: str = ""
    country: str = ""
    remote: bool = False
    salary: str = ""
    required_skills: list[str] = field(default_factory=list)
    experience: str = ""
    description: str = ""
    apply_url: str = ""
    source: str = ""
    score: AIJobScore = field(default_factory=AIJobScore)


async def parse_job_intent(
    query: str,
    profile: dict[str, Any] | None = None,
) -> ParsedIntent:
    """Extract structured intent from a natural language job search query using AI."""
    from noray.llm.smart_router import smart_router
    from noray.llm.providers.base_provider import LLMConfig, LLMMessage

    messages = [
        LLMMessage(role="system", content="You extract structured job search intent. Return only valid JSON."),
        LLMMessage(role="user", content=INTENT_EXTRACTION_PROMPT.format(query=query)),
    ]

    config = LLMConfig(model="", temperature=0.1, max_tokens=800, system_prompt="")

    try:
        start = time.time()
        result = await smart_router.generate_with_fallback(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            config=config,
            query=query,
        )
        elapsed = time.time() - start
        logger.info(f"Intent extraction completed in {elapsed:.2f}s for query: {query[:50]}")

        raw = json.loads(result.content.strip())
        intent = ParsedIntent(
            role=raw.get("role", ""),
            skills=raw.get("skills", []),
            experience_level=raw.get("experience_level", "any"),
            country=raw.get("country", ""),
            remote=raw.get("remote", False),
            salary_range=raw.get("salary_range", ""),
            company_preference=raw.get("company_preference", ""),
            employment_type=raw.get("employment_type", "any"),
            expanded_queries=raw.get("expanded_queries", []),
        )

        # Ensure we have at least some queries
        if not intent.expanded_queries and intent.role:
            intent.expanded_queries = [intent.role]

        return intent

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse job intent: {e}")
        return ParsedIntent(role=query, expanded_queries=[query])
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        return ParsedIntent(role=query, expanded_queries=[query])


async def search_ai_jobs(
    parsed_intent: ParsedIntent,
    max_results: int = 50,
) -> tuple[list[AIJobResult], list[str]]:
    """Search multiple job providers using expanded queries and return normalized results."""
    from noray.career_agent.providers import provider_registry
    from noray.career_agent.job_search import JobPosting, _deduplicate, _load_seen_jobs, _load_tracker_companies

    queries = parsed_intent.expanded_queries[:5]
    location_str = parsed_intent.country
    if parsed_intent.remote:
        location_str = "Remote"

    active_providers = provider_registry.get_active_providers()
    provider_names = [p.name for p in active_providers]
    logger.info(f"AI job search: {len(queries)} queries x {len(active_providers)} providers")

    all_jobs: list[JobPosting] = []

    for query in queries:
        tasks = []
        for provider in active_providers:
            tasks.append(asyncio.create_task(
                provider.search(query, location=location_str, limit=max_results)
            ))

        if tasks:
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=15.0,
                )
                for res in results:
                    if isinstance(res, list):
                        all_jobs.extend(res)
            except asyncio.TimeoutError:
                for task in tasks:
                    if not task.done():
                        task.cancel()

    # Deduplicate
    seen = _load_seen_jobs()
    tracker = _load_tracker_companies()
    new_jobs = _deduplicate(all_jobs, seen, tracker)

    # Convert to AIJobResult with empty scores (scored separately)
    results = []
    for job in new_jobs[:max_results]:
        results.append(AIJobResult(
            company=job.company,
            role=job.title,
            country=job.location,
            remote=("remote" in job.location.lower()) or parsed_intent.remote,
            salary="",
            required_skills=[],
            experience=parsed_intent.experience_level,
            description=job.description,
            apply_url=job.url,
            source=job.source,
        ))

    return results, provider_names


async def score_job_ai(
    job: AIJobResult,
    profile: dict[str, Any],
) -> AIJobScore:
    """Run AI-based job fit scoring against the user profile."""
    from noray.llm.smart_router import smart_router
    from noray.llm.providers.base_provider import LLMConfig, LLMMessage

    profile_skills = []
    for cat in ["primary", "secondary", "domain", "tools"]:
        profile_skills.extend(profile.get("skills", {}).get(cat, []))

    target_roles = profile.get("goals", {}).get("target_roles", [])
    experience = profile.get("experience", [])

    prompt = AI_SCORING_PROMPT.format(
        title=job.role,
        company=job.company,
        location=job.country,
        description=job.description[:1500],
        profile_skills=", ".join(set(profile_skills)),
        target_roles=", ".join(target_roles),
        experience=json.dumps([{"title": e.get("title"), "company": e.get("company")} for e in experience[:3]]),
    )

    messages = [
        LLMMessage(role="system", content="You are a job fit analyzer. Return only valid JSON."),
        LLMMessage(role="user", content=prompt),
    ]

    config = LLMConfig(model="", temperature=0.2, max_tokens=600, system_prompt="")

    try:
        start = time.time()
        result = await smart_router.generate_with_fallback(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            config=config,
            query=f"Score job fit for {job.role} at {job.company}",
        )
        elapsed = time.time() - start
        logger.info(f"AI scoring completed in {elapsed:.2f}s for {job.role} at {job.company}")

        raw = json.loads(result.content.strip())
        return AIJobScore(
            overall_match=float(raw.get("overall_match", 0)),
            skill_match=float(raw.get("skill_match", 0)),
            role_alignment=float(raw.get("role_alignment", 0)),
            ats_estimate=float(raw.get("ats_estimate", 0)),
            strengths=raw.get("strengths", []),
            gaps=raw.get("gaps", []),
            missing_skills=raw.get("missing_skills", []),
            recommendation=raw.get("recommendation", "consider"),
            summary=raw.get("summary", ""),
        )

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse AI score for {job.role}: {e}")
        return AIJobScore(overall_match=50, summary="Scoring unavailable")
    except Exception as e:
        logger.error(f"AI scoring failed for {job.role}: {e}")
        return AIJobScore(overall_match=50, summary="Scoring unavailable")


async def batch_score_jobs(
    jobs: list[AIJobResult],
    profile: dict[str, Any],
    max_concurrent: int = 5,
) -> list[AIJobResult]:
    """Score all jobs in parallel batches."""
    scored: list[AIJobResult] = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _score_one(job: AIJobResult) -> AIJobResult:
        async with semaphore:
            job.score = await score_job_ai(job, profile)
            return job

    tasks = [_score_one(job) for job in jobs]
    for coro in asyncio.as_completed(tasks):
        try:
            scored.append(await coro)
        except Exception as e:
            logger.error(f"Batch scoring error: {e}")

    scored.sort(key=lambda j: j.score.overall_match, reverse=True)
    return scored


async def full_ai_job_search(
    query: str,
    profile: dict[str, Any] | None = None,
    max_results: int = 30,
) -> dict[str, Any]:
    """
    End-to-end AI-powered job search.
    1. Parse intent from natural language query
    2. Expand search terms
    3. Fetch from all providers
    4. AI-score each result
    5. Return ranked results
    """
    from noray.shared.profile_store import load_profile

    if profile is None:
        profile = load_profile()
        if hasattr(profile, "model_dump"):
            profile = profile.model_dump(mode="json")

    total_start = time.time()

    parsed = await parse_job_intent(query, profile)
    raw_jobs, sources = await search_ai_jobs(parsed, max_results=max_results)
    scored_jobs = await batch_score_jobs(raw_jobs, profile)

    total_elapsed = time.time() - total_start
    logger.info(f"Full AI job search completed: {len(scored_jobs)} jobs in {total_elapsed:.1f}s")

    return {
        "query": query,
        "parsed_intent": asdict(parsed),
        "sources_searched": sources,
        "total_found": len(scored_jobs),
        "jobs": [
            {
                "company": j.company,
                "role": j.role,
                "country": j.country,
                "remote": j.remote,
                "salary": j.salary,
                "required_skills": j.required_skills,
                "experience": j.experience,
                "description": j.description[:500],
                "apply_url": j.apply_url,
                "source": j.source,
                "score": asdict(j.score),
            }
            for j in scored_jobs
        ],
        "search_time_seconds": round(total_elapsed, 1),
    }
