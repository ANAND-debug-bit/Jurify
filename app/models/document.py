"""Document + Complaint models.

Complaint is not its own file in the folder structure doc (06 §models/)
— it's kept here because it's tightly coupled to Document (a Complaint IS
a filed Document plus filing metadata) and has no independent lifecycle.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.case import Case


class Document(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "documents"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    document_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text)
    recipient: Mapped[str | None] = mapped_column(String(255))
    filing_authority: Mapped[str | None] = mapped_column(String(255))
    format: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str | None] = mapped_column(String(32))

    case: Mapped["Case"] = relationship(back_populates="documents")
    complaints: Mapped[list["Complaint"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Complaint(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "complaints"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    filed_with: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(32))
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    case: Mapped["Case"] = relationship(back_populates="complaints")
    document: Mapped["Document"] = relationship(back_populates="complaints")
