"""
NORAY — Jobs API Routes

Endpoints for job search, evaluation, and application.
"""

from fastapi import APIRouter

from noray.shared.profile_store import load_profile
from noray.api.schemas import JobSearchRequest, JobSearchResponse, JobEvaluateRequest, JobApplyRequest
from noray.dashboard.jobs import load_applications, get_application_stats, add_application, JobApplication

router = APIRouter()


@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """Search for jobs matching the profile."""
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


@router.post("/evaluate")
async def evaluate_job(request: JobEvaluateRequest):
    """Evaluate a job posting against the profile."""
    from noray.career_agent.ats_analyzer import analyze_cv_ats, extract_keywords_from_posting, generate_optimization_report

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
    """Generate a job application (CV + cover letter)."""
    from noray.career_agent.cv_optimizer import optimize_cv
    from noray.career_agent.cover_letter_generator import generate_cover_letter

    profile = load_profile()

    results = {}

    if request.generate_cv:
        cv_result = optimize_cv(profile, request.job_text or "", request.company)
        results["cv"] = {"latex": cv_result.tex_path, "success": cv_result.success, "ats_score": cv_result.ats_score}

    if request.generate_cover_letter:
        cl_result = generate_cover_letter(profile, request.job_text or "", request.company, request.role)
        results["cover_letter"] = {"latex": cl_result.tex_path, "success": cl_result.success, "language": cl_result.language}

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
