"""
NORAY — Workspace API Integration Tests

Verifies /chat, /search, and /research endpoints are fully functional,
yield correct JSON formats, and return the new explainability structures.
"""

import pytest
from fastapi.testclient import TestClient

from noray.api.app import app

client = TestClient(app)

def test_workspace_chat_endpoint():
    payload = {
        "query": "Find scholarships for master in Germany",
        "temperature": 0.2
    }
    response = client.post("/api/workspace/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "response" in data
    assert "intent" in data
    assert "citations" in data
    assert "explainability" in data
    assert "confidence_score" in data["explainability"]
    assert "retrieved_nodes" in data["explainability"]

def test_workspace_search_endpoint():
    payload = {
        "query": "Fulbright",
        "limit": 3
    }
    response = client.post("/api/workspace/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "results" in data
    assert isinstance(data["results"], list)

def test_workspace_research_endpoint():
    payload = {
        "objective": "Research DAAD EPOS eligibility rules",
        "max_depth": 1
    }
    response = client.post("/api/workspace/research", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "report" in data
    assert "status" in data
    assert "citations" in data
    assert "explainability" in data
