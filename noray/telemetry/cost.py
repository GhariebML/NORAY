"""
NORAY — Cost Intelligence Module

Tracks token usage, embedding costs, inference costs, retrieval overhead, and tool execution costs.
Provides metrics for optimization and dashboards.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CostEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_id: str
    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    category: str = "inference"  # inference, embedding, retrieval, tool

class CostTracker:
    def __init__(self):
        self._entries: list[CostEntry] = []

    def record(self, entry: CostEntry) -> None:
        self._entries.append(entry)

    def get_total_cost(self, execution_id: str = None) -> float:
        return sum(
            e.cost_usd for e in self._entries
            if execution_id is None or e.execution_id == execution_id
        )

    def get_suggestions(self) -> list[str]:
        """Analyzes historical costs and suggests optimizations."""
        suggestions = []
        total = self.get_total_cost()
        if total > 5.0:
            suggestions.append("Consider switching to a local model for repetitive tasks.")
        return suggestions
