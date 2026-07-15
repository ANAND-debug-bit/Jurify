from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.case import Case


class RiskScore(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Versioned by created_at, never overwritten — the dashboard reads
    the latest row per case_id (docs/architecture/04-database-design.md
    §4.2). `rationale` added Module 15 — the RiskAssessment schema has
    required this field since Module 6, but no column ever existed for
    it (same class of gap as Module 7's EmergencyAssessment.rationale
    fix)."""

    __tablename__ = "risk_scores"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    financial_risk: Mapped[float | None] = mapped_column(Float)
    criminal_risk: Mapped[float | None] = mapped_column(Float)
    urgency_level: Mapped[str | None] = mapped_column(String(32))
    needs_police: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    needs_lawyer: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    needs_medical: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    settlement_probability: Mapped[float | None] = mapped_column(Float)
    case_strength: Mapped[float | None] = mapped_column(Float)
    rationale: Mapped[str | None] = mapped_column(Text)

    case: Mapped["Case"] = relationship(back_populates="risk_scores")
