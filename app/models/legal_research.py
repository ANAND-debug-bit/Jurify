from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.case import Case


class LegalResearchResult(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "legal_research_results"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    jurisdiction: Mapped[str] = mapped_column(String(64), default="India", server_default="India")
    applicable_laws: Mapped[dict[str, Any] | None] = mapped_column(JSONBType)
    plain_explanation: Mapped[str | None] = mapped_column(Text)

    case: Mapped["Case"] = relationship(back_populates="legal_research_results")
    citations: Mapped[list["LegalCitation"]] = relationship(
        back_populates="legal_research_result", cascade="all, delete-orphan"
    )


class LegalCitation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "legal_citations"
    __table_args__ = (
        Index(
            "ix_legal_citations_legal_research_result_id_is_verified",
            "legal_research_result_id",
            "is_verified",
        ),
    )

    legal_research_result_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("legal_research_results.id", ondelete="CASCADE"), index=True
    )
    act_name: Mapped[str] = mapped_column(String(255))
    section: Mapped[str | None] = mapped_column(String(64))
    source_url: Mapped[str | None] = mapped_column(String(1024))
    excerpt: Mapped[str | None] = mapped_column(Text)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    verification_status: Mapped[str] = mapped_column(
        String(32), default="unverified", server_default="unverified"
    )
    verification_notes: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    legal_research_result: Mapped["LegalResearchResult"] = relationship(back_populates="citations")
