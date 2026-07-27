"""
NORAY — Persistent Conversation Cache

Stores conversation state, embeddings metadata, last provider/model, and
retrieved context across provider switches. Uses Redis when available,
falls back to in-memory dict storage.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any

logger = logging.getLogger("noray.llm.conversation_cache")


@dataclass
class ConversationState:
    session_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    last_provider: str = ""
    last_model: str = ""
    retrieved_context: list[dict[str, Any]] = field(default_factory=list)
    embeddings_metadata: dict[str, Any] = field(default_factory=dict)
    system_prompt: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    current_offline_mode: bool = False
    fallback_chain: list[str] = field(default_factory=list)


class ConversationCache:
    """
    Persistent conversation cache with Redis primary and in-memory fallback.
    Stored keys: conversation:{session_id}
    """

    def __init__(self, redis_url: str | None = None):
        self._redis_url = redis_url or os.environ.get("REDIS_URL", "")
        self._redis = None
        self._memory_store: dict[str, ConversationState] = {}
        self._redis_available: bool = False
        self._tried_redis: bool = False

    @property
    def _cache(self) -> dict[str, ConversationState]:
        return self._memory_store

    def _ensure_redis(self) -> None:
        if self._tried_redis:
            return
        self._tried_redis = True
        if not self._redis_url:
            return
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=2,
            )
            self._redis_available = True
            logger.info("ConversationCache: connected to Redis")
        except Exception as e:
            self._redis_available = False
            logger.warning(f"ConversationCache: Redis unavailable, using in-memory: {e}")

    async def get_context(self, session_id: str) -> ConversationState | None:
        """Retrieve conversation state for a session."""
        self._ensure_redis()

        if self._redis_available:
            try:
                data = await self._redis.get(f"conversation:{session_id}")
                if data:
                    raw = json.loads(data)
                    return ConversationState(**raw)
            except Exception as e:
                logger.debug(f"Redis get failed for {session_id}: {e}")

        return self._memory_store.get(session_id)

    async def update_context(self, state: ConversationState) -> None:
        """Persist conversation state for a session."""
        state.updated_at = time.time()
        self._ensure_redis()

        if self._redis_available:
            try:
                await self._redis.set(
                    f"conversation:{state.session_id}",
                    json.dumps(asdict(state), default=str),
                    ex=86400,
                )
                return
            except Exception as e:
                logger.debug(f"Redis set failed for {state.session_id}: {e}")

        self._memory_store[state.session_id] = state

    async def clear_context(self, session_id: str) -> None:
        """Remove conversation state for a session."""
        self._ensure_redis()

        if self._redis_available:
            try:
                await self._redis.delete(f"conversation:{session_id}")
            except Exception:
                pass

        self._memory_store.pop(session_id, None)

    async def get_all_sessions(self) -> list[dict[str, Any]]:
        """List all active sessions (metadata only)."""
        self._ensure_redis()
        sessions: list[dict[str, Any]] = []

        if self._redis_available:
            try:
                keys = await self._redis.keys("conversation:*")
                for key in keys:
                    data = await self._redis.get(key)
                    if data:
                        raw = json.loads(data)
                        sessions.append({
                            "session_id": raw.get("session_id", ""),
                            "last_provider": raw.get("last_provider", ""),
                            "last_model": raw.get("last_model", ""),
                            "message_count": len(raw.get("messages", [])),
                            "updated_at": raw.get("updated_at", 0),
                            "offline_mode": raw.get("current_offline_mode", False),
                        })
            except Exception:
                pass

        # Merge in-memory sessions
        for sid, state in self._memory_store.items():
            if not any(s["session_id"] == sid for s in sessions):
                sessions.append({
                    "session_id": sid,
                    "last_provider": state.last_provider,
                    "last_model": state.last_model,
                    "message_count": len(state.messages),
                    "updated_at": state.updated_at,
                    "offline_mode": state.current_offline_mode,
                })

        return sorted(sessions, key=lambda s: s.get("updated_at", 0), reverse=True)

    async def append_message(
        self, session_id: str, role: str, content: str,
    ) -> ConversationState:
        """Append a message to the conversation and persist."""
        state = await self.get_context(session_id)
        if not state:
            state = ConversationState(
                session_id=session_id,
                created_at=time.time(),
                updated_at=time.time(),
            )
        state.messages.append({"role": role, "content": content})
        state.updated_at = time.time()
        await self.update_context(state)
        return state

    async def get_recent_context(
        self, session_id: str, max_messages: int = 20,
    ) -> str:
        """Get recent conversation context as a formatted string."""
        state = await self.get_context(session_id)
        if not state or not state.messages:
            return ""

        recent = state.messages[-max_messages:]
        lines = ["## Conversation History", ""]
        for msg in recent:
            prefix = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{prefix}: {msg['content']}")
            lines.append("")

        if state.current_offline_mode:
            lines.append("Note: Currently operating in Offline Knowledge Mode.")
            lines.append("")

        return "\n".join(lines)


conversation_cache = ConversationCache()
