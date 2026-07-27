"""
NORAY — Telemetry & Metrics Aggregator
"""
from typing import Any


class TelemetryStore:
    def __init__(self):
        self.metrics = {
            "requests_per_sec": 0,
            "average_latency_ms": 0,
            "tokens_per_sec": 0,
            "gpu_utilization": "25%",
            "cache_hit_rate": 0.85
        }

    def get_metrics(self) -> dict[str, Any]:
        return self.metrics

telemetry_store = TelemetryStore()
