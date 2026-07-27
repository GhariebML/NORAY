"""
NORAY — Analytics

Application statistics, timeline visualization data, success rates,
skill gap trends, and pipeline conversion rates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from noray.dashboard.jobs import load_applications as load_jobs
from noray.dashboard.scholarships import load_applications as load_scholarships


@dataclass
class AnalyticsSummary:
    """Structured analytics result."""
    jobs: dict[str, Any] = field(default_factory=dict)
    scholarships: dict[str, Any] = field(default_factory=dict)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    monthly_activity: dict[str, int] = field(default_factory=dict)


def get_analytics_summary() -> dict[str, Any]:
    """Get a comprehensive analytics summary."""
    jobs = load_jobs()
    scholarships = load_scholarships()

    # Job analytics
    job_response_rate = _calculate_response_rate(jobs)
    job_avg_days = _avg_days_to_response(jobs)
    job_interview_rate = _calculate_interview_rate(jobs)
    job_offer_rate = _calculate_offer_rate(jobs)

    # Scholarship analytics
    sch_success_rate = _calculate_award_rate(scholarships)
    sch_response_rate = _calculate_sch_response_rate(scholarships)

    # Timeline
    timeline = _build_timeline(jobs, scholarships)
    monthly = _build_monthly_activity(jobs, scholarships)

    # Generate insights
    insights = _generate_insights(jobs, scholarships, job_response_rate, sch_success_rate)

    return {
        "jobs": {
            "total_applied": len([j for j in jobs if j.status != "discovered"]),
            "total_tracked": len(jobs),
            "response_rate": round(job_response_rate, 2),
            "avg_days_to_response": round(job_avg_days, 1),
            "interview_rate": round(job_interview_rate, 2),
            "offer_rate": round(job_offer_rate, 2),
            "by_status": _count_by_status(jobs),
            "response_time_distribution": _response_time_distribution(jobs),
        },
        "scholarships": {
            "total_applied": len([s for s in scholarships if s.status not in ("discovered", "preparing")]),
            "total_tracked": len(scholarships),
            "success_rate": round(sch_success_rate, 2),
            "response_rate": round(sch_response_rate, 2),
            "upcoming_deadlines": _count_upcoming_deadlines(scholarships, days=30),
            "by_status": _count_by_status_sch(scholarships),
        },
        "timeline": timeline,
        "monthly_activity": monthly,
        "insights": insights,
        "conversion_funnel": _build_conversion_funnel(jobs, scholarships),
    }


def get_dashboard_summary() -> dict[str, Any]:
    """Get a compact dashboard summary for display."""
    analytics = get_analytics_summary()
    return {
        "total_applications": analytics["jobs"]["total_tracked"] + analytics["scholarships"]["total_tracked"],
        "active_applications": (
            analytics["jobs"]["total_applied"] + analytics["scholarships"]["total_applied"]
        ),
        "interview_rate": analytics["jobs"]["interview_rate"],
        "response_rate": analytics["jobs"]["response_rate"],
        "scholarship_success_rate": analytics["scholarships"]["success_rate"],
        "upcoming_deadlines": analytics["scholarships"]["upcoming_deadlines"],
        "top_insights": analytics["insights"][:3],
    }


def format_analytics(analytics: dict[str, Any]) -> str:
    """Format analytics as readable markdown."""
    lines = ["# Analytics Dashboard", ""]

    # Jobs section
    j = analytics["jobs"]
    lines.append("## Job Applications")
    lines.append(f"- Total tracked: {j['total_tracked']}")
    lines.append(f"- Applied: {j['total_applied']}")
    lines.append(f"- Response rate: {j['response_rate']:.0%}")
    lines.append(f"- Interview rate: {j['interview_rate']:.0%}")
    lines.append(f"- Offer rate: {j['offer_rate']:.0%}")
    lines.append(f"- Avg days to response: {j['avg_days_to_response']:.0f} days")
    lines.append("")

    # Status breakdown
    if j.get("by_status"):
        lines.append("### Job Status Breakdown")
        for status, count in sorted(j["by_status"].items()):
            lines.append(f"- {status}: {count}")
        lines.append("")

    # Scholarships section
    s = analytics["scholarships"]
    lines.append("## Scholarship Applications")
    lines.append(f"- Total tracked: {s['total_tracked']}")
    lines.append(f"- Applied: {s['total_applied']}")
    lines.append(f"- Success rate: {s['success_rate']:.0%}")
    lines.append(f"- Upcoming deadlines (30 days): {s['upcoming_deadlines']}")
    lines.append("")

    # Insights
    if analytics.get("insights"):
        lines.append("## Insights")
        for insight in analytics["insights"]:
            lines.append(f"- {insight}")
        lines.append("")

    # Monthly activity
    if analytics.get("monthly_activity"):
        lines.append("## Monthly Activity")
        for month, count in sorted(analytics["monthly_activity"].items(), reverse=True)[:6]:
            bar = "█" * min(count, 20)
            lines.append(f"- {month}: {bar} ({count})")
        lines.append("")

    return "\n".join(lines)


# ─── Internal helpers ─────────────────────────────────────────

def _calculate_response_rate(jobs: list) -> float:
    """Calculate the response rate for job applications."""
    applied = [j for j in jobs if j.status != "discovered"]
    responded = [j for j in applied if j.status not in ("applied",)]
    return len(responded) / max(len(applied), 1)


def _calculate_interview_rate(jobs: list) -> float:
    """Calculate interview rate."""
    applied = [j for j in jobs if j.status not in ("discovered",)]
    interviews = [j for j in jobs if j.status in ("interview", "technical", "offer")]
    return len(interviews) / max(len(applied), 1)


def _calculate_offer_rate(jobs: list) -> float:
    """Calculate offer rate."""
    applied = [j for j in jobs if j.status not in ("discovered",)]
    offers = [j for j in jobs if j.status == "offer"]
    return len(offers) / max(len(applied), 1)


def _calculate_award_rate(scholarships: list) -> float:
    """Calculate scholarship award rate."""
    submitted = [s for s in scholarships if s.status not in ("discovered", "preparing")]
    awarded = [s for s in scholarships if s.status == "awarded"]
    return len(awarded) / max(len(submitted), 1)


def _calculate_sch_response_rate(scholarships: list) -> float:
    """Calculate scholarship response rate."""
    submitted = [s for s in scholarships if s.status not in ("discovered", "preparing")]
    responded = [s for s in submitted if s.status not in ("submitted",)]
    return len(responded) / max(len(submitted), 1)


def _avg_days_to_response(jobs: list) -> float:
    """Calculate average days from application to first response."""
    days = []
    for job in jobs:
        if job.applied_date and job.status not in ("applied", "discovered"):
            try:
                applied = datetime.strptime(job.applied_date, "%Y-%m-%d")
                updated = datetime.strptime(job.last_updated[:10], "%Y-%m-%d")
                days.append((updated - applied).days)
            except (ValueError, TypeError):
                pass
    return sum(days) / len(days) if days else 0


def _response_time_distribution(jobs: list) -> dict[str, int]:
    """Get distribution of response times."""
    buckets = {"same_day": 0, "1-3_days": 0, "4-7_days": 0, "8-14_days": 0, "14+_days": 0}
    for job in jobs:
        if job.applied_date and job.status not in ("applied", "discovered"):
            try:
                applied = datetime.strptime(job.applied_date, "%Y-%m-%d")
                updated = datetime.strptime(job.last_updated[:10], "%Y-%m-%d")
                diff = (updated - applied).days
                if diff == 0:
                    buckets["same_day"] += 1
                elif diff <= 3:
                    buckets["1-3_days"] += 1
                elif diff <= 7:
                    buckets["4-7_days"] += 1
                elif diff <= 14:
                    buckets["8-14_days"] += 1
                else:
                    buckets["14+_days"] += 1
            except (ValueError, TypeError):
                pass
    return buckets


def _count_by_status(jobs: list) -> dict[str, int]:
    """Count jobs by status."""
    counts = {}
    for j in jobs:
        counts[j.status] = counts.get(j.status, 0) + 1
    return counts


def _count_by_status_sch(scholarships: list) -> dict[str, int]:
    """Count scholarships by status."""
    counts = {}
    for s in scholarships:
        counts[s.status] = counts.get(s.status, 0) + 1
    return counts


def _count_upcoming_deadlines(scholarships: list, days: int = 30) -> int:
    """Count scholarships with deadlines in the next N days."""
    cutoff = datetime.now() + timedelta(days=days)
    count = 0
    for s in scholarships:
        if s.deadline and s.status in ("discovered", "preparing"):
            try:
                deadline = datetime.strptime(s.deadline, "%Y-%m-%d")
                if deadline <= cutoff:
                    count += 1
            except (ValueError, TypeError):
                pass
    return count


def _build_timeline(jobs: list, scholarships: list) -> list[dict]:
    """Build a timeline of application events."""
    events = []

    for job in jobs:
        if job.applied_date:
            events.append({
                "date": job.applied_date,
                "type": "job_applied",
                "name": f"{job.role} at {job.company}",
                "status": job.status,
            })

    for sch in scholarships:
        if sch.applied_date:
            events.append({
                "date": sch.applied_date,
                "type": "scholarship_applied",
                "name": sch.name,
                "status": sch.status,
            })

    return sorted(events, key=lambda e: e["date"], reverse=True)


def _build_monthly_activity(jobs: list, scholarships: list) -> dict[str, int]:
    """Build monthly application activity counts."""
    monthly = {}
    for job in jobs:
        if job.applied_date:
            month = job.applied_date[:7]  # YYYY-MM
            monthly[month] = monthly.get(month, 0) + 1
    for sch in scholarships:
        if sch.applied_date:
            month = sch.applied_date[:7]
            monthly[month] = monthly.get(month, 0) + 1
    return monthly


def _build_conversion_funnel(jobs: list, scholarships: list) -> dict[str, Any]:
    """Build conversion funnel data."""
    job_total = len([j for j in jobs if j.status != "discovered"])
    job_interviews = len([j for j in jobs if j.status in ("interview", "technical")])
    job_offers = len([j for j in jobs if j.status == "offer"])

    sch_total = len([s for s in scholarships if s.status not in ("discovered",)])
    sch_submitted = len([s for s in scholarships if s.status in ("submitted",)])
    sch_interviews = len([s for s in scholarships if s.status == "interview"])
    sch_awarded = len([s for s in scholarships if s.status == "awarded"])

    return {
        "jobs": {
            "applied": job_total,
            "interviewed": job_interviews,
            "offered": job_offers,
        },
        "scholarships": {
            "applied": sch_total,
            "submitted": sch_submitted,
            "interviewed": sch_interviews,
            "awarded": sch_awarded,
        },
    }


def _generate_insights(
    jobs: list,
    scholarships: list,
    job_response_rate: float,
    sch_success_rate: float,
) -> list[str]:
    """Generate actionable insights from analytics."""
    insights = []

    total_applied = len([j for j in jobs if j.status != "discovered"])
    if total_applied == 0:
        insights.append("No applications tracked yet. Start by running /find_jobs or /find_scholarships.")
        return insights

    # Response rate insight
    if job_response_rate < 0.3:
        insights.append("Low response rate (<30%). Consider optimizing your CV and cover letter with /apply_job.")
    elif job_response_rate > 0.5:
        insights.append(f"Strong response rate ({job_response_rate:.0%}). Your application materials are working.")

    # Interview rate insight
    interview_rate = _calculate_interview_rate(jobs)
    if interview_rate < 0.1 and total_applied >= 5:
        insights.append("Few interviews so far. Practice with /interview to improve your interview skills.")

    # Offer insight
    offers = len([j for j in jobs if j.status == "offer"])
    if offers > 0:
        insights.append(f"Congratulations! {offers} offer(s) received. Review them carefully.")

    # Scholarship insights
    sch_applied = len([s for s in scholarships if s.status not in ("discovered",)])
    if sch_applied == 0:
        insights.append("No scholarship applications yet. Run /find_scholarships to explore opportunities.")

    if sch_success_rate > 0:
        insights.append(f"Scholarship success rate: {sch_success_rate:.0%}. Keep up the good work!")

    # Stale applications
    stale_count = 0
    for job in jobs:
        if job.status == "applied" and job.last_updated:
            try:
                updated = datetime.strptime(job.last_updated[:10], "%Y-%m-%d")
                if (datetime.now() - updated).days > 14:
                    stale_count += 1
            except (ValueError, TypeError):
                pass
    if stale_count > 0:
        insights.append(f"{stale_count} application(s) haven't been updated in 14+ days. Consider following up.")

    # Response time
    avg_days = _avg_days_to_response(jobs)
    if avg_days > 0:
        if avg_days < 7:
            insights.append(f"Fast response times (avg {avg_days:.0f} days). Your applications are getting attention.")
        elif avg_days > 21:
            insights.append(f"Slow response times (avg {avg_days:.0f} days). Be patient, but consider following up.")

    if not insights:
        insights.append("Keep tracking applications to get personalized insights.")

    return insights
