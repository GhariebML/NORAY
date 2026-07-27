"""
NORAY — Pydantic Data Models for career_profile.json

These schemas define the canonical structure of the user's career profile.
All agents read from and write to this structure.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

# ─── Identity ─────────────────────────────────────────────────

class Location(BaseModel):
    city: str = ""
    country: str = ""


class Language(BaseModel):
    language: str = ""
    proficiency: str = ""  # native, fluent, intermediate, beginner


class Identity(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: Location = Field(default_factory=Location)
    linkedin_url: str = ""
    github_url: str = ""
    website_url: str = ""
    languages: list[Language] = Field(default_factory=list)


# ─── Education ────────────────────────────────────────────────

class Education(BaseModel):
    degree: str = ""  # PhD, MSc, BSc, etc.
    field: str = ""
    institution: str = ""
    start_year: int = 0
    end_year: int = 0
    thesis: str = ""
    gpa: str = ""
    topics: list[str] = Field(default_factory=list)
    honors: str = ""


# ─── Experience ───────────────────────────────────────────────

class Experience(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""  # YYYY-MM or YYYY
    end_date: str = ""    # YYYY-MM or "present"
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


# ─── Projects ─────────────────────────────────────────────────

class Project(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    url: str = ""
    highlights: list[str] = Field(default_factory=list)


# ─── Skills ───────────────────────────────────────────────────

class Skills(BaseModel):
    primary: list[str] = Field(default_factory=list)
    secondary: list[str] = Field(default_factory=list)
    domain: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


# ─── Certifications ───────────────────────────────────────────

class Certification(BaseModel):
    name: str = ""
    issuer: str = ""
    date: str = ""
    hours: int = 0
    credential_url: str = ""


# ─── Awards ───────────────────────────────────────────────────

class Award(BaseModel):
    name: str = ""
    event: str = ""
    year: int = 0
    description: str = ""


# ─── Publications ─────────────────────────────────────────────

class Publication(BaseModel):
    authors: list[str] = Field(default_factory=list)
    title: str = ""
    journal: str = ""
    year: int = 0
    doi: str = ""
    url: str = ""


# ─── Behavioral ───────────────────────────────────────────────

class Behavioral(BaseModel):
    assessment_type: str = ""  # PI, DISC, MBTI, self-assessment
    traits: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    growth_areas: list[str] = Field(default_factory=list)
    work_style: str = ""
    management_style: str = ""
    ideal_environment: str = ""


# ─── Goals ────────────────────────────────────────────────────

class CareerGoals(BaseModel):
    career_objectives: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    target_sectors: list[str] = Field(default_factory=list)
    deal_breakers: list[str] = Field(default_factory=list)
    salary_expectations: str = ""
    location_preferences: str = ""


class ScholarshipGoals(BaseModel):
    target_degrees: list[str] = Field(default_factory=list)
    target_countries: list[str] = Field(default_factory=list)
    research_interests: list[str] = Field(default_factory=list)
    funding_needed: str = ""
    deadlines: list[str] = Field(default_factory=list)


# ─── GitHub ───────────────────────────────────────────────────

class GitHubProfile(BaseModel):
    username: str = ""
    repos: list[dict] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    contributions: int = 0
    highlights: list[str] = Field(default_factory=list)


# ─── Profile Metadata ────────────────────────────────────────

class ProfileMeta(BaseModel):
    version: str = "1.0.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sources: list[str] = Field(default_factory=list)


# ─── Root Profile ─────────────────────────────────────────────

class CareerProfile(BaseModel):
    """The canonical career profile. All agents read from this."""
    meta: ProfileMeta = Field(default_factory=ProfileMeta)
    identity: Identity = Field(default_factory=Identity)
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    certifications: list[Certification] = Field(default_factory=list)
    awards: list[Award] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    behavioral: Behavioral = Field(default_factory=Behavioral)
    goals: CareerGoals = Field(default_factory=CareerGoals)
    scholarship_goals: ScholarshipGoals = Field(default_factory=ScholarshipGoals)
    github: GitHubProfile = Field(default_factory=GitHubProfile)
