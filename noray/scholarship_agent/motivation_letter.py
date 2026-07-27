"""
NORAY — Motivation Letter Generator

Generate European-style motivation letters for scholarship applications.
More personal than an SOP — focuses on motivation, personal story, and program fit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from noray.shared.models import CareerProfile


@dataclass
class MotivationLetterOutput:
    """Result of motivation letter generation."""
    content: str = ""
    word_count: int = 0
    sections: list[str] = field(default_factory=list)
    success: bool = False
    key_decisions: list[str] = field(default_factory=list)


# ─── Public API ───────────────────────────────────────────────

def generate_motivation_letter(
    profile: CareerProfile,
    scholarship_info: str,
    word_limit: int = 500,
    target_degree: str = "",
    target_country: str = "",
) -> MotivationLetterOutput:
    """
    Generate a European-style motivation letter for a scholarship application.
    
    More personal than an SOP — focuses on personal motivation, what drives
    the candidate, and how the program fits their journey.
    
    Args:
        profile: The candidate's career profile
        scholarship_info: Details about the scholarship/program
        word_limit: Target word count
        target_degree: Target degree level
        target_country: Target country
    
    Returns:
        MotivationLetterOutput with the generated letter
    """
    output = MotivationLetterOutput()

    # Build sections
    sections = _build_sections(profile, scholarship_info, target_degree, target_country)

    # Assemble
    content = _assemble(sections)

    output.content = content
    output.word_count = len(content.split())
    output.sections = list(sections.keys())
    output.success = True
    output.key_decisions = _document_decisions(profile, target_degree, target_country)

    return output


def generate_motivation_outline(
    profile: CareerProfile,
    scholarship_info: str,
) -> dict[str, str]:
    """Generate a motivation letter outline for the user to fill in."""
    return _build_sections(profile, scholarship_info, outline_only=True)


# ─── Section Building ─────────────────────────────────────────

def _build_sections(
    profile: CareerProfile,
    scholarship_info: str,
    target_degree: str = "",
    target_country: str = "",
    outline_only: bool = False,
) -> dict[str, str]:
    """Build each section of the motivation letter."""
    sections = {}

    # ── 1. Personal Motivation ──
    sections["motivation"] = _build_motivation(profile, outline_only)

    # ── 2. Academic & Professional Background ──
    sections["background"] = _build_background(profile, outline_only)

    # ── 3. Why This Program ──
    sections["why_program"] = _build_why_program(profile, scholarship_info, target_degree, target_country, outline_only)

    # ── 4. What I Will Contribute ──
    sections["contribution"] = _build_contribution(profile, outline_only)

    # ── 5. Closing ──
    sections["closing"] = _build_closing(profile, target_degree, outline_only)

    return sections


def _build_motivation(profile: CareerProfile, outline_only: bool = False) -> str:
    """Build the personal motivation opening."""
    if outline_only:
        return (
            "## Personal Motivation\n"
            "- Open with what drives you personally and academically\n"
            "- Share a specific moment or experience that shaped your direction\n"
            "- Connect your personal story to your academic/career path\n"
            "- Keep it genuine and personal, not generic\n"
        )

    parts = []

    # Career objectives as motivation
    if profile.goals.career_objectives:
        parts.append(
            f"My motivation for pursuing further studies stems from a deep commitment to "
            f"{profile.goals.career_objectives[0].lower()}"
        )
    elif profile.goals.target_roles:
        parts.append(
            f"I am driven by my aspiration to become a {profile.goals.target_roles[0]}, "
            f"a goal that requires advanced knowledge and research skills"
        )
    else:
        parts.append(
            "I am motivated by a genuine passion for learning and a desire to contribute "
            "meaningfully to my field through advanced study and research"
        )

    # Connection to experience
    if profile.experience:
        exp = profile.experience[0]
        if exp.achievements:
            parts.append(
                f"During my time as {exp.title} at {exp.company}, {exp.achievements[0].lower()}. "
                f"This experience reinforced my conviction that advanced study is the right next step."
            )

    return " ".join(parts) + "." if parts else (
        "I am writing to express my strong motivation for this program. "
        "My experiences have shaped my academic direction and prepared me for this opportunity."
    )


def _build_background(profile: CareerProfile, outline_only: bool = False) -> str:
    """Build the background section."""
    if outline_only:
        return (
            "## Background\n"
            "- Summarize your relevant academic background\n"
            "- Highlight key professional experiences\n"
            "- Mention skills that are relevant to the program\n"
        )

    parts = []

    # Education
    if profile.education:
        edu = profile.education[0]
        parts.append(f"I hold a {edu.degree} in {edu.field} from {edu.institution}.")
        if edu.thesis:
            parts.append(f"My thesis on \"{edu.thesis}\" deepened my research capabilities.")

    # Key experience
    if profile.experience:
        exp = profile.experience[0]
        parts.append(f"Professionally, I have worked as {exp.title} at {exp.company}.")
        if exp.responsibilities:
            parts.append(f"My role involved {exp.responsibilities[0].lower()}.")

    # Key skills
    if profile.skills.primary:
        parts.append(f"My core competencies include {', '.join(profile.skills.primary[:4])}.")

    return " ".join(parts) if parts else (
        "My academic and professional background has provided me with the skills "
        "and perspective needed for this program."
    )


def _build_why_program(
    profile: CareerProfile,
    scholarship_info: str,
    target_degree: str,
    target_country: str,
    outline_only: bool = False,
) -> str:
    """Build the 'why this program' section."""
    if outline_only:
        return (
            "## Why This Program\n"
            "- Explain what specifically attracts you to this program\n"
            "- Mention the country/institution if relevant\n"
            "- Connect your goals to what the program offers\n"
        )

    parts = []

    if target_country:
        parts.append(
            f"Studying in {target_country} offers a unique opportunity to engage with "
            f"a diverse academic community and gain international perspective."
        )

    if target_degree:
        parts.append(
            f"Pursuing a {target_degree} will allow me to deepen my expertise "
            f"and conduct original research in my area of interest."
        )

    # Skills alignment
    if profile.skills.domain:
        parts.append(
            f"The program's focus on {profile.skills.domain[0]} aligns perfectly "
            f"with my academic interests and career trajectory."
        )

    return " ".join(parts) if parts else (
        "This program stands out for its academic excellence and its commitment to "
        "fostering the next generation of researchers and practitioners."
    )


def _build_contribution(profile: CareerProfile, outline_only: bool = False) -> str:
    """Build the 'what I will contribute' section."""
    if outline_only:
        return (
            "## What I Will Contribute\n"
            "- Describe what unique perspective or skills you bring\n"
            "- Mention how you'll enrich the program community\n"
            "- Reference specific projects or experiences that add value\n"
        )

    parts = []

    # Skills and experience
    if profile.skills.primary:
        parts.append(
            f"I bring strong technical skills in {', '.join(profile.skills.primary[:3])}, "
            f"which I can apply directly to the program's research activities."
        )

    # Projects
    if profile.projects:
        proj = profile.projects[0]
        parts.append(
            f"My experience with {proj.name}, {proj.description.lower()}, "
            f"demonstrates my ability to translate research ideas into practical outcomes."
        )

    # Publications
    if profile.publications:
        parts.append(
            f"With {len(profile.publications)} publication(s), I bring experience in "
            f"academic writing and research methodology."
        )

    # Behavioral strengths
    if profile.behavioral.strengths:
        parts.append(
            f"My strengths in {', '.join(profile.behavioral.strengths[:3]).lower()} "
            f"will enable me to contribute positively to the program's collaborative environment."
        )

    return " ".join(parts) if parts else (
        "I am confident that my background and skills will allow me to contribute "
        "meaningfully to the program's academic community."
    )


def _build_closing(profile: CareerProfile, target_degree: str, outline_only: bool = False) -> str:
    """Build the closing paragraph."""
    if outline_only:
        return (
            "## Closing\n"
            "- Reaffirm your enthusiasm for the program\n"
            "- Express gratitude for the opportunity\n"
            "- End with a forward-looking statement\n"
        )

    parts = []

    degree_text = f"a {target_degree}" if target_degree else "this program"
    parts.append(
        f"I am deeply motivated to pursue {degree_text} and confident that this opportunity "
        f"will be transformative for my academic and professional development."
    )
    parts.append(
        "I am grateful for your consideration and look forward to the opportunity "
        "to contribute to and learn from this program."
    )

    return " ".join(parts)


# ─── Assembly ─────────────────────────────────────────────────

def _assemble(sections: dict[str, str]) -> str:
    """Assemble motivation letter sections."""
    parts = []
    order = ["motivation", "background", "why_program", "contribution", "closing"]
    for name in order:
        content = sections.get(name, "")
        if content:
            parts.append(content)
    return "\n\n".join(parts)


def _document_decisions(
    profile: CareerProfile,
    target_degree: str,
    target_country: str,
) -> list[str]:
    """Document key decisions."""
    decisions = []
    if target_degree:
        decisions.append(f"Targeted motivation letter for {target_degree} application")
    if target_country:
        decisions.append(f"Emphasized international study in {target_country}")
    if profile.goals.career_objectives:
        decisions.append(f"Connected motivation to career objective: {profile.goals.career_objectives[0][:60]}")
    if profile.behavioral.strengths:
        decisions.append(f"Highlighted behavioral strengths: {', '.join(profile.behavioral.strengths[:3])}")
    return decisions
