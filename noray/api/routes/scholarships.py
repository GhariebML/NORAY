"""
NORAY — AI-Powered Scholarships API Routes

Endpoints for AI-driven scholarship search, eligibility analysis,
and document generation.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from noray.api.schemas import ScholarshipApplyRequest, ScholarshipSearchRequest, ScholarshipSearchResponse
from noray.dashboard.scholarships import (
    ScholarshipApplication,
    add_application,
    get_upcoming_deadlines,
    load_applications,
)
from noray.shared.profile_store import load_profile

router = APIRouter()


class AIScholarshipSearchRequest(BaseModel):
    query: str


class AIEligibilityRequest(BaseModel):
    name: str
    provider: str = ""
    country: str = ""
    degree_level: str = ""
    funding: str = ""
    description: str = ""
    official_url: str = ""


@router.post("/search", response_model=ScholarshipSearchResponse)
async def search_scholarships(request: ScholarshipSearchRequest):
    """Search for scholarships matching the profile (legacy)."""
    from noray.scholarship_agent.scholarship_search import search_scholarships as _search_scholarships
    profile = load_profile()
    result = _search_scholarships(
        profile.model_dump(mode="json"),
        target_degree=request.target_degree,
        target_country=request.target_country,
        research_area=request.research_area,
    )
    return ScholarshipSearchResponse(
        scholarships=[vars(s) for s in result.scholarships],
        total_found=result.total_found,
    )


@router.post("/ai-search")
async def ai_scholarship_search(request: AIScholarshipSearchRequest):
    """
    AI-powered scholarship search with intent parsing and eligibility analysis.
    """
    from noray.scholarship_agent.ai_scholarship_search import full_ai_scholarship_search
    profile = load_profile()
    result = await full_ai_scholarship_search(
        query=request.query,
        profile=profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile,
    )
    return result


@router.post("/parse-intent")
async def parse_scholarship_intent(request: AIScholarshipSearchRequest):
    """Parse a natural language scholarship query into structured intent."""
    from noray.scholarship_agent.ai_scholarship_search import parse_scholarship_intent
    profile = load_profile()
    intent = await parse_scholarship_intent(
        request.query,
        profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile,
    )
    from dataclasses import asdict
    return {"status": "parsed", "intent": asdict(intent)}


@router.post("/ai-eligibility")
async def analyze_eligibility(request: AIEligibilityRequest):
    """Run AI-based eligibility analysis for a scholarship."""
    from noray.scholarship_agent.ai_scholarship_search import analyze_eligibility, ScholarshipEligibility

    profile = load_profile()
    profile_dict = profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile

    sch = {
        "name": request.name,
        "provider": request.provider,
        "country": request.country,
        "degrees": [request.degree_level] if request.degree_level else [],
        "funding": request.funding,
        "description": request.description or f"{request.name} at {request.provider}",
    }

    result = await analyze_eligibility(sch, profile_dict)

    from dataclasses import asdict
    return {"status": "analyzed", "eligibility": asdict(result)}


@router.post("/apply")
async def apply_scholarship(request: ScholarshipApplyRequest):
    """Generate SOP, motivation letter, research proposal for a scholarship."""
    from noray.document_generator.service import generate_document

    profile = load_profile()
    profile_str = str(profile.model_dump(mode="json")) if hasattr(profile, "model_dump") else str(profile)
    target = f"{request.scholarship_name} at {request.country}"
    context = f"Degree: {request.degree_level}, Research: {request.research_area}"

    results = {}

    if request.generate_sop:
        sop = await generate_document("statement_of_purpose", target, profile_str, context)
        results["sop"] = {"length": len(sop), "content_preview": sop[:500]}

    if request.generate_motivation:
        mot = await generate_document("motivation_letter", target, profile_str, context)
        results["motivation_letter"] = {"length": len(mot), "content_preview": mot[:500]}

    if request.generate_research:
        rp = await generate_document("research_proposal", target, profile_str, context)
        results["research_proposal"] = {"length": len(rp), "content_preview": rp[:500]}

    if request.generate_email:
        email = await generate_document(
            "email",
            f"Professor inquiry for {target}",
            profile_str,
            context,
        )
        results["email"] = {"length": len(email), "content_preview": email[:500]}

    app = add_application(ScholarshipApplication(
        name=request.scholarship_name,
        provider=request.provider,
        country=request.country,
        degree_level=request.degree_level,
        status="applied",
    ))

    return {
        "status": "generated",
        "application_id": app.id,
        "results": results,
    }


@router.get("/tracker")
async def get_scholarship_tracker():
    """Get all tracked scholarship applications."""
    applications = load_applications()
    return {
        "applications": [vars(a) for a in applications],
    }


@router.get("/deadlines")
async def get_scholarship_deadlines(days: int = 30):
    """Get scholarships with upcoming deadlines."""
    deadlines = get_upcoming_deadlines(days)
    return {
        "deadlines": deadlines,
    }
