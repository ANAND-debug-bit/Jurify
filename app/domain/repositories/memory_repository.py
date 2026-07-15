"""Memory repository interface (port) — short-term conversation buffer
and long-term, embedded, cross-case memory
(docs/architecture/12-multilingual-architecture.md §12.4)."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.entities.memory import ConversationTurn, LongTermMemoryRecord


class MemoryRepository(Protocol):
    async def append_conversation_turn(
        self, case_id: UUID, role: str, content: str, language: str | None
    ) -> ConversationTurn: ...

    async def list_conversation(self, case_id: UUID) -> list[ConversationTurn]: ...

    async def save_long_term_memory(
        self,
        user_id: UUID,
        memory_type: str,
        content: dict[str, object],
        embedding: list[float] | None = None,
    ) -> LongTermMemoryRecord: ...

    async def list_long_term_memory(self, user_id: UUID) -> list[LongTermMemoryRecord]: ...
