"""
NORAY — Scholarship Search

Discover scholarships, fellowships, and grants from multiple sources.
Supports portal-specific searches, web search, and eligibility-based scoring.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field

from noray.config import DATA_DIR


# ─── Data Models ──────────────────────────────────────────────

@dataclass
class Scholarship:
    """A discovered scholarship opportunity."""
    name: str = ""
    provider: str = ""
    country: str = ""
    degree_level: str = ""          # BSc, MSc, PhD, PostDoc
    field_restrictions: list[str] = field(default_factory=list)
    amount: str = ""
    deadline: str = ""
    url: str = ""
    description: str = ""
    eligibility_notes: list[str] = field(default_factory=list)
    fit_score: int = 0              # 0-100
    fit_level: str = ""             # high, medium, low
    eligibility_details: dict = field(default_factory=dict)
    application_materials: list[str] = field(default_factory=list)  # sop, motivation, research_proposal, recommendation
    source: str = ""                # portal name or "web"
    funding_type: str = ""          # fully_funded, partial, tuition_waiver, stipend


@dataclass
class ScholarshipSearchResult:
    """Result of a scholarship search."""
    scholarships: list[Scholarship] = field(default_factory=list)
    total_found: int = 0
    new_count: int = 0
    sources_searched: list[str] = field(default_factory=list)
    search_date: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))


# ─── Known Scholarship Portals ────────────────────────────────

SCHOLARSHIP_PORTALS = {
    "daad": {
        "name": "DAAD",
        "url": "www.daad.de",
        "region": "Germany",
        "degree_levels": ["MSc", "PhD", "PostDoc"],
        "funding": "fully_funded",
        "requires": ["sop", "recommendation"],
    },
    "chevening": {
        "name": "Chevening",
        "url": "www.chevening.org",
        "region": "UK",
        "degree_levels": ["MSc"],
        "funding": "fully_funded",
        "requires": ["sop", "recommendation"],
        "eligible_nationalities": "chevening_eligible",
    },
    "fulbright": {
        "name": "Fulbright",
        "url": "fulbright.org",
        "region": "USA",
        "degree_levels": ["MSc", "PhD"],
        "funding": "fully_funded",
        "requires": ["sop", "recommendation"],
    },
    "erasmus": {
        "name": "Erasmus Mundus",
        "url": "erasmus-plus.ec.europa.eu",
        "region": "EU",
        "degree_levels": ["MSc"],
        "funding": "fully_funded",
        "requires": ["motivation", "recommendation"],
    },
    "commonwealth": {
        "name": "Commonwealth Scholarship",
        "url": "cscuk.fcdo.gov.uk",
        "region": "UK",
        "degree_levels": ["MSc", "PhD"],
        "funding": "fully_funded",
        "requires": ["sop", "recommendation"],
    },
    "gates_cambridge": {
        "name": "Gates Cambridge",
        "url": "www.gatescambridge.org",
        "region": "UK",
        "degree_levels": ["PhD", "PostDoc"],
        "funding": "fully_funded",
        "requires": ["sop", "research_proposal", "recommendation"],
    },
    "rhodes": {
        "name": "Rhodes Scholarship",
        "url": "www.rhodeshouse.ox.ac.uk",
        "region": "UK",
        "degree_levels": ["MSc", "PhD"],
        "funding": "fully_funded",
        "requires": ["sop", "recommendation"],
    },
    "schwarzman": {
        "name": "Schwarzman Scholars",
        "url": "www.schwarzmanscholars.org",
        "region": "China",
        "degree_levels": ["MSc"],
        "funding": "fully_funded",
        "requires": ["sop", "recommendation"],
    },
    "mastercard": {
        "name": "Mastercard Foundation Scholars",
        "url": "mastercardfdn.org",
        "region": "Africa",
        "degree_levels": ["BSc", "MSc"],
        "funding": "fully_funded",
        "requires": ["motivation", "recommendation"],
    },
    "turkiye_burslari": {
        "name": "Türkiye Bursları",
        "url": "turkiyeburslari.gov.tr",
        "region": "Turkey",
        "degree_levels": ["BSc", "MSc", "PhD"],
        "funding": "fully_funded",
        "requires": ["motivation"],
    },
    "japan_mext": {
        "name": "MEXT Scholarship",
        "url": "studyinjapan.go.jp",
        "region": "Japan",
        "degree_levels": ["MSc", "PhD"],
        "funding": "fully_funded",
        "requires": ["sop", "recommendation"],
    },
    "csc_china": {
        "name": "CSC Scholarship",
        "url": "campuschina.org",
        "region": "China",
        "degree_levels": ["MSc", "PhD"],
        "funding": "fully_funded",
        "requires": ["sop", "research_proposal", "recommendation"],
    },
    "stipendium_hungaricum": {
        "name": "Stipendium Hungaricum",
        "url": "stipendiumhungaricum.hu",
        "region": "Hungary",
        "degree_levels": ["BSc", "MSc", "PhD"],
        "funding": "fully_funded",
        "requires": ["motivation", "recommendation"],
    },
}


# ─── Public API ───────────────────────────────────────────────

def search_scholarships(
    profile: dict[str, Any],
    target_degree: str = "",
    target_country: str = "",
    research_area: str = "",
) -> ScholarshipSearchResult:
    """
    Search for scholarships matching the candidate's profile.
    
    Args:
        profile: Career profile dict
        target_degree: Target degree level (MSc, PhD, etc.)
        target_country: Target country for study
        research_area: Research interest area
    
    Returns:
        ScholarshipSearchResult with discovered and scored scholarships
    """
    # Build search queries
    queries = build_scholarship_queries(profile, target_degree, target_country, research_area)

    # Score known portals against profile
    portal_matches = _score_portals(profile, target_degree, target_country)

    return ScholarshipSearchResult(
        scholarships=portal_matches,
        total_found=len(portal_matches),
        new_count=len(portal_matches),
        sources_searched=list(SCHOLARSHIP_PORTALS.keys()),
    )


def build_scholarship_queries(
    profile: dict[str, Any],
    target_degree: str = "",
    target_country: str = "",
    research_area: str = "",
) -> list[dict[str, str]]:
    """
    Build search queries for scholarship discovery.
    Returns list of {query, priority, category} dicts for WebSearch.
    """
    queries = []
    nationality = profile.get("identity", {}).get("location", {}).get("country", "")
    field = ""
    if profile.get("education"):
        field = profile["education"][0].get("field", "")
    skills = profile.get("skills", {}).get("primary", [])

    # Priority 1: Specific portal + degree + country
    if target_degree and target_country:
        queries.append({
            "query": f"{target_degree} scholarship {target_country} {nationality} students 2026 fully funded",
            "priority": "1",
            "category": "targeted",
        })

    # Priority 2: Research area + degree
    if research_area:
        queries.append({
            "query": f"PhD scholarship {research_area} fully funded 2026",
            "priority": "1",
            "category": "research",
        })
        queries.append({
            "query": f"research fellowship {research_area} 2026 international students",
            "priority": "2",
            "category": "research",
        })

    # Priority 3: Nationality-based
    if nationality:
        queries.append({
            "query": f"scholarships for {nationality} students 2026 fully funded",
            "priority": "2",
            "category": "nationality",
        })
        queries.append({
            "query": f"international scholarships {nationality} {target_degree or 'MSc'} 2026",
            "priority": "2",
            "category": "nationality",
        })

    # Priority 4: Field-based
    if field:
        queries.append({
            "query": f"{field} scholarship {target_degree or 'MSc'} 2026 international",
            "priority": "3",
            "category": "field",
        })

    # Priority 5: Specific portals
    for portal_key, portal in SCHOLARSHIP_PORTALS.items():
        if target_degree and target_degree in portal.get("degree_levels", []):
            queries.append({
                "query": f"{portal['name']} scholarship {target_degree} {nationality} 2026",
                "priority": "3",
                "category": f"portal_{portal_key}",
            })

    # Priority 6: Skills-based
    if skills:
        queries.append({
            "query": f"{' '.join(skills[:2])} scholarship {target_degree or 'graduate'} 2026",
            "priority": "4",
            "category": "skills",
        })

    return queries


def get_portal_info(portal_key: str) -> dict[str, Any] | None:
    """Get information about a specific scholarship portal."""
    return SCHOLARSHIP_PORTALS.get(portal_key)


def get_matching_portals(
    profile: dict[str, Any],
    target_degree: str = "",
    target_country: str = "",
) -> list[dict[str, Any]]:
    """
    Get portals that match the candidate's profile and goals.
    Returns list of portal dicts with match info.
    """
    matches = []
    nationality = profile.get("identity", {}).get("location", {}).get("country", "")
    education = profile.get("education", [])

    for key, portal in SCHOLARSHIP_PORTALS.items():
        # Check degree level match
        if target_degree and target_degree not in portal.get("degree_levels", []):
            continue

        # Check region/country match
        if target_country:
            region = portal.get("region", "").lower()
            if target_country.lower() not in region and region not in target_country.lower():
                # Not an exact match, but still include as an option
                pass

        match_info = {
            "key": key,
            "name": portal["name"],
            "url": portal["url"],
            "region": portal["region"],
            "degree_levels": portal.get("degree_levels", []),
            "funding": portal.get("funding", ""),
            "requires": portal.get("requires", []),
            "match_reason": _explain_portal_match(portal, target_degree, target_country, nationality, education),
        }
        matches.append(match_info)

    return matches


# ─── Internal: Portal Scoring ─────────────────────────────────

def _score_portals(
    profile: dict[str, Any],
    target_degree: str,
    target_country: str,
) -> list[Scholarship]:
    """Score known portals against the profile and return Scholarship objects."""
    from noray.scholarship_agent.eligibility_scoring import score_eligibility

    scholarships = []
    nationality = profile.get("identity", {}).get("location", {}).get("country", "")
    education = profile.get("education", [])
    field = education[0].get("field", "") if education else ""
    languages = [l.get("language", "") for l in profile.get("identity", {}).get("languages", [])]

    for key, portal in SCHOLARSHIP_PORTALS.items():
        # Build a scholarship dict for eligibility scoring
        scholarship_data = {
            "name": portal["name"],
            "degree_level": portal.get("degree_levels", [""])[0] if portal.get("degree_levels") else "",
            "field_restrictions": [field] if field else [],
            "required_languages": ["English"],  # Most international scholarships require English
        }

        # Score eligibility
        eligibility = score_eligibility(profile, scholarship_data)

        # Determine fit level
        if eligibility.overall_score >= 70:
            fit_level = "high"
        elif eligibility.overall_score >= 40:
            fit_level = "medium"
        else:
            fit_level = "low"

        # Only include if there's some match
        if target_degree and target_degree not in portal.get("degree_levels", []):
            continue

        scholarship = Scholarship(
            name=portal["name"],
            provider=portal["name"],
            country=portal.get("region", ""),
            degree_level=", ".join(portal.get("degree_levels", [])),
            url=portal.get("url", ""),
            description=f"{portal['name']} scholarship — {portal.get('funding', 'fully funded')} — {portal.get('region', '')}",
            fit_score=eligibility.overall_score,
            fit_level=fit_level,
            eligibility_details={
                "criteria_met": eligibility.criteria_met,
                "criteria_not_met": eligibility.criteria_not_met,
                "criteria_partial": eligibility.criteria_partial,
            },
            application_materials=portal.get("requires", []),
            source=key,
            funding_type=portal.get("funding", "fully_funded"),
            eligibility_notes=eligibility.recommendations,
        )
        scholarships.append(scholarship)

    # Sort by fit score
    scholarships.sort(key=lambda s: s.fit_score, reverse=True)

    return scholarships


def _explain_portal_match(
    portal: dict,
    target_degree: str,
    target_country: str,
    nationality: str,
    education: list[dict],
) -> str:
    """Explain why a portal matches the candidate."""
    reasons = []

    if target_degree and target_degree in portal.get("degree_levels", []):
        reasons.append(f"Offers {target_degree} funding")

    if target_country and target_country.lower() in portal.get("region", "").lower():
        reasons.append(f"Located in target country ({portal['region']})")

    if portal.get("funding") == "fully_funded":
        reasons.append("Fully funded")

    if not reasons:
        reasons.append("Available international scholarship")

    return "; ".join(reasons)


# ─── State Management ─────────────────────────────────────────

SEEN_FILE = DATA_DIR / "seen_scholarships.json"


def load_seen_scholarships() -> dict:
    """Load previously seen scholarships for deduplication."""
    if SEEN_FILE.exists():
        try:
            return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            pass
    return {"seen": {}}


def record_seen_scholarship(scholarship: Scholarship) -> None:
    """Record a scholarship as seen for future deduplication."""
    seen = load_seen_scholarships()
    key = scholarship.url.lower() if scholarship.url else scholarship.name.lower()
    seen["seen"][key] = {
        "name": scholarship.name,
        "provider": scholarship.provider,
        "url": scholarship.url,
        "first_seen": datetime.utcnow().strftime("%Y-%m-%d"),
        "fit": scholarship.fit_level,
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(seen, indent=2, ensure_ascii=False), encoding="utf-8")
