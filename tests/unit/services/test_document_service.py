from __future__ import annotations

from uuid import uuid4

from app.schemas.document import DocumentType, GeneratedDocument
from app.services.document_service import DocumentService
from tests.unit.services.fakes import FakeCaseRepository


async def test_record_and_list_documents() -> None:
    repo = FakeCaseRepository()
    service = DocumentService(repo)
    case_id = uuid4()

    doc = GeneratedDocument(
        document_type=DocumentType.LEGAL_NOTICE,
        title="Legal Notice",
        content="Dear Sir/Madam...",
        recipient="ABC Traders",
    )
    added = await service.record_documents(case_id, [doc])

    assert added[0].title == "Legal Notice"
    listed = await service.list_documents(case_id)
    assert len(listed) == 1
    assert listed[0].recipient == "ABC Traders"


async def test_list_documents_empty_for_new_case() -> None:
    repo = FakeCaseRepository()
    service = DocumentService(repo)

    assert await service.list_documents(uuid4()) == []
