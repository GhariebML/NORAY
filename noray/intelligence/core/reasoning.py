"""
NORAY — Cognitive Reasoning Engine
Implements the 9-step ReAct (Reason + Act) loop with Reflection.
"""

from __future__ import annotations
import uuid
import json
import logging
from typing import Any, Dict, List, Optional

from noray.intelligence.core.interfaces import IReasoningEngine, IContextEngine
from noray.intelligence.core.planning import PlanningMode, get_planning_mode, PlanModeType
from noray.llm.factory import LLMProviderFactory
from noray.llm.router import ModelRouter, ModelRouteRequest
from noray.llm.providers.base_provider import LLMMessage, LLMConfig
from noray.prompts.loader import PromptLoader
from noray.agents.tools.builtins import BuiltinToolRegistry
from noray.services.conversation_manager import ConversationManager, ConversationSession
from noray.llm.response_builder import ResponseBuilder

logger = logging.getLogger("noray.intelligence.reasoning")


class ReasoningEngine(IReasoningEngine):
    """Executes the ReAct loop, coordinating tool discovery, execution, reflection, and responds."""
    
    def __init__(self, context_engine: IContextEngine):
        self.context_engine = context_engine
        self.prompt_loader = PromptLoader()
        self.router = ModelRouter()
        self.budget_manager = None  # Lazy load budget manager inside loop to avoid cyclic dependencies
        self.session_manager = ConversationManager()
        self.builtin_tools = BuiltinToolRegistry()

    async def execute_cognitive_loop(
        self, 
        goal: str, 
        context: str, 
        mode: Optional[PlanningMode] = None, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the autonomous cognitive reasoning cycle.
        """
        # Resolve dependencies
        from noray.llm.budget_manager import TokenCostBudgetManager
        if not self.budget_manager:
            self.budget_manager = TokenCostBudgetManager()

        active_session_id = session_id or str(uuid.uuid4())
        active_mode = mode or get_planning_mode(PlanModeType.BALANCED)

        # Load or create active session state
        session = self.session_manager.get_session(active_session_id)
        if not session:
            session = self.session_manager.create_session(active_session_id, goal)

        # 1. Routing Model Selection
        req = ModelRouteRequest(
            query=goal,
            complexity="high" if active_mode.max_reflection_iterations > 3 else "medium",
            required_context_length=len(context) + 1000,
            requires_tools=True,
            requires_reasoning=True
        )
        model_name, provider_name, fallbacks, confidence = self.router.route(req)
        
        # 2. Extract tools metadata
        tools_list = self.builtin_tools.list_tools()
        system_prompt = self.prompt_loader.render("system", {
            "agent_name": "Cognitive Coordinator", 
            "agent_context": "Executing autonomous goal resolution"
        })
        
        react_instructions = (
            f"You are inside NORAY's ReAct execution loop.\n"
            f"Context: {context}\n"
            f"Goal: {goal}\n"
            f"Available tools: {json.dumps(tools_list)}\n"
            f"On each turn, you MUST output a JSON object containing either:\n"
            f"1. For tools: {{\"thought\": \"your logic\", \"action\": \"tool_name\", \"arguments\": {{...}}}}\n"
            f"2. For final answer: {{\"thought\": \"your logic\", \"answer\": \"your markdown response\"}}\n"
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=react_instructions)
        ]

        # Build candidates chain including fallbacks
        candidates = [(model_name, provider_name)] + fallbacks
        active_candidate_idx = 0

        provider = LLMProviderFactory.get_provider(provider_name)
        config = LLMConfig(
            model=model_name,
            system_prompt=system_prompt,
            temperature=0.2,
            json_mode=True
        )

        reasoning_steps = []
        tools_executed = []
        final_answer = ""
        
        iterations = active_mode.max_reflection_iterations
        for i in range(iterations):
            current_model = config.model
            current_provider_name = candidates[active_candidate_idx][1] if active_candidate_idx < len(candidates) else "unknown"
            logger.info(f"ReAct Loop turn {i+1}/{iterations} using model {current_model} via {current_provider_name}")
            
            res = None
            success = False
            
            while not success:
                try:
                    res = provider.generate(messages, config)
                    self.budget_manager.record_usage(active_session_id, res.estimated_cost, res.input_tokens, res.output_tokens)
                    session.cost += res.estimated_cost
                    success = True
                except Exception as e:
                    logger.error(f"ReAct LLM Turn failed with model {config.model} via provider: {e}")
                    active_candidate_idx += 1
                    if active_candidate_idx < len(candidates):
                        next_model, next_prov = candidates[active_candidate_idx]
                        logger.info(f"Falling back to candidate: {next_model} via {next_prov}")
                        provider = LLMProviderFactory.get_provider(next_prov)
                        config = LLMConfig(
                            model=next_model,
                            system_prompt=system_prompt,
                            temperature=0.2,
                            json_mode=True
                        )
                    else:
                        logger.error("All routed models and fallbacks failed. Using offline local mock fallback.")
                        mock_content = '{"thought": "LLM communication failed", "answer": "All configured LLM providers returned errors (e.g., Anthropic API error: 401 Unauthorized). Please check that your API keys are valid."}'
                        from noray.llm.providers.base_provider import LLMResponse
                        res = LLMResponse(
                            content=mock_content,
                            model="mock-fallback",
                            provider="mock",
                            latency_ms=10
                        )
                        success = True

            # Parse action or answer JSON
            try:
                data = json.loads(res.content)
            except Exception:
                data = {"thought": "JSON parsing failed, returning raw response", "answer": res.content}

            thought = data.get("thought", "")
            if thought:
                reasoning_steps.append(thought)
                session.reasoning_trace.append(f"Turn {i+1} Thought: {thought}")

            action = data.get("action")
            if action:
                args = data.get("arguments", {})
                session.reasoning_trace.append(f"Turn {i+1} Action: {action} with arguments {json.dumps(args)}")
                
                # Execute tool autonomously
                tool_def = self.builtin_tools.get(action)
                if tool_def:
                    logger.info(f"Autonomous Tool Execution: {action}")
                    obs = self.builtin_tools.execute(action, args)
                    tools_executed.append(action)
                    session.tools_executed.append(action)
                else:
                    obs = f"Error: Tool '{action}' is not registered."

                session.reasoning_trace.append(f"Turn {i+1} Observation: {json.dumps(obs)}")
                
                # Append context for next loop turn
                messages.append(LLMMessage(role="assistant", content=res.content))
                messages.append(LLMMessage(role="user", content=f"Observation: {json.dumps(obs)}"))
            elif "answer" in data:
                final_answer = data["answer"]
                session.reasoning_trace.append(f"Turn {i+1} Final Answer reached.")
                break
            else:
                final_answer = res.content
                break

        if not final_answer:
            final_answer = "Reasoning budget limits reached before a final answer could be resolved."

        # Compile final response
        structured_res = ResponseBuilder.build_structured_response(
            raw_content=final_answer,
            citations=[{"source": "NORAY Memory", "score": confidence}],
            confidence_score=confidence,
            reasoning_steps=reasoning_steps,
            suggested_actions=["Verify ATS compatibility", "Tailor CV to ML Job requirements"]
        )

        session.status = "completed"
        self.session_manager.save_session(session)

        return structured_res
