"""
NORAY — Tools & MCP Package

Implements a hybrid tool registry:
1. Built-in Tools: standard out-of-the-box tools for local filesystem,
   PostgreSQL database, Qdrant search, PDF parsing, document managers,
   and local search indexing.
2. MCP Client Adapter: standard JSON-RPC interface to dynamically discover,
   load, and call tools exposed by external Model Context Protocol (MCP) servers.
"""

from noray.agents.tools.builtins import BuiltinToolRegistry, ToolDefinition
from noray.agents.tools.mcp_adapter import McpClientAdapter

__all__ = [
    "BuiltinToolRegistry",
    "ToolDefinition",
    "McpClientAdapter",
]
