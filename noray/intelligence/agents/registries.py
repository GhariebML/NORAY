"""
NORAY — Agent and Capability Registries

Implementations of the dynamic registries to allow agents to discover each other
by capability rather than hardcoded names.
"""


from noray.intelligence.core import AgentMetadata, IAgent, IAgentRegistry, ICapabilityRegistry


class InMemoryAgentRegistry(IAgentRegistry):
    def __init__(self):
        self._agents: dict[str, IAgent] = {}

    def register(self, agent: IAgent) -> None:
        meta = agent.get_metadata()
        self._agents[meta.agent_id] = agent

    def get_agent(self, agent_id: str) -> IAgent | None:
        return self._agents.get(agent_id)

    def list_agents(self) -> list[AgentMetadata]:
        return [agent.get_metadata() for agent in self._agents.values()]


class InMemoryCapabilityRegistry(ICapabilityRegistry):
    def __init__(self):
        self._capabilities: dict[str, list[str]] = {}

    def register_capability(self, capability: str, agent_id: str) -> None:
        if capability not in self._capabilities:
            self._capabilities[capability] = []
        if agent_id not in self._capabilities[capability]:
            self._capabilities[capability].append(agent_id)

    def get_agents_for_capability(self, capability: str) -> list[str]:
        return self._capabilities.get(capability, [])

