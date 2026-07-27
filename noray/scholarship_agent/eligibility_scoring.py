"""
NORAY — Eligibility Scoring

Score candidate eligibility against scholarship criteria.
Checks nationality, degree level, GPA, field, languages, experience, and publications.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EligibilityResult:
    """Result of eligibility scoring."""
    overall_score: int = 0      # 0-100
    criteria_met: list[str] = field(default_factory=list)
    criteria_not_met: list[str] = field(default_factory=list)
    criteria_partial: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    is_eligible: bool = False
    strength_areas: list[str] = field(default_factory=list)
    weakness_areas: list[str] = field(default_factory=list)


def score_eligibility(
    profile: dict[str, Any],
    scholarship: dict[str, Any],
) -> EligibilityResult:
    """
    Score a candidate's eligibility for a specific scholarship.
    
    Args:
        profile: Career profile dict
        scholarship: Scholarship details dict
    
    Returns:
        EligibilityResult with detailed scoring
    """
    result = EligibilityResult()
    weights = {"met": 100, "partial": 50, "not_met": 0}
    total_weight = 0
    score_sum = 0

    # ── 1. Nationality check ──
    nationality = profile.get("identity", {}).get("location", {}).get("country", "")
    eligible_nationalities = scholarship.get("eligible_nationalities", [])
    if eligible_nationalities and nationality:
        total_weight += 1
        if nationality in eligible_nationalities:
            result.criteria_met.append(f"Nationality: {nationality} is eligible")
            score_sum += weights["met"]
        else:
            result.criteria_not_met.append(f"Nationality: {nationality} may not be eligible")
            score_sum += weights["not_met"]
            result.weakness_areas.append("nationality")

    # ── 2. Degree level check ──
    target_degree = scholarship.get("degree_level", "")
    education = profile.get("education", [])
    if target_degree:
        total_weight += 1
        has_prereq = _check_degree_prereq(education, target_degree)
        if has_prereq:
            result.criteria_met.append(f"Education level meets {target_degree} requirement")
            score_sum += weights["met"]
        else:
            result.criteria_partial.append(f"Education level may not fully meet {target_degree} requirement")
            score_sum += weights["partial"]
            result.recommendations.append(f"Consider gaining the prerequisite degree for {target_degree}")

    # ── 3. GPA check ──
    min_gpa = scholarship.get("min_gpa")
    if min_gpa:
        total_weight += 1
        gpa_found = False
        for edu in education:
            gpa_str = edu.get("gpa", "")
            if gpa_str:
                gpa_val = _parse_gpa(gpa_str)
                if gpa_val and gpa_val >= min_gpa:
                    result.criteria_met.append(f"GPA: {gpa_str} meets minimum {min_gpa}")
                    score_sum += weights["met"]
                    gpa_found = True
                elif gpa_val:
                    result.criteria_not_met.append(f"GPA: {gpa_str} below minimum {min_gpa}")
                    score_sum += weights["not_met"]
                    gpa_found = True
                    result.weakness_areas.append("gpa")
        if not gpa_found:
            result.criteria_partial.append("GPA not available for verification")
            score_sum += weights["partial"]

    # ── 4. Field of study check ──
    required_fields = scholarship.get("field_restrictions", [])
    if required_fields:
        total_weight += 1
        profile_fields = [e.get("field", "") for e in education if e.get("field")]
        matching = []
        for pf in profile_fields:
            for rf in required_fields:
                if rf.lower() in pf.lower() or pf.lower() in rf.lower():
                    matching.append(pf)
                    break
        if matching:
            result.criteria_met.append(f"Field of study matches: {', '.join(set(matching))}")
            score_sum += weights["met"]
            result.strength_areas.append("field_match")
        else:
            result.criteria_partial.append("Field of study may not directly match requirements")
            score_sum += weights["partial"]
            result.recommendations.append("Highlight transferable skills from your field")

    # ── 5. Language check ──
    required_langs = scholarship.get("required_languages", [])
    profile_langs = [l.get("language", "").lower() for l in profile.get("identity", {}).get("languages", [])]
    if required_langs:
        total_weight += 1
        langs_met = []
        langs_missing = []
        for lang in required_langs:
            if lang.lower() in profile_langs:
                langs_met.append(lang)
            else:
                langs_missing.append(lang)
        if not langs_missing:
            result.criteria_met.append(f"Languages: {', '.join(langs_met)} proficiency confirmed")
            score_sum += weights["met"]
        elif langs_met:
            result.criteria_partial.append(f"Languages: {', '.join(langs_met)} confirmed, {', '.join(langs_missing)} not documented")
            score_sum += weights["partial"]
        else:
            result.criteria_not_met.append(f"Languages: {', '.join(langs_missing)} proficiency not documented")
            score_sum += weights["not_met"]
            result.weakness_areas.append("languages")
            result.recommendations.append(f"Obtain language certification for {', '.join(langs_missing)}")

    # ── 6. Experience check ──
    min_years = scholarship.get("min_experience_years", 0)
    if min_years:
        total_weight += 1
        experience = profile.get("experience", [])
        total_years = _estimate_total_years(experience)
        if total_years >= min_years:
            result.criteria_met.append(f"Experience: ~{total_years} years meets {min_years}-year requirement")
            score_sum += weights["met"]
            result.strength_areas.append("experience")
        elif total_years >= min_years * 0.7:
            result.criteria_partial.append(f"Experience: ~{total_years} years, close to {min_years}-year requirement")
            score_sum += weights["partial"]
        else:
            result.criteria_not_met.append(f"Experience: ~{total_years} years, below {min_years}-year requirement")
            score_sum += weights["not_met"]
            result.weakness_areas.append("experience")

    # ── 7. Publications check ──
    requires_publications = scholarship.get("requires_publications", False)
    if requires_publications:
        total_weight += 1
        publications = profile.get("publications", [])
        if publications:
            result.criteria_met.append(f"Publications: {len(publications)} publication(s) listed")
            score_sum += weights["met"]
            result.strength_areas.append("publications")
        else:
            result.criteria_partial.append("Publications: none listed — may be a disadvantage for research-focused scholarships")
            score_sum += weights["partial"]
            result.recommendations.append("Highlight any conference presentations, theses, or working papers")

    # ── 8. Research interests check ──
    required_research = scholarship.get("research_areas", [])
    if required_research:
        total_weight += 1
        profile_research = profile.get("scholarship_goals", {}).get("research_interests", [])
        profile_domain = profile.get("skills", {}).get("domain", [])
        all_research = [r.lower() for r in profile_research + profile_domain]
        matching_research = []
        for rr in required_research:
            if any(rr.lower() in ar or ar in rr.lower() for ar in all_research):
                matching_research.append(rr)
        if matching_research:
            result.criteria_met.append(f"Research interests match: {', '.join(matching_research)}")
            score_sum += weights["met"]
            result.strength_areas.append("research_fit")
        else:
            result.criteria_partial.append("Research interests don't directly match — consider framing adjacent interests")
            score_sum += weights["partial"]

    # ── Calculate overall score ──
    if total_weight > 0:
        result.overall_score = int(score_sum / total_weight)
    else:
        # No specific criteria to check — assume moderate eligibility
        result.overall_score = 60

    # ── Eligibility verdict ──
    result.is_eligible = (
        result.overall_score >= 50
        and len(result.criteria_not_met) <= 1  # Allow one hard miss if score is high enough
    )

    # If score is very high, override hard misses
    if result.overall_score >= 80 and len(result.criteria_not_met) <= 2:
        result.is_eligible = True

    return result


def generate_eligibility_report(result: EligibilityResult, scholarship_name: str) -> str:
    """Generate a human-readable eligibility report."""
    lines = [f"# Eligibility Report: {scholarship_name}\n"]

    lines.append(f"**Overall Score: {result.overall_score}/100**")
    lines.append(f"**Eligible:** {'✅ Yes' if result.is_eligible else '❌ No'}\n")

    if result.criteria_met:
        lines.append("## ✅ Criteria Met")
        for c in result.criteria_met:
            lines.append(f"- {c}")
        lines.append("")

    if result.criteria_partial:
        lines.append("## 🟡 Partially Met")
        for c in result.criteria_partial:
            lines.append(f"- {c}")
        lines.append("")

    if result.criteria_not_met:
        lines.append("## ❌ Not Met")
        for c in result.criteria_not_met:
            lines.append(f"- {c}")
        lines.append("")

    if result.strength_areas:
        lines.append("## 💪 Strength Areas")
        for s in result.strength_areas:
            lines.append(f"- {s.replace('_', ' ').title()}")
        lines.append("")

    if result.weakness_areas:
        lines.append("## ⚠️ Weakness Areas")
        for w in result.weakness_areas:
            lines.append(f"- {w.replace('_', ' ').title()}")
        lines.append("")

    if result.recommendations:
        lines.append("## 💡 Recommendations")
        for r in result.recommendations:
            lines.append(f"- {r}")
        lines.append("")

    return "\n".join(lines)


# ─── Internal Helpers ─────────────────────────────────────────

def _check_degree_prereq(education: list[dict], target: str) -> bool:
    """Check if education meets the prerequisite for the target degree."""
    hierarchy = {
        "bsc": 1, "bachelor": 1, "ba": 1, "bs": 1,
        "msc": 2, "master": 2, "ma": 2, "ms": 2, "mba": 2,
        "phd": 3, "doctorate": 3, "doctoral": 3,
        "postdoc": 4, "postdoctoral": 4,
    }
    target_level = hierarchy.get(target.lower().replace(".", "").strip(), 0)

    for edu in education:
        degree = edu.get("degree", "").lower().replace(".", "").strip()
        edu_level = hierarchy.get(degree, 0)
        # One level below target is usually OK (e.g., BSc for MSc application)
        if edu_level >= target_level - 1:
            return True
    return False


def _parse_gpa(gpa_str: str) -> float | None:
    """Parse a GPA string into a float. Handles various formats."""
    gpa_str = gpa_str.strip()

    # Direct number: "3.8", "3.8/4.0"
    match = re.match(r"(\d+\.?\d*)", gpa_str)
    if match:
        val = float(match.group(1))
        # If it looks like a percentage (e.g., "85%"), convert to 4.0 scale
        if val > 5:
            return val / 25.0  # Rough conversion
        return val

    return None


def _estimate_total_years(experience: list[dict]) -> float:
    """Estimate total years of experience from experience entries."""
    total_months = 0
    for exp in experience:
        start = exp.get("start_date", "")
        end = exp.get("end_date", "present")

        start_year = _extract_year(start)
        end_year = _extract_year(end) if end and end.lower() != "present" else 2026

        if start_year and end_year:
            total_months += max(0, (end_year - start_year) * 12)

    return round(total_months / 12, 1)


def _extract_year(date_str: str) -> int | None:
    """Extract a year from a date string."""
    if not date_str:
        return None
    match = re.search(r"(\d{4})", date_str)
    return int(match.group(1)) if match else None
