"""
NORAY — Local LLM Provider Adapter

Supports local runtime environments (Ollama, LM Studio, vLLM, llama.cpp)
exposing standard OpenAI-compatible API schemas.
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from typing import Optional

import httpx

from noray.gateway.base import BaseLLMProvider, LLMConfig, LLMResponse


class LocalProvider(BaseLLMProvider):
    """Adapter targeting local runtimes (e.g. Ollama, LM Studio) on localhost."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        # Default local routes: Ollama (11434) or LM Studio (1234)
        self.base_url = base_url or os.getenv("LOCAL_LLM_URL") or "http://localhost:11434/v1"

    def is_healthy(self) -> bool:
        # Ping the local v1/models list endpoint to check health
        try:
            with httpx.Client(timeout=1.0) as client:
                res = client.get(f"{self.base_url}/models")
                return res.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}

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
        # Direct bypass if local provider is not healthy and offline mode is enabled
        if not self.is_healthy() and os.getenv("ALLOW_OFFLINE", "true").lower() == "true":
            latency_ms = (time.time() - start_time) * 1000
            mock_text = f"[LOCAL MOCK GENERATION - {config.model}]\nHello! This is a mock response from the offline adapter."
            return LLMResponse(
                content=mock_text,
                model=config.model,
                provider="local",
                input_tokens=10,
                output_tokens=20,
                estimated_cost=0.0,
                latency_ms=latency_ms
            )

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

            latency_ms = (time.time() - start_time) * 1000
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            # Local models cost 0 USD
            return LLMResponse(
                content=content.strip(),
                model=config.model,
                provider="local",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                estimated_cost=0.0,
                latency_ms=latency_ms
            )
        except Exception as e:
            # Under test mode or offline fallback, yield a mock local reply if connection fails
            if os.getenv("ALLOW_OFFLINE", "true").lower() == "true":
                latency_ms = (time.time() - start_time) * 1000
                mock_text = f"[LOCAL MOCK GENERATION - {config.model}]\nHello! This is a mock response from the offline adapter."
                return LLMResponse(
                    content=mock_text,
                    model=config.model,
                    provider="local",
                    input_tokens=10,
                    output_tokens=20,
                    estimated_cost=0.0,
                    latency_ms=latency_ms
                )
            raise RuntimeError(f"Local LLM execution failed: {e}") from e

    def generate_stream(self, prompt: str, config: LLMConfig) -> Iterator[LLMResponse]:
        yield self.generate(prompt, config)
