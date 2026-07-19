"""
NORAY — Shared test fixtures and configuration.

Provides reusable fixtures for all test modules.
"""

import os
import tempfile

# Force testing environment before any pydantic settings or models are loaded
os.environ["ENVIRONMENT"] = "testing"
_test_dir = tempfile.mkdtemp(prefix="noray_test_data")
os.environ["DATABASE_URL"] = f"sqlite:///{_test_dir}/noray_test.db"
# Optional: also mock out vector db hosts if tests try to connect
os.environ["QDRANT_HOST"] = "localhost"
os.environ["REDIS_HOST"] = "localhost"
os.environ["QDRANT_PORT"] = "6333"

import tempfile
from pathlib import Path

import pytest

from noray.shared.models import (
    CareerProfile, Identity, Location, Language,
    Education, Experience, Skills, Certification,
    Project, Behavioral, CareerGoals, ScholarshipGoals,
    Publication, ProfileMeta,
)


@pytest.fixture
def sample_profile() -> CareerProfile:
    """Create a comprehensive sample profile for testing."""
    return CareerProfile(
        meta=ProfileMeta(version="1.0.0"),
        identity=Identity(
            name="Gharieb Mohamed",
            email="gharieb@example.com",
            phone="+201234567890",
            location=Location(city="Cairo", country="Egypt"),
            linkedin="https://linkedin.com/in/gharieb",
            github="https://github.com/GhariebML",
            languages=[
                Language(language="Arabic", proficiency="native"),
                Language(language="English", proficiency="fluent"),
            ],
        ),
        education=[
            Education(
                degree="BSc",
                field="Computer Science",
                institution="Cairo University",
                start_year=2018,
                end_year=2022,
                gpa="3.8",
                thesis="Deep Learning for Arabic NLP",
            ),
        ],
        experience=[
            Experience(
                title="Data Scientist",
                company="Google",
                location="Cairo",
                start_date="2022",
                end_date="present",
                responsibilities=[
                    "Built ML pipelines for ad targeting",
                    "Led a team of 5 engineers",
                    "Designed A/B testing framework",
                ],
                achievements=[
                    "Reduced latency by 40%",
                    "Improved accuracy from 72% to 89%",
                    "Saved $2M annually through optimization",
                ],
                technologies=["Python", "TensorFlow", "scikit-learn", "BigQuery"],
            ),
        ],
        projects=[
            Project(
                name="ADPilot",
                description="AI advertising platform for automated campaign optimization",
                technologies=["Python", "Machine Learning", "FastAPI"],
                url="https://github.com/GhariebML/ADPilot",
            ),
        ],
        skills=Skills(
            primary=["Python", "Machine Learning", "Data Science", "Deep Learning"],
            secondary=["NLP", "Computer Vision", "MLOps"],
            domain=["healthcare data", "advertising technology", "Arabic NLP"],
            tools=["Docker", "Git", "TensorFlow", "PyTorch", "scikit-learn", "BigQuery"],
        ),
        certifications=[
            Certification(name="AWS Solutions Architect", issuer="Amazon", date="2023"),
        ],
        publications=[
            Publication(
                authors=["Gharieb M.", "Awni K."],
                title="Deep Learning for Arabic Sentiment Analysis",
                journal="ACL 2023",
                year=2023,
            ),
        ],
        behavioral=Behavioral(
            strengths=["Analytical thinking", "Leadership", "Problem-solving", "Communication"],
            work_style="Collaborative, data-driven",
            values=["Innovation", "Impact", "Continuous learning"],
        ),
        goals=CareerGoals(
            target_roles=["Data Scientist", "ML Engineer", "Research Scientist"],
            target_sectors=["Technology", "Healthcare", "AI Research"],
            career_objectives=["Lead ML engineering teams", "Build impactful AI products"],
        ),
        scholarship_goals=ScholarshipGoals(
            target_degrees=["PhD"],
            target_countries=["Germany", "UK", "USA"],
            research_interests=["Machine Learning", "Healthcare AI", "NLP", "Arabic NLP"],
            funding_preferences=["Fully funded"],
        ),
    )


@pytest.fixture
def sample_profile_dict(sample_profile: CareerProfile) -> dict:
    """Sample profile as a dict (JSON-serializable)."""
    return sample_profile.model_dump(mode="json")


@pytest.fixture
def tmp_profile_path(tmp_path: Path) -> Path:
    """Temporary profile file path."""
    return tmp_path / "career_profile.json"


@pytest.fixture
def tmp_tracker_path(tmp_path: Path) -> Path:
    """Temporary tracker file path."""
    return tmp_path / "tracker.json"

@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    from noray.database import Base, engine
    # Create all tables in the temporary sqlite db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
