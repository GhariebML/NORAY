"""
NORAY — Agentic Planner

Decomposes complex user goals into structured DAG task trees.
Each task node represents a discrete unit of work that can be executed
by a domain agent, with explicit dependencies between tasks.

Architecture:
    The PlannerAgent receives a natural language goal and produces a TaskPlan
    containing a list of TaskNode objects. Each TaskNode has:
        - A unique ID
        - A description of the work
        - A target agent (career, scholarship, research, etc.)
        - Dependencies (other task IDs that must complete first)
        - Status tracking

    The planner supports two modes:
        1. Rule-based (fast, zero-cost) — pattern matches on keywords to
           produce simple task decompositions.
        2. LLM-assisted (optional) — uses the LLM to generate sophisticated
           multi-step plans for complex goals.

Design Decisions:
    - TaskPlan and TaskNode are plain dataclasses, fully serializable to JSON.
    - The planner is stateless — it produces a plan but does not execute it.
      Execution is handled by the RouterAgent.
    - Plans are deterministic for the same input when LLM is disabled,
      making testing reliable.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Lifecycle status of a task node."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionMode(str, Enum):
    """How sibling tasks should be scheduled."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


@dataclass
class TaskNode:
    """A single unit of work in a task plan.

    Attributes:
        id: Unique task identifier.
        description: Human-readable description of the work.
        agent: Target domain agent name (career, scholarship, research, etc.).
        action: Specific action verb (search, generate, analyze, compare, etc.).
        parameters: Key-value parameters passed to the agent.
        dependencies: List of task IDs that must complete before this task starts.
        status: Current lifecycle status.
        result: Output data after execution (populated by the router).
        error: Error message if the task failed.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    agent: str = "general"
    action: str = "query"
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "agent": self.agent,
            "action": self.action,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskNode":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            description=data.get("description", ""),
            agent=data.get("agent", "general"),
            action=data.get("action", "query"),
            parameters=data.get("parameters", {}),
            dependencies=data.get("dependencies", []),
            status=TaskStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
        )


@dataclass
class TaskPlan:
    """A structured plan consisting of multiple task nodes.

    Attributes:
        id: Unique plan identifier.
        goal: The original user goal that generated this plan.
        tasks: Ordered list of task nodes.
        execution_mode: Default execution mode for independent tasks.
        metadata: Additional plan-level metadata.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    goal: str = ""
    tasks: List[TaskNode] = field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "tasks": [t.to_dict() for t in self.tasks],
            "execution_mode": self.execution_mode.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskPlan":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:12]),
            goal=data.get("goal", ""),
            tasks=[TaskNode.from_dict(t) for t in data.get("tasks", [])],
            execution_mode=ExecutionMode(data.get("execution_mode", "sequential")),
            metadata=data.get("metadata", {}),
        )

    def get_ready_tasks(self) -> List[TaskNode]:
        """Return tasks whose dependencies are all completed."""
        completed_ids = {
            t.id for t in self.tasks if t.status == TaskStatus.COMPLETED
        }
        return [
            t for t in self.tasks
            if t.status == TaskStatus.PENDING
            and all(dep in completed_ids for dep in t.dependencies)
        ]

    def is_complete(self) -> bool:
        """Check if all tasks have reached a terminal state."""
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)
            for t in self.tasks
        )

    @property
    def summary(self) -> str:
        """Human-readable summary of plan progress."""
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        return f"Plan '{self.id}': {done}/{total} completed, {failed} failed"


# ---------------------------------------------------------------------------
# Agent Name Constants
# ---------------------------------------------------------------------------

AGENT_NAMES = {
    "career", "scholarship", "research", "resume", "interview",
    "knowledge", "document", "analytics", "web", "general",
}


# ---------------------------------------------------------------------------
# Planner Agent
# ---------------------------------------------------------------------------

class PlannerAgent:
    """Decomposes user goals into structured task plans.

    Args:
        use_llm: Whether to attempt LLM-assisted planning.
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm

    def plan(self, goal: str) -> TaskPlan:
        """Generate a task plan for the given goal.

        Tries LLM-assisted planning first (if enabled), then falls back
        to rule-based decomposition.
        """
        # Try LLM planning for complex multi-step goals
        if self.use_llm and self._is_complex_goal(goal):
            llm_plan = self._plan_with_llm(goal)
            if llm_plan and llm_plan.tasks:
                return llm_plan

        # Fallback: rule-based planning
        return self._plan_rules(goal)

    def _is_complex_goal(self, goal: str) -> bool:
        """Heuristic to detect multi-step goals that benefit from LLM planning."""
        complexity_signals = [
            " and ", " then ", " also ", " compare ", " analyze ",
            " research ", " generate ", " create ", " build ",
            " find ", " review ", " prepare ",
        ]
        goal_lower = goal.lower()
        signal_count = sum(1 for s in complexity_signals if s in goal_lower)
        return signal_count >= 2 or len(goal.split()) > 20

    def _plan_rules(self, goal: str) -> TaskPlan:
        """Rule-based task decomposition."""
        goal_lower = goal.lower()
        tasks: List[TaskNode] = []

        # --- Scholarship-related goals ---
        if any(kw in goal_lower for kw in ["scholarship", "funding", "grant", "fellowship"]):
            search_task = TaskNode(
                id="search",
                description="Search for matching scholarships based on profile",
                agent="scholarship",
                action="search",
                parameters={"query": goal},
            )
            tasks.append(search_task)

            if any(kw in goal_lower for kw in ["sop", "statement", "proposal", "essay"]):
                tasks.append(TaskNode(
                    id="generate_sop",
                    description="Generate Statement of Purpose draft",
                    agent="scholarship",
                    action="generate_sop",
                    parameters={"query": goal},
                    dependencies=["search"],
                ))

            if any(kw in goal_lower for kw in ["compare", "rank", "best", "top"]):
                tasks.append(TaskNode(
                    id="compare",
                    description="Compare and rank scholarship options",
                    agent="analytics",
                    action="compare",
                    dependencies=["search"],
                ))

        # --- Career-related goals ---
        elif any(kw in goal_lower for kw in ["job", "career", "resume", "cv", "interview", "salary", "hire"]):
            search_task = TaskNode(
                id="search",
                description="Search for matching job opportunities",
                agent="career",
                action="search",
                parameters={"query": goal},
            )
            tasks.append(search_task)

            if any(kw in goal_lower for kw in ["resume", "cv", "tailor"]):
                tasks.append(TaskNode(
                    id="generate_cv",
                    description="Generate or tailor resume/CV",
                    agent="resume",
                    action="generate",
                    parameters={"query": goal},
                    dependencies=["search"],
                ))

            if any(kw in goal_lower for kw in ["interview", "prepare", "practice"]):
                tasks.append(TaskNode(
                    id="interview_prep",
                    description="Prepare interview answers and practice questions",
                    agent="interview",
                    action="prepare",
                    parameters={"query": goal},
                    dependencies=["search"],
                ))

        # --- Research goals ---
        elif any(kw in goal_lower for kw in ["research", "paper", "study", "investigate", "analyze"]):
            tasks.append(TaskNode(
                id="research",
                description="Conduct deep research on the topic",
                agent="research",
                action="deep_research",
                parameters={"query": goal},
            ))

        # --- Document goals ---
        elif any(kw in goal_lower for kw in ["document", "upload", "index", "ingest"]):
            tasks.append(TaskNode(
                id="document",
                description="Process and index documents",
                agent="document",
                action="ingest",
                parameters={"query": goal},
            ))

        # --- Fallback: single general task ---
        if not tasks:
            tasks.append(TaskNode(
                id="general",
                description=f"Answer query: {goal}",
                agent="general",
                action="query",
                parameters={"query": goal},
            ))

        # Determine if independent tasks can run in parallel
        independent_count = sum(1 for t in tasks if not t.dependencies)
        mode = ExecutionMode.PARALLEL if independent_count > 1 else ExecutionMode.SEQUENTIAL

        return TaskPlan(goal=goal, tasks=tasks, execution_mode=mode)

    def _plan_with_llm(self, goal: str) -> Optional[TaskPlan]:
        """LLM-assisted plan generation."""
        try:
            from noray.shared.llm_utils import call_llm, LLMConfig

            prompt = (
                "You are a task planning agent. Decompose the following user goal into "
                "a structured plan of discrete tasks.\n\n"
                f"Goal: \"{goal}\"\n\n"
                f"Available agents: {', '.join(sorted(AGENT_NAMES))}\n"
                "Available actions: search, generate, analyze, compare, prepare, ingest, query, deep_research\n\n"
                "Return a JSON object with:\n"
                "{\n"
                '  "tasks": [\n'
                '    {"id": "t1", "description": "...", "agent": "...", "action": "...", "dependencies": []},\n'
                '    {"id": "t2", "description": "...", "agent": "...", "action": "...", "dependencies": ["t1"]}\n'
                "  ],\n"
                '  "execution_mode": "sequential" or "parallel"\n'
                "}\n\n"
                "Return ONLY the JSON object."
            )

            response = call_llm(prompt, LLMConfig(temperature=0.1, max_tokens=800))
            return self._parse_llm_plan(goal, response.content)

        except Exception:
            return None

    def _parse_llm_plan(self, goal: str, response_text: str) -> Optional[TaskPlan]:
        """Parse LLM JSON response into a TaskPlan."""
        try:
            json_text = response_text.strip()
            if "```" in json_text:
                match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", json_text, re.DOTALL)
                if match:
                    json_text = match.group(1).strip()

            data = json.loads(json_text)
            data["goal"] = goal
            return TaskPlan.from_dict(data)

        except (json.JSONDecodeError, KeyError, TypeError):
            return None
