"""Persisted generated document.

Distinct from app.schemas.document.GeneratedDocument (the Complaint
Generation Agent's output, no id/case_id) — this is the persisted row.
title/recipient/filing_authority were added to the `documents` table in
migration 0002 after this module's repository work surfaced that
GeneratedDocument's fields didn't all have a column to land in (Module 5
shipped the table before Module 8's schema was cross-checked against it).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Document(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    document_type: str
    title: str | None = None
    content: str | None = None
    recipient: str | None = None
    filing_authority: str | None = None
    format: str | None = None
    status: str | None = None
    created_at: datetime
