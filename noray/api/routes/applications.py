"""
NORAY — Applications API Routes

Unified application tracking endpoints.
"""

from fastapi import APIRouter

from noray.dashboard.applications import get_all_applications, get_pipeline_stats

router = APIRouter()


@router.get("")
async def get_applications():
    """Get all applications (jobs + scholarships) in a unified view."""
    applications = get_all_applications()
    stats = get_pipeline_stats()
    return {
        "applications": [vars(a) for a in applications],
        "stats": stats,
    }


@router.get("/analytics")
async def get_analytics():
    """Get application analytics and statistics."""
    from noray.dashboard.analytics import get_analytics_summary
    return get_analytics_summary()
