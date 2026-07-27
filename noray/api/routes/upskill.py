"""
NORAY — Upskill API Routes

Endpoints for skill gap analysis and career roadmapping.
"""

from fastapi import APIRouter, Query

from noray.api.schemas import RoadmapRequest, UpskillRequest
from noray.shared.profile_store import load_profile

router = APIRouter()


@router.post("/analyze")
async def analyze_skill_gaps(request: UpskillRequest):
    """Run skill gap analysis against tracked jobs or a specific posting."""
    from noray.dashboard.jobs import load_applications
    from noray.upskill_agent.skill_gap_analysis import analyze_skill_gaps as run_analysis
    from noray.upskill_agent.skill_gap_analysis import generate_optimization_report

    profile = load_profile()
    profile_dict = profile.model_dump(mode="json")

    job_text = getattr(request, 'job_text', None)
    if job_text:
        # Targeted mode: analyze against a single posting
        import re
        requirements = re.findall(r'\b[A-Z][a-zA-Z+#.]+\b', request.job_text)
        result = run_analysis(profile_dict, requirements, mode="targeted")
    else:
        # Aggregate mode: gather skills from profile gaps vs. tracked job descriptions
        jobs = load_applications()
        all_requirements: list[str] = []
        freq: dict[str, int] = {}
        import re
        for job in jobs:
            desc = getattr(job, 'description', None) or ""
            if desc:
                skills = re.findall(r'\b[A-Z][a-zA-Z+#.]+\b', desc)
                for s in skills:
                    freq[s] = freq.get(s, 0) + 1
                all_requirements.extend(skills)
        # Deduplicate
        unique_reqs = list(set(all_requirements))
        if not unique_reqs:
            # Fallback: use common tech skills as requirements
            unique_reqs = ["Python", "Machine Learning", "Docker", "Kubernetes", "AWS", "SQL", "Git"]
        result = run_analysis(profile_dict, unique_reqs, mode="aggregate", job_frequency=freq)

    report = generate_optimization_report(profile_dict, [g.skill for g in result.gaps])

    return {
        "status": "analyzed",
        "mode": result.mode,
        "profile_skills_count": result.profile_skills_count,
        "gaps": [
            {
                "skill": g.skill,
                "priority": g.priority,
                "gap_type": g.gap_type,
                "category": g.category,
                "time_estimate": g.time_estimate,
                "study_direction": g.study_direction,
                "learning_resources": g.learning_resources,
            }
            for g in result.gaps
        ],
        "top_priority_skills": result.top_priority_skills,
        "themes": result.themes,
        "recommendations": result.recommendations,
        "report": report,
    }


@router.post("/roadmap")
async def generate_roadmap(request: RoadmapRequest):
    """Generate a career roadmap."""
    from noray.upskill_agent.roadmap_builder import build_roadmap, format_roadmap

    profile = load_profile()
    profile_dict = profile.model_dump(mode="json")

    roadmap = build_roadmap(
        profile_dict,
        timeline_months=request.timeline_months,
    )

    return {
        "status": "generated",
        "career_path": roadmap.career_path,
        "timeline_months": roadmap.timeline_months,
        "total_time_estimate": roadmap.total_time_estimate,
        "summary": roadmap.summary,
        "milestones": [
            {
                "title": m.title,
                "description": m.description,
                "target_date": m.target_date,
                "category": m.category,
                "time_estimate": m.time_estimate,
                "success_criteria": m.success_criteria,
                "resources": m.resources,
            }
            for m in roadmap.milestones
        ],
        "phases": roadmap.phases,
        "formatted": format_roadmap(roadmap),
    }


@router.post("/resources")
async def find_learning_resources(skill: str = Query(..., description="Skill to find resources for")):
    """Find learning resources for a specific skill."""
    from noray.upskill_agent.learning_resources import find_resources

    plan = find_resources(skill)

    return {
        "status": "found",
        "skill": plan.skill,
        "total_hours": plan.total_hours,
        "prerequisites": plan.prerequisites,
        "milestones": plan.milestones,
        "resources": [
            {
                "name": r.name,
                "url": r.url,
                "type": r.resource_type,
                "provider": r.provider,
                "hours": r.estimated_hours,
                "difficulty": r.difficulty,
                "free": r.free,
                "reason": r.reason,
            }
            for r in plan.resources
        ],
    }
