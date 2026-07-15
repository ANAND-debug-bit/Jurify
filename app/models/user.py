from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.memory import LongTermMemory


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))
    preferred_language: Mapped[str] = mapped_column(
        String(8), default="en", server_default="en"
    )

    cases: Mapped[list["Case"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    long_term_memories: Mapped[list["LongTermMemory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
