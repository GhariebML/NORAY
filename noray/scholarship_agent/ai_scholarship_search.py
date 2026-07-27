"""
NORAY — AI-Powered Scholarship Search Engine

Intent-driven scholarship discovery with AI understanding,
multi-source search, eligibility analysis, and document generation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any

logger = logging.getLogger("noray.scholarship_agent.ai_scholarship_search")

INTENT_EXTRACTION_PROMPT = """You are a scholarship search intent analyzer. Extract structured information from the user's query.

User query: "{query}"

Return ONLY a JSON object (no markdown, no code fences):
{{
  "degree_level": "phd|masters|bachelors|any",
  "field_of_study": "research field or empty",
  "country": "target country or empty",
  "funding_type": "full|partial|tuition|living|any",
  "ielts_required": true|false,
  "deadline_preference": "upcoming|flexible|any",
  "research_area": "specific research interest or empty",
  "university_preference": "university name or empty",
  "expanded_terms": ["DAAD", "Chevening", "Fulbright", "Erasmus", "MEXT"]
}}"""

ELIGIBILITY_PROMPT = """You are a scholarship eligibility analyst. Evaluate this scholarship against the candidate's profile.

SCHOLARSHIP:
Name: {name}
Provider: {provider}
Country: {country}
Degree Level: {degree_level}
Requirements: {requirements}
Funding: {funding}
Deadline: {deadline}
Description: {description}

CANDIDATE PROFILE:
Nationality: {nationality}
Education: {education}
Languages: {languages}
Skills: {skills}

Return ONLY a JSON object (no markdown, no code fences):
{{
  "eligibility_score": 0-100,
  "why_eligible": ["reason1", "reason2"],
  "missing_documents": ["doc1", "doc2"],
  "recommended_timeline": "timeline description",
  "competition_level": "low|medium|high|very_high",
  "acceptance_difficulty": "easy|moderate|difficult|very_difficult",
  "recommendation": "strongly_recommend|consider|unlikely",
  "summary": "1-2 sentence assessment"
}}"""


@dataclass
class ParsedScholarshipIntent:
    degree_level: str = "any"
    field_of_study: str = ""
    country: str = ""
    funding_type: str = "any"
    ielts_required: bool = False
    deadline_preference: str = "any"
    research_area: str = ""
    university_preference: str = ""
    expanded_terms: list[str] = field(default_factory=list)


@dataclass
class ScholarshipEligibility:
    eligibility_score: float = 0.0
    why_eligible: list[str] = field(default_factory=list)
    missing_documents: list[str] = field(default_factory=list)
    recommended_timeline: str = ""
    competition_level: str = "medium"
    acceptance_difficulty: str = "moderate"
    recommendation: str = "consider"
    summary: str = ""


@dataclass
class ScholarshipResult:
    name: str = ""
    provider: str = ""
    country: str = ""
    university: str = ""
    degree_level: str = ""
    funding: str = ""
    deadline: str = ""
    requirements: list[str] = field(default_factory=list)
    language: str = ""
    research_areas: list[str] = field(default_factory=list)
    description: str = ""
    official_url: str = ""
    eligibility: ScholarshipEligibility = field(default_factory=ScholarshipEligibility)


# Known scholarship portals with metadata
KNOWN_SCHOLARSHIPS: list[dict[str, Any]] = [
    {"name": "DAAD Scholarships", "provider": "DAAD", "country": "Germany", "url": "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
     "degrees": ["masters", "phd", "research"], "funding": "Full", "language": "en/de"},
    {"name": "Chevening Scholarships", "provider": "UK Government", "country": "United Kingdom", "url": "https://www.chevening.org/scholarships/",
     "degrees": ["masters"], "funding": "Full", "language": "en"},
    {"name": "Fulbright Program", "provider": "US Department of State", "country": "USA", "url": "https://fulbrightonline.org/",
     "degrees": ["masters", "phd", "research"], "funding": "Full", "language": "en"},
    {"name": "Erasmus Mundus Joint Masters", "provider": "European Commission", "country": "Europe", "url": "https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus_en",
     "degrees": ["masters"], "funding": "Full", "language": "en"},
    {"name": "MEXT Scholarships", "provider": "Japanese Government", "country": "Japan", "url": "https://www.mext.go.jp/en/policy/education/highered/title02/detail02/1373858.htm",
     "degrees": ["masters", "phd", "research"], "funding": "Full", "language": "en/ja"},
    {"name": "Commonwealth Scholarships", "provider": "Commonwealth Scholarship Commission", "country": "United Kingdom", "url": "https://cscuk.fcdo.gov.uk/",
     "degrees": ["masters", "phd"], "funding": "Full", "language": "en"},
    {"name": "Gates Cambridge Scholarships", "provider": "Gates Cambridge Trust", "country": "United Kingdom", "url": "https://www.gatescambridge.org/",
     "degrees": ["masters", "phd"], "funding": "Full", "language": "en"},
    {"name": "KAUST Fellowship", "provider": "KAUST", "country": "Saudi Arabia", "url": "https://www.kaust.edu.sa/study/fellowship",
     "degrees": ["masters", "phd"], "funding": "Full", "language": "en"},
    {"name": "ETH Zurich Scholarships", "provider": "ETH Zurich", "country": "Switzerland", "url": "https://ethz.ch/en/studies/financial/scholarships.html",
     "degrees": ["masters", "phd"], "funding": "Partial", "language": "en/de"},
    {"name": "Oxford Scholarships", "provider": "University of Oxford", "country": "United Kingdom", "url": "https://www.ox.ac.uk/admissions/graduate/fees-and-funding/fees-funding-and-scholarship-search",
     "degrees": ["masters", "phd"], "funding": "Partial", "language": "en"},
    {"name": "Cambridge Trust", "provider": "Cambridge University", "country": "United Kingdom", "url": "https://www.cambridgetrust.org/",
     "degrees": ["masters", "phd"], "funding": "Partial", "language": "en"},
    {"name": "MIT Scholarships", "provider": "MIT", "country": "USA", "url": "https://mitadmissions.org/afford/",
     "degrees": ["bachelors", "masters", "phd"], "funding": "Full", "language": "en"},
    {"name": "Rhodes Scholarships", "provider": "Rhodes Trust", "country": "United Kingdom", "url": "https://www.rhodeshouse.ox.ac.uk/scholarships/",
     "degrees": ["masters", "phd"], "funding": "Full", "language": "en"},
    {"name": "Rotary Foundation Global Grants", "provider": "Rotary International", "country": "Global", "url": "https://www.rotary.org/en/our-programs/global-grants",
     "degrees": ["masters", "phd"], "funding": "Partial", "language": "en"},
    {"name": "Humboldt Research Fellowship", "provider": "Alexander von Humboldt Foundation", "country": "Germany", "url": "https://www.humboldt-foundation.de/en/apply/sponsorship-programmes/humboldt-research-fellowship",
     "degrees": ["phd", "research"], "funding": "Full", "language": "en"},
    {"name": "Marie Curie Fellowships", "provider": "European Commission", "country": "Europe", "url": "https://ec.europa.eu/research/mariecurieactions/",
     "degrees": ["phd", "research"], "funding": "Full", "language": "en"},
    {"name": "Scholarships.com", "provider": "Scholarships.com", "country": "USA", "url": "https://www.scholarships.com/",
     "degrees": ["bachelors", "masters"], "funding": "Partial", "language": "en"},
    {"name": "FindAPhD", "provider": "FindAPhD", "country": "Global", "url": "https://www.findaphd.com/",
     "degrees": ["phd"], "funding": "Partial", "language": "en"},
    {"name": "FindAMasters", "provider": "FindAMasters", "country": "Global", "url": "https://www.findamasters.com/",
     "degrees": ["masters"], "funding": "Partial", "language": "en"},
]


def _filter_known_scholarships(intent: ParsedScholarshipIntent) -> list[dict[str, Any]]:
    """Filter the known scholarship database based on parsed intent."""
    matched = []
    for sch in KNOWN_SCHOLARSHIPS:
        score = 0
        reasons = []

        # Degree match
        if intent.degree_level != "any":
            if intent.degree_level in sch["degrees"]:
                score += 25
                reasons.append("degree_match")
            else:
                continue

        # Country match
        if intent.country:
            if intent.country.lower() in sch["country"].lower():
                score += 25
                reasons.append("country_match")

        # Research area match (partial)
        if intent.research_area and sch["name"]:
            score += 10
            reasons.append("general_match")

        # Field of study (liberal match)
        if intent.field_of_study:
            score += 10
            reasons.append("field_match")

        matched.append({**sch, "_score": score, "_reasons": reasons})

    matched.sort(key=lambda s: s["_score"], reverse=True)
    return matched


async def parse_scholarship_intent(
    query: str,
    profile: dict[str, Any] | None = None,
) -> ParsedScholarshipIntent:
    """Extract structured intent from a natural language scholarship query."""
    from noray.llm.smart_router import smart_router
    from noray.llm.providers.base_provider import LLMConfig, LLMMessage

    messages = [
        LLMMessage(role="system", content="You extract structured scholarship search intent. Return only valid JSON."),
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
        logger.info(f"Scholarship intent extraction in {elapsed:.2f}s: {query[:50]}")

        raw = json.loads(result.content.strip())
        return ParsedScholarshipIntent(
            degree_level=raw.get("degree_level", "any"),
            field_of_study=raw.get("field_of_study", ""),
            country=raw.get("country", ""),
            funding_type=raw.get("funding_type", "any"),
            ielts_required=raw.get("ielts_required", False),
            deadline_preference=raw.get("deadline_preference", "any"),
            research_area=raw.get("research_area", ""),
            university_preference=raw.get("university_preference", ""),
            expanded_terms=raw.get("expanded_terms", ["DAAD", "Chevening", "Fulbright"]),
        )

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse scholarship intent: {e}")
        return ParsedScholarshipIntent(degree_level="any", expanded_terms=["DAAD", "Chevening", "Fulbright"])
    except Exception as e:
        logger.error(f"Scholarship intent extraction failed: {e}")
        return ParsedScholarshipIntent(degree_level="any", expanded_terms=["DAAD", "Chevening", "Fulbright"])


async def analyze_eligibility(
    scholarship: dict[str, Any],
    profile: dict[str, Any],
) -> ScholarshipEligibility:
    """Run AI-based eligibility analysis for a scholarship."""
    from noray.llm.smart_router import smart_router
    from noray.llm.providers.base_provider import LLMConfig, LLMMessage

    education = profile.get("education", [])
    identity = profile.get("identity", {})
    skills_data = profile.get("skills", {})

    prompt = ELIGIBILITY_PROMPT.format(
        name=scholarship.get("name", ""),
        provider=scholarship.get("provider", ""),
        country=scholarship.get("country", ""),
        degree_level=", ".join(scholarship.get("degrees", [])),
        requirements=scholarship.get("requirements", "See official URL"),
        funding=scholarship.get("funding", ""),
        deadline=scholarship.get("deadline", "Varies"),
        description=scholarship.get("description", f"{scholarship.get('name')} offered by {scholarship.get('provider')} in {scholarship.get('country')}"),
        nationality=identity.get("nationality", identity.get("location", {}).get("country", "International")),
        education=json.dumps([{"degree": e.get("degree"), "field": e.get("field"), "institution": e.get("institution")} for e in education[:3]]),
        languages=identity.get("languages", "English"),
        skills=", ".join(skills_data.get("primary", []) + skills_data.get("secondary", [])),
    )

    messages = [
        LLMMessage(role="system", content="You are a scholarship eligibility analyst. Return only valid JSON."),
        LLMMessage(role="user", content=prompt),
    ]

    config = LLMConfig(model="", temperature=0.2, max_tokens=600, system_prompt="")

    try:
        start = time.time()
        result = await smart_router.generate_with_fallback(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            config=config,
            query=f"Eligibility for {scholarship.get('name')}",
        )
        elapsed = time.time() - start
        logger.info(f"Eligibility analysis in {elapsed:.2f}s for {scholarship.get('name')}")

        raw = json.loads(result.content.strip())
        return ScholarshipEligibility(
            eligibility_score=float(raw.get("eligibility_score", 0)),
            why_eligible=raw.get("why_eligible", []),
            missing_documents=raw.get("missing_documents", []),
            recommended_timeline=raw.get("recommended_timeline", ""),
            competition_level=raw.get("competition_level", "medium"),
            acceptance_difficulty=raw.get("acceptance_difficulty", "moderate"),
            recommendation=raw.get("recommendation", "consider"),
            summary=raw.get("summary", ""),
        )

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse eligibility: {e}")
        return ScholarshipEligibility(eligibility_score=50, summary="Analysis unavailable")
    except Exception as e:
        logger.error(f"Eligibility analysis failed: {e}")
        return ScholarshipEligibility(eligibility_score=50, summary="Analysis unavailable")


def _convert_to_results(
    matched: list[dict[str, Any]],
    intent: ParsedScholarshipIntent,
) -> list[ScholarshipResult]:
    """Convert matched scholarships to result objects."""
    results = []
    for sch in matched:
        results.append(ScholarshipResult(
            name=sch.get("name", ""),
            provider=sch.get("provider", ""),
            country=sch.get("country", ""),
            degree_level=", ".join(sch.get("degrees", [])),
            funding=sch.get("funding", ""),
            official_url=sch.get("url", ""),
        ))
    return results


async def full_ai_scholarship_search(
    query: str,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    End-to-end AI-powered scholarship search.
    1. Parse intent from natural language
    2. Match against known scholarships
    3. AI-score eligibility for each
    4. Return ranked results with analysis
    """
    from noray.shared.profile_store import load_profile

    if profile is None:
        profile = load_profile()
        if hasattr(profile, "model_dump"):
            profile = profile.model_dump(mode="json")

    total_start = time.time()

    parsed = await parse_scholarship_intent(query, profile)
    matched = _filter_known_scholarships(parsed)
    results = _convert_to_results(matched, parsed)

    # Score eligibility in parallel
    semaphore = asyncio.Semaphore(3)

    async def _analyze(sch: dict, result: ScholarshipResult) -> ScholarshipResult:
        async with semaphore:
            result.eligibility = await analyze_eligibility(sch, profile)
            return result

    tasks = []
    for sch, result in zip(matched, results):
        tasks.append(_analyze(sch, result))

    scored = []
    for coro in asyncio.as_completed(tasks):
        try:
            scored.append(await coro)
        except Exception as e:
            logger.error(f"Batch eligibility error: {e}")

    scored.sort(key=lambda s: s.eligibility.eligibility_score, reverse=True)

    total_elapsed = time.time() - total_start
    logger.info(f"Full scholarship search: {len(scored)} results in {total_elapsed:.1f}s")

    return {
        "query": query,
        "parsed_intent": asdict(parsed),
        "total_found": len(scored),
        "scholarships": [
            {
                "name": s.name,
                "provider": s.provider,
                "country": s.country,
                "university": s.university,
                "degree_level": s.degree_level,
                "funding": s.funding,
                "deadline": s.deadline,
                "requirements": s.requirements,
                "language": s.language,
                "research_areas": s.research_areas,
                "description": s.description,
                "official_url": s.official_url,
                "eligibility": asdict(s.eligibility),
            }
            for s in scored
        ],
        "search_time_seconds": round(total_elapsed, 1),
    }
