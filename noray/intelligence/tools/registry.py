"""
NORAY — Tool Registry

Manages dynamic registration and discovery of tools (Native, MCP, REST, Python).
Each tool declares its capabilities, permissions, latency, and cost metadata.
"""

from typing import Dict, List, Optional
from noray.intelligence.core import ITool

class ToolMetadata:
    """Metadata for tools to support safe execution and orchestration."""
    def __init__(
        self,
        name: str,
        description: str,
        capabilities: List[str],
        permissions: List[str],
        is_active: bool = True,
        cost_per_use: float = 0.0,
        average_latency_ms: float = 0.0,
        requires_auth: bool = False
    ):
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.permissions = permissions
        self.is_active = is_active
        self.cost_per_use = cost_per_use
        self.average_latency_ms = average_latency_ms
        self.requires_auth = requires_auth

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ITool] = {}
        self._metadata: Dict[str, ToolMetadata] = {}

    def register(self, tool: ITool, metadata: ToolMetadata) -> None:
        self._tools[tool.name] = tool
        self._metadata[tool.name] = metadata

    def get_tool(self, name: str) -> Optional[ITool]:
        return self._tools.get(name)

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        return self._metadata.get(name)

    def list_tools(self) -> List[ToolMetadata]:
        return list(self._metadata.values())

    def get_tools_for_capability(self, capability: str) -> List[ITool]:
        return [
            self._tools[name]
            for name, meta in self._metadata.items()
            if capability in meta.capabilities and meta.is_active
        ]
