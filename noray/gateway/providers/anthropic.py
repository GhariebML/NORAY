"""
NORAY — Anthropic Cloud Provider Adapter
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from typing import Optional

import httpx

from noray.gateway.base import BaseLLMProvider, LLMConfig, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """Adapter for Anthropic Messages API endpoints."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    def is_healthy(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                content=f"[MOCK ANTHROPIC RESPONSE - API KEY MISSING] Prompt: {prompt[:50]}...",
                model=config.model,
                provider="anthropic"
            )

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        payload = {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }
        if config.system_prompt:
            payload["system"] = config.system_prompt

        start_time = time.time()
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

            latency_ms = (time.time() - start_time) * 1000

            content_text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content_text += block.get("text", "")

            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            # Estimate cost
            cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000

            return LLMResponse(
                content=content_text.strip(),
                model=config.model,
                provider="anthropic",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=cost,
                latency_ms=latency_ms
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {e}") from e

    def generate_stream(self, prompt: str, config: LLMConfig) -> Iterator[LLMResponse]:
        yield self.generate(prompt, config)
