"""
NORAY — Persistent Conversation Session Manager
Enables dynamic session resume, execution states, costs, and traces persistence.
"""

from __future__ import annotations
import os
import json
import logging
from typing import Dict, Any, List, Optional

from noray.cache.redis_cache import RedisCache

logger = logging.getLogger("noray.services.session")


class ConversationSession:
    """Represents the complete execution context and trace data for a persistent user goal."""
    
    def __init__(self, session_id: str, goal: str = ""):
        self.session_id = session_id
        self.goal = goal
        self.status = "active"  # "active", "paused", "completed"
        self.sub_goals: List[str] = []
        self.dag: Dict[str, Any] = {}
        self.reasoning_trace: List[str] = []
        self.messages: List[Dict[str, Any]] = []
        self.artifacts: List[Dict[str, Any]] = []
        self.tools_executed: List[str] = []
        self.cost: float = 0.0
        self.telemetry: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "status": self.status,
            "sub_goals": self.sub_goals,
            "dag": self.dag,
            "reasoning_trace": self.reasoning_trace,
            "messages": self.messages,
            "artifacts": self.artifacts,
            "tools_executed": self.tools_executed,
            "cost": self.cost,
            "telemetry": self.telemetry
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConversationSession:
        session = cls(data["session_id"], data.get("goal", ""))
        session.status = data.get("status", "active")
        session.sub_goals = data.get("sub_goals", [])
        session.dag = data.get("dag", {})
        session.reasoning_trace = data.get("reasoning_trace", [])
        session.messages = data.get("messages", [])
        session.artifacts = data.get("artifacts", [])
        session.tools_executed = data.get("tools_executed", [])
        session.cost = data.get("cost", 0.0)
        session.telemetry = data.get("telemetry", {})
        return session


class ConversationManager:
    """Handles CRUD operations for persistent conversation sessions using Redis."""
    
    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache or RedisCache(namespace="noray_sessions")

    def create_session(self, session_id: str, goal: str) -> ConversationSession:
        """Initializes a new persistent session."""
        session = ConversationSession(session_id, goal)
        self.save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Fetches session metadata context from Redis cache."""
        data = self.cache.get(session_id)
        if data:
            return ConversationSession.from_dict(data)
        return None

    def save_session(self, session: ConversationSession) -> bool:
        """Saves current state metrics to the database cache."""
        return self.cache.set(session.session_id, session.to_dict(), ttl=604800)  # 7-day retention TTL
