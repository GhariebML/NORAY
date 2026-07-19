"""
NORAY — Skill Gap Analysis

Identify gaps between the candidate's profile and target roles/scholarships.
Supports both aggregate (tracked jobs) and targeted (single posting) modes.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
import re


@dataclass
class SkillGap:
    """A single identified skill gap."""
    skill: str = ""
    priority: str = ""  # critical, high, medium, low
    gap_type: str = ""  # hard, soft, domain, tooling, credential
    source: str = ""  # where the gap was identified
    frequency: int = 0  # how many jobs mention it
    score: float = 0.0  # weighted score
    category: str = ""  # for roadmap grouping
    time_estimate: str = ""  # estimated learning time
    study_direction: str = ""  # suggested path
    learning_resources: list[str] = field(default_factory=list)  # suggested resources


@dataclass
class GapAnalysisResult:
    """Result of a skill gap analysis."""
    mode: str = ""  # aggregate or targeted
    gaps: list[SkillGap] = field(default_factory=list)
    total_jobs_analyzed: int = 0
    profile_skills_count: int = 0
    gap_count_by_priority: dict[str, int] = field(default_factory=dict)
    themes: dict[str, list[str]] = field(default_factory=dict)  # theme -> skills
    recommendations: list[str] = field(default_factory=list)
    top_priority_skills: list[str] = field(default_factory=list)


# Priority mapping for different gap types
_GAP_PRIORITY = {
    "credential": "critical",
    "hard": "high",
    "domain": "medium",
    "tooling": "medium",
    "soft": "low",
}

# Time estimates by difficulty
_TIME_ESTIMATES = {
    "easy": "~20h",
    "medium": "~40h",
    "hard": "~80h",
}

# Skill category keywords
_CATEGORY_MAP = {
    "programming": ["python", "java", "javascript", "typescript", "golang", "rust", "c++", "sql"],
    "ml_ai": ["machine learning", "deep learning", "nlp", "computer vision", "pytorch", "tensorflow", "scikit-learn", "transformer", "llm"],
    "data": ["data science", "data analysis", "data engineering", "pandas", "numpy", "spark", "hadoop"],
    "cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd"],
    "web": ["react", "vue", "angular", "node.js", "fastapi", "django", "flask", "html", "css"],
    "tools": ["git", "linux", "bash", "vim", "vscode", "jira", "confluence"],
    "soft": ["leadership", "communication", "teamwork", "problem-solving", "project management", "mentoring"],
    "domain": ["healthcare", "finance", "advertising", "nlp", "recommender", "time series"],
}

# Known learning resources by skill
_SKILL_RESOURCES = {
    "python": ["Automate the Boring Stuff", "Python for Data Science Handbook", "Real Python"],
    "machine learning": ["Andrew Ng's ML Course", "Hands-On ML with Scikit-Learn", "Fast.ai"],
    "deep learning": ["Deep Learning Specialization (Coursera)", "Deep Learning with PyTorch", "fast.ai"],
    "nlp": ["Stanford CS224N", "NLP Specialization (deeplearning.ai)", "Hugging Face Course"],
    "pytorch": ["PyTorch Official Tutorials", "PyTorch Lightning Docs", "d2l.ai"],
    "tensorflow": ["TensorFlow Official Tutorials", "TF Certification", "Keras Docs"],
    "aws": ["AWS Cloud Practitioner", "AWS Solutions Architect", 'A Cloud Guru'],
    "docker": ["Docker Official Docs", "Docker Deep Dive (Nigel Poulton)", "KodeKloud"],
    "kubernetes": ["Kubernetes Official Tutorials", "CKA Certification", "kodekloud"],
    "data science": ["IBM Data Science Certificate", "Kaggle Learn", "DataCamp"],
    "sql": ["SQLBolt", "Mode Analytics SQL Tutorial", "LeetCode Database"],
    "git": ["Pro Git Book", "GitHub Skills", "Learn Git Branching"],
    "leadership": ["The Manager's Path", "High Output Management", "Staff Engineer"],
    "communication": ["Crucial Conversations", "The Art of Explanation"],
}


def analyze_skill_gaps(
    profile: dict[str, Any],
    requirements: list[str],
    mode: str = "targeted",
    job_frequency: dict[str, int] | None = None,
) -> GapAnalysisResult:
    """
    Analyze skill gaps between profile and target requirements.

    Args:
        profile: Career profile dict
        requirements: List of required/preferred skills from jobs or scholarships
        mode: "targeted" (single posting) or "aggregate" (multiple tracked jobs)
        job_frequency: Skill -> count of jobs mentioning it (for aggregate mode)

    Returns:
        GapAnalysisResult with prioritized gaps
    """
    result = GapAnalysisResult(mode=mode)

    if job_frequency is None:
        job_frequency = {}

    # Get profile skills
    profile_skills = _extract_profile_skills(profile)
    result.profile_skills_count = len(profile_skills)

    # Normalize requirements to avoid duplicates
    seen = set()
    for req in requirements:
        req_normalized = req.lower().strip()
        if req_normalized in seen:
            continue
        seen.add(req_normalized)

        if not _skill_matches(req, profile_skills):
            skill_type = _classify_skill_type(req)
            gap_type = _classify_gap_type(req)
            freq = job_frequency.get(req, job_frequency.get(req_normalized, 1))

            gap = SkillGap(
                skill=req,
                gap_type=gap_type,
                source="job_requirement" if mode == "targeted" else "aggregate_tracker",
                frequency=freq,
                category=skill_type,
                time_estimate=_estimate_learning_time(req, gap_type),
                study_direction=_suggest_study_direction(req, skill_type),
                learning_resources=_SKILL_RESOURCES.get(req_normalized, []),
            )
            result.gaps.append(gap)

    # Sort and prioritize
    result.gaps = _prioritize_gaps(result.gaps, job_frequency)
    result.gap_count_by_priority = _count_by_priority(result.gaps)
    result.top_priority_skills = [g.skill for g in result.gaps if g.priority in ("critical", "high")][:10]

    # Group by theme
    result.themes = _group_gaps_by_theme(result.gaps)

    # Generate recommendations
    result.recommendations = _generate_recommendations(result)

    return result


def generate_optimization_report(
    profile: dict[str, Any],
    requirements: list[str],
    job_frequency: dict[str, int] | None = None,
) -> str:
    """Generate a human-readable skill gap report."""
    result = analyze_skill_gaps(profile, requirements, mode="aggregate", job_frequency=job_frequency)

    lines = ["# Skill Gap Analysis Report", ""]
    lines.append(f"**Mode**: {result.mode}")
    lines.append(f"**Profile skills**: {result.profile_skills_count}")
    lines.append(f"**Gaps identified**: {len(result.gaps)}")
    lines.append(f"**Critical + High priority**: {len(result.top_priority_skills)}")
    lines.append("")

    if result.gap_count_by_priority:
        lines.append("## Priority Breakdown")
        for p in ["critical", "high", "medium", "low"]:
            count = result.gap_count_by_priority.get(p, 0)
            if count > 0:
                lines.append(f"- **{p.title()}**: {count}")
        lines.append("")

    if result.top_priority_skills:
        lines.append("## Top Priority Skills")
        for skill in result.top_priority_skills:
            lines.append(f"- {skill}")
        lines.append("")

    if result.themes:
        lines.append("## Gaps by Theme")
        for theme, skills in result.themes.items():
            lines.append(f"\n### {theme}")
            for skill in skills:
                lines.append(f"- {skill}")
        lines.append("")

    if result.recommendations:
        lines.append("## Recommendations")
        for rec in result.recommendations:
            lines.append(f"- {rec}")

    return "\n".join(lines)


def _extract_profile_skills(profile: dict[str, Any]) -> set[str]:
    """Extract all skills from the profile as a normalized set."""
    skills = set()
    skill_data = profile.get("skills", {})
    for category in ["primary", "secondary", "domain", "tools"]:
        for skill in skill_data.get(category, []):
            skills.add(skill.lower().strip())
    return skills


def _skill_matches(requirement: str, profile_skills: set[str]) -> bool:
    """Check if a requirement is already covered by profile skills."""
    req_lower = requirement.lower().strip()
    for skill in profile_skills:
        if req_lower in skill or skill in req_lower:
            return True
        # Word-boundary match for short skills
        if len(req_lower) <= 3:
            if re.search(rf"\b{re.escape(req_lower)}\b", skill):
                return True
    return False


def _classify_skill_type(skill: str) -> str:
    """Classify a skill into a category."""
    skill_lower = skill.lower()
    for category, keywords in _CATEGORY_MAP.items():
        for kw in keywords:
            if kw in skill_lower or skill_lower in kw:
                return category
    return "general"


def _classify_gap_type(skill: str) -> str:
    """Classify what type of gap this is."""
    skill_lower = skill.lower()
    credential_keywords = ["certification", "certificate", "degree", "phd", "masters"]
    if any(kw in skill_lower for kw in credential_keywords):
        return "credential"
    tool_keywords = ["docker", "kubernetes", "git", "aws", "azure", "gcp", "terraform"]
    if any(kw in skill_lower for kw in tool_keywords):
        return "tooling"
    soft_keywords = ["leadership", "communication", "teamwork", "mentoring", "management"]
    if any(kw in skill_lower for kw in soft_keywords):
        return "soft"
    domain_keywords = ["healthcare", "finance", "advertising", "nlp", "recommender", "time series"]
    if any(kw in skill_lower for kw in domain_keywords):
        return "domain"
    return "hard"


def _estimate_learning_time(skill: str, gap_type: str) -> str:
    """Estimate time to learn a skill."""
    if gap_type == "credential":
        return "~200h"
    if gap_type == "soft":
        return "~30h"
    # Check known skills
    skill_lower = skill.lower()
    for known_skill, estimate in {
        "python": "~80h",
        "machine learning": "~120h",
        "deep learning": "~160h",
        "docker": "~40h",
        "kubernetes": "~60h",
        "sql": "~40h",
        "git": "~20h",
        "aws": "~80h",
        "react": "~80h",
        "pytorch": "~80h",
        "tensorflow": "~80h",
        "nlp": "~100h",
    }.items():
        if known_skill in skill_lower or skill_lower in known_skill:
            return estimate
    return _TIME_ESTIMATES.get("medium", "~40h")


def _suggest_study_direction(skill: str, category: str) -> str:
    """Suggest a study direction for a skill."""
    direction_map = {
        "programming": f"Start with fundamentals, then build projects. Practice on LeetCode/HackerRank.",
        "ml_ai": f"Start with theory (Andrew Ng), then hands-on (Kaggle). Build a portfolio project.",
        "data": f"Learn through practice. Work with real datasets on Kaggle.",
        "cloud": f"Start with free tier, get certified. Build and deploy projects.",
        "web": f"Build projects from scratch. Start with tutorials, then full apps.",
        "tools": f"Use in daily workflow. Learn through practice, not just reading.",
        "soft": f"Read books, practice in real situations. Seek feedback.",
        "domain": f"Study domain-specific literature. Apply ML to domain problems.",
    }
    return direction_map.get(category, f"Find structured learning path. Practice consistently.")


def _prioritize_gaps(gaps: list[SkillGap], job_frequency: dict[str, int]) -> list[SkillGap]:
    """Sort gaps by priority based on type and frequency."""
    for gap in gaps:
        base_priority = _GAP_PRIORITY.get(gap.gap_type, "medium")
        # Boost priority if frequency is high
        if gap.frequency >= 5:
            base_priority = "critical"
        elif gap.frequency >= 3 and base_priority in ("medium", "low"):
            base_priority = "high"
        gap.priority = base_priority
        gap.score = gap.frequency * _GAP_PRIORITY_REVERSE.get(base_priority, 2)

    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(gaps, key=lambda g: (-g.score, priority_order.get(g.priority, 4)))


_GAP_PRIORITY_REVERSE = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _count_by_priority(gaps: list[SkillGap]) -> dict[str, int]:
    """Count gaps by priority level."""
    counts = {}
    for gap in gaps:
        counts[gap.priority] = counts.get(gap.priority, 0) + 1
    return counts


def _group_gaps_by_theme(gaps: list[SkillGap]) -> dict[str, list[str]]:
    """Group gaps by category theme."""
    themes = {}
    for gap in gaps:
        theme = gap.category.title()
        if theme not in themes:
            themes[theme] = []
        themes[theme].append(gap.skill)
    return themes


def _generate_recommendations(result: GapAnalysisResult) -> list[str]:
    """Generate actionable recommendations."""
    recs = []

    critical_high = [g for g in result.gaps if g.priority in ("critical", "high")]
    if len(critical_high) > 3:
        recs.append(f"Focus on {len(critical_high)} high-priority skills before applying to competitive roles.")

    credential_gaps = [g for g in result.gaps if g.gap_type == "credential"]
    if credential_gaps:
        names = ", ".join(g.skill for g in credential_gaps[:3])
        recs.append(f"Consider pursuing credentials: {names}. These are often hard requirements.")

    tool_gaps = [g for g in result.gaps if g.gap_type == "tooling"]
    if tool_gaps:
        recs.append(f"Quick wins: Learn {tool_gaps[0].skill} ({tool_gaps[0].time_estimate}) to fill a tooling gap.")

    if result.profile_skills_count < 5:
        recs.append("Your profile has few listed skills. Add more to improve ATS matching.")

    if not recs:
        recs.append("Profile looks strong. Focus on experience and projects to differentiate.")

    return recs
