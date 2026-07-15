from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.case import Case


class EmergencyAssessment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only — one row per intake turn where emergency detection
    ran (docs/architecture/04-database-design.md §4.2), not one per case.
    Combines both the Emergency Detection Agent's assessment (is_emergency
    through rationale) and the Emergency Agent's guidance (immediate_steps
    through recommended_authorities, populated only when is_emergency is
    true) — one table, two agents' outputs, per the documented schema."""

    __tablename__ = "emergency_assessments"
    __table_args__ = (
        Index("ix_emergency_assessments_case_id_created_at", "case_id", "created_at"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    category: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    rationale: Mapped[str | None] = mapped_column(Text)
    immediate_steps: Mapped[list[str] | None] = mapped_column(JSONBType)
    evidence_preservation_checklist: Mapped[list[str] | None] = mapped_column(JSONBType)
    helplines: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONBType)
    recommended_authorities: Mapped[list[str] | None] = mapped_column(JSONBType)

    case: Mapped["Case"] = relationship(back_populates="emergency_assessments")
