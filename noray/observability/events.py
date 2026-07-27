import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str
    execution_id: str | None = None
    agent_id: str | None = None
    task_id: str | None = None
    session_id: str | None = None
    severity: str = "info"  # info, warning, error, debug
    latency: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

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
