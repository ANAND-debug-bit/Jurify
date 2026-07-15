"""Shared ORM mixins (Module 5).

Most tables in docs/architecture/04-database-design.md share the same
UUID primary key and created_at/updated_at column shape; these mixins
factor that out so each model file only declares what's actually
distinct about that table. The declarative base itself (Base, plus the
naming convention) lives in app.database.base (Module 4) — mixins add to
that single registry, they don't create a second one.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UpdatedAtMixin:
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
