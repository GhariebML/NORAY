# Memory System

NORAY OS's memory architecture is organized around six memory types, reflecting how a research/career assistant needs both short-term conversational context and longer-term accumulated knowledge.

| Memory Type | Status | Description |
|---|---|---|
| Conversation Memory | ✅ Implemented | Chat history and session context |
| Workspace Memory | ✅ Implemented | Current active documents and project state |
| Semantic Memory | 🟡 Partial | Infrastructure exists; long-term knowledge extraction is still evolving |
| Episodic Memory | 🟡 Partial | Interaction history exists; retrieval optimization still under development |
| Procedural Memory | 🟡 Partial | Learning-signal architecture exists; automatic behavior adaptation not yet implemented |
| Organization Memory | ⚪ Planned | Future extension for team/organization-scoped memory |

## Coordination

Memory retrieval is currently coordinated by the **Context Engine**, which decides what conversational and workspace context to inject into a given request. A dedicated **Memory Router**, capable of dynamically selecting the optimal memory sources per query across all six types, is a planned future capability rather than current behavior.

## Memory Explorer

The AI Memory Center (Command Center) exposes a Memory Explorer UI for inspecting what the system currently holds in Conversation and Workspace memory. Semantic/Episodic/Procedural views exist but reflect the partial implementation state of those memory types.

## Design Intent

The six-memory-type model is intended to eventually support:

- Short-term conversational continuity (Conversation Memory)
- Task/document context awareness (Workspace Memory)
- Long-term factual knowledge accumulation (Semantic Memory)
- "What happened when" interaction history (Episodic Memory)
- Learned behavioral adaptation over time (Procedural Memory)
- Team/organization-level shared memory (Organization Memory, planned)

This is documented as the intended end-state architecture; current production behavior is limited to Conversation and Workspace memory being fully reliable, with the remaining types at varying stages of completion.
