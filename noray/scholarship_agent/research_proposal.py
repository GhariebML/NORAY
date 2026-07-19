"""
NORAY — Research Proposal Generator

Generate research proposals for PhD and postdoc applications.
Structured format: title, introduction, literature review, methodology, timeline, outcomes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from noray.shared.models import CareerProfile


@dataclass
class ResearchProposalOutput:
    """Result of research proposal generation."""
    title: str = ""
    introduction: str = ""
    literature_review: str = ""
    methodology: str = ""
    timeline: str = ""
    expected_outcomes: str = ""
    feasibility: str = ""
    references: list[str] = field(default_factory=list)
    word_count: int = 0
    sections: list[str] = field(default_factory=list)
    success: bool = False
    key_decisions: list[str] = field(default_factory=list)

    @property
    def content(self) -> str:
        """Assemble all sections into a single content string."""
        parts = []
        if self.title:
            parts.append(f"# {self.title}")
        if self.introduction:
            parts.append(f"## 1. Introduction\n{self.introduction}")
        if self.literature_review:
            parts.append(f"## 2. Literature Review\n{self.literature_review}")
        if self.methodology:
            parts.append(f"## 3. Methodology\n{self.methodology}")
        if self.timeline:
            parts.append(f"## 4. Timeline\n{self.timeline}")
        if self.expected_outcomes:
            parts.append(f"## 5. Expected Outcomes\n{self.expected_outcomes}")
        if self.feasibility:
            parts.append(f"## 6. Feasibility\n{self.feasibility}")
        return "\n\n".join(parts)


# ─── Public API ───────────────────────────────────────────────

def generate_research_proposal(
    profile: CareerProfile,
    scholarship_info: str,
    research_interests: list[str],
    word_limit: int = 2000,
) -> ResearchProposalOutput:
    """
    Generate a research proposal for PhD/postdoc applications.
    
    Args:
        profile: The candidate's career profile
        scholarship_info: Details about the program
        research_interests: Research areas of interest
        word_limit: Target word count
    
    Returns:
        ResearchProposalOutput with structured proposal sections
    """
    output = ResearchProposalOutput()

    # Build sections
    title = _build_title(research_interests)
    introduction = _build_introduction(profile, research_interests, scholarship_info)
    lit_review = _build_literature_review(research_interests)
    methodology = _build_methodology(profile, research_interests)
    timeline = _build_timeline(research_interests)
    outcomes = _build_expected_outcomes(research_interests)
    feasibility = _build_feasibility(profile, research_interests)
    references = _build_references(research_interests)

    output.title = title
    output.introduction = introduction
    output.literature_review = lit_review
    output.methodology = methodology
    output.timeline = timeline
    output.expected_outcomes = outcomes
    output.feasibility = feasibility
    output.references = references

    full_text = f"{title}\n\n{introduction}\n\n{lit_review}\n\n{methodology}\n\n{timeline}\n\n{outcomes}\n\n{feasibility}"
    output.word_count = len(full_text.split())
    output.sections = ["title", "introduction", "literature_review", "methodology", "timeline", "expected_outcomes", "feasibility", "references"]
    output.success = True
    output.key_decisions = _document_decisions(profile, research_interests)

    return output


def generate_proposal_outline(
    profile: CareerProfile,
    research_interests: list[str],
) -> dict[str, str]:
    """Generate a research proposal outline for the user to fill in."""
    return {
        "title": _build_title(research_interests, outline_only=True),
        "introduction": _build_introduction(profile, research_interests, "", outline_only=True),
        "literature_review": _build_literature_review(research_interests, outline_only=True),
        "methodology": _build_methodology(profile, research_interests, outline_only=True),
        "timeline": _build_timeline(research_interests, outline_only=True),
        "expected_outcomes": _build_expected_outcomes(research_interests, outline_only=True),
        "feasibility": _build_feasibility(profile, research_interests, outline_only=True),
    }


# ─── Section Builders ─────────────────────────────────────────

def _build_title(research_interests: list[str], outline_only: bool = False) -> str:
    """Build the research proposal title."""
    if outline_only:
        return (
            "## Title\n"
            "- Clear, specific, and descriptive\n"
            "- Include the main topic and approach\n"
            "- Avoid jargon; accessible to a review committee\n"
        )

    if research_interests:
        primary = research_interests[0]
        secondary = research_interests[1] if len(research_interests) > 1 else ""
        if secondary:
            return f"Advancing {primary} Through {secondary}: A Multi-Method Approach"
        return f"Investigating {primary}: Methods, Applications, and Impact"
    return "Research Proposal: [Title to be determined]"


def _build_introduction(
    profile: CareerProfile,
    research_interests: list[str],
    scholarship_info: str,
    outline_only: bool = False,
) -> str:
    """Build the introduction section."""
    if outline_only:
        return (
            "## 1. Introduction\n"
            "- State the research question or problem\n"
            "- Explain its significance and relevance\n"
            "- Provide brief context and background\n"
            "- State the objectives of the proposed research\n"
            "- Outline the expected contribution to the field\n"
        )

    parts = []

    # Research question
    if research_interests:
        primary = research_interests[0]
        parts.append(
            f"This proposal outlines a research program investigating {primary}, "
            f"an area of growing importance in contemporary scholarship."
        )

    # Significance
    if research_interests:
        parts.append(
            f"Understanding {research_interests[0]} has significant implications for both "
            f"theoretical advancement and practical applications. Despite considerable progress "
            f"in recent years, key questions remain unanswered, particularly regarding "
            f"the intersection of {', '.join(research_interests[:2])}."
        )

    # Objectives
    if research_interests:
        parts.append(
            f"The primary objectives of this research are: (1) to develop a comprehensive "
            f"understanding of {research_interests[0]}, (2) to propose novel methodologies "
            f"for addressing current limitations, and (3) to validate these approaches "
            f"through empirical investigation."
        )

    # Candidate's motivation
    if profile.experience:
        exp = profile.experience[0]
        parts.append(
            f"This research builds on my experience as {exp.title} at {exp.company}, "
            f"where I developed expertise in {', '.join(profile.skills.primary[:3])}."
        )

    return "\n\n".join(parts) if parts else (
        "This proposal presents a research plan to investigate a significant topic "
        "in the field. The research aims to contribute both theoretical insights "
        "and practical applications."
    )


def _build_literature_review(research_interests: list[str], outline_only: bool = False) -> str:
    """Build the literature review section."""
    if outline_only:
        return (
            "## 2. Literature Review\n"
            "- Summarize the current state of knowledge\n"
            "- Identify key theories and frameworks\n"
            "- Highlight gaps in existing research\n"
            "- Explain how your research addresses these gaps\n"
            "- Cite relevant and recent sources\n"
        )

    parts = []

    if research_interests:
        primary = research_interests[0]
        parts.append(
            f"The field of {primary} has seen substantial development in recent years. "
            f"Early work established foundational frameworks, while more recent studies "
            f"have begun to explore the complexities and nuances of the domain."
        )
        parts.append(
            f"Key contributions include advances in theoretical understanding, "
            f"methodological innovations, and empirical applications. However, "
            f"significant gaps remain, particularly in understanding the relationship "
            f"between {', '.join(research_interests[:2])} and their practical implications."
        )
        parts.append(
            f"This research addresses these gaps by proposing a novel approach that "
            f"combines established methodologies with innovative techniques, "
            f"building on the strengths of existing work while addressing its limitations."
        )

    return "\n\n".join(parts) if parts else (
        "A thorough review of the literature reveals both the progress made in this "
        "field and the significant gaps that this research aims to address."
    )


def _build_methodology(profile: CareerProfile, research_interests: list[str], outline_only: bool = False) -> str:
    """Build the methodology section."""
    if outline_only:
        return (
            "## 3. Methodology\n"
            "- Describe your research design (qualitative, quantitative, mixed)\n"
            "- Detail data collection methods\n"
            "- Explain analysis techniques\n"
            "- Discuss validity and reliability measures\n"
            "- Address ethical considerations\n"
        )

    parts = []

    # Research design
    if research_interests:
        parts.append(
            f"This research employs a mixed-methods approach, combining quantitative "
            f"analysis with qualitative insights to provide a comprehensive understanding "
            f"of {research_interests[0]}."
        )

    # Data collection
    primary_skills = profile.skills.primary[:3]
    tools = profile.skills.tools[:3]
    all_methods = primary_skills + tools
    if all_methods:
        parts.append(
            f"Data collection will leverage {', '.join(all_methods[:4])}, "
            f"ensuring robust and reproducible results."
        )
    else:
        parts.append(
            "Data collection will follow established protocols, ensuring rigor "
            "and reproducibility throughout the research process."
        )

    # Analysis
    parts.append(
        "Analysis will employ both statistical methods for quantitative data and "
        "thematic analysis for qualitative data, following best practices in the field."
    )

    # Validation
    parts.append(
        "Validity and reliability will be ensured through triangulation of data sources, "
        "peer review of coding schemes, and member checking where appropriate."
    )

    return "\n\n".join(parts)


def _build_timeline(research_interests: list[str], outline_only: bool = False) -> str:
    """Build the timeline section."""
    if outline_only:
        return (
            "## 4. Timeline\n"
            "- Break the research into phases\n"
            "- Assign realistic timeframes\n"
            "- Include milestones and deliverables\n"
            "- Account for writing and revision time\n"
        )

    return (
        "**Year 1 (Months 1-12): Foundation**\n"
        "- Months 1-3: Literature review refinement and methodology design\n"
        "- Months 4-6: Pilot study and instrument development\n"
        "- Months 7-9: Data collection Phase 1\n"
        "- Months 10-12: Preliminary analysis and first-year report\n\n"
        "**Year 2 (Months 13-24): Core Research**\n"
        "- Months 13-15: Data collection Phase 2\n"
        "- Months 16-18: Comprehensive data analysis\n"
        "- Months 19-21: Findings synthesis and interpretation\n"
        "- Months 22-24: Draft manuscript and conference presentations\n\n"
        "**Year 3 (Months 25-36): Completion**\n"
        "- Months 25-27: Thesis/paper writing\n"
        "- Months 28-30: Revision and peer feedback\n"
        "- Months 31-33: Final revisions and submission\n"
        "- Months 34-36: Defense preparation and graduation"
    )


def _build_expected_outcomes(research_interests: list[str], outline_only: bool = False) -> str:
    """Build the expected outcomes section."""
    if outline_only:
        return (
            "## 5. Expected Outcomes\n"
            "- Describe the expected contributions to the field\n"
            "- List planned publications or outputs\n"
            "- Discuss potential impact (academic and practical)\n"
        )

    parts = []

    if research_interests:
        parts.append(
            f"This research is expected to yield several significant contributions to {research_interests[0]}:"
        )

    parts.append(
        "- A novel theoretical framework for understanding the research problem\n"
        "- Empirical evidence supporting or challenging existing theories\n"
        "- Methodological contributions that can be applied to related research areas\n"
        "- Practical recommendations for practitioners in the field"
    )

    parts.append(
        "Planned outputs include 2-3 peer-reviewed journal articles, conference presentations "
        "at leading venues, and a comprehensive thesis document."
    )

    return "\n".join(parts)


def _build_feasibility(profile: CareerProfile, research_interests: list[str], outline_only: bool = False) -> str:
    """Build the feasibility section."""
    if outline_only:
        return (
            "## 6. Feasibility\n"
            "- Explain why you are the right person for this research\n"
            "- Describe your relevant skills and experience\n"
            "- Mention any preliminary work or pilot studies\n"
            "- Address potential challenges and mitigation strategies\n"
        )

    parts = []

    # Skills
    if profile.skills.primary:
        parts.append(
            f"This research is feasible given my expertise in {', '.join(profile.skills.primary[:4])}. "
            f"I have the technical skills necessary to execute the proposed methodology."
        )

    # Experience
    if profile.experience:
        exp = profile.experience[0]
        parts.append(
            f"My experience as {exp.title} at {exp.company} has provided me with "
            f"practical skills in research design, data analysis, and project management."
        )

    # Publications
    if profile.publications:
        parts.append(
            f"With {len(profile.publications)} publication(s), I have demonstrated my "
            f"ability to conduct rigorous research and communicate findings effectively."
        )

    # Challenges
    parts.append(
        "Potential challenges include data access and scope management. "
        "These will be mitigated through careful planning, regular advisor consultations, "
        "and a phased approach to data collection."
    )

    return "\n\n".join(parts)


def _build_references(research_interests: list[str]) -> list[str]:
    """Build a starter reference list."""
    refs = []

    if research_interests:
        primary = research_interests[0]
        refs.extend([
            f"[Author] (Year). A foundational study on {primary}. [Journal Name], [Volume(Issue)], [Pages].",
            f"[Author] (Year). Recent advances in {primary} methodology. [Journal Name], [Volume(Issue)], [Pages].",
            f"[Author] (Year). A comprehensive review of {primary}. [Journal Name], [Volume(Issue)], [Pages].",
            f"[Author] (Year). Empirical applications of {primary} in practice. [Journal Name], [Volume(Issue)], [Pages].",
            f"[Author] (Year). Theoretical frameworks for understanding {primary}. [Journal Name], [Volume(Issue)], [Pages].",
        ])

    return refs


def _document_decisions(profile: CareerProfile, research_interests: list[str]) -> list[str]:
    """Document key decisions."""
    decisions = []
    if research_interests:
        decisions.append(f"Focused proposal on: {', '.join(research_interests[:3])}")
    if profile.skills.primary:
        decisions.append(f"Highlighted technical skills: {', '.join(profile.skills.primary[:3])}")
    if profile.publications:
        decisions.append(f"Referenced {len(profile.publications)} existing publication(s) for credibility")
    decisions.append("Used mixed-methods approach for broad applicability")
    decisions.append("Structured as 3-year PhD timeline (adjustable for other programs)")
    return decisions
