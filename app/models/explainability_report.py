from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.case import Case


class ExplainabilityReport(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Versioned by created_at, never overwritten (see RiskScore)."""

    __tablename__ = "explainability_reports"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    conclusion: Mapped[str | None] = mapped_column(Text)
    reasoning: Mapped[str | None] = mapped_column(Text)
    supporting_evidence_refs: Mapped[list[str] | None] = mapped_column(JSONBType)
    supporting_legal_refs: Mapped[list[str] | None] = mapped_column(JSONBType)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    missing_information: Mapped[list[str] | None] = mapped_column(JSONBType)

    case: Mapped["Case"] = relationship(back_populates="explainability_reports")
