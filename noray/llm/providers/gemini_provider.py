"""
NORAY — Gemini Provider Adapter
"""

from __future__ import annotations
import os
import time
import httpx
import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional

from noray.llm.providers.base_provider import BaseLLMProvider, LLMMessage, LLMConfig, LLMResponse

logger = logging.getLogger("noray.llm.gemini")


class GeminiProvider(BaseLLMProvider):
    """Adapter targeting Google Gemini API endpoints."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def health(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        converted = []
        for m in messages:
            # Gemini expects 'user' or 'model' role, and structure: {'role': 'user', 'parts': [{'text': '...'}]}
            role = "user" if m.role in ["user", "system", "tool"] else "model"
            converted.append({
                "role": role,
                "parts": [{"text": m.content}]
            })
        return converted

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Gemini 1.5 Flash: $0.075/M input, $0.30/M output
        return (input_tokens * 0.000075 + output_tokens * 0.0003) / 1000

    def generate(self, messages: List[LLMMessage], config: LLMConfig) -> LLMResponse:
        start_time = time.time()
        
        if not self.api_key:
            logger.warning("Gemini API key missing. Returning mock response.")
            return LLMResponse(
                content=f"[MOCK GEMINI RESPONSE] Answer to: {messages[-1].content}",
                model=config.model,
                provider="gemini",
                latency_ms=(time.time() - start_time) * 1000
            )

        model_name = config.model
        url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        # Extract system instruction
        system_instruction = None
        system_text = config.system_prompt or ""
        for m in messages:
            if m.role == "system":
                system_text += "\n" + m.content
        if system_text.strip():
            system_instruction = {"parts": [{"text": system_text.strip()}]}

        payload = {
            "contents": self._convert_messages(messages),
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if config.json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

            latency_ms = (time.time() - start_time) * 1000
            
            candidates = data.get("candidates", [])
            content_text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for p in parts:
                    content_text += p.get("text", "")

            # Cost / usage parsing
            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

            return LLMResponse(
                content=content_text.strip(),
                model=config.model,
                provider="gemini",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=self.estimate_cost(input_tokens, output_tokens),
                latency_ms=latency_ms,
                finish_reason="stop"
            )
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini API execution failed: {e}")

    async def stream(self, messages: List[LLMMessage], config: LLMConfig) -> AsyncGenerator[LLMResponse, None]:
        start_time = time.time()
        
        if not self.api_key:
            yield LLMResponse(
                content=f"[MOCK GEMINI STREAM] Answer to: {messages[-1].content}",
                model=config.model,
                provider="gemini",
                latency_ms=(time.time() - start_time) * 1000
            )
            return

        model_name = config.model
        url = f"{self.base_url}/{model_name}:streamGenerateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        system_instruction = None
        system_text = config.system_prompt or ""
        for m in messages:
            if m.role == "system":
                system_text += "\n" + m.content
        if system_text.strip():
            system_instruction = {"parts": [{"text": system_text.strip()}]}

        payload = {
            "contents": self._convert_messages(messages),
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if config.json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        # Gemini returns SSE or raw JSON chunks in stream
                        if not line.strip():
                            continue
                        
                        # Strip formatting wrappers if any
                        line_cleaned = line.strip().lstrip("[").rstrip(",").strip()
                        if line_cleaned == "]":
                            break
                            
                        try:
                            chunk = json.loads(line_cleaned)
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    text_piece = p.get("text", "")
                                    if text_piece:
                                        yield LLMResponse(
                                            content=text_piece,
                                            model=config.model,
                                            provider="gemini"
                                        )
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise RuntimeError(f"Gemini stream failed: {e}")

    def embeddings(self, text: str) -> List[float]:
        if not self.api_key:
            return [0.0] * 768

        url = f"{self.base_url}/text-embedding-004:embedContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "content": {"parts": [{"text": text}]}
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
            return data["embedding"]["values"]
        except Exception as e:
            logger.error(f"Gemini Embeddings error: {e}")
            raise RuntimeError(f"Gemini embeddings extraction failed: {e}")
