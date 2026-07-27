"""
NORAY — Retrieval Telemetry Service

Stores structured JSON telemetry for every retrieval pipeline step.
Powers the diagnostics dashboard and developer console.
Users never see this data — it's for developer observability only.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("noray.rag.telemetry")

TELEMETRY_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "retrieval_telemetry.jsonl"


@dataclass
class PipelineStepTelemetry:
    """Telemetry for a single retrieval pipeline step."""
    step_name: str
    execution_time_ms: float = 0.0
    success: bool = False
    fallback_used: bool = False
    provider: str = ""
    collection: str = ""
    retrieved_chunks: int = 0
    similarity_score: float = 0.0
    embedding_model: str = ""
    latency_ms: float = 0.0
    retry_count: int = 0
    recovery_action: str = ""
    error: str = ""


@dataclass
class RetrievalTelemetry:
    """Complete telemetry for one retrieval pipeline execution."""
    timestamp: str = ""
    query: str = ""
    intent: str = ""
    session_id: str = ""
    steps: list[PipelineStepTelemetry] = field(default_factory=list)
    total_duration_ms: float = 0.0
    final_status: str = "success"
    fallback_chain_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp or time.strftime("%Y-%m-%dT%H:%M:%S"),
            "query": self.query,
            "intent": self.intent,
            "session_id": self.session_id,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "final_status": self.final_status,
            "fallback_chain_used": self.fallback_chain_used,
            "steps": [
                {
                    "step": s.step_name,
                    "time_ms": round(s.execution_time_ms, 2),
                    "ok": s.success,
                    "fallback": s.fallback_used,
                    "provider": s.provider,
                    "collection": s.collection,
                    "chunks": s.retrieved_chunks,
                    "score": round(s.similarity_score, 4),
                    "embedding": s.embedding_model,
                    "latency_ms": round(s.latency_ms, 2),
                    "retries": s.retry_count,
                    "recovery": s.recovery_action,
                    "error": s.error[:200] if s.error else "",
                }
                for s in self.steps
            ],
        }


class TelemetryStore:
    """Persists retrieval telemetry to a JSONL file for diagnostics."""

    def __init__(self, path: str | Path = TELEMETRY_LOG_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, telemetry: RetrievalTelemetry) -> None:
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(telemetry.to_dict()) + "\n")
        except Exception as e:
            logger.debug(f"Failed to write telemetry: {e}")

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Read the most recent N telemetry entries (for diagnostics API)."""
        if not self.path.exists():
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            entries = [json.loads(line) for line in lines if line.strip()]
            return entries[-limit:]
        except Exception:
            return []

    def clear(self) -> None:
        """Clear all telemetry data."""
        if self.path.exists():
            self.path.unlink()


# Global singleton
telemetry_store = TelemetryStore()


class PipelineTimer:
    """Context manager for timing pipeline steps."""

    def __init__(self, step_name: str):
        self.step_name = step_name
        self.start: float = 0.0
        self.step_telemetry: PipelineStepTelemetry = PipelineStepTelemetry(step_name=step_name)

    def __enter__(self):
        self.start = time.time()
        return self.step_telemetry

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.step_telemetry.execution_time_ms = (time.time() - self.start) * 1000
        self.step_telemetry.success = exc_type is None
        if exc_type is not None:
            self.step_telemetry.error = str(exc_val or "")
            self.step_telemetry.recovery_action = "fallback_triggered"
