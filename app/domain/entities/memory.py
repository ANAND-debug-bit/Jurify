"""Persisted memory entities.

Not in the original 8-file domain/entities/ list — MemoryRepository needs
typed, persisted-row return shapes for both the short-term conversation
buffer and the long-term, embedded, cross-case memory
(docs/architecture/12-multilingual-architecture.md §12.4,
docs/architecture/11-scalability-roadmap.md §11.3)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationTurn(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    role: str
    content: str
    language: str | None = None
    created_at: datetime


class LongTermMemoryRecord(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    user_id: UUID
    memory_type: str
    content: dict[str, object] = Field(default_factory=dict)
    embedding: list[float] | None = None
    created_at: datetime
