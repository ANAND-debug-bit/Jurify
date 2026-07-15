"""SQLAlchemy implementation of MemoryRepository (Module 7)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.domain.entities.memory import ConversationTurn, LongTermMemoryRecord


class SqlAlchemyMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append_conversation_turn(
        self, case_id: UUID, role: str, content: str, language: str | None
    ) -> ConversationTurn:
        orm_turn = models.ConversationMemory(
            case_id=case_id, role=role, content=content, language=language
        )
        self._session.add(orm_turn)
        await self._session.flush()
        await self._session.refresh(orm_turn)
        return ConversationTurn.model_validate(orm_turn)

    async def list_conversation(self, case_id: UUID) -> list[ConversationTurn]:
        stmt = (
            select(models.ConversationMemory)
            .where(models.ConversationMemory.case_id == case_id)
            .order_by(models.ConversationMemory.created_at)
        )
        result = await self._session.execute(stmt)
        return [ConversationTurn.model_validate(row) for row in result.scalars().all()]

    async def save_long_term_memory(
        self,
        user_id: UUID,
        memory_type: str,
        content: dict[str, object],
        embedding: list[float] | None = None,
    ) -> LongTermMemoryRecord:
        orm_memory = models.LongTermMemory(
            user_id=user_id, memory_type=memory_type, content=content, embedding=embedding
        )
        self._session.add(orm_memory)
        await self._session.flush()
        await self._session.refresh(orm_memory)
        return LongTermMemoryRecord.model_validate(orm_memory)

    async def list_long_term_memory(self, user_id: UUID) -> list[LongTermMemoryRecord]:
        stmt = (
            select(models.LongTermMemory)
            .where(models.LongTermMemory.user_id == user_id)
            .order_by(models.LongTermMemory.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [LongTermMemoryRecord.model_validate(row) for row in result.scalars().all()]
