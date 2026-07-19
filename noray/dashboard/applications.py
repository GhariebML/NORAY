"""
NORAY — Unified Application Tracker

Merged view of job and scholarship applications with filtering,
timeline views, and pipeline visualization data.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field

from noray.dashboard.jobs import load_applications as load_jobs
from noray.dashboard.scholarships import load_applications as load_scholarships


@dataclass
class ApplicationSummary:
    """Unified application entry."""
    id: str = ""
    type: str = ""  # job or scholarship
    name: str = ""  # company or scholarship name
    role: str = ""  # role title or degree level
    status: str = ""
    date: str = ""
    url: str = ""
    priority: str = ""  # high, medium, low
    days_since_applied: int = 0


# Status to priority mapping for visual pipeline
_STATUS_ORDER = {
    "offer": 0, "awarded": 0,
    "interview": 1,
    "technical": 1,
    "submitted": 2, "applied": 2,
    "preparing": 3,
    "discovered": 4,
    "rejected": 5, "withdrawn": 5,
}


def get_all_applications() -> list[ApplicationSummary]:
    """Get a unified view of all applications."""
    apps = []

    for job in load_jobs():
        apps.append(ApplicationSummary(
            id=job.id,
            type="job",
            name=job.company,
            role=job.role,
            status=job.status,
            date=job.applied_date or "",
            url=job.url,
            priority=_infer_priority(job),
            days_since_applied=_days_since(job.applied_date),
        ))

    for sch in load_scholarships():
        apps.append(ApplicationSummary(
            id=sch.id,
            type="scholarship",
            name=sch.name,
            role=sch.degree_level or "",
            status=sch.status,
            date=sch.applied_date or "",
            url=sch.url,
            priority=_infer_priority_sch(sch),
            days_since_applied=_days_since(sch.applied_date),
        ))

    return sorted(apps, key=lambda a: a.date, reverse=True)


def get_filtered_applications(
    type_filter: str = "",  # "job", "scholarship", or "" for all
    status_filter: str = "",
) -> list[ApplicationSummary]:
    """Get filtered applications."""
    apps = get_all_applications()
    if type_filter:
        apps = [a for a in apps if a.type == type_filter]
    if status_filter:
        apps = [a for a in apps if a.status == status_filter]
    return apps


def get_pipeline_stats() -> dict[str, Any]:
    """Get pipeline conversion statistics."""
    jobs = load_jobs()
    scholarships = load_scholarships()

    job_statuses = {}
    for j in jobs:
        job_statuses[j.status] = job_statuses.get(j.status, 0) + 1

    sch_statuses = {}
    for s in scholarships:
        sch_statuses[s.status] = sch_statuses.get(s.status, 0) + 1

    # Pipeline stages
    job_pipeline = _build_pipeline(jobs)
    sch_pipeline = _build_pipeline_sch(scholarships)

    return {
        "jobs": {
            "total": len(jobs),
            "by_status": job_statuses,
            "pipeline": job_pipeline,
        },
        "scholarships": {
            "total": len(scholarships),
            "by_status": sch_statuses,
            "pipeline": sch_pipeline,
        },
        "combined_total": len(jobs) + len(scholarships),
    }


def get_upcoming_actions(days: int = 14) -> list[dict[str, Any]]:
    """Get actions needed in the next N days (deadlines, interviews, etc.)."""
    actions = []
    from datetime import datetime, timedelta

    cutoff = datetime.now() + timedelta(days=days)

    # Job applications: check for interviews (status=interview means action needed)
    for job in load_jobs():
        if job.status in ("interview", "technical"):
            actions.append({
                "type": "job",
                "name": f"{job.role} at {job.company}",
                "action": f"Interview in progress ({job.status})",
                "date": job.applied_date or "",
                "days_until": 0,
            })

    for sch in load_scholarships():
        if sch.deadline:
            try:
                deadline = datetime.strptime(sch.deadline, "%Y-%m-%d")
                if deadline <= cutoff:
                    actions.append({
                        "type": "scholarship",
                        "name": sch.name,
                        "action": f"Deadline: {sch.degree_level or 'Apply'}",
                        "date": sch.deadline,
                        "days_until": (deadline - datetime.now()).days,
                    })
            except (ValueError, TypeError):
                pass

    return sorted(actions, key=lambda a: a.get("days_until", 99))


def _build_pipeline(jobs: list) -> list[dict[str, Any]]:
    """Build job pipeline visualization data."""
    stages = ["discovered", "applied", "interview", "offer", "rejected"]
    pipeline = []
    for stage in stages:
        count = sum(1 for j in jobs if j.status == stage)
        pipeline.append({"stage": stage, "count": count})
    return pipeline


def _build_pipeline_sch(scholarships: list) -> list[dict[str, Any]]:
    """Build scholarship pipeline visualization data."""
    stages = ["discovered", "preparing", "submitted", "interview", "awarded", "rejected"]
    pipeline = []
    for stage in stages:
        count = sum(1 for s in scholarships if s.status == stage)
        pipeline.append({"stage": stage, "count": count})
    return pipeline


def _infer_priority(job) -> str:
    """Infer priority from job application status and engagement."""
    if job.status in ("interview", "offer", "technical"):
        return "high"
    if job.status in ("applied", "submitted"):
        return "medium"
    return "low"


def _infer_priority_sch(sch) -> str:
    """Infer priority from scholarship status."""
    if sch.status in ("interview", "awarded"):
        return "high"
    if sch.status in ("submitted", "preparing"):
        return "medium"
    return "low"


def _days_since(date_str: str | None) -> int:
    """Calculate days since a date string."""
    if not date_str:
        return 0
    try:
        from datetime import datetime
        date = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return (datetime.now() - date).days
    except (ValueError, TypeError):
        return 0
