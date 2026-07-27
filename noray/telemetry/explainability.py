"""
NORAY — Explainability Module

Generates transparent explanations for why models, agents, tools, and documents were selected.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ReasoningStep(BaseModel):
    step_type: str  # "model_selection", "agent_selection", "retrieval", "tool_execution"
    decision: str
    rationale: str
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExplainabilityTrace(BaseModel):
    execution_id: str
    goal: str
    steps: list[ReasoningStep] = Field(default_factory=list)
    final_confidence: float = 0.0
    summary: str = ""

    def add_step(self, step_type: str, decision: str, rationale: str, confidence_score: float) -> None:
        self.steps.append(ReasoningStep(
            step_type=step_type,
            decision=decision,
            rationale=rationale,
            confidence_score=confidence_score
        ))

    def generate_summary(self) -> str:
        if not self.steps:
            return "No reasoning steps recorded."
        self.summary = f"Execution completed with {len(self.steps)} steps. Final confidence: {self.final_confidence:.2f}"
        return self.summary
