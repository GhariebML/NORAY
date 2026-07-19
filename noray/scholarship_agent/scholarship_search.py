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
    portal: str = ""                # Alias for provider
    country: str = ""
    degree_level: str = ""          # BSc, MSc, PhD, PostDoc
    field_restrictions: list[str] = field(default_factory=list)
    amount: str = ""
    deadline: str = ""
    url: str = ""
    description: str = ""
    eligibility_notes: list[str] = field(default_factory=list)
    match_reasons: list[str] = field(default_factory=list) # Alias for eligibility_notes
    fit_score: int = 0              # 0-100
    eligibility_score: int = 0      # Alias for fit_score
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
        "name": "DAAD Development-Related Postgraduate Courses (EPOS)",
        "url": "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
        "region": "Germany",
        "degree_levels": ["MSc", "PhD", "PostDoc", "masters", "phd", "postdoc"],
        "funding": "fully_funded",
        "amount": "Full Tuition + €934-€1,300/month + Travel Allowance & Health Insurance",
        "deadline": "2026-10-31",
        "requires": ["sop", "motivation", "recommendation"],
    },
    "chevening": {
        "name": "Chevening UK Government Scholarship",
        "url": "https://www.chevening.org/scholarships/",
        "region": "UK",
        "degree_levels": ["MSc", "masters"],
        "funding": "fully_funded",
        "amount": "Full University Tuition + Monthly Living Stipend (£1,350/mo) + Flight",
        "deadline": "2026-11-05",
        "requires": ["sop", "motivation", "recommendation"],
    },
    "fulbright": {
        "name": "Fulbright Foreign Student Program",
        "url": "https://fulbrightforeign.org/",
        "region": "USA",
        "degree_levels": ["MSc", "PhD", "masters", "phd"],
        "funding": "fully_funded",
        "amount": "Full Tuition + $2,500/month Stipend + J-1 Visa Support & Health Insurance",
        "deadline": "2026-10-15",
        "requires": ["sop", "motivation", "research_proposal", "recommendation"],
    },
    "erasmus": {
        "name": "Erasmus Mundus Joint Master Degrees (EMJMD)",
        "url": "https://erasmus-plus.ec.europa.eu/opportunities/opportunities-for-individuals/students/erasmus-mundus-joint-masters",
        "region": "EU",
        "degree_levels": ["MSc", "masters"],
        "funding": "fully_funded",
        "amount": "Full Tuition + €1,400/month Allowance + Travel & Installation Costs",
        "deadline": "2026-12-15",
        "requires": ["motivation", "sop", "recommendation"],
    },
    "commonwealth": {
        "name": "Commonwealth Master's & PhD Scholarships",
        "url": "https://cscuk.fcdo.gov.uk/scholarships/",
        "region": "UK",
        "degree_levels": ["MSc", "PhD", "masters", "phd"],
        "funding": "fully_funded",
        "amount": "Full Tuition + £1,347/month Stipend + Airfare + Thesis Grant",
        "deadline": "2026-10-17",
        "requires": ["sop", "research_proposal", "recommendation"],
    },
    "gates_cambridge": {
        "name": "Gates Cambridge Scholarship",
        "url": "https://www.gatescambridge.org/apply/eligibility/",
        "region": "UK",
        "degree_levels": ["MSc", "PhD", "PostDoc", "masters", "phd", "postdoc"],
        "funding": "fully_funded",
        "amount": "Full Tuition at Cambridge + £20,000/year Maintenance Allowance",
        "deadline": "2026-12-03",
        "requires": ["sop", "research_proposal", "recommendation"],
    },
    "rhodes": {
        "name": "Rhodes Scholarship at Oxford University",
        "url": "https://www.rhodeshouse.ox.ac.uk/scholarships/applications/",
        "region": "UK",
        "degree_levels": ["MSc", "PhD", "masters", "phd"],
        "funding": "fully_funded",
        "amount": "Full Oxford Tuition + £18,180/year Stipend + Visa & Health Costs",
        "deadline": "2026-10-02",
        "requires": ["sop", "recommendation"],
    },
    "schwarzman": {
        "name": "Schwarzman Scholars Program at Tsinghua University",
        "url": "https://www.schwarzmanscholars.org/admissions/",
        "region": "China",
        "degree_levels": ["MSc", "masters"],
        "funding": "fully_funded",
        "amount": "Full Tuition + Room & Board + Travel + $4,000 Personal Stipend",
        "deadline": "2026-09-20",
        "requires": ["sop", "motivation", "recommendation"],
    },
    "mastercard": {
        "name": "Mastercard Foundation Scholars Program",
        "url": "https://mastercardfdn.org/all/scholars/",
        "region": "Africa",
        "degree_levels": ["BSc", "MSc", "undergraduate", "masters"],
        "funding": "fully_funded",
        "amount": "Full Tuition + Accommodations + Books + Monthly Allowance & Travel",
        "deadline": "2026-11-30",
        "requires": ["motivation", "recommendation"],
    },
    "turkiye_burslari": {
        "name": "Türkiye Burslari Government Scholarship",
        "url": "https://turkiyeburslari.gov.tr/",
        "region": "Turkey",
        "degree_levels": ["BSc", "MSc", "PhD", "undergraduate", "masters", "phd"],
        "funding": "fully_funded",
        "amount": "Full University Tuition + Monthly Stipend + Dormitory & Turkish Course",
        "deadline": "2026-02-20",
        "requires": ["motivation", "sop"],
    },
    "japan_mext": {
        "name": "Japan MEXT Government Embassy Scholarship",
        "url": "https://www.studyinjapan.go.jp/en/planning/by-style/pamphlet/",
        "region": "Japan",
        "degree_levels": ["MSc", "PhD", "masters", "phd"],
        "funding": "fully_funded",
        "amount": "143,000 JPY/month Stipend + Full Tuition Waiver + Roundtrip Flight",
        "deadline": "2026-05-30",
        "requires": ["sop", "research_proposal", "recommendation"],
    },
    "csc_china": {
        "name": "Chinese Government Scholarship (CSC)",
        "url": "https://www.campuschina.org/",
        "region": "China",
        "degree_levels": ["MSc", "PhD", "masters", "phd"],
        "funding": "fully_funded",
        "amount": "Full Tuition Waiver + Free Accommodation + 3,500 RMB/month Stipend",
        "deadline": "2026-03-31",
        "requires": ["sop", "research_proposal", "recommendation"],
    },
    "stipendium_hungaricum": {
        "name": "Stipendium Hungaricum Higher Education Scholarship",
        "url": "https://stipendiumhungaricum.hu/",
        "region": "Hungary",
        "degree_levels": ["BSc", "MSc", "PhD", "undergraduate", "masters", "phd"],
        "funding": "fully_funded",
        "amount": "Tuition-free Education + Accommodation + Monthly Living Allowance",
        "deadline": "2026-01-15",
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
    Search for scholarships matching the candidate's profile and query parameters.
    """
    queries = build_scholarship_queries(profile, target_degree, target_country, research_area)
    portal_matches = _score_portals(profile, target_degree, target_country, research_area)

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
    """Build search queries for scholarship discovery."""
    queries = []
    nationality = profile.get("identity", {}).get("location", {}).get("country", "")
    field = ""
    if profile.get("education"):
        field = profile["education"][0].get("field", "")

    if target_degree and target_country:
        queries.append({
            "query": f"{target_degree} scholarship {target_country} {nationality} students 2026 fully funded",
            "priority": "1",
            "category": "targeted",
        })

    if research_area:
        queries.append({
            "query": f"PhD scholarship {research_area} fully funded 2026",
            "priority": "1",
            "category": "research",
        })

    return queries


# ─── Internal: Portal Scoring ─────────────────────────────────

def _score_portals(
    profile: dict[str, Any],
    target_degree: str,
    target_country: str,
    research_area: str = "",
) -> list[Scholarship]:
    """Score known portals against the profile, degree, country, and research area."""
    from noray.scholarship_agent.eligibility_scoring import score_eligibility

    scholarships = []
    norm_degree = target_degree.lower().strip() if target_degree else ""
    norm_country = target_country.lower().strip() if target_country else ""
    norm_area = research_area.lower().strip() if research_area else ""

    for key, portal in SCHOLARSHIP_PORTALS.items():
        portal_degrees = [d.lower() for d in portal.get("degree_levels", [])]
        portal_region = portal.get("region", "").lower()

        # 1. Degree Level Filtering
        if norm_degree and norm_degree != "any":
            deg_match = any(
                norm_degree in d or d in norm_degree
                for d in portal_degrees
            )
            if not deg_match:
                continue

        # 2. Country / Region Matching
        country_match = False
        if norm_country:
            if norm_country in portal_region or portal_region in norm_country:
                country_match = True
            elif norm_country in ["eu", "europe"] and portal_region in ["germany", "uk", "hungary", "eu"]:
                country_match = True

        # Base eligibility score
        scholarship_data = {
            "name": portal["name"],
            "degree_level": portal.get("degree_levels", [""])[0],
            "field_restrictions": [norm_area] if norm_area else [],
            "required_languages": ["English"],
        }
        eligibility = score_eligibility(profile, scholarship_data)

        # Dynamic score boosting based on search criteria
        score = eligibility.overall_score
        match_reasons = []

        if norm_degree and norm_degree != "any":
            score += 15
            match_reasons.append(f"Supports target degree ({target_degree.upper()})")

        if country_match:
            score += 25
            match_reasons.append(f"Direct match for target location ({portal['region']})")

        if norm_area:
            score += 20
            match_reasons.append(f"Funding aligned with research area: {research_area.title()}")

        if portal.get("funding") == "fully_funded":
            match_reasons.append("100% Fully Funded (Tuition + Monthly Stipend)")

        # Cap score at 98
        final_score = min(98, max(50, score))

        if final_score >= 80:
            fit_level = "high"
        elif final_score >= 60:
            fit_level = "medium"
        else:
            fit_level = "low"

        display_degrees = [d for d in portal.get("degree_levels", []) if len(d) <= 8][:3]

        scholarship = Scholarship(
            name=portal["name"],
            provider=portal["name"],
            portal=portal["name"],
            country=portal.get("region", ""),
            degree_level=", ".join(display_degrees) if display_degrees else "MSc, PhD",
            amount=portal.get("amount", "Fully Funded"),
            deadline=portal.get("deadline", "2026-11-01"),
            url=portal.get("url", ""),
            description=f"{portal['name']} — {portal.get('amount')} in {portal.get('region')}",
            fit_score=final_score,
            eligibility_score=final_score,
            fit_level=fit_level,
            eligibility_notes=match_reasons,
            match_reasons=match_reasons,
            application_materials=portal.get("requires", ["sop", "motivation"]),
            source=key,
            funding_type=portal.get("funding", "fully_funded"),
        )
        scholarships.append(scholarship)

    # Sort by fit score
    scholarships.sort(key=lambda s: s.fit_score, reverse=True)

    return scholarships


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
