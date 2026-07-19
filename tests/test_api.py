"""
Tests for the NORAY REST API.

Tests all API endpoints using FastAPI's TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from noray.api.app import app

client = TestClient(app)


# ─── Root & Health ────────────────────────────────────────────

class TestRoot:
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NORAY"
        assert data["version"] == "0.1.0"

    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ─── Profile ──────────────────────────────────────────────────

class TestProfileAPI:
    def test_get_profile(self):
        response = client.get("/api/profile")
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        assert "meta" in data

    def test_update_profile(self):
        response = client.put("/api/profile", json={
            "updates": {"goals": {"target_roles": ["ML Engineer"]}},
            "source": "api_test",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "updated"


# ─── Jobs ─────────────────────────────────────────────────────

class TestJobsAPI:
    def test_search_jobs(self):
        response = client.post("/api/jobs/search", json={"focus_area": "ML", "broad": False})
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total_found" in data

    def test_evaluate_job(self):
        response = client.post("/api/jobs/evaluate", json={
            "job_text": "Python, Machine Learning, TensorFlow required",
        })
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "matched_keywords" in data

    def test_evaluate_no_text(self):
        response = client.post("/api/jobs/evaluate", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    def test_apply_job(self):
        response = client.post("/api/jobs/apply", json={
            "company": "TestCorp",
            "role": "ML Engineer",
            "job_text": "Python, ML, TensorFlow",
            "generate_cv": True,
            "generate_cover_letter": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generated"
        assert "application_id" in data
        assert "results" in data

    def test_tracker(self):
        response = client.get("/api/jobs/tracker")
        assert response.status_code == 200
        data = response.json()
        assert "applications" in data
        assert "stats" in data


# ─── Scholarships ─────────────────────────────────────────────

class TestScholarshipsAPI:
    def test_search_scholarships(self):
        response = client.post("/api/scholarships/search", json={
            "target_degree": "PhD",
            "target_country": "Germany",
        })
        assert response.status_code == 200
        data = response.json()
        assert "scholarships" in data
        assert "total_found" in data

    def test_apply_scholarship(self):
        response = client.post("/api/scholarships/apply", json={
            "scholarship_name": "DAAD PhD",
            "scholarship_info": "PhD in Computer Science at German university",
            "generate_sop": True,
            "generate_motivation": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generated"
        assert "sop" in data["results"]
        assert "motivation_letter" in data["results"]

    def test_tracker(self):
        response = client.get("/api/scholarships/tracker")
        assert response.status_code == 200
        data = response.json()
        assert "applications" in data

    def test_deadlines(self):
        response = client.get("/api/scholarships/deadlines?days=30")
        assert response.status_code == 200


# ─── SOP & Documents ──────────────────────────────────────────

class TestDocumentsAPI:
    def test_generate_sop(self):
        response = client.post("/api/sop/sop", json={
            "scholarship_info": "DAAD PhD program",
            "research_interests": ["Machine Learning"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generated"
        assert "content" in data
        assert "word_count" in data
        assert data["word_count"] > 100

    def test_generate_motivation(self):
        response = client.post("/api/sop/motivation", json={
            "scholarship_info": "Erasmus Mundus MSc",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generated"
        assert data["word_count"] > 50

    def test_generate_research_proposal(self):
        response = client.post("/api/sop/research", json={
            "scholarship_info": "PhD in CS",
            "research_interests": ["Machine Learning", "NLP"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generated"
        assert "title" in data
        assert data["word_count"] > 200


# ─── Applications ─────────────────────────────────────────────

class TestApplicationsAPI:
    def test_get_applications(self):
        response = client.get("/api/applications")
        assert response.status_code == 200
        data = response.json()
        assert "applications" in data
        assert "stats" in data

    def test_get_analytics(self):
        response = client.get("/api/applications/analytics")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "scholarships" in data
        assert "insights" in data
        assert "conversion_funnel" in data


# ─── Upskill ──────────────────────────────────────────────────

class TestUpskillAPI:
    def test_analyze_gaps(self):
        response = client.post("/api/upskill/analyze", json={
            "job_text": "Python, Kubernetes, Go, Rust required",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "analyzed"
        assert "gaps" in data
        assert "recommendations" in data
        assert "report" in data

    def test_generate_roadmap(self):
        response = client.post("/api/upskill/roadmap", json={
            "timeline_months": 12,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generated"
        assert "career_path" in data
        assert "milestones" in data
        assert "phases" in data
        assert "formatted" in data
        assert len(data["milestones"]) > 0

    def test_find_resources(self):
        response = client.post("/api/upskill/resources?skill=Python")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "found"
        assert data["skill"] == "Python"
        assert len(data["resources"]) > 0

    def test_analyze_aggregate_mode(self):
        response = client.post("/api/upskill/analyze", json={
            "mode": "aggregate",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "analyzed"
