"""
NORAY — Career Roadmap Builder

Generate long-term career and learning roadmaps with milestones.
Includes portfolio project suggestions, certification milestones,
and application timeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Milestone:
    """A single roadmap milestone."""
    title: str = ""
    description: str = ""
    target_date: str = ""  # e.g., "Month 3"
    category: str = ""  # learning, project, certification, application, networking
    dependencies: list[str] = field(default_factory=list)
    time_estimate: str = ""  # e.g., "~20h"
    completed: bool = False
    resources: list[str] = field(default_factory=list)
    success_criteria: str = ""  # how to know when done


@dataclass
class CareerRoadmap:
    """A complete career roadmap."""
    timeline_months: int = 12
    milestones: list[Milestone] = field(default_factory=list)
    career_path: str = ""
    summary: str = ""
    total_time_estimate: str = ""
    phases: dict[str, list[str]] = field(default_factory=dict)  # phase -> milestone titles


# Portfolio project templates by career path
_PORTFOLIO_PROJECTS = {
    "data_scientist": [
        {"title": "End-to-End ML Pipeline", "desc": "Build a complete ML pipeline: data collection → training → deployment → monitoring", "time": "~60h", "skills": ["python", "ml", "docker"]},
        {"title": "Kaggle Competition", "desc": "Compete in a Kaggle competition, document approach and results", "time": "~40h", "skills": ["data science", "ml"]},
        {"title": "Interactive Dashboard", "desc": "Build an analytics dashboard with Streamlit or Dash", "time": "~30h", "skills": ["python", "data visualization"]},
    ],
    "ml_engineer": [
        {"title": "Model Serving API", "desc": "Build a production ML API with FastAPI + Docker + CI/CD", "time": "~50h", "skills": ["python", "fastapi", "docker"]},
        {"title": "MLOps Pipeline", "desc": "Set up experiment tracking, model registry, and automated retraining", "time": "~80h", "skills": ["mlops", "docker", "kubernetes"]},
        {"title": "Benchmark Suite", "desc": "Create a reproducible benchmark comparing model architectures", "time": "~40h", "skills": ["pytorch", "python"]},
    ],
    "software_engineer": [
        {"title": "Full-Stack App", "desc": "Build a full-stack application with auth, API, and database", "time": "~60h", "skills": ["react", "python", "sql"]},
        {"title": "Open Source Contribution", "desc": "Contribute meaningful PRs to an open source project", "time": "~40h", "skills": ["git", "python"]},
        {"title": "System Design", "desc": "Design and document a distributed system architecture", "time": "~30h", "skills": ["system design", "architecture"]},
    ],
}

# Certification paths by domain
_CERTIFICATIONS = {
    "cloud": [
        {"name": "AWS Solutions Architect", "time": "~80h", "value": "high"},
        {"name": "GCP Professional ML Engineer", "time": "~100h", "value": "high"},
    ],
    "ml_ai": [
        {"name": "TensorFlow Developer Certificate", "time": "~60h", "value": "medium"},
        {"name": "AWS ML Specialty", "time": "~100h", "value": "high"},
    ],
    "data": [
        {"name": "Google Data Analytics Certificate", "time": "~40h", "value": "medium"},
        {"name": "IBM Data Science Certificate", "time": "~60h", "value": "medium"},
    ],
}


def build_roadmap(
    profile: dict[str, Any],
    career_goals: dict[str, Any] | None = None,
    skill_gaps: list[dict[str, Any]] | None = None,
    timeline_months: int = 12,
) -> CareerRoadmap:
    """
    Build a career roadmap with learning milestones.

    Args:
        profile: Career profile dict
        career_goals: Career goals from profile (uses profile["goals"] if None)
        skill_gaps: Identified skill gaps from GapAnalysisResult.gaps
        timeline_months: Roadmap duration in months

    Returns:
        CareerRoadmap with ordered milestones
    """
    if career_goals is None:
        career_goals = profile.get("goals", {})
    if skill_gaps is None:
        skill_gaps = []

    roadmap = CareerRoadmap(timeline_months=timeline_months)
    roadmap.career_path = _determine_career_path(profile, career_goals)

    # Phase 1: Skill building (months 1-4)
    learning_milestones = _create_learning_milestones(skill_gaps, timeline_months)
    roadmap.milestones.extend(learning_milestones)

    # Phase 2: Certification (months 2-6)
    cert_milestones = _create_certification_milestones(profile, roadmap.career_path, timeline_months)
    roadmap.milestones.extend(cert_milestones)

    # Phase 3: Projects (months 3-8)
    project_milestones = _create_project_milestones(profile, roadmap.career_path, timeline_months)
    roadmap.milestones.extend(project_milestones)

    # Phase 4: Applications (months 6+)
    app_milestones = _create_application_milestones(career_goals, timeline_months)
    roadmap.milestones.extend(app_milestones)

    # Phase 5: Networking (ongoing)
    network_milestones = _create_networking_milestones(timeline_months)
    roadmap.milestones.extend(network_milestones)

    # Sort all milestones
    roadmap.milestones.sort(key=lambda m: _month_to_int(m.target_date))

    # Group into phases
    roadmap.phases = _group_into_phases(roadmap.milestones)

    # Calculate total time
    total_hours = sum(_parse_hours(m.time_estimate) for m in roadmap.milestones)
    roadmap.total_time_estimate = f"~{total_hours}h"

    # Generate summary
    roadmap.summary = _generate_summary(roadmap)

    return roadmap


def format_roadmap(roadmap: CareerRoadmap) -> str:
    """Format roadmap as readable markdown."""
    lines = [
        f"# Career Roadmap: {roadmap.career_path.title()}",
        "",
        f"**Timeline**: {roadmap.timeline_months} months",
        f"**Total estimated time**: {roadmap.total_time_estimate}",
        f"**Milestones**: {len(roadmap.milestones)}",
        "",
        "---",
        "",
    ]

    # Summary
    if roadmap.summary:
        lines.append("## Summary")
        lines.append(roadmap.summary)
        lines.append("")

    # Phases
    for phase_name, milestone_titles in roadmap.phases.items():
        lines.append(f"## {phase_name}")
        lines.append("")
        for title in milestone_titles:
            ms = next((m for m in roadmap.milestones if m.title == title), None)
            if ms:
                status = "✅" if ms.completed else "⬜"
                lines.append(f"{status} **{ms.title}** ({ms.target_date}, {ms.time_estimate})")
                if ms.description:
                    lines.append(f"  {ms.description}")
                if ms.success_criteria:
                    lines.append(f"  *Done when: {ms.success_criteria}*")
                if ms.resources:
                    lines.append(f"  Resources: {', '.join(ms.resources)}")
                lines.append("")

    return "\n".join(lines)


def _determine_career_path(profile: dict, goals: dict) -> str:
    """Determine the primary career path from profile and goals."""
    target_roles = goals.get("target_roles", [])
    for role in target_roles:
        role_lower = role.lower()
        if "data scien" in role_lower or "analyst" in role_lower:
            return "data_scientist"
        if "ml eng" in role_lower or "machine learning" in role_lower:
            return "ml_engineer"
        if "software" in role_lower or "backend" in role_lower or "full stack" in role_lower:
            return "software_engineer"
    # Fallback: check skills
    skills = profile.get("skills", {})
    primary = [s.lower() for s in skills.get("primary", [])]
    if any("machine learning" in s or "deep learning" in s for s in primary):
        return "ml_engineer"
    if any("data scien" in s or "data analy" in s for s in primary):
        return "data_scientist"
    return "software_engineer"


def _create_learning_milestones(gaps: list[dict], months: int) -> list[Milestone]:
    """Create learning milestones from skill gaps."""
    milestones = []
    # Only take top 6 gaps to avoid overloading
    for i, gap in enumerate(gaps[:6]):
        month = min(1 + i, months - 2)
        skill = gap.get("skill", "Unknown")
        milestones.append(Milestone(
            title=f"Learn {skill}",
            description=gap.get("study_direction", f"Study {skill} fundamentals and practice."),
            target_date=f"Month {month}",
            category="learning",
            time_estimate=gap.get("time_estimate", "~40h"),
            resources=gap.get("learning_resources", []),
            success_criteria=f"Complete a small project or exercise demonstrating {skill} proficiency.",
        ))
    return milestones


def _create_certification_milestones(profile: dict, career_path: str, months: int) -> list[Milestone]:
    """Create certification milestones based on career path."""
    milestones = []
    certs = _CERTIFICATIONS.get("cloud" if "cloud" in career_path else "ml_ai", [])

    existing_certs = [c.get("name", "").lower() for c in profile.get("certifications", [])]

    for i, cert in enumerate(certs[:2]):
        if any(cert["name"].lower() in existing for existing in existing_certs):
            continue
        month = min(3 + i * 2, months - 2)
        milestones.append(Milestone(
            title=f"Certification: {cert['name']}",
            description=f"Prepare for and pass {cert['name']} certification.",
            target_date=f"Month {month}",
            category="certification",
            time_estimate=cert["time"],
            success_criteria=f"Pass the {cert['name']} exam.",
            resources=[f"Search for {cert['name']} study materials"],
        ))
    return milestones


def _create_project_milestones(profile: dict, career_path: str, months: int) -> list[Milestone]:
    """Create portfolio project milestones."""
    milestones = []
    projects = _PORTFOLIO_PROJECTS.get(career_path, _PORTFOLIO_PROJECTS["data_scientist"])

    for i, proj in enumerate(projects[:3]):
        month = min(4 + i * 2, months - 1)
        milestones.append(Milestone(
            title=f"Project: {proj['title']}",
            description=proj["desc"],
            target_date=f"Month {month}",
            category="project",
            time_estimate=proj["time"],
            success_criteria=f"Deploy and document the {proj['title']} project. Add to GitHub portfolio.",
        ))
    return milestones


def _create_application_milestones(goals: dict, months: int) -> list[Milestone]:
    """Create job/scholarship application milestones."""
    milestones = []
    target_roles = goals.get("target_roles", [])
    target_countries = goals.get("target_countries", goals.get("scholarship", {}).get("target_countries", []))

    apply_start = max(6, int(months * 0.5))
    milestones.append(Milestone(
        title="Begin active job applications",
        description=f"Start applying to roles: {', '.join(target_roles[:3])}" if target_roles else "Start applying to target roles",
        target_date=f"Month {apply_start}",
        category="application",
        success_criteria="Submit at least 10 tailored applications.",
    ))

    milestones.append(Milestone(
        title="CV + Cover Letter review round",
        description="Get feedback on application materials from 2-3 people.",
        target_date=f"Month {apply_start - 1}",
        category="application",
        dependencies=["CV optimization"],
    ))

    if target_countries:
        milestones.append(Milestone(
            title="Scholarship applications",
            description=f"Apply to relevant scholarships for {', '.join(target_countries[:2])}",
            target_date=f"Month {apply_start}",
            category="application",
            success_criteria="Submit at least 3 scholarship applications.",
        ))

    return milestones


def _create_networking_milestones(months: int) -> list[Milestone]:
    """Create networking milestones."""
    milestones = []
    milestones.append(Milestone(
        title="LinkedIn profile optimization",
        description="Update LinkedIn with projects, skills, and career interests.",
        target_date="Month 1",
        category="networking",
        time_estimate="~4h",
        success_criteria="Profile completeness 100%, featured section populated.",
    ))

    milestones.append(Milestone(
        title="Connect with 20 professionals in target field",
        description="Reach out to professionals in target roles/companies.",
        target_date="Month 3",
        category="networking",
        success_criteria="20 meaningful connections made.",
    ))

    milestones.append(Milestone(
        title="Attend 2 industry events or meetups",
        description="Attend virtual or in-person events in target field.",
        target_date="Month 6",
        category="networking",
        success_criteria="Attended events and followed up with contacts.",
    ))

    return milestones


def _group_into_phases(milestones: list[Milestone]) -> dict[str, list[str]]:
    """Group milestones into career phases."""
    phases = {
        "Phase 1: Skill Building (Months 1-4)": [],
        "Phase 2: Certification & Projects (Months 3-8)": [],
        "Phase 3: Applications & Networking (Months 6+)": [],
    }

    for ms in milestones:
        month = _month_to_int(ms.target_date)
        if month <= 4:
            if ms.category in ("learning", "networking"):
                phases["Phase 1: Skill Building (Months 1-4)"].append(ms.title)
            else:
                phases["Phase 2: Certification & Projects (Months 3-8)"].append(ms.title)
        elif month <= 8:
            phases["Phase 2: Certification & Projects (Months 3-8)"].append(ms.title)
        else:
            phases["Phase 3: Applications & Networking (Months 6+)"].append(ms.title)

    # Remove empty phases
    return {k: v for k, v in phases.items() if v}


def _generate_summary(roadmap: CareerRoadmap) -> str:
    """Generate a summary of the roadmap."""
    categories = {}
    for ms in roadmap.milestones:
        categories[ms.category] = categories.get(ms.category, 0) + 1

    parts = []
    if "learning" in categories:
        parts.append(f"{categories['learning']} learning milestones")
    if "certification" in categories:
        parts.append(f"{categories['certification']} certifications")
    if "project" in categories:
        parts.append(f"{categories['project']} portfolio projects")
    if "application" in categories:
        parts.append(f"{categories['application']} application milestones")
    if "networking" in categories:
        parts.append(f"{categories['networking']} networking activities")

    return f"This roadmap includes {', '.join(parts)} over {roadmap.timeline_months} months."


def _month_to_int(target_date: str) -> int:
    """Convert 'Month 3' to integer 3."""
    try:
        return int(target_date.replace("Month ", "").strip())
    except (ValueError, AttributeError):
        return 99


def _parse_hours(time_estimate: str) -> int:
    """Parse '~40h' to integer 40."""
    try:
        return int("".join(filter(str.isdigit, time_estimate)))
    except ValueError:
        return 0
