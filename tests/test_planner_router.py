"""
NORAY — Planner & Router Agent Tests

Tests the agentic orchestration layer: goal decomposition, task planning,
dependency resolution, sequential/parallel execution, and agent routing.
"""

import pytest
from typing import Any, Dict

from noray.agents.planner import (
    PlannerAgent,
    TaskNode,
    TaskPlan,
    TaskStatus,
    ExecutionMode,
)
from noray.agents.router import (
    RouterAgent,
    DomainAgentRegistry,
    DomainAgent,
    create_default_registry,
)


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

class MockAgent:
    """A simple mock domain agent for testing."""

    def __init__(self, agent_name: str, should_fail: bool = False):
        self._name = agent_name
        self._should_fail = should_fail
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    def execute(self, task: TaskNode, context: Dict[str, Any]) -> Any:
        self.call_count += 1
        if self._should_fail:
            raise RuntimeError(f"Agent {self._name} intentionally failed")
        return {
            "agent": self._name,
            "action": task.action,
            "description": task.description,
            "status": "mock_completed",
        }


@pytest.fixture
def planner():
    """PlannerAgent with LLM disabled for deterministic testing."""
    return PlannerAgent(use_llm=False)


@pytest.fixture
def mock_registry():
    """Registry with mock agents for testing."""
    registry = DomainAgentRegistry()
    registry.register(MockAgent("career"))
    registry.register(MockAgent("scholarship"))
    registry.register(MockAgent("research"))
    registry.register(MockAgent("resume"))
    registry.register(MockAgent("interview"))
    registry.register(MockAgent("document"))
    registry.register(MockAgent("analytics"))
    registry.register(MockAgent("general"))
    registry.register(MockAgent("knowledge"))
    registry.register(MockAgent("web"))
    return registry


@pytest.fixture
def router(mock_registry):
    """RouterAgent wired to mock agents."""
    return RouterAgent(
        registry=mock_registry,
        context={"session_id": "test-session"},
    )


# ---------------------------------------------------------------------------
# TaskNode and TaskPlan Tests
# ---------------------------------------------------------------------------

class TestTaskDomainObjects:
    def test_task_node_creation(self):
        task = TaskNode(description="Search jobs", agent="career", action="search")
        assert task.status == TaskStatus.PENDING
        assert task.agent == "career"
        assert len(task.id) == 8

    def test_task_node_serialization(self):
        task = TaskNode(
            id="t1",
            description="Generate CV",
            agent="resume",
            action="generate",
            parameters={"format": "pdf"},
            dependencies=["t0"],
        )
        d = task.to_dict()
        assert d["id"] == "t1"
        assert d["dependencies"] == ["t0"]

        restored = TaskNode.from_dict(d)
        assert restored.agent == "resume"
        assert restored.dependencies == ["t0"]

    def test_task_plan_ready_tasks(self):
        plan = TaskPlan(
            goal="Test plan",
            tasks=[
                TaskNode(id="t1", description="First", agent="career"),
                TaskNode(id="t2", description="Second", agent="resume", dependencies=["t1"]),
                TaskNode(id="t3", description="Third", agent="general"),
            ],
        )
        ready = plan.get_ready_tasks()
        ready_ids = {t.id for t in ready}
        assert "t1" in ready_ids  # No dependencies
        assert "t3" in ready_ids  # No dependencies
        assert "t2" not in ready_ids  # Depends on t1

    def test_task_plan_ready_after_completion(self):
        plan = TaskPlan(
            goal="Test",
            tasks=[
                TaskNode(id="t1", description="First", agent="career", status=TaskStatus.COMPLETED),
                TaskNode(id="t2", description="Second", agent="resume", dependencies=["t1"]),
            ],
        )
        ready = plan.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "t2"

    def test_task_plan_is_complete(self):
        plan = TaskPlan(
            goal="Test",
            tasks=[
                TaskNode(id="t1", status=TaskStatus.COMPLETED),
                TaskNode(id="t2", status=TaskStatus.FAILED),
            ],
        )
        assert plan.is_complete()

    def test_task_plan_not_complete(self):
        plan = TaskPlan(
            goal="Test",
            tasks=[
                TaskNode(id="t1", status=TaskStatus.COMPLETED),
                TaskNode(id="t2", status=TaskStatus.PENDING),
            ],
        )
        assert not plan.is_complete()

    def test_task_plan_summary(self):
        plan = TaskPlan(
            goal="Test",
            tasks=[
                TaskNode(id="t1", status=TaskStatus.COMPLETED),
                TaskNode(id="t2", status=TaskStatus.PENDING),
                TaskNode(id="t3", status=TaskStatus.FAILED),
            ],
        )
        summary = plan.summary
        assert "1/" in summary  # 1 completed
        assert "1 failed" in summary


# ---------------------------------------------------------------------------
# Planner Agent Tests
# ---------------------------------------------------------------------------

class TestPlannerAgent:
    def test_scholarship_plan(self, planner):
        plan = planner.plan("Find scholarships for Master in Germany")
        assert plan.goal == "Find scholarships for Master in Germany"
        assert len(plan.tasks) >= 1
        agents = {t.agent for t in plan.tasks}
        assert "scholarship" in agents

    def test_career_plan(self, planner):
        plan = planner.plan("Find jobs for ML engineer and prepare my resume")
        assert len(plan.tasks) >= 2
        agents = {t.agent for t in plan.tasks}
        assert "career" in agents
        assert "resume" in agents

    def test_career_with_interview(self, planner):
        plan = planner.plan("Find software engineering jobs and prepare for interview")
        agents = {t.agent for t in plan.tasks}
        assert "career" in agents
        assert "interview" in agents

    def test_research_plan(self, planner):
        plan = planner.plan("Research the latest advances in quantum computing")
        assert len(plan.tasks) >= 1
        agents = {t.agent for t in plan.tasks}
        assert "research" in agents

    def test_document_plan(self, planner):
        plan = planner.plan("Upload and index my documents folder")
        assert len(plan.tasks) >= 1
        agents = {t.agent for t in plan.tasks}
        assert "document" in agents

    def test_fallback_general_plan(self, planner):
        plan = planner.plan("Hello, how are you?")
        assert len(plan.tasks) == 1
        assert plan.tasks[0].agent == "general"

    def test_dependency_chain(self, planner):
        plan = planner.plan("Find scholarships and then write a statement of purpose")
        # Search should happen first, SOP should depend on it
        search_tasks = [t for t in plan.tasks if t.action == "search"]
        sop_tasks = [t for t in plan.tasks if t.action == "generate_sop"]
        assert len(search_tasks) >= 1
        assert len(sop_tasks) >= 1
        assert search_tasks[0].id in sop_tasks[0].dependencies

    def test_complex_goal_detection(self, planner):
        simple = "Find scholarships"
        complex_goal = "Find scholarships in Germany and compare them and also prepare a research proposal and generate a CV"
        assert not planner._is_complex_goal(simple)
        assert planner._is_complex_goal(complex_goal)


# ---------------------------------------------------------------------------
# Domain Agent Registry Tests
# ---------------------------------------------------------------------------

class TestDomainAgentRegistry:
    def test_register_and_get(self):
        registry = DomainAgentRegistry()
        agent = MockAgent("test_agent")
        registry.register(agent)
        assert registry.get("test_agent") is agent

    def test_get_unknown_agent(self):
        registry = DomainAgentRegistry()
        assert registry.get("nonexistent") is None

    def test_list_agents(self):
        registry = DomainAgentRegistry()
        registry.register(MockAgent("a"))
        registry.register(MockAgent("b"))
        assert set(registry.list_agents()) == {"a", "b"}

    def test_has_agent(self):
        registry = DomainAgentRegistry()
        registry.register(MockAgent("x"))
        assert registry.has("x")
        assert not registry.has("y")

    def test_default_registry(self):
        registry = create_default_registry()
        assert registry.has("career")
        assert registry.has("scholarship")
        assert registry.has("general")
        assert registry.has("research")
        assert len(registry.list_agents()) >= 9


# ---------------------------------------------------------------------------
# Router Agent Tests
# ---------------------------------------------------------------------------

class TestRouterAgent:
    def test_execute_simple_plan(self, router, planner):
        plan = planner.plan("Find scholarships in Germany")
        result = router.execute_plan(plan)
        assert result.is_complete()
        for task in result.tasks:
            assert task.status == TaskStatus.COMPLETED

    def test_execute_plan_with_dependencies(self, router):
        plan = TaskPlan(
            goal="Test dependencies",
            tasks=[
                TaskNode(id="t1", description="First", agent="career", action="search"),
                TaskNode(id="t2", description="Second", agent="resume", action="generate", dependencies=["t1"]),
            ],
        )
        result = router.execute_plan(plan)
        assert result.is_complete()
        assert result.tasks[0].status == TaskStatus.COMPLETED
        assert result.tasks[1].status == TaskStatus.COMPLETED

    def test_execute_parallel_plan(self, router):
        plan = TaskPlan(
            goal="Test parallel",
            execution_mode=ExecutionMode.PARALLEL,
            tasks=[
                TaskNode(id="t1", description="A", agent="career", action="search"),
                TaskNode(id="t2", description="B", agent="scholarship", action="search"),
                TaskNode(id="t3", description="C", agent="research", action="query"),
            ],
        )
        result = router.execute_plan(plan)
        assert result.is_complete()
        assert all(t.status == TaskStatus.COMPLETED for t in result.tasks)

    def test_task_results_in_context(self, router):
        plan = TaskPlan(
            goal="Test context propagation",
            tasks=[
                TaskNode(id="t1", description="Search", agent="career", action="search"),
            ],
        )
        router.execute_plan(plan)
        assert "task_result_t1" in router.context

    def test_unknown_agent_fails_task(self, router):
        plan = TaskPlan(
            goal="Test unknown agent",
            tasks=[
                TaskNode(id="t1", description="Test", agent="nonexistent_agent", action="query"),
            ],
        )
        result = router.execute_plan(plan)
        assert result.tasks[0].status == TaskStatus.FAILED
        assert "No agent registered" in result.tasks[0].error

    def test_failing_agent_with_retry(self):
        registry = DomainAgentRegistry()
        failing_agent = MockAgent("failing", should_fail=True)
        registry.register(failing_agent)

        router = RouterAgent(registry=registry, max_retries=2)
        plan = TaskPlan(
            goal="Test retries",
            tasks=[
                TaskNode(id="t1", description="Will fail", agent="failing", action="query"),
            ],
        )
        result = router.execute_plan(plan)
        assert result.tasks[0].status == TaskStatus.FAILED
        assert failing_agent.call_count == 3  # 1 initial + 2 retries

    def test_deadlock_detection(self, router):
        """Tasks with circular dependencies should not loop forever."""
        plan = TaskPlan(
            goal="Test deadlock",
            tasks=[
                TaskNode(id="t1", description="A", agent="career", dependencies=["t2"]),
                TaskNode(id="t2", description="B", agent="career", dependencies=["t1"]),
            ],
        )
        result = router.execute_plan(plan)
        # Both tasks should still be pending (deadlocked)
        assert all(t.status == TaskStatus.PENDING for t in result.tasks)

    @pytest.mark.asyncio
    async def test_async_execution(self, router):
        plan = TaskPlan(
            goal="Test async",
            execution_mode=ExecutionMode.PARALLEL,
            tasks=[
                TaskNode(id="t1", description="A", agent="career", action="search"),
                TaskNode(id="t2", description="B", agent="scholarship", action="search"),
            ],
        )
        result = await router.execute_plan_async(plan)
        assert result.is_complete()
        assert all(t.status == TaskStatus.COMPLETED for t in result.tasks)
