"""
NORAY — Centralized AI Gateway Interfaces

Defines the contract for LLM providers, input/output schemas,
and request routing requirements.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional
from pydantic import BaseModel, Field


@dataclass
class LLMConfig:
    """Standard request config payload for LLM generations."""
    model: str
    temperature: float = 0.3
    max_tokens: int = 1500
    system_prompt: str = ""
    json_mode: bool = False


@dataclass
class LLMResponse:
    """Unified response envelope returned by any provider adapter."""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: float = 0.0


class RouteRequirements(BaseModel):
    """Requirements used by the Model Router to dispatch LLM queries."""
    task_type: str = "chat"  # "chat", "planning", "research", "summarization", "extraction"
    min_context_window: int = 4000
    require_json: bool = False
    require_tools: bool = False
    require_reasoning: bool = False
    max_cost_limit: Optional[float] = None
    preferred_provider: Optional[str] = None  # "local", "openai", "anthropic", "gemini"


class BaseLLMProvider:
    """Abstract interface class representing a model execution provider."""

    def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Execute text generation request synchronously."""
        raise NotImplementedError

    def generate_stream(self, prompt: str, config: LLMConfig) -> Iterator[LLMResponse]:
        """Execute text generation request yielding streaming response tokens."""
        raise NotImplementedError

    def is_healthy(self) -> bool:
        """Perform a quick ping check to determine provider availability."""
        return True
