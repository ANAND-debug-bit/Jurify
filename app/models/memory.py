"""ConversationMemory (short-term, per-case) + LongTermMemory (per-user,
cross-case, embedded) — one file per docs/architecture/06-folder-
structure.md, kept together since both back app.memory.memory_manager's
single facade (see docs/architecture/12-multilingual-architecture.md
§12.4 for why conversation turns carry a language tag)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONBType, VectorType

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.user import User


class ConversationMemory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "conversation_memory"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(8))

    case: Mapped["Case"] = relationship(back_populates="conversation_memory")


class LongTermMemory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "long_term_memory"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    memory_type: Mapped[str] = mapped_column(String(64))
    content: Mapped[dict[str, Any] | None] = mapped_column(JSONBType)
    embedding: Mapped[list[float] | None] = mapped_column(VectorType)

    user: Mapped["User"] = relationship(back_populates="long_term_memories")
