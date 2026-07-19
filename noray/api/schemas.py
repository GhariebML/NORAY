"""
NORAY — API Request/Response Schemas

Pydantic models for API endpoints.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ─── Profile ──────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    profile: dict
    meta: dict = Field(default_factory=dict)


class ProfileUpdateRequest(BaseModel):
    updates: dict
    source: str = "api"


class ImportCVRequest(BaseModel):
    file_path: str


class ImportGithubRequest(BaseModel):
    username: str


# ─── Jobs ─────────────────────────────────────────────────────

class JobSearchRequest(BaseModel):
    focus_area: str = ""
    broad: bool = False


class JobSearchResponse(BaseModel):
    jobs: list[dict]
    total_found: int
    new_count: int


class JobEvaluateRequest(BaseModel):
    job_url: str = ""
    job_text: str = ""


class JobApplyRequest(BaseModel):
    job_url: str = ""
    job_text: str = ""
    company: str
    role: str
    generate_cv: bool = True
    generate_cover_letter: bool = True


# ─── Scholarships ─────────────────────────────────────────────

class ScholarshipSearchRequest(BaseModel):
    target_degree: str = ""
    target_country: str = ""
    research_area: str = ""


class ScholarshipSearchResponse(BaseModel):
    scholarships: list[dict]
    total_found: int


class ScholarshipApplyRequest(BaseModel):
    scholarship_info: str
    scholarship_name: str
    generate_sop: bool = True
    generate_motivation: bool = False
    generate_research_proposal: bool = False


# ─── CV & Documents ───────────────────────────────────────────

class CVGenerateRequest(BaseModel):
    job_url: str = ""
    job_text: str = ""
    company: str
    role: str = ""


class CVOptimizeRequest(BaseModel):
    cv_text: str
    job_keywords: list[str] = Field(default_factory=list)


class SOPGenerateRequest(BaseModel):
    scholarship_info: str
    research_interests: list[str] = Field(default_factory=list)
    word_limit: int = 1000


class MotivationGenerateRequest(BaseModel):
    scholarship_info: str
    word_limit: int = 500


class ResearchProposalRequest(BaseModel):
    scholarship_info: str
    research_interests: list[str] = Field(default_factory=list)
    word_limit: int = 2000


# ─── Applications ─────────────────────────────────────────────

class ApplicationResponse(BaseModel):
    applications: list[dict]
    stats: dict


# ─── Upskill ──────────────────────────────────────────────────

class UpskillRequest(BaseModel):
    job_url: str = ""
    job_text: str = ""
    mode: str = "aggregate"  # aggregate or targeted


class RoadmapRequest(BaseModel):
    timeline_months: int = 12
    target_roles: list[str] = Field(default_factory=list)


class UpskillResponse(BaseModel):
    gaps: list[dict]
    learning_plan: list[dict]
    roadmap: dict
