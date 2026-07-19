"""
NORAY — Simple Dependency Injection Container
Provides an IoC container and singleton resolution helpers for the AI Kernel.
"""

from __future__ import annotations
from typing import Type, TypeVar, Dict, Any, Callable

T = TypeVar('T')


class DIContainer:
    """IoC container mapping interfaces to singleton or transient factory instances."""
    
    _instances: Dict[Type, Any] = {}
    _factories: Dict[Type, Callable[[], Any]] = {}
    
    @classmethod
    def register_instance(cls, interface: Type[T], instance: T) -> None:
        """Register a singleton instance for an interface."""
        cls._instances[interface] = instance
        
    @classmethod
    def register_factory(cls, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for an interface."""
        cls._factories[interface] = factory
        
    @classmethod
    def resolve(cls, interface: Type[T]) -> T:
        """Resolve an instance for the given interface."""
        if interface in cls._instances:
            return cls._instances[interface]
        if interface in cls._factories:
            instance = cls._factories[interface]()
            return instance
        raise ValueError(f"No implementation registered for interface {interface.__name__}")

    @classmethod
    def clear(cls) -> None:
        """Clear all registered dependencies (useful for testing)."""
        cls._instances.clear()
        cls._factories.clear()


def get_kernel() -> Any:
    """Convenience helper to retrieve or construct the singleton AIKernel orchestration object."""
    from noray.intelligence.core.kernel import AIKernel
    
    try:
        return DIContainer.resolve(AIKernel)
    except ValueError:
        from noray.intelligence.agents.registries import InMemoryAgentRegistry, InMemoryCapabilityRegistry
        from noray.intelligence.tools.registry import ToolRegistry
        from noray.intelligence.memory.context_engine import ContextEngine
        from noray.intelligence.core.reasoning import ReasoningEngine
        from noray.services.hitl import HITLManager
        
        agent_registry = InMemoryAgentRegistry()
        capability_registry = InMemoryCapabilityRegistry()
        tool_registry = ToolRegistry()
        context_engine = ContextEngine()
        reasoning_engine = ReasoningEngine(context_engine)
        hitl_manager = HITLManager()
        
        kernel = AIKernel(
            agent_registry=agent_registry,
            capability_registry=capability_registry,
            tool_registry=tool_registry,
            context_engine=context_engine,
            reasoning_engine=reasoning_engine,
            hitl_manager=hitl_manager
        )
        
        DIContainer.register_instance(AIKernel, kernel)
        return kernel
