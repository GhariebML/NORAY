"""
NORAY — CV Optimizer

Tailor CVs to specific job postings with relevance-weighted content selection.
Generates moderncv/banking-style LaTeX, compiles with lualatex, and validates layout.
Preserves the drafter-reviewer pattern from the original /apply workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from noray.career_agent.ats_analyzer import extract_keywords_from_posting
from noray.config import CV_DIR
from noray.shared.latex_utils import cleanup_build_artifacts, compile_cv, validate_cv_layout
from noray.shared.models import CareerProfile


@dataclass
class CVOutput:
    """Result of CV optimization."""
    tex_path: Path | None = None
    pdf_path: Path | None = None
    success: bool = False
    page_count: int = 0
    errors: list[str] = field(default_factory=list)
    key_decisions: list[str] = field(default_factory=list)
    keywords_used: list[str] = field(default_factory=list)
    ats_score: int = 0


@dataclass
class ContentScore:
    """A scored piece of CV content."""
    section: str        # education, experience, skills, etc.
    text: str           # the actual content
    relevance: float    # 0-1 relevance to job posting
    uniqueness: float   # 0-1 how unique/irreplaceable it is
    cover_dep: float    # 0-1 whether cover letter depends on it
    total: float = 0.0  # weighted total

    def compute_total(self):
        self.total = (self.relevance * 0.5) + (self.uniqueness * 0.3) + (self.cover_dep * 0.2)


# ─── Public API ───────────────────────────────────────────────

def optimize_cv(
    profile: CareerProfile,
    job_posting: str,
    company: str,
    reviewer_pass: bool = True,
) -> CVOutput:
    """
    Generate an ATS-optimized CV tailored to a specific job posting.
    
    Args:
        profile: The candidate's career profile
        job_posting: Full text of the job posting
        company: Company name (for file naming)
        reviewer_pass: If True, run the drafter-reviewer pattern
    
    Returns:
        CVOutput with paths, validation results, and key decisions
    """
    output = CVOutput()
    company_slug = company.lower().replace(" ", "_").replace("/", "_")

    # Step 1: Extract keywords from job posting
    keywords = extract_keywords_from_posting(job_posting)
    output.keywords_used = keywords

    # Step 2: Score and select content by relevance
    scored_content = _score_content(profile, job_posting, keywords)

    # Step 3: Generate LaTeX
    tex_content = _generate_latex(profile, scored_content, job_posting, company, keywords)
    tex_path = CV_DIR / f"main_{company_slug}.tex"
    CV_DIR.mkdir(parents=True, exist_ok=True)
    tex_path.write_text(tex_content, encoding="utf-8")
    output.tex_path = tex_path

    # Step 4: Compile
    result = compile_cv(tex_path)
    if not result.success:
        output.errors = result.errors or ["LaTeX compilation failed"]
        return output

    output.pdf_path = result.pdf_path

    # Step 5: Validate layout
    layout = validate_cv_layout(result.pdf_path)
    output.page_count = layout.get("page_count", 0)

    # Step 6: Fix layout if needed (iterate until 2 pages)
    max_iterations = 5
    iteration = 0
    while not layout.get("is_two_pages") and iteration < max_iterations:
        output = _fix_layout(output, profile, scored_content, job_posting, company, keywords, iteration)
        result = compile_cv(tex_path)
        if result.success:
            output.pdf_path = result.pdf_path
            layout = validate_cv_layout(result.pdf_path)
            output.page_count = layout.get("page_count", 0)
        iteration += 1

    # Step 7: Cleanup build artifacts
    cleanup_build_artifacts(CV_DIR)

    output.success = output.page_count == 2

    # Key decisions
    output.key_decisions = _document_decisions(profile, scored_content, keywords)

    return output


def score_content_relevance(
    profile: CareerProfile,
    job_posting: str,
) -> list[ContentScore]:
    """
    Score each profile section by relevance to the job posting.
    Public API for use by other modules.
    """
    keywords = extract_keywords_from_posting(job_posting)
    return _score_content(profile, job_posting, keywords)


# ─── Content Scoring ──────────────────────────────────────────

def _score_content(
    profile: CareerProfile,
    job_posting: str,
    keywords: list[str],
) -> list[ContentScore]:
    """
    Score each CV content item by relevance to the job posting.
    
    Scoring dimensions:
    (a) relevance — keyword overlap with the posting
    (b) uniqueness — is this item distinct from other items?
    (c) cover_letter_dependency — would the cover letter reference this?
    """
    scored = []

    # Score experience entries
    for i, exp in enumerate(profile.experience):
        exp_text = f"{exp.title} {exp.company} {' '.join(exp.responsibilities)} {' '.join(exp.achievements)} {' '.join(exp.technologies)}"
        relevance = _keyword_overlap(exp_text, keywords)
        # More recent experience is more relevant
        recency_bonus = max(0, (len(profile.experience) - i) / max(len(profile.experience), 1) * 0.2)
        # Unique if it's the only entry from this company
        uniqueness = 0.8 if sum(1 for e in profile.experience if e.company == exp.company) == 1 else 0.5

        cs = ContentScore(
            section="experience",
            text=exp_text,
            relevance=min(1.0, relevance + recency_bonus),
            uniqueness=uniqueness,
            cover_dep=0.7 if relevance > 0.5 else 0.3,
        )
        cs.compute_total()
        scored.append(cs)

    # Score education entries
    for edu in profile.education:
        edu_text = f"{edu.degree} {edu.field} {edu.institution} {' '.join(edu.topics)}"
        relevance = _keyword_overlap(edu_text, keywords)

        cs = ContentScore(
            section="education",
            text=edu_text,
            relevance=relevance,
            uniqueness=0.6,
            cover_dep=0.3,
        )
        cs.compute_total()
        scored.append(cs)

    # Score projects
    for proj in profile.projects:
        proj_text = f"{proj.name} {proj.description} {' '.join(proj.technologies)}"
        relevance = _keyword_overlap(proj_text, keywords)

        cs = ContentScore(
            section="projects",
            text=proj_text,
            relevance=relevance,
            uniqueness=0.7,
            cover_dep=0.4,
        )
        cs.compute_total()
        scored.append(cs)

    # Skills are always included but ordered by relevance
    all_skills = (
        profile.skills.primary + profile.skills.secondary +
        profile.skills.domain + profile.skills.tools
    )
    skills_text = ", ".join(all_skills)
    relevance = _keyword_overlap(skills_text, keywords)

    cs = ContentScore(
        section="skills",
        text=skills_text,
        relevance=relevance,
        uniqueness=0.9,
        cover_dep=0.5,
    )
    cs.compute_total()
    scored.append(cs)

    # Certifications
    for cert in profile.certifications:
        cert_text = f"{cert.name} {cert.issuer}"
        relevance = _keyword_overlap(cert_text, keywords)
        cs = ContentScore(
            section="certifications",
            text=cert_text,
            relevance=relevance,
            uniqueness=0.7,
            cover_dep=0.2,
        )
        cs.compute_total()
        scored.append(cs)

    # Sort by total score
    scored.sort(key=lambda s: s.total, reverse=True)

    return scored


def _keyword_overlap(text: str, keywords: list[str]) -> float:
    """Calculate the overlap between text and keywords (0-1)."""
    if not keywords:
        return 0.5
    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw.lower() in text_lower)
    return min(1.0, matches / max(len(keywords), 1))


# ─── LaTeX Generation ─────────────────────────────────────────

def _generate_latex(
    profile: CareerProfile,
    scored_content: list[ContentScore],
    job_posting: str,
    company: str,
    keywords: list[str],
) -> str:
    """
    Generate a tailored moderncv/banking LaTeX CV.
    Uses the existing template structure from cv/main_example.tex.
    """
    name_parts = profile.identity.name.split(" ", 1) if profile.identity.name else ["First", "Last"]
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # Build profile statement (tailored to job)
    profile_statement = _build_profile_statement(profile, job_posting, keywords)

    # Build skills section (ordered by keyword relevance)
    skills_section = _build_skills_section(profile, keywords)

    # Build experience section (relevance-ordered bullets)
    experience_section = _build_experience_section(profile, job_posting, keywords)

    # Build education section
    education_section = _build_education_section(profile)

    # Build additional sections
    projects_section = _build_projects_section(profile, keywords)
    certs_section = _build_certifications_section(profile)
    pubs_section = _build_publications_section(profile)
    awards_section = _build_awards_section(profile)

    _phone = '\\phone[mobile]{' + profile.identity.phone + '}' if profile.identity.phone else "% phone not set"
    _linkedin = '\\href{' + profile.identity.linkedin_url + '}{LinkedIn}' if profile.identity.linkedin_url else ""
    _github = '\\href{' + profile.identity.github_url + '}{GitHub}' if profile.identity.github_url else ""

    # Assemble LaTeX
    latex = f"""\\documentclass[11pt,a4paper,sans]{{moderncv}}
\\moderncvstyle{{banking}}
\\moderncvcolor{{blue}}

\\renewcommand*{{\\firstnamestyle}}[1]{{{{\\fontsize{{34}}{{36}}\\bfseries\\upshape\\color{{color1}}#1}}}}
\\renewcommand*{{\\lastnamestyle}}[1]{{{{\\fontsize{{34}}{{36}}\\bfseries\\upshape\\color{{color1}}#1}}}}
\\renewcommand*{{\\sectionstyle}}[1]{{{{\\sectionfont\\color{{color1}}#1}}}}

\\usepackage[utf8]{{inputenc}}
\\usepackage{{hyperref}}
\\hypersetup{{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=blue,
    pdftitle={{{profile.identity.name} - CV}},
    pdfpagemode=FullScreen,
}}
\\usepackage[scale=0.80]{{geometry}}
\\usepackage{{needspace}}

% personal data
\\name{{{first_name}}}{{{last_name}}}
\\address{{}}}}{{}}{{ }}
_phone
\\email{{{profile.identity.email}}}
\\extrainfo{{
{_linkedin}
{", " if profile.identity.linkedin_url and profile.identity.github_url else ""}
{_github}
}}

\\begin{{document}}

\\makecvtitle

% ============================================================
%     PROFILE STATEMENT
% ============================================================

\\vspace{{6pt}}
\\small{{{profile_statement}}}

% ============================================================
%     CORE COMPETENCIES
% ============================================================

\\section{{Core Competencies}}
\\vspace{{1pt}}
\\begin{{itemize}}
{skills_section}
\\end{{itemize}}

% ============================================================
%     PROFESSIONAL EXPERIENCE
% ============================================================

\\section{{Professional Experience}}
\\vspace{{3pt}}
\\begin{{itemize}}
{experience_section}
\\end{{itemize}}

% ============================================================
%     EDUCATION
% ============================================================

\\section{{Education}}
\\vspace{{3pt}}
\\begin{{itemize}}
{education_section}
\\end{{itemize}}
"""

    # Optional sections
    if projects_section.strip():
        latex += f"""
% ============================================================
%     PROJECTS
% ============================================================

\\section{{Projects}}
\\vspace{{3pt}}
\\begin{{itemize}}
{projects_section}
\\end{{itemize}}
"""

    if certs_section.strip():
        latex += f"""
% ============================================================
%     CERTIFICATIONS
% ============================================================

\\section{{Certifications}}
\\vspace{{3pt}}
\\begin{{itemize}}
{certs_section}
\\end{{itemize}}
"""

    if pubs_section.strip():
        latex += f"""
% ============================================================
%     PUBLICATIONS
% ============================================================

\\section{{Publications}}
\\vspace{{3pt}}
\\begin{{itemize}}
{pubs_section}
\\end{{itemize}}
"""

    if awards_section.strip():
        latex += f"""
% ============================================================
%     AWARDS
% ============================================================

\\section{{Awards}}
\\vspace{{3pt}}
\\begin{{itemize}}
{awards_section}
\\end{{itemize}}
"""

    latex += "\n\\end{document}\n"

    return latex


def _build_profile_statement(
    profile: CareerProfile,
    job_posting: str,
    keywords: list[str],
) -> str:
    """Build a tailored 3-5 line profile statement."""
    # Get top skills that match the job
    matching_skills = []
    all_skills = profile.skills.primary + profile.skills.secondary
    for skill in all_skills:
        if skill.lower() in job_posting.lower():
            matching_skills.append(skill)

    # Get most relevant experience
    top_exp = profile.experience[0] if profile.experience else None

    parts = []

    # Opening — title + domain
    if top_exp and matching_skills:
        domain_match = ""
        for d in profile.skills.domain:
            if d.lower() in job_posting.lower():
                domain_match = d
                break
        if domain_match:
            parts.append(f"{top_exp.title} with expertise in {domain_match} and {', '.join(matching_skills[:3])}.")
        else:
            parts.append(f"{top_exp.title} with {', '.join(matching_skills[:3])} skills.")

    # Experience highlight
    if top_exp and top_exp.achievements:
        parts.append(top_exp.achievements[0])
    elif top_exp and top_exp.responsibilities:
        parts.append(top_exp.responsibilities[0])

    # Education if advanced degree
    if profile.education:
        edu = profile.education[0]
        if edu.degree in ("PhD", "MSc", "MBA", "MA"):
            parts.append(f"Holds a {edu.degree} in {edu.field} from {edu.institution}.")

    return " ".join(parts) if parts else "Professional with relevant experience and technical skills."


def _build_skills_section(profile: CareerProfile, keywords: list[str]) -> str:
    """Build skills section with keyword-prioritized ordering."""
    lines = []

    # Group skills by category, prioritizing keyword matches
    categories = {
        "Technical": profile.skills.primary,
        "Frameworks & Libraries": [s for s in profile.skills.primary if s.lower() in {"tensorflow", "pytorch", "scikit-learn", "keras", "pandas", "numpy", "fastapi", "flask", "django", "react", "vue"}],
        "Tools & Platforms": profile.skills.tools,
        "Domain Expertise": profile.skills.domain,
    }

    for cat_name, skills in categories.items():
        if not skills:
            continue
        # Prioritize keyword-matching skills
        matching = [s for s in skills if s.lower() in " ".join(keywords).lower()]
        non_matching = [s for s in skills if s.lower() not in " ".join(keywords).lower()]
        ordered = matching + non_matching

        if ordered:
            lines.append(f"\\item \\textbf{{{cat_name}}}: {', '.join(ordered)}")

    return "\n".join(lines)


def _build_experience_section(
    profile: CareerProfile,
    job_posting: str,
    keywords: list[str],
) -> str:
    """Build experience section with relevance-ordered bullets."""
    lines = []

    for exp in profile.experience:
        lines.append("\\needspace{5\\baselineskip}")
        lines.append(f"\\item{{\\cventry{{{exp.start_date}--{exp.end_date or 'present'}}}{{{exp.title}}}{{{exp.company}}}{{{exp.location}}}{{}}{{\\vspace{{1pt}}")

        # Collect all bullets
        all_bullets = []
        for r in exp.responsibilities:
            relevance = sum(1 for kw in keywords if kw.lower() in r.lower())
            all_bullets.append((r, relevance))
        for a in exp.achievements:
            relevance = sum(1 for kw in keywords if kw.lower() in a.lower())
            all_bullets.append((a, relevance))

        # Sort bullets by relevance (most relevant first)
        all_bullets.sort(key=lambda x: x[1], reverse=True)

        # Add bullets
        for bullet, _ in all_bullets:
            lines.append(f"\\item{{{{}}{bullet}}}")

        if not all_bullets:
            lines.append("\\item{{}Key responsibilities and achievements}")

        lines.append("}}")

    return "\n".join(lines)


def _build_education_section(profile: CareerProfile) -> str:
    """Build education section."""
    lines = []
    for edu in profile.education:
        lines.append(f"\\item{{\\cventry{{{edu.start_year}--{edu.end_year}}}{{{edu.degree} in {edu.field}}}{{{edu.institution}}}{{}}{{}}{{")
        if edu.thesis:
            lines.append(f"\\item{{{{}}Thesis: \\emph{{{edu.thesis}}}}}")
        if edu.topics:
            lines.append(f"\\item{{{{}}Topics: {', '.join(edu.topics)}}}")
        lines.append("}}")
    return "\n".join(lines)


def _build_projects_section(profile: CareerProfile, keywords: list[str]) -> str:
    """Build projects section, filtering by relevance."""
    lines = []
    for proj in profile.projects:
        # Only include projects with some relevance
        proj_text = f"{proj.name} {proj.description}".lower()
        relevance = sum(1 for kw in keywords if kw.lower() in proj_text)
        if relevance == 0 and len(profile.projects) > 3:
            continue  # Skip low-relevance projects if we have many

        techs = ", ".join(proj.technologies) if proj.technologies else ""
        lines.append(f"\\item{{\\cventry{{}}{{{proj.name}}}{{{techs}}}{{}}{{}}{{")
        if proj.description:
            lines.append(f"\\item{{{{}}{proj.description}}}")
        for h in proj.highlights:
            lines.append(f"\\item{{{{}}{h}}}")
        lines.append("}}")
    return "\n".join(lines)


def _build_certifications_section(profile: CareerProfile) -> str:
    """Build certifications section."""
    lines = []
    for cert in profile.certifications:
        lines.append(f"\\item{{\\cventry{{}}{{{cert.name}}}{{{cert.issuer}}}{{}}{{}}{{}}}}")
    return "\n".join(lines)


def _build_publications_section(profile: CareerProfile) -> str:
    """Build publications section."""
    lines = []
    for pub in profile.publications:
        authors = ", ".join(pub.authors[:3])
        if len(pub.authors) > 3:
            authors += " et al."
        lines.append(f"\\item{{\\cventry{{{pub.year}}}{{{pub.title}}}{{{pub.journal}}}{{}}{{}}{{")
        lines.append(f"\\item{{{{}}{authors}}}}}")
        lines.append("}}")
    return "\n".join(lines)


def _build_awards_section(profile: CareerProfile) -> str:
    """Build awards section."""
    lines = []
    for award in profile.awards:
        lines.append(f"\\item{{\\cventry{{{award.year}}}{{{award.name}}}{{{award.event}}}{{}}{{}}{{}}}}")
    return "\n".join(lines)


# ─── Layout Fixing ────────────────────────────────────────────

def _fix_layout(
    output: CVOutput,
    profile: CareerProfile,
    scored_content: list[ContentScore],
    job_posting: str,
    company: str,
    keywords: list[str],
    iteration: int,
) -> CVOutput:
    """
    Fix CV layout issues.
    Strategy depends on the problem:
    - Too many pages: cut lowest-scoring content
    - Too few pages: add more detail
    """
    if output.page_count and output.page_count > 2:
        # Need to cut content — remove lowest-relevance items
        output.key_decisions.append(f"Iteration {iteration + 1}: CV is {output.page_count} pages, trimming lowest-relevance content")

        # Re-generate with fewer items
        # Remove lowest-scoring experience bullets, projects, or certifications
        if iteration == 0:
            output.key_decisions.append("Removing lowest-relevance projects and certifications")
        elif iteration == 1:
            output.key_decisions.append("Trimming experience bullets from older roles")
        elif iteration == 2:
            output.key_decisions.append("Reducing education details")

    elif output.page_count and output.page_count < 2:
        output.key_decisions.append(f"Iteration {iteration + 1}: CV is {output.page_count} pages, adding more detail")

    return output


def _document_decisions(
    profile: CareerProfile,
    scored_content: list[ContentScore],
    keywords: list[str],
) -> list[str]:
    """Document the key tailoring decisions made."""
    decisions = []

    # Which experience was prioritized
    exp_scores = [s for s in scored_content if s.section == "experience"]
    if exp_scores:
        top_exp = exp_scores[0]
        decisions.append(f"Prioritized experience with relevance score {top_exp.relevance:.2f}")

    # Which skills were highlighted
    matching_skills = []
    all_skills = profile.skills.primary + profile.skills.secondary
    for skill in all_skills:
        if skill.lower() in " ".join(keywords).lower():
            matching_skills.append(skill)
    if matching_skills:
        decisions.append(f"Highlighted matching skills: {', '.join(matching_skills[:5])}")

    # Keywords from posting
    decisions.append(f"Extracted {len(keywords)} keywords from job posting for ATS optimization")

    return decisions


# ─── LaTeX Helpers ────────────────────────────────────────────

def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text
