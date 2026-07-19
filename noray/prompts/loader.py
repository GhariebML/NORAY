"""
NORAY — Prompt Loader Service
Handles version selection, caching, validation, and variable rendering for prompt templates.
"""

from __future__ import annotations
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from noray.cache.redis_cache import RedisCache
from noray.config import PROJECT_ROOT


class PromptLoader:
    """PromptLoader loads, validates, caches, and renders system prompts from versioned YAML files."""
    
    def __init__(self, cache: Optional[RedisCache] = None):
        self.prompts_dir = PROJECT_ROOT / "noray" / "prompts"
        self.cache = cache or RedisCache(namespace="noray_prompts")

    def get_prompt_path(self, category: str, version: str) -> Path:
        return self.prompts_dir / category / f"{version}.yaml"

    def load_prompt(self, category: str, version: str = "v1") -> Dict[str, Any]:
        """Loads and parses prompt template from disk or Redis cache."""
        cache_key = f"{category}:{version}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        file_path = self.get_prompt_path(category, version)
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse prompt template YAML {file_path}: {e}")

        # Validate basic schema
        required_keys = ["id", "version", "variables", "template"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Invalid prompt template schema at {file_path}. Missing: {key}")

        self.cache.set(cache_key, data, ttl=3600)  # cache for 1 hour
        return data

    def render(self, category: str, variables: Dict[str, Any], version: str = "v1") -> str:
        """Renders the template replacing double curly brace variables with values."""
        prompt_data = self.load_prompt(category, version)
        required_vars = prompt_data.get("variables", [])
        
        # Verify variables
        missing = [v for v in required_vars if v not in variables]
        if missing:
            # Log warning or handle gracefully
            pass
            
        template: str = prompt_data["template"]
        rendered = template
        for k, v in variables.items():
            placeholder = f"{{{{{k}}}}}"
            rendered = rendered.replace(placeholder, str(v) if v is not None else "")
            
        return rendered
