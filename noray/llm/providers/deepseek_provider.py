"""
NORAY — DeepSeek Provider Adapter
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

logger = logging.getLogger("noray.llm.deepseek")


class DeepSeekProvider(BaseLLMProvider):
    """Adapter targeting DeepSeek cloud completions APIs (deepseek-chat, deepseek-reasoner)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = "https://api.deepseek.com"

    def health(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        converted = []
        for m in messages:
            msg = {"role": m.role, "content": m.content}
            converted.append(msg)
        return converted

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # DeepSeek Chat: $0.14/M input, $0.28/M output (cached input is $0.014/M)
        return (input_tokens * 0.00014 + output_tokens * 0.00028) / 1000

    def generate(self, messages: list[LLMMessage], config: LLMConfig) -> LLMResponse:
        start_time = time.time()

        if not self.api_key:
            logger.warning("DeepSeek API key missing. Returning mock response.")
            return LLMResponse(
                content=f"[MOCK DEEPSEEK RESPONSE] Answer to: {messages[-1].content}",
                model=config.model,
                provider="deepseek",
                latency_ms=(time.time() - start_time) * 1000
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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

            # DeepSeek Reasoner exposes reasoning_content
            reasoning_content = choice["message"].get("reasoning_content", "")
            if reasoning_content:
                content = f"<think>\n{reasoning_content}\n</think>\n" + content

            return LLMResponse(
                content=content,
                model=config.model,
                provider="deepseek",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                estimated_cost=self.estimate_cost(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)),
                latency_ms=latency_ms,
                finish_reason=choice.get("finish_reason", "stop")
            )
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise RuntimeError(f"DeepSeek API execution failed: {e}") from e

    async def stream(self, messages: list[LLMMessage], config: LLMConfig) -> AsyncGenerator[LLMResponse, None]:
        start_time = time.time()

        if not self.api_key:
            yield LLMResponse(
                content=f"[MOCK DEEPSEEK STREAM] Answer to: {messages[-1].content}",
                model=config.model,
                provider="deepseek",
                latency_ms=(time.time() - start_time) * 1000
            )
            return

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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

                            # Stream reasoning delta if present
                            reasoning_piece = delta.get("reasoning_content", "")
                            if reasoning_piece:
                                content_piece = f"[Reasoning] {reasoning_piece}"

                            yield LLMResponse(
                                content=content_piece,
                                model=config.model,
                                provider="deepseek",
                                finish_reason=choice.get("finish_reason", "stop") or "stop"
                            )
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}")
            raise RuntimeError(f"DeepSeek stream failed: {e}") from e

    def embeddings(self, text: str) -> list[float]:
        return [0.0] * 384
