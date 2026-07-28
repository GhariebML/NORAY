"""
NORAY — Central Configuration

All paths, model settings, and defaults in one place.
Uses pydantic-settings for robust environment variable validation.
"""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Disable symlinks warning on Windows for huggingface_hub to improve compatibility
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ─── Root Paths ───────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
NORAY_DIR = PROJECT_ROOT / "noray"
DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTS_DIR = PROJECT_ROOT / "documents"

class Settings(BaseSettings):
    """
    Centralized configuration management.
    Reads from .env, .env.local, and environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.local'),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Database Settings
    POSTGRES_USER: str = Field(default="noray")
    POSTGRES_PASSWORD: str = Field(default="noray_dev")
    POSTGRES_DB: str = Field(default="noray_db")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: str = Field(default="5432")
    DATABASE_URL: str | None = Field(default=None)

    # Job Search API Credentials
    ADZUNA_APP_ID: str | None = Field(default=None)
    ADZUNA_APP_KEY: str | None = Field(default=None)
    TAVILY_API_KEY: str | None = Field(default=None)
    SERPAPI_API_KEY: str | None = Field(default=None)
    LINKEDIN_API_KEY: str | None = Field(default=None)

    # LLM Provider API Keys & Base URLs
    # MiMo — Xiaomi's official API endpoint: https://platform.xiaomimimo.com
    MIMIO_API_KEY: str | None = Field(default=None)
    MIMIO_BASE_URL: str = Field(default="https://api.xiaomimimo.com/v1")
    MIMIO_MODEL: str = Field(default="mimo-v2.5-pro")
    OPENAI_API_KEY: str | None = Field(default=None)
    ANTHROPIC_API_KEY: str | None = Field(default=None)
    GOOGLE_API_KEY: str | None = Field(default=None)
    GEMINI_API_KEY: str | None = Field(default=None)
    OPENROUTER_API_KEY: str | None = Field(default=None)
    TOGETHER_API_KEY: str | None = Field(default=None)
    MISTRAL_API_KEY: str | None = Field(default=None)
    DEEPSEEK_API_KEY: str | None = Field(default=None)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434/v1")

    # Infrastructure & Servers
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: str = Field(default="6333")
    QDRANT_URL: str | None = Field(default=None)
    QDRANT_API_KEY: str | None = Field(default=None)
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: str = Field(default="6379")
    REDIS_URL: str | None = Field(default=None)
    ALLOWED_ORIGINS: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")

    # AI & Vector Store Config
    AI_PROVIDER: str = Field(default="mimio")
    VECTOR_STORE_PROVIDER: str = Field(default="qdrant")
    EMBEDDINGS_PROVIDER: str = Field(default="local")
    EMBEDDINGS_MODEL: str = Field(default="all-MiniLM-L6-v2")
    EMBEDDING_MODEL_KEY: str = Field(default="bge-m3")
    ALLOW_OFFLINE: bool = Field(default=True)
    ENVIRONMENT: str = Field(default="development")

    # LLM Defaults
    DEFAULT_MODEL: str = Field(default="claude-sonnet-4-20250514")
    REVIEWER_MODEL: str = Field(default="claude-sonnet-4-20250514")
    TEMPERATURE: float = Field(default=0.3)
    MAX_TOKENS: int = Field(default=4096)

settings = Settings()

# Alias for backwards compatibility across the codebase
POSTGRES_USER = settings.POSTGRES_USER
POSTGRES_PASSWORD = settings.POSTGRES_PASSWORD
POSTGRES_DB = settings.POSTGRES_DB
POSTGRES_HOST = settings.POSTGRES_HOST
POSTGRES_PORT = settings.POSTGRES_PORT

QDRANT_HOST = settings.QDRANT_HOST
QDRANT_PORT = settings.QDRANT_PORT

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT

DEFAULT_MODEL = settings.DEFAULT_MODEL
REVIEWER_MODEL = settings.REVIEWER_MODEL
TEMPERATURE = settings.TEMPERATURE
MAX_TOKENS = settings.MAX_TOKENS

# ─── Profile ──────────────────────────────────────────────────
CAREER_PROFILE_PATH = PROJECT_ROOT / "career_profile.json"

# ─── Skill Files ──────────────────────────────────────────────
SKILL_FILES_DIR = PROJECT_ROOT / ".claude" / "skills" / "job-application-assistant"
LEGACY_SKILL_FILES = {
    "candidate_profile": SKILL_FILES_DIR / "01-candidate-profile.md",
    "behavioral_profile": SKILL_FILES_DIR / "02-behavioral-profile.md",
    "writing_style": SKILL_FILES_DIR / "03-writing-style.md",
    "job_evaluation": SKILL_FILES_DIR / "04-job-evaluation.md",
    "cv_templates": SKILL_FILES_DIR / "05-cv-templates.md",
    "cover_letter_templates": SKILL_FILES_DIR / "06-cover-letter-templates.md",
    "interview_prep": SKILL_FILES_DIR / "07-interview-prep.md",
}

# ─── LaTeX ────────────────────────────────────────────────────
CV_DIR = PROJECT_ROOT / "cv"
COVER_LETTERS_DIR = PROJECT_ROOT / "cover_letters"
CV_TEMPLATE = CV_DIR / "main_example.tex"
COVER_LETTER_CLASS = COVER_LETTERS_DIR / "cover.cls"
LATEX_FONTS_DIR = COVER_LETTERS_DIR / "OpenFonts" / "fonts"

# ─── Output ───────────────────────────────────────────────────
UPSILL_REPORTS_DIR = PROJECT_ROOT / "upskill"
SCHOLARSHIP_REPORTS_DIR = PROJECT_ROOT / "scholarships"
JOB_SCRAPER_DIR = PROJECT_ROOT / "job_scraper"

# ─── Dashboard ────────────────────────────────────────────────
JOB_TRACKER_PATH = PROJECT_ROOT / "job_search_tracker.csv"
APPLICATIONS_DIR = DATA_DIR / "applications"

# ─── ATS Scoring ─────────────────────────────────────────────
ATS_SECTION_HEADERS = [
    "education", "experience", "work experience", "professional experience",
    "skills", "technical skills", "publications", "awards", "certifications",
    "projects", "languages", "summary", "profile", "objective",
]

# ─── Job Search ───────────────────────────────────────────────
SEARCH_LOOKBACK_DAYS = 14
MAX_SEARCH_RESULTS = 50
DEDUP_FIELDS = ["company", "title", "url"]

# ─── Ensure directories exist ─────────────────────────────────
for d in [DATA_DIR, APPLICATIONS_DIR, UPSILL_REPORTS_DIR, SCHOLARSHIP_REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
