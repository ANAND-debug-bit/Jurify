from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.case import Case


class GovernmentSchemeMatch(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Versioned by created_at, never overwritten (see RiskScore)."""

    __tablename__ = "government_scheme_matches"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    scheme_name: Mapped[str] = mapped_column(String(64))
    eligible: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    confidence: Mapped[float | None] = mapped_column(Float)
    documents_required: Mapped[dict[str, Any] | None] = mapped_column(JSONBType)
    how_to_apply: Mapped[str | None] = mapped_column(Text)
    relevant_authority: Mapped[str | None] = mapped_column(String(255))

    case: Mapped["Case"] = relationship(back_populates="government_scheme_matches")
