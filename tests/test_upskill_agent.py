"""
Tests for the NORAY Upskill Agent module.

Tests skill gap analysis, roadmap building, and learning resources.
"""

import pytest

from noray.shared.models import (
    CareerProfile, Identity, Location, Language,
    Education, Experience, Skills, Certification,
    Project, Behavioral, CareerGoals, ScholarshipGoals,
)
from noray.upskill_agent.skill_gap_analysis import (
    SkillGap, GapAnalysisResult, analyze_skill_gaps,
    generate_optimization_report,
    _extract_profile_skills, _skill_matches, _classify_skill_type,
    _classify_gap_type, _estimate_learning_time, _prioritize_gaps,
)
from noray.upskill_agent.roadmap_builder import (
    Milestone, CareerRoadmap, build_roadmap, format_roadmap,
    _determine_career_path, _month_to_int, _parse_hours,
    _create_learning_milestones, _create_certification_milestones,
    _create_project_milestones, _create_application_milestones,
)
from noray.upskill_agent.learning_resources import (
    LearningResource, LearningPlan, find_resources,
    suggest_study_order, _get_prerequisites, _get_learning_milestones,
)


# ─── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def sample_profile() -> CareerProfile:
    return CareerProfile(
        identity=Identity(
            name="Gharieb Mohamed",
            email="gharieb@example.com",
            location=Location(city="Cairo", country="Egypt"),
            languages=[
                Language(language="Arabic", proficiency="native"),
                Language(language="English", proficiency="fluent"),
            ],
        ),
        education=[
            Education(
                degree="BSc", field="Computer Science", institution="Cairo University",
                start_year=2018, end_year=2022,
            ),
        ],
        experience=[
            Experience(
                title="Data Scientist", company="Google", location="Cairo",
                start_date="2022", end_date="present",
                responsibilities=["Built ML pipelines"],
                achievements=["Reduced latency by 40%"],
                technologies=["Python", "TensorFlow", "scikit-learn"],
            ),
        ],
        projects=[
            Project(name="ADPilot", description="AI advertising platform", technologies=["Python", "ML"]),
        ],
        skills=Skills(
            primary=["Python", "Machine Learning", "Data Science"],
            secondary=["NLP", "Deep Learning"],
            domain=["healthcare data", "advertising technology"],
            tools=["Docker", "Git", "TensorFlow"],
        ),
        certifications=[
            Certification(name="AWS SA", issuer="Amazon", date="2023"),
        ],
        behavioral=Behavioral(
            strengths=["Analytical", "Leadership", "Problem-solving"],
        ),
        goals=CareerGoals(
            target_roles=["Data Scientist", "ML Engineer"],
            target_sectors=["Tech", "Healthcare"],
            career_objectives=["Lead ML engineering teams"],
        ),
        scholarship_goals=ScholarshipGoals(
            target_degrees=["PhD"],
            target_countries=["Germany", "UK"],
            research_interests=["Machine Learning", "Healthcare AI", "NLP"],
        ),
    )


# ─── Skill Gap Analysis Tests ─────────────────────────────────

class TestSkillGapAnalysis:
    """Test skill gap analysis."""

    def test_analyze_gaps_targeted(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["Python", "Machine Learning", "Kubernetes", "Rust"]
        result = analyze_skill_gaps(profile_dict, requirements, mode="targeted")
        assert isinstance(result, GapAnalysisResult)
        assert result.mode == "targeted"
        assert result.profile_skills_count > 0

    def test_identifies_gaps(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["Rust", "Go", "Kubernetes"]
        result = analyze_skill_gaps(profile_dict, requirements)
        # All three should be gaps
        assert len(result.gaps) == 3
        gap_skills = {g.skill for g in result.gaps}
        assert "Rust" in gap_skills
        assert "Go" in gap_skills
        assert "Kubernetes" in gap_skills

    def test_no_gaps_when_covered(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["Python", "Machine Learning"]
        result = analyze_skill_gaps(profile_dict, requirements)
        assert len(result.gaps) == 0

    def test_gap_types(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["PhD", "Docker", "Leadership", "NLP", "Healthcare AI"]
        result = analyze_skill_gaps(profile_dict, requirements)
        # Should classify correctly
        types = {g.gap_type for g in result.gaps}
        assert "credential" in types  # PhD
        assert "soft" in types  # Leadership
        # Note: Docker is in profile tools, so won't be a gap

    def test_gap_frequency_boosts_priority(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["Rust", "Go"]
        freq = {"Rust": 10, "Go": 1}
        result = analyze_skill_gaps(profile_dict, requirements, job_frequency=freq)
        rust_gap = next(g for g in result.gaps if g.skill == "Rust")
        go_gap = next(g for g in result.gaps if g.skill == "Go")
        # Rust with frequency 10 should have higher score
        assert rust_gap.score > go_gap.score
        # Rust should be critical (freq >= 5)
        assert rust_gap.priority == "critical"

    def test_themes_grouping(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["Python", "Machine Learning", "Deep Learning", "NLP"]
        result = analyze_skill_gaps(profile_dict, requirements)
        # These are covered, so no gaps. Test with uncovered skills
        requirements2 = ["Kubernetes", "React", "Leadership"]
        result2 = analyze_skill_gaps(profile_dict, requirements2)
        assert len(result2.themes) > 0

    def test_recommendations(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["Kubernetes", "Go", "Rust", "React"]
        result = analyze_skill_gaps(profile_dict, requirements)
        assert len(result.recommendations) > 0

    def test_top_priority_skills(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["Kubernetes", "Go", "Rust"]
        result = analyze_skill_gaps(profile_dict, requirements)
        assert len(result.top_priority_skills) > 0

    def test_extract_profile_skills(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        skills = _extract_profile_skills(profile_dict)
        assert "python" in skills
        assert "machine learning" in skills
        assert "docker" in skills

    def test_skill_matches(self):
        skills = {"python", "machine learning", "docker"}
        assert _skill_matches("Python", skills)
        assert _skill_matches("Machine Learning", skills)
        assert not _skill_matches("Rust", skills)

    def test_classify_skill_type(self):
        assert _classify_skill_type("Python") == "programming"
        assert _classify_skill_type("Machine Learning") == "ml_ai"
        assert _classify_skill_type("Docker") == "cloud"
        assert _classify_skill_type("Leadership") == "soft"
        assert _classify_skill_type("NLP") == "ml_ai"

    def test_classify_gap_type(self):
        assert _classify_gap_type("PhD") == "credential"
        assert _classify_gap_type("Docker") == "tooling"
        assert _classify_gap_type("Leadership") == "soft"
        assert _classify_gap_type("NLP") == "domain"
        assert _classify_gap_type("Python") == "hard"

    def test_estimate_learning_time(self):
        assert _estimate_learning_time("Python", "hard") != ""
        assert _estimate_learning_time("PhD", "credential") == "~200h"
        assert _estimate_learning_time("Leadership", "soft") == "~30h"

    def test_optimization_report(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["Kubernetes", "Go", "React"]
        report = generate_optimization_report(profile_dict, requirements)
        assert "Skill Gap Analysis Report" in report
        assert "Kubernetes" in report
        assert "Go" in report


# ─── Roadmap Builder Tests ────────────────────────────────────

class TestRoadmapBuilder:
    """Test roadmap building."""

    def test_build_roadmap(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        roadmap = build_roadmap(profile_dict)
        assert isinstance(roadmap, CareerRoadmap)
        assert roadmap.timeline_months == 12
        assert len(roadmap.milestones) > 0

    def test_roadmap_with_gaps(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        gaps = [
            {"skill": "Kubernetes", "time_estimate": "~60h", "study_direction": "Learn K8s"},
            {"skill": "Go", "time_estimate": "~40h", "study_direction": "Learn Go"},
        ]
        roadmap = build_roadmap(profile_dict, skill_gaps=gaps)
        titles = [m.title for m in roadmap.milestones]
        assert any("Kubernetes" in t for t in titles)
        assert any("Go" in t for t in titles)

    def test_roadmap_has_phases(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        roadmap = build_roadmap(profile_dict)
        assert len(roadmap.phases) > 0

    def test_roadmap_summary(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        roadmap = build_roadmap(profile_dict)
        assert roadmap.summary != ""
        assert roadmap.total_time_estimate != ""

    def test_format_roadmap(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        roadmap = build_roadmap(profile_dict)
        formatted = format_roadmap(roadmap)
        assert "Career Roadmap" in formatted
        assert "Summary" in formatted
        assert "Phase" in formatted

    def test_determine_career_path(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        path = _determine_career_path(profile_dict, profile_dict.get("goals", {}))
        assert path in ("data_scientist", "ml_engineer", "software_engineer")

    def test_determine_path_ml(self):
        profile = {"skills": {"primary": ["Machine Learning", "Deep Learning"]}, "goals": {"target_roles": ["ML Engineer"]}}
        assert _determine_career_path(profile, profile["goals"]) == "ml_engineer"

    def test_determine_path_sw(self):
        profile = {"skills": {"primary": ["React", "Node.js"]}, "goals": {"target_roles": ["Software Engineer"]}}
        assert _determine_career_path(profile, profile["goals"]) == "software_engineer"

    def test_create_learning_milestones(self):
        gaps = [
            {"skill": "Kubernetes", "time_estimate": "~60h", "study_direction": "Learn K8s"},
            {"skill": "Go", "time_estimate": "~40h", "study_direction": "Learn Go"},
        ]
        milestones = _create_learning_milestones(gaps, 12)
        assert len(milestones) == 2
        assert "Kubernetes" in milestones[0].title

    def test_create_cert_milestones(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        milestones = _create_certification_milestones(profile_dict, "ml_engineer", 12)
        assert len(milestones) > 0

    def test_create_project_milestones(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        milestones = _create_project_milestones(profile_dict, "data_scientist", 12)
        assert len(milestones) > 0

    def test_create_application_milestones(self):
        goals = {"target_roles": ["ML Engineer"], "target_countries": ["Germany"]}
        milestones = _create_application_milestones(goals, 12)
        assert len(milestones) >= 2

    def test_month_to_int(self):
        assert _month_to_int("Month 3") == 3
        assert _month_to_int("Month 12") == 12
        assert _month_to_int("invalid") == 99

    def test_parse_hours(self):
        assert _parse_hours("~40h") == 40
        assert _parse_hours("~120h") == 120
        assert _parse_hours("invalid") == 0

    def test_milestone_categories(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        roadmap = build_roadmap(profile_dict)
        categories = {m.category for m in roadmap.milestones}
        # Should have at least project, application, networking
        assert "project" in categories
        assert "application" in categories
        assert "networking" in categories


# ─── Learning Resources Tests ─────────────────────────────────

class TestLearningResources:
    """Test learning resource finding."""

    def test_find_resources_python(self):
        plan = find_resources("Python")
        assert isinstance(plan, LearningPlan)
        assert plan.skill == "Python"
        assert len(plan.resources) > 0
        assert plan.total_hours > 0

    def test_find_resources_ml(self):
        plan = find_resources("Machine Learning")
        assert len(plan.resources) > 0
        assert any("Coursera" in r.provider or "fast.ai" in r.provider for r in plan.resources)

    def test_find_resources_docker(self):
        plan = find_resources("Docker")
        assert len(plan.resources) > 0
        assert any(r.free for r in plan.resources)

    def test_find_resources_with_format(self):
        plan = find_resources("Python", preferred_format="course")
        assert all(r.resource_type == "course" for r in plan.resources)

    def test_find_resources_unknown_skill(self):
        plan = find_resources("UnknownSkill123")
        assert isinstance(plan, LearningPlan)
        assert len(plan.resources) == 0

    def test_prerequisites(self):
        prereqs = _get_prerequisites("Machine Learning")
        assert "python" in prereqs

        prereqs_dl = _get_prerequisites("Deep Learning")
        assert "machine learning" in prereqs_dl

    def test_learning_milestones(self):
        milestones = _get_learning_milestones("Python", "beginner")
        assert len(milestones) > 0

    def test_suggest_study_order(self):
        plans = [
            find_resources("Deep Learning"),
            find_resources("Python"),
            find_resources("Kubernetes"),
        ]
        ordered = suggest_study_order(plans)
        # Python should come before Deep Learning
        python_idx = next(i for i, p in enumerate(ordered) if p.skill == "Python")
        dl_idx = next(i for i, p in enumerate(ordered) if p.skill == "Deep Learning")
        assert python_idx < dl_idx

    def test_resource_properties(self):
        plan = find_resources("Python")
        for resource in plan.resources:
            assert resource.name != ""
            assert resource.url != ""
            assert resource.resource_type in ("course", "book", "tutorial", "documentation", "certification")


# ─── Integration Tests ────────────────────────────────────────

class TestUpskillIntegration:
    """Integration tests for the upskill pipeline."""

    def test_gap_analysis_to_roadmap(self, sample_profile):
        """Test gap analysis → roadmap building."""
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["Kubernetes", "Go", "React", "System Design"]

        # Step 1: Analyze gaps
        gaps = analyze_skill_gaps(profile_dict, requirements)
        assert len(gaps.gaps) > 0

        # Step 2: Build roadmap from gaps
        gap_dicts = [
            {"skill": g.skill, "time_estimate": g.time_estimate, "study_direction": g.study_direction}
            for g in gaps.gaps
        ]
        roadmap = build_roadmap(profile_dict, skill_gaps=gap_dicts)
        assert len(roadmap.milestones) > 0

        # Step 3: Find resources for top gap
        top_gap = gaps.gaps[0]
        plan = find_resources(top_gap.skill)
        assert plan.total_hours > 0

    def test_full_upskill_pipeline(self, sample_profile):
        """Test the complete upskill pipeline."""
        profile_dict = sample_profile.model_dump(mode="json")
        requirements = ["Kubernetes", "Go", "Rust", "Leadership"]

        # Analyze
        gaps = analyze_skill_gaps(profile_dict, requirements)
        assert len(gaps.recommendations) > 0

        # Roadmap
        roadmap = build_roadmap(profile_dict)
        assert roadmap.summary != ""

        # Resources for each gap
        for gap in gaps.gaps[:3]:
            plan = find_resources(gap.skill)
            assert isinstance(plan, LearningPlan)

        # Format roadmap
        formatted = format_roadmap(roadmap)
        assert "Career Roadmap" in formatted
