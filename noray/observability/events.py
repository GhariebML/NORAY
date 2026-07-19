from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    event_type: str
    execution_id: Optional[str] = None
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    severity: str = "info"  # info, warning, error, debug
    latency: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Agent Lifecycle
class AgentStarted(BaseEvent): event_type: str = "AgentStarted"
class AgentFinished(BaseEvent): event_type: str = "AgentFinished"

# DAG Execution
class NodeStarted(BaseEvent): event_type: str = "NodeStarted"
class NodeCompleted(BaseEvent): event_type: str = "NodeCompleted"

# Tools
class ToolCalled(BaseEvent): event_type: str = "ToolCalled"
class ToolFinished(BaseEvent): event_type: str = "ToolFinished"

# Retrieval
class RetrievalStarted(BaseEvent): event_type: str = "RetrievalStarted"
class RetrievalCompleted(BaseEvent): event_type: str = "RetrievalCompleted"
class VectorSearch(BaseEvent): event_type: str = "VectorSearch"
class GraphSearch(BaseEvent): event_type: str = "GraphSearch"
class BM25Search(BaseEvent): event_type: str = "BM25Search"
class UniversalRetrieverDecision(BaseEvent): event_type: str = "UniversalRetrieverDecision"

# Memory
class MemoryLookup(BaseEvent): event_type: str = "MemoryLookup"
class MemoryStored(BaseEvent): event_type: str = "MemoryStored"

# Cognitive Loop
class PlannerStarted(BaseEvent): event_type: str = "PlannerStarted"
class PlannerFinished(BaseEvent): event_type: str = "PlannerFinished"
class ReasoningIteration(BaseEvent): event_type: str = "ReasoningIteration"
class ReflectionIteration(BaseEvent): event_type: str = "ReflectionIteration"

# LLM / Models
class ModelSelected(BaseEvent): event_type: str = "ModelSelected"
class LLMRequest(BaseEvent): event_type: str = "LLMRequest"
class LLMResponse(BaseEvent): event_type: str = "LLMResponse"
class EmbeddingCreated(BaseEvent): event_type: str = "EmbeddingCreated"
class CacheHit(BaseEvent): event_type: str = "CacheHit"
class CacheMiss(BaseEvent): event_type: str = "CacheMiss"
class TokenUsage(BaseEvent): event_type: str = "TokenUsage"

# HITL & Governance
class ApprovalRequested(BaseEvent): event_type: str = "ApprovalRequested"
class ApprovalApproved(BaseEvent): event_type: str = "ApprovalApproved"
class ApprovalRejected(BaseEvent): event_type: str = "ApprovalRejected"

# General
class Error(BaseEvent): event_type: str = "Error"
class CostUpdate(BaseEvent): event_type: str = "CostUpdate"
class SessionFinished(BaseEvent): event_type: str = "SessionFinished"
