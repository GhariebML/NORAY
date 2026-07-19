"""
NORAY — Token & Cost Budget Manager
Prevents cost overrun and monitors token transactions.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional

from noray.cache.redis_cache import RedisCache

logger = logging.getLogger("noray.llm.budget")


class TokenCostBudgetManager:
    """Estimates LLM request costs and tracks transaction budgets across sessions."""
    
    def __init__(self, cache: Optional[RedisCache] = None, max_session_cost_usd: float = 0.50):
        self.cache = cache or RedisCache(namespace="noray_budget")
        self.max_session_cost_usd = max_session_cost_usd

    def estimate_prompt_cost(self, prompt: str, system_prompt: str, model_name: str) -> Dict[str, Any]:
        """Provides raw token count and USD cost estimation for the target model."""
        prompt_words = len(prompt.split()) + len(system_prompt.split())
        est_tokens = int(prompt_words * 1.3) + 100  # Token multiplier buffer
        
        # Cost index matching
        cost_per_1k = 0.003  # default claude rate
        if "mini" in model_name:
            cost_per_1k = 0.00015
        elif "flash" in model_name:
            cost_per_1k = 0.000075
        elif "qwen" in model_name or "llama" in model_name:
            cost_per_1k = 0.0  # Local models are free
            
        est_cost = (est_tokens / 1000.0) * cost_per_1k
        return {"estimated_tokens": est_tokens, "estimated_cost_usd": est_cost}

    def check_budget(self, session_id: str, estimated_cost: float) -> bool:
        """Validates if the session budget limit is violated."""
        cache_key = f"cost:{session_id}"
        current = self.cache.get(cache_key) or 0.0
        
        total = current + estimated_cost
        if total > self.max_session_cost_usd:
            logger.warning(
                f"[Session: {session_id}] Cost limit exceeded! "
                f"Max: ${self.max_session_cost_usd:.4f} | Expected: ${total:.4f}"
            )
            return False
        return True

    def record_usage(self, session_id: str, actual_cost: float, input_tokens: int, output_tokens: int):
        """Records session and global cost tracking aggregates."""
        cache_key = f"cost:{session_id}"
        current = self.cache.get(cache_key) or 0.0
        self.cache.set(cache_key, current + actual_cost, ttl=86400)  # TTL of 1 day
        
        # Accumulate global telemetry cost statistics
        global_cost = self.cache.get("global_cost") or 0.0
        self.cache.set("global_cost", global_cost + actual_cost)
        
        global_tokens = self.cache.get("global_tokens") or 0
        self.cache.set("global_tokens", global_tokens + input_tokens + output_tokens)
