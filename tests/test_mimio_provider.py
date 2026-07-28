"""
NORAY — Xiaomi MiMo Provider Validation Tests

Verifies DNS resolution, HTTPS connectivity, endpoint validation,
structured error handling, and retry behavior for the MiMo provider.
"""

import socket
from unittest.mock import MagicMock, patch

import httpx
import pytest

from noray.llm.providers.mimio_provider import (
    ProviderDiagnostics,
    ProviderHealthState,
    MimioProvider,
    _classify_error,
    _is_non_retryable,
)


# ─── Error Classification Tests ────────────────────────────

class TestErrorClassification:
    def test_dns_error_classified(self):
        assert _classify_error("Failed to resolve 'api.mimio.ai'") == "DNS resolution failed"

    def test_connection_refused_classified(self):
        assert _classify_error("Connection refused") == "Connection refused"

    def test_ssl_error_classified(self):
        assert _classify_error("SSL certificate verify failed") == "TLS/SSL error"

    def test_auth_error_classified(self):
        assert _classify_error("401 Unauthorized") == "Authentication failed"

    def test_rate_limit_classified(self):
        assert _classify_error("429 Too Many Requests") == "Quota exceeded"

    def test_timeout_classified(self):
        assert _classify_error("Request timed out") == "Timeout"

    def test_server_error_classified(self):
        assert _classify_error("500 Internal Server Error") == "Server error"

    def test_non_retryable_dns(self):
        assert _is_non_retryable("Failed to resolve hostname") is True

    def test_non_retryable_auth(self):
        assert _is_non_retryable("401 Unauthorized") is True

    def test_non_retryable_forbidden(self):
        assert _is_non_retryable("403 Forbidden") is True

    def test_retryable_timeout(self):
        assert _is_non_retryable("Request timed out") is False

    def test_retryable_server_error(self):
        assert _is_non_retryable("503 Service Unavailable") is False


# ─── Provider Initialization Tests ─────────────────────────

class TestProviderInit:
    def test_default_endpoint(self):
        provider = MimioProvider()
        assert provider.base_url == "https://api.xiaomimimo.com/v1"

    def test_custom_endpoint(self):
        provider = MimioProvider(base_url="https://custom.example.com/v1")
        assert provider.base_url == "https://custom.example.com/v1"

    def test_trailing_slash_stripped(self):
        provider = MimioProvider(base_url="https://example.com/v1/")
        assert provider.base_url == "https://example.com/v1"

    def test_no_default_api_key(self):
        provider = MimioProvider()
        assert provider.api_key == ""

    def test_custom_api_key(self):
        provider = MimioProvider(api_key="test-key-123")
        assert provider.api_key == "test-key-123"


# ─── Health Check Tests ────────────────────────────────────

class TestHealthCheck:
    def test_health_returns_false_without_key(self):
        provider = MimioProvider(api_key="", base_url="https://example.com/v1")
        assert provider.health() is False
        assert provider.status.health_state == ProviderHealthState.DISABLED

    def test_health_returns_false_without_url(self):
        provider = MimioProvider(api_key="test-key", base_url="")
        assert provider.health() is False


# ─── Endpoint Validation Tests ─────────────────────────────

class TestEndpointValidation:
    def test_validation_no_url(self):
        provider = MimioProvider(api_key="test-key", base_url="not-a-url")
        diag = provider.validate_endpoint()
        assert diag.health_state == ProviderHealthState.UNHEALTHY

    def test_validation_no_key(self):
        provider = MimioProvider(api_key="", base_url="https://example.com/v1")
        diag = provider.validate_endpoint()
        assert diag.health_state == ProviderHealthState.DISABLED
        assert diag.auth_error == "API key not configured"

    def test_validation_dns_failure(self):
        provider = MimioProvider(api_key="test-key", base_url="https://nonexistent.invalid.xyz/v1")
        with patch("socket.getaddrinfo", side_effect=socket.gaierror("Name resolution failed")):
            diag = provider.validate_endpoint()
        assert diag.health_state == ProviderHealthState.UNHEALTHY
        assert diag.dns_resolved is False
        assert "DNS resolution failed" in provider.status.last_error

    @patch("noray.llm.providers.mimio_provider.httpx.Client")
    def test_validation_auth_failure(self, mock_client_cls):
        provider = MimioProvider(api_key="invalid-key", base_url="https://api.xiaomimimo.com/v1")

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.get.return_value = mock_response

        with patch("socket.getaddrinfo"):
            diag = provider.validate_endpoint()

        assert diag.https_reachable is True
        assert diag.auth_valid is False
        assert "Invalid API key" in diag.auth_error
        assert provider.status.api_key_valid is False

    @patch("noray.llm.providers.mimio_provider.httpx.Client")
    def test_validation_success(self, mock_client_cls):
        provider = MimioProvider(api_key="valid-key", base_url="https://api.xiaomimimo.com/v1")

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "mimo-v2.5-pro"}, {"id": "mimo-v2-flash"}]
        }
        mock_client.get.return_value = mock_response

        with patch("socket.getaddrinfo"):
            diag = provider.validate_endpoint()

        assert diag.endpoint_healthy is True
        assert diag.health_state == ProviderHealthState.HEALTHY
        assert diag.auth_valid is True
        assert "mimo-v2.5-pro" in diag.models_available
        assert provider.status.api_key_valid is True


# ─── Generation Error Handling Tests ───────────────────────

class TestGenerateErrorHandling:
    def _make_provider(self, api_key="test-key", base_url="https://api.xiaomimimo.com/v1"):
        return MimioProvider(api_key=api_key, base_url=base_url)

    def test_generate_no_key_returns_structured_error(self):
        provider = MimioProvider(api_key="", base_url="https://api.xiaomimimo.com/v1")
        from noray.llm.providers.base_provider import LLMConfig, LLMMessage

        messages = [LLMMessage(role="user", content="Hello")]
        config = LLMConfig(model="mimo-v2.5-pro")
        response = provider.generate(messages, config)

        assert response.finish_reason == "error"
        assert "API key is not configured" in response.content
        assert provider.status.failed_calls == 1

    def test_generate_no_url_returns_structured_error(self):
        provider = MimioProvider(api_key="test-key", base_url="https://nonexistent.invalid/v1")
        from noray.llm.providers.base_provider import LLMConfig, LLMMessage

        with patch("noray.llm.providers.mimio_provider.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ConnectError("Failed to resolve hostname")

            messages = [LLMMessage(role="user", content="Hello")]
            config = LLMConfig(model="mimo-v2.5-pro")
            response = provider.generate(messages, config)

            assert response.finish_reason == "error"
            assert "Cannot reach MiMo endpoint" in response.content

    @patch("noray.llm.providers.mimio_provider.httpx.Client")
    def test_generate_auth_error_returns_structured_message(self, mock_client_cls):
        provider = self._make_provider()

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=mock_response
        )
        mock_client.post.return_value = mock_response

        from noray.llm.providers.base_provider import LLMConfig, LLMMessage
        messages = [LLMMessage(role="user", content="Hello")]
        config = LLMConfig(model="mimo-v2.5-pro")
        response = provider.generate(messages, config)

        assert response.finish_reason == "error"
        assert "Authentication failed" in response.content
        assert provider.status.api_key_valid is False

    @patch("noray.llm.providers.mimio_provider.httpx.Client")
    def test_generate_connection_error_returns_structured_message(self, mock_client_cls):
        provider = self._make_provider()

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = httpx.ConnectError("Failed to resolve hostname")

        from noray.llm.providers.base_provider import LLMConfig, LLMMessage
        messages = [LLMMessage(role="user", content="Hello")]
        config = LLMConfig(model="mimo-v2.5-pro")
        response = provider.generate(messages, config)

        assert response.finish_reason == "error"
        assert "Cannot reach MiMo endpoint" in response.content
        assert "DNS resolution failed" in response.content

    @patch("noray.llm.providers.mimio_provider.httpx.Client")
    def test_generate_success(self, mock_client_cls):
        provider = self._make_provider()

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello from MiMo!"}}],
            "model": "mimo-v2.5-pro",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        mock_client.post.return_value = mock_response

        from noray.llm.providers.base_provider import LLMConfig, LLMMessage
        messages = [LLMMessage(role="user", content="Hello")]
        config = LLMConfig(model="mimo-v2.5-pro")
        response = provider.generate(messages, config)

        assert response.content == "Hello from MiMo!"
        assert response.finish_reason == "stop"
        assert provider.status.successful_calls == 1
        assert provider.status.last_error == ""


# ─── Status API Tests ──────────────────────────────────────

class TestStatusAPI:
    def test_get_status_dict(self):
        provider = MimioProvider(api_key="test", base_url="https://example.com/v1")
        status_dict = provider.get_status_dict()

        assert "provider_name" in status_dict
        assert "base_url" in status_dict
        assert "health_state" in status_dict
        assert "diagnostics" in status_dict
        assert status_dict["provider_name"] == "mimio"

    def test_diagnostics_to_dict(self):
        diag = ProviderDiagnostics(base_url="https://example.com/v1")
        d = diag.to_dict()
        assert d["base_url"] == "https://example.com/v1"
        assert d["dns_resolved"] is False
        assert d["endpoint_healthy"] is False
