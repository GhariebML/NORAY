"""
NORAY — Execution Graph (DAG)

Represents complex tasks as a Directed Acyclic Graph.
Each node contains task data, required agents, tools, memory, and status.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class TaskNode(BaseModel):
    """A single execution step within a larger DAG."""
    task_id: str
    description: str
    required_capabilities: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    
    assigned_agent: Optional[str] = None
    status: str = "pending"  # pending, running, awaiting_hitl, completed, failed
    retry_count: int = 0
    max_retries: int = 3
    estimated_cost: float = 0.0
    priority: int = 1
    timeout_seconds: int = 60
    
    result: Optional[Any] = None
    error_message: Optional[str] = None
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionGraph(BaseModel):
    """The overarching DAG representing a complex user goal."""
    execution_id: str
    goal: str
    nodes: Dict[str, TaskNode] = Field(default_factory=dict)
    global_status: str = "pending" # pending, running, paused, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_node(self, node: TaskNode) -> None:
        self.nodes[node.task_id] = node
        
    def get_executable_nodes(self) -> List[TaskNode]:
        """Returns all pending nodes whose dependencies are completed."""
        executable = []
        for node in self.nodes.values():
            if node.status == "pending":
                deps_met = all(self.nodes[d].status == "completed" for d in node.dependencies)
                if deps_met:
                    executable.append(node)
        # Sort by priority (higher is better)
        executable.sort(key=lambda n: n.priority, reverse=True)
        return executable
        
    def is_complete(self) -> bool:
        """Returns true if all nodes are completed successfully."""
        return all(node.status == "completed" for node in self.nodes.values())
        
    def has_failures(self) -> bool:
        """Returns true if any node failed permanently."""
        return any(node.status == "failed" for node in self.nodes.values())
