# Contributing

## Project Status

NORAY OS is currently an independent, solo-developed project. It is not yet open for external contributions in a formal sense, and no open-source licensing decision has been finalized (see [`LICENSE.md`](./LICENSE.md)).

This document is included to establish the engineering standards the project follows internally, and to lay groundwork should external contribution be opened in the future.

## Creator & Roles

NORAY OS was designed and developed entirely by **Mohamed Gharieb**, who fulfilled every role across the software lifecycle: product vision, software architecture, backend/frontend engineering, RAG/LLM engineering, database design, DevOps, UI/UX design, testing, and documentation.

## AI-Assisted Engineering Acknowledgment

AI assistants (Claude, ChatGPT, Gemini, and Antigravity) were used as engineering copilots throughout development — for brainstorming, code review, architecture discussion, debugging, and accelerating implementation. All architectural decisions, implementation direction, integration choices, and final engineering judgment were made by Mohamed Gharieb. This is documented transparently as a modern, AI-assisted software engineering practice, not as a substitute for the underlying engineering work.

## Engineering Standards Followed

- **Clean Architecture** and **SOLID principles** across the backend (see [`AI_KERNEL.md`](./AI_KERNEL.md))
- Explicit separation of API, service, kernel, and persistence layers
- Honest, maturity-labeled documentation (✅ / 🟡 / ⚪) — no capability is described as complete unless it functions end-to-end
- Configuration via environment variables; no secrets committed to source control

## If Contribution Opens in the Future

Anticipated guidelines (subject to change once formalized):

1. Open an issue describing the proposed change before submitting a pull request.
2. Match existing code style and the Clean Architecture layering.
3. Include tests for new functionality once the automated test suite (see [`TESTING.md`](./TESTING.md)) is established.
4. Update the relevant documentation file(s) alongside any functional change, preserving the ✅/🟡/⚪ maturity labeling.

## Code of Conduct

Contributors and collaborators are expected to engage respectfully and constructively. A formal Code of Conduct document will be added if and when the project opens to external contributors.
