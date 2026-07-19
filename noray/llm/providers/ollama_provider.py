"""
NORAY — Ollama Local Provider Adapter
"""

from __future__ import annotations
import os
import time
import httpx
import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional

from noray.llm.providers.base_provider import BaseLLMProvider, LLMMessage, LLMConfig, LLMResponse

logger = logging.getLogger("noray.llm.ollama")


class OllamaProvider(BaseLLMProvider):
    """Adapter targeting local Ollama runtime endpoints."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434/v1"

    def health(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.base_url}/models")
                return res.status_code == 200
        except Exception:
            return False

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        converted = []
        for m in messages:
            msg = {"role": m.role, "content": m.content}
            if m.tool_calls:
                msg["tool_calls"] = m.tool_calls
            converted.append(msg)
        return converted

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0  # Local execution cost is free

    def generate(self, messages: List[LLMMessage], config: LLMConfig) -> LLMResponse:
        start_time = time.time()
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}

        payload = {
            "model": config.model,
            "messages": self._convert_messages(messages),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens
        }
        if config.json_mode:
            payload["response_format"] = {"type": "json_object"}
        if config.tools:
            payload["tools"] = config.tools

        try:
            with httpx.Client(timeout=300.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

            latency_ms = (time.time() - start_time) * 1000
            choice = data["choices"][0]
            content = choice["message"].get("content") or ""
            tool_calls = choice["message"].get("tool_calls")
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=config.model,
                provider="ollama",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                estimated_cost=0.0,
                latency_ms=latency_ms,
                tool_calls=tool_calls,
                finish_reason=choice.get("finish_reason", "stop")
            )
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Ollama API execution failed: {e}")

    async def stream(self, messages: List[LLMMessage], config: LLMConfig) -> AsyncGenerator[LLMResponse, None]:
        start_time = time.time()
        
        if not self.health() and os.getenv("ALLOW_OFFLINE", "true").lower() == "true":
            yield LLMResponse(
                content=f"[LOCAL OFFLINE MOCK - {config.model}] Answer to: {messages[-1].content}",
                model=config.model,
                provider="ollama",
                latency_ms=(time.time() - start_time) * 1000
            )
            return

        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}

        payload = {
            "model": config.model,
            "messages": self._convert_messages(messages),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": True
        }
        if config.json_mode:
            payload["response_format"] = {"type": "json_object"}
        if config.tools:
            payload["tools"] = config.tools

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        line_content = line[6:].strip()
                        if line_content == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(line_content)
                            choice = chunk["choices"][0]
                            delta = choice.get("delta", {})
                            content_piece = delta.get("content", "")
                            tool_calls = delta.get("tool_calls")
                            
                            yield LLMResponse(
                                content=content_piece,
                                model=config.model,
                                provider="ollama",
                                tool_calls=tool_calls,
                                finish_reason=choice.get("finish_reason", "stop") or "stop"
                            )
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise RuntimeError(f"Ollama stream failed: {e}")

    def embeddings(self, text: str) -> List[float]:
        # Connect to Ollama's embeddings endpoint
        url = f"{self.base_url}/embeddings"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "bge-m3", # default local model
            "input": text
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
            return data["embedding"]
        except Exception:
            # Return a simple 384 dummy array under failure/offline fallback
            return [0.0] * 384
