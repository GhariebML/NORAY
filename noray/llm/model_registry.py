import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("noray.llm.model_registry")

class ModelMetadata(BaseModel):
    """Metadata representing capabilities and specifications of an LLM."""
    provider: str
    model: str
    context_window: int = 4096
    supports_vision: bool = False
    supports_tools: bool = False
    supports_streaming: bool = True
    supports_embeddings: bool = False
    cost_input_per_m: float = 0.0  # Cost per 1 Million input tokens in USD
    cost_output_per_m: float = 0.0  # Cost per 1 Million output tokens in USD
    reasoning_score: float = 0.5  # Scale 0.0 - 1.0 (quality of thought/logic)
    coding_score: float = 0.5  # Scale 0.0 - 1.0 (coding proficiency)
    speed_score: float = 0.5  # Scale 0.0 - 1.0 (tokens per second)
    offline_capable: bool = False
    health_status: str = "Healthy"  # "Healthy" | "Quarantined" | "Unavailable"
    last_latency_ms: float = 0.0
    last_success: bool = True


class ModelRegistry:
    """Central registry maintaining capabilities of all supported models in NORAY."""
    
    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._populate_defaults()

    def register(self, metadata: ModelMetadata) -> None:
        """Register a new model in the registry."""
        key = f"{metadata.provider}:{metadata.model}".lower()
        self._models[key] = metadata
        # Also map standard model name direct lookups
        self._models[metadata.model.lower()] = metadata

    def get_model(self, model_name: str, provider_name: Optional[str] = None) -> Optional[ModelMetadata]:
        """Lookup model metadata by model name or provider:model key."""
        if provider_name:
            key = f"{provider_name}:{model_name}".lower()
            return self._models.get(key)
        
        # Try direct key lookup
        direct_key = model_name.lower()
        if direct_key in self._models:
            return self._models[direct_key]
            
        # Linear search by model name if key wasn't formatted as provider:model
        for key, meta in self._models.items():
            if meta.model.lower() == model_name.lower():
                return meta
        return None

    def list_models(self) -> List[ModelMetadata]:
        """Return all unique registered model metadatas."""
        seen = set()
        unique_models = []
        for meta in self._models.values():
            key = f"{meta.provider}:{meta.model}".lower()
            if key not in seen:
                seen.add(key)
                unique_models.append(meta)
        return unique_models

    def get_models_by_provider(self, provider_name: str) -> List[ModelMetadata]:
        """List all models registered under a specific provider."""
        return [m for m in self.list_models() if m.provider.lower() == provider_name.lower()]

    def _populate_defaults(self) -> None:
        # ─── Local Ollama Models ───
        self.register(ModelMetadata(
            provider="ollama", model="qwen2.5:7b",
            context_window=32768, supports_tools=True, reasoning_score=0.6, coding_score=0.65, speed_score=0.8,
            offline_capable=True
        ))
        self.register(ModelMetadata(
            provider="ollama", model="qwen2.5-coder:7b",
            context_window=32768, supports_tools=True, reasoning_score=0.65, coding_score=0.85, speed_score=0.8,
            offline_capable=True
        ))
        self.register(ModelMetadata(
            provider="ollama", model="llama3.1:8b",
            context_window=128000, supports_tools=True, reasoning_score=0.7, coding_score=0.6, speed_score=0.75,
            offline_capable=True
        ))
        self.register(ModelMetadata(
            provider="ollama", model="deepseek-r1:8b",
            context_window=16384, supports_tools=False, reasoning_score=0.75, coding_score=0.5, speed_score=0.5,
            offline_capable=True
        ))
        self.register(ModelMetadata(
            provider="ollama", model="nomic-embed-text",
            context_window=8192, supports_embeddings=True, reasoning_score=0.0, coding_score=0.0, speed_score=0.9,
            offline_capable=True
        ))

        # ─── OpenAI Models ───
        self.register(ModelMetadata(
            provider="openai", model="gpt-4o-mini",
            context_window=128000, supports_tools=True, supports_vision=True,
            cost_input_per_m=0.150, cost_output_per_m=0.600, reasoning_score=0.75, coding_score=0.75, speed_score=0.85
        ))
        self.register(ModelMetadata(
            provider="openai", model="gpt-4o",
            context_window=128000, supports_tools=True, supports_vision=True,
            cost_input_per_m=2.50, cost_output_per_m=10.00, reasoning_score=0.92, coding_score=0.9, speed_score=0.7
        ))
        self.register(ModelMetadata(
            provider="openai", model="text-embedding-3-small",
            context_window=8192, supports_embeddings=True, reasoning_score=0.0, coding_score=0.0, speed_score=0.9
        ))

        # ─── Anthropic Models ───
        self.register(ModelMetadata(
            provider="anthropic", model="claude-3-5-sonnet-20241022",
            context_window=200000, supports_tools=True, supports_vision=True,
            cost_input_per_m=3.00, cost_output_per_m=15.00, reasoning_score=0.96, coding_score=0.98, speed_score=0.65
        ))

        # ─── Google Gemini Models ───
        self.register(ModelMetadata(
            provider="gemini", model="gemini-1.5-flash",
            context_window=1048576, supports_tools=True, supports_vision=True,
            cost_input_per_m=0.075, cost_output_per_m=0.300, reasoning_score=0.78, coding_score=0.72, speed_score=0.9
        ))
        self.register(ModelMetadata(
            provider="gemini", model="gemini-1.5-pro",
            context_window=2097152, supports_tools=True, supports_vision=True,
            cost_input_per_m=1.25, cost_output_per_m=5.00, reasoning_score=0.93, coding_score=0.88, speed_score=0.55
        ))

        # ─── DeepSeek Models ───
        self.register(ModelMetadata(
            provider="deepseek", model="deepseek-chat",
            context_window=64000, supports_tools=True,
            cost_input_per_m=0.14, cost_output_per_m=0.28, reasoning_score=0.82, coding_score=0.92, speed_score=0.8
        ))
        self.register(ModelMetadata(
            provider="deepseek", model="deepseek-reasoner",
            context_window=64000, supports_tools=False,
            cost_input_per_m=0.55, cost_output_per_m=2.19, reasoning_score=0.95, coding_score=0.85, speed_score=0.3
        ))

        # ─── OpenRouter Auto Routing ───
        self.register(ModelMetadata(
            provider="openrouter", model="openrouter/auto",
            context_window=128000, supports_tools=True, reasoning_score=0.8, coding_score=0.8, speed_score=0.7
        ))

        # ─── Mistral Models ───
        self.register(ModelMetadata(
            provider="mistral", model="mistral-large-latest",
            context_window=128000, supports_tools=True,
            cost_input_per_m=2.0, cost_output_per_m=6.0, reasoning_score=0.88, coding_score=0.85, speed_score=0.6
        ))

        # ─── Together AI Models ───
        self.register(ModelMetadata(
            provider="together", model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            context_window=128000, supports_tools=True, reasoning_score=0.6, coding_score=0.6, speed_score=0.85
        ))

# Global registry instance
model_registry = ModelRegistry()
