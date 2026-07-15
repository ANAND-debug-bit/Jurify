from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.case import Case


class JudgeOpinion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One-per-case (docs/architecture/04-database-design.md §4.1 ERD:
    CASES ||--o| JUDGE_OPINIONS) — unlike RiskScore/Strategy this is not
    versioned; case_id is unique."""

    __tablename__ = "judge_opinions"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), unique=True, index=True
    )
    strengths: Mapped[dict[str, Any] | None] = mapped_column(JSONBType)
    weaknesses: Mapped[dict[str, Any] | None] = mapped_column(JSONBType)
    likely_outcome: Mapped[str | None] = mapped_column(String(255))
    settlement_recommendation: Mapped[str | None] = mapped_column(Text)
    recommended_improvements: Mapped[dict[str, Any] | None] = mapped_column(JSONBType)

    case: Mapped["Case"] = relationship(back_populates="judge_opinion")
