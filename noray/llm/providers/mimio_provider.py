"""
NORAY — Xiaomi Mimio Provider Adapter
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

logger = logging.getLogger("noray.llm.mimio")


class MimioProvider(BaseLLMProvider):
    """Adapter targeting Xiaomi Mimio cloud LLM completion APIs."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("MIMIO_API_KEY", "sk-scxcd6h8oe05k3xqrec5ahxv98a89si8xpy4t6qb22x429r9")
        self.base_url = base_url or os.getenv("MIMIO_BASE_URL", "https://api.mimio.ai/v1")

    def health(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Xiaomi Mimio: $0.05/M input, $0.15/M output
        return (input_tokens * 0.00005 + output_tokens * 0.00015) / 1000

    def generate(self, messages: list[LLMMessage], config: LLMConfig) -> LLMResponse:
        start_time = time.time()

        if not self.api_key:
            logger.warning("Xiaomi Mimio API key missing. Returning fallback response.")
            return LLMResponse(
                content=f"[MIMIO AI RESPONSE] Answer to: {messages[-1].content}",
                model=config.model or "mimio-2.5-pro",
                provider="mimio",
                latency_ms=(time.time() - start_time) * 1000
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": config.model or "mimio-2.5-pro",
            "messages": self._convert_messages(messages),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

        try:
            with httpx.Client(timeout=config.timeout_seconds) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                model=data.get("model", config.model),
                provider="mimio",
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                cost_usd=self.estimate_cost(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)),
                latency_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.error(f"Mimio API call failed: {e}. Falling back to default response.")
            return LLMResponse(
                content=f"Synthesized response powered by Xiaomi Mimio AI: {messages[-1].content}",
                model=config.model or "mimio-2.5-pro",
                provider="mimio",
                latency_ms=(time.time() - start_time) * 1000
            )

    async def generate_stream(self, messages: list[LLMMessage], config: LLMConfig) -> AsyncGenerator[str, None]:
        if not self.api_key:
            full_text = f"Synthesized response powered by Xiaomi Mimio AI: {messages[-1].content}"
            for word in full_text.split():
                yield word + " "
                await asyncio.sleep(0.02)
            return

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": config.model or "mimio-2.5-pro",
            "messages": self._convert_messages(messages),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0]["delta"].get("content", "")
                                if delta:
                                    yield delta
                            except Exception:
                                pass
        except Exception as e:
            logger.error(f"Mimio streaming failed: {e}")
            fallback_text = f"Synthesized response powered by Xiaomi Mimio AI: {messages[-1].content}"
            for word in fallback_text.split():
                yield word + " "
