"""
NORAY — Benchmark Engine
Tracks latency averages, reliability metrics, and performance counters per provider.
"""

from __future__ import annotations

import logging
from typing import Any

from noray.cache.redis_cache import RedisCache

logger = logging.getLogger("noray.services.benchmark")


class BenchmarkEngine:
    """Gathers transactional metrics across executions to inform LLM routing decisions."""

    def __init__(self, cache: RedisCache | None = None):
        self.cache = cache or RedisCache(namespace="noray_benchmarks")

    def record_transaction(self, provider_name: str, model_name: str, latency_ms: float, success: bool = True):
        """Records latency and status values for routing calibration."""
        # 1. Update average latency
        key_lat = f"{provider_name}:{model_name}:latency"
        stats = self.cache.get(key_lat) or {"count": 0, "avg": 0.0}
        stats["avg"] = (stats["avg"] * stats["count"] + latency_ms) / (stats["count"] + 1)
        stats["count"] += 1
        self.cache.set(key_lat, stats)

        # 2. Update success rate
        key_succ = f"{provider_name}:{model_name}:success"
        succ_stats = self.cache.get(key_succ) or {"total": 0, "successes": 0}
        succ_stats["total"] += 1
        if success:
            succ_stats["successes"] += 1
        self.cache.set(key_succ, succ_stats)

        logger.debug(
            f"Logged transaction: provider={provider_name} model={model_name} "
            f"latency={latency_ms:.2f}ms success={success}"
        )

    def get_benchmark_scores(self, provider_name: str, model_name: str) -> dict[str, Any]:
        """Calculates success rates and average latencies from historical execution logs."""
        key_lat = f"{provider_name}:{model_name}:latency"
        key_succ = f"{provider_name}:{model_name}:success"

        stats = self.cache.get(key_lat) or {"avg": 2000.0}
        succ_stats = self.cache.get(key_succ) or {"total": 1, "successes": 1}

        success_rate = succ_stats["successes"] / max(succ_stats["total"], 1)
        return {
            "average_latency_ms": stats["avg"],
            "success_rate": success_rate
        }
