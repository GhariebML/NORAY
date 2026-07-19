"""
NORAY — Tools and MCP Integration Tests

Verifies built-in tool layers (filesystem, postgres, qdrant, pdf, local search)
and the dynamic MCP client adapter tool discovery/handshake mechanism.
"""

import os
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from noray.agents.tools.builtins import BuiltinToolRegistry, ToolDefinition
from noray.agents.tools.mcp_adapter import McpClientAdapter

@pytest.fixture
def temp_workspace():
    with TemporaryDirectory() as tmpdir:
        # Create dummy sub-folders & files
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        
        doc_file = data_dir / "resume_draft.txt"
        doc_file.write_text("Hello, this is a CV draft for a Python Developer.", encoding="utf-8")
        
        yield Path(tmpdir)

@pytest.fixture
def registry(temp_workspace):
    return BuiltinToolRegistry(workspace_root=str(temp_workspace))

def test_list_directory_tool(registry):
    res = registry.execute("list_directory", {"path": "data"})
    assert "items" in res
    names = {item["name"] for item in res["items"]}
    assert "resume_draft.txt" in names

def test_read_file_tool(registry):
    res = registry.execute("read_file", {"path": "data/resume_draft.txt"})
    assert "content" in res
    assert "Python Developer" in res["content"]

def test_read_file_path_traversal_protection(registry):
    # Try reading file outside the workspace root
    res = registry.execute("read_file", {"path": "../../../some_sys_file.txt"})
    assert "error" in res
    assert "restricted" in res["error"]

def test_list_tools_metadata(registry):
    tools = registry.list_tools()
    names = {t["name"] for t in tools}
    assert "list_directory" in names
    assert "read_file" in names
    assert "query_db" in names
    assert "parse_pdf" in names

def test_query_db_tool_readonly(registry):
    # Only SELECT statements are permitted
    res = registry.execute("query_db", {"sql": "INSERT INTO applications (id) VALUES ('123')"})
    assert "error" in res
    assert "read-only" in res["error"]

def test_mcp_adapter_test_mode_discovery():
    # Setup temporary config file
    with NamedTemporaryFile(suffix=".json", mode="w+", delete=False) as f:
        config = {
            "mcpServers": {
                "mock-server": {
                    "command": "node",
                    "args": ["dummy.js"]
                }
            }
        }
        json_data = json_dumps = f.write(json_str := '{"mcpServers": {"mock-server": {"command": "node", "args": ["dummy.js"]}}}')
        config_path = f.name

    os.environ["MCP_TEST_MODE"] = "true"
    os.environ["MCP_CONFIG_PATH"] = config_path
    
    try:
        adapter = McpClientAdapter()
        # Verify mock-server test tool is registered in test mode
        assert "mock-server_test_tool" in adapter.discovered_tools
        
        # Verify calling the mock tool yields the inputs back
        res = adapter.execute_tool("mock-server_test_tool", {"param": "value"})
        assert res["status"] == "success"
        assert res["mock"] is True
    finally:
        os.environ.pop("MCP_TEST_MODE", None)
        os.environ.pop("MCP_CONFIG_PATH", None)
        if os.path.exists(config_path):
            os.remove(config_path)
