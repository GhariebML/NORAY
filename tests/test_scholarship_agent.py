"""
Tests for the NORAY Scholarship Agent module.

Tests scholarship search, eligibility scoring, SOP, motivation letter,
research proposal, and recommendation draft generation.
"""

import json
import tempfile
from pathlib import Path

import pytest

from noray.shared.models import (
    CareerProfile, Identity, Location, Language,
    Education, Experience, Skills, Certification,
    Project, Behavioral, CareerGoals, ScholarshipGoals,
    Publication,
)
from noray.scholarship_agent.scholarship_search import (
    Scholarship, ScholarshipSearchResult,
    search_scholarships, build_scholarship_queries,
    get_portal_info, get_matching_portals,
    _score_portals, _explain_portal_match,
    load_seen_scholarships, record_seen_scholarship,
    SCHOLARSHIP_PORTALS,
)
from noray.scholarship_agent.eligibility_scoring import (
    EligibilityResult, score_eligibility,
    generate_eligibility_report,
    _check_degree_prereq, _parse_gpa, _estimate_total_years,
)
from noray.scholarship_agent.sop_generator import (
    generate_sop, generate_sop_outline, SOPOutput,
)
from noray.scholarship_agent.motivation_letter import (
    generate_motivation_letter, generate_motivation_outline,
    MotivationLetterOutput,
)
from noray.scholarship_agent.research_proposal import (
    generate_research_proposal, generate_proposal_outline,
    ResearchProposalOutput,
)
from noray.scholarship_agent.recommendation_draft import (
    draft_recommendation, draft_multiple_recommendations,
    RecommendationDraft,
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
                thesis="Deep Learning for Arabic NLP",
                gpa="3.8",
            ),
        ],
        experience=[
            Experience(
                title="Data Scientist", company="Google", location="Cairo",
                start_date="2022", end_date="present",
                responsibilities=["Built ML pipelines", "Led team of 5"],
                achievements=["Reduced latency by 40%", "Improved accuracy from 72% to 89%"],
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
        publications=[
            Publication(
                authors=["Gharieb", "Awni"],
                title="Arabic NLP with Deep Learning",
                journal="ACL 2023",
                year=2023,
            ),
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


# ─── Scholarship Search Tests ────────────────────────────────

class TestScholarshipSearch:
    """Test scholarship search functionality."""

    def test_search_returns_result(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        result = search_scholarships(profile_dict)
        assert isinstance(result, ScholarshipSearchResult)
        assert result.search_date

    def test_search_with_filters(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        result = search_scholarships(profile_dict, target_degree="PhD", target_country="Germany")
        assert isinstance(result, ScholarshipSearchResult)

    def test_build_queries_basic(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        queries = build_scholarship_queries(profile_dict)
        assert len(queries) > 0
        assert any("Egypt" in q["query"] for q in queries)

    def test_build_queries_with_degree(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        queries = build_scholarship_queries(profile_dict, target_degree="PhD")
        assert any("PhD" in q["query"] for q in queries)

    def test_build_queries_with_research(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        queries = build_scholarship_queries(profile_dict, research_area="Machine Learning")
        assert any("Machine Learning" in q["query"] for q in queries)

    def test_portal_info(self):
        daad = get_portal_info("daad")
        assert daad is not None
        assert daad["name"] == "DAAD"
        assert "PhD" in daad["degree_levels"]

    def test_portal_info_invalid(self):
        assert get_portal_info("nonexistent_portal") is None

    def test_matching_portals(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        matches = get_matching_portals(profile_dict, target_degree="PhD")
        assert len(matches) > 0
        # Should include PhD portals
        portal_degrees = [m["degree_levels"] for m in matches]
        assert any("PhD" in deg for degs in portal_degrees for deg in degs)

    def test_score_portals(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        scholarships = _score_portals(profile_dict, "PhD", "")
        assert len(scholarships) > 0
        # All should have a fit score
        assert all(s.fit_score >= 0 for s in scholarships)
        # Should be sorted by score
        for i in range(len(scholarships) - 1):
            assert scholarships[i].fit_score >= scholarships[i + 1].fit_score

    def test_explain_portal_match(self):
        portal = {"name": "DAAD", "region": "Germany", "degree_levels": ["PhD"], "funding": "fully_funded"}
        explanation = _explain_portal_match(portal, "PhD", "Germany", "Egypt", [])
        assert "PhD" in explanation

    def test_record_seen_scholarship(self, tmp_path):
        import noray.scholarship_agent.scholarship_search as ss
        original = ss.SEEN_FILE
        ss.SEEN_FILE = tmp_path / "seen.json"

        sch = Scholarship(name="Test Scholarship", url="https://example.com/sch")
        record_seen_scholarship(sch)

        seen = load_seen_scholarships()
        assert "https://example.com/sch" in seen["seen"]
        assert seen["seen"]["https://example.com/sch"]["name"] == "Test Scholarship"

        ss.SEEN_FILE = original


# ─── Eligibility Scoring Tests ────────────────────────────────

class TestEligibilityScoring:
    """Test scholarship eligibility scoring."""

    def test_eligibility_basic(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        scholarship = {
            "degree_level": "PhD",
            "field_restrictions": ["Computer Science", "Engineering"],
            "required_languages": ["English"],
        }
        result = score_eligibility(profile_dict, scholarship)
        assert result.overall_score >= 60
        assert result.is_eligible

    def test_eligibility_with_nationality(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        scholarship = {
            "eligible_nationalities": ["Egypt", "Jordan", "Tunisia"],
            "degree_level": "PhD",
            "required_languages": ["English"],
        }
        result = score_eligibility(profile_dict, scholarship)
        assert result.is_eligible
        assert any("Egypt" in c for c in result.criteria_met)

    def test_eligibility_ineligible_nationality(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        scholarship = {
            "eligible_nationalities": ["USA", "Canada"],
            "degree_level": "PhD",
            "required_languages": ["English"],
        }
        result = score_eligibility(profile_dict, scholarship)
        assert any("Egypt" in c for c in result.criteria_not_met)

    def test_eligibility_field_match(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        scholarship = {
            "field_restrictions": ["Computer Science"],
            "degree_level": "MSc",
        }
        result = score_eligibility(profile_dict, scholarship)
        assert any("Computer Science" in c for c in result.criteria_met)

    def test_eligibility_language_check(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")

        # When one lang is met and one is missing, it goes to partial
        scholarship = {"required_languages": ["English", "German"]}
        result = score_eligibility(profile_dict, scholarship)
        all_criteria = result.criteria_met + result.criteria_partial
        assert any("English" in c for c in all_criteria), f"English not found in met or partial: {all_criteria}"
        assert any("German" in c for c in all_criteria), f"German not found in met or partial: {all_criteria}"

        # When all required languages are missing, they go to not_met
        scholarship_all_missing = {"required_languages": ["German", "French"]}
        result2 = score_eligibility(profile_dict, scholarship_all_missing)
        assert any("German" in c for c in result2.criteria_not_met), f"German not in not_met: {result2.criteria_not_met}"

    def test_eligibility_publications(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        scholarship = {"requires_publications": True}
        result = score_eligibility(profile_dict, scholarship)
        assert any("publication" in c.lower() for c in result.criteria_met)

    def test_eligibility_no_publications(self):
        profile = CareerProfile(
            education=[Education(degree="BSc", field="CS")],
        ).model_dump(mode="json")
        scholarship = {"requires_publications": True}
        result = score_eligibility(profile, scholarship)
        assert any("publication" in c.lower() for c in result.criteria_partial)

    def test_eligibility_report(self):
        result = EligibilityResult(
            overall_score=75,
            is_eligible=True,
            criteria_met=["Nationality eligible", "Field matches"],
            criteria_partial=["GPA not available"],
            recommendations=["Obtain language certification"],
        )
        report = generate_eligibility_report(result, "DAAD")
        assert "75/100" in report
        assert "DAAD" in report
        assert "Nationality eligible" in report

    def test_check_degree_prereq(self):
        education = [{"degree": "BSc", "field": "CS"}]
        assert _check_degree_prereq(education, "MSc") is True
        assert _check_degree_prereq(education, "PhD") is False

    def test_parse_gpa(self):
        assert _parse_gpa("3.8") == 3.8
        assert _parse_gpa("3.8/4.0") == 3.8
        assert _parse_gpa("85%") is not None  # Converts from percentage

    def test_estimate_total_years(self):
        experience = [
            {"start_date": "2020", "end_date": "2022"},
            {"start_date": "2022", "end_date": "present"},
        ]
        years = _estimate_total_years(experience)
        assert years >= 4.0  # 2020-2026 = ~6 years

    def test_eligibility_research_interests(self, sample_profile):
        profile_dict = sample_profile.model_dump(mode="json")
        scholarship = {"research_areas": ["Machine Learning", "Computer Vision"]}
        result = score_eligibility(profile_dict, scholarship)
        assert any("Machine Learning" in c for c in result.criteria_met)


# ─── SOP Generator Tests ─────────────────────────────────────

class TestSOPGenerator:
    """Test SOP generation."""

    def test_generate_sop(self, sample_profile):
        output = generate_sop(
            sample_profile,
            "DAAD PhD program in Computer Science",
            ["Machine Learning", "Healthcare AI"],
        )
        assert output.success
        assert output.word_count > 200
        assert len(output.sections) >= 4
        assert "Machine Learning" in output.content

    def test_generate_sop_sections(self, sample_profile):
        output = generate_sop(sample_profile, "PhD program", ["NLP"])
        assert "opening" in output.sections
        assert "academic_background" in output.sections
        assert "research_experience" in output.sections
        assert "why_this_program" in output.sections
        assert "future_goals" in output.sections

    def test_generate_sop_references_education(self, sample_profile):
        output = generate_sop(sample_profile, "PhD program", ["ML"])
        assert "Cairo University" in output.content
        assert "Computer Science" in output.content

    def test_generate_sop_references_publications(self, sample_profile):
        output = generate_sop(sample_profile, "PhD program", ["ML"])
        assert "publication" in output.content.lower()

    def test_generate_sop_outline(self, sample_profile):
        outline = generate_sop_outline(sample_profile, "PhD program", ["ML"])
        assert isinstance(outline, dict)
        assert "opening" in outline
        assert len(outline) >= 4

    def test_generate_sop_empty_profile(self):
        profile = CareerProfile()
        output = generate_sop(profile, "PhD program", ["ML"])
        assert output.success
        assert output.word_count > 100


# ─── Motivation Letter Tests ─────────────────────────────────

class TestMotivationLetter:
    """Test motivation letter generation."""

    def test_generate_motivation(self, sample_profile):
        output = generate_motivation_letter(
            sample_profile,
            "Erasmus Mundus MSc Data Science",
            target_degree="MSc",
            target_country="EU",
        )
        assert output.success
        assert output.word_count > 150
        assert len(output.sections) >= 4

    def test_generate_motivation_sections(self, sample_profile):
        output = generate_motivation_letter(sample_profile, "Erasmus Mundus")
        assert "motivation" in output.sections
        assert "background" in output.sections
        assert "why_program" in output.sections
        assert "contribution" in output.sections
        assert "closing" in output.sections

    def test_generate_motivation_references_skills(self, sample_profile):
        output = generate_motivation_letter(sample_profile, "Erasmus Mundus")
        assert any(s in output.content for s in ["Python", "Machine Learning", "Data Science"])

    def test_generate_motivation_references_country(self, sample_profile):
        output = generate_motivation_letter(
            sample_profile, "Erasmus Mundus", target_country="Germany"
        )
        assert "Germany" in output.content

    def test_generate_motivation_outline(self, sample_profile):
        outline = generate_motivation_outline(sample_profile, "Erasmus Mundus")
        assert isinstance(outline, dict)
        assert "motivation" in outline

    def test_generate_motivation_empty_profile(self):
        profile = CareerProfile()
        output = generate_motivation_letter(profile, "Test Program")
        assert output.success


# ─── Research Proposal Tests ──────────────────────────────────

class TestResearchProposal:
    """Test research proposal generation."""

    def test_generate_proposal(self, sample_profile):
        output = generate_research_proposal(
            sample_profile,
            "DAAD PhD program",
            ["Machine Learning", "Healthcare AI"],
        )
        assert output.success
        assert output.word_count > 500
        assert len(output.sections) >= 7

    def test_generate_proposal_title(self, sample_profile):
        output = generate_research_proposal(
            sample_profile, "PhD", ["Machine Learning", "NLP"]
        )
        assert output.title
        assert "Machine Learning" in output.title

    def test_generate_proposal_sections(self, sample_profile):
        output = generate_research_proposal(
            sample_profile, "PhD", ["Machine Learning"]
        )
        assert "title" in output.sections
        assert "introduction" in output.sections
        assert "literature_review" in output.sections
        assert "methodology" in output.sections
        assert "timeline" in output.sections
        assert "expected_outcomes" in output.sections
        assert "feasibility" in output.sections
        assert "references" in output.sections

    def test_generate_proposal_references_profile(self, sample_profile):
        output = generate_research_proposal(
            sample_profile, "PhD", ["ML"]
        )
        assert "Google" in output.content or "Cairo" in output.content

    def test_generate_proposal_has_references(self, sample_profile):
        output = generate_research_proposal(
            sample_profile, "PhD", ["Machine Learning"]
        )
        assert len(output.references) >= 3

    def test_generate_proposal_outline(self, sample_profile):
        outline = generate_proposal_outline(sample_profile, ["ML"])
        assert isinstance(outline, dict)
        assert "title" in outline
        assert "methodology" in outline


# ─── Recommendation Draft Tests ───────────────────────────────

class TestRecommendationDraft:
    """Test recommendation letter drafting."""

    def test_draft_academic(self, sample_profile):
        draft = draft_recommendation(
            sample_profile,
            referee_name="Prof. Ahmed",
            relationship="thesis supervisor",
            tone="academic_supervisor",
        )
        assert draft.success
        assert "Prof. Ahmed" in draft.content
        assert "Gharieb" in draft.content or "[Candidate]" in draft.content

    def test_draft_employer(self, sample_profile):
        draft = draft_recommendation(
            sample_profile,
            referee_name="Dr. Sarah",
            relationship="team lead at Google",
            tone="employer",
        )
        assert draft.success
        assert "Google" in draft.content

    def test_draft_colleague(self, sample_profile):
        draft = draft_recommendation(
            sample_profile,
            referee_name="Awni",
            relationship="colleague",
            tone="colleague",
        )
        assert draft.success
        assert "Awni" in draft.content

    def test_draft_has_fill_in_markers(self, sample_profile):
        draft = draft_recommendation(
            sample_profile,
            referee_name="Prof. Ahmed",
            relationship="supervisor",
        )
        assert len(draft.fill_in_markers) >= 3

    def test_draft_references_publications(self, sample_profile):
        draft = draft_recommendation(
            sample_profile,
            referee_name="Prof. Ahmed",
            relationship="supervisor",
            tone="academic_supervisor",
        )
        assert "publication" in draft.content.lower()

    def test_draft_multiple(self, sample_profile):
        referees = [
            {"name": "Prof. Ahmed", "relationship": "supervisor", "tone": "academic_supervisor"},
            {"name": "Dr. Sarah", "relationship": "team lead", "tone": "employer"},
        ]
        drafts = draft_multiple_recommendations(sample_profile, referees)
        assert len(drafts) == 2
        assert drafts[0].referee_name == "Prof. Ahmed"
        assert drafts[1].referee_name == "Dr. Sarah"

    def test_draft_with_target_degree(self, sample_profile):
        draft = draft_recommendation(
            sample_profile,
            referee_name="Prof. Ahmed",
            relationship="supervisor",
            target_degree="PhD",
        )
        assert "PhD" in draft.content


# ─── Dashboard Scholarships Tests ─────────────────────────────

class TestDashboardScholarships:
    """Test scholarship application tracker."""

    def test_load_empty_tracker(self):
        from noray.dashboard.scholarships import load_applications, TRACKER_PATH
        import noray.dashboard.scholarships as sch_module

        original = sch_module.TRACKER_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            sch_module.TRACKER_PATH = Path(tmpdir) / "test_tracker.json"
            apps = load_applications()
            assert len(apps) == 0
        sch_module.TRACKER_PATH = original

    def test_add_and_load(self):
        from noray.dashboard.scholarships import (
            ScholarshipApplication, add_application, load_applications, TRACKER_PATH,
        )
        import noray.dashboard.scholarships as sch_module

        original = sch_module.TRACKER_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            sch_module.TRACKER_PATH = Path(tmpdir) / "test_tracker.json"

            app = ScholarshipApplication(
                name="DAAD", provider="DAAD", country="Germany",
                status="preparing", eligibility_score=85,
                deadline="2026-10-15",
            )
            saved = add_application(app)
            assert saved.id.startswith("sch_")

            loaded = load_applications()
            assert len(loaded) == 1
            assert loaded[0].name == "DAAD"

        sch_module.TRACKER_PATH = original

    def test_update_application(self):
        from noray.dashboard.scholarships import (
            ScholarshipApplication, add_application, update_application, TRACKER_PATH,
        )
        import noray.dashboard.scholarships as sch_module

        original = sch_module.TRACKER_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            sch_module.TRACKER_PATH = Path(tmpdir) / "test_tracker.json"

            app = add_application(ScholarshipApplication(name="DAAD", status="preparing"))
            updated = update_application(app.id, {"status": "submitted"})

            assert updated is not None
            assert updated.status == "submitted"

        sch_module.TRACKER_PATH = original

    def test_get_stats(self):
        from noray.dashboard.scholarships import (
            ScholarshipApplication, add_application, get_application_stats, TRACKER_PATH,
        )
        import noray.dashboard.scholarships as sch_module

        original = sch_module.TRACKER_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            sch_module.TRACKER_PATH = Path(tmpdir) / "test_tracker.json"

            add_application(ScholarshipApplication(name="DAAD", status="preparing", deadline="2026-10-15"))
            add_application(ScholarshipApplication(name="Erasmus", status="submitted"))

            stats = get_application_stats()
            assert stats["total"] == 2
            assert stats["by_status"]["preparing"] == 1

        sch_module.TRACKER_PATH = original

    def test_get_upcoming_deadlines(self):
        from noray.dashboard.scholarships import (
            ScholarshipApplication, add_application, get_upcoming_deadlines, TRACKER_PATH,
        )
        import noray.dashboard.scholarships as sch_module

        original = sch_module.TRACKER_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            sch_module.TRACKER_PATH = Path(tmpdir) / "test_tracker.json"

            add_application(ScholarshipApplication(name="Soon", status="preparing", deadline="2026-06-10"))
            add_application(ScholarshipApplication(name="Later", status="preparing", deadline="2026-12-31"))

            upcoming = get_upcoming_deadlines(30)
            # Depends on current date; just verify it runs
            assert isinstance(upcoming, list)

        sch_module.TRACKER_PATH = original


# ─── Integration Tests ────────────────────────────────────────

class TestScholarshipIntegration:
    """Integration tests for the scholarship pipeline."""

    def test_full_pipeline(self, sample_profile):
        """Test search → eligibility → SOP → research proposal."""
        profile_dict = sample_profile.model_dump(mode="json")

        # Step 1: Search
        result = search_scholarships(profile_dict, target_degree="PhD")
        assert len(result.scholarships) > 0

        # Step 2: Score eligibility for top match
        top = result.scholarships[0]
        eligibility = score_eligibility(profile_dict, {"degree_level": "PhD", "required_languages": ["English"]})
        assert eligibility.overall_score >= 50

        # Step 3: Generate SOP
        sop = generate_sop(sample_profile, top.name, ["Machine Learning"])
        assert sop.success
        assert sop.word_count > 200

        # Step 4: Generate research proposal
        proposal = generate_research_proposal(sample_profile, top.name, ["ML"])
        assert proposal.success
        assert proposal.word_count > 500

    def test_eligibility_to_report(self, sample_profile):
        """Test eligibility scoring → report generation."""
        profile_dict = sample_profile.model_dump(mode="json")
        scholarship = {
            "degree_level": "PhD",
            "field_restrictions": ["Computer Science"],
            "required_languages": ["English"],
            "requires_publications": True,
        }
        result = score_eligibility(profile_dict, scholarship)
        report = generate_eligibility_report(result, "DAAD")

        assert "DAAD" in report
        assert str(result.overall_score) in report
        assert len(report) > 200
