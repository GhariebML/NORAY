"""
NORAY — Phase 4.3 Cognitive Engine & Unified Gateway Tests
"""

import pytest
import os
from noray.cache.redis_cache import RedisCache
from noray.prompts.loader import PromptLoader
from noray.llm.router import ModelRouter, ModelRouteRequest
from noray.llm.memory_ranking import MemoryRanker
from noray.llm.response_builder import ResponseBuilder
from noray.intelligence.core.di import get_kernel


def test_redis_cache_fallback():
    """Verify RedisCache defaults gracefully to in-memory fallback if server is offline."""
    cache = RedisCache(namespace="test_noray_cache", host="localhost", port=9999)
    assert cache.client is None or not cache.client.ping()
    
    # Verify fallback operations succeed
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    cache.delete("key1")
    assert cache.get("key1") is None


def test_prompt_loader_rendering():
    """Verify PromptLoader resolves paths and processes template replacements."""
    loader = PromptLoader()
    # system_v1 requires: agent_name, agent_context
    rendered = loader.render("system", {"agent_name": "TestAgent", "agent_context": "Testing prompts system"})
    assert "TestAgent" in rendered
    assert "Testing prompts system" in rendered


def test_model_router_scoring():
    """Verify ModelRouter score ranking select logic."""
    router = ModelRouter()
    req = ModelRouteRequest(
        query="Write code for a high-performance vector retrieval engine",
        complexity="high",
        requires_tools=True,
        requires_reasoning=True
    )
    model, provider, fallbacks, confidence = router.route(req)
    assert model is not None
    assert provider is not None
    assert confidence > 0.0


def test_memory_ranker():
    """Verify priority structure of ranked memory parts."""
    ranker = MemoryRanker(top_k=2)
    working = ["working_task_1"]
    semantic = ["profile_fact_1"]
    
    context = ranker.rank_context(
        query="test query",
        working_memory=working,
        semantic_memories=semantic
    )
    
    assert "working_task_1" in context
    assert "profile_fact_1" in context
    assert context.index("working_task_1") < context.index("profile_fact_1")


def test_response_builder():
    """Verify response wrapper structured output formatting."""
    res = ResponseBuilder.build_structured_response(
        raw_content="Match fit is 80%.",
        citations=[{"source": "CV File"}],
        confidence_score=0.85,
        reasoning_steps=["Looked up CV", "Compared skill matches"]
    )
    
    assert "Match fit is 80%." in res["response"]
    assert "Citations" in res["response"]
    assert len(res["citations"]) == 1
    assert res["confidence_score"] == 0.85


@pytest.mark.asyncio
async def test_kernel_e2e_mock():
    """Verify AIKernel coordinates request through full mock lifecycle."""
    kernel = get_kernel()
    res = await kernel.execute_request("Decompose jobs matching profile requirements", session_id="test_session")
    
    assert res is not None
    assert "response" in res
    assert res["confidence_score"] > 0.0
