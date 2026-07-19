"""
NORAY — OpenRouter LLM Provider Adapter
"""

from __future__ import annotations
import os
import time
import httpx
from typing import Iterator, Optional

from noray.gateway.base import BaseLLMProvider, LLMConfig, LLMResponse


class OpenRouterProvider(BaseLLMProvider):
    """Adapter targeting OpenRouter."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

    def is_healthy(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, config: LLMConfig) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OpenRouter API key is missing.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/GhariebML/NORAY",
            "X-Title": "NORAY AI OS",
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
            
            # OpenRouter optionally returns cost in usage, but for now we mock it as 0.0 unless returned
            estimated_cost = usage.get("total_cost", 0.0)

            return LLMResponse(
                content=content.strip(),
                model=config.model,
                provider="openrouter",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                estimated_cost=estimated_cost,
                latency_ms=latency_ms
            )
        except Exception as e:
            raise RuntimeError(f"OpenRouter execution failed: {e}")

    def generate_stream(self, prompt: str, config: LLMConfig) -> Iterator[LLMResponse]:
        yield self.generate(prompt, config)
