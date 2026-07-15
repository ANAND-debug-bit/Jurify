"""Lawyer + CaseLawyerMatch models.

CaseLawyerMatch is kept in this file, not a separate one — it's the join
table between Case and Lawyer with no independent lifecycle of its own
(mirrors the Document/Complaint pairing rationale in app.models.document).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.case import Case


class Lawyer(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "lawyers"
    __table_args__ = (Index("ix_lawyers_city_specialization", "city", "specialization"),)

    full_name: Mapped[str] = mapped_column(String(255))
    specialization: Mapped[str | None] = mapped_column(String(128))
    city: Mapped[str | None] = mapped_column(String(128))
    languages: Mapped[dict[str, Any] | None] = mapped_column(JSONBType)
    fee_range_min: Mapped[float | None] = mapped_column(Float)
    fee_range_max: Mapped[float | None] = mapped_column(Float)
    rating: Mapped[float | None] = mapped_column(Float)
    years_experience: Mapped[int | None] = mapped_column(Integer)
    contact_info: Mapped[str | None] = mapped_column(String(255))

    case_matches: Mapped[list["CaseLawyerMatch"]] = relationship(
        back_populates="lawyer", cascade="all, delete-orphan"
    )


class CaseLawyerMatch(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "case_lawyer_matches"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    lawyer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lawyers.id", ondelete="CASCADE"), index=True
    )
    match_score: Mapped[float | None] = mapped_column(Float)
    match_reason: Mapped[str | None] = mapped_column(Text)

    case: Mapped["Case"] = relationship(back_populates="lawyer_matches")
    lawyer: Mapped["Lawyer"] = relationship(back_populates="case_matches")
