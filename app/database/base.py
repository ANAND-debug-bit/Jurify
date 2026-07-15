"""SQLAlchemy declarative base (Module 4).

A fixed naming convention for constraints/indexes is applied so Alembic
autogenerate produces stable, predictable names instead of dialect-default
anonymous ones that vary across runs/environments — see
https://alembic.sqlalchemy.org/en/latest/naming.html

Every ORM model (Module 5 onward) subclasses Base, which is also what
alembic/env.py points target_metadata at — a model that never imports
into env.py's metadata registration path is invisible to autogenerate,
so Module 5 must import each new model module there as it's added.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
