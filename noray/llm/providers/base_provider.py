"""
NORAY — Base LLM Provider Interface
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, AsyncGenerator, Iterator
from pydantic import BaseModel, Field


@dataclass
class LLMMessage:
    """Standardized representation of a chat message."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMConfig:
    """Generation configuration parameters."""
    model: str
    temperature: float = 0.3
    max_tokens: int = 1500
    system_prompt: str = ""
    json_mode: bool = False
    tools: Optional[List[Dict[str, Any]]] = None


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: float = 0.0
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: str = "stop"


class BaseLLMProvider(ABC):
    """Abstract interface that all NORAY LLM providers must implement."""
    
    @abstractmethod
    def generate(self, messages: List[LLMMessage], config: LLMConfig) -> LLMResponse:
        """Synchronously execute a generation request."""
        pass

    @abstractmethod
    async def stream(self, messages: List[LLMMessage], config: LLMConfig) -> AsyncGenerator[LLMResponse, None]:
        """Asynchronously stream generation tokens."""
        pass

    @abstractmethod
    def embeddings(self, text: str) -> List[float]:
        """Generate vector embedding representation for the text."""
        pass

    @abstractmethod
    def health(self) -> bool:
        """Perform health status check for the provider endpoint."""
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate the USD transaction cost for this invocation."""
        pass
