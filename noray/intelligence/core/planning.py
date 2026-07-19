"""
NORAY — Planning Modes

Defines various configuration strategies for how the reasoning engine builds and executes plans.
Modes control retrieval depth, reflection iterations, and reasoning budgets.
"""

from enum import Enum
from pydantic import BaseModel

class PlanModeType(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    DEEP_RESEARCH = "deep_research"
    AUTONOMOUS = "autonomous"
    EXPERIMENTAL = "experimental"

class PlanningMode(BaseModel):
    """Configuration constraints for a specific execution strategy."""
    mode_type: PlanModeType
    max_reflection_iterations: int
    retrieval_depth: int  # e.g., how many chunks to retrieve or graph hops
    cost_limit_usd: float
    reasoning_budget_tokens: int

def get_planning_mode(mode: PlanModeType) -> PlanningMode:
    """Factory to retrieve a configured planning mode."""
    modes = {
        PlanModeType.FAST: PlanningMode(
            mode_type=PlanModeType.FAST,
            max_reflection_iterations=1,
            retrieval_depth=3,
            cost_limit_usd=0.01,
            reasoning_budget_tokens=2048
        ),
        PlanModeType.BALANCED: PlanningMode(
            mode_type=PlanModeType.BALANCED,
            max_reflection_iterations=3,
            retrieval_depth=10,
            cost_limit_usd=0.10,
            reasoning_budget_tokens=8192
        ),
        PlanModeType.DEEP_RESEARCH: PlanningMode(
            mode_type=PlanModeType.DEEP_RESEARCH,
            max_reflection_iterations=5,
            retrieval_depth=50,
            cost_limit_usd=0.50,
            reasoning_budget_tokens=32768
        ),
        PlanModeType.AUTONOMOUS: PlanningMode(
            mode_type=PlanModeType.AUTONOMOUS,
            max_reflection_iterations=10,
            retrieval_depth=20,
            cost_limit_usd=1.00,
            reasoning_budget_tokens=65536
        ),
        PlanModeType.EXPERIMENTAL: PlanningMode(
            mode_type=PlanModeType.EXPERIMENTAL,
            max_reflection_iterations=20,
            retrieval_depth=100,
            cost_limit_usd=5.00,
            reasoning_budget_tokens=128000
        )
    }
    return modes[mode]
