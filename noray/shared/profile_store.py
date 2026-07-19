"""
NORAY — Profile Store

Read/write career_profile.json with validation.
Provides migration from legacy skill files to JSON.
Provides diff/merge for incremental updates from importers.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Any

from noray.config import CAREER_PROFILE_PATH, LEGACY_SKILL_FILES, SKILL_FILES_DIR
from noray.shared.models import (
    CareerProfile, ProfileMeta, Identity, Location, Language,
    Education, Experience, Project, Skills, Certification,
    Award, Publication, Behavioral, CareerGoals, ScholarshipGoals,
    GitHubProfile,
)


# ─── Core CRUD ────────────────────────────────────────────────

def load_profile(path: Path = CAREER_PROFILE_PATH) -> CareerProfile:
    """Load career profile from JSON file. Returns empty profile if not found."""
    if not path.exists():
        return CareerProfile(meta=ProfileMeta(
            version="1.0.0",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        ))
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CareerProfile.model_validate(data)


def save_profile(
    profile: CareerProfile,
    path: Path = CAREER_PROFILE_PATH,
    source: str = "",
) -> None:
    """Save career profile to JSON file with updated timestamp."""
    profile.meta.updated_at = datetime.utcnow().isoformat()
    if source and source not in profile.meta.sources:
        profile.meta.sources.append(source)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(mode="json"), f, indent=2, ensure_ascii=False)


def profile_exists(path: Path = CAREER_PROFILE_PATH) -> bool:
    """Check if career_profile.json exists and has meaningful content."""
    if not path.exists() or path.stat().st_size < 50:
        return False
    try:
        profile = load_profile(path)
        return bool(profile.identity.name)
    except (json.JSONDecodeError, Exception):
        return False


def backup_profile(path: Path = CAREER_PROFILE_PATH) -> Path | None:
    """Create a timestamped backup of the profile. Returns backup path."""
    if not path.exists():
        return None
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = path.parent / f"career_profile_backup_{timestamp}.json"
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


# ─── Merge / Diff ─────────────────────────────────────────────

def merge_profile(
    existing: CareerProfile,
    incoming: CareerProfile,
    source: str = "",
    overwrite: bool = False,
) -> CareerProfile:
    """
    Merge an incoming profile into an existing one.
    
    Rules:
    - Empty fields in incoming never overwrite non-empty fields in existing
    - Lists are merged (deduped by content, not replaced)
    - If overwrite=True, incoming values take precedence
    - source is added to meta.sources
    """
    if source:
        incoming.meta.sources = list(set(incoming.meta.sources + [source]))

    # Identity — only overwrite non-empty
    if incoming.identity.name and (overwrite or not existing.identity.name):
        existing.identity.name = incoming.identity.name
    if incoming.identity.email and (overwrite or not existing.identity.email):
        existing.identity.email = incoming.identity.email
    if incoming.identity.phone and (overwrite or not existing.identity.phone):
        existing.identity.phone = incoming.identity.phone
    if incoming.identity.location.city and (overwrite or not existing.identity.location.city):
        existing.identity.location.city = incoming.identity.location.city
    if incoming.identity.location.country and (overwrite or not existing.identity.location.country):
        existing.identity.location.country = incoming.identity.location.country
    if incoming.identity.linkedin_url and (overwrite or not existing.identity.linkedin_url):
        existing.identity.linkedin_url = incoming.identity.linkedin_url
    if incoming.identity.github_url and (overwrite or not existing.identity.github_url):
        existing.identity.github_url = incoming.identity.github_url
    if incoming.identity.website_url and (overwrite or not existing.identity.website_url):
        existing.identity.website_url = incoming.identity.website_url

    # Languages — merge, dedup
    existing_langs = {l.language.lower() for l in existing.identity.languages}
    for lang in incoming.identity.languages:
        if lang.language.lower() not in existing_langs:
            existing.identity.languages.append(lang)
            existing_langs.add(lang.language.lower())

    # Education — merge by (institution, degree) key
    existing_edu_keys = {
        (e.institution.lower(), e.degree.lower()) for e in existing.education
    }
    for edu in incoming.education:
        key = (edu.institution.lower(), edu.degree.lower())
        if key not in existing_edu_keys or overwrite:
            existing.education.append(edu)
            existing_edu_keys.add(key)

    # Experience — merge by (company, title) key
    existing_exp_keys = {
        (e.company.lower(), e.title.lower()) for e in existing.experience
    }
    for exp in incoming.experience:
        key = (exp.company.lower(), exp.title.lower())
        if key not in existing_exp_keys or overwrite:
            existing.experience.append(exp)
            existing_exp_keys.add(key)

    # Projects — merge by name
    existing_proj_names = {p.name.lower() for p in existing.projects}
    for proj in incoming.projects:
        if proj.name.lower() not in existing_proj_names or overwrite:
            existing.projects.append(proj)
            existing_proj_names.add(proj.name.lower())

    # Skills — merge lists
    for category in ["primary", "secondary", "domain", "tools"]:
        existing_skills = set(getattr(existing.skills, category))
        for skill in getattr(incoming.skills, category):
            if skill not in existing_skills:
                getattr(existing.skills, category).append(skill)
                existing_skills.add(skill)

    # Certifications — merge by (name, issuer) key
    existing_cert_keys = {
        (c.name.lower(), c.issuer.lower()) for c in existing.certifications
    }
    for cert in incoming.certifications:
        key = (cert.name.lower(), cert.issuer.lower())
        if key not in existing_cert_keys or overwrite:
            existing.certifications.append(cert)
            existing_cert_keys.add(key)

    # Awards — merge by (name, event) key
    existing_award_keys = {
        (a.name.lower(), a.event.lower()) for a in existing.awards
    }
    for award in incoming.awards:
        key = (award.name.lower(), award.event.lower())
        if key not in existing_award_keys or overwrite:
            existing.awards.append(award)
            existing_award_keys.add(key)

    # Publications — merge by title
    existing_pub_titles = {p.title.lower() for p in existing.publications}
    for pub in incoming.publications:
        if pub.title.lower() not in existing_pub_titles or overwrite:
            existing.publications.append(pub)
            existing_pub_titles.add(pub.title.lower())

    # Behavioral — only overwrite non-empty
    if incoming.behavioral.assessment_type and (overwrite or not existing.behavioral.assessment_type):
        existing.behavioral.assessment_type = incoming.behavioral.assessment_type
    if incoming.behavioral.work_style and (overwrite or not existing.behavioral.work_style):
        existing.behavioral.work_style = incoming.behavioral.work_style
    if incoming.behavioral.management_style and (overwrite or not existing.behavioral.management_style):
        existing.behavioral.management_style = incoming.behavioral.management_style
    if incoming.behavioral.ideal_environment and (overwrite or not existing.behavioral.ideal_environment):
        existing.behavioral.ideal_environment = incoming.behavioral.ideal_environment
    for trait in incoming.behavioral.traits:
        if trait not in existing.behavioral.traits:
            existing.behavioral.traits.append(trait)
    for s in incoming.behavioral.strengths:
        if s not in existing.behavioral.strengths:
            existing.behavioral.strengths.append(s)
    for g in incoming.behavioral.growth_areas:
        if g not in existing.behavioral.growth_areas:
            existing.behavioral.growth_areas.append(g)

    # Goals
    for field_name in ["career_objectives", "target_roles", "target_sectors", "deal_breakers"]:
        existing_list = getattr(existing.goals, field_name)
        existing_set = set(existing_list)
        for item in getattr(incoming.goals, field_name):
            if item not in existing_set:
                existing_list.append(item)

    # Scholarship goals
    for field_name in ["target_degrees", "target_countries", "research_interests", "deadlines"]:
        existing_list = getattr(existing.scholarship_goals, field_name)
        existing_set = set(existing_list)
        for item in getattr(incoming.scholarship_goals, field_name):
            if item not in existing_set:
                existing_list.append(item)

    # GitHub
    if incoming.github.username and (overwrite or not existing.github.username):
        existing.github.username = incoming.github.username
    if incoming.github.repos:
        existing_repo_urls = {r.get("url", "") for r in existing.github.repos}
        for repo in incoming.github.repos:
            if repo.get("url", "") not in existing_repo_urls:
                existing.github.repos.append(repo)
    if incoming.github.languages:
        existing_langs = set(existing.github.languages)
        for lang in incoming.github.languages:
            if lang not in existing_langs:
                existing.github.languages.append(lang)

    # Update sources
    existing.meta.sources = list(set(existing.meta.sources + incoming.meta.sources))

    return existing


def get_profile_diff(existing: CareerProfile, incoming: CareerProfile) -> dict[str, list[str]]:
    """
    Compare two profiles and return what's new in incoming that's not in existing.
    Returns dict of section -> list of new item descriptions.
    """
    diff = {}

    # Identity
    identity_diff = []
    if incoming.identity.name and incoming.identity.name != existing.identity.name:
        identity_diff.append(f"Name: {existing.identity.name} → {incoming.identity.name}")
    if incoming.identity.email and incoming.identity.email != existing.identity.email:
        identity_diff.append(f"Email: {existing.identity.email} → {incoming.identity.email}")
    if identity_diff:
        diff["identity"] = identity_diff

    # Education
    existing_keys = {(e.institution.lower(), e.degree.lower()) for e in existing.education}
    new_edus = [
        f"{e.degree} in {e.field} — {e.institution}"
        for e in incoming.education
        if (e.institution.lower(), e.degree.lower()) not in existing_keys
    ]
    if new_edus:
        diff["education"] = new_edus

    # Experience
    existing_exp = {(e.company.lower(), e.title.lower()) for e in existing.experience}
    new_exps = [
        f"{e.title} at {e.company}"
        for e in incoming.experience
        if (e.company.lower(), e.title.lower()) not in existing_exp
    ]
    if new_exps:
        diff["experience"] = new_exps

    # Skills
    all_existing_skills = set()
    for cat in ["primary", "secondary", "domain", "tools"]:
        all_existing_skills.update(s.lower() for s in getattr(existing.skills, cat))
    new_skills = []
    for cat in ["primary", "secondary", "domain", "tools"]:
        for s in getattr(incoming.skills, cat):
            if s.lower() not in all_existing_skills:
                new_skills.append(f"[{cat}] {s}")
    if new_skills:
        diff["skills"] = new_skills

    # Certifications
    existing_certs = {(c.name.lower(), c.issuer.lower()) for c in existing.certifications}
    new_certs = [
        f"{c.name} — {c.issuer}"
        for c in incoming.certifications
        if (c.name.lower(), c.issuer.lower()) not in existing_certs
    ]
    if new_certs:
        diff["certifications"] = new_certs

    return diff


# ─── Migration from Legacy Skill Files ────────────────────────

def migrate_from_skill_files() -> CareerProfile:
    """
    Read legacy skill files and extract what we can into a CareerProfile.
    Best-effort extraction from markdown files with [PLACEHOLDER] tokens.
    """
    profile = CareerProfile(meta=ProfileMeta(
        version="1.0.0",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
        sources=["skill_files_migration"],
    ))

    # ── 01-candidate-profile.md ──
    candidate_path = LEGACY_SKILL_FILES["candidate_profile"]
    if candidate_path.exists():
        content = candidate_path.read_text(encoding="utf-8")
        _extract_identity(content, profile)
        _extract_education(content, profile)
        _extract_experience(content, profile)
        _extract_skills(content, profile)
        _extract_certifications(content, profile)
        _extract_publications(content, profile)
        _extract_awards(content, profile)
        _extract_behavioral(content, profile)

    # ── 02-behavioral-profile.md ──
    behavioral_path = LEGACY_SKILL_FILES["behavioral_profile"]
    if behavioral_path.exists():
        content = behavioral_path.read_text(encoding="utf-8")
        _extract_behavioral_detailed(content, profile)

    return profile


def _is_placeholder(value: str) -> bool:
    """Check if a value is still a placeholder token."""
    return "[" in value or value.strip() == ""


def _extract_identity(content: str, profile: CareerProfile) -> None:
    """Extract identity fields from candidate profile markdown."""
    patterns = {
        "name": r"\*\*Name:\*\*\s*(.+)",
        "location": r"\*\*Location:\*\*\s*(.+)",
        "languages": r"\*\*Languages:\*\*\s*(.+)",
        "linkedin": r"\*\*LinkedIn headline:\*\*\s*\"?(.+?)\"?\s*$",
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            value = match.group(1).strip()
            if _is_placeholder(value):
                continue

            if field == "name":
                profile.identity.name = value
            elif field == "location":
                parts = [p.strip() for p in value.split(",")]
                if len(parts) >= 2:
                    profile.identity.location.city = parts[0]
                    # Remove constraint text in parentheses
                    country = re.sub(r"\s*\(.*\)", "", parts[1])
                    profile.identity.location.country = country
                elif len(parts) == 1:
                    profile.identity.location.city = parts[0]
            elif field == "languages":
                for lang in value.split(","):
                    lang = lang.strip()
                    if lang and not _is_placeholder(lang):
                        profile.identity.languages.append(Language(language=lang))
            elif field == "linkedin":
                profile.identity.linkedin_url = value


def _extract_education(content: str, profile: CareerProfile) -> None:
    """Extract education entries from candidate profile markdown."""
    # Pattern: **[DEGREE] in [FIELD]** ([YEAR]-[YEAR]) - [INSTITUTION]
    edu_pattern = r"\*\*(.+?)\s+in\s+(.+?)\*\*\s*\((\d{4})-(\d{4})\)\s*-\s*(.+)"
    for match in re.finditer(edu_pattern, content):
        degree, field, start, end, institution = match.groups()
        degree = degree.strip()
        field = field.strip()
        institution = institution.strip()
        if any(_is_placeholder(v) for v in [degree, field, institution]):
            continue
        profile.education.append(Education(
            degree=degree,
            field=field,
            institution=institution,
            start_year=int(start),
            end_year=int(end),
        ))

    # Extract thesis if present
    thesis_match = re.search(r'Thesis:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
    if thesis_match and not _is_placeholder(thesis_match.group(1)):
        if profile.education:
            profile.education[0].thesis = thesis_match.group(1).strip().strip('"')


def _extract_experience(content: str, profile: CareerProfile) -> None:
    """Extract work experience entries from candidate profile markdown."""
    # Pattern: **[TITLE]** ([DATES]) - **[COMPANY]** ([LOCATION])
    exp_pattern = r"\*\*(.+?)\*\*\s*\((\d{4}(?:-\d{2})?)\s*-\s*(\d{4}(?:-\d{2})?|present)\)\s*-\s*\*\*(.+?)\*\*\s*\((.+?)\)"
    for match in re.finditer(exp_pattern, content):
        title, start, end, company, location = match.groups()
        if any(_is_placeholder(v) for v in [title, company]):
            continue
        profile.experience.append(Experience(
            title=title.strip(),
            company=company.strip(),
            location=location.strip(),
            start_date=start.strip(),
            end_date=end.strip(),
        ))

    # Simpler pattern: **[TITLE]** - **[COMPANY]**
    if not profile.experience:
        simple_pattern = r"\*\*(.+?)\*\*\s*-\s*\*\*(.+?)\*\*"
        for match in re.finditer(simple_pattern, content):
            title, company = match.groups()
            if not any(_is_placeholder(v) for v in [title, company]):
                profile.experience.append(Experience(
                    title=title.strip(),
                    company=company.strip(),
                ))


def _extract_skills(content: str, profile: CareerProfile) -> None:
    """Extract skills from candidate profile markdown."""
    skill_map = {
        "primary": r"\*\*Primary:\*\*\s*(.+)",
        "secondary": r"\*\*Secondary:\*\*\s*(.+)",
        "domain": r"\*\*Domain:\*\*\s*(.+)",
        "software": r"\*\*Software:\*\*\s*(.+)",
    }

    for category, pattern in skill_map.items():
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            value = match.group(1).strip()
            if _is_placeholder(value):
                continue
            skills = [s.strip() for s in value.split(",") if s.strip()]
            target = category if category != "software" else "tools"
            setattr(profile.skills, target, skills)


def _extract_certifications(content: str, profile: CareerProfile) -> None:
    """Extract certifications from candidate profile markdown."""
    cert_pattern = r"\*\*(.+?)\*\*\s*-\s*(\d+)h\s*-\s*completed\s*(.+)"
    for match in re.finditer(cert_pattern, content):
        name, hours, date = match.groups()
        if not _is_placeholder(name):
            profile.certifications.append(Certification(
                name=name.strip(),
                hours=int(hours),
                date=date.strip(),
            ))


def _extract_publications(content: str, profile: CareerProfile) -> None:
    """Extract publications from candidate profile markdown."""
    pub_pattern = r"-\s*(.+?)\s*\((\d{4})\)\.\s*(.+?)\.\s*(.+?)\."
    for match in re.finditer(pub_pattern, content):
        authors_str, year, title, journal = match.groups()
        if any(_is_placeholder(v) for v in [authors_str, title]):
            continue
        authors = [a.strip() for a in authors_str.split(",")]
        profile.publications.append(Publication(
            authors=authors,
            title=title.strip(),
            journal=journal.strip(),
            year=int(year),
        ))


def _extract_awards(content: str, profile: CareerProfile) -> None:
    """Extract awards from candidate profile markdown."""
    award_pattern = r"-\s*(.+?)\s*-\s*(.+?)\s*\((\d{4})\)"
    in_awards_section = False
    for line in content.split("\n"):
        if "### Awards" in line:
            in_awards_section = True
            continue
        if in_awards_section and line.startswith("###"):
            break
        if in_awards_section:
            match = re.match(award_pattern, line.strip())
            if match:
                name, event, year = match.groups()
                if not _is_placeholder(name):
                    profile.awards.append(Award(
                        name=name.strip(),
                        event=event.strip(),
                        year=int(year),
                    ))


def _extract_behavioral(content: str, profile: CareerProfile) -> None:
    """Extract behavioral profile from candidate profile markdown."""
    strengths_match = re.search(r"\*\*Strengths:\*\*\s*(.+)", content, re.MULTILINE)
    if strengths_match and not _is_placeholder(strengths_match.group(1)):
        profile.behavioral.strengths = [
            s.strip() for s in strengths_match.group(1).split(",") if s.strip()
        ]

    growth_match = re.search(r"\*\*Growth areas:\*\*\s*(.+)", content, re.MULTILINE)
    if growth_match and not _is_placeholder(growth_match.group(1)):
        profile.behavioral.growth_areas = [
            s.strip() for s in growth_match.group(1).split(",") if s.strip()
        ]

    thrive_match = re.search(r"\*\*Thrives in:\*\*\s*(.+)", content, re.MULTILINE)
    if thrive_match and not _is_placeholder(thrive_match.group(1)):
        profile.behavioral.ideal_environment = thrive_match.group(1).strip()


def _extract_behavioral_detailed(content: str, profile: CareerProfile) -> None:
    """Extract detailed behavioral profile from 02-behavioral-profile.md."""
    # This is a more detailed file — extract structured sections
    assessment_match = re.search(r"\*\*Assessment Type:\*\*\s*(.+)", content, re.MULTILINE)
    if assessment_match and not _is_placeholder(assessment_match.group(1)):
        profile.behavioral.assessment_type = assessment_match.group(1).strip()

    work_style_match = re.search(r"\*\*Work Style:\*\*\s*(.+)", content, re.MULTILINE)
    if work_style_match and not _is_placeholder(work_style_match.group(1)):
        profile.behavioral.work_style = work_style_match.group(1).strip()

    mgmt_match = re.search(r"\*\*Management Style:\*\*\s*(.+)", content, re.MULTILINE)
    if mgmt_match and not _is_placeholder(mgmt_match.group(1)):
        profile.behavioral.management_style = mgmt_match.group(1).strip()


# ─── Export to Legacy Skill Files ─────────────────────────────

def export_to_skill_files(profile: CareerProfile) -> dict[str, str]:
    """
    Generate markdown content for each legacy skill file from the profile.
    Returns a dict mapping filename -> content.
    This ensures backward compatibility with existing Claude Code commands.
    """
    exports = {}

    # ── 01-candidate-profile.md ──
    lines = ["# Candidate Profile\n"]

    lines.append("### Identity")
    lines.append(f"- **Name:** {profile.identity.name}")
    lines.append(f"- **Location:** {profile.identity.location.city}, {profile.identity.location.country}")
    if profile.identity.languages:
        langs = ", ".join(l.language for l in profile.identity.languages)
        lines.append(f"- **Languages:** {langs}")
    lines.append(f"- **Status:** {'Employed' if profile.experience else 'Seeking opportunities'}")
    lines.append("")

    lines.append("### Education")
    for edu in profile.education:
        lines.append(f"- **{edu.degree} in {edu.field}** ({edu.start_year}-{edu.end_year}) - {edu.institution}")
        if edu.thesis:
            lines.append(f'  - Thesis: "{edu.thesis}"')
        if edu.topics:
            lines.append(f"  - Topics: {', '.join(edu.topics)}")
    lines.append("")

    lines.append("### Professional Experience")
    for exp in profile.experience:
        end = exp.end_date if exp.end_date else "present"
        lines.append(f"- **{exp.title}** ({exp.start_date} - {end}) - **{exp.company}** ({exp.location})")
        for r in exp.responsibilities:
            lines.append(f"  - {r}")
        for a in exp.achievements:
            lines.append(f"  - ✦ {a}")
    lines.append("")

    lines.append("### Technical Skills")
    if profile.skills.primary:
        lines.append(f"- **Primary:** {', '.join(profile.skills.primary)}")
    if profile.skills.secondary:
        lines.append(f"- **Secondary:** {', '.join(profile.skills.secondary)}")
    if profile.skills.domain:
        lines.append(f"- **Domain:** {', '.join(profile.skills.domain)}")
    if profile.skills.tools:
        lines.append(f"- **Software:** {', '.join(profile.skills.tools)}")
    lines.append("")

    if profile.certifications:
        lines.append("### Certifications")
        for cert in profile.certifications:
            h = f" - {cert.hours}h" if cert.hours else ""
            lines.append(f"- **{cert.name}**{h} - completed {cert.date}")
        lines.append("")

    if profile.publications:
        lines.append("### Publications")
        for pub in profile.publications:
            authors = ", ".join(pub.authors)
            lines.append(f"- {authors} ({pub.year}). {pub.title}. {pub.journal}.")
        lines.append("")

    if profile.awards:
        lines.append("### Awards")
        for award in profile.awards:
            lines.append(f"- {award.name} - {award.event} ({award.year})")
        lines.append("")

    if profile.behavioral.strengths or profile.behavioral.growth_areas:
        lines.append("### Behavioral Profile")
        if profile.behavioral.traits:
            for trait in profile.behavioral.traits:
                lines.append(f"- {trait}")
        if profile.behavioral.strengths:
            lines.append(f"- **Strengths:** {', '.join(profile.behavioral.strengths)}")
        if profile.behavioral.growth_areas:
            lines.append(f"- **Growth areas:** {', '.join(profile.behavioral.growth_areas)}")
        if profile.behavioral.ideal_environment:
            lines.append(f"- **Thrives in:** {profile.behavioral.ideal_environment}")
        lines.append("")

    if profile.goals.target_sectors:
        lines.append("### Target Sectors")
        for sector in profile.goals.target_sectors:
            lines.append(f"- {sector}")
        lines.append("")

    if profile.goals.deal_breakers:
        lines.append("### Deal-breakers")
        for db in profile.goals.deal_breakers:
            lines.append(f"- {db}")
        lines.append("")

    exports["01-candidate-profile.md"] = "\n".join(lines)

    # ── 02-behavioral-profile.md ──
    beh_lines = ["# Behavioral Profile\n"]
    if profile.behavioral.assessment_type:
        beh_lines.append(f"**Assessment Type:** {profile.behavioral.assessment_type}\n")
    if profile.behavioral.strengths:
        beh_lines.append("## Strengths")
        for s in profile.behavioral.strengths:
            beh_lines.append(f"- {s}")
        beh_lines.append("")
    if profile.behavioral.growth_areas:
        beh_lines.append("## Growth Areas")
        for g in profile.behavioral.growth_areas:
            beh_lines.append(f"- {g}")
        beh_lines.append("")
    if profile.behavioral.work_style:
        beh_lines.append(f"## Work Style\n{profile.behavioral.work_style}\n")
    if profile.behavioral.ideal_environment:
        beh_lines.append(f"## Ideal Environment\n{profile.behavioral.ideal_environment}\n")
    exports["02-behavioral-profile.md"] = "\n".join(beh_lines)

    # ── 04-job-evaluation.md (skill match areas) ──
    eval_lines = ["# Job Evaluation Framework\n"]
    eval_lines.append("## Skill Match Areas\n")
    if profile.skills.primary:
        eval_lines.append(f"**Strong match:** {', '.join(profile.skills.primary)}")
    if profile.skills.secondary:
        eval_lines.append(f"**Moderate match:** {', '.join(profile.skills.secondary)}")
    eval_lines.append("")
    if profile.goals.career_objectives:
        eval_lines.append("## Career Goals")
        for obj in profile.goals.career_objectives:
            eval_lines.append(f"- {obj}")
        eval_lines.append("")
    if profile.goals.target_roles:
        eval_lines.append("## Target Roles")
        for role in profile.goals.target_roles:
            eval_lines.append(f"- {role}")
        eval_lines.append("")
    exports["04-job-evaluation.md"] = "\n".join(eval_lines)

    # ── 07-interview-prep.md (STAR stubs from experience) ──
    intv_lines = ["# Interview Preparation\n"]
    intv_lines.append("## STAR Candidates (Auto-generated from profile)\n")
    for exp in profile.experience[:5]:  # Top 5 experiences
        intv_lines.append(f"### {exp.title} at {exp.company}")
        intv_lines.append(f"**What happened:** Key responsibilities and achievements in this role")
        intv_lines.append(f"**Why it matters:** Demonstrates relevant experience for target roles")
        intv_lines.append("**S/T/A/R stub:**")
        intv_lines.append(f"- Situation: Working as {exp.title} at {exp.company}")
        intv_lines.append("- Task: [Describe the specific challenge or project]")
        intv_lines.append("- Action: [Describe what you did]")
        intv_lines.append("- Result: [Describe the measurable outcome]")
        intv_lines.append("")
    exports["07-interview-prep.md"] = "\n".join(intv_lines)

    return exports


def sync_to_skill_files(profile: CareerProfile) -> dict[str, Path]:
    """
    Generate backward-compatible skill files from the profile.
    Returns dict mapping filename -> path of written file.
    """
    exports = export_to_skill_files(profile)
    written = {}
    SKILL_FILES_DIR.mkdir(parents=True, exist_ok=True)

    for filename, content in exports.items():
        filepath = SKILL_FILES_DIR / filename
        filepath.write_text(content, encoding="utf-8")
        written[filename] = filepath

    return written
