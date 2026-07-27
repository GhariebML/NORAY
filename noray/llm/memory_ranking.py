"""
NORAY — Advanced Memory Ranking
Prioritizes, selects, and compresses context facts from multiple memory indexes.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("noray.llm.memory")


class MemoryRanker:
    """Prioritizes and fuses Working Memory -> Goal -> Conversation -> Semantic -> KG -> Vector -> Long-Term."""

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    def rank_context(
        self,
        query: str,
        working_memory: list[str] | None = None,
        goal_memory: list[str] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        semantic_memories: list[str] | None = None,
        kg_facts: list[str] | None = None,
        vector_hits: list[dict[str, Any]] | None = None,
        max_context_chars: int = 15000
    ) -> str:
        """
        Aggregates and formats context fragments using precedence hierarchy.
        Performs character-level compression truncation if the context exceeds constraints.
        """
        sections = []

        # 1. Working Memory (Active tasks / prior outputs)
        if working_memory:
            sections.append("### Active Working Memory")
            sections.extend([f"- {m}" for m in working_memory[:self.top_k]])

        # 2. Goal Memory
        if goal_memory:
            sections.append("### Active Goal Context")
            sections.extend([f"- {m}" for m in goal_memory[:self.top_k]])

        # 3. Conversation Memory
        if conversation_history:
            sections.append("### Conversation History")
            for msg in conversation_history[-self.top_k:]:
                sections.append(f"  {msg.get('role', 'user')}: {msg.get('content', '')}")

        # 4. Semantic Memory
        if semantic_memories:
            sections.append("### Semantic Memory (User Profile fragments)")
            sections.extend([f"- {m}" for m in semantic_memories[:self.top_k]])

        # 5. Knowledge Graph Facts
        if kg_facts:
            sections.append("### Fused Knowledge Graph entities & facts")
            sections.extend([f"- {fact}" for fact in kg_facts[:self.top_k]])

        # 6. Vector Document Retrieval
        if vector_hits:
            sections.append("### Relevant Vector DB Document Chunks")
            for i, hit in enumerate(vector_hits[:self.top_k]):
                content = hit.get("content") or hit.get("payload", {}).get("content", "")
                source = hit.get("payload", {}).get("source", "Unknown")
                sections.append(f"  Chunk {i+1} [Source: {source}]: {content}")

        # Assemble and enforce safety limits
        full_context = "\n".join(sections)
        if len(full_context) > max_context_chars:
            logger.warning(f"Context size ({len(full_context)} chars) exceeds limit of {max_context_chars}. Compressing...")
            full_context = full_context[:max_context_chars] + "\n... [Context truncated for token/budget safety limits] ..."

        return full_context
