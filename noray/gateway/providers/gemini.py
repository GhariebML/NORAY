"""
NORAY — Google Gemini Cloud Provider Adapter
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from typing import Optional

import httpx

from noray.gateway.base import BaseLLMProvider, LLMConfig, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Adapter for Google Gemini API endpoints."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY", "")

    def is_healthy(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        # Check if api key is available; fallback to mock/development if missing
        if not self.api_key:
            return LLMResponse(
                content=f"[MOCK GEMINI RESPONSE - API KEY MISSING] Prompt: {prompt[:50]}...",
                model=config.model,
                provider="gemini"
            )

        # Gemini 1.5 formats can be called via OpenAI-compatible endpoints or Google APIs
        # Standardize call structure via google developer api or simple fallback wrapper
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_tokens
            }
        }
        if config.system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": config.system_prompt}]}

        start_time = time.time()
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

            latency_ms = (time.time() - start_time) * 1000
            content = data["candidates"][0]["content"]["parts"][0]["text"]

            # Simple token estimation
            input_tokens = len(prompt) // 4
            output_tokens = len(content) // 4
            cost = (input_tokens * 0.000075 + output_tokens * 0.0003) / 1000

            return LLMResponse(
                content=content.strip(),
                model=config.model,
                provider="gemini",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=cost,
                latency_ms=latency_ms
            )
        except Exception as e:
            # Fallback to standard OpenAI client endpoint format if raw Google API fails
            raise RuntimeError(f"Gemini API call failed: {e}") from e

    def generate_stream(self, prompt: str, config: LLMConfig) -> Iterator[LLMResponse]:
        yield self.generate(prompt, config)
