"""
NORAY — Scholarships API Routes

Endpoints for scholarship search, evaluation, and application.
"""

from fastapi import APIRouter

from noray.shared.profile_store import load_profile
from noray.api.schemas import ScholarshipSearchRequest, ScholarshipSearchResponse, ScholarshipApplyRequest
from noray.dashboard.scholarships import load_applications, get_upcoming_deadlines, add_application, ScholarshipApplication

router = APIRouter()


@router.post("/search", response_model=ScholarshipSearchResponse)
async def search_scholarships_endpoint(request: ScholarshipSearchRequest):
    """Search for scholarships matching the profile."""
    from noray.scholarship_agent.scholarship_search import search_scholarships
    profile = load_profile()
    result = search_scholarships(
        profile.model_dump(mode="json"),
        target_degree=request.target_degree,
        target_country=request.target_country,
        research_area=request.research_area,
    )
    return ScholarshipSearchResponse(
        scholarships=[vars(s) for s in result.scholarships],
        total_found=result.total_found,
    )


@router.post("/apply")
async def apply_scholarship(request: ScholarshipApplyRequest):
    """Generate scholarship application materials (SOP, motivation letter, research proposal)."""
    from noray.scholarship_agent.sop_generator import generate_sop
    from noray.scholarship_agent.motivation_letter import generate_motivation_letter
    from noray.scholarship_agent.research_proposal import generate_research_proposal
    from noray.shared.models import CareerProfile

    profile = load_profile()
    results = {}

    if request.generate_sop:
        sop = generate_sop(profile, request.scholarship_info, request.research_interests if hasattr(request, 'research_interests') else [])
        results["sop"] = {"content": sop.content, "word_count": sop.word_count, "sections": sop.sections}

    if request.generate_motivation:
        motivation = generate_motivation_letter(profile, request.scholarship_info)
        results["motivation_letter"] = {"content": motivation.content, "word_count": motivation.word_count}

    if request.generate_research_proposal:
        interests = profile.scholarship_goals.research_interests if profile.scholarship_goals else []
        proposal = generate_research_proposal(profile, request.scholarship_info, interests)
        results["research_proposal"] = {"content": proposal.content, "word_count": proposal.word_count, "title": proposal.title}

    # Track the application
    app = add_application(ScholarshipApplication(
        name=request.scholarship_name,
        status="preparing",
    ))

    return {"status": "generated", "application_id": app.id, "results": results}


@router.get("/tracker")
async def get_scholarship_tracker():
    """Get all tracked scholarship applications."""
    applications = load_applications()
    upcoming = get_upcoming_deadlines()
    return {
        "applications": [vars(a) for a in applications],
        "upcoming_deadlines": [vars(a) for a in upcoming],
    }


@router.get("/deadlines")
async def get_deadlines(days: int = 30):
    """Get scholarships with upcoming deadlines."""
    upcoming = get_upcoming_deadlines(days)
    return {"deadlines": [vars(a) for a in upcoming]}
