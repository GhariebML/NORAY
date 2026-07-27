"""
NORAY — Local Model Registry
Auto-discovers Ollama models and maintains a dynamic registry with
model name, context window, size, modified date, status, and availability.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger("noray.llm.local_model_registry")

PREFERRED_MODELS = ["gemma", "qwen2.5-coder", "qwen2.5"]
# Priority order: Gemma > Qwen Coder > any other installed model


@dataclass
class LocalModelInfo:
    """Information about a locally available Ollama model."""
    name: str
    size_bytes: int = 0
    modified_at: str = ""
    family: str = ""
    format: str = ""
    parameter_size: str = ""
    quantization: str = ""
    context_window: int = 8192
    available: bool = True
    last_checked: float = 0.0
    priority: int = 99

    @property
    def size_gb(self) -> float:
        return round(self.size_bytes / (1024 ** 3), 2) if self.size_bytes > 0 else 0.0


class LocalModelRegistry:
    """Discovers and maintains a live registry of locally installed Ollama models."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._models: dict[str, LocalModelInfo] = {}
        self._last_discovery: float = 0.0
        self._discovery_interval: float = 60.0  # Re-discover every 60s
        self._ollama_running: bool = False

    async def discover_models(self, force: bool = False) -> list[LocalModelInfo]:
        """Discover all locally installed Ollama models via the Ollama API."""
        now = time.time()
        if not force and now - self._last_discovery < self._discovery_interval:
            return self.sorted_models

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code != 200:
                    self._ollama_running = False
                    logger.warning(f"Ollama API returned status {res.status_code}")
                    return self.sorted_models

                self._ollama_running = True
                models_data = res.json().get("models", [])
                self._models.clear()

                for m in models_data:
                    name: str = m.get("name", "unknown")
                    details = m.get("details", {}) or {}

                    # Determine priority based on preferred model list
                    priority = 99
                    for idx, preferred in enumerate(PREFERRED_MODELS):
                        if preferred in name.lower():
                            priority = idx
                            break

                    info = LocalModelInfo(
                        name=name,
                        size_bytes=m.get("size", 0) or 0,
                        modified_at=m.get("modified_at", ""),
                        family=details.get("family", ""),
                        format=details.get("format", ""),
                        parameter_size=details.get("parameter_size", ""),
                        quantization=details.get("quantization", ""),
                        context_window=self._estimate_context_window(name, details),
                        available=True,
                        last_checked=now,
                        priority=priority,
                    )
                    self._models[name] = info

                self._last_discovery = now
                logger.info(f"Discovered {len(self._models)} local Ollama models")
                for m in self.sorted_models:
                    logger.debug(f"  Local model: {m.name} ({m.size_gb} GB, priority={m.priority})")

        except httpx.ConnectError:
            self._ollama_running = False
            logger.warning("Ollama is not running — cannot discover local models")
        except Exception as e:
            self._ollama_running = False
            logger.error(f"Failed to discover local models: {e}")

        return self.sorted_models

    @property
    def sorted_models(self) -> list[LocalModelInfo]:
        """Return models sorted by priority (Gemma first, Qwen Coder second, then rest)."""
        return sorted(self._models.values(), key=lambda m: (m.priority, m.name))

    @property
    def primary_model(self) -> str | None:
        """Get the highest-priority available local model name."""
        models = self.sorted_models
        return models[0].name if models else None

    @property
    def is_ollama_running(self) -> bool:
        return self._ollama_running

    def get_model(self, name: str) -> LocalModelInfo | None:
        """Look up a model by name."""
        return self._models.get(name)

    async def refresh(self) -> None:
        """Force rediscovery of local models."""
        await self.discover_models(force=True)

    def _estimate_context_window(self, name: str, details: dict[str, Any]) -> int:
        """Estimate context window based on model family and parameter size."""
        name_lower = name.lower()
        details_lower = {k.lower(): str(v).lower() for k, v in details.items()}

        param_size = details.get("parameter_size", "") or ""
        family = details.get("family", "") or ""

        if "gemma" in name_lower:
            return 8192
        if "qwen" in name_lower:
            return 32768 if "7b" in param_size or "7b" in name_lower else 128000
        if "llama" in name_lower:
            return 128000
        if "deepseek" in name_lower or "r1" in name_lower:
            return 16384
        if "mistral" in name_lower:
            return 32768
        if "nomic-embed" in name_lower:
            return 8192
        if "phi" in name_lower or "mixtral" in name_lower:
            return 32768
        if "command-r" in name_lower:
            return 128000

        return 8192


# Global singleton instance
local_model_registry = LocalModelRegistry()
