"""DocumentService — generated document persistence (Module 8).

Triggering the Complaint Generation Agent is Module 17's job; this
service persists/reads whatever documents it produces.
"""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.document import Document
from app.domain.repositories.case_repository import CaseRepository
from app.schemas.document import GeneratedDocument


class DocumentService:
    def __init__(self, case_repo: CaseRepository) -> None:
        self._case_repo = case_repo

    async def record_documents(
        self, case_id: UUID, docs: list[GeneratedDocument]
    ) -> list[Document]:
        return await self._case_repo.add_documents(case_id, docs)

    async def list_documents(self, case_id: UUID) -> list[Document]:
        return await self._case_repo.list_documents(case_id)
