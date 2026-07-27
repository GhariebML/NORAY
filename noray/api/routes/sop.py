"""
NORAY — SOP & Document API Routes

Endpoints for SOP, motivation letter, and research proposal generation.
"""

from fastapi import APIRouter

from noray.api.schemas import MotivationGenerateRequest, ResearchProposalRequest, SOPGenerateRequest
from noray.shared.profile_store import load_profile

router = APIRouter()


@router.post("/sop")
async def generate_sop_endpoint(request: SOPGenerateRequest):
    """Generate a Statement of Purpose."""
    from noray.scholarship_agent.sop_generator import generate_sop
    profile = load_profile()
    sop = generate_sop(profile, request.scholarship_info, request.research_interests)
    return {
        "status": "generated",
        "content": sop.content,
        "sop": sop.content,
        "word_count": sop.word_count,
        "sections": sop.sections,
        "key_decisions": sop.key_decisions,
    }


@router.post("/motivation")
async def generate_motivation_endpoint(request: MotivationGenerateRequest):
    """Generate a motivation letter."""
    from noray.scholarship_agent.motivation_letter import generate_motivation_letter
    profile = load_profile()
    motivation = generate_motivation_letter(profile, request.scholarship_info)
    return {
        "status": "generated",
        "content": motivation.content,
        "motivation": motivation.content,
        "word_count": motivation.word_count,
        "sections": motivation.sections,
    }


@router.post("/research")
async def generate_research_proposal_endpoint(request: ResearchProposalRequest):
    """Generate a research proposal."""
    from noray.scholarship_agent.research_proposal import generate_research_proposal
    profile = load_profile()
    interests = request.research_interests
    if not interests and profile.scholarship_goals:
        interests = profile.scholarship_goals.research_interests
    proposal = generate_research_proposal(profile, request.scholarship_info, interests)
    return {
        "status": "generated",
        "title": proposal.title,
        "content": proposal.content,
        "research_proposal": proposal.content,
        "word_count": proposal.word_count,
        "sections": proposal.sections,
        "references": proposal.references,
    }
