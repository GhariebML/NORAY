# Agent Architecture

## Overview

NORAY OS's intelligence layer is organized around a capability-based, agent-oriented design, coordinated by the custom AI Kernel (see [`AI_KERNEL.md`](./AI_KERNEL.md)) rather than an external agent framework.

## Implemented Components

| Component | Status |
|---|---|
| Multi-Agent Registry | 🟡 Partial — agents are registered and individually invokable; autonomous multi-agent collaboration on a single task is still evolving |
| ReAct Reasoning Loop | ✅ Implemented — agents reason, act (tool/retrieval call), and observe iteratively |
| Capability-based Agent Routing | ✅ Implemented — requests are routed to the agent whose registered capability matches the task |
| Universal Retriever | ✅ Implemented |
| Context Engine | ✅ Implemented |
| Explainability Engine | ✅ Implemented |
| Cost Tracker | ✅ Implemented |
| Task Runner | ✅ Implemented |
| Human-in-the-Loop Manager | 🟡 Partial |
| Execution DAG | ✅ Implemented (visualization) |
| Planning Modes | 🟡 Partial — rule-assisted, not fully autonomous |
| Memory Injection | ✅ Implemented (Conversation/Workspace) / 🟡 Partial (Semantic/Episodic/Procedural) |
| Prompt Library | ✅ Implemented |
| Response Builder | ✅ Implemented |

## Example Agents (Visible in Command Center)

- **Task Planner** — orchestration and DAG planning
- **Research Agent** — web and document vector mining
- **Knowledge Agent** — semantic graph traversal (🟡 partial, tied to Knowledge Graph status)
- **Resume / CV Optimizer** — profile-to-role ATS alignment matching

Each agent runs against a configurable model (local or cloud) and reports its status (idle/running/completed) to the Agent Monitor in real time.

## What "Multi-Agent" Means Today vs. the Roadmap

Today, NORAY OS supports **multiple discrete agents**, each with a defined capability, invoked individually or in a fixed sequence by the orchestrator. It does **not yet** support agents autonomously decomposing an open-ended goal into sub-tasks and dynamically assigning them across agents — that capability is part of the Phase 5+ roadmap (Dynamic Task Planner, Multi-Agent Planning; see [`DEVELOPMENT_ROADMAP.md`](./DEVELOPMENT_ROADMAP.md)).

## Framework Independence

The agent architecture deliberately avoids LangChain/LangGraph as its runtime, in favor of the custom AI Kernel. The long-term goal is to evolve this into a fully autonomous, capability-driven planning engine while remaining framework-independent.
