"""
NORAY — Interview Coach

Generate STAR-format interview preparation, talking points,
questions for the candidate to ask, and gap-aware coaching.
Reads from the career profile for personalized preparation.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any

from noray.shared.models import CareerProfile
from noray.career_agent.ats_analyzer import extract_keywords_from_posting


# ─── Data Models ──────────────────────────────────────────────

@dataclass
class STARExample:
    """A STAR-format interview answer."""
    question: str = ""
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""
    category: str = ""  # behavioral, technical, situational
    skill_demonstrated: str = ""
    use_for: list[str] = field(default_factory=list)


@dataclass
class TalkingPoint:
    """A key talking point for the interview."""
    topic: str = ""
    content: str = ""
    priority: str = ""  # high, medium


@dataclass
class GapPreparation:
    """Preparation for a potential gap question."""
    gap: str = ""
    response_strategy: str = ""
    framing: str = ""


@dataclass
class InterviewPrep:
    """Complete interview preparation package."""
    company: str = ""
    role: str = ""
    star_examples: list[STARExample] = field(default_factory=list)
    talking_points: list[TalkingPoint] = field(default_factory=list)
    questions_to_ask: list[str] = field(default_factory=list)
    gap_preparations: list[GapPreparation] = field(default_factory=list)
    elevator_pitch: str = ""
    red_flags_to_address: list[str] = field(default_factory=list)
    role_specific_tips: list[str] = field(default_factory=list)


# ─── Public API ───────────────────────────────────────────────

def prepare_interview(
    profile: CareerProfile,
    job_posting: str,
    company: str,
    role: str,
) -> InterviewPrep:
    """
    Generate comprehensive interview preparation.
    
    Args:
        profile: The candidate's career profile
        job_posting: Full text of the job posting
        company: Company name
        role: Role title
    
    Returns:
        InterviewPrep with STAR examples, talking points, and questions
    """
    prep = InterviewPrep(company=company, role=role)

    # Extract what the job cares about
    keywords = extract_keywords_from_posting(job_posting)
    required_skills = _extract_required_skills(job_posting)

    # Generate STAR examples from profile experience
    prep.star_examples = _generate_star_examples(profile, job_posting, keywords)

    # Generate talking points
    prep.talking_points = _generate_talking_points(profile, job_posting, keywords)

    # Generate questions to ask
    prep.questions_to_ask = _generate_questions_to_ask(company, role, job_posting)

    # Identify gaps and prepare responses
    prep.gap_preparations = _prepare_for_gaps(profile, required_skills)

    # Generate elevator pitch
    prep.elevator_pitch = _generate_elevator_pitch(profile, role, company)

    # Identify red flags to address
    prep.red_flags_to_address = _identify_red_flags(profile, job_posting)

    # Role-specific tips
    prep.role_specific_tips = _generate_role_tips(role, job_posting)

    return prep


def format_prep_as_markdown(prep: InterviewPrep) -> str:
    """Format the interview prep as a readable markdown document."""
    lines = [f"# Interview Preparation: {prep.role} at {prep.company}\n"]

    # Elevator Pitch
    if prep.elevator_pitch:
        lines.append("## 🎤 Elevator Pitch (60 seconds)\n")
        lines.append(prep.elevator_pitch)
        lines.append("")

    # STAR Examples
    if prep.star_examples:
        lines.append("## ⭐ STAR Examples\n")
        for i, star in enumerate(prep.star_examples, 1):
            lines.append(f"### {i}. {star.question}")
            lines.append(f"**Skill demonstrated:** {star.skill_demonstrated}\n")
            lines.append(f"**S:** {star.situation}")
            lines.append(f"**T:** {star.task}")
            lines.append(f"**A:** {star.action}")
            lines.append(f"**R:** {star.result}")
            if star.use_for:
                lines.append(f"**Use for:** {', '.join(star.use_for)}")
            lines.append("")

    # Talking Points
    if prep.talking_points:
        lines.append("## 💬 Key Talking Points\n")
        for tp in prep.talking_points:
            emoji = "🔴" if tp.priority == "high" else "🟡"
            lines.append(f"- {emoji} **{tp.topic}:** {tp.content}")
        lines.append("")

    # Questions to Ask
    if prep.questions_to_ask:
        lines.append("## ❓ Questions to Ask the Interviewer\n")
        for i, q in enumerate(prep.questions_to_ask, 1):
            lines.append(f"{i}. {q}")
        lines.append("")

    # Gap Preparations
    if prep.gap_preparations:
        lines.append("## 🛡️ Gap Preparation\n")
        lines.append("Anticipated questions about gaps in your profile:\n")
        for gap in prep.gap_preparations:
            lines.append(f"### Gap: {gap.gap}")
            lines.append(f"**Strategy:** {gap.response_strategy}")
            lines.append(f"**Framing:** {gap.framing}")
            lines.append("")

    # Red Flags
    if prep.red_flags_to_address:
        lines.append("## 🚩 Red Flags to Prepare For\n")
        for flag in prep.red_flags_to_address:
            lines.append(f"- {flag}")
        lines.append("")

    # Role-Specific Tips
    if prep.role_specific_tips:
        lines.append("## 💡 Role-Specific Tips\n")
        for tip in prep.role_specific_tips:
            lines.append(f"- {tip}")
        lines.append("")

    return "\n".join(lines)


# ─── STAR Generation ──────────────────────────────────────────

def _generate_star_examples(
    profile: CareerProfile,
    job_posting: str,
    keywords: list[str],
) -> list[STARExample]:
    """
    Generate STAR examples from the candidate's experience.
    Maps experience entries to likely interview questions.
    """
    examples = []
    job_lower = job_posting.lower()

    for exp in profile.experience:
        # For each achievement, build a STAR example
        for achievement in exp.achievements[:2]:
            # Determine what skill this demonstrates
            skill = _infer_skill(achievement, keywords)
            question = _infer_question(skill, job_lower)

            star = STARExample(
                question=question,
                situation=f"While working as {exp.title} at {exp.company}.",
                task=f"Responsible for {exp.responsibilities[0] if exp.responsibilities else 'delivering key results'}.",
                action=achievement,
                result=_infer_result(achievement),
                category="behavioral" if skill in {"leadership", "teamwork", "communication"} else "technical",
                skill_demonstrated=skill,
                use_for=[question],
            )
            examples.append(star)

        # Also use key responsibilities if few achievements
        if len(exp.achievements) < 2 and exp.responsibilities:
            for resp in exp.responsibilities[:1]:
                skill = _infer_skill(resp, keywords)
                star = STARExample(
                    question=f"Tell me about your experience with {skill}.",
                    situation=f"At {exp.company} as {exp.title}.",
                    task=f"Tasked with {resp.lower()}.",
                    action=f"Successfully {resp.lower()}.",
                    result="Delivered expected outcomes and contributed to team success.",
                    category="technical",
                    skill_demonstrated=skill,
                )
                examples.append(star)

    # Add behavioral STAR from behavioral profile
    if profile.behavioral.strengths:
        for strength in profile.behavioral.strengths[:2]:
            star = STARExample(
                question=f"Tell me about a time you demonstrated {strength.lower()}.",
                situation="Throughout my career, I have consistently demonstrated this quality.",
                task="Applied this strength to overcome challenges and deliver results.",
                action=f"Leveraged {strength.lower()} to drive positive outcomes.",
                result="Received positive feedback and achieved measurable improvements.",
                category="behavioral",
                skill_demonstrated=strength,
                use_for=[f"Behavioral questions about {strength.lower()}"],
            )
            examples.append(star)

    return examples[:7]  # Limit to 7 examples


def _generate_talking_points(
    profile: CareerProfile,
    job_posting: str,
    keywords: list[str],
) -> list[TalkingPoint]:
    """Generate key talking points for the interview."""
    points = []
    job_lower = job_posting.lower()

    # Skills match points
    matching_skills = []
    for skill in profile.skills.primary + profile.skills.secondary:
        if skill.lower() in job_lower:
            matching_skills.append(skill)
    if matching_skills:
        points.append(TalkingPoint(
            topic="Skills Alignment",
            content=f"Your skills in {', '.join(matching_skills[:5])} directly match the job requirements.",
            priority="high",
        ))

    # Experience relevance
    for exp in profile.experience[:2]:
        for keyword in keywords[:5]:
            if keyword.lower() in f"{exp.title} {' '.join(exp.responsibilities)}".lower():
                points.append(TalkingPoint(
                    topic=f"Relevant Experience at {exp.company}",
                    content=f"Your work as {exp.title} at {exp.company} directly relates to this role.",
                    priority="high",
                ))
                break

    # Domain expertise
    for domain in profile.skills.domain:
        if domain.lower() in job_lower:
            points.append(TalkingPoint(
                topic="Domain Expertise",
                content=f"Your domain expertise in {domain} is a strong differentiator.",
                priority="medium",
            ))

    # Education alignment
    if profile.education:
        edu = profile.education[0]
        if edu.field.lower() in job_lower or any(kw in edu.field.lower() for kw in keywords):
            points.append(TalkingPoint(
                topic="Academic Background",
                content=f"Your {edu.degree} in {edu.field} from {edu.institution} provides strong foundations.",
                priority="medium",
            ))

    # Projects
    for proj in profile.projects[:2]:
        proj_text = f"{proj.name} {proj.description}".lower()
        if any(kw.lower() in proj_text for kw in keywords):
            points.append(TalkingPoint(
                topic=f"Project: {proj.name}",
                content=f"Your {proj.name} project demonstrates relevant skills and initiative.",
                priority="medium",
            ))

    return points


def _generate_questions_to_ask(
    company: str,
    role: str,
    job_posting: str,
) -> list[str]:
    """Generate thoughtful questions for the candidate to ask."""
    questions = [
        f"What does success look like in this {role} role in the first 6 months?",
        "What are the biggest challenges the team is currently facing?",
        "How does this role contribute to the company's strategic goals?",
        "What's the team structure and how would I collaborate with other departments?",
        "What opportunities are there for professional development and growth?",
    ]

    # Add role-specific questions
    job_lower = job_posting.lower()
    if "team" in job_lower or "lead" in job_lower:
        questions.append("How large is the team, and what's the current team composition?")
    if "remote" in job_lower or "hybrid" in job_lower:
        questions.append("How does the team handle remote collaboration?")
    if "data" in job_lower or "ml" in job_lower:
        questions.append("What does the current data infrastructure look like?")
    if "startup" in job_lower or "scale" in job_lower:
        questions.append("What stage is the company at, and what are the growth plans?")

    return questions[:8]


def _prepare_for_gaps(
    profile: CareerProfile,
    required_skills: list[str],
) -> list[GapPreparation]:
    """Identify skill gaps and prepare response strategies."""
    preparations = []

    profile_skills = set()
    for cat in ["primary", "secondary", "domain", "tools"]:
        profile_skills.update(s.lower() for s in getattr(profile.skills, cat))

    for skill in required_skills:
        if skill.lower() not in profile_skills:
            preparations.append(GapPreparation(
                gap=f"Missing: {skill}",
                response_strategy=(
                    f"Acknowledge the gap honestly, then pivot to related experience. "
                    f"Example: 'I haven't worked with {skill} directly, but I have extensive "
                    f"experience with [related skill], and I'm a fast learner who picks up "
                    f"new technologies quickly.'"
                ),
                framing="Honest + pivoting to related experience + eagerness to learn",
            ))

    return preparations[:5]


def _generate_elevator_pitch(
    profile: CareerProfile,
    role: str,
    company: str,
) -> str:
    """Generate a 60-second elevator pitch."""
    parts = []

    # Current/most recent role
    if profile.experience:
        exp = profile.experience[0]
        parts.append(f"I'm a {exp.title} at {exp.company}.")

    # Key skills
    if profile.skills.primary:
        parts.append(f"My core expertise is in {', '.join(profile.skills.primary[:3])}.")

    # Top achievement
    for exp in profile.experience:
        if exp.achievements:
            parts.append(exp.achievements[0])
            break

    # Why this role
    parts.append(f"I'm excited about the {role} role at {company} because it aligns with my career direction.")

    return " ".join(parts)


def _identify_red_flags(profile: CareerProfile, job_posting: str) -> list[str]:
    """Identify potential red flags and prepare responses."""
    flags = []

    # Short tenure
    for exp in profile.experience:
        if exp.end_date and exp.start_date:
            try:
                # Simple check for short tenure
                start = int(exp.start_date[:4]) if exp.start_date[:4].isdigit() else 0
                end = int(exp.end_date[:4]) if exp.end_date[:4].isdigit() else 2026
                if 0 < end - start < 1:
                    flags.append(f"Short tenure at {exp.company} — prepare to explain what you learned")
            except (ValueError, IndexError):
                pass

    # Employment gaps
    if len(profile.experience) >= 2:
        for i in range(len(profile.experience) - 1):
            current = profile.experience[i]
            previous = profile.experience[i + 1]
            if current.end_date and previous.start_date:
                try:
                    end_year = int(current.end_date[:4]) if current.end_date[:4].isdigit() else 0
                    start_year = int(previous.start_date[:4]) if previous.start_date[:4].isdigit() else 0
                    if 0 < start_year - end_year > 1:
                        flags.append(f"Gap between {current.company} and {previous.company} — prepare a positive framing")
                except (ValueError, IndexError):
                    pass

    # Missing required skills
    profile_skills = set()
    for cat in ["primary", "secondary", "domain", "tools"]:
        profile_skills.update(s.lower() for s in getattr(profile.skills, cat))

    job_lower = job_posting.lower()
    for skill in ["python", "machine learning", "docker", "aws", "sql"]:
        if skill in job_lower and skill not in profile_skills:
            flags.append(f"Job requires {skill} but it's not in your profile — prepare to address")

    return flags[:5]


def _generate_role_tips(role: str, job_posting: str) -> list[str]:
    """Generate role-specific interview tips."""
    tips = []
    role_lower = role.lower()
    job_lower = job_posting.lower()

    if "data scientist" in role_lower or "ml" in role_lower or "machine learning" in role_lower:
        tips.extend([
            "Be prepared to discuss a specific ML project end-to-end: data, model, deployment, impact.",
            "Know the difference between precision/recall and when to optimize for each.",
            "Have an opinion on the latest ML trends (LLMs, transformers, etc.).",
        ])

    if "engineer" in role_lower or "developer" in role_lower:
        tips.extend([
            "Be ready for system design questions — practice drawing architecture diagrams.",
            "Prepare to discuss code quality, testing, and CI/CD practices.",
        ])

    if "lead" in role_lower or "manager" in role_lower or "senior" in role_lower:
        tips.extend([
            "Prepare examples of mentoring junior team members.",
            "Have stories about resolving technical disagreements in a team.",
            "Be ready to discuss how you've driven technical decisions.",
        ])

    if "remote" in job_lower or "hybrid" in job_lower:
        tips.append("Discuss your remote work setup and how you maintain productivity and communication.")

    return tips


# ─── Helpers ──────────────────────────────────────────────────

def _extract_required_skills(job_text: str) -> list[str]:
    """Extract required skills from a job posting text."""
    skills = []
    tech_skills = [
        "python", "java", "javascript", "typescript", "c++", "go", "rust", "r", "sql",
        "machine learning", "deep learning", "nlp", "computer vision", "data science",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "docker", "kubernetes", "aws", "azure", "gcp",
        "git", "ci/cd", "fastapi", "flask", "django", "react",
        "postgresql", "mysql", "mongodb", "redis",
        "spark", "hadoop", "airflow", "kafka",
    ]
    job_lower = job_text.lower()
    for skill in tech_skills:
        if skill in job_lower:
            skills.append(skill)
    return skills


def _infer_skill(text: str, keywords: list[str]) -> str:
    """Infer what skill a text demonstrates."""
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return kw
    # Fallback to common categories
    for skill, triggers in {
        "leadership": ["led", "managed", "directed", "coordinated", "mentored"],
        "teamwork": ["collaborated", "team", "cross-functional", "partnered"],
        "problem-solving": ["solved", "optimized", "improved", "reduced", "resolved"],
        "communication": ["presented", "reported", "communicated", "stakeholder"],
        "technical": ["built", "developed", "implemented", "designed", "architected"],
    }.items():
        if any(t in text_lower for t in triggers):
            return skill
    return "technical competency"


def _infer_question(skill: str, job_lower: str) -> str:
    """Infer a likely interview question based on the skill."""
    question_map = {
        "leadership": "Tell me about a time you led a team or project.",
        "teamwork": "Describe a situation where you had to collaborate across teams.",
        "problem-solving": "Walk me through how you solved a complex technical problem.",
        "communication": "Tell me about a time you had to explain a complex concept to a non-technical audience.",
    }
    return question_map.get(skill, f"Tell me about your experience with {skill}.")


def _infer_result(achievement: str) -> str:
    """Try to extract a result from an achievement text."""
    # Look for numbers
    numbers = re.findall(r"\d+[%k$€£]?", achievement)
    if numbers:
        return f"Achieved measurable improvement: {achievement}"
    return f"Successfully delivered the expected outcomes."
