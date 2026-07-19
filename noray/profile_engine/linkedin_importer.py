"""
NORAY — LinkedIn Importer

Parse LinkedIn profile exports (PDF format) and extract structured data.
LinkedIn PDF exports have a predictable structure that we can reliably parse.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Any

from noray.shared.models import (
    CareerProfile, Education, Experience, Certification, Language,
)
from noray.profile_engine.cv_importer import _extract_from_pdf


# ─── Public API ───────────────────────────────────────────────

def parse_linkedin(file_path: Path) -> dict[str, Any]:
    """
    Parse a LinkedIn PDF export and extract structured data.
    
    Returns:
        Dict with raw_text, structured fields, source, and file path.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"LinkedIn export not found: {file_path}")

    raw_text = _extract_from_pdf(file_path)
    structured = _extract_linkedin_sections(raw_text)

    return {
        "raw_text": raw_text,
        "structured": structured,
        "source": "linkedin",
        "file": str(file_path),
    }


def import_linkedin_to_profile(file_path: Path, profile: CareerProfile) -> CareerProfile:
    """
    Parse a LinkedIn export and merge into existing profile.
    
    LinkedIn data is treated as a cross-reference source — it fills gaps
    but doesn't overwrite existing CV-sourced data.
    """
    parsed = parse_linkedin(file_path)
    structured = parsed["structured"]

    # Identity — fill gaps only
    if structured.get("name") and not profile.identity.name:
        profile.identity.name = structured["name"]
    if structured.get("headline") and not profile.identity.linkedin_url:
        profile.identity.linkedin_url = structured.get("linkedin_url", "")
    if structured.get("location") and not profile.identity.location.city:
        profile.identity.location.city = structured["location"]

    # Education — add if not already present
    for edu_data in structured.get("education", []):
        exists = any(
            e.institution.lower() == edu_data.get("institution", "").lower()
            for e in profile.education
        )
        if not exists and edu_data.get("institution"):
            profile.education.append(Education(
                degree=edu_data.get("degree", ""),
                field=edu_data.get("field", ""),
                institution=edu_data.get("institution", ""),
                start_year=edu_data.get("start_year", 0),
                end_year=edu_data.get("end_year", 0),
            ))

    # Experience — add if not already present
    for exp_data in structured.get("experience", []):
        exists = any(
            e.company.lower() == exp_data.get("company", "").lower() and
            e.title.lower() == exp_data.get("title", "").lower()
            for e in profile.experience
        )
        if not exists and exp_data.get("company"):
            profile.experience.append(Experience(
                title=exp_data.get("title", ""),
                company=exp_data.get("company", ""),
                location=exp_data.get("location", ""),
                start_date=exp_data.get("start_date", ""),
                end_date=exp_data.get("end_date", ""),
                responsibilities=exp_data.get("responsibilities", []),
            ))

    # Skills — merge
    all_existing = set()
    for cat in ["primary", "secondary", "domain", "tools"]:
        all_existing.update(s.lower() for s in getattr(profile.skills, cat))

    for skill in structured.get("skills", []):
        if skill.lower() not in all_existing:
            profile.skills.primary.append(skill)
            all_existing.add(skill.lower())

    # Certifications — add if not present
    existing_certs = {(c.name.lower(), c.issuer.lower()) for c in profile.certifications}
    for cert_data in structured.get("certifications", []):
        key = (cert_data.get("name", "").lower(), cert_data.get("issuer", "").lower())
        if key not in existing_certs and cert_data.get("name"):
            profile.certifications.append(Certification(
                name=cert_data.get("name", ""),
                issuer=cert_data.get("issuer", ""),
                date=cert_data.get("date", ""),
            ))

    # Languages — add if not present
    existing_langs = {l.language.lower() for l in profile.identity.languages}
    for lang in structured.get("languages", []):
        if lang.get("language", "").lower() not in existing_langs:
            profile.identity.languages.append(Language(
                language=lang.get("language", ""),
                proficiency=lang.get("proficiency", ""),
            ))

    # About section — store as behavioral signal
    if structured.get("about") and not profile.behavioral.work_style:
        profile.behavioral.work_style = f"[From LinkedIn About]\n{structured['about']}"

    if "linkedin_import" not in profile.meta.sources:
        profile.meta.sources.append("linkedin_import")

    return profile


# ─── LinkedIn Section Extraction ──────────────────────────────

def _extract_linkedin_sections(text: str) -> dict[str, Any]:
    """
    Extract structured sections from LinkedIn PDF export text.
    
    LinkedIn exports follow a predictable pattern:
    - Name (large text, first line)
    - Headline
    - Location
    - About
    - Experience
    - Education
    - Skills
    - Certifications
    - Languages
    """
    result = {}

    # Name — first substantial line
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        result["name"] = lines[0]

    # Headline — usually second line
    if len(lines) > 1:
        result["headline"] = lines[1]

    # Location — look for city/country pattern
    loc_match = re.search(r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)", text[:1000])
    if loc_match:
        result["location"] = loc_match.group(1)

    # About section
    result["about"] = _extract_linkedin_section(text, ["About", "Summary"])

    # Experience
    result["experience"] = _extract_linkedin_experience(text)

    # Education
    result["education"] = _extract_linkedin_education(text)

    # Skills
    result["skills"] = _extract_linkedin_skills(text)

    # Certifications
    result["certifications"] = _extract_linkedin_certifications(text)

    # Languages
    result["languages"] = _extract_linkedin_languages(text)

    return result


def _extract_linkedin_section(text: str, headers: list[str]) -> str:
    """Extract the content of a LinkedIn section by header name."""
    for header in headers:
        pattern = rf"(?:^|\n)\s*{re.escape(header)}\s*\n(.*?)(?=\n\s*[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s*\n|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""


def _extract_linkedin_experience(text: str) -> list[dict]:
    """Extract experience entries from LinkedIn export."""
    experience = []
    section = _extract_linkedin_section(text, ["Experience"])
    if not section:
        return experience

    # LinkedIn experience entries typically look like:
    # Title
    # Company · Type
    # Date range · Location
    # Description (optional)

    lines = section.split("\n")
    current = {}
    for line in lines:
        line = line.strip()
        if not line:
            if current.get("title") and current.get("company"):
                experience.append(current)
                current = {}
            continue

        # Date range pattern: "Jan 2020 - Present" or "2020 - 2022"
        date_match = re.match(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\s*[-–]\s*((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})|Present|Current)",
            line
        )
        if date_match:
            current["start_date"] = date_match.group(1)
            current["end_date"] = date_match.group(2)
            continue

        # Year-only date: "2020 - 2022"
        year_match = re.match(r"(\d{4})\s*[-–]\s*(\d{4}|Present|Current)", line)
        if year_match:
            current["start_date"] = year_match.group(1)
            current["end_date"] = year_match.group(2)
            continue

        # Company line: often has "·" separator
        if "·" in line:
            parts = line.split("·")
            if parts[0].strip() and not current.get("company"):
                current["company"] = parts[0].strip()
            continue

        # Title line: if we don't have a title yet and it's not a date
        if not current.get("title") and not re.match(r"^\d", line):
            current["title"] = line

    # Don't forget the last entry
    if current.get("title") and current.get("company"):
        experience.append(current)

    return experience


def _extract_linkedin_education(text: str) -> list[dict]:
    """Extract education entries from LinkedIn export."""
    education = []
    section = _extract_linkedin_section(text, ["Education"])
    if not section:
        return education

    lines = section.split("\n")
    current = {}
    for line in lines:
        line = line.strip()
        if not line:
            if current.get("institution"):
                education.append(current)
                current = {}
            continue

        # Year range
        year_match = re.match(r"(\d{4})\s*[-–]\s*(\d{4})", line)
        if year_match:
            current["start_year"] = int(year_match.group(1))
            current["end_year"] = int(year_match.group(2))
            continue

        # Degree line: "Bachelor of Science - BS, Computer Science"
        degree_match = re.match(r"(.+?)\s*[-–]\s*\w+\.?,?\s*(.+)?", line)
        if degree_match and not current.get("degree"):
            current["degree"] = degree_match.group(1).strip()
            if degree_match.group(2):
                current["field"] = degree_match.group(2).strip()
            continue

        # Institution name
        if not current.get("institution") and not re.match(r"^\d", line):
            current["institution"] = line

    if current.get("institution"):
        education.append(current)

    return education


def _extract_linkedin_skills(text: str) -> list[str]:
    """Extract skills from LinkedIn export."""
    skills = []
    section = _extract_linkedin_section(text, ["Skills"])
    if not section:
        return skills

    lines = section.split("\n")
    for line in lines:
        line = line.strip()
        if line and not line.startswith("Skills") and len(line) < 100:
            # Remove endorsement counts like "(5)"
            skill = re.sub(r"\s*\(\d+\)\s*$", "", line)
            if skill:
                skills.append(skill)

    return skills


def _extract_linkedin_certifications(text: str) -> list[dict]:
    """Extract certifications from LinkedIn export."""
    certifications = []
    section = _extract_linkedin_section(text, ["Licenses & Certifications", "Certifications"])
    if not section:
        return certifications

    lines = section.split("\n")
    current = {}
    for line in lines:
        line = line.strip()
        if not line:
            if current.get("name"):
                certifications.append(current)
                current = {}
            continue

        # Date pattern: "Issued Jan 2023"
        date_match = re.match(r"Issued\s+(.+)", line, re.IGNORECASE)
        if date_match:
            current["date"] = date_match.group(1)
            continue

        # Issuer line (usually after the cert name)
        if current.get("name") and not current.get("issuer"):
            current["issuer"] = line
            continue

        # Cert name
        if not current.get("name"):
            current["name"] = line

    if current.get("name"):
        certifications.append(current)

    return certifications


def _extract_linkedin_languages(text: str) -> list[dict]:
    """Extract languages from LinkedIn export."""
    languages = []
    section = _extract_linkedin_section(text, ["Languages"])
    if not section:
        return languages

    lines = section.split("\n")
    current = {}
    for line in lines:
        line = line.strip()
        if not line:
            if current.get("language"):
                languages.append(current)
                current = {}
            continue

        # Proficiency: "Professional working proficiency"
        prof_match = re.match(r"(.+?)\s*(?:proficiency|level)", line, re.IGNORECASE)
        if prof_match and current.get("language"):
            current["proficiency"] = line
            continue

        # Language name
        if not current.get("language"):
            current["language"] = line

    if current.get("language"):
        languages.append(current)

    return languages
