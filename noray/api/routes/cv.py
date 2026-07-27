"""
NORAY — AI Document Generation API Routes

Endpoints for AI-powered document generation with quality checks, streaming,
and multi-document type support. All generation through SmartRouter.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from noray.shared.profile_store import load_profile

logger = logging.getLogger("noray.api.routes.cv")

router = APIRouter()


class GenerateDocumentRequest(BaseModel):
    doc_type: str = "ats_resume"
    target: str = ""
    context: str = ""
    session_id: str = ""
    run_quality_check: bool = True


class GenerateSopRequest(BaseModel):
    scholarship_name: str = ""
    university: str = ""
    program: str = ""
    research_interests: str = ""
    word_limit: int = 1000
    context: str = ""
    session_id: str = ""


class GenerateMotivationRequest(BaseModel):
    scholarship_name: str = ""
    program: str = ""
    word_limit: int = 800
    context: str = ""
    session_id: str = ""


class GenerateResearchRequest(BaseModel):
    scholarship_name: str = ""
    university: str = ""
    program: str = ""
    research_topics: str = ""
    word_limit: int = 2000
    context: str = ""
    session_id: str = ""


@router.post("/generate")
async def generate_document(request: GenerateDocumentRequest):
    """Generate an AI document with optional quality check."""
    from noray.document_generator.service import generate_with_quality, get_rag_context

    profile = load_profile()
    profile_str = str(profile.model_dump(mode="json")) if hasattr(profile, "model_dump") else str(profile)

    rag_context = await get_rag_context(request.target)
    full_context = f"{request.context}\n\nRetrieved Knowledge:\n{rag_context}".strip()

    result = await generate_with_quality(
        doc_type=request.doc_type,
        target=request.target,
        profile_str=profile_str,
        context=full_context,
        session_id=request.session_id,
    )

    return result


@router.post("/stream")
async def stream_document(request: GenerateDocumentRequest):
    """Stream an AI-generated document via SSE."""
    from noray.document_generator.service import stream_document, get_rag_context

    profile = load_profile()
    profile_str = str(profile.model_dump(mode="json")) if hasattr(profile, "model_dump") else str(profile)

    rag_context = await get_rag_context(request.target)
    full_context = f"{request.context}\n\nRetrieved Knowledge:\n{rag_context}".strip()

    async def event_stream():
        doc_type_label = request.doc_type.replace("_", " ").title()
        yield f"data: {json.dumps({'type': 'start', 'doc_type': request.doc_type, 'label': doc_type_label})}\n\n"

        full = ""
        async for chunk in stream_document(
            doc_type=request.doc_type,
            target=request.target,
            profile_str=profile_str,
            context=full_context,
            session_id=request.session_id,
        ):
            if chunk:
                full += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'length': len(full)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/quality")
async def check_document_quality(request: GenerateDocumentRequest):
    """Run AI quality check on existing document content."""
    from noray.document_generator.service import check_quality

    if not request.target:
        return {"status": "error", "message": "Provide document content in 'target'"}

    report = await check_quality(request.target, request.doc_type)
    from dataclasses import asdict
    return {"status": "checked", "report": asdict(report)}


@router.post("/sop")
async def generate_sop(request: GenerateSopRequest):
    """Generate a Statement of Purpose."""
    from noray.document_generator.service import generate_with_quality

    profile = load_profile()
    profile_str = str(profile.model_dump(mode="json")) if hasattr(profile, "model_dump") else str(profile)

    target = f"{request.program} at {request.university}" if request.university else request.scholarship_name
    context = f"Research Interests: {request.research_interests}\n{request.context}"

    result = await generate_with_quality(
        doc_type="statement_of_purpose",
        target=target,
        profile_str=profile_str,
        context=context,
        session_id=request.session_id,
    )

    return result


@router.post("/motivation")
async def generate_motivation(request: GenerateMotivationRequest):
    """Generate a Motivation Letter."""
    from noray.document_generator.service import generate_with_quality

    profile = load_profile()
    profile_str = str(profile.model_dump(mode="json")) if hasattr(profile, "model_dump") else str(profile)

    target = f"{request.scholarship_name} - {request.program}"
    context = request.context

    result = await generate_with_quality(
        doc_type="motivation_letter",
        target=target,
        profile_str=profile_str,
        context=context,
        session_id=request.session_id,
    )

    return result


@router.post("/research")
async def generate_research(request: GenerateResearchRequest):
    """Generate a Research Proposal."""
    from noray.document_generator.service import generate_with_quality

    profile = load_profile()
    profile_str = str(profile.model_dump(mode="json")) if hasattr(profile, "model_dump") else str(profile)

    target = f"{request.scholarship_name} - {request.program} at {request.university}"
    context = f"Research Topics: {request.research_topics}\n{request.context}"

    result = await generate_with_quality(
        doc_type="research_proposal",
        target=target,
        profile_str=profile_str,
        context=context,
        session_id=request.session_id,
    )

    return result


@router.post("/email")
async def generate_email(request: GenerateDocumentRequest):
    """Generate a professional email."""
    from noray.document_generator.service import generate_with_quality

    profile = load_profile()
    profile_str = str(profile.model_dump(mode="json")) if hasattr(profile, "model_dump") else str(profile)

    result = await generate_with_quality(
        doc_type="email",
        target=request.target,
        profile_str=profile_str,
        context=request.context,
        session_id=request.session_id,
    )

    return result


@router.post("/linkedin")
async def generate_linkedin(request: GenerateDocumentRequest):
    """Generate a LinkedIn summary."""
    from noray.document_generator.service import generate_with_quality

    profile = load_profile()
    profile_str = str(profile.model_dump(mode="json")) if hasattr(profile, "model_dump") else str(profile)

    result = await generate_with_quality(
        doc_type="linkedin_summary",
        target=request.target,
        profile_str=profile_str,
        context=request.context,
        session_id=request.session_id,
    )

    return result


@router.post("/optimize")
async def optimize_cv(request: GenerateDocumentRequest):
    """Analyze CV text for ATS compatibility (legacy)."""
    from noray.career_agent.ats_analyzer import (
        analyze_cv_ats,
        extract_keywords_from_posting,
    )

    if not request.target:
        return {"status": "error", "message": "Provide CV text in 'target'"}

    posting_keywords = extract_keywords_from_posting(request.context)
    result = analyze_cv_ats(request.target, posting_keywords)

    return {
        "status": "analyzed",
        "ats_score": result.overall_score,
        "keywords_found": result.keywords_found,
        "keywords_missing": result.keywords_missing,
    }
