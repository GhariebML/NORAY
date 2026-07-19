"""
NORAY — Diagnostics, Tracing & Exceptions Integration Tests

Verifies health check endpoints, tracing middleware context, and custom
stage exceptions.
"""

import pytest
from fastapi.testclient import TestClient

from noray.api.app import app
from noray.api.errors import WorkspaceStageError

client = TestClient(app)

def test_health_aggregated_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "details" in data
    assert "database" in data["details"]
    assert "vector_store" in data["details"]

def test_health_specific_endpoints():
    endpoints = ["/api/health/database", "/api/health/vector", "/api/health/graph", "/api/health/llm", "/api/health/mcp"]
    for path in endpoints:
        res = client.get(path)
        assert res.status_code == 200
        assert "status" in res.json()

def test_request_tracing_middleware():
    # Make request and verify trace ID header is injected in response
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "X-Trace-ID" in response.headers
    assert len(response.headers["X-Trace-ID"]) > 10

def test_custom_stage_error_serializes_cleanly():
    # Trigger a request that raises WorkspaceStageError manually in a mock view
    # For testing, we can directly assert the dictionary format
    err = WorkspaceStageError(
        stage="Planner",
        error="DAG decomposition error",
        details="Circular dependency detected",
        trace_id="test-trace-id-123"
    )
    d = err.to_dict()
    assert d["stage"] == "Planner"
    assert d["error"] == "DAG decomposition error"
    assert d["details"] == "Circular dependency detected"
    assert d["trace_id"] == "test-trace-id-123"
