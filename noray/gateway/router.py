"""
NORAY — Intelligent Model Router

Implements requirement-aware routing rules, cost-latency trade-off balances,
and graceful provider fallback hierarchies.
"""

from __future__ import annotations

import os

from noray.gateway.base import RouteRequirements
from noray.gateway.registry import ModelMetadata, ModelRegistry


class ModelRouter:
    """Intelligently routes requests to the optimal LLM based on task constraints."""

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self.registry = registry or ModelRegistry()

    def route(self, req: RouteRequirements, active_states: dict[str, bool]) -> tuple[str, str]:
        """Determine the best model name and provider for a given set of requirements.
        
        Args:
            req: Target RouteRequirements (context, json, reasoning, preferred).
            active_states: Current health availability statuses of providers:
                           {"local": bool, "openai": bool, "anthropic": bool, "gemini": bool}
        
        Returns:
            Tuple of (model_name, provider_name).
        """
        # Read preferences override if forced
        force_provider = os.getenv("AI_PROVIDER", "auto").lower()
        if force_provider in ["local", "openai", "anthropic", "gemini"]:
            req.preferred_provider = force_provider

        # Check offline requirement
        allow_offline_only = os.getenv("ALLOW_OFFLINE", "true").lower() == "true"

        # Candidate scoring & filtering
        candidates: list[ModelMetadata] = []
        for name, meta in self.registry.list_models().items():
            # Check availability
            if not meta.is_available:
                continue

            # Check provider status
            prov = meta.provider
            if not active_states.get(prov, False):
                continue

            # If offline only, filter out cloud models
            if allow_offline_only and prov != "local":
                continue

            # Validate context size
            if meta.context_window < req.min_context_window:
                continue

            # Validate json capability
            if req.require_json and not meta.supports_json:
                continue

            # Validate reasoning capability
            if req.require_reasoning and not meta.supports_reasoning:
                continue

            # Validate cost limits
            if req.max_cost_limit is not None:
                est_cost = (meta.input_cost_per_1k + meta.output_cost_per_1k) / 2
                if est_cost > req.max_cost_limit:
                    continue

            candidates.append(meta)

        # Sort candidates:
        # 1. Preferred provider boost
        # 2. Priority index (lower is better)
        # 3. Cost profile
        def score_candidate(c: ModelMetadata) -> float:
            score = float(c.priority)
            if req.preferred_provider and c.provider == req.preferred_provider:
                score -= 1000  # Large boost to match preferred provider
            return score

        candidates.sort(key=score_candidate)

        if candidates:
            selected = candidates[0]
            return selected.name, selected.provider

        # Fallback chains when no candidates match strict bounds
        fallback_order = ["local", "openai", "anthropic", "gemini"]
        for fallback_prov in fallback_order:
            if active_states.get(fallback_prov, False):
                # Return first default model in active provider
                for name, meta in self.registry.list_models().items():
                    if meta.provider == fallback_prov:
                        return meta.name, meta.provider

        # Terminal fallback
        return "qwen2.5-coder:7b", "local"
