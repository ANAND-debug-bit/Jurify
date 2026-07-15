"""MemoryService — conversation + long-term memory access (Module 8)."""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.memory import ConversationTurn, LongTermMemoryRecord
from app.domain.repositories.memory_repository import MemoryRepository


class MemoryService:
    def __init__(self, memory_repo: MemoryRepository) -> None:
        self._memory_repo = memory_repo

    async def append_conversation_turn(
        self, case_id: UUID, role: str, content: str, language: str | None = None
    ) -> ConversationTurn:
        return await self._memory_repo.append_conversation_turn(case_id, role, content, language)

    async def get_conversation(self, case_id: UUID) -> list[ConversationTurn]:
        return await self._memory_repo.list_conversation(case_id)

    async def save_long_term_memory(
        self,
        user_id: UUID,
        memory_type: str,
        content: dict[str, object],
        embedding: list[float] | None = None,
    ) -> LongTermMemoryRecord:
        return await self._memory_repo.save_long_term_memory(
            user_id, memory_type, content, embedding
        )

    async def get_long_term_memory(self, user_id: UUID) -> list[LongTermMemoryRecord]:
        return await self._memory_repo.list_long_term_memory(user_id)
