from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.case import Case


class OppositionRound(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Single append-only table for both roles (docs/architecture/04-
    database-design.md §4.2) — `role` discriminates 'opposition' |
    'counter', `round_number` orders the transcript."""

    __tablename__ = "opposition_rounds"
    __table_args__ = (
        Index("ix_opposition_rounds_case_id_round_number", "case_id", "round_number"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    round_number: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[dict[str, Any] | None] = mapped_column(JSONBType)

    case: Mapped["Case"] = relationship(back_populates="opposition_rounds")
