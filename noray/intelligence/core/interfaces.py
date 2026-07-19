"""
NORAY — Cognitive Architecture Interfaces

Defines abstract base classes (ABCs) and interfaces for the intelligence layer
to enforce Clean Architecture, SOLID principles, and dependency inversion.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set
from pydantic import BaseModel

class ICapability(ABC):
    """Abstract capability that an agent or tool can expose."""
    name: str
    description: str

class ITool(ABC):
    """Abstract tool that can be executed by the reasoning engine."""
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass

class AgentMetadata(BaseModel):
    """Metadata describing a registered agent."""
    agent_id: str
    name: str
    version: str
    description: str
    capabilities: List[str]
    supported_models: List[str]
    supported_tools: List[str]
    required_permissions: List[str]
    memory_types: List[str]
    status: str = "active"
    health: bool = True
    average_latency_ms: float = 0.0
    cost_profile: str = "balanced"

class IAgent(ABC):
    """Abstract autonomous agent interface."""
    
    @abstractmethod
    def get_metadata(self) -> AgentMetadata:
        pass
    
    @abstractmethod
    async def process_task(self, task: Any, context: Any) -> Any:
        """Process a delegated subtask."""
        pass

class IAgentRegistry(ABC):
    """Abstract registry for discovering dynamic agents."""
    
    @abstractmethod
    def register(self, agent: IAgent) -> None:
        pass
        
    @abstractmethod
    def get_agent(self, agent_id: str) -> Optional[IAgent]:
        pass
        
    @abstractmethod
    def list_agents(self) -> List[AgentMetadata]:
        pass

class ICapabilityRegistry(ABC):
    """Abstract registry mapping capabilities to capable agents."""
    
    @abstractmethod
    def register_capability(self, capability: str, agent_id: str) -> None:
        pass
        
    @abstractmethod
    def get_agents_for_capability(self, capability: str) -> List[str]:
        pass

class IContextEngine(ABC):
    """Abstract context builder and compressor."""
    
    @abstractmethod
    async def build_context(self, query: str, session_id: str) -> str:
        """Gathers, ranks, and compresses context from all memory sources."""
        pass

class IReasoningEngine(ABC):
    """Abstract cognitive reasoning core."""
    
    @abstractmethod
    async def execute_cognitive_loop(self, goal: str, context: str) -> Any:
        """Executes the Understand -> Plan -> Retrieve -> Reason -> Execute cycle."""
        pass
