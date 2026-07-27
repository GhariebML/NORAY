"""
NORAY — AI-Powered Jobs API Routes

Endpoints for AI-driven job search, intent parsing, scoring, and application.
All generation routes through the SmartRouter.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from noray.api.schemas import JobApplyRequest, JobEvaluateRequest, JobSearchRequest, JobSearchResponse
from noray.dashboard.jobs import JobApplication, add_application, get_application_stats, load_applications
from noray.shared.profile_store import load_profile

router = APIRouter()


class AIJobSearchRequest(BaseModel):
    query: str
    max_results: int = 30


class AIJobScoreRequest(BaseModel):
    company: str
    role: str
    country: str = ""
    description: str = ""


@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """Search for jobs matching the profile (legacy provider-based)."""
    from noray.career_agent.job_search import search_jobs
    profile = load_profile()
    result = await search_jobs(
        profile.model_dump(mode="json"),
        focus_area=request.focus_area,
        broad=request.broad,
    )
    return JobSearchResponse(
        jobs=[vars(j) for j in result.jobs],
        total_found=result.total_found,
        new_count=result.new_count,
    )


@router.post("/ai-search")
async def ai_job_search(request: AIJobSearchRequest):
    """
    AI-powered job search with intent parsing, query expansion,
    multi-provider fetch, and AI scoring.
    """
    from noray.career_agent.ai_job_search import full_ai_job_search
    profile = load_profile()
    result = await full_ai_job_search(
        query=request.query,
        profile=profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile,
        max_results=request.max_results,
    )
    return result


@router.post("/parse-intent")
async def parse_job_intent(request: AIJobSearchRequest):
    """Parse a natural language job search query into structured intent."""
    from noray.career_agent.ai_job_search import parse_job_intent
    profile = load_profile()
    intent = await parse_job_intent(
        request.query,
        profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile,
    )
    from dataclasses import asdict
    return {"status": "parsed", "intent": asdict(intent)}


@router.post("/ai-score")
async def score_job_ai_endpoint(request: AIJobScoreRequest):
    """AI-based job fit scoring against user profile."""
    from noray.career_agent.ai_job_search import AIJobResult, score_job_ai

    profile = load_profile()
    profile_dict = profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile

    job = AIJobResult(
        company=request.company,
        role=request.role,
        country=request.country,
        description=request.description,
    )

    score = await score_job_ai(job, profile_dict)
    from dataclasses import asdict
    return {"status": "scored", "score": asdict(score)}


@router.post("/evaluate")
async def evaluate_job(request: JobEvaluateRequest):
    """Evaluate a job posting against the profile (legacy ATS analyzer)."""
    from noray.career_agent.ats_analyzer import (
        analyze_cv_ats,
        extract_keywords_from_posting,
        generate_optimization_report,
    )

    profile = load_profile()
    profile_dict = profile.model_dump(mode="json")

    if not request.job_text:
        return {"status": "error", "message": "Provide job_text"}

    posting_keywords = extract_keywords_from_posting(request.job_text)
    profile_skills = []
    skills_data = profile_dict.get("skills", {})
    for cat in ["primary", "secondary", "domain", "tools"]:
        profile_skills.extend(skills_data.get(cat, []))

    result = analyze_cv_ats(" ".join(profile_skills), posting_keywords)
    report = generate_optimization_report(result)

    return {
        "status": "analyzed",
        "score": result.overall_score,
        "breakdown": {
            "structure": result.structure_score,
            "content": result.content_score,
            "keywords": result.keyword_score,
            "format": result.formatting_score,
        },
        "matched_keywords": result.keywords_found,
        "missing_keywords": result.keywords_missing,
        "posting_keywords": posting_keywords,
        "report": report,
    }


@router.post("/apply")
async def apply_job(request: JobApplyRequest):
    """Generate job application materials."""
    from noray.career_agent.cover_letter_generator import generate_cover_letter
    from noray.career_agent.cv_optimizer import optimize_cv
    from noray.document_generator.service import generate_document

    profile = load_profile()
    results = {}

    if request.generate_cv:
        try:
            ai_cv = await generate_document(
                doc_type="ats_resume",
                target=request.job_text or request.role,
                profile_str=str(profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile),
                context=f"Company: {request.company}, Role: {request.role}",
            )
            results["ai_cv"] = {"content_preview": ai_cv[:500], "length": len(ai_cv)}
        except Exception:
            cv_result = optimize_cv(profile, request.job_text or "", request.company)
            results["cv"] = {"latex": cv_result.tex_path, "success": cv_result.success, "ats_score": cv_result.ats_score}

    if request.generate_cover_letter:
        try:
            ai_cl = await generate_document(
                doc_type="cover_letter",
                target=f"{request.company} - {request.role}",
                profile_str=str(profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile),
                context=request.job_text or "",
            )
            results["ai_cover_letter"] = {"content_preview": ai_cl[:500], "length": len(ai_cl)}
        except Exception:
            cl_result = generate_cover_letter(profile, request.job_text or "", request.company, request.role)
            results["cover_letter"] = {"latex": cl_result.tex_path, "success": cl_result.success}

    app = add_application(JobApplication(
        company=request.company,
        role=request.role,
        url=request.job_url,
        status="applied",
    ))

    return {
        "status": "generated",
        "application_id": app.id,
        "results": results,
    }


@router.get("/tracker")
async def get_job_tracker():
    """Get all tracked job applications."""
    applications = load_applications()
    stats = get_application_stats()
    return {
        "applications": [vars(a) for a in applications],
        "stats": stats,
    }
