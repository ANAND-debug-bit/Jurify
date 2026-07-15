from __future__ import annotations

from uuid import uuid4

from app.services.memory_service import MemoryService
from tests.unit.services.fakes import FakeMemoryRepository


async def test_append_and_get_conversation() -> None:
    repo = FakeMemoryRepository()
    service = MemoryService(repo)
    case_id = uuid4()

    await service.append_conversation_turn(case_id, "user", "hello", "en")
    await service.append_conversation_turn(case_id, "assistant", "hi there", "en")

    turns = await service.get_conversation(case_id)
    assert [t.role for t in turns] == ["user", "assistant"]


async def test_save_and_get_long_term_memory() -> None:
    repo = FakeMemoryRepository()
    service = MemoryService(repo)
    user_id = uuid4()

    await service.save_long_term_memory(user_id, "case_summary", {"note": "prior dispute"})

    records = await service.get_long_term_memory(user_id)
    assert len(records) == 1
    assert records[0].content["note"] == "prior dispute"
