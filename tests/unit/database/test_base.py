from typing import cast

from sqlalchemy import Column, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase

from app.database.base import NAMING_CONVENTION, Base


def test_base_is_a_declarative_base() -> None:
    assert issubclass(Base, DeclarativeBase)


def test_base_metadata_uses_naming_convention() -> None:
    assert Base.metadata.naming_convention == NAMING_CONVENTION


def test_naming_convention_produces_stable_constraint_names() -> None:
    class _ThrowawayModel(Base):
        __tablename__ = "throwaway_naming_test"
        __table_args__ = (UniqueConstraint("email", name=None),)

        id = Column(Integer, primary_key=True)
        email = Column(String, nullable=False)

    table = cast(Table, _ThrowawayModel.__table__)
    constraints = {c.name for c in table.constraints}
    assert "pk_throwaway_naming_test" in constraints
    assert "uq_throwaway_naming_test_email" in constraints

    Base.metadata.remove(table)
