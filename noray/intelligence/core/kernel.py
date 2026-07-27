"""
NORAY — AI Kernel
The central execution coordinator for the intelligence layer.
"""

from __future__ import annotations

import logging
from typing import Any

from noray.intelligence.core.interfaces import IAgentRegistry, ICapabilityRegistry, IContextEngine, IReasoningEngine
from noray.intelligence.core.planning import PlanModeType, get_planning_mode
from noray.intelligence.tools.registry import ToolRegistry
from noray.services.evaluation_engine import EvaluationEngine
from noray.services.hitl import HITLManager

logger = logging.getLogger("noray.intelligence.kernel")


class AIKernel:
    """Central orchestrator connecting memory, router, reasoning engine, and evaluations."""

    def __init__(
        self,
        agent_registry: IAgentRegistry,
        capability_registry: ICapabilityRegistry,
        tool_registry: ToolRegistry,
        context_engine: IContextEngine,
        reasoning_engine: IReasoningEngine,
        hitl_manager: HITLManager
    ):
        self.agents = agent_registry
        self.capabilities = capability_registry
        self.tools = tool_registry
        self.context = context_engine
        self.reasoning = reasoning_engine
        self.hitl = hitl_manager
        self.eval_engine = EvaluationEngine()

    async def execute_request(self, goal: str, session_id: str, mode: str = "balanced") -> dict[str, Any]:
        """Main entry point for all cognitive tasks."""
        logger.info(f"[Kernel] Executing request for session {session_id} - Goal: {goal}")

        # 1. Build Context using ContextEngine and MemoryRanker
        context_str = await self.context.build_context(goal, session_id)

        # 2. Planning and Reasoning loop execution
        planning_mode = get_planning_mode(PlanModeType(mode))

        # Invoke ReAct reasoning loop
        result = await self.reasoning.execute_cognitive_loop(
            goal=goal,
            context=context_str,
            mode=planning_mode,
            session_id=session_id
        )

        # 3. Post-execution evaluation
        try:
            eval_scores = self.eval_engine.evaluate(
                session_id=session_id,
                prompt=goal,
                response=result["response"]
            )
            result["evaluation"] = eval_scores
        except Exception as e:
            logger.warning(f"Failed to execute evaluation scoring: {e}")
            result["evaluation"] = {}

        return result
