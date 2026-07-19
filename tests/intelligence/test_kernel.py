import pytest
import asyncio
from noray.intelligence.core.kernel import AIKernel
from noray.intelligence.agents.registries import InMemoryAgentRegistry, InMemoryCapabilityRegistry
from noray.intelligence.tools.registry import ToolRegistry
from noray.intelligence.memory.context_engine import ContextEngine
from noray.intelligence.core.reasoning import ReasoningEngine
from noray.services.hitl import HITLManager
from noray.career_agent.agent import CareerAgent
from noray.intelligence.core.planning import PlanModeType

@pytest.mark.asyncio
async def test_ai_kernel_execution():
    # Setup dependencies
    agent_registry = InMemoryAgentRegistry()
    cap_registry = InMemoryCapabilityRegistry()
    tool_registry = ToolRegistry()
    context_engine = ContextEngine()
    reasoning_engine = ReasoningEngine(context_engine)
    hitl_manager = HITLManager()
    
    # Register an agent
    career_agent = CareerAgent()
    agent_registry.register(career_agent)
    for cap in career_agent.get_metadata().capabilities:
        cap_registry.register_capability(cap, career_agent.get_metadata().agent_id)
        
    # Construct Kernel
    kernel = AIKernel(
        agent_registry=agent_registry,
        capability_registry=cap_registry,
        tool_registry=tool_registry,
        context_engine=context_engine,
        reasoning_engine=reasoning_engine,
        hitl_manager=hitl_manager
    )
    
    # Execute a task
    goal = "I want to find a remote software engineering job."
    result = await kernel.execute_request(goal=goal, session_id="test_session", mode="fast")
    
    assert result is not None
    assert "response" in result
    assert result["confidence_score"] >= 0.0
    assert "citations" in result
