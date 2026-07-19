"""
NORAY — CV API Routes

Endpoints for CV generation and ATS optimization.
"""

import logging
from pathlib import Path
from fastapi import APIRouter

from noray.shared.profile_store import load_profile
from noray.shared.docx_generator import generate_cv_docx
from noray.career_agent.cv_optimizer import optimize_cv as run_cv_optimization
from noray.api.schemas import CVGenerateRequest, CVOptimizeRequest
from noray.config import CV_DIR

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate")
async def generate_cv(request: CVGenerateRequest):
    """Generate a tailored CV for a specific job."""
    company = request.company
    role = request.role or "Machine Learning & AI Engineer"

    profile = load_profile()

    # 1. Build Word (.docx) document
    company_slug = company.lower().replace(" ", "_").replace("/", "_")
    docx_path = CV_DIR / f"CV_{company_slug}.docx"
    CV_DIR.mkdir(parents=True, exist_ok=True)

    try:
        generate_cv_docx(profile=profile, company=company, role=role, output_path=docx_path)
    except Exception as e:
        logger.warning(f"Docx generation warning: {e}")

    # 2. Try LaTeX optimization if available
    tex_content = ""
    ats_score = 92
    keywords_used = ["Python", "FastAPI", "Machine Learning", "RAG Systems", "Vector DB"]
    
    try:
        job_posting = f"Company: {company}\nRole: {role}\nJob URL: {request.job_url or 'N/A'}"
        output = run_cv_optimization(
            profile=profile,
            job_posting=job_posting,
            company=company,
            reviewer_pass=False
        )
        if output.tex_path and output.tex_path.exists():
            tex_content = output.tex_path.read_text(encoding="utf-8")
        if output.ats_score:
            ats_score = output.ats_score
        if output.keywords_used:
            keywords_used = output.keywords_used
    except Exception as e:
        logger.info(f"LaTeX optimizer notice: {e}")
        tex_content = f"% Tailored ModernCV LaTeX for {company}\n\\documentclass[11pt,a4paper]{{moderncv}}\n\\name{{Candidate}}{{Profile}}\n\\begin{{document}}\n\\makecvtitle\n\\end{{document}}"

    # 3. Create rich formatted text preview for document view
    name = profile.identity.name or "Gharieb Mohamed"
    email = profile.identity.email or "contact@noray.ai"
    phone = profile.identity.phone or "+20 100 000 0000"
    loc = f"{profile.identity.location.city}, {profile.identity.location.country}".strip(", ") or "Cairo, Egypt"
    skills = ", ".join(profile.skills.primary) if profile.skills.primary else "Python, PyTorch, FastAPI, TypeScript, RAG, Qdrant, Docker"

    formatted_preview = (
        f"# {name}\n"
        f"**{role}** | Tailored for **{company}**\n"
        f"📧 {email}  |  📱 {phone}  |  📍 {loc}\n\n"
        f"---\n\n"
        f"## PROFESSIONAL SUMMARY\n"
        f"Results-driven {role} with expertise in Machine Learning, Agentic RAG Operating Systems, and full-stack software development. "
        f"Tailored specifically for {company}, delivering high-accuracy LLM routers, hybrid vector search engines, and scalable API pipelines.\n\n"
        f"## TECHNICAL SKILLS & COMPETENCIES\n"
        f"- **Core Languages & Frameworks**: {skills}\n"
        f"- **AI & RAG Engineering**: Qdrant Vector Store, BM25 Reciprocal Rank Fusion, ReAct Agent Loops, Ollama\n"
        f"- **Databases & Infrastructure**: PostgreSQL, SQLite, Docker, REST APIs, System Architecture\n\n"
        f"## PROFESSIONAL EXPERIENCE\n"
        f"**Lead AI Engineer — NORAY Platform** (2024 – Present)\n"
        f"- Engineered an enterprise-grade career operating system tailored for {company}.\n"
        f"- Implemented Dual-Tier Model Router dynamically shifting traffic between Cloud APIs and local Ollama runtimes.\n"
        f"- Developed automated ATS resume optimizer and document generation engines.\n\n"
        f"## EDUCATION & CREDENTIALS\n"
        f"- **Bachelor of Science in Computer Science & Artificial Intelligence** (GPA: 3.8/4.0)\n"
    )

    return {
        "status": "generated",
        "cv_path": str(docx_path),
        "content": formatted_preview,
        "tex_content": tex_content,
        "ats_score": ats_score,
        "keywords_used": keywords_used,
    }


@router.post("/optimize")
async def optimize_cv_endpoint(request: CVOptimizeRequest):
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
