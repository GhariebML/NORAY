"""
NORAY — AI Document Generator

AI-powered document generation with RAG context, streaming support,
quality checks, and multi-document types. Everything goes through the
SmartRouter — no direct provider calls.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, AsyncGenerator

logger = logging.getLogger("noray.document_generator")

DOCUMENT_TYPES = [
    "ats_resume", "executive_resume", "academic_cv",
    "cover_letter", "statement_of_purpose", "motivation_letter",
    "research_proposal", "email", "linkedin_summary",
]

DOCUMENT_PROMPTS: dict[str, str] = {
    "ats_resume": """Generate an ATS-optimized resume section for the following context.
Job Description: {target}
Profile: {profile}
Knowledge Context: {context}

Return as structured markdown with these sections:
- Professional Summary (2-3 lines with ATS keywords)
- Technical Skills (categorized, with proficiency)
- Professional Experience (bullet points with metrics)
- Education & Certifications

Focus on matching keywords from the job description. Use action verbs and measurable achievements.""",

    "cover_letter": """Write a professional cover letter.
Target: {target}
Profile: {profile}
Context: {context}

Return a complete cover letter with:
- Professional salutation
- Opening paragraph expressing interest
- 2 body paragraphs connecting experience to requirements
- Closing with call to action
- Professional sign-off""",

    "statement_of_purpose": """Write a compelling Statement of Purpose.
Program/Scholarship: {target}
Profile: {profile}
Context: {context}

Include:
- Opening: Academic/professional journey hook
- Academic Background: Relevant coursework, research, projects
- Research/Professional Experience: Key achievements
- Why This Program: Specific alignment with program
- Future Goals: Career aspirations
- Closing: Enthusiasm and readiness""",

    "research_proposal": """Write a structured research proposal.
Topic/Program: {target}
Profile: {profile}
Context: {context}

Structure:
1. Title
2. Abstract (150 words)
3. Introduction & Background
4. Research Questions / Hypotheses
5. Literature Review
6. Methodology
7. Expected Outcomes
8. Timeline (12-36 months)
9. References""",

    "motivation_letter": """Write a motivation letter for a scholarship application.
Scholarship: {target}
Profile: {profile}
Context: {context}

Include:
- Motivation for applying
- Academic and professional background relevance
- Why you are a strong candidate
- How you will contribute
- Future plans""",

    "email": """Write a professional email.
Context: {target}
Profile: {profile}

Write a concise, professional email suitable for academic or professional correspondence.""",

    "linkedin_summary": """Write a compelling LinkedIn summary.
Profile: {profile}
Target: {target}
Context: {context}

Write a professional LinkedIn 'About' section that highlights unique value proposition, key skills, and career narrative.""",

    "executive_resume": """Generate an executive-level resume (C-suite / Director level).
Target: {target}
Profile: {profile}
Context: {context}

Sections:
- Executive Summary (strategic leader, vision, impact)
- Core Competencies (leadership, strategy, domain)
- Professional Experience (strategic achievements, team leadership)
- Board Memberships / Advisory Roles
- Education & Certifications""",

    "academic_cv": """Generate an academic CV.
Target: {target}
Profile: {profile}
Context: {context}

Sections:
- Education
- Research Experience
- Publications
- Teaching Experience
- Awards & Honors
- Professional Service
- References""",
}

QUALITY_CHECK_PROMPT = """You are an AI document quality reviewer. Analyze this generated document and return a quality assessment.

DOCUMENT TYPE: {doc_type}
DOCUMENT:
{document}

Return ONLY a valid JSON object. No markdown, no code fences, no explanation text before or after.
The JSON must contain exactly these fields with numeric scores 0-100:
{{
  "ats_score": 75,
  "grammar_score": 90,
  "keyword_coverage": 60,
  "readability_score": 85,
  "hallucination_risk": "low",
  "formatting_issues": [],
  "consistency_issues": [],
  "suggestions": ["Add more quantified achievements", "Include industry keywords from job description"],
  "overall_quality": "good",
  "improvements_needed": 2
}}"""


@dataclass
class QualityReport:
    ats_score: float = 0.0
    grammar_score: float = 0.0
    keyword_coverage: float = 0.0
    readability_score: float = 0.0
    hallucination_risk: str = "low"
    formatting_issues: list[str] = field(default_factory=list)
    consistency_issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    overall_quality: str = "fair"
    improvements_needed: int = 0


def get_document_prompt(doc_type: str, target: str, profile: str, context: str) -> str:
    """Get the appropriate prompt template for the document type."""
    template = DOCUMENT_PROMPTS.get(doc_type, DOCUMENT_PROMPTS["cover_letter"])
    return template.format(target=target, profile=profile, context=context)


async def generate_document(
    doc_type: str,
    target: str,
    profile_str: str,
    context: str = "",
    session_id: str = "",
) -> str:
    """Generate a document using AI through the SmartRouter."""
    from noray.llm.smart_router import smart_router
    from noray.llm.providers.base_provider import LLMConfig, LLMMessage

    if doc_type not in DOCUMENT_PROMPTS:
        doc_type = "cover_letter"

    prompt = get_document_prompt(doc_type, target, profile_str, context)

    system_prompt = (
        "You are an expert document writer for career and academic applications. "
        "Write professional, tailored documents. Use precise language and measurable achievements. "
        "Never fabricate information — only use what's provided in the profile and context."
    )

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=prompt),
    ]

    config = LLMConfig(model="", temperature=0.3, max_tokens=4096, system_prompt=system_prompt)

    try:
        start = time.time()
        result = await smart_router.generate_with_fallback(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            config=config,
            query=f"Generate {doc_type} for {target[:80]}",
        )
        elapsed = time.time() - start
        logger.info(f"Document generated ({doc_type}) in {elapsed:.1f}s: {len(result.content)} chars")
        return result.content

    except Exception as e:
        logger.error(f"Document generation failed ({doc_type}): {e}")
        return f"Document generation encountered an issue. Please try again.\n\nError: {str(e)[:200]}"


async def stream_document(
    doc_type: str,
    target: str,
    profile_str: str,
    context: str = "",
    session_id: str = "",
) -> AsyncGenerator[str, None]:
    """Stream a document generation token by token."""
    from noray.llm.smart_router import smart_router
    from noray.llm.providers.base_provider import LLMConfig, LLMMessage

    if doc_type not in DOCUMENT_PROMPTS:
        doc_type = "cover_letter"

    prompt = get_document_prompt(doc_type, target, profile_str, context)

    system_prompt = (
        "You are an expert document writer for career and academic applications. "
        "Write professional, tailored documents."
    )

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=prompt),
    ]

    config = LLMConfig(model="", temperature=0.3, max_tokens=4096, system_prompt=system_prompt)

    full_content = ""
    try:
        async for chunk in smart_router.stream_with_continuity(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            config=config,
            session_id=session_id,
            query=f"Generate {doc_type}",
        ):
            if chunk.content:
                full_content += chunk.content
                yield chunk.content
    except Exception as e:
        logger.error(f"Streaming document generation failed: {e}")
        yield f"\n\n[Generation interrupted. Partial content available.]"


async def check_quality(
    document: str,
    doc_type: str,
) -> QualityReport:
    """Run AI quality check on a generated document."""
    from noray.llm.smart_router import smart_router
    from noray.llm.providers.base_provider import LLMConfig, LLMMessage

    prompt = QUALITY_CHECK_PROMPT.format(doc_type=doc_type, document=document[:3000])

    messages = [
        LLMMessage(role="system", content="You are a document quality reviewer. Return only valid JSON."),
        LLMMessage(role="user", content=prompt),
    ]

    config = LLMConfig(model="", temperature=0.1, max_tokens=2048, system_prompt="")

    try:
        start = time.time()
        result = await smart_router.generate_with_fallback(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            config=config,
            query=f"Quality check {doc_type}",
        )
        elapsed = time.time() - start
        logger.info(f"Quality check completed in {elapsed:.2f}s for {doc_type}")

        raw_text = result.content.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            # Remove first and last lines (```json and ```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw_text = "\n".join(lines).strip()

        raw = json.loads(raw_text)

        # Normalize hallucination_risk (LLM may return int or string)
        hr = raw.get("hallucination_risk", "low")
        if isinstance(hr, (int, float)):
            hr = "low" if hr <= 33 else ("medium" if hr <= 66 else "high")

        # Normalize overall_quality (LLM may return int or string)
        oq = raw.get("overall_quality", "fair")
        if isinstance(oq, (int, float)):
            oq = "poor" if oq <= 25 else ("fair" if oq <= 50 else ("good" if oq <= 75 else "excellent"))

        # Normalize improvements_needed (LLM may return list or int)
        imp = raw.get("improvements_needed", 0)
        if isinstance(imp, list):
            imp = len(imp)

        return QualityReport(
            ats_score=float(raw.get("ats_score", 0)),
            grammar_score=float(raw.get("grammar_score", 0)),
            keyword_coverage=float(raw.get("keyword_coverage", 0)),
            readability_score=float(raw.get("readability_score", 0)),
            hallucination_risk=hr,
            formatting_issues=raw.get("formatting_issues", []),
            consistency_issues=raw.get("consistency_issues", []),
            suggestions=raw.get("suggestions", []),
            overall_quality=oq,
            improvements_needed=imp,
        )

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse quality check: {e}")
        return QualityReport(ats_score=70, overall_quality="fair")
    except Exception as e:
        logger.error(f"Quality check failed: {e}")
        return QualityReport(ats_score=70, overall_quality="fair")


async def generate_with_quality(
    doc_type: str,
    target: str,
    profile_str: str,
    context: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    """Generate a document and run quality check."""
    content = await generate_document(doc_type, target, profile_str, context, session_id)
    quality = await check_quality(content, doc_type)

    return {
        "doc_type": doc_type,
        "content": content,
        "length": len(content),
        "quality": asdict(quality),
    }


async def get_rag_context(
    query: str,
    max_chunks: int = 5,
) -> str:
    """Retrieve RAG context from uploaded documents and knowledge base."""
    try:
        from noray.rag.retrieval_pipeline import RetrievalPipeline

        pipeline = RetrievalPipeline()
        result = await pipeline.retrieve(query=query, limit=max_chunks)
        context = result.get("context", "")
        return context[:3000]
    except Exception as e:
        logger.debug(f"RAG context retrieval skipped: {e}")
        return ""
