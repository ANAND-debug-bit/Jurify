from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.case import Case


class CaseTimelineEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "case_timeline_events"
    __table_args__ = (
        Index("ix_case_timeline_events_case_id_sequence_order", "case_id", "sequence_order"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    description: Mapped[str] = mapped_column(Text)
    is_inconsistent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    inconsistency_note: Mapped[str | None] = mapped_column(Text)
    sequence_order: Mapped[int] = mapped_column(Integer)

    case: Mapped["Case"] = relationship(back_populates="timeline_events")
