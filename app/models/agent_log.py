from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.case import Case


class AgentLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only, one row per agent invocation including retries
    (docs/architecture/04-database-design.md §4.2) — never updated in
    place. agent_name='supervisor' rows double as the routing audit
    trail (Change 1)."""

    __tablename__ = "agent_logs"
    __table_args__ = (Index("ix_agent_logs_case_id_created_at", "case_id", "created_at"),)

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    agent_name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    tokens_input: Mapped[int | None] = mapped_column(Integer)
    tokens_output: Mapped[int | None] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text)

    case: Mapped["Case"] = relationship(back_populates="agent_logs")
