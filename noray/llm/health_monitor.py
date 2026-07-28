"""
NORAY — Provider Health Monitor

Continuously evaluates provider availability with real API health checks,
implements circuit breaker logic, and feeds health data to the SmartRouter.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from noray.cache.redis_cache import RedisCache
from noray.llm.factory import LLMProviderFactory

logger = logging.getLogger("noray.llm.health")

ALL_PROVIDERS = ["mimio", "openai", "anthropic", "gemini", "ollama", "openrouter", "deepseek", "mistral", "together"]
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


class ProviderHealthMonitor:
    """Monitors model provider endpoint latencies, errors, and sets dynamic scores with quarantine support."""

    def __init__(self, cache: RedisCache | None = None):
        self.cache = cache or RedisCache(namespace="noray_health")
        self.providers = ALL_PROVIDERS
        # In-memory circuit breaker state
        self._consecutive_failures: dict[str, int] = {}
        self._last_failure_time: dict[str, float] = {}
        self._quarantine_duration: int = 60
        self._circuit_breaker_threshold: int = 3
        self._circuit_cooldown: int = 300  # 5 minutes for circuit breaker

    def evaluate_all(self) -> dict[str, float]:
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

        # Check circuit breaker
        if self._is_circuit_open(provider_name):
            remaining = self._circuit_cooldown - (time.time() - self._last_failure_time.get(provider_name, 0))
            logger.info(f"Circuit OPEN for '{provider_name}', skipping ({remaining:.0f}s remaining)")
            return 0.0

        try:
            provider = LLMProviderFactory.get_provider(provider_name)
            start_time = time.time()
            is_healthy = provider.health()
            latency = (time.time() - start_time) * 1000

            if not is_healthy:
                score = 0.0
                self._record_failure(provider_name)
            else:
                self._record_success(provider_name)
                latency_penalty = min(latency / 5000.0, 0.5)
                score = 1.0 - latency_penalty

            self.cache.set(cache_key, {
                "score": score,
                "latency_ms": latency,
                "healthy": is_healthy,
                "last_success": time.time() if is_healthy else None,
                "last_error": None if is_healthy else "Health check failed",
                "consecutive_failures": self._consecutive_failures.get(provider_name, 0),
            }, ttl=60)

            logger.info(f"Health: {provider_name} healthy={is_healthy} latency={latency:.1f}ms score={score:.2f}")
            return score

        except Exception as e:
            logger.error(f"Failed to evaluate provider '{provider_name}': {e}")
            self._record_failure(provider_name)
            self.quarantine_provider(provider_name, error_msg=str(e))
            return 0.0

    def _record_failure(self, provider_name: str) -> None:
        """Track consecutive failures for circuit breaker logic."""
        current = self._consecutive_failures.get(provider_name, 0) + 1
        self._consecutive_failures[provider_name] = current
        self._last_failure_time[provider_name] = time.time()
        logger.warning(f"Provider '{provider_name}' failure #{current}")

    def _record_success(self, provider_name: str) -> None:
        """Reset failure count on success."""
        self._consecutive_failures[provider_name] = 0

    def _is_circuit_open(self, provider_name: str) -> bool:
        """Check if circuit breaker is OPEN (skip provider until cooldown expires)."""
        failures = self._consecutive_failures.get(provider_name, 0)
        if failures < self._circuit_breaker_threshold:
            return False
        elapsed = time.time() - self._last_failure_time.get(provider_name, 0)
        if elapsed >= self._circuit_cooldown:
            # Circuit half-open — reset and allow request
            self._consecutive_failures[provider_name] = 0
            logger.info(f"Circuit breaker HALF_OPEN for '{provider_name}' — allowing retry")
            return False
        return True

    def quarantine_provider(self, provider_name: str, duration: int | None = None, error_msg: str | None = None) -> None:
        """Place provider in quarantine to prevent routing requests to it during cooldown."""
        provider_name = provider_name.lower().strip()
        duration = duration or self._quarantine_duration
        quarantine_until = time.time() + duration

        logger.warning(f"Quarantining provider '{provider_name}' for {duration}s. Reason: {error_msg or 'Unresponsive'}")

        self.cache.set(f"quarantine:{provider_name}", quarantine_until, ttl=duration)
        self.cache.set(f"score:{provider_name}", {
            "score": 0.0,
            "latency_ms": 0.0,
            "healthy": False,
            "last_error": error_msg or "Unresponsive",
            "quarantined": True,
            "consecutive_failures": self._consecutive_failures.get(provider_name, 0),
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
        if self._is_circuit_open(provider_name):
            return 0.0

        cache_key = f"score:{provider_name}"
        data = self.cache.get(cache_key)
        if data:
            return data.get("score", 0.0)
        return self.evaluate_provider(provider_name)

    def get_circuit_breaker_status(self, provider_name: str) -> dict[str, Any]:
        """Get detailed circuit breaker status for diagnostic display."""
        provider_name = provider_name.lower().strip()
        failures = self._consecutive_failures.get(provider_name, 0)
        circuit_open = self._is_circuit_open(provider_name)
        remaining = 0
        if circuit_open:
            remaining = max(0, int(self._circuit_cooldown - (time.time() - self._last_failure_time.get(provider_name, 0))))

        return {
            "provider": provider_name,
            "consecutive_failures": failures,
            "threshold": self._circuit_breaker_threshold,
            "circuit_open": circuit_open,
            "cooldown_remaining_seconds": remaining,
            "quarantined": self.is_quarantined(provider_name),
        }
