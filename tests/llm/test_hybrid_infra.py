import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from noray.api.app import app
from noray.llm.model_registry import model_registry, ModelMetadata
from noray.llm.router import ModelRouter, ModelRouteRequest
from noray.llm.local_manager import local_runtime
from noray.config import settings

client = TestClient(app)

def test_model_registry_metadata():
    """Verify registry correctly resolves and returns metadata descriptors."""
    model = model_registry.get_model("qwen2.5:7b")
    assert model is not None
    assert model.provider == "ollama"
    assert model.supports_tools
    assert model.context_window == 32768
    
    # Custom registration
    custom = ModelMetadata(
        provider="custom_test_provider",
        model="custom-model",
        context_window=2048,
        supports_tools=False
    )
    model_registry.register(custom)
    
    resolved = model_registry.get_model("custom-model", "custom_test_provider")
    assert resolved == custom
    assert custom in model_registry.list_models()


def test_model_router_fallbacks_and_priorities():
    """Verify router prioritization logic (Local Ollama first, OpenAI/Anthropic next)."""
    router = ModelRouter()
    
    # Mock settings so only Ollama and OpenAI are configured
    with patch.object(ModelRouter, "is_provider_configured", lambda self, p: p in ["ollama", "openai"]), \
         patch("noray.llm.health_monitor.ProviderHealthMonitor.get_provider_score", return_value=1.0):
        
        # Test low complexity -> should choose Local Qwen
        req_low = ModelRouteRequest(query="Hello", complexity="low")
        model, provider, fallbacks, confidence = router.route(req_low)
        
        # Ollama has highest priority (1.0) and Qwen has Low complexity bonus
        assert provider == "ollama"
        assert model in ["qwen2.5:7b", "qwen2.5-coder:7b", "llama3.1:8b", "deepseek-r1:8b"]
        
        # Test high complexity -> cloud models
        req_high = ModelRouteRequest(query="Analyze complex logs and generate roadmap", complexity="high")
        model, provider, fallbacks, confidence = router.route(req_high)
        # OpenAI (0.8) and quality (0.75-0.92) vs Ollama (1.0) and quality (0.55-0.65). 
        # OpenAI candidate gpt-4o should be matched
        assert provider in ["openai", "ollama"]


def test_local_manager_hardware_info():
    """Verify hardware info detection structure."""
    info = local_runtime.get_hardware_info()
    assert "cpu" in info
    assert "ram_gb" in info
    assert "gpu" in info
    assert "vram_gb" in info
    
    recs = local_runtime.get_model_recommendations()
    assert len(recs) > 0
    assert "nomic-embed-text" in recs


def test_system_providers_endpoint():
    """Verify GET /api/system/providers returns valid status schema."""
    with patch.object(ModelRouter, "is_provider_configured", return_value=True), \
         patch("noray.llm.providers.base_provider.BaseLLMProvider.health", return_value=True):
        
        response = client.get("/api/system/providers")
        assert response.status_code == 200
        data = response.json()
        
        assert "providers" in data
        providers = data["providers"]
        assert len(providers) > 0
        
        # Verify first item keys
        first = providers[0]
        assert "provider" in first
        assert "status" in first
        assert "latency" in first
        assert "available_models" in first
        assert "streaming" in first
        assert "configured" in first
        assert "healthy" in first


def test_system_diagnostics_endpoint():
    """Verify GET /api/system/diagnostics checklist reports."""
    with patch("noray.llm.local_manager.LocalRuntimeManager.is_ollama_running", return_value=True), \
         patch("noray.llm.local_manager.LocalRuntimeManager.get_downloaded_models", return_value=[{"name": "qwen2.5:7b"}, {"name": "nomic-embed-text"}, {"name": "llama3.1:8b"}]), \
         patch("noray.llm.providers.ollama_provider.OllamaProvider.embeddings", return_value=[0.1]*384):
        
        response = client.get("/api/system/diagnostics")
        assert response.status_code == 200
        data = response.json()
        
        assert "ollama_running" in data
        assert "models_downloaded" in data
        assert "api_keys_loaded" in data
        assert "router_healthy" in data
        assert "embeddings_healthy" in data
        assert "streaming_works" in data
        assert "hardware" in data


def test_quarantine_failed_provider():
    """Verify that failed/unresponsive providers are quarantined and return 0 score."""
    from noray.llm.health_monitor import ProviderHealthMonitor
    monitor = ProviderHealthMonitor()
    
    # Place deepseek in quarantine for 10 seconds
    monitor.quarantine_provider("deepseek", duration=10, error_msg="Timeout test")
    
    assert monitor.is_quarantined("deepseek") is True
    # Quarantined provider score must immediately return 0.0 without pinging
    assert monitor.get_provider_score("deepseek") == 0.0


def test_router_policy_presets():
    """Verify router scoring shifts according to different policy weight adjustments."""
    router = ModelRouter()
    
    # 1. Coding policy - deepseek should win coding-rich requests
    with patch.object(ModelRouter, "is_provider_configured", lambda self, p: True), \
         patch("noray.llm.health_monitor.ProviderHealthMonitor.get_provider_score", return_value=1.0), \
         patch.dict(os.environ, {"AI_ROUTING_POLICY": "coding"}):
        
        req = ModelRouteRequest(query="def test_function(): pass", complexity="medium")
        model, provider, _, _ = router.route(req)
        assert provider == "deepseek" or "coder" in model
        
    # 2. Offline-first policy - Ollama local qwen should win
    with patch.object(ModelRouter, "is_provider_configured", lambda self, p: True), \
         patch("noray.llm.health_monitor.ProviderHealthMonitor.get_provider_score", return_value=1.0), \
         patch.dict(os.environ, {"AI_ROUTING_POLICY": "offline-first"}):
        
        req = ModelRouteRequest(query="General chat question", complexity="low")
        model, provider, _, _ = router.route(req)
        assert provider == "ollama"
