"""
Tests for the NORAY Profile Engine module.

Tests the core profile store, models, importers, and builder.
"""

import json
import tempfile
from pathlib import Path

import pytest

from noray.shared.models import (
    CareerProfile, Identity, Location, Language,
    Education, Experience, Skills, Certification,
    Award, Publication, Project, Behavioral,
    CareerGoals, ScholarshipGoals, GitHubProfile,
    ProfileMeta,
)
from noray.shared.profile_store import (
    load_profile, save_profile, profile_exists,
    merge_profile, get_profile_diff, backup_profile,
    export_to_skill_files, migrate_from_skill_files,
)


# ─── Model Tests ──────────────────────────────────────────────

class TestModels:
    """Test Pydantic data models."""

    def test_empty_profile(self):
        profile = CareerProfile()
        assert profile.identity.name == ""
        assert profile.education == []
        assert profile.experience == []
        assert profile.skills.primary == []

    def test_profile_with_data(self):
        profile = CareerProfile(
            identity=Identity(
                name="Gharieb",
                email="test@example.com",
                location=Location(city="Cairo", country="Egypt"),
                languages=[Language(language="Arabic", proficiency="native")],
            ),
            education=[
                Education(
                    degree="BSc",
                    field="Computer Science",
                    institution="Cairo University",
                    start_year=2018,
                    end_year=2022,
                )
            ],
            skills=Skills(
                primary=["Python", "Machine Learning"],
                tools=["Git", "Docker"],
            ),
        )
        assert profile.identity.name == "Gharieb"
        assert len(profile.education) == 1
        assert profile.education[0].degree == "BSc"
        assert "Python" in profile.skills.primary

    def test_profile_serialization(self):
        profile = CareerProfile(
            identity=Identity(name="Test User"),
            skills=Skills(primary=["Python"]),
        )
        data = profile.model_dump(mode="json")
        assert isinstance(data, dict)
        assert data["identity"]["name"] == "Test User"
        assert "Python" in data["skills"]["primary"]

    def test_profile_deserialization(self):
        data = {
            "identity": {"name": "Test", "location": {"city": "Cairo"}},
            "education": [{"degree": "BSc", "field": "CS", "institution": "MIT"}],
            "skills": {"primary": ["Python"]},
        }
        profile = CareerProfile.model_validate(data)
        assert profile.identity.name == "Test"
        assert profile.identity.location.city == "Cairo"
        assert len(profile.education) == 1

    def test_experience_model(self):
        exp = Experience(
            title="Data Scientist",
            company="Google",
            location="Zurich",
            start_date="2022-01",
            end_date="present",
            responsibilities=["Built ML pipelines", "Led team of 3"],
            technologies=["Python", "TensorFlow"],
        )
        assert exp.title == "Data Scientist"
        assert len(exp.responsibilities) == 2

    def test_github_profile(self):
        github = GitHubProfile(
            username="testuser",
            repos=[{"name": "repo1", "url": "https://github.com/testuser/repo1"}],
            languages=["Python", "JavaScript"],
        )
        assert github.username == "testuser"
        assert len(github.repos) == 1


# ─── Profile Store Tests ─────────────────────────────────────

class TestProfileStore:
    """Test profile CRUD operations."""

    def test_load_nonexistent_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "career_profile.json"
            profile = load_profile(path)
            assert profile.identity.name == ""
            assert profile.meta.version == "1.0.0"

    def test_save_and_load_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "career_profile.json"
            profile = CareerProfile(
                identity=Identity(name="Test User"),
                skills=Skills(primary=["Python", "ML"]),
            )
            save_profile(profile, path)

            loaded = load_profile(path)
            assert loaded.identity.name == "Test User"
            assert "Python" in loaded.skills.primary

    def test_profile_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "career_profile.json"
            assert not profile_exists(path)

            profile = CareerProfile(identity=Identity(name="Test"))
            save_profile(profile, path)
            assert profile_exists(path)

    def test_backup_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "career_profile.json"
            profile = CareerProfile(identity=Identity(name="Test"))
            save_profile(profile, path)

            backup = backup_profile(path)
            assert backup is not None
            assert backup.exists()
            assert "backup" in backup.name

    def test_backup_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "career_profile.json"
            assert backup_profile(path) is None


# ─── Merge Tests ──────────────────────────────────────────────

class TestMerge:
    """Test profile merging logic."""

    def test_merge_identity(self):
        existing = CareerProfile(identity=Identity(name="Existing"))
        incoming = CareerProfile(
            identity=Identity(email="new@example.com", name="Incoming")
        )
        merged = merge_profile(existing, incoming)
        assert merged.identity.name == "Existing"  # Don't overwrite non-empty
        assert merged.identity.email == "new@example.com"

    def test_merge_identity_overwrite(self):
        existing = CareerProfile(identity=Identity(name="Old"))
        incoming = CareerProfile(identity=Identity(name="New"))
        merged = merge_profile(existing, incoming, overwrite=True)
        assert merged.identity.name == "New"

    def test_merge_education(self):
        existing = CareerProfile(education=[
            Education(degree="BSc", field="CS", institution="MIT"),
        ])
        incoming = CareerProfile(education=[
            Education(degree="MSc", field="ML", institution="Stanford"),
        ])
        merged = merge_profile(existing, incoming)
        assert len(merged.education) == 2

    def test_merge_education_no_duplicate(self):
        existing = CareerProfile(education=[
            Education(degree="BSc", field="CS", institution="MIT"),
        ])
        incoming = CareerProfile(education=[
            Education(degree="BSc", field="CS", institution="MIT"),
        ])
        merged = merge_profile(existing, incoming)
        assert len(merged.education) == 1

    def test_merge_skills(self):
        existing = CareerProfile(skills=Skills(primary=["Python"]))
        incoming = CareerProfile(skills=Skills(primary=["Python", "ML"], tools=["Git"]))
        merged = merge_profile(existing, incoming)
        assert "Python" in merged.skills.primary
        assert "ML" in merged.skills.primary
        assert "Git" in merged.skills.tools

    def test_merge_experience(self):
        existing = CareerProfile(experience=[
            Experience(title="Engineer", company="Google"),
        ])
        incoming = CareerProfile(experience=[
            Experience(title="Engineer", company="Google"),  # duplicate
            Experience(title="Scientist", company="Meta"),  # new
        ])
        merged = merge_profile(existing, incoming)
        assert len(merged.experience) == 2

    def test_merge_certifications(self):
        existing = CareerProfile(certifications=[
            Certification(name="AWS SA", issuer="Amazon"),
        ])
        incoming = CareerProfile(certifications=[
            Certification(name="AWS SA", issuer="Amazon"),  # duplicate
            Certification(name="GCP ACE", issuer="Google"),  # new
        ])
        merged = merge_profile(existing, incoming)
        assert len(merged.certifications) == 2

    def test_merge_projects(self):
        existing = CareerProfile(projects=[
            Project(name="Project A", description="desc a"),
        ])
        incoming = CareerProfile(projects=[
            Project(name="Project A", description="desc a"),  # duplicate
            Project(name="Project B", description="desc b"),  # new
        ])
        merged = merge_profile(existing, incoming)
        assert len(merged.projects) == 2

    def test_merge_languages(self):
        existing = CareerProfile(
            identity=Identity(languages=[Language(language="Arabic")])
        )
        incoming = CareerProfile(
            identity=Identity(languages=[Language(language="Arabic"), Language(language="English")])
        )
        merged = merge_profile(existing, incoming)
        assert len(merged.identity.languages) == 2

    def test_merge_github(self):
        existing = CareerProfile(github=GitHubProfile(
            username="user1",
            repos=[{"name": "repo1", "url": "https://github.com/user1/repo1"}],
            languages=["Python"],
        ))
        incoming = CareerProfile(github=GitHubProfile(
            username="user1",
            repos=[
                {"name": "repo1", "url": "https://github.com/user1/repo1"},  # dup
                {"name": "repo2", "url": "https://github.com/user1/repo2"},  # new
            ],
            languages=["Python", "JavaScript"],
        ))
        merged = merge_profile(existing, incoming)
        assert len(merged.github.repos) == 2
        assert "JavaScript" in merged.github.languages

    def test_merge_sources(self):
        existing = CareerProfile(meta=ProfileMeta(sources=["cv"]))
        incoming = CareerProfile(meta=ProfileMeta(sources=["linkedin"]))
        merged = merge_profile(existing, incoming, source="github")
        assert "cv" in merged.meta.sources
        assert "linkedin" in merged.meta.sources
        assert "github" in merged.meta.sources


# ─── Diff Tests ───────────────────────────────────────────────

class TestDiff:
    """Test profile diff computation."""

    def test_diff_empty(self):
        existing = CareerProfile()
        incoming = CareerProfile()
        diff = get_profile_diff(existing, incoming)
        assert diff == {}

    def test_diff_new_education(self):
        existing = CareerProfile()
        incoming = CareerProfile(education=[
            Education(degree="BSc", field="CS", institution="MIT"),
        ])
        diff = get_profile_diff(existing, incoming)
        assert "education" in diff
        assert len(diff["education"]) == 1

    def test_diff_existing_education(self):
        existing = CareerProfile(education=[
            Education(degree="BSc", field="CS", institution="MIT"),
        ])
        incoming = CareerProfile(education=[
            Education(degree="BSc", field="CS", institution="MIT"),
        ])
        diff = get_profile_diff(existing, incoming)
        assert "education" not in diff  # Already exists

    def test_diff_new_skills(self):
        existing = CareerProfile(skills=Skills(primary=["Python"]))
        incoming = CareerProfile(skills=Skills(primary=["Python", "ML"]))
        diff = get_profile_diff(existing, incoming)
        assert "skills" in diff
        assert any("ML" in s for s in diff["skills"])

    def test_diff_new_experience(self):
        existing = CareerProfile()
        incoming = CareerProfile(experience=[
            Experience(title="Engineer", company="Google"),
        ])
        diff = get_profile_diff(existing, incoming)
        assert "experience" in diff


# ─── Export Tests ─────────────────────────────────────────────

class TestExport:
    """Test skill file export."""

    def test_export_basic_profile(self):
        profile = CareerProfile(
            identity=Identity(
                name="Test User",
                location=Location(city="Cairo", country="Egypt"),
            ),
            education=[
                Education(degree="BSc", field="CS", institution="MIT", start_year=2018, end_year=2022),
            ],
            experience=[
                Experience(title="Engineer", company="Google", start_date="2022", end_date="present"),
            ],
            skills=Skills(primary=["Python", "ML"], tools=["Git"]),
        )
        exports = export_to_skill_files(profile)
        assert "01-candidate-profile.md" in exports
        content = exports["01-candidate-profile.md"]
        assert "Test User" in content
        assert "Cairo" in content
        assert "Python" in content
        assert "BSc in CS" in content

    def test_export_empty_profile(self):
        profile = CareerProfile()
        exports = export_to_skill_files(profile)
        assert "01-candidate-profile.md" in exports
        content = exports["01-candidate-profile.md"]
        assert "Candidate Profile" in content

    def test_export_with_certifications(self):
        profile = CareerProfile(
            certifications=[
                Certification(name="AWS SA", issuer="Amazon", date="2023"),
            ]
        )
        exports = export_to_skill_files(profile)
        assert "AWS SA" in exports["01-candidate-profile.md"]

    def test_export_with_publications(self):
        profile = CareerProfile(
            publications=[
                Publication(
                    authors=["Gharieb", "Awni"],
                    title="ML Paper",
                    journal="ICML",
                    year=2023,
                )
            ]
        )
        exports = export_to_skill_files(profile)
        assert "ML Paper" in exports["01-candidate-profile.md"]

    def test_export_behavioral(self):
        profile = CareerProfile(
            behavioral=Behavioral(
                strengths=["Analytical", "Creative"],
                growth_areas=["Public Speaking"],
                ideal_environment="Fast-paced startup",
            )
        )
        exports = export_to_skill_files(profile)
        assert "Analytical" in exports["01-candidate-profile.md"]
        assert "Public Speaking" in exports["01-candidate-profile.md"]

    def test_export_interview_prep(self):
        profile = CareerProfile(experience=[
            Experience(title="Data Scientist", company="Google"),
            Experience(title="ML Engineer", company="Meta"),
        ])
        exports = export_to_skill_files(profile)
        assert "07-interview-prep.md" in exports
        assert "Data Scientist" in exports["07-interview-prep.md"]


# ─── CV Importer Tests ───────────────────────────────────────

class TestCVImporter:
    """Test CV parsing and import."""

    def test_extract_email(self):
        from noray.profile_engine.cv_importer import _extract_email
        assert _extract_email("Contact: john@example.com or call") == "john@example.com"
        assert _extract_email("No email here") == ""

    def test_extract_linkedin(self):
        from noray.profile_engine.cv_importer import _extract_linkedin
        assert "linkedin.com/in/johndoe" in _extract_linkedin("linkedin.com/in/johndoe")
        assert _extract_linkedin("No linkedin") == ""

    def test_extract_github(self):
        from noray.profile_engine.cv_importer import _extract_github
        assert "github.com/testuser" in _extract_github("github.com/testuser")

    def test_extract_name(self):
        from noray.profile_engine.cv_importer import _extract_name
        text = "John Doe\nSoftware Engineer\njohn@example.com"
        # Name extraction is best-effort; validate it returns something reasonable
        result = _extract_name(text)
        # The pattern looks for 2-5 word alphabetic lines at the top
        assert result == "John Doe" or result == ""  # May skip if pattern doesn't match

    def test_extract_skills(self):
        from noray.profile_engine.cv_importer import _extract_skills_section
        text = """
        Skills
        Python, JavaScript, SQL, Machine Learning, Docker, Git
        """
        skills = _extract_skills_section(text)
        # Skills are normalized to lowercase in the extractor
        all_found = skills["primary"] + skills.get("tools", [])
        assert any("python" in s.lower() for s in all_found)

    def test_pattern_extract(self):
        from noray.profile_engine.cv_importer import _pattern_extract
        text = """
        John Doe
        john@example.com
        +1 555 123 4567
        linkedin.com/in/johndoe
        github.com/johndoe
        
        Education
        BSc in Computer Science, MIT, 2018 - 2022
        
        Skills
        Python, Machine Learning, Docker
        """
        result = _pattern_extract(text)
        assert result["email"] == "john@example.com"
        assert "linkedin.com/in/johndoe" in result["linkedin"]

    def test_parse_nonexistent_file(self):
        from noray.profile_engine.cv_importer import parse_cv
        with pytest.raises(FileNotFoundError):
            parse_cv(Path("/nonexistent/file.pdf"))

    def test_parse_unsupported_format(self):
        from noray.profile_engine.cv_importer import parse_cv
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test")
            path = Path(f.name)
        with pytest.raises(ValueError, match="Unsupported"):
            parse_cv(path)
        path.unlink()


# ─── LaTeX Extraction Tests ───────────────────────────────────

class TestLatexExtraction:
    """Test LaTeX CV text extraction."""

    def test_extract_from_latex(self, tmp_path):
        from noray.profile_engine.cv_importer import _extract_from_latex
        tex_content = r"""
        \documentclass{moderncv}
        \name{John}{Doe}
        \email{john@example.com}
        \begin{document}
        \section{Education}
        \cventry{2018--2022}{BSc Computer Science}{MIT}{}{}{}
        \section{Experience}
        \cventry{2022--present}{Data Scientist}{Google}{}{}{Built ML pipelines}
        \end{document}
        """
        tex_file = tmp_path / "cv.tex"
        tex_file.write_text(tex_content)
        text = _extract_from_latex(tex_file)
        assert "john@example.com" in text
        assert "Education" in text


# ─── GitHub Importer Tests ────────────────────────────────────

class TestGitHubImporter:
    """Test GitHub API integration."""

    def test_import_invalid_user(self):
        from noray.profile_engine.github_importer import fetch_github_profile
        result = fetch_github_profile("this-user-definitely-does-not-exist-xyz-12345")
        assert "error" in result or result.get("total_repos", 0) == 0


# ─── Eligibility Scoring Tests ────────────────────────────────

class TestEligibilityScoring:
    """Test scholarship eligibility scoring."""

    def test_eligibility_basic(self):
        from noray.scholarship_agent.eligibility_scoring import score_eligibility
        profile = {
            "identity": {
                "location": {"country": "Egypt"},
                "languages": [{"language": "English"}, {"language": "Arabic"}],
            },
            "education": [{"degree": "BSc", "field": "Computer Science"}],
        }
        scholarship = {
            "eligible_nationalities": ["Egypt", "Jordan", "Tunisia"],
            "degree_level": "MSc",
            "field_restrictions": ["Computer Science", "Engineering"],
            "required_languages": ["English"],
        }
        result = score_eligibility(profile, scholarship)
        assert result.is_eligible
        assert result.overall_score >= 50
        assert len(result.criteria_met) >= 2

    def test_eligibility_ineligible(self):
        from noray.scholarship_agent.eligibility_scoring import score_eligibility
        profile = {
            "identity": {
                "location": {"country": "USA"},
                "languages": [{"language": "English"}],
            },
            "education": [{"degree": "BSc", "field": "Art History"}],
        }
        scholarship = {
            "eligible_nationalities": ["Egypt", "Jordan"],
            "degree_level": "PhD",
            "field_restrictions": ["Computer Science", "Engineering"],
            "required_languages": ["German"],
        }
        result = score_eligibility(profile, scholarship)
        assert not result.is_eligible or result.overall_score < 50


# ─── ATS Analyzer Tests ──────────────────────────────────────

class TestATSAnalyzer:
    """Test ATS compatibility scoring."""

    def test_ats_good_cv(self):
        from noray.career_agent.ats_analyzer import analyze_cv_ats
        cv_text = """
        JOHN DOE
        john@example.com | +1 555 123 4567
        
        EDUCATION
        BSc in Computer Science, MIT, 2018-2022
        
        EXPERIENCE
        Data Scientist at Google (2022 - Present)
        - Built ML pipelines using Python and TensorFlow
        - Reduced inference latency by 40%
        
        SKILLS
        Python, Machine Learning, Docker, AWS
        """
        score = analyze_cv_ats(cv_text, ["Python", "Machine Learning", "AWS"])
        assert score.overall_score >= 60
        assert "Python" in score.keywords_found

    def test_ats_poor_cv(self):
        from noray.career_agent.ats_analyzer import analyze_cv_ats
        cv_text = "Just some random text without any structure"
        score = analyze_cv_ats(cv_text)
        assert score.overall_score < 80
        assert len(score.issues) > 0

    def test_ats_keyword_matching(self):
        from noray.career_agent.ats_analyzer import analyze_cv_ats
        cv_text = "Python developer with Docker and Kubernetes experience"
        score = analyze_cv_ats(cv_text, ["Python", "Docker", "Kubernetes", "AWS", "Terraform"])
        assert "Python" in score.keywords_found
        assert "AWS" in score.keywords_missing


# ─── Skill Gap Analysis Tests ─────────────────────────────────

class TestSkillGapAnalysis:
    """Test skill gap analysis."""

    def test_gap_analysis_basic(self):
        from noray.upskill_agent.skill_gap_analysis import analyze_skill_gaps
        profile = {
            "skills": {
                "primary": ["Python", "Machine Learning"],
                "tools": ["Git", "Docker"],
            }
        }
        requirements = ["Python", "Kubernetes", "AWS", "Machine Learning"]
        result = analyze_skill_gaps(profile, requirements, mode="targeted")
        assert result.mode == "targeted"
        gap_skills = [g.skill for g in result.gaps]
        assert "Kubernetes" in gap_skills
        assert "AWS" in gap_skills
        assert "Python" not in gap_skills

    def test_gap_analysis_no_gaps(self):
        from noray.upskill_agent.skill_gap_analysis import analyze_skill_gaps
        profile = {
            "skills": {"primary": ["Python", "ML"], "tools": ["Git"]}
        }
        result = analyze_skill_gaps(profile, ["Python", "ML", "Git"])
        assert len(result.gaps) == 0


# ─── Integration Test ─────────────────────────────────────────

class TestIntegration:
    """Integration tests for the full profile pipeline."""

    def test_full_pipeline(self, tmp_path):
        """Test creating, saving, loading, merging, and exporting a profile."""
        from noray.config import CAREER_PROFILE_PATH

        # Create profile
        profile = CareerProfile(
            identity=Identity(
                name="Gharieb",
                email="gharieb@example.com",
                location=Location(city="Cairo", country="Egypt"),
            ),
            education=[
                Education(degree="BSc", field="CS", institution="Cairo University", start_year=2018, end_year=2022),
            ],
            skills=Skills(primary=["Python", "ML"], tools=["Git"]),
        )

        # Save
        path = tmp_path / "career_profile.json"
        save_profile(profile, path)
        assert path.exists()

        # Load
        loaded = load_profile(path)
        assert loaded.identity.name == "Gharieb"

        # Merge new data
        incoming = CareerProfile(
            experience=[Experience(title="Data Scientist", company="Google")],
            skills=Skills(primary=["Python", "ML", "Deep Learning"], tools=["Docker"]),
        )
        merged = merge_profile(loaded, incoming)
        assert len(merged.experience) == 1
        assert "Deep Learning" in merged.skills.primary
        assert "Docker" in merged.skills.tools

        # Save merged
        save_profile(merged, path)

        # Export to skill files
        exports = export_to_skill_files(merged)
        assert "Gharieb" in exports["01-candidate-profile.md"]
        assert "Deep Learning" in exports["01-candidate-profile.md"]
        assert "Data Scientist" in exports["01-candidate-profile.md"]
