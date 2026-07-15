"""Lawyer domain entity.

Deliberately a re-export of app.schemas.lawyer.LawyerProfile rather than
a parallel duplicate class — LawyerProfile already has exactly the
persisted-entity shape (id plus every searchable/displayable field), so
defining a second, identical class here would be pure duplication.
"""

from __future__ import annotations

from app.schemas.lawyer import LawyerProfile as Lawyer

__all__ = ["Lawyer"]
