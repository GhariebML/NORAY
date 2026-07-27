"""
NORAY — ATS Analyzer

Score CVs against ATS (Applicant Tracking System) parsing rules.
Identifies formatting issues, missing keywords, and optimization opportunities.
Integrates with the career profile for personalized recommendations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from noray.config import ATS_SECTION_HEADERS


@dataclass
class ATSScore:
    """ATS compatibility score for a CV."""
    overall_score: int = 0  # 0-100
    formatting_score: int = 0
    keyword_score: int = 0
    structure_score: int = 0
    content_score: int = 0
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    keywords_found: list[str] = field(default_factory=list)
    keywords_missing: list[str] = field(default_factory=list)
    sections_found: list[str] = field(default_factory=list)
    sections_missing: list[str] = field(default_factory=list)


def analyze_cv_ats(
    cv_text: str,
    job_keywords: list[str] | None = None,
    profile_skills: list[str] | None = None,
) -> ATSScore:
    """
    Analyze a CV for ATS compatibility.
    
    Args:
        cv_text: Full text content of the CV
        job_keywords: Optional list of keywords from the target job posting
        profile_skills: Optional list of skills from the candidate profile
    
    Returns:
        ATSScore with detailed analysis
    """
    score = ATSScore()

    # Check formatting
    score.formatting_score = _check_formatting(cv_text, score)

    # Check structure (section headers)
    score.structure_score = _check_structure(cv_text, score)

    # Check content quality
    score.content_score = _check_content(cv_text, score)

    # Check keywords if job provided
    if job_keywords:
        score.keyword_score = _check_keywords(cv_text, job_keywords, score)
    elif profile_skills:
        score.keyword_score = _check_keywords(cv_text, profile_skills, score)
    else:
        score.keyword_score = 70

    # Calculate overall (weighted)
    score.overall_score = int(
        (score.formatting_score * 0.2) +
        (score.structure_score * 0.25) +
        (score.keyword_score * 0.35) +
        (score.content_score * 0.2)
    )

    return score


def extract_keywords_from_posting(job_text: str) -> list[str]:
    """
    Extract key requirements/keywords from a job posting.
    
    Returns a list of skill/keyword strings found in the posting.
    """
    keywords = set()
    text_lower = job_text.lower()

    # Technical skills dictionary
    tech_skills = [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "r", "matlab", "scala", "sql", "nosql", "html", "css", "react", "vue",
        "angular", "node.js", "next.js", "fastapi", "flask", "django", "spring",
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "data science", "data engineering", "data analysis",
        "tensorflow", "pytorch", "scikit-learn", "keras", "pandas", "numpy",
        "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "linux",
        "git", "ci/cd", "jenkins", "github actions", "gitlab ci",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "neo4j",
        "spark", "hadoop", "kafka", "airflow", "dbt", "snowflake",
        "agile", "scrum", "jira", "confluence",
        "api", "rest", "graphql", "microservices",
        "etl", "data pipeline", "mlops", "devops",
        "tableau", "power bi", "looker",
        "excel", "powerpoint", "word",
    ]

    for skill in tech_skills:
        if skill in text_lower:
            keywords.add(skill)

    # Extract capitalized terms (likely proper nouns / technologies)
    caps_pattern = r"\b[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*\b"
    for match in re.finditer(caps_pattern, job_text):
        term = match.group(0)
        if len(term) > 2 and term not in {"The", "This", "With", "About", "What", "Your", "Our", "You", "We", "Are", "For", "And", "Not", "All"}:
            keywords.add(term)

    return sorted(keywords)


def generate_optimization_report(score: ATSScore) -> str:
    """Generate a human-readable ATS optimization report."""
    lines = ["# ATS Optimization Report\n"]

    lines.append(f"**Overall Score: {score.overall_score}/100**\n")

    # Score breakdown
    lines.append("## Score Breakdown")
    lines.append("| Category | Score |")
    lines.append("|----------|-------|")
    lines.append(f"| Formatting | {score.formatting_score}/100 |")
    lines.append(f"| Structure | {score.structure_score}/100 |")
    lines.append(f"| Keywords | {score.keyword_score}/100 |")
    lines.append(f"| Content | {score.content_score}/100 |")
    lines.append("")

    # Issues
    if score.issues:
        lines.append("## ❌ Issues (Must Fix)")
        for issue in score.issues:
            lines.append(f"- {issue}")
        lines.append("")

    # Recommendations
    if score.recommendations:
        lines.append("## 💡 Recommendations")
        for rec in score.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    # Keywords
    if score.keywords_found:
        lines.append(f"## ✅ Keywords Found ({len(score.keywords_found)})")
        lines.append(f"- {', '.join(score.keywords_found)}")
        lines.append("")

    if score.keywords_missing:
        lines.append(f"## ❌ Keywords Missing ({len(score.keywords_missing)})")
        lines.append(f"- {', '.join(score.keywords_missing)}")
        lines.append("")

    # Rating
    if score.overall_score >= 85:
        lines.append("**Rating:** 🟢 Excellent — your CV is well-optimized for ATS.")
    elif score.overall_score >= 70:
        lines.append("**Rating:** 🟡 Good — some improvements would help.")
    elif score.overall_score >= 50:
        lines.append("**Rating:** 🟠 Needs work — address the issues above.")
    else:
        lines.append("**Rating:** 🔴 Poor — significant restructuring needed.")

    return "\n".join(lines)


# ─── Internal Checks ──────────────────────────────────────────

def _check_formatting(text: str, score: ATSScore) -> int:
    """Check CV formatting for ATS compatibility."""
    points = 100

    # Check for tables (bad for ATS)
    if "|" in text and "---" in text:
        score.issues.append("Contains table formatting — ATS may not parse correctly")
        points -= 20

    # Check for special characters
    special_chars = {"•": "bullet", "★": "star", "→": "arrow", "▸": "arrow", "■": "square"}
    for char, name in special_chars.items():
        if char in text:
            score.recommendations.append(f"Replace '{char}' with standard bullet (- or *) — some ATS can't parse {name} characters")
            points -= 3
            break  # Only penalize once

    # Check for headers in ALL CAPS (good for ATS)
    lines = text.split("\n")
    caps_headers = sum(1 for line in lines if line.strip().isupper() and len(line.strip()) > 3)
    if caps_headers < 2:
        score.recommendations.append("Use ALL CAPS for section headers (EDUCATION, EXPERIENCE, SKILLS) — helps ATS parsing")
        points -= 10

    # Check for contact info at top
    first_500 = text[:500].lower()
    has_email = bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", first_500))
    has_phone = bool(re.search(r"\+?\d[\d\s\-]{8,}", first_500))

    if not has_email:
        score.issues.append("Email not found in the first 500 characters — ATS may miss it")
        points -= 15
    if not has_phone:
        score.recommendations.append("Consider adding phone number near the top of the CV")
        points -= 5

    # Check for unusual fonts or encoding issues
    if "□" in text or "�" in text:
        score.issues.append("Encoding issues detected — characters may not render in ATS")
        points -= 10

    # Check document length (too short or too long)
    word_count = len(text.split())
    if word_count < 200:
        score.issues.append(f"CV is very short ({word_count} words) — may not have enough content")
        points -= 15
    elif word_count > 1500:
        score.recommendations.append(f"CV is long ({word_count} words) — consider trimming to 2 pages")

    return max(0, points)


def _check_structure(text: str, score: ATSScore) -> int:
    """Check CV structure (section headers, order)."""
    points = 100
    text_lower = text.lower()
    found_sections = []
    missing_sections = []

    for header in ATS_SECTION_HEADERS:
        if header in text_lower:
            found_sections.append(header)
        else:
            # Check for common variants
            variants = {
                "experience": ["work experience", "professional experience", "employment", "work history"],
                "education": ["academic background", "qualifications", "academic"],
                "skills": ["technical skills", "competencies", "expertise", "technologies"],
            }
            found_variant = False
            if header in variants:
                for variant in variants[header]:
                    if variant in text_lower:
                        found_sections.append(f"{header} ({variant})")
                        found_variant = True
                        break
            if not found_variant:
                missing_sections.append(header)

    score.sections_found = found_sections
    score.sections_missing = missing_sections

    # Must have experience and education
    has_experience = any("experience" in s.lower() for s in found_sections)
    has_education = any("education" in s.lower() for s in found_sections)
    has_skills = any("skill" in s.lower() for s in found_sections)

    if not has_experience:
        score.issues.append("No 'Experience' section found — critical for ATS")
        points -= 25
    if not has_education:
        score.issues.append("No 'Education' section found — critical for ATS")
        points -= 20
    if not has_skills:
        score.recommendations.append("Add a dedicated 'Skills' section for better ATS keyword matching")
        points -= 10

    if len(found_sections) < 3:
        score.issues.append(f"Only {len(found_sections)} standard sections found — ATS may miss content")
        points -= 15

    # Check for profile/summary section (good for ATS)
    if not any(s in text_lower for s in ["profile", "summary", "objective"]):
        score.recommendations.append("Add a Profile/Summary section at the top for better ATS keyword density")
        points -= 5

    return max(0, points)


def _check_content(text: str, score: ATSScore) -> int:
    """Check content quality for ATS readability."""
    points = 100

    # Check for bullet points (good for ATS)
    bullet_count = text.count("\n-") + text.count("\n•") + text.count("\n*")
    if bullet_count < 5:
        score.recommendations.append("Use more bullet points — ATS and recruiters prefer structured content")
        points -= 10

    # Check for quantified achievements
    number_pattern = r"\b\d+[%k$€£]?\b"
    numbers = re.findall(number_pattern, text)
    if len(numbers) < 3:
        score.recommendations.append("Add more quantified achievements (numbers, percentages, metrics)")
        points -= 10

    # Check for action verbs at the start of bullets
    action_verbs = [
        "built", "developed", "created", "designed", "implemented", "managed",
        "led", "improved", "reduced", "increased", "achieved", "delivered",
        "analyzed", "automated", "optimized", "established", "launched",
        "coordinated", "mentored", "trained", "researched", "published",
    ]
    lines = text.split("\n")
    bullet_lines = [l.strip() for l in lines if l.strip().startswith(("-", "•", "*"))]
    if bullet_lines:
        action_verb_count = sum(
            1 for l in bullet_lines
            if any(l.lstrip("-•* ").lower().startswith(v) for v in action_verbs)
        )
        action_ratio = action_verb_count / len(bullet_lines) if bullet_lines else 0
        if action_ratio < 0.3:
            score.recommendations.append("Start more bullet points with action verbs (built, developed, led, improved...)")
            points -= 10

    # Check for dates (chronological structure)
    date_pattern = r"\b(20\d{2}|19\d{2})\b"
    dates = re.findall(date_pattern, text)
    if len(dates) < 2:
        score.recommendations.append("Add clear dates to experience and education entries")
        points -= 5

    return max(0, points)


def _check_keywords(text: str, keywords: list[str], score: ATSScore) -> int:
    """Check how many job keywords appear in the CV."""
    if not keywords:
        return 70

    text_lower = text.lower()
    found = []
    missing = []

    for keyword in keywords:
        keyword_lower = keyword.lower().strip()
        if not keyword_lower:
            continue
        # Fuzzy match: check if keyword appears as substring
        if keyword_lower in text_lower:
            found.append(keyword)
        else:
            # Check for common variations
            variations = [
                keyword_lower.replace(".", ""),
                keyword_lower.replace(" ", ""),
                keyword_lower.replace("-", " "),
            ]
            if any(v in text_lower for v in variations):
                found.append(keyword)
            else:
                missing.append(keyword)

    score.keywords_found = found
    score.keywords_missing = missing

    total = len(found) + len(missing)
    if total == 0:
        return 70

    match_rate = len(found) / total

    if match_rate >= 0.8:
        return 95
    elif match_rate >= 0.6:
        return 80
    elif match_rate >= 0.4:
        if missing:
            score.recommendations.append(f"Add missing keywords: {', '.join(missing[:5])}")
        return 60
    else:
        if missing:
            score.issues.append(f"Low keyword match ({len(found)}/{total}). Missing: {', '.join(missing[:7])}")
        return 40
