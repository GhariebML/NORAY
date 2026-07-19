"""
NORAY — Centralized AI Gateway Facade

Provides the single entry point for all model query transactions.
Manages provider health caches, execution, fallbacks, and cost tracking.
"""

from __future__ import annotations
import logging
import uuid
import time
from typing import Dict, List, Optional

from noray.gateway.base import BaseLLMProvider, LLMConfig, LLMResponse, RouteRequirements
from noray.gateway.registry import ModelRegistry
from noray.gateway.router import ModelRouter

# Specific Provider imports
from noray.gateway.providers.local import LocalProvider
from noray.gateway.providers.openai import OpenAIProvider
from noray.gateway.providers.anthropic import AnthropicProvider
from noray.gateway.providers.gemini import GeminiProvider
from noray.gateway.providers.openrouter import OpenRouterProvider

logger = logging.getLogger("noray.gateway")


class AIGateway:
    """Enterprise AI Gateway providing unified model dispatching and tracking."""

    _instance: Optional[AIGateway] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, registry: Optional[ModelRegistry] = None) -> None:
        if self._initialized:
            return
        
        self.registry = registry or ModelRegistry()
        self.router = ModelRouter(self.registry)
        
        # Instantiate provider clients
        self.providers: Dict[str, BaseLLMProvider] = {
            "local": LocalProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
            "openrouter": OpenRouterProvider()
        }
        
        # Diagnostics tracking metrics
        self.metrics = {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_estimated_cost": 0.0,
            "total_latency_ms": 0.0
        }
        
        self._initialized = True

    def get_provider_health_states(self) -> Dict[str, bool]:
        """Perform light status pings across providers to evaluate health."""
        states = {}
        for name, provider in self.providers.items():
            # Local is always considered available if test-mode or offline mode is true
            if name == "local":
                states[name] = True
            else:
                states[name] = provider.is_healthy()
        return states

    def call_llm(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1500,
        requirements: Optional[RouteRequirements] = None
    ) -> LLMResponse:
        """Central execution point for all LLM calls in NORAY."""
        req_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        start_time = time.time()

        req = requirements or RouteRequirements()
        health_states = self.get_provider_health_states()

        # Phase 1: Determine target model & provider
        try:
            model_name, provider_name = self.router.route(req, health_states)
        except Exception as e:
            logger.error(f"[Req: {req_id}] Routing resolution failed: {e}. Defaulting to local Qwen.")
            model_name, provider_name = "qwen2.5-coder:7b", "local"

        logger.info(f"[Req: {req_id} | Trace: {trace_id}] Routing to model={model_name} (provider={provider_name})")

        # Phase 2: Execute with fallback chains
        error_msg = None
        try:
            provider = self.providers[provider_name]
            cfg = LLMConfig(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                json_mode=req.require_json
            )
            response = provider.generate(prompt, cfg)
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"[Req: {req_id}] Provider {provider_name} failed: {e}. Initiating fallback chain.")
            fallback_provider = self.providers["local"]
            cfg = LLMConfig(
                model="qwen2.5-coder:7b",
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                json_mode=req.require_json
            )
            response = fallback_provider.generate(prompt, cfg)

        total_exec_time = (time.time() - start_time) * 1000

        # Update metrics
        self.metrics["total_requests"] += 1
        self.metrics["total_input_tokens"] += response.input_tokens
        self.metrics["total_output_tokens"] += response.output_tokens
        self.metrics["total_estimated_cost"] += response.estimated_cost
        self.metrics["total_latency_ms"] += response.latency_ms

        # Structured Logging for Observability
        logger.info(
            f"[Req: {req_id} | Trace: {trace_id}] Execution completed. "
            f"Provider: {response.provider} | Model: {response.model} | "
            f"Tokens (In/Out): {response.input_tokens}/{response.output_tokens} | "
            f"Latency: {response.latency_ms:.2f}ms | Total Time: {total_exec_time:.2f}ms | "
            f"Cost: ${response.estimated_cost:.6f}"
            + (f" | Error: {error_msg}" if error_msg else "")
        )

        return response
