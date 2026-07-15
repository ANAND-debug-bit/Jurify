"""Domain-level exceptions (Module 7).

These are the only exceptions repository implementations raise for
expected conditions (not-found, duplicate) — infrastructure-specific
exceptions (e.g. SQLAlchemy's IntegrityError) are caught and translated
at the repository boundary so callers (services, agents) never need to
import SQLAlchemy to handle a domain-level failure.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base for every domain-level exception."""


class EntityNotFoundError(DomainError):
    def __init__(self, entity_name: str, entity_id: object) -> None:
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} not found: {entity_id}")


class DuplicateEntityError(DomainError):
    def __init__(self, entity_name: str, detail: str) -> None:
        self.entity_name = entity_name
        self.detail = detail
        super().__init__(f"{entity_name} already exists: {detail}")
