from __future__ import annotations

from uuid import uuid4

from app import models
from app.repositories.sqlalchemy_memory_repository import SqlAlchemyMemoryRepository


async def _create_case(session) -> tuple[models.User, models.Case]:
    user = models.User(email=f"{uuid4()}@example.com", hashed_password="x")
    session.add(user)
    await session.flush()
    case = models.Case(user_id=user.id, status="intake_in_progress")
    session.add(case)
    await session.flush()
    return user, case


async def test_append_and_list_conversation_turns_in_order(session) -> None:
    _, case = await _create_case(session)
    repo = SqlAlchemyMemoryRepository(session)

    await repo.append_conversation_turn(case.id, "user", "hello", "en")
    await repo.append_conversation_turn(case.id, "assistant", "hi, how can I help?", "en")
    await session.commit()

    turns = await repo.list_conversation(case.id)
    assert [t.role for t in turns] == ["user", "assistant"]
    assert turns[0].language == "en"


async def test_save_and_list_long_term_memory(session) -> None:
    user, _ = await _create_case(session)
    repo = SqlAlchemyMemoryRepository(session)

    await repo.save_long_term_memory(
        user.id, "case_summary", {"note": "prior consumer dispute"}, embedding=[0.1, 0.2]
    )
    await session.commit()

    records = await repo.list_long_term_memory(user.id)
    assert len(records) == 1
    assert records[0].content["note"] == "prior consumer dispute"
    assert records[0].embedding == [0.1, 0.2]


async def test_list_long_term_memory_empty_for_new_user(session) -> None:
    user, _ = await _create_case(session)
    repo = SqlAlchemyMemoryRepository(session)

    assert await repo.list_long_term_memory(user.id) == []
