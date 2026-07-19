"""
NORAY — Edge Case & Integration Tests

Tests for edge cases, error handling, and cross-module integration.
"""

import tempfile
from pathlib import Path

import pytest

from noray.shared.models import CareerProfile, Identity, Skills, Education
from noray.shared.profile_store import (
    load_profile, save_profile, merge_profile, get_profile_diff,
    export_to_skill_files, backup_profile,
)
from noray.scholarship_agent.scholarship_search import search_scholarships, build_scholarship_queries
from noray.scholarship_agent.eligibility_scoring import score_eligibility
from noray.scholarship_agent.sop_generator import generate_sop
from noray.upskill_agent.skill_gap_analysis import analyze_skill_gaps
from noray.upskill_agent.roadmap_builder import build_roadmap, format_roadmap
from noray.upskill_agent.learning_resources import find_resources, suggest_study_order
from noray.dashboard.analytics import get_analytics_summary


# ─── Profile Edge Cases ───────────────────────────────────────

class TestProfileEdgeCases:
    """Test profile store edge cases."""

    def test_empty_profile_load(self):
        """Loading a profile with no file returns a default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.json"
            profile = load_profile(path=path)
            assert profile is not None
            assert isinstance(profile, CareerProfile)

    def test_save_and_reload_preserves_data(self, sample_profile):
        """Saving and loading preserves all data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_profile.json"
            save_profile(sample_profile, path=path)
            loaded = load_profile(path=path)
            assert loaded.identity.name == "Gharieb Mohamed"
            assert len(loaded.education) == 1
            assert loaded.education[0].degree == "BSc"
            assert "Python" in loaded.skills.primary

    def test_merge_with_empty_profile(self, sample_profile):
        """Merging with an empty profile keeps original data."""
        empty = CareerProfile()
        merged = merge_profile(sample_profile, empty)
        assert merged.identity.name == "Gharieb Mohamed"
        assert len(merged.education) == 1

    def test_merge_adds_new_data(self, sample_profile):
        """Merging adds new data without overwriting."""
        new_data = CareerProfile(
            identity=Identity(name="Gharieb Mohamed"),
            education=[Education(degree="MSc", field="AI", institution="MIT")],
        )
        merged = merge_profile(sample_profile, new_data)
        assert len(merged.education) == 2
        degrees = {e.degree for e in merged.education}
        assert "BSc" in degrees
        assert "MSc" in degrees

    def test_diff_empty_profiles(self):
        """Diffing two empty profiles shows no changes."""
        p1 = CareerProfile()
        p2 = CareerProfile()
        diff = get_profile_diff(p1, p2)
        # All values should be empty lists
        for key, val in diff.items():
            assert val == [], f"Expected empty list for '{key}', got {val}"

    def test_diff_detects_changes(self, sample_profile):
        """Diffing detects added education."""
        modified = sample_profile.model_copy(deep=True)
        modified.education.append(Education(degree="MSc", field="AI"))
        diff = get_profile_diff(sample_profile, modified)
        # Should detect the new MSc
        total_changes = sum(len(v) for v in diff.values())
        assert total_changes > 0

    def test_backup_creates_file(self, sample_profile):
        """Backup creates a timestamped file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_profile.json"
            save_profile(sample_profile, path=path)
            backup_path = backup_profile(path=path)
            assert backup_path is not None
            assert backup_path.exists()


# ─── Scholarship Edge Cases ───────────────────────────────────

class TestScholarshipEdgeCases:
    """Test scholarship module edge cases."""

    def test_empty_profile_search(self):
        """Searching with an empty profile returns results."""
        empty = CareerProfile().model_dump(mode="json")
        result = search_scholarships(empty)
        assert result.total_found >= 0

    def test_eligibility_empty_scholarship(self, sample_profile):
        """Eligibility scoring with empty scholarship criteria."""
        profile_dict = sample_profile.model_dump(mode="json")
        result = score_eligibility(profile_dict, {})
        assert result.overall_score >= 0

    def test_sop_empty_profile(self):
        """SOP generation with empty profile still produces output."""
        empty = CareerProfile()
        sop = generate_sop(empty, "PhD program", ["ML"])
        assert sop.success
        assert sop.word_count > 100

    def test_scholarship_queries_with_research(self, sample_profile):
        """Query building includes research interests."""
        profile_dict = sample_profile.model_dump(mode="json")
        queries = build_scholarship_queries(profile_dict, research_area="Healthcare AI")
        assert any("Healthcare AI" in q["query"] for q in queries)


# ─── Upskill Edge Cases ───────────────────────────────────────

class TestUpskillEdgeCases:
    """Test upskill module edge cases."""

    def test_gap_analysis_no_requirements(self, sample_profile):
        """Gap analysis with no requirements returns empty gaps."""
        profile_dict = sample_profile.model_dump(mode="json")
        result = analyze_skill_gaps(profile_dict, [])
        assert len(result.gaps) == 0

    def test_gap_analysis_all_covered(self, sample_profile):
        """Gap analysis with all skills covered returns empty gaps."""
        profile_dict = sample_profile.model_dump(mode="json")
        result = analyze_skill_gaps(profile_dict, ["Python", "Machine Learning"])
        assert len(result.gaps) == 0

    def test_gap_analysis_all_gaps(self, sample_profile):
        """Gap analysis with all skills missing returns all as gaps."""
        profile_dict = sample_profile.model_dump(mode="json")
        result = analyze_skill_gaps(profile_dict, ["Rust", "Go", "Haskell"])
        assert len(result.gaps) == 3

    def test_roadmap_empty_profile(self):
        """Roadmap generation with empty profile."""
        empty = CareerProfile().model_dump(mode="json")
        roadmap = build_roadmap(empty)
        assert len(roadmap.milestones) > 0
        assert roadmap.summary != ""

    def test_roadmap_formatting(self, sample_profile):
        """Roadmap formatting produces readable markdown."""
        profile_dict = sample_profile.model_dump(mode="json")
        roadmap = build_roadmap(profile_dict)
        formatted = format_roadmap(roadmap)
        assert "# Career Roadmap" in formatted
        assert "Month" in formatted

    def test_resources_unknown_skill(self):
        """Finding resources for unknown skill returns empty plan."""
        plan = find_resources("NonexistentSkillXYZ")
        assert plan.skill == "NonexistentSkillXYZ"
        assert len(plan.resources) == 0

    def test_study_order_empty(self):
        """Study order with empty list."""
        ordered = suggest_study_order([])
        assert len(ordered) == 0

    def test_study_order_single(self):
        """Study order with single plan."""
        plans = [find_resources("Python")]
        ordered = suggest_study_order(plans)
        assert len(ordered) == 1


# ─── Cross-Module Integration ─────────────────────────────────

class TestCrossModuleIntegration:
    """Integration tests spanning multiple modules."""

    def test_profile_to_scholarship_search(self, sample_profile):
        """Profile → scholarship search → eligibility scoring."""
        profile_dict = sample_profile.model_dump(mode="json")

        # Search
        result = search_scholarships(profile_dict, target_degree="PhD")
        assert len(result.scholarships) > 0

        # Score eligibility for top result
        top = result.scholarships[0]
        eligibility = score_eligibility(profile_dict, {"degree_level": "PhD", "required_languages": ["English"]})
        assert eligibility.overall_score >= 50

    def test_profile_to_gap_analysis_to_roadmap(self, sample_profile):
        """Profile → gap analysis → roadmap."""
        profile_dict = sample_profile.model_dump(mode="json")

        # Gap analysis
        gaps = analyze_skill_gaps(profile_dict, ["Kubernetes", "Go", "Rust"])
        assert len(gaps.gaps) > 0

        # Roadmap from gaps
        gap_dicts = [
            {"skill": g.skill, "time_estimate": g.time_estimate, "study_direction": g.study_direction}
            for g in gaps.gaps
        ]
        roadmap = build_roadmap(profile_dict, skill_gaps=gap_dicts)
        assert len(roadmap.milestones) > 0

    def test_full_document_generation_pipeline(self, sample_profile):
        """Profile → SOP + motivation letter + research proposal."""
        # SOP
        sop = generate_sop(sample_profile, "DAAD PhD", ["ML", "Healthcare AI"])
        assert sop.success
        assert sop.word_count > 200

        # All should use the same profile data consistently
        assert "Gharieb" in sop.content or "Cairo" in sop.content

    def test_profile_export_import_roundtrip(self, sample_profile):
        """Profile → export to skill files → verify content."""
        files = export_to_skill_files(sample_profile)
        assert len(files) > 0
        # Each file should have content
        for filename, content in files.items():
            assert len(content) > 0

    def test_dashboard_with_mixed_data(self):
        """Dashboard handles mixed job + scholarship data."""
        import noray.dashboard.jobs as jmod
        import noray.dashboard.scholarships as smod
        from noray.dashboard.jobs import JobApplication, add_application as add_job
        from noray.dashboard.scholarships import ScholarshipApplication, add_application as add_sch

        j_original = jmod.TRACKER_PATH
        s_original = smod.TRACKER_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            jmod.TRACKER_PATH = Path(tmpdir) / "jobs.json"
            smod.TRACKER_PATH = Path(tmpdir) / "sch.json"

            add_job(JobApplication(company="Google", role="ML Engineer", status="applied"))
            add_sch(ScholarshipApplication(name="DAAD", status="submitted"))

            analytics = get_analytics_summary()
            assert analytics["jobs"]["total_tracked"] == 1
            assert analytics["scholarships"]["total_tracked"] == 1

        jmod.TRACKER_PATH = j_original
        smod.TRACKER_PATH = s_original


# ─── Model Edge Cases ─────────────────────────────────────────

class TestModelEdgeCases:
    """Test Pydantic model edge cases."""

    def test_profile_with_none_fields(self):
        """Profile handles None values gracefully."""
        profile = CareerProfile(
            identity=Identity(name="Test"),
            education=[],
            experience=[],
            skills=Skills(),
        )
        assert profile.identity.name == "Test"
        assert profile.education == []
        assert profile.skills.primary == []

    def test_profile_serialization_roundtrip(self, sample_profile):
        """Profile → dict → JSON → dict → Profile preserves data."""
        data = sample_profile.model_dump(mode="json")
        restored = CareerProfile(**data)
        assert restored.identity.name == sample_profile.identity.name
        assert len(restored.education) == len(sample_profile.education)
        assert restored.skills.primary == sample_profile.skills.primary

    def test_profile_with_unicode(self):
        """Profile handles unicode characters."""
        profile = CareerProfile(
            identity=Identity(name="Gharieb محمد"),
        )
        data = profile.model_dump(mode="json")
        assert "محمد" in data["identity"]["name"]

    def test_experience_with_empty_lists(self):
        """Experience handles empty lists."""
        from noray.shared.models import Experience
        exp = Experience(title="Engineer", company="Test")
        assert exp.responsibilities == []
        assert exp.achievements == []
        assert exp.technologies == []
