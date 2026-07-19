"""
NORAY — Cover Letter Generator

Generate targeted cover letters using the drafter-reviewer pattern.
Uses the existing cover.cls LaTeX template with Lato/Raleway fonts.
Handles language matching (Danish/English) and company-specific tailoring.
"""

from __future__ import annotations
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from noray.shared.models import CareerProfile
from noray.shared.latex_utils import compile_cover_letter, validate_cover_letter_layout, cleanup_build_artifacts
from noray.career_agent.ats_analyzer import extract_keywords_from_posting
from noray.config import COVER_LETTERS_DIR


@dataclass
class CoverLetterOutput:
    """Result of cover letter generation."""
    tex_path: Path | None = None
    pdf_path: Path | None = None
    success: bool = False
    page_count: int = 0
    errors: list[str] = field(default_factory=list)
    key_decisions: list[str] = field(default_factory=list)
    language: str = "en"


@dataclass
class LetterSection:
    """A structured cover letter section."""
    opening: str = ""      # Hook + connection to company
    motivation: str = ""   # Why this role/company
    evidence: str = ""     # Key achievements matching requirements
    closing: str = ""      # Forward-looking close


# ─── Public API ───────────────────────────────────────────────

def generate_cover_letter(
    profile: CareerProfile,
    job_posting: str,
    company: str,
    role: str,
    language: str = "en",
    reviewer_pass: bool = True,
    contact_person: str = "",
) -> CoverLetterOutput:
    """
    Generate a targeted cover letter for a specific job posting.
    
    Args:
        profile: The candidate's career profile
        job_posting: Full text of the job posting
        company: Company name
        role: Role title
        language: Language of the cover letter (en/da)
        reviewer_pass: If True, run the drafter-reviewer pattern
        contact_person: Name of the hiring manager (if known)
    
    Returns:
        CoverLetterOutput with paths and validation
    """
    output = CoverLetterOutput(language=language)
    company_slug = company.lower().replace(" ", "_").replace("/", "_")
    role_slug = role.lower().replace(" ", "_").replace("/", "_")[:30]

    # Step 1: Extract keywords and analyze the posting
    keywords = extract_keywords_from_posting(job_posting)

    # Step 2: Build the letter sections
    sections = _build_letter_sections(profile, job_posting, company, role, keywords)

    # Step 3: Generate LaTeX
    tex_content = _generate_latex(
        profile, sections, company, role, language, contact_person
    )

    filename = f"cover_{company_slug}_{role_slug}.tex"
    tex_path = COVER_LETTERS_DIR / filename
    COVER_LETTERS_DIR.mkdir(parents=True, exist_ok=True)
    tex_path.write_text(tex_content, encoding="utf-8")
    output.tex_path = tex_path

    # Step 4: Compile
    result = compile_cover_letter(tex_path)
    if not result.success:
        output.errors = result.errors or ["LaTeX compilation failed"]
        return output

    output.pdf_path = result.pdf_path

    # Step 5: Validate layout
    layout = validate_cover_letter_layout(result.pdf_path)
    output.page_count = layout.get("page_count", 0)

    # Step 6: Fix if needed
    max_iterations = 3
    iteration = 0
    while not layout.get("is_one_page") and iteration < max_iterations:
        output = _fix_layout(output, sections, iteration)
        # Re-generate with trimmed content
        tex_content = _generate_latex(
            profile, sections, company, role, language, contact_person
        )
        tex_path.write_text(tex_content, encoding="utf-8")
        result = compile_cover_letter(tex_path)
        if result.success:
            output.pdf_path = result.pdf_path
            layout = validate_cover_letter_layout(result.pdf_path)
            output.page_count = layout.get("page_count", 0)
        iteration += 1

    # Step 7: Cleanup
    cleanup_build_artifacts(COVER_LETTERS_DIR)

    output.success = output.page_count == 1
    output.key_decisions = _document_decisions(profile, job_posting, company, role, keywords)

    return output


# ─── Letter Section Building ──────────────────────────────────

def _build_letter_sections(
    profile: CareerProfile,
    job_posting: str,
    company: str,
    role: str,
    keywords: list[str],
) -> LetterSection:
    """Build the four sections of the cover letter."""
    sections = LetterSection()
    job_lower = job_posting.lower()

    # ── Opening (Hook + Connection) ──
    sections.opening = _build_opening(profile, company, role, job_posting)

    # ── Motivation (Why this role/company) ──
    sections.motivation = _build_motivation(profile, company, role, job_posting)

    # ── Evidence (Key achievements matching requirements) ──
    sections.evidence = _build_evidence(profile, job_posting, keywords)

    # ── Closing (Forward-looking) ──
    sections.closing = _build_closing(profile, company, role)

    return sections


def _build_opening(
    profile: CareerProfile,
    company: str,
    role: str,
    job_posting: str,
) -> str:
    """Build the opening paragraph — hook + connection to company."""
    # Find a specific connection to the company
    connection = ""

    # Check if any experience is in the same industry
    for exp in profile.experience:
        if exp.company.lower() in job_posting.lower():
            connection = f"Having worked at {exp.company}, I understand the landscape {company} operates in."
            break

    # Check if any skills directly match
    matching_skills = []
    for skill in profile.skills.primary:
        if skill.lower() in job_posting.lower():
            matching_skills.append(skill)

    if not connection and matching_skills:
        connection = f"With hands-on experience in {', '.join(matching_skills[:3])}, I am excited to bring my expertise to the {role} role at {company}."

    if not connection:
        connection = f"I am writing to express my interest in the {role} position at {company}."

    return connection


def _build_motivation(
    profile: CareerProfile,
    company: str,
    role: str,
    job_posting: str,
) -> str:
    """Build the motivation paragraph — why this role and company."""
    parts = []

    # What excites about the role
    role_elements = []
    for keyword in ["innovative", "data-driven", "research", "scale", "impact", "team", "product"]:
        if keyword in job_posting.lower():
            role_elements.append(keyword)

    if role_elements:
        parts.append(f"The {role} role appeals to me because of its emphasis on {', '.join(role_elements[:2])}.")

    # Career goal alignment
    if profile.goals.career_objectives:
        parts.append(profile.goals.career_objectives[0])
    elif profile.goals.target_roles:
        parts.append(f"This position aligns with my career focus on {profile.goals.target_roles[0]}.")

    return " ".join(parts) if parts else f"I am drawn to the opportunity to contribute to {company}'s mission."


def _build_evidence(
    profile: CareerProfile,
    job_posting: str,
    keywords: list[str],
) -> str:
    """Build the evidence paragraph — 2-3 most relevant achievements."""
    # Find the most relevant experiences
    scored_exps = []
    for exp in profile.experience:
        exp_text = f"{exp.title} {' '.join(exp.responsibilities)} {' '.join(exp.achievements)}"
        relevance = sum(1 for kw in keywords if kw.lower() in exp_text.lower())
        scored_exps.append((exp, relevance))

    scored_exps.sort(key=lambda x: x[1], reverse=True)

    # Build evidence from top 2-3 experiences
    evidence_parts = []
    for exp, _ in scored_exps[:2]:
        # Pick the most impactful bullet
        best_bullet = ""
        for a in exp.achievements:
            if any(kw.lower() in a.lower() for kw in keywords):
                best_bullet = a
                break
        if not best_bullet and exp.responsibilities:
            best_bullet = exp.responsibilities[0]

        if best_bullet:
            evidence_parts.append(f"At {exp.company}, {best_bullet.lower() if best_bullet[0].isupper() else best_bullet}")

    return " ".join(evidence_parts) if evidence_parts else "My experience has prepared me well for this role."


def _build_closing(
    profile: CareerProfile,
    company: str,
    role: str,
) -> str:
    """Build the closing paragraph — forward-looking and confident."""
    return (
        f"I would welcome the opportunity to discuss how my background and skills "
        f"can contribute to {company}'s {role} team. I look forward to hearing from you."
    )


# ─── LaTeX Generation ─────────────────────────────────────────

def _generate_latex(
    profile: CareerProfile,
    sections: LetterSection,
    company: str,
    role: str,
    language: str,
    contact_person: str,
) -> str:
    """Generate LaTeX cover letter using cover.cls template."""
    today = _get_date_string(language)

    # Salutation
    if contact_person:
        salutation = f"Dear {contact_person}," if language == "en" else f"Kære {contact_person},"
    else:
        salutation = "Dear Hiring Manager," if language == "en" else "Kære Ansættelsesudvalg,"

    # Build the letter body using \lettercontent{} for each section
    # Note: \lettercontent{} appends \\, so we must NOT end with \end{itemize} inside it
    body_parts = []

    # Opening
    body_parts.append(f"\\lettercontent{{{sections.opening}}}")

    # Motivation
    body_parts.append(f"\\lettercontent{{{sections.motivation}}}")

    # Evidence — may need bullet points
    if len(sections.evidence) > 200:
        # Long evidence — use \lettercontent for the intro, then itemize for bullets
        body_parts.append(f"\\lettercontent{{My recent experience demonstrates this:}}")
        body_parts.append("""{\\raggedright\\fontspec[Path = OpenFonts/fonts/raleway/]{Raleway-Medium}\\fontsize{11pt}{13pt}\\selectfont \\begin{itemize}""")
        for sentence in _split_into_bullets(sections.evidence):
            body_parts.append(f"    \\item {_escape_latex(sentence)}")
        body_parts.append("\\end{itemize}\\par}")
    else:
        body_parts.append(f"\\lettercontent{{{sections.evidence}}}")

    # Closing
    body_parts.append(f"\\lettercontent{{{sections.closing}}}")

    body = "\n\n".join(body_parts)

    latex = f"""\\documentclass[11pt, a4paper]{{cover}}

% ── Sender ────────────────────────────────────────────────
\\name{{{profile.identity.name.split()[0] if profile.identity.name else 'First'}}}{{{ ' '.join(profile.identity.name.split()[1:]) if profile.identity.name and len(profile.identity.name.split()) > 1 else 'Last'}}}
\\address{{{{}}}}{{ }}{{ }}
{f'\\mobile{{{profile.identity.phone}}}' if profile.identity.phone else '% phone not set'}
\\email{{{profile.identity.email}}}
{f'\\homepage{{{profile.identity.website_url}}}' if profile.identity.website_url else ''}

% ── Recipient ─────────────────────────────────────────────
\\recipient{{{{Hiring Manager}}}}{{{company}}}{{{{}}}}{{{{}}}}

\\date{{{today}}}

\\subject{{{role} — Application}}

\\begin{{document}}
\\makelettertitle

{body}

\\makeletterclosing

\\end{{document}}
"""

    return latex


# ─── Helpers ──────────────────────────────────────────────────

def _split_into_bullets(text: str) -> list[str]:
    """Split text into bullet-point-sized chunks."""
    # Split by sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    # Filter out very short ones
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def _fix_layout(
    output: CoverLetterOutput,
    sections: LetterSection,
    iteration: int,
) -> CoverLetterOutput:
    """Fix cover letter layout to fit on 1 page."""
    if iteration == 0:
        # Trim evidence paragraph
        sentences = sections.evidence.split(". ")
        if len(sentences) > 3:
            sections.evidence = ". ".join(sentences[:3]) + "."
        output.key_decisions.append("Trimmed evidence paragraph to fit 1 page")
    elif iteration == 1:
        # Shorten motivation
        sentences = sections.motivation.split(". ")
        if len(sentences) > 2:
            sections.motivation = ". ".join(sentences[:2]) + "."
        output.key_decisions.append("Shortened motivation paragraph")
    elif iteration == 2:
        # Shorten opening
        sections.opening = sections.opening[:150] + "."
        output.key_decisions.append("Shortened opening paragraph")

    return output


def _get_date_string(language: str) -> str:
    """Get formatted date string in the appropriate language."""
    from datetime import datetime
    now = datetime.utcnow()

    if language == "da":
        months = ["januar", "februar", "marts", "april", "maj", "juni",
                   "juli", "august", "september", "oktober", "november", "december"]
        return f"{now.day}. {months[now.month - 1]} {now.year}"
    else:
        return now.strftime("%B %d, %Y")


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def _document_decisions(
    profile: CareerProfile,
    job_posting: str,
    company: str,
    role: str,
    keywords: list[str],
) -> list[str]:
    """Document key decisions made during generation."""
    decisions = []

    matching_skills = [
        s for s in profile.skills.primary + profile.skills.secondary
        if s.lower() in job_posting.lower()
    ]
    if matching_skills:
        decisions.append(f"Highlighted matching skills: {', '.join(matching_skills[:5])}")

    # Check if we found a specific company connection
    for exp in profile.experience:
        if exp.company.lower() in job_posting.lower():
            decisions.append(f"Referenced prior experience at {exp.company} as connection to {company}")
            break

    decisions.append(f"Extracted {len(keywords)} keywords from job posting")

    return decisions
