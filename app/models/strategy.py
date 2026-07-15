from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.case import Case


class Strategy(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Versioned by created_at, never overwritten (see RiskScore)."""

    __tablename__ = "strategies"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    forum: Mapped[str] = mapped_column(String(64))
    estimated_cost: Mapped[float | None] = mapped_column(Float)
    estimated_time: Mapped[str | None] = mapped_column(String(64))
    difficulty: Mapped[str | None] = mapped_column(String(32))
    success_probability: Mapped[float | None] = mapped_column(Float)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    case: Mapped["Case"] = relationship(back_populates="strategies")
