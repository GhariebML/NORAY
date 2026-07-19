import pytest
from noray.intelligence.agents.registries import InMemoryAgentRegistry, InMemoryCapabilityRegistry
from noray.career_agent.agent import CareerAgent
from noray.intelligence.tools.registry import ToolRegistry, ToolMetadata

def test_agent_registry():
    registry = InMemoryAgentRegistry()
    agent = CareerAgent()
    registry.register(agent)
    
    meta = registry.get_agent("career_agent_v1").get_metadata()
    assert meta.name == "Career Agent"
    assert "resume_generation" in meta.capabilities
    
def test_capability_registry():
    cap_registry = InMemoryCapabilityRegistry()
    cap_registry.register_capability("job_search", "career_agent_v1")
    cap_registry.register_capability("job_search", "another_agent")
    
    agents = cap_registry.get_agents_for_capability("job_search")
    assert "career_agent_v1" in agents
    assert len(agents) == 2

def test_tool_registry():
    registry = ToolRegistry()
    
    # Mock tool implementation
    class MockTool:
        name = "web_search"
        description = "Searches the web"
        async def execute(self, **kwargs): return "results"
        
    tool = MockTool()
    meta = ToolMetadata(
        name=tool.name,
        description=tool.description,
        capabilities=["search", "research"],
        permissions=["internet"]
    )
    
    registry.register(tool, meta)
    
    fetched = registry.get_tool("web_search")
    assert fetched is not None
    assert fetched.name == "web_search"
    
    capable = registry.get_tools_for_capability("search")
    assert len(capable) == 1
    assert capable[0].name == "web_search"
