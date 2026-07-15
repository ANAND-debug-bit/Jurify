from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.case import Case


class EvidenceReport(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Versioned by created_at, never overwritten (see RiskScore) — the
    Evidence Analysis Agent's assessment of what's been submitted so far,
    distinct from the raw `evidence` rows it assesses (Module 14, closing
    a gap left open by Module 8's EvidenceService: "The Evidence Analysis
    Agent's quality assessment... are Module 14's job")."""

    __tablename__ = "evidence_reports"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    submitted_evidence: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONBType)
    gaps: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONBType)
    completeness_score: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)

    case: Mapped["Case"] = relationship(back_populates="evidence_reports")
