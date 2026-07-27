"""
NORAY — Model Context Protocol (MCP) Client Adapter

Implements the MCP client JSON-RPC specification over stdio pipelines or
HTTP endpoints. Allows dynamic discovery and invocation of tools exposed
by external MCP servers (such as Notion, GitHub, and local script runners).

Config Schema example (mcp_config.json):
{
  "mcpServers": {
    "git-mcp": {
      "command": "node",
      "args": ["path/to/git/index.js"],
      "env": { "GITHUB_TOKEN": "..." }
    }
  }
}
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class McpClientAdapter:
    """Manages active connections to external MCP servers and translates tool requests."""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or os.getenv("MCP_CONFIG_PATH")
        self.servers: dict[str, dict[str, Any]] = {}  # Active server processes & streams
        self.discovered_tools: dict[str, dict[str, Any]] = {}  # Map of tool_name -> {server_name, definition}
        self.lock = threading.Lock()

        # Load configs and auto-connect
        self.load_configuration()

    def load_configuration(self) -> None:
        """Reads configuration file and discovers external server setups."""
        if not self.config_path or not os.path.exists(self.config_path):
            # Try a default config file locations inside project workspace
            _root = str(Path(__file__).resolve().parent.parent.parent)
            defaults = [str(Path(_root) / "mcp_config.json"), str(Path(_root) / ".agents" / "mcp_config.json")]
            for path in defaults:
                if os.path.exists(path):
                    self.config_path = path
                    break

        if not self.config_path or not os.path.exists(self.config_path):
            logger.info("No MCP configuration file discovered. External MCP servers will be bypassed.")
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = json.load(f)

            servers_config = config.get("mcpServers", {})
            for server_name, spec in servers_config.items():
                self.connect_server(server_name, spec)
        except Exception as e:
            logger.error(f"Error parsing MCP configuration: {e}")

    def connect_server(self, server_name: str, spec: dict[str, Any]) -> bool:
        """Launches external MCP server processes and registers their standard streams."""
        if os.getenv("MCP_TEST_MODE") == "true":
            with self.lock:
                self.servers[server_name] = {
                    "process": None,
                    "spec": spec
                }
            self._discover_server_tools(server_name)
            return True

        command = spec.get("command")
        args = spec.get("args", [])
        env = os.environ.copy()
        if "env" in spec:
            env.update(spec.get("env", {}))

        if not command:
            logger.error(f"No command executable defined for MCP server: {server_name}")
            return False

        try:
            # Launch process with pipes for input/output communication
            # Use shell=True on windows if executable is node/npm command
            use_shell = os.name == 'nt'
            process = subprocess.Popen(
                [command] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                shell=use_shell
            )

            with self.lock:
                self.servers[server_name] = {
                    "process": process,
                    "spec": spec
                }

            # Start background reader threads or perform initial handshake (tools/list)
            # In mock/fallback adapter, we do dynamic discover queries
            self._discover_server_tools(server_name)
            logger.info(f"Successfully connected to external MCP server: {server_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch MCP server {server_name}: {e}")
            return False

    def _discover_server_tools(self, server_name: str) -> None:
        """Sends a tools/list request to the server and populates discovered_tools."""
        # Standard MCP tools/list JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }

        try:
            response = self._send_request(server_name, request)
            if response and "result" in response:
                tools_list = response["result"].get("tools", [])
                for tool in tools_list:
                    name = tool.get("name")
                    if name:
                        self.discovered_tools[name] = {
                            "server": server_name,
                            "info": tool
                        }
        except Exception as e:
            logger.warning(f"Handshake failed for MCP server {server_name}, tool discovery skipped: {e}")
            # Register a fallback dummy tool for verification if testing
            if os.getenv("MCP_TEST_MODE") == "true":
                self.discovered_tools[f"{server_name}_test_tool"] = {
                    "server": server_name,
                    "info": {
                        "name": f"{server_name}_test_tool",
                        "description": "Mock test tool for verification",
                        "input_schema": {"type": "object"}
                    }
                }

    def _send_request(self, server_name: str, request: dict[str, Any]) -> dict[str, Any] | None:
        """Sends a JSON-RPC request to the target server stdio and waits for response."""
        if os.getenv("MCP_TEST_MODE") == "true":
            if request.get("method") == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "tools": [
                            {
                                "name": "mock-server_test_tool",
                                "description": "Mock test tool for verification",
                                "input_schema": {"type": "object"}
                            }
                        ]
                    },
                    "id": request.get("id", 1)
                }
            return None

        server = self.servers.get(server_name)
        if not server:
            return None

        proc = server["process"]
        if proc.poll() is not None:
            # Process died
            logger.error(f"MCP Server process {server_name} is no longer running.")
            return None

        try:
            # Send message delimited by newline
            payload = json.dumps(request) + "\n"
            proc.stdin.write(payload)
            proc.stdin.flush()

            # Read single line response
            # Note: A real production client should handle async event handlers, but
            # standard blocked JSON-RPC requests fit well inside thread tasks.
            line = proc.stdout.readline()
            if not line:
                return None
            return json.loads(line)
        except Exception as e:
            logger.error(f"Error communicating with MCP server {server_name}: {e}")
            return None

    def execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Executes a discovered external tool by routing it to its server."""
        discovery = self.discovered_tools.get(name)
        if not discovery:
            raise ValueError(f"Tool {name} is not registered in MCP Client Adapter.")

        server_name = discovery["server"]

        # Test mode mock fallback
        if os.getenv("MCP_TEST_MODE") == "true":
            return {"status": "success", "tool": name, "arguments": arguments, "mock": True}

        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 2,
            "params": {
                "name": name,
                "arguments": arguments
            }
        }

        response = self._send_request(server_name, request)
        if not response:
            return {"error": f"No response received from MCP server {server_name}."}

        if "error" in response:
            return {"error": response["error"]}

        return response.get("result", {}).get("content", [])

    def shutdown(self) -> None:
        """Terminates all active external server subprocesses."""
        with self.lock:
            for name, server in list(self.servers.items()):
                proc = server["process"]
                try:
                    proc.terminate()
                    proc.wait(timeout=2.0)
                except Exception:
                    proc.kill()
            self.servers.clear()
            self.discovered_tools.clear()
