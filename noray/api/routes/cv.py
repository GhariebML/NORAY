"""
NORAY — CV API Routes

Endpoints for CV generation and ATS optimization.
"""

from fastapi import APIRouter

from noray.api.schemas import CVGenerateRequest, CVOptimizeRequest

router = APIRouter()


@router.post("/generate")
async def generate_cv(request: CVGenerateRequest):
    """Generate a tailored CV for a specific job."""
    # TODO: Implement using career_agent.cv_optimizer
    return {"status": "not_implemented", "message": "CV generation coming in Phase 2"}


@router.post("/optimize")
async def optimize_cv(request: CVOptimizeRequest):
    """Analyze and optimize a CV for ATS compatibility."""
    from noray.career_agent.ats_analyzer import analyze_cv_ats
    score = analyze_cv_ats(request.cv_text, request.job_keywords)
    return {
        "overall_score": score.overall_score,
        "formatting_score": score.formatting_score,
        "keyword_score": score.keyword_score,
        "structure_score": score.structure_score,
        "issues": score.issues,
        "recommendations": score.recommendations,
        "keywords_found": score.keywords_found,
        "keywords_missing": score.keywords_missing,
    }
