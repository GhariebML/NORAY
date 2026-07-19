import os
import logging
from typing import List, Tuple, Optional, Dict
from pydantic import BaseModel

logger = logging.getLogger("noray.llm.router")

class ModelRouteRequest(BaseModel):
    """Configuration mapping for incoming task demands."""
    query: str
    complexity: str = "medium"  # "low" | "medium" | "high"
    required_context_length: int = 2048
    requires_tools: bool = False
    requires_reasoning: bool = False
    requires_vision: bool = False
    privacy_mode: bool = False


class ModelRouter:
    """Dynamic scoring-based router dishing to Tier-1, Tier-2 and Tier-3 models."""

    TIER_1_PROVIDERS = {"gemini", "deepseek", "together", "openrouter"}
    TIER_2_PROVIDERS = {"ollama"}
    TIER_3_PROVIDERS = {"openai", "anthropic", "mistral"}

    def __init__(self, monitor = None):
        from noray.llm.health_monitor import ProviderHealthMonitor
        self.monitor = monitor or ProviderHealthMonitor()

    @staticmethod
    def is_provider_configured(provider: str) -> bool:
        """Helper checking if API keys are configured for the provider."""
        from noray.config import settings
        prov = provider.lower().strip()
        if prov == "ollama":
            return bool(settings.OLLAMA_BASE_URL)
        if prov == "openai":
            return bool(settings.OPENAI_API_KEY)
        if prov == "anthropic":
            return bool(settings.ANTHROPIC_API_KEY)
        if prov == "gemini":
            return bool(settings.GOOGLE_API_KEY)
        if prov == "openrouter":
            return bool(settings.OPENROUTER_API_KEY)
        if prov == "mistral":
            return bool(settings.MISTRAL_API_KEY)
        if prov == "deepseek":
            return bool(settings.DEEPSEEK_API_KEY)
        if prov == "together":
            return bool(settings.TOGETHER_API_KEY)
        return False

    def get_policy_weights(self, policy: str) -> Dict[str, float]:
        """Get weights coefficient for model scoring according to routing policy."""
        # Defaults to balanced
        weights = {
            "reasoning": 0.25,
            "coding": 0.25,
            "latency": 0.15,
            "cost": 0.15,
            "availability": 0.1,
            "streaming": 0.05,
            "tools": 0.05
        }
        p = policy.lower().strip()
        if p == "fastest":
            weights = {
                "reasoning": 0.1,
                "coding": 0.1,
                "latency": 0.5,
                "cost": 0.1,
                "availability": 0.1,
                "streaming": 0.05,
                "tools": 0.05
            }
        elif p == "lowest-cost" or p == "lowest cost":
            weights = {
                "reasoning": 0.1,
                "coding": 0.1,
                "latency": 0.1,
                "cost": 0.6,
                "availability": 0.05,
                "streaming": 0.025,
                "tools": 0.025
            }
        elif p == "highest-quality" or p == "highest quality":
            weights = {
                "reasoning": 0.4,
                "coding": 0.4,
                "latency": 0.05,
                "cost": 0.0,
                "availability": 0.05,
                "streaming": 0.05,
                "tools": 0.05
            }
        elif p == "research":
            weights = {
                "reasoning": 0.45,
                "coding": 0.15,
                "latency": 0.1,
                "cost": 0.1,
                "availability": 0.1,
                "streaming": 0.05,
                "tools": 0.05
            }
        elif p == "coding":
            weights = {
                "reasoning": 0.15,
                "coding": 0.55,
                "latency": 0.1,
                "cost": 0.1,
                "availability": 0.05,
                "streaming": 0.025,
                "tools": 0.025
            }
        return weights

    def route(self, req: ModelRouteRequest) -> Tuple[str, str, List[Tuple[str, str]], float]:
        """
        Dynamically route and prioritize cloud, local and premium providers.
        Returns:
            Tuple of (model_name, provider_name, fallback_chain, confidence_score)
        """
        from noray.llm.model_registry import model_registry
        
        forced_provider = os.getenv("AI_PROVIDER", "auto").lower().strip()
        policy = os.getenv("AI_ROUTING_POLICY", "balanced").lower().strip()

        # Enforced Offline
        if policy == "offline-first" or policy == "offline-only" or req.privacy_mode:
            forced_provider = "ollama"

        all_registered_models = model_registry.list_models()
        weights = self.get_policy_weights(policy)

        # Separate models into Tier lists
        t1_candidates = []
        t2_candidates = []
        t3_candidates = []

        for m in all_registered_models:
            provider = m.provider.lower()
            
            # Skip if not configured
            if not self.is_provider_configured(provider):
                continue
                
            # Filter based on forced provider
            if forced_provider != "auto" and provider != forced_provider:
                continue

            # Context window compatibility
            if m.context_window < req.required_context_length:
                continue
                
            # Tools capability
            if req.requires_tools and not m.supports_tools:
                continue

            # Vision capability
            if req.requires_vision and not m.supports_vision:
                continue

            # Fetch active health status score from monitor (quarantine returns 0.0)
            health_score = self.monitor.get_provider_score(provider)
            if health_score <= 0.0 and forced_provider == "auto" and provider != "ollama":
                continue

            # Calculate cost factor (higher score is cheaper)
            total_cost = m.cost_input_per_m + m.cost_output_per_m
            cost_factor = 1.0 / (1.0 + total_cost * 100.0)

            # Score calculations
            score = (
                m.reasoning_score * weights["reasoning"] +
                m.coding_score * weights["coding"] +
                health_score * weights["availability"] +
                cost_factor * weights["cost"] +
                (1.0 if m.supports_streaming else 0.0) * weights["streaming"] +
                (1.0 if m.supports_tools else 0.0) * weights["tools"]
            )

            # Workload/Task matching bonuses
            query_lower = req.query.lower()
            if "code" in query_lower or "def " in query_lower or "class " in query_lower or "function" in query_lower or "programming" in query_lower:
                score += m.coding_score * 0.25  # Coding bonus
            if "reason" in query_lower or "explain" in query_lower or "solve" in query_lower:
                score += m.reasoning_score * 0.25 # Reasoning bonus

            # Sort into Tiers
            if provider in self.TIER_1_PROVIDERS:
                t1_candidates.append((score, m))
            elif provider in self.TIER_2_PROVIDERS:
                t2_candidates.append((score, m))
            elif provider in self.TIER_3_PROVIDERS:
                t3_candidates.append((score, m))

        # Sort candidates descending
        t1_candidates.sort(key=lambda x: x[0], reverse=True)
        t2_candidates.sort(key=lambda x: x[0], reverse=True)
        t3_candidates.sort(key=lambda x: x[0], reverse=True)

        selected = None
        fallback_list = []

        # Tier Decision Priority Flow
        if t1_candidates:
            # Normal Cloud path
            selected = t1_candidates[0][1]
            fallback_list = [c[1] for c in t1_candidates[1:]] + [c[1] for c in t2_candidates] + [c[1] for c in t3_candidates]
        elif t2_candidates:
            # Fallback to local offline inference
            selected = t2_candidates[0][1]
            fallback_list = [c[1] for c in t2_candidates[1:]] + [c[1] for c in t3_candidates]
        elif t3_candidates:
            # Ultimate premium fallback (OpenAI/Anthropic)
            selected = t3_candidates[0][1]
            fallback_list = [c[1] for c in t3_candidates[1:]]
        else:
            # Hardcoded ultimate recovery fallback
            return "qwen2.5-coder:7b", "ollama", [], 0.5

        confidence = 0.85
        fallback_chain = [(fb.model, fb.provider) for fb in fallback_list]

        logger.info(
            f"Routing decision matching: selected={selected.model} provider={selected.provider} "
            f"policy={policy} fallbacks={len(fallback_chain)}"
        )

        return selected.model, selected.provider, fallback_chain, confidence
