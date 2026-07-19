"""
NORAY — CV Importer

Parse CV/resume files (PDF, LaTeX, DOCX) and extract structured data
for the career profile. Uses pattern matching for structured extraction
and provides raw text for LLM-based extraction at a higher layer.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Any

from noray.shared.models import (
    CareerProfile, Identity, Location, Language,
    Education, Experience, Skills, Certification, Award, Publication,
)


# ─── Public API ───────────────────────────────────────────────

def parse_cv(file_path: Path) -> dict[str, Any]:
    """
    Parse a CV file and extract structured data + raw text.
    
    Supports: PDF (.pdf), LaTeX (.tex), Word (.docx)
    
    Returns:
        Dict with:
        - raw_text: full text content for LLM extraction
        - structured: dict of pattern-extracted fields
        - source: file type
        - file: file path
    """
    if not file_path.exists():
        raise FileNotFoundError(f"CV file not found: {file_path}")

    suffix = file_path.suffix.lower()
    extractors = {
        ".pdf": _extract_from_pdf,
        ".tex": _extract_from_latex,
        ".docx": _extract_from_docx,
    }

    extractor = extractors.get(suffix)
    if not extractor:
        raise ValueError(f"Unsupported CV format: {suffix}. Supported: PDF, .tex, .docx")

    raw_text = extractor(file_path)
    structured = _pattern_extract(raw_text)

    return {
        "raw_text": raw_text,
        "structured": structured,
        "source": suffix.lstrip("."),
        "file": str(file_path),
    }


def import_cv_to_profile(file_path: Path, profile: CareerProfile) -> CareerProfile:
    """
    Parse a CV file and merge extracted data into an existing profile.
    
    Uses pattern matching for structured fields. For fields that pattern
    matching can't reliably extract, the raw_text is preserved for LLM
    extraction at a higher layer (profile_builder).
    
    Args:
        file_path: Path to the CV file
        profile: Existing CareerProfile to merge into
    
    Returns:
        Updated CareerProfile with new data merged in
    """
    parsed = parse_cv(file_path)
    structured = parsed["structured"]

    # Identity
    if structured.get("name") and not profile.identity.name:
        profile.identity.name = structured["name"]
    if structured.get("email") and not profile.identity.email:
        profile.identity.email = structured["email"]
    if structured.get("phone") and not profile.identity.phone:
        profile.identity.phone = structured["phone"]
    if structured.get("linkedin"):
        profile.identity.linkedin_url = structured["linkedin"]
    if structured.get("github"):
        profile.identity.github_url = structured["github"]
    if structured.get("location"):
        loc = structured["location"]
        if not profile.identity.location.city:
            profile.identity.location.city = loc
    if structured.get("languages"):
        existing_langs = {l.language.lower() for l in profile.identity.languages}
        for lang in structured["languages"]:
            if lang.lower() not in existing_langs:
                profile.identity.languages.append(Language(language=lang))
                existing_langs.add(lang.lower())

    # Education
    for edu_data in structured.get("education", []):
        if not _edu_exists(profile, edu_data):
            profile.education.append(Education(
                degree=edu_data.get("degree", ""),
                field=edu_data.get("field", ""),
                institution=edu_data.get("institution", ""),
                start_year=edu_data.get("start_year", 0),
                end_year=edu_data.get("end_year", 0),
                thesis=edu_data.get("thesis", ""),
            ))

    # Experience
    for exp_data in structured.get("experience", []):
        if not _exp_exists(profile, exp_data):
            profile.experience.append(Experience(
                title=exp_data.get("title", ""),
                company=exp_data.get("company", ""),
                location=exp_data.get("location", ""),
                start_date=exp_data.get("start_date", ""),
                end_date=exp_data.get("end_date", ""),
                responsibilities=exp_data.get("responsibilities", []),
            ))

    # Skills
    for category in ["primary", "secondary", "domain", "tools"]:
        existing = set(getattr(profile.skills, category))
        for skill in structured.get("skills", {}).get(category, []):
            if skill not in existing:
                getattr(profile.skills, category).append(skill)
                existing.add(skill)

    # Certifications
    for cert_data in structured.get("certifications", []):
        cert_key = (cert_data.get("name", "").lower(), cert_data.get("issuer", "").lower())
        existing_keys = {(c.name.lower(), c.issuer.lower()) for c in profile.certifications}
        if cert_key not in existing_keys:
            profile.certifications.append(Certification(
                name=cert_data.get("name", ""),
                issuer=cert_data.get("issuer", ""),
                date=cert_data.get("date", ""),
            ))

    # Publications
    for pub_data in structured.get("publications", []):
        existing_titles = {p.title.lower() for p in profile.publications}
        if pub_data.get("title", "").lower() not in existing_titles:
            profile.publications.append(Publication(
                authors=pub_data.get("authors", []),
                title=pub_data.get("title", ""),
                journal=pub_data.get("journal", ""),
                year=pub_data.get("year", 0),
            ))

    # Awards
    for award_data in structured.get("awards", []):
        existing_keys = {(a.name.lower(), a.event.lower()) for a in profile.awards}
        key = (award_data.get("name", "").lower(), award_data.get("event", "").lower())
        if key not in existing_keys:
            profile.awards.append(Award(
                name=award_data.get("name", ""),
                event=award_data.get("event", ""),
                year=award_data.get("year", 0),
            ))

    # Mark source
    if "cv_import" not in profile.meta.sources:
        profile.meta.sources.append("cv_import")

    return profile


# ─── File Extractors ──────────────────────────────────────────

def _extract_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""
    # Try pdfplumber first (better layout preservation)
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)
    except ImportError:
        pass

    # Fallback to PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(str(file_path))
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n\n".join(pages)
    except ImportError:
        pass

    raise ImportError(
        "No PDF library available. Install one of:\n"
        "  pip install pdfplumber\n"
        "  pip install pymupdf"
    )


def _extract_from_latex(file_path: Path) -> str:
    """
    Extract text content from a LaTeX file.
    Strips LaTeX commands but preserves structure.
    """
    content = file_path.read_text(encoding="utf-8")

    # Remove comments
    content = re.sub(r"%.*$", "", content, flags=re.MULTILINE)

    # Remove common LaTeX commands but keep their content
    strip_commands = [
        r"\\textbf\{([^}]*)\}",
        r"\\textit\{([^}]*)\}",
        r"\\emph\{([^}]*)\}",
        r"\\text\{([^}]*)\}",
        r"\\href\{[^}]*\}\{([^}]*)\}",
    ]
    for cmd in strip_commands:
        content = re.sub(cmd, r"\1", content)

    # Remove common LaTeX environments content wrappers
    content = re.sub(r"\\begin\{(?:center|flushleft|flushright)\}", "", content)
    content = re.sub(r"\\end\{(?:center|flushleft|flushright)\}", "", content)

    # Remove common commands without arguments
    remove_cmds = [
        r"\\newpage", r"\\pagebreak", r"\\noindent", r"\\vspace\{[^}]*\}",
        r"\\hspace\{[^}]*\}", r"\\par", r"\\\\", r"\\&",
    ]
    for cmd in remove_cmds:
        content = re.sub(cmd, "", content)

    # Remove remaining backslash commands (but keep content in braces)
    content = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^}]*)\})?", r"\1", content)

    # Clean up extra whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = re.sub(r"  +", " ", content)

    return content.strip()


def _extract_from_docx(file_path: Path) -> str:
    """Extract text from a DOCX file."""
    try:
        import docx
        doc = docx.Document(str(file_path))
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        return "\n\n".join(paragraphs)
    except ImportError:
        raise ImportError(
            "python-docx not installed. Install with:\n"
            "  pip install python-docx"
        )


# ─── Pattern Extraction ───────────────────────────────────────

def _pattern_extract(text: str) -> dict[str, Any]:
    """
    Extract structured data from CV text using regex patterns.
    This is a best-effort extraction. For complex CVs, the raw text
    should be sent to the LLM for more accurate extraction.
    """
    result = {}

    # Contact info
    result["name"] = _extract_name(text)
    result["email"] = _extract_email(text)
    result["phone"] = _extract_phone(text)
    result["linkedin"] = _extract_linkedin(text)
    result["github"] = _extract_github(text)
    result["location"] = _extract_location(text)

    # Sections
    result["education"] = _extract_education_section(text)
    result["experience"] = _extract_experience_section(text)
    result["skills"] = _extract_skills_section(text)
    result["certifications"] = _extract_certifications_section(text)
    result["publications"] = _extract_publications_section(text)
    result["awards"] = _extract_awards_section(text)
    result["languages"] = _extract_languages(text)

    return result


def _extract_name(text: str) -> str:
    """Extract name — usually the first non-empty line or largest text."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return ""

    # Skip common non-name lines
    skip_patterns = [
        r"^[\d\s\+\-\(\)]+$",  # Phone numbers
        r"@",  # Email lines
        r"https?://",  # URLs
        r"^(curriculum vitae|resume|cv)$",  # Headers
        r"^[A-Z\s]+$",  # ALL CAPS section headers (but not single names)
    ]

    for line in lines[:5]:
        line_clean = line.strip().rstrip("|").strip()
        if not line_clean:
            continue
        # Skip if it matches any skip pattern
        if any(re.search(p, line_clean, re.IGNORECASE) for p in skip_patterns):
            continue
        # A name is typically 2-5 words, mostly alphabetic
        words = line_clean.split()
        if 2 <= len(words) <= 5 and all(w.replace(".", "").replace("-", "").isalpha() for w in words):
            return line_clean

    return ""


def _extract_email(text: str) -> str:
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    patterns = [
        r"\+?\d{1,3}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}",
        r"\(\d{3}\)\s*\d{3}[\-]\d{4}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return ""


def _extract_linkedin(text: str) -> str:
    match = re.search(r"linkedin\.com/in/[\w\-]+", text)
    if match:
        url = match.group(0)
        return f"https://{url}" if not url.startswith("http") else url
    return ""


def _extract_github(text: str) -> str:
    match = re.search(r"github\.com/[\w\-]+", text)
    if match:
        url = match.group(0)
        return f"https://{url}" if not url.startswith("http") else url
    return ""


def _extract_location(text: str) -> str:
    # Look for common location patterns near the top
    top_section = text[:500]
    patterns = [
        r"(?:^|\n)\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)",
        r"(?:Location|Address|City)[:\s]+(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, top_section)
        if match:
            return match.group(1).strip()
    return ""


def _extract_education_section(text: str) -> list[dict]:
    """Extract education entries from CV text."""
    education = []
    section = _find_section(text, ["education", "academic background", "qualifications"])
    if not section:
        return education

    # Pattern: Degree in Field, Institution, Year
    edu_patterns = [
        # "BSc in Computer Science, MIT, 2018-2022"
        r"(?:(?:BSc|MSc|BA|MA|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.|MBA|Doctor|Master|Bachelor)[^,\n]*?)\s*(?:in|,)\s*([^,\n]+?)(?:,\s*([^,\n]+?))?(?:,\s*(\d{4})\s*[-–]\s*(\d{4}|present|current))?",
        # "University of X — BSc Computer Science (2018-2022)"
        r"([^,\n]+?(?:University|Institut|School|College|Academy)[^,\n]*?)\s*[-–|]\s*([^,\n]+?)\s*\((\d{4})\s*[-–]\s*(\d{4}|present|current)\)",
    ]

    for pattern in edu_patterns:
        for match in re.finditer(pattern, section, re.IGNORECASE):
            groups = match.groups()
            edu = {}
            if len(groups) >= 2:
                edu["field"] = groups[0].strip() if groups[0] else ""
                edu["institution"] = groups[1].strip() if groups[1] else ""
            if len(groups) >= 4:
                edu["start_year"] = int(groups[2]) if groups[2] and groups[2].isdigit() else 0
                end = groups[3]
                edu["end_year"] = int(end) if end and end.isdigit() else 0

            # Try to extract degree level
            degree_match = re.search(r"(BSc|MSc|BA|MA|PhD|B\.S\.|M\.S\.|MBA|Doctor|Master|Bachelor)", section, re.IGNORECASE)
            if degree_match:
                edu["degree"] = degree_match.group(1)

            if edu.get("institution") or edu.get("field"):
                education.append(edu)

    return education


def _extract_experience_section(text: str) -> list[dict]:
    """Extract work experience entries from CV text."""
    experience = []
    section = _find_section(text, [
        "experience", "work experience", "professional experience",
        "employment", "work history", "career",
    ])
    if not section:
        return experience

    # Look for job title patterns
    exp_patterns = [
        # "Software Engineer at Google (2020 - present)"
        r"([^,\n]+?)\s+(?:at|@)\s+([^,\n(]+?)\s*\((\d{4}(?:[-–]\d{2})?)\s*[-–]\s*(\d{4}(?:[-–]\d{2})?|present|current)\)",
        # "Software Engineer | Google | 2020 - present"
        r"([^|,\n]+?)\s*\|\s*([^|,\n]+?)\s*\|\s*(\d{4}(?:[-–]\d{2})?)\s*[-–]\s*(\d{4}(?:[-–]\d{2})?|present|current)",
    ]

    for pattern in exp_patterns:
        for match in re.finditer(pattern, section, re.IGNORECASE):
            groups = match.groups()
            if len(groups) >= 4:
                experience.append({
                    "title": groups[0].strip(),
                    "company": groups[1].strip(),
                    "start_date": groups[2].strip(),
                    "end_date": groups[3].strip(),
                })

    return experience


def _extract_skills_section(text: str) -> dict[str, list[str]]:
    """Extract skills from CV text."""
    skills = {"primary": [], "secondary": [], "domain": [], "tools": []}
    section = _find_section(text, ["skills", "technical skills", "competencies", "technologies"])
    if not section:
        return skills

    # Split by common delimiters
    lines = section.split("\n")
    all_skills = []
    for line in lines:
        # Remove bullet points and headers
        line = re.sub(r"^[\s\-\*•]+", "", line).strip()
        if not line or len(line) > 200:  # Skip headers or very long lines
            continue
        # Split by commas, semicolons, or pipes
        items = re.split(r"[,;|]", line)
        for item in items:
            item = item.strip()
            if item and len(item) < 50:  # Reasonable skill name length
                # Remove category prefixes like "Languages:" or "Tools:"
                item = re.sub(r"^(?:Languages?|Tools?|Frameworks?|Platforms?|Databases?|Other)[:\s]+", "", item, flags=re.IGNORECASE)
                if item:
                    all_skills.append(item)

    # Categorize based on common patterns
    programming = {"python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", "rust", "swift", "kotlin", "r", "matlab", "scala", "php", "perl"}
    tools = {"git", "docker", "kubernetes", "aws", "azure", "gcp", "linux", "windows", "jira", "confluence", "slack", "figma", "tableau", "powerbi"}

    for skill in all_skills:
        skill_lower = skill.lower()
        if skill_lower in programming or any(lang in skill_lower for lang in ["python", "java", "script"]):
            skills["primary"].append(skill)
        elif skill_lower in tools or any(t in skill_lower for t in ["docker", "kubernetes", "aws", "cloud"]):
            skills["tools"].append(skill)
        else:
            skills["primary"].append(skill)

    return skills


def _extract_certifications_section(text: str) -> list[dict]:
    """Extract certifications from CV text."""
    certifications = []
    section = _find_section(text, ["certifications", "certificates", "courses", "training"])
    if not section:
        return certifications

    lines = section.split("\n")
    for line in lines:
        line = re.sub(r"^[\s\-\*•]+", "", line).strip()
        if not line or len(line) > 200:
            continue

        # Try to extract: Name, Issuer, Date
        cert_match = re.match(r"(.+?)(?:,|\s*[-–|]\s*)(.+?)(?:,|\s*[-–|]\s*)(\d{4}(?:[-–]\d{2})?)", line)
        if cert_match:
            certifications.append({
                "name": cert_match.group(1).strip(),
                "issuer": cert_match.group(2).strip(),
                "date": cert_match.group(3).strip(),
            })
        elif len(line) > 5:
            certifications.append({"name": line, "issuer": "", "date": ""})

    return certifications


def _extract_publications_section(text: str) -> list[dict]:
    """Extract publications from CV text."""
    publications = []
    section = _find_section(text, ["publications", "papers", "research"])
    if not section:
        return publications

    lines = section.split("\n")
    for line in lines:
        line = re.sub(r"^[\s\-\*•]+", "", line).strip()
        if not line or len(line) > 500:
            continue

        # Try academic citation format: Authors (Year). Title. Journal.
        pub_match = re.match(r"(.+?)\s*\((\d{4})\)\.\s*(.+?)\.\s*(.+?)\.?", line)
        if pub_match:
            authors = [a.strip() for a in pub_match.group(1).split(",")]
            publications.append({
                "authors": authors,
                "year": int(pub_match.group(2)),
                "title": pub_match.group(3).strip(),
                "journal": pub_match.group(4).strip(),
            })
        elif len(line) > 20:
            publications.append({"authors": [], "title": line, "journal": "", "year": 0})

    return publications


def _extract_awards_section(text: str) -> list[dict]:
    """Extract awards from CV text."""
    awards = []
    section = _find_section(text, ["awards", "honors", "achievements", "distinctions"])
    if not section:
        return awards

    lines = section.split("\n")
    for line in lines:
        line = re.sub(r"^[\s\-\*•]+", "", line).strip()
        if not line or len(line) > 200:
            continue

        # Try: Award - Event (Year)
        award_match = re.match(r"(.+?)(?:\s*[-–|]\s*(.+?))?\s*\((\d{4})\)", line)
        if award_match:
            awards.append({
                "name": award_match.group(1).strip(),
                "event": (award_match.group(2) or "").strip(),
                "year": int(award_match.group(3)),
            })
        elif len(line) > 5:
            awards.append({"name": line, "event": "", "year": 0})

    return awards


def _extract_languages(text: str) -> list[str]:
    """Extract spoken languages from CV text."""
    section = _find_section(text, ["languages", "language skills", "spoken languages"])
    if not section:
        return []

    languages = []
    # Remove proficiency markers
    section_clean = re.sub(r"\((?:native|fluent|intermediate|basic|beginner|advanced|proficient|C[12]|B[12]|A[12])\)", "", section, flags=re.IGNORECASE)
    items = re.split(r"[,;\n]", section_clean)
    for item in items:
        item = re.sub(r"^[\s\-\*•]+", "", item).strip()
        if item and len(item) < 30 and not re.match(r"^(languages?|spoken)", item, re.IGNORECASE):
            languages.append(item)

    return languages


# ─── Helpers ──────────────────────────────────────────────────

def _find_section(text: str, headers: list[str]) -> str | None:
    """Find a section in the CV text by its header."""
    text_lower = text.lower()
    for header in headers:
        # Look for the header with common formatting
        patterns = [
            rf"(?:^|\n)\s*#?\s*{re.escape(header)}\s*#?\s*\n(.*?)(?=\n\s*#?\s*(?:[A-Z]|{'|'.join(h for h in headers if h != header)})\s*#?\s*\n|\Z)",
            rf"(?:^|\n)\s*{re.escape(header)}\s*[:\-–]?\s*\n(.*?)(?=\n\s*(?:[A-Z])\w*\s*[:\-–]?\s*\n|\Z)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return None


def _edu_exists(profile: CareerProfile, edu_data: dict) -> bool:
    """Check if an education entry already exists in the profile."""
    for edu in profile.education:
        if (edu.institution.lower() == edu_data.get("institution", "").lower() and
            edu.degree.lower() == edu_data.get("degree", "").lower()):
            return True
    return False


def _exp_exists(profile: CareerProfile, exp_data: dict) -> bool:
    """Check if an experience entry already exists in the profile."""
    for exp in profile.experience:
        if (exp.company.lower() == exp_data.get("company", "").lower() and
            exp.title.lower() == exp_data.get("title", "").lower()):
            return True
    return False
