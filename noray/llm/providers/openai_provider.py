"""
NORAY — OpenAI Provider Adapter
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

logger = logging.getLogger("noray.llm.openai")


class OpenAIProvider(BaseLLMProvider):
    """Adapter targeting standard OpenAI chat completions and embeddings endpoints."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or "https://api.openai.com/v1"

    def health(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        converted = []
        for m in messages:
            msg = {"role": m.role, "content": m.content}
            if m.tool_calls:
                msg["tool_calls"] = m.tool_calls
            if m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            if m.name:
                msg["name"] = m.name
            converted.append(msg)
        return converted

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Mini cost: $0.15/M input, $0.60/M output
        # Large cost: $2.50/M input, $10.00/M output
        return (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000

    def generate(self, messages: list[LLMMessage], config: LLMConfig) -> LLMResponse:
        start_time = time.time()

        if not self.api_key:
            logger.warning("OpenAI API key missing. Returning mock response.")
            return LLMResponse(
                content=f"[MOCK OPENAI RESPONSE] Answer to: {messages[-1].content}",
                model=config.model,
                provider="openai",
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
        if config.json_mode:
            payload["response_format"] = {"type": "json_object"}
        if config.tools:
            payload["tools"] = config.tools

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

            latency_ms = (time.time() - start_time) * 1000
            choice = data["choices"][0]
            content = choice["message"].get("content") or ""
            tool_calls = choice["message"].get("tool_calls")
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            return LLMResponse(
                content=content,
                model=config.model,
                provider="openai",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=self.estimate_cost(input_tokens, output_tokens),
                latency_ms=latency_ms,
                tool_calls=tool_calls,
                finish_reason=choice.get("finish_reason", "stop")
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API execution failed: {e}") from e

    async def stream(self, messages: list[LLMMessage], config: LLMConfig) -> AsyncGenerator[LLMResponse, None]:
        start_time = time.time()

        if not self.api_key:
            yield LLMResponse(
                content=f"[MOCK OPENAI STREAM] Answer to: {messages[-1].content}",
                model=config.model,
                provider="openai",
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
        if config.json_mode:
            payload["response_format"] = {"type": "json_object"}
        if config.tools:
            payload["tools"] = config.tools

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
                            tool_calls = delta.get("tool_calls")

                            yield LLMResponse(
                                content=content_piece,
                                model=config.model,
                                provider="openai",
                                tool_calls=tool_calls,
                                finish_reason=choice.get("finish_reason", "stop") or "stop"
                            )
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise RuntimeError(f"OpenAI stream failed: {e}") from e

    def embeddings(self, text: str) -> list[float]:
        if not self.api_key:
            # return 1536 size dummy vector
            return [0.0] * 1536

        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "text-embedding-3-small",
            "input": text
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"OpenAI Embeddings error: {e}")
            raise RuntimeError(f"OpenAI embeddings extraction failed: {e}") from e
