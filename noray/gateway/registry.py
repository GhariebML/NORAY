"""
NORAY — Model Registry Database

Holds configuration capabilities, costs, requirements, and health tracking
status metadata for local and cloud models.
"""

from __future__ import annotations

from pydantic import BaseModel


class ModelMetadata(BaseModel):
    """Metadata detailing capabilities, costs, and availability of an LLM."""
    name: str
    provider: str  # "local" (Ollama/LMStudio), "openai", "anthropic", "gemini"
    context_window: int = 4096
    supports_tools: bool = False
    supports_json: bool = False
    supports_reasoning: bool = False
    input_cost_per_1k: float = 0.0  # In USD
    output_cost_per_1k: float = 0.0  # In USD
    memory_usage_gb: float = 0.0
    gpu_required: bool = False
    priority: int = 100  # Lower number = higher priority
    is_available: bool = True


# Standard pre-registered model definitions
DEFAULT_REGISTRY: dict[str, ModelMetadata] = {
    # --- Primary Cloud Models (Xiaomi Mimio) ---
    "mimio-1.0": ModelMetadata(
        name="mimio-1.0",
        provider="mimio",
        context_window=128000,
        supports_tools=True,
        supports_json=True,
        supports_reasoning=True,
        input_cost_per_1k=0.00005,
        output_cost_per_1k=0.00015,
        priority=1
    ),

    # --- Fallback Cloud Models (Google Gemini) ---
    "gemini-1.5-flash": ModelMetadata(
        name="gemini-1.5-flash",
        provider="gemini",
        context_window=1048576,
        supports_tools=True,
        supports_json=True,
        input_cost_per_1k=0.000075,
        output_cost_per_1k=0.0003,
        priority=2
    ),

    # --- Cloud Models (OpenRouter / Aggregated) ---
    "openrouter/auto": ModelMetadata(
        name="openrouter/auto",
        provider="openrouter",
        context_window=128000,
        supports_tools=True,
        supports_json=True,
        priority=3
    ),

    # --- Cloud Models (Together AI) ---
    "together/llama-3-70b": ModelMetadata(
        name="together/llama-3-70b",
        provider="together",
        context_window=8192,
        supports_tools=True,
        priority=4
    ),

    # --- Cloud / API Models (DeepSeek) ---
    "deepseek-chat": ModelMetadata(
        name="deepseek-chat",
        provider="deepseek",
        context_window=64000,
        supports_reasoning=True,
        supports_tools=True,
        priority=5
    ),

    # --- Local Models (Ollama) ---
    "gemma2:2b": ModelMetadata(
        name="gemma2:2b",
        provider="local",
        context_window=8192,
        supports_tools=True,
        supports_json=True,
        memory_usage_gb=2.0,
        gpu_required=False,
        priority=6
    ),
    "qwen2.5-coder:7b": ModelMetadata(
        name="qwen2.5-coder:7b",
        provider="local",
        context_window=32768,
        supports_tools=True,
        supports_json=True,
        memory_usage_gb=6.0,
        gpu_required=True,
        priority=7
    ),
    "llama3:8b": ModelMetadata(
        name="llama3:8b",
        provider="local",
        context_window=8192,
        supports_tools=True,
        supports_json=True,
        memory_usage_gb=6.5,
        gpu_required=True,
        priority=7
    ),
    "deepseek-r1:7b": ModelMetadata(
        name="deepseek-r1:7b",
        provider="local",
        context_window=16384,
        supports_reasoning=True,
        memory_usage_gb=6.0,
        priority=8
    ),

    # --- Cloud Models (OpenAI & Anthropic) ---
    "gpt-4o-mini": ModelMetadata(
        name="gpt-4o-mini",
        provider="openai",
        context_window=128000,
        supports_tools=True,
        supports_json=True,
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
        priority=10
    ),
    "claude-3-5-sonnet-20241022": ModelMetadata(
        name="claude-3-5-sonnet-20241022",
        provider="anthropic",
        context_window=200000,
        supports_tools=True,
        supports_json=True,
        supports_reasoning=True,
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
        priority=20
    )
}


class ModelRegistry:
    """Manages registered models metadata and tracks current health/latencies."""

    def __init__(self) -> None:
        self.models = DEFAULT_REGISTRY.copy()

        # Detect locally installed Ollama models
        installed = []
        try:
            import subprocess
            out = subprocess.check_output(["ollama", "list"], text=True, stderr=subprocess.DEVNULL).split("\n")
            for line in out[1:]:
                parts = line.split()
                if parts:
                    installed.append(parts[0])
        except Exception:
            pass

        installed_clean = [m.split(":")[0] for m in installed]

        for name, meta in list(self.models.items()):
            if meta.provider == "local":
                clean_name = name.split(":")[0]
                if name in installed or clean_name in installed_clean:
                    meta.is_available = True
                else:
                    meta.is_available = False

    def register(self, model: ModelMetadata) -> None:
        """Register a new custom model in the registry."""
        self.models[model.name] = model

    def get(self, name: str) -> ModelMetadata | None:
        """Fetch metadata for a given model name."""
        return self.models.get(name)

    def list_models(self) -> dict[str, ModelMetadata]:
        """List all registered models metadata."""
        return self.models
