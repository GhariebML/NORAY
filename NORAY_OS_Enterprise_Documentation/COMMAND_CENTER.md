# Command Center

The Command Center is NORAY OS's operational and observability console — separate from the end-user AI Workspace — designed for inspecting how the system is actually behaving under the hood.

## Sections

| Section | Status | Description |
|---|---|---|
| Execution DAG | ✅ Implemented (visualization) | Live graph view of the request pipeline: Goal Definition → Task Planner → Retriever/Knowledge Graph → Reasoner → Grounding Validator → Final Response. Represents the target cognitive flow; not every node reflects live per-request computation yet (see [`SYSTEM_ARCHITECTURE.md`](./SYSTEM_ARCHITECTURE.md)). |
| Agent Monitor | ✅ Implemented | Shows active/idle/completed status for each registered agent (e.g., Task Planner, Research Agent, Knowledge Agent, Resume/CV Optimizer), including current task and model in use. |
| Memory | 🟡 Partial | Inspector for the current memory system state. |
| Retriever | ✅ Implemented | Inspection of retrieval calls — dense, BM25, and metadata results, and fusion output. |
| Tools | ✅ Implemented | Tool Registry view: which tools are available and their invocation status. |
| Models | ✅ Implemented | Model Observatory: provider, model name, token counts, execution cost, and latency per call. |
| Telemetry | ✅ Implemented | Aggregate system-wide metrics dashboard. |
| Governance | 🟡 Partial | Surfaces the Human-in-the-Loop approval queue and system logs; full governance workflow (policy enforcement, audit trail) is still developing. |
| HITL Inbox | 🟡 Partial | Tab exists in the UI; backend approval workflow exists, full production workflow is still being finalized. |
| System Logs | ✅ Implemented | Real-time log stream (e.g., kernel connection events, session initialization). |

## Purpose

The Command Center exists to make NORAY OS's internal reasoning **inspectable** rather than opaque — a deliberate design choice distinguishing it from a typical chatbot interface. This directly supports the Explainability goals described in [`SYSTEM_ARCHITECTURE.md`](./SYSTEM_ARCHITECTURE.md) and [`RAG_PIPELINE.md`](./RAG_PIPELINE.md).

## Honest Note on the DAG Visualization

The Execution DAG diagram intentionally includes nodes (e.g., Knowledge Graph Triples Search, full Grounding Validation) that represent the **target architecture** rather than fully wired, per-request computation today. This is a deliberate design decision to keep the observability surface aligned with where the system is heading, but it means the diagram should be read as **architectural intent for some nodes**, not a claim that every node executes live logic in the current build.
