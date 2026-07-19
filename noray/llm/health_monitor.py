"""
NORAY — Provider Health Monitor
Continuously evaluates provider availability, latency, and handles quarantine logic.
"""

from __future__ import annotations
import time
import logging
from typing import Dict, Optional

from noray.llm.factory import LLMProviderFactory
from noray.cache.redis_cache import RedisCache

logger = logging.getLogger("noray.llm.health")


class ProviderHealthMonitor:
    """Monitors model provider endpoint latencies, errors, and sets dynamic scores with quarantine support."""
    
    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache or RedisCache(namespace="noray_health")
        self.providers = ["openai", "anthropic", "gemini", "ollama", "openrouter", "deepseek", "mistral", "together"]

    def evaluate_all(self) -> Dict[str, float]:
        """Runs health evaluation checks across all configured providers."""
        scores = {}
        for p_name in self.providers:
            scores[p_name] = self.evaluate_provider(p_name)
        return scores

    def evaluate_provider(self, provider_name: str) -> float:
        """Pings the target provider to evaluate availability, latencies and compute score."""
        provider_name = provider_name.lower().strip()
        cache_key = f"score:{provider_name}"
        
        # Check quarantine first
        if self.is_quarantined(provider_name):
            logger.info(f"Skipping evaluation: provider '{provider_name}' is currently quarantined.")
            return 0.0

        try:
            provider = LLMProviderFactory.get_provider(provider_name)
            start_time = time.time()
            is_healthy = provider.health()
            latency = (time.time() - start_time) * 1000
            
            if not is_healthy:
                score = 0.0
                self.quarantine_provider(provider_name)
            else:
                # Higher latency penalizes the score (up to 0.5 maximum penalty)
                latency_penalty = min(latency / 5000.0, 0.5)
                score = 1.0 - latency_penalty
                
            self.cache.set(cache_key, {
                "score": score,
                "latency_ms": latency,
                "healthy": is_healthy,
                "last_success": time.time() if is_healthy else None,
                "last_error": None if is_healthy else "Health check failed"
            }, ttl=60)
            return score
        except Exception as e:
            logger.error(f"Failed to evaluate provider '{provider_name}': {e}")
            self.quarantine_provider(provider_name, error_msg=str(e))
            return 0.0

    def quarantine_provider(self, provider_name: str, duration: int = 60, error_msg: Optional[str] = None) -> None:
        """Place provider in quarantine to prevent routing requests to it during cooldown."""
        provider_name = provider_name.lower().strip()
        quarantine_until = time.time() + duration
        
        logger.warning(f"Quarantining provider '{provider_name}' for {duration}s. Reason: {error_msg or 'Unresponsive'}")
        
        # Store quarantine state and metadata
        self.cache.set(f"quarantine:{provider_name}", quarantine_until, ttl=duration)
        self.cache.set(f"score:{provider_name}", {
            "score": 0.0,
            "latency_ms": 0.0,
            "healthy": False,
            "last_error": error_msg or "Unresponsive",
            "quarantined": True
        }, ttl=duration)

    def is_quarantined(self, provider_name: str) -> bool:
        """Check if provider is quarantined."""
        provider_name = provider_name.lower().strip()
        quarantine_until = self.cache.get(f"quarantine:{provider_name}")
        if quarantine_until and time.time() < float(quarantine_until):
            return True
        return False

    def get_provider_score(self, provider_name: str) -> float:
        """Retrieves cached score, triggering immediate evaluation if miss."""
        provider_name = provider_name.lower().strip()
        if self.is_quarantined(provider_name):
            return 0.0
            
        cache_key = f"score:{provider_name}"
        data = self.cache.get(cache_key)
        if data:
            return data.get("score", 0.0)
        return self.evaluate_provider(provider_name)
