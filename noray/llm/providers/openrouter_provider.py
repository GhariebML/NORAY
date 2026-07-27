"""
NORAY — OpenRouter Provider Adapter
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from noray.llm.providers.base_provider import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse

logger = logging.getLogger("noray.llm.openrouter")


class OpenRouterProvider(BaseLLMProvider):
    """Adapter targeting OpenRouter cloud models."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"

    def health(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        converted = []
        for m in messages:
            msg = {"role": m.role, "content": m.content}
            if m.tool_calls:
                msg["tool_calls"] = m.tool_calls
            converted.append(msg)
        return converted

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Standard average open weights cost: $0.10/M input, $0.40/M output
        return (input_tokens * 0.0000001 + output_tokens * 0.0000004)

    def generate(self, messages: list[LLMMessage], config: LLMConfig) -> LLMResponse:
        start_time = time.time()

        if not self.api_key:
            logger.warning("OpenRouter API key missing. Returning mock response.")
            return LLMResponse(
                content=f"[MOCK OPENROUTER RESPONSE] Answer to: {messages[-1].content}",
                model=config.model,
                provider="openrouter",
                latency_ms=(time.time() - start_time) * 1000
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://NORAY.ai",
            "X-Title": "NORAY OS",
            "Content-Type": "application/json"
        }

        payload = {
            "model": config.model,
            "messages": self._convert_messages(messages),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

            latency_ms = (time.time() - start_time) * 1000
            choice = data["choices"][0]
            content = choice["message"].get("content") or ""
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=config.model,
                provider="openrouter",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                estimated_cost=self.estimate_cost(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)),
                latency_ms=latency_ms,
                finish_reason=choice.get("finish_reason", "stop")
            )
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise RuntimeError(f"OpenRouter API execution failed: {e}") from e

    async def stream(self, messages: list[LLMMessage], config: LLMConfig) -> AsyncGenerator[LLMResponse, None]:
        start_time = time.time()

        if not self.api_key:
            yield LLMResponse(
                content=f"[MOCK OPENROUTER STREAM] Answer to: {messages[-1].content}",
                model=config.model,
                provider="openrouter",
                latency_ms=(time.time() - start_time) * 1000
            )
            return

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://NORAY.ai",
            "X-Title": "NORAY OS",
            "Content-Type": "application/json"
        }

        payload = {
            "model": config.model,
            "messages": self._convert_messages(messages),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
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

                            yield LLMResponse(
                                content=content_piece,
                                model=config.model,
                                provider="openrouter",
                                finish_reason=choice.get("finish_reason", "stop") or "stop"
                            )
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"OpenRouter streaming error: {e}")
            raise RuntimeError(f"OpenRouter stream failed: {e}") from e

    def embeddings(self, text: str) -> list[float]:
        # Fallback to local or OpenAI
        return [0.0] * 384
