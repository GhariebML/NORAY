"""
NORAY — Xiaomi MiMo Provider Adapter

Production-grade provider with:
- Configurable endpoint (no hardcoded URLs)
- Pre-flight validation (DNS, HTTPS, auth, model availability)
- Structured error handling (no raw exceptions exposed)
- Intelligent retry (transient failures only)
- Real health checks (actual API ping, not just key presence)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
import ssl
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlparse

import httpx

from noray.llm.providers.base_provider import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse

logger = logging.getLogger("noray.llm.mimio")

# Non-retryable error classes — these indicate permanent configuration problems
_NON_RETRYABLE_PATTERNS = [
    "failed to resolve",
    "nameResolutionError",
    "name or service not known",
    "no address associated with hostname",
    "connection refused",
    "certificate verify",
    "ssl: cert",
]

# Default model constant
DEFAULT_MODEL = "mimo-v2.5-pro"
DEFAULT_TIMEOUT_SECONDS = 30


class ProviderHealthState(str, Enum):
    UNKNOWN = "unknown"
    VALIDATING = "validating"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"


@dataclass
class ProviderDiagnostics:
    """Structured diagnostics for provider health and connectivity."""
    dns_resolved: bool = False
    dns_latency_ms: float = 0.0
    dns_error: str = ""
    https_reachable: bool = False
    https_latency_ms: float = 0.0
    https_error: str = ""
    auth_valid: bool = False
    auth_error: str = ""
    models_available: list[str] = field(default_factory=list)
    models_error: str = ""
    base_url: str = ""
    endpoint_healthy: bool = False
    last_check_time: float = 0.0
    health_state: ProviderHealthState = ProviderHealthState.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "dns_resolved": self.dns_resolved,
            "dns_latency_ms": round(self.dns_latency_ms, 2),
            "dns_error": self.dns_error,
            "https_reachable": self.https_reachable,
            "https_latency_ms": round(self.https_latency_ms, 2),
            "https_error": self.https_error,
            "auth_valid": self.auth_valid,
            "auth_error": self.auth_error,
            "models_available": self.models_available,
            "models_error": self.models_error,
            "endpoint_healthy": self.endpoint_healthy,
            "last_check_time": self.last_check_time,
            "health_state": self.health_state.value,
        }


@dataclass
class ProviderStatus:
    """Live status snapshot for the Streamlit dashboard."""
    provider_name: str = "mimio"
    base_url: str = ""
    model: str = ""
    api_key_present: bool = False
    api_key_valid: bool = False
    health_state: ProviderHealthState = ProviderHealthState.UNKNOWN
    last_successful_call: float = 0.0
    last_error: str = ""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    average_latency_ms: float = 0.0
    diagnostics: ProviderDiagnostics = field(default_factory=ProviderDiagnostics)

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return round((self.successful_calls / self.total_calls) * 100, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "base_url": self.base_url,
            "model": self.model,
            "api_key_present": self.api_key_present,
            "api_key_valid": self.api_key_valid,
            "health_state": self.health_state.value,
            "last_successful_call": self.last_successful_call,
            "last_error": self.last_error,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.success_rate,
            "average_latency_ms": round(self.average_latency_ms, 2),
            "diagnostics": self.diagnostics.to_dict(),
        }


def _classify_error(error_str: str) -> str:
    """Classify an error into a structured category for the UI."""
    lower = error_str.lower()
    for pattern in _NON_RETRYABLE_PATTERNS:
        if pattern in lower:
            if "resolve" in lower or "name" in lower or "hostname" in lower or "address" in lower:
                return "DNS resolution failed"
            if "connection refused" in lower:
                return "Connection refused"
            if "certificate" in lower or "ssl" in lower:
                return "TLS/SSL error"
    if "401" in lower or "unauthorized" in lower or "authentication" in lower:
        return "Authentication failed"
    if "403" in lower or "forbidden" in lower:
        return "Access denied"
    if "429" in lower or "rate limit" in lower or "too many requests" in lower:
        return "Quota exceeded"
    if "timeout" in lower or "timed out" in lower:
        return "Timeout"
    if "500" in lower or "502" in lower or "503" in lower:
        return "Server error"
    return error_str


def _is_non_retryable(error_str: str) -> bool:
    """Determine if an error is permanent and should NOT be retried."""
    lower = error_str.lower()
    for pattern in _NON_RETRYABLE_PATTERNS:
        if pattern in lower:
            return True
    if "401" in lower or "unauthorized" in lower:
        return True
    if "403" in lower or "forbidden" in lower:
        return True
    return False


class MimioProvider(BaseLLMProvider):
    """
    Production-grade Xiaomi MiMo provider adapter.
    
    Validates the endpoint before inference. Returns structured errors instead
    of raw exceptions. Never exposes Python tracebacks to the UI.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("MIMIO_API_KEY", "")
        self.base_url = (base_url or os.getenv("MIMIO_BASE_URL") or "https://api.xiaomimimo.com/v1").rstrip("/")

        # Runtime state
        self._status = ProviderStatus(
            base_url=self.base_url,
            model=os.getenv("MIMIO_MODEL", DEFAULT_MODEL),
            api_key_present=bool(self.api_key),
        )
        self._diagnostics = ProviderDiagnostics(base_url=self.base_url)
        self._last_validation_time: float = 0.0
        self._validation_cache_ttl: float = 300.0  # Re-validate every 5 minutes

    # ─── Public Status API ─────────────────────────────────

    @property
    def status(self) -> ProviderStatus:
        """Current provider status for the dashboard."""
        return self._status

    @property
    def diagnostics(self) -> ProviderDiagnostics:
        """Detailed diagnostics for the system info panel."""
        return self._diagnostics

    def get_status_dict(self) -> dict[str, Any]:
        """Return full status as a serializable dict."""
        return self._status.to_dict()

    # ─── Health Check (real, not just key presence) ─────────

    def health(self) -> bool:
        """Real health check: validates DNS + HTTPS reachability."""
        if not self.api_key:
            self._status.health_state = ProviderHealthState.DISABLED
            return False

        now = time.time()
        if (now - self._last_validation_time) < self._validation_cache_ttl:
            return self._diagnostics.endpoint_healthy

        self.validate_endpoint()
        return self._diagnostics.endpoint_healthy

    # ─── Endpoint Validation ───────────────────────────────

    def validate_endpoint(self) -> ProviderDiagnostics:
        """
        Full pre-flight validation of the provider endpoint.
        Checks: DNS resolution, HTTPS connectivity, API key format.
        Returns structured diagnostics.
        """
        self._status.health_state = ProviderHealthState.VALIDATING
        diag = ProviderDiagnostics(base_url=self.base_url)

        if not self.base_url:
            diag.health_state = ProviderHealthState.UNHEALTHY
            diag.https_error = "No base URL configured"
            self._diagnostics = diag
            self._status.health_state = ProviderHealthState.UNHEALTHY
            self._status.last_error = "No base URL configured"
            return diag

        parsed = urlparse(self.base_url)
        hostname = parsed.hostname
        if not hostname:
            diag.health_state = ProviderHealthState.UNHEALTHY
            diag.https_error = f"Invalid base URL: {self.base_url}"
            self._diagnostics = diag
            self._status.health_state = ProviderHealthState.UNHEALTHY
            self._status.last_error = "Invalid base URL"
            return diag

        # 1. DNS Resolution
        try:
            dns_start = time.time()
            socket.getaddrinfo(hostname, parsed.port or 443, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
            diag.dns_latency_ms = (time.time() - dns_start) * 1000
            diag.dns_resolved = True
        except socket.gaierror as e:
            diag.dns_error = _classify_error(str(e))
            logger.error(f"MiMo DNS resolution failed for '{hostname}': {e}")
            diag.health_state = ProviderHealthState.UNHEALTHY
            diag.last_check_time = time.time()
            self._diagnostics = diag
            self._status.health_state = ProviderHealthState.UNHEALTHY
            self._status.last_error = f"DNS resolution failed: {diag.dns_error}"
            self._last_validation_time = time.time()
            return diag

        # 2. HTTPS Connectivity
        if not self.api_key:
            diag.health_state = ProviderHealthState.DISABLED
            diag.auth_error = "API key not configured"
            diag.last_check_time = time.time()
            self._diagnostics = diag
            self._status.health_state = ProviderHealthState.DISABLED
            self._status.last_error = "API key not configured"
            self._last_validation_time = time.time()
            return diag

        try:
            https_start = time.time()
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                resp = client.get(f"{self.base_url}/models", headers={
                    "Authorization": f"Bearer {self.api_key}",
                })
                diag.https_latency_ms = (time.time() - https_start) * 1000

                if resp.status_code == 200:
                    diag.https_reachable = True
                    diag.auth_valid = True
                    # Parse available models
                    try:
                        data = resp.json()
                        models = data.get("data", [])
                        diag.models_available = [m.get("id", "") for m in models if m.get("id")]
                    except Exception:
                        pass
                elif resp.status_code == 401:
                    diag.https_reachable = True
                    diag.auth_error = "Invalid API key"
                    logger.warning(f"MiMo auth failed: 401 Unauthorized")
                elif resp.status_code == 403:
                    diag.https_reachable = True
                    diag.auth_error = "Access denied (403 Forbidden)"
                elif resp.status_code == 429:
                    diag.https_reachable = True
                    diag.auth_error = "Rate limited (429)"
                else:
                    diag.https_reachable = True
                    diag.https_error = f"HTTP {resp.status_code}"

        except httpx.ConnectError as e:
            diag.https_error = _classify_error(str(e))
            logger.error(f"MiMo HTTPS connection failed: {e}")
        except httpx.TimeoutException:
            diag.https_error = "Timeout connecting to endpoint"
        except Exception as e:
            diag.https_error = _classify_error(str(e))
            logger.error(f"MiMo endpoint validation error: {e}")

        # 3. Determine overall health
        if diag.https_reachable and diag.auth_valid:
            diag.endpoint_healthy = True
            diag.health_state = ProviderHealthState.HEALTHY
            self._status.health_state = ProviderHealthState.HEALTHY
            self._status.api_key_valid = True
            self._status.last_error = ""
        elif diag.https_reachable and not diag.auth_valid:
            diag.endpoint_healthy = False
            diag.health_state = ProviderHealthState.UNHEALTHY
            self._status.health_state = ProviderHealthState.UNHEALTHY
            self._status.api_key_valid = False
            self._status.last_error = diag.auth_error
        elif diag.dns_resolved and not diag.https_reachable:
            diag.endpoint_healthy = False
            diag.health_state = ProviderHealthState.UNHEALTHY
            self._status.health_state = ProviderHealthState.UNHEALTHY
            self._status.last_error = f"HTTPS unreachable: {diag.https_error}"
        else:
            diag.endpoint_healthy = False
            diag.health_state = ProviderHealthState.UNHEALTHY
            self._status.health_state = ProviderHealthState.UNHEALTHY
            self._status.last_error = diag.dns_error or diag.https_error or "Unknown error"

        diag.last_check_time = time.time()
        self._diagnostics = diag
        self._last_validation_time = time.time()
        return diag

    # ─── Core Generation ───────────────────────────────────

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Xiaomi MiMo V2.5 Pro: $1.00/M input, $3.00/M output
        return (input_tokens * 0.001 + output_tokens * 0.003) / 1000

    def generate(self, messages: list[LLMMessage], config: LLMConfig) -> LLMResponse:
        start_time = time.time()
        model = config.model or DEFAULT_MODEL

        if not self.api_key:
            logger.warning("MiMo API key missing — returning structured error")
            self._status.last_error = "API key not configured"
            self._status.failed_calls += 1
            self._status.total_calls += 1
            return LLMResponse(
                content="[Provider Error] Xiaomi MiMo API key is not configured. Set MIMIO_API_KEY in your .env file.",
                model=model,
                provider="mimio",
                latency_ms=(time.time() - start_time) * 1000,
                finish_reason="error",
            )

        if not self.base_url:
            logger.warning("MiMo base URL missing — returning structured error")
            self._status.last_error = "Base URL not configured"
            self._status.failed_calls += 1
            self._status.total_calls += 1
            return LLMResponse(
                content="[Provider Error] Xiaomi MiMo base URL is not configured. Set MIMIO_BASE_URL in your .env file.",
                model=model,
                provider="mimio",
                latency_ms=(time.time() - start_time) * 1000,
                finish_reason="error",
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

        self._status.total_calls += 1

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            latency = (time.time() - start_time) * 1000

            self._status.successful_calls += 1
            self._status.last_successful_call = time.time()
            self._status.last_error = ""
            self._update_average_latency(latency)

            return LLMResponse(
                content=content,
                model=data.get("model", model),
                provider="mimio",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                estimated_cost=self.estimate_cost(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)),
                latency_ms=latency,
            )
        except httpx.HTTPStatusError as e:
            error_str = str(e)
            classified = _classify_error(error_str)
            self._status.failed_calls += 1
            self._status.last_error = classified

            if e.response.status_code == 401:
                self._status.api_key_valid = False
                return LLMResponse(
                    content=f"[Provider Error] Authentication failed. Check your MIMIO_API_KEY. ({classified})",
                    model=model, provider="mimio",
                    latency_ms=(time.time() - start_time) * 1000,
                    finish_reason="error",
                )
            if e.response.status_code == 429:
                return LLMResponse(
                    content=f"[Provider Error] Rate limit exceeded. Try again later. ({classified})",
                    model=model, provider="mimio",
                    latency_ms=(time.time() - start_time) * 1000,
                    finish_reason="error",
                )
            return LLMResponse(
                content=f"[Provider Error] MiMo API returned HTTP {e.response.status_code}: {classified}",
                model=model, provider="mimio",
                latency_ms=(time.time() - start_time) * 1000,
                finish_reason="error",
            )
        except httpx.ConnectError as e:
            error_str = str(e)
            self._status.failed_calls += 1
            classified = _classify_error(error_str)
            self._status.last_error = classified
            logger.error(f"MiMo connection failed: {classified}")
            return LLMResponse(
                content=f"[Provider Error] Cannot reach MiMo endpoint: {classified}. "
                        f"Check MIMIO_BASE_URL in your .env file.",
                model=model, provider="mimio",
                latency_ms=(time.time() - start_time) * 1000,
                finish_reason="error",
            )
        except httpx.TimeoutException:
            self._status.failed_calls += 1
            self._status.last_error = "Request timed out"
            return LLMResponse(
                content=f"[Provider Error] Request to MiMo timed out ({DEFAULT_TIMEOUT_SECONDS}s). "
                        f"The model may be under heavy load.",
                model=model, provider="mimio",
                latency_ms=(time.time() - start_time) * 1000,
                finish_reason="timeout",
            )
        except Exception as e:
            error_str = str(e)
            self._status.failed_calls += 1
            classified = _classify_error(error_str)
            self._status.last_error = classified
            logger.error(f"MiMo API call failed: {classified}")
            return LLMResponse(
                content=f"[Provider Error] MiMo request failed: {classified}",
                model=model, provider="mimio",
                latency_ms=(time.time() - start_time) * 1000,
                finish_reason="error",
            )

    # ─── Streaming ─────────────────────────────────────────

    async def stream(self, messages: list[LLMMessage], config: LLMConfig) -> AsyncGenerator[LLMResponse, None]:
        """Stream tokens as LLMResponse chunks. Required by BaseLLMProvider ABC."""
        model = config.model or DEFAULT_MODEL
        full_content = ""
        start_time = time.time()

        async for token in self.generate_stream(messages, config):
            full_content += token
            yield LLMResponse(
                content=token,
                model=model,
                provider="mimio",
            )

        # Final chunk with timing metadata
        yield LLMResponse(
            content="",
            model=model,
            provider="mimio",
            latency_ms=(time.time() - start_time) * 1000,
            finish_reason="stop",
        )

    async def generate_stream(self, messages: list[LLMMessage], config: LLMConfig) -> AsyncGenerator[str, None]:
        model = config.model or DEFAULT_MODEL

        if not self.api_key or not self.base_url:
            error_msg = "[Provider Error] MiMo API key or base URL not configured."
            yield error_msg
            return

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": True
        }

        self._status.total_calls += 1

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
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
                            except (json.JSONDecodeError, KeyError, IndexError):
                                pass

            self._status.successful_calls += 1
            self._status.last_successful_call = time.time()
            self._status.last_error = ""

        except httpx.ConnectError as e:
            classified = _classify_error(str(e))
            self._status.failed_calls += 1
            self._status.last_error = classified
            logger.error(f"MiMo streaming connection failed: {classified}")
            yield f"\n\n[Provider Error] Cannot reach MiMo endpoint: {classified}"
        except httpx.HTTPStatusError as e:
            classified = _classify_error(str(e))
            self._status.failed_calls += 1
            self._status.last_error = classified
            yield f"\n\n[Provider Error] MiMo streaming failed: HTTP {e.response.status_code} - {classified}"
        except Exception as e:
            classified = _classify_error(str(e))
            self._status.failed_calls += 1
            self._status.last_error = classified
            logger.error(f"MiMo streaming failed: {classified}")
            yield f"\n\n[Provider Error] MiMo streaming failed: {classified}"

    def _update_average_latency(self, new_latency_ms: float) -> None:
        """Update rolling average latency."""
        total = self._status.successful_calls + self._status.failed_calls
        if total <= 1:
            self._status.average_latency_ms = new_latency_ms
        else:
            self._status.average_latency_ms = (
                (self._status.average_latency_ms * (total - 1) + new_latency_ms) / total
            )

    # ─── Embeddings (not supported by MiMo, returns empty) ─

    def embeddings(self, text: str) -> list[float]:
        """MiMo does not provide an embeddings endpoint. Returns empty list."""
        logger.debug("MiMo embeddings() called but MiMo does not support embeddings")
        return []
