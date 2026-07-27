"""
NORAY — Statement of Purpose Generator

Generate academic Statements of Purpose for scholarship and program applications.
Follows a structured academic format: hook → background → research → fit → goals.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from noray.shared.models import CareerProfile


@dataclass
class SOPOutput:
    """Result of SOP generation."""
    content: str = ""
    word_count: int = 0
    sections: list[str] = field(default_factory=list)
    success: bool = False
    key_decisions: list[str] = field(default_factory=list)


# ─── Public API ───────────────────────────────────────────────

def generate_sop(
    profile: CareerProfile,
    scholarship_info: str,
    research_interests: list[str],
    word_limit: int = 1000,
) -> SOPOutput:
    """
    Generate a Statement of Purpose for a scholarship/program application.
    
    Args:
        profile: The candidate's career profile
        scholarship_info: Details about the scholarship/program
        research_interests: List of research interest areas
        word_limit: Target word count
    
    Returns:
        SOPOutput with the generated SOP
    """
    output = SOPOutput()

    # Build each section
    sections = _build_sop_sections(profile, scholarship_info, research_interests, word_limit)

    # Assemble the SOP
    content = _assemble_sop(sections)

    output.content = content
    output.word_count = len(content.split())
    output.sections = list(sections.keys())
    output.success = True
    output.key_decisions = _document_decisions(profile, research_interests)

    return output


def generate_sop_outline(
    profile: CareerProfile,
    scholarship_info: str,
    research_interests: list[str],
) -> dict[str, str]:
    """
    Generate an SOP outline (section headers + bullet points) for the user to fill in.
    Useful when the user wants to write their own SOP but needs structure.
    """
    return _build_sop_sections(profile, scholarship_info, research_interests, outline_only=True)


# ─── Section Building ─────────────────────────────────────────

def _build_sop_sections(
    profile: CareerProfile,
    scholarship_info: str,
    research_interests: list[str],
    word_limit: int = 1000,
    outline_only: bool = False,
) -> dict[str, str]:
    """Build each section of the SOP."""
    sections = {}

    # ── 1. Opening Hook ──
    sections["opening"] = _build_opening(profile, research_interests, scholarship_info, outline_only)

    # ── 2. Academic Background ──
    sections["academic_background"] = _build_academic_background(profile, outline_only)

    # ── 3. Research Experience ──
    sections["research_experience"] = _build_research_experience(profile, research_interests, outline_only)

    # ── 4. Why This Program ──
    sections["why_this_program"] = _build_why_program(profile, scholarship_info, research_interests, outline_only)

    # ── 5. Future Goals ──
    sections["future_goals"] = _build_future_goals(profile, research_interests, outline_only)

    return sections


def _build_opening(
    profile: CareerProfile,
    research_interests: list[str],
    scholarship_info: str,
    outline_only: bool = False,
) -> str:
    """Build the opening hook paragraph."""
    if outline_only:
        return (
            "## Opening Hook\n"
            "- Start with a compelling moment or insight that sparked your interest\n"
            "- Connect your personal motivation to the research area\n"
            "- State your research question or area of focus\n"
            "- Keep it specific and personal, not generic\n"
        )

    parts = []

    # Research interest hook
    if research_interests:
        primary_interest = research_interests[0]
        parts.append(
            f"My fascination with {primary_interest} began during my academic journey, "
            f"where I witnessed firsthand how data-driven approaches can transform our "
            f"understanding of complex problems."
        )

    # Connection to career
    if profile.experience:
        exp = profile.experience[0]
        if exp.achievements:
            parts.append(
                f"This interest deepened during my work as {exp.title} at {exp.company}, "
                f"where {exp.achievements[0].lower()}"
            )
        elif exp.responsibilities:
            parts.append(
                f"This interest deepened during my work as {exp.title} at {exp.company}, "
                f"where I was responsible for {exp.responsibilities[0].lower()}"
            )

    # Research question
    if research_interests:
        parts.append(
            f"I am now eager to pursue advanced research in {', '.join(research_interests[:2])}, "
            f"and I believe this program provides the ideal environment to do so."
        )

    return " ".join(parts) if parts else (
        "I am writing to express my strong interest in this program. "
        "My academic background and professional experience have prepared me "
        "to contribute meaningfully to the field."
    )


def _build_academic_background(profile: CareerProfile, outline_only: bool = False) -> str:
    """Build the academic background section."""
    if outline_only:
        return (
            "## Academic Background\n"
            "- List your degrees with institution and dates\n"
            "- Highlight relevant coursework and thesis topics\n"
            "- Mention academic achievements (honors, GPA if strong)\n"
            "- Connect your academic journey to the target program\n"
        )

    parts = []

    for edu in profile.education:
        degree_line = f"I completed my {edu.degree} in {edu.field} at {edu.institution}"
        if edu.start_year and edu.end_year:
            degree_line += f" ({edu.start_year}–{edu.end_year})"
        parts.append(degree_line + ".")

        if edu.thesis:
            parts.append(f"My thesis, titled \"{edu.thesis}\", provided me with a strong foundation in research methodology.")
        if edu.topics:
            parts.append(f"Key coursework included {', '.join(edu.topics[:5])}.")

    # Certifications
    if profile.certifications:
        cert_names = [c.name for c in profile.certifications[:3]]
        parts.append(f"I have also earned certifications in {', '.join(cert_names)}, demonstrating my commitment to continuous learning.")

    return " ".join(parts) if parts else "My academic journey has provided me with a solid foundation for advanced study."


def _build_research_experience(
    profile: CareerProfile,
    research_interests: list[str],
    outline_only: bool = False,
) -> str:
    """Build the research/professional experience section."""
    if outline_only:
        return (
            "## Research & Professional Experience\n"
            "- Describe your most relevant research or professional experience\n"
            "- Focus on methodological skills and analytical capabilities\n"
            "- Highlight any publications, presentations, or research outputs\n"
            "- Connect your experience to your proposed research area\n"
        )

    parts = []

    # Professional experience
    for exp in profile.experience[:2]:
        exp_text = f"As {exp.title} at {exp.company}"
        if exp.location:
            exp_text += f" ({exp.location})"
        exp_text += ","

        if exp.achievements:
            exp_text += f" I {exp.achievements[0].lower()}"
            if len(exp.achievements) > 1:
                exp_text += f" and {exp.achievements[1].lower()}"
        elif exp.responsibilities:
            exp_text += f" I was responsible for {exp.responsibilities[0].lower()}"

        parts.append(exp_text + ".")

        # Technologies/methodologies
        if exp.technologies:
            parts.append(f"This work involved {', '.join(exp.technologies[:4])}.")

    # Publications
    if profile.publications:
        pub_count = len(profile.publications)
        parts.append(f"I have {pub_count} publication(s), including work on {profile.publications[0].title}.")
        if pub_count > 1:
            parts.append("These publications demonstrate my ability to conduct and communicate rigorous research.")

    # Projects
    if profile.projects:
        proj = profile.projects[0]
        parts.append(f"My {proj.name} project, {proj.description.lower()}, showcases my ability to apply research insights to practical problems.")

    return " ".join(parts) if parts else (
        "My professional experience has equipped me with the analytical and methodological "
        "skills necessary for advanced research."
    )


def _build_why_program(
    profile: CareerProfile,
    scholarship_info: str,
    research_interests: list[str],
    outline_only: bool = False,
) -> str:
    """Build the 'Why This Program' section."""
    if outline_only:
        return (
            "## Why This Program\n"
            "- Explain why this specific program/institution is the right fit\n"
            "- Mention specific faculty, labs, or research groups\n"
            "- Connect your research interests to the program's strengths\n"
            "- Show you've done your research on the program\n"
        )

    parts = []

    # Research alignment
    if research_interests:
        parts.append(
            f"I am particularly drawn to this program because of its strength in "
            f"{', '.join(research_interests[:2])}, which directly align with my research interests."
        )

    # Skills alignment
    primary_skills = profile.skills.primary[:3]
    if primary_skills:
        parts.append(
            f"My expertise in {', '.join(primary_skills)} positions me well to contribute "
            f"to the program's research output from day one."
        )

    # Career goals alignment
    if profile.goals.career_objectives:
        parts.append(
            f"This program directly supports my career objective of {profile.goals.career_objectives[0].lower()}"
        )

    return " ".join(parts) if parts else (
        "This program's reputation for academic excellence and its commitment to "
        "interdisciplinary research make it the ideal environment for my graduate studies."
    )


def _build_future_goals(
    profile: CareerProfile,
    research_interests: list[str],
    outline_only: bool = False,
) -> str:
    """Build the future goals section."""
    if outline_only:
        return (
            "## Future Goals\n"
            "- Describe your short-term goals (during the program)\n"
            "- Describe your long-term career vision\n"
            "- Explain how the program enables these goals\n"
            "- End with a forward-looking statement about your contribution to the field\n"
        )

    parts = []

    # Short-term goals
    if research_interests:
        parts.append(
            f"During my studies, I aim to deepen my expertise in {research_interests[0]} "
            f"and contribute original research to the field."
        )

    # Long-term goals
    if profile.goals.career_objectives:
        parts.append(
            f"My long-term goal is to {profile.goals.career_objectives[0].lower()} "
        )
    elif profile.goals.target_roles:
        parts.append(
            f"Long-term, I aspire to work as a {profile.goals.target_roles[0]}, "
            f"bridging the gap between academic research and practical impact."
        )
    else:
        parts.append(
            "Long-term, I aspire to become a researcher and practitioner who bridges "
            "the gap between academic knowledge and real-world applications."
        )

    # Impact statement
    if research_interests:
        parts.append(
            f"I am confident that this program will provide me with the tools, mentorship, "
            f"and network to make meaningful contributions to {research_interests[0]}."
        )

    return " ".join(parts)


# ─── Assembly ─────────────────────────────────────────────────

def _assemble_sop(sections: dict[str, str]) -> str:
    """Assemble SOP sections into a complete document."""
    parts = []

    section_order = [
        "opening",
        "academic_background",
        "research_experience",
        "why_this_program",
        "future_goals",
    ]

    for section_name in section_order:
        content = sections.get(section_name, "")
        if content:
            parts.append(content)
            parts.append("")  # Paragraph break

    return "\n\n".join(parts)


def _document_decisions(
    profile: CareerProfile,
    research_interests: list[str],
) -> list[str]:
    """Document key decisions made during generation."""
    decisions = []

    if research_interests:
        decisions.append(f"Focused SOP on research interests: {', '.join(research_interests[:3])}")

    if profile.experience:
        decisions.append(f"Used {profile.experience[0].company} experience as primary evidence")

    if profile.publications:
        decisions.append(f"Referenced {len(profile.publications)} publication(s) for academic credibility")

    if profile.education:
        decisions.append(f"Highlighted {profile.education[0].degree} from {profile.education[0].institution}")

    return decisions
