"""
NORAY — Mistral Provider Adapter
"""

from __future__ import annotations
import os
import time
import httpx
import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional

from noray.llm.providers.base_provider import BaseLLMProvider, LLMMessage, LLMConfig, LLMResponse

logger = logging.getLogger("noray.llm.mistral")


class MistralProvider(BaseLLMProvider):
    """Adapter targeting Mistral cloud API endpoints."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "")
        self.base_url = "https://api.mistral.ai/v1"

    def health(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        converted = []
        for m in messages:
            msg = {"role": m.role, "content": m.content}
            converted.append(msg)
        return converted

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Mistral Large average: $2.50/M input, $7.50/M output
        return (input_tokens * 0.0025 + output_tokens * 0.0075) / 1000

    def generate(self, messages: List[LLMMessage], config: LLMConfig) -> LLMResponse:
        start_time = time.time()
        
        if not self.api_key:
            logger.warning("Mistral API key missing. Returning mock response.")
            return LLMResponse(
                content=f"[MOCK MISTRAL RESPONSE] Answer to: {messages[-1].content}",
                model=config.model,
                provider="mistral",
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

            return LLMResponse(
                content=content,
                model=config.model,
                provider="mistral",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                estimated_cost=self.estimate_cost(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)),
                latency_ms=latency_ms,
                finish_reason=choice.get("finish_reason", "stop")
            )
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            raise RuntimeError(f"Mistral API execution failed: {e}")

    async def stream(self, messages: List[LLMMessage], config: LLMConfig) -> AsyncGenerator[LLMResponse, None]:
        start_time = time.time()
        
        if not self.api_key:
            yield LLMResponse(
                content=f"[MOCK MISTRAL STREAM] Answer to: {messages[-1].content}",
                model=config.model,
                provider="mistral",
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
                            
                            yield LLMResponse(
                                content=content_piece,
                                model=config.model,
                                provider="mistral",
                                finish_reason=choice.get("finish_reason", "stop") or "stop"
                            )
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"Mistral streaming error: {e}")
            raise RuntimeError(f"Mistral stream failed: {e}")

    def embeddings(self, text: str) -> List[float]:
        # Mistral embeddings endpoint
        if not self.api_key:
            return [0.0] * 1024

        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-embed",
            "input": [text]
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Mistral Embeddings error: {e}")
            raise RuntimeError(f"Mistral embeddings extraction failed: {e}")
