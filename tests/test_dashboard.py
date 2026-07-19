"""
Tests for the NORAY Dashboard module.

Tests unified application tracker and analytics.
"""

import tempfile
from pathlib import Path

import pytest

from noray.shared.models import (
    CareerProfile, Identity, Location, Skills,
    Education, Experience, Certification,
)
from noray.dashboard.jobs import (
    JobApplication, add_application as add_job, load_applications as load_jobs,
)
from noray.dashboard.scholarships import (
    ScholarshipApplication, add_application as add_sch, load_applications as load_scholarships,
)
from noray.dashboard.applications import (
    ApplicationSummary, get_all_applications, get_filtered_applications,
    get_pipeline_stats, get_upcoming_actions,
    _infer_priority, _days_since,
)
from noray.dashboard.analytics import (
    get_analytics_summary, get_dashboard_summary, format_analytics,
    _calculate_response_rate, _calculate_interview_rate,
    _calculate_award_rate, _generate_insights, _build_monthly_activity,
)


# ─── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def sample_jobs():
    """Create sample job applications for testing."""
    import noray.dashboard.jobs as jmod
    original = jmod.TRACKER_PATH
    with tempfile.TemporaryDirectory() as tmpdir:
        jmod.TRACKER_PATH = Path(tmpdir) / "jobs.json"
        add_job(JobApplication(
            company="Google", role="ML Engineer", status="applied",
            applied_date="2026-05-01",
        ))
        add_job(JobApplication(
            company="Meta", role="Data Scientist", status="interview",
            applied_date="2026-04-15",
        ))
        add_job(JobApplication(
            company="OpenAI", role="Research Engineer", status="offer",
            applied_date="2026-04-01",
        ))
        yield
    jmod.TRACKER_PATH = original


@pytest.fixture
def sample_scholarships():
    """Create sample scholarship applications for testing."""
    import noray.dashboard.scholarships as smod
    original = smod.TRACKER_PATH
    with tempfile.TemporaryDirectory() as tmpdir:
        smod.TRACKER_PATH = Path(tmpdir) / "sch.json"
        add_sch(ScholarshipApplication(
            name="DAAD", status="submitted", degree_level="PhD",
            applied_date="2026-04-10",
        ))
        add_sch(ScholarshipApplication(
            name="Erasmus Mundus", status="awarded", degree_level="MSc",
            applied_date="2026-03-01",
        ))
        yield
    smod.TRACKER_PATH = original


# ─── Unified Tracker Tests ────────────────────────────────────

class TestUnifiedTracker:
    """Test unified application tracking."""

    def test_get_all_applications(self, sample_jobs, sample_scholarships):
        apps = get_all_applications()
        assert len(apps) == 5
        types = {a.type for a in apps}
        assert "job" in types
        assert "scholarship" in types

    def test_get_filtered_by_type(self, sample_jobs, sample_scholarships):
        jobs = get_filtered_applications(type_filter="job")
        assert len(jobs) == 3
        assert all(a.type == "job" for a in jobs)

        schs = get_filtered_applications(type_filter="scholarship")
        assert len(schs) == 2
        assert all(a.type == "scholarship" for a in schs)

    def test_get_filtered_by_status(self, sample_jobs, sample_scholarships):
        applied = get_filtered_applications(status_filter="applied")
        assert len(applied) == 1
        assert applied[0].name == "Google"

    def test_pipeline_stats(self, sample_jobs, sample_scholarships):
        stats = get_pipeline_stats()
        assert stats["combined_total"] == 5
        assert stats["jobs"]["total"] == 3
        assert stats["scholarships"]["total"] == 2
        assert stats["jobs"]["pipeline"] is not None
        assert stats["scholarships"]["pipeline"] is not None

    def test_upcoming_actions_empty(self, sample_jobs, sample_scholarships):
        actions = get_upcoming_actions(days=1)
        # No next_step_date or deadlines set, so should be empty
        assert isinstance(actions, list)

    def test_infer_priority(self):
        from noray.dashboard.jobs import JobApplication
        assert _infer_priority(JobApplication(status="interview")) == "high"
        assert _infer_priority(JobApplication(status="applied")) == "medium"
        assert _infer_priority(JobApplication(status="discovered")) == "low"

    def test_days_since(self):
        assert _days_since(None) == 0
        assert _days_since("") == 0
        assert _days_since("invalid") == 0


# ─── Analytics Tests ──────────────────────────────────────────

class TestAnalytics:
    """Test analytics module."""

    def test_analytics_summary(self, sample_jobs, sample_scholarships):
        summary = get_analytics_summary()
        assert "jobs" in summary
        assert "scholarships" in summary
        assert "timeline" in summary
        assert "insights" in summary
        assert "monthly_activity" in summary
        assert "conversion_funnel" in summary

    def test_job_analytics(self, sample_jobs, sample_scholarships):
        summary = get_analytics_summary()
        j = summary["jobs"]
        assert j["total_tracked"] == 3
        assert j["total_applied"] == 3
        assert "response_rate" in j
        assert "interview_rate" in j
        assert "offer_rate" in j
        assert "by_status" in j

    def test_scholarship_analytics(self, sample_jobs, sample_scholarships):
        summary = get_analytics_summary()
        s = summary["scholarships"]
        assert s["total_tracked"] == 2
        assert "success_rate" in s
        assert "upcoming_deadlines" in s

    def test_dashboard_summary(self, sample_jobs, sample_scholarships):
        dash = get_dashboard_summary()
        assert "total_applications" in dash
        assert "active_applications" in dash
        assert "top_insights" in dash

    def test_format_analytics(self, sample_jobs, sample_scholarships):
        summary = get_analytics_summary()
        formatted = format_analytics(summary)
        assert "Analytics Dashboard" in formatted
        assert "Job Applications" in formatted
        assert "Scholarship Applications" in formatted

    def test_calculate_response_rate(self):
        from noray.dashboard.jobs import JobApplication
        jobs = [
            JobApplication(status="applied"),
            JobApplication(status="interview"),
            JobApplication(status="offer"),
        ]
        rate = _calculate_response_rate(jobs)
        assert rate == pytest.approx(2 / 3, abs=0.01)

    def test_calculate_interview_rate(self):
        from noray.dashboard.jobs import JobApplication
        jobs = [
            JobApplication(status="applied"),
            JobApplication(status="applied"),
            JobApplication(status="interview"),
        ]
        rate = _calculate_interview_rate(jobs)
        assert rate == pytest.approx(1 / 3, abs=0.01)

    def test_calculate_award_rate(self):
        from noray.dashboard.scholarships import ScholarshipApplication
        schs = [
            ScholarshipApplication(status="submitted"),
            ScholarshipApplication(status="awarded"),
        ]
        rate = _calculate_award_rate(schs)
        assert rate == pytest.approx(0.5, abs=0.01)

    def test_generate_insights(self):
        from noray.dashboard.jobs import JobApplication
        jobs = [JobApplication(status="applied", applied_date="2026-05-01")]
        insights = _generate_insights(jobs, [], 0.0, 0.0)
        assert len(insights) > 0

    def test_monthly_activity(self):
        from noray.dashboard.jobs import JobApplication
        jobs = [JobApplication(applied_date="2026-05-01")]
        monthly = _build_monthly_activity(jobs, [])
        assert "2026-05" in monthly

    def test_empty_analytics(self):
        """Test analytics with no data still works."""
        import noray.dashboard.jobs as jmod
        import noray.dashboard.scholarships as smod
        j_original = jmod.TRACKER_PATH
        s_original = smod.TRACKER_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            jmod.TRACKER_PATH = Path(tmpdir) / "empty_jobs.json"
            smod.TRACKER_PATH = Path(tmpdir) / "empty_sch.json"
            summary = get_analytics_summary()
            assert summary["jobs"]["total_tracked"] == 0
            assert summary["scholarships"]["total_tracked"] == 0
        jmod.TRACKER_PATH = j_original
        smod.TRACKER_PATH = s_original
