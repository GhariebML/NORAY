"""
NORAY — Centralized AI Gateway Tests

Verifies ModelRegistry metadata mapping, ModelRouter task requirements scoring,
AIGateway client adapters, metric tracking, and graceful recovery execution.
"""

import pytest
import os
from noray.gateway.base import RouteRequirements, LLMConfig
from noray.gateway.registry import ModelRegistry, ModelMetadata
from noray.gateway.router import ModelRouter
from noray.gateway.facade import AIGateway


def test_model_registry_metadata():
    reg = ModelRegistry()
    meta = reg.get("gpt-4o-mini")
    assert meta is not None
    assert meta.provider == "openai"
    assert meta.supports_json is True
    assert meta.supports_tools is True
    assert meta.input_cost_per_1k > 0.0


def test_model_router_offline_preference(monkeypatch):
    monkeypatch.setenv("ALLOW_OFFLINE", "false")
    reg = ModelRegistry()
    for meta in reg.models.values():
        meta.is_available = True
    router = ModelRouter(reg)
    
    # Provider states (mocked healthy)
    states = {"local": True, "openai": True, "anthropic": True, "gemini": True}

    # Ask for local preferred
    req = RouteRequirements(preferred_provider="local")
    model, provider = router.route(req, states)
    assert provider == "local"

    # Ask for cloud reasoning
    req_reasoning = RouteRequirements(require_reasoning=True, preferred_provider="anthropic")
    model, provider = router.route(req_reasoning, states)
    assert provider == "anthropic"

def test_model_router_fallback(monkeypatch):
    monkeypatch.setenv("ALLOW_OFFLINE", "false")
    reg = ModelRegistry()
    for meta in reg.models.values():
        meta.is_available = True
    router = ModelRouter(reg)
    
    # Local is down, cloud is available
    states = {"local": False, "openai": True, "anthropic": True, "gemini": True}
    req = RouteRequirements(preferred_provider="local")
    model, provider = router.route(req, states)
    
    # Must fallback to cloud Gemini (priority 1 cloud provider) since local is offline
    assert provider == "gemini"


def test_gateway_facade_and_metrics_accumulation():
    from unittest.mock import patch
    from noray.gateway.base import LLMResponse
    
    # Set mock environment config variables
    os.environ["ALLOW_OFFLINE"] = "true"
    
    mock_res = LLMResponse(
        content="Hello [MOCK] response",
        model="llama3.1:8b",
        provider="local",
        input_tokens=10,
        output_tokens=10,
        estimated_cost=0.0,
        latency_ms=12.3
    )
    
    with patch("noray.gateway.providers.local.LocalProvider.generate", return_value=mock_res):
        gateway = AIGateway()
        res = gateway.call_llm(
            prompt="test prompt",
            system_prompt="system",
            temperature=0.7,
            requirements=RouteRequirements(preferred_provider="local")
        )
        
        assert res is not None
        assert res.provider == "local"
        assert "MOCK" in res.content
        
        # Metrics should be updated
        assert gateway.metrics["total_requests"] >= 1
        assert gateway.metrics["total_latency_ms"] >= 0.0
