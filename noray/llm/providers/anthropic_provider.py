"""
NORAY — Anthropic Provider Adapter
"""

from __future__ import annotations
import os
import time
import httpx
import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional

from noray.llm.providers.base_provider import BaseLLMProvider, LLMMessage, LLMConfig, LLMResponse

logger = logging.getLogger("noray.llm.anthropic")


class AnthropicProvider(BaseLLMProvider):
    """Adapter targeting Anthropic Messages API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.base_url = "https://api.anthropic.com/v1/messages"

    def health(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        converted = []
        for m in messages:
            # Anthropic messages cannot have system role in user messages list
            if m.role == "system":
                continue
            
            msg = {"role": m.role, "content": m.content}
            converted.append(msg)
        return converted

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Claude 3.5 Sonnet: $3.00/M input, $15.00/M output
        return (input_tokens * 0.003 + output_tokens * 0.015) / 1000

    def generate(self, messages: List[LLMMessage], config: LLMConfig) -> LLMResponse:
        start_time = time.time()
        
        if not self.api_key:
            logger.warning("Anthropic API key missing. Returning mock response.")
            return LLMResponse(
                content=f"[MOCK ANTHROPIC RESPONSE] Answer to: {messages[-1].content}",
                model=config.model,
                provider="anthropic",
                latency_ms=(time.time() - start_time) * 1000
            )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        # System prompt passed outside messages list in Anthropic
        system_text = config.system_prompt or ""
        for m in messages:
            if m.role == "system":
                system_text += "\n" + m.content

        payload = {
            "model": config.model,
            "messages": self._convert_messages(messages),
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }
        if system_text:
            payload["system"] = system_text.strip()

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(self.base_url, json=payload, headers=headers)
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

            return LLMResponse(
                content=content_text.strip(),
                model=config.model,
                provider="anthropic",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=self.estimate_cost(input_tokens, output_tokens),
                latency_ms=latency_ms,
                finish_reason=data.get("stop_reason") or "stop"
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise RuntimeError(f"Anthropic API execution failed: {e}")

    async def stream(self, messages: List[LLMMessage], config: LLMConfig) -> AsyncGenerator[LLMResponse, None]:
        start_time = time.time()
        
        if not self.api_key:
            yield LLMResponse(
                content=f"[MOCK ANTHROPIC STREAM] Answer to: {messages[-1].content}",
                model=config.model,
                provider="anthropic",
                latency_ms=(time.time() - start_time) * 1000
            )
            return

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        system_text = config.system_prompt or ""
        for m in messages:
            if m.role == "system":
                system_text += "\n" + m.content

        payload = {
            "model": config.model,
            "messages": self._convert_messages(messages),
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": True
        }
        if system_text:
            payload["system"] = system_text.strip()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", self.base_url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        line_content = line[6:].strip()
                        
                        try:
                            event = json.loads(line_content)
                            event_type = event.get("type")
                            if event_type == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield LLMResponse(
                                        content=delta.get("text", ""),
                                        model=config.model,
                                        provider="anthropic"
                                    )
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise RuntimeError(f"Anthropic stream failed: {e}")

    def embeddings(self, text: str) -> List[float]:
        # Anthropic does not have native embeddings endpoints, fallback to local Qwen/all-MiniLM or OpenAI
        logger.warning("Anthropic does not offer native embeddings. Returning fallback empty vector.")
        return [0.0] * 384
