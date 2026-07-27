"""
NORAY — OpenAI Cloud Provider Adapter
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from typing import Optional

import httpx

from noray.gateway.base import BaseLLMProvider, LLMConfig, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """Adapter for OpenAI Chat Completions API endpoints."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    def is_healthy(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                content=f"[MOCK OPENAI RESPONSE - API KEY MISSING] Prompt: {prompt[:50]}...",
                model=config.model,
                provider="openai"
            )

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens
        }
        if config.json_mode:
            payload["response_format"] = {"type": "json_object"}

        start_time = time.time()
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

            latency_ms = (time.time() - start_time) * 1000
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            # Estimate cost
            cost = (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000

            return LLMResponse(
                content=content.strip(),
                model=config.model,
                provider="openai",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=cost,
                latency_ms=latency_ms
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}") from e

    def generate_stream(self, prompt: str, config: LLMConfig) -> Iterator[LLMResponse]:
        # Simple non-stream wrapper for testing compatibility
        yield self.generate(prompt, config)
