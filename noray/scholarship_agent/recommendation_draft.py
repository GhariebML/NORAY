"""
NORAY — Recommendation Letter Draft

Draft recommendation letter outlines for referees to personalize.
Provides structured templates based on the relationship type and tone.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from noray.shared.models import CareerProfile


@dataclass
class RecommendationDraft:
    """A drafted recommendation letter outline."""
    referee_name: str = ""
    relationship: str = ""
    tone: str = ""              # academic_supervisor, employer, colleague
    content: str = ""
    fill_in_markers: list[str] = field(default_factory=list)
    success: bool = False
    sections: list[str] = field(default_factory=list)
    key_decisions: list[str] = field(default_factory=list)


# ─── Public API ───────────────────────────────────────────────

def draft_recommendation(
    profile: CareerProfile,
    referee_name: str,
    relationship: str,
    tone: str = "academic_supervisor",
    scholarship_info: str = "",
    target_degree: str = "",
) -> RecommendationDraft:
    """
    Draft a recommendation letter outline for a referee.
    
    Args:
        profile: The candidate's career profile
        referee_name: Name of the referee
        relationship: How the referee knows the candidate
        tone: Tone of the letter (academic_supervisor, employer, colleague)
        scholarship_info: Optional scholarship/program context
        target_degree: Target degree level for tailoring
    
    Returns:
        RecommendationDraft with [FILL IN] markers for personal anecdotes
    """
    draft = RecommendationDraft(
        referee_name=referee_name,
        relationship=relationship,
        tone=tone,
    )

    # Build the letter
    sections = _build_sections(profile, referee_name, relationship, tone, scholarship_info, target_degree)

    draft.content = _assemble(sections)
    draft.fill_in_markers = _extract_fill_in_markers(draft.content)
    draft.sections = list(sections.keys())
    draft.success = True
    draft.key_decisions = _document_decisions(profile, tone, relationship)

    return draft


def draft_multiple_recommendations(
    profile: CareerProfile,
    referees: list[dict[str, str]],
    scholarship_info: str = "",
    target_degree: str = "",
) -> list[RecommendationDraft]:
    """
    Draft recommendation letters for multiple referees.
    
    Args:
        profile: The candidate's career profile
        referees: List of {name, relationship, tone} dicts
        scholarship_info: Optional scholarship context
        target_degree: Target degree level
    
    Returns:
        List of RecommendationDraft objects
    """
    drafts = []
    for ref in referees:
        draft = draft_recommendation(
            profile=profile,
            referee_name=ref.get("name", "Professor [Name]"),
            relationship=ref.get("relationship", "academic supervisor"),
            tone=ref.get("tone", "academic_supervisor"),
            scholarship_info=scholarship_info,
            target_degree=target_degree,
        )
        drafts.append(draft)
    return drafts


# ─── Section Building ─────────────────────────────────────────

def _build_sections(
    profile: CareerProfile,
    referee_name: str,
    relationship: str,
    tone: str,
    scholarship_info: str,
    target_degree: str,
) -> dict[str, str]:
    """Build each section of the recommendation letter."""
    sections = {}

    sections["opening"] = _build_opening(referee_name, relationship, tone, profile)
    sections["academic_ability"] = _build_academic_ability(profile, tone, target_degree)
    sections["character_traits"] = _build_character_traits(profile, tone)
    sections["comparative"] = _build_comparative(profile, tone)
    sections["closing"] = _build_closing(profile, referee_name, tone, target_degree)

    return sections


def _build_opening(
    referee_name: str,
    relationship: str,
    tone: str,
    profile: CareerProfile,
) -> str:
    """Build the opening paragraph — context of the relationship."""
    name = profile.identity.name or "[Candidate Name]"

    if tone == "academic_supervisor":
        return (
            f"I am pleased to write this letter of recommendation for {name}. "
            f"I have known {name} in my capacity as {relationship}, and I can attest "
            f"to their exceptional academic abilities and research potential.\n\n"
            f"[FILL IN: How long you have known the candidate and in what capacity. "
            f"Include specific courses, research projects, or academic interactions.]"
        )
    elif tone == "employer":
        return (
            f"I am writing to recommend {name} for this opportunity. "
            f"I have worked with {name} as their {relationship}, and I have been "
            f"consistently impressed by their professionalism and capabilities.\n\n"
            f"[FILL IN: How long you have supervised/worked with the candidate. "
            f"Describe their role and responsibilities in your organization.]"
        )
    else:  # colleague
        return (
            f"I am happy to recommend {name} for this program. "
            f"I have worked alongside {name} as {relationship}, and I can speak "
            f"to their character, work ethic, and contributions.\n\n"
            f"[FILL IN: Context of your professional relationship. "
            f"Projects or initiatives you worked on together.]"
        )


def _build_academic_ability(
    profile: CareerProfile,
    tone: str,
    target_degree: str,
) -> str:
    """Build the academic/professional ability section."""
    parts = []

    if tone == "academic_supervisor":
        parts.append(
            f"Academically, {profile.identity.name or '[Candidate]'} has demonstrated "
            f"exceptional ability in their field."
        )
        # Reference education
        if profile.education:
            edu = profile.education[0]
            parts.append(
                f"Their {edu.degree} in {edu.field} from {edu.institution} "
                f"provided a strong foundation for advanced study."
            )
        if profile.publications:
            parts.append(
                f"They have {len(profile.publications)} publication(s), demonstrating "
                f"their ability to conduct and communicate original research."
            )
        parts.append(
            "\n[FILL IN: Specific examples of academic excellence. "
            "Top grades, outstanding papers, research contributions, "
            "thesis quality, analytical skills demonstrated in coursework.]"
        )

    elif tone == "employer":
        parts.append(
            f"During their time with our organization, {profile.identity.name or '[Candidate]'} "
            f"has consistently exceeded expectations."
        )
        # Reference experience
        if profile.experience:
            exp = profile.experience[0]
            parts.append(f"As {exp.title}, they were responsible for {exp.responsibilities[0].lower() if exp.responsibilities else 'key deliverables'}.")
        parts.append(
            "\n[FILL IN: Specific achievements, projects led, problems solved, "
            "impact on the organization, technical skills demonstrated.]"
        )

    else:
        parts.append(
            f"In our professional interactions, {profile.identity.name or '[Candidate]'} "
            f"has shown remarkable competence and dedication."
        )
        parts.append(
            "\n[FILL IN: Specific examples of their contributions, "
            "collaborative skills, and professional growth.]"
        )

    return " ".join(parts)


def _build_character_traits(profile: CareerProfile, tone: str) -> str:
    """Build the character/personal qualities section."""
    parts = []
    name = profile.identity.name or "[Candidate]"

    # Use behavioral profile data
    strengths = profile.behavioral.strengths[:3] if profile.behavioral.strengths else []
    work_style = profile.behavioral.work_style if profile.behavioral.work_style else ""

    if strengths:
        parts.append(
            f"Beyond their technical abilities, {name} possesses strong personal qualities. "
            f"They are known for being {', '.join(s.lower() for s in strengths)}."
        )
    else:
        parts.append(
            f"Beyond their professional abilities, {name} is a person of great character."
        )

    if work_style and "[From LinkedIn" not in work_style:
        parts.append(f"Their work style is characterized by {work_style.lower()}.")

    if tone == "academic_supervisor":
        parts.append(
            "\n[FILL IN: Personal qualities observed in an academic setting. "
            "Intellectual curiosity, perseverance, ability to handle challenges, "
            "collaboration with peers, initiative in research.]"
        )
    elif tone == "employer":
        parts.append(
            "\n[FILL IN: Workplace qualities. Leadership potential, teamwork, "
            "communication skills, reliability, ability to work under pressure, "
            "adaptability to new challenges.]"
        )
    else:
        parts.append(
            "\n[FILL IN: Personal qualities you've observed. Integrity, "
            "work ethic, interpersonal skills, contributions to team dynamics.]"
        )

    return " ".join(parts)


def _build_comparative(profile: CareerProfile, tone: str) -> str:
    """Build the comparative assessment section."""
    name = profile.identity.name or "[Candidate]"

    if tone == "academic_supervisor":
        return (
            f"In my assessment, {name} ranks among the top [FILL IN: percentage, e.g., 5%] "
            f"of students I have supervised in my [FILL IN: number] years of academic mentorship. "
            f"Their combination of [FILL IN: specific strengths] sets them apart from their peers.\n\n"
            f"[FILL IN: Compare to other students/mentees. What makes this candidate unique? "
            f"Any specific distinction or honor you can speak to.]"
        )
    elif tone == "employer":
        return (
            f"Among the [FILL IN: number] professionals I have managed, {name} "
            f"stands out for [FILL IN: specific differentiator]. "
            f"I would rank them in the top [FILL IN: percentage] of their cohort.\n\n"
            f"[FILL IN: Compare to peers at similar career stage. "
            f"What distinguishes this candidate from others in similar roles?]"
        )
    else:
        return (
            f"Having worked with many professionals in this field, I can say that {name} "
            f"is among the most [FILL IN: quality] individuals I have encountered.\n\n"
            f"[FILL IN: How does this candidate compare to others you've worked with?]"
        )


def _build_closing(profile: CareerProfile, referee_name: str, tone: str, target_degree: str) -> str:
    """Build the closing endorsement."""
    name = profile.identity.name or "[Candidate]"
    degree_text = f"this {target_degree} program" if target_degree else "this program"

    if tone == "academic_supervisor":
        return (
            f"I give {name} my strongest recommendation for {degree_text}. "
            f"I am confident they will excel in advanced study and make meaningful contributions to the field.\n\n"
            f"Please do not hesitate to contact me if you require any further information.\n\n"
            f"Sincerely,\n"
            f"{referee_name}\n"
            f"[FILL IN: Title, Department, Institution, Email, Phone]"
        )
    elif tone == "employer":
        return (
            f"I wholeheartedly recommend {name} for {degree_text}. "
            f"Their professional abilities and personal qualities make them an outstanding candidate.\n\n"
            f"I would be happy to provide any additional information you may need.\n\n"
            f"Sincerely,\n"
            f"{referee_name}\n"
            f"[FILL IN: Title, Company, Email, Phone]"
        )
    else:
        return (
            f"I strongly recommend {name} for {degree_text}. "
            f"I am confident they will be a valuable addition to your program.\n\n"
            f"Feel free to contact me for any further information.\n\n"
            f"Sincerely,\n"
            f"{referee_name}\n"
            f"[FILL IN: Title, Organization, Email, Phone]"
        )


# ─── Helpers ──────────────────────────────────────────────────

def _assemble(sections: dict[str, str]) -> str:
    """Assemble the recommendation letter."""
    parts = []
    order = ["opening", "academic_ability", "character_traits", "comparative", "closing"]
    for name in order:
        content = sections.get(name, "")
        if content:
            parts.append(content)
    return "\n\n".join(parts)


def _extract_fill_in_markers(content: str) -> list[str]:
    """Extract all [FILL IN: ...] markers from the content."""
    import re
    markers = re.findall(r"\[FILL IN:(.*?)\]", content)
    return [m.strip() for m in markers]


def _document_decisions(profile: CareerProfile, tone: str, relationship: str) -> list[str]:
    """Document key decisions."""
    decisions = []
    decisions.append(f"Generated for {tone} recommendation")
    decisions.append(f"Relationship context: {relationship}")
    if profile.behavioral.strengths:
        decisions.append(f"Incorporated behavioral strengths: {', '.join(profile.behavioral.strengths[:3])}")
    if profile.experience:
        decisions.append(f"Referenced experience at {profile.experience[0].company}")
    if profile.publications:
        decisions.append(f"Mentioned {len(profile.publications)} publication(s)")
    return decisions
