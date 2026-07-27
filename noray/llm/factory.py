"""
NORAY — LLM Provider Factory
Instantiates and pools LLM provider connections dynamically.
Integrates with the SmartRouter for enterprise-grade routing.
"""

from __future__ import annotations

import os

from noray.llm.providers.anthropic_provider import AnthropicProvider
from noray.llm.providers.base_provider import BaseLLMProvider
from noray.llm.providers.deepseek_provider import DeepSeekProvider
from noray.llm.providers.gemini_provider import GeminiProvider
from noray.llm.providers.mimio_provider import MimioProvider
from noray.llm.providers.mistral_provider import MistralProvider
from noray.llm.providers.ollama_provider import OllamaProvider
from noray.llm.providers.openai_provider import OpenAIProvider
from noray.llm.providers.openrouter_provider import OpenRouterProvider
from noray.llm.providers.together_provider import TogetherProvider


class LLMProviderFactory:
    """Factory creating and caching instances of specific LLM Providers."""

    _instances: dict[str, BaseLLMProvider] = {}

    @classmethod
    def get_provider(cls, provider_name: str) -> BaseLLMProvider:
        """Returns a cached provider instance or instantiates a new one."""
        name = provider_name.lower().strip()

        if name in cls._instances:
            return cls._instances[name]

        from noray.config import settings

        if name in ["mimio", "xiaomi", "default"]:
            provider = MimioProvider(api_key=settings.MIMIO_API_KEY, base_url=settings.MIMIO_BASE_URL)
        elif name == "openai":
            provider = OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        elif name == "anthropic":
            provider = AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
        elif name == "gemini":
            provider = GeminiProvider(api_key=settings.GOOGLE_API_KEY)
        elif name in ["local", "ollama"]:
            provider = OllamaProvider(base_url=settings.OLLAMA_BASE_URL)
        elif name == "openrouter":
            provider = OpenRouterProvider(api_key=settings.OPENROUTER_API_KEY)
        elif name == "deepseek":
            provider = DeepSeekProvider(api_key=settings.DEEPSEEK_API_KEY)
        elif name == "mistral":
            provider = MistralProvider(api_key=settings.MISTRAL_API_KEY)
        elif name == "together":
            provider = TogetherProvider(api_key=settings.TOGETHER_API_KEY)
        elif name == "groq":
            groq_key = getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
            provider = OpenAIProvider(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
        elif name == "huggingface":
            hf_key = getattr(settings, "HUGGINGFACE_API_KEY", "") or os.getenv("HUGGINGFACE_API_KEY", "")
            provider = OpenAIProvider(api_key=hf_key, base_url="https://api-inference.huggingface.co/v1")
        else:
            provider = OllamaProvider(base_url=settings.OLLAMA_BASE_URL)

        cls._instances[name] = provider
        return provider

    @classmethod
    def get_smart_router(cls):
        """Get the global SmartRouter singleton."""
        from noray.llm.smart_router import smart_router
        return smart_router

    @classmethod
    def reset_instances(cls) -> None:
        """Clear all cached provider instances (useful for testing)."""
        cls._instances.clear()
