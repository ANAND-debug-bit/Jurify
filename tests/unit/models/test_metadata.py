from sqlalchemy.dialects import sqlite
from sqlalchemy.schema import CreateTable

import app.models  # noqa: F401  -- registers every model on Base.metadata
from app.database.base import Base

EXPECTED_TABLES = {
    "users",
    "cases",
    "case_timeline_events",
    "evidence",
    "evidence_reports",
    "legal_research_results",
    "legal_citations",
    "emergency_assessments",
    "government_scheme_matches",
    "explainability_reports",
    "risk_scores",
    "strategies",
    "documents",
    "complaints",
    "lawyers",
    "case_lawyer_matches",
    "opposition_rounds",
    "judge_opinions",
    "agent_logs",
    "conversation_memory",
    "long_term_memory",
}
# 20 from the original ER diagram (docs/architecture/04-database-design.md)
# + evidence_reports, added Module 14 to close a gap: doc 02 always said
# the Evidence Analysis Agent "writes evidence rows + evidence_reports",
# but doc 04's ER diagram never defined that table.


def test_all_tables_from_the_er_diagram_are_registered() -> None:
    assert set(Base.metadata.tables.keys()) == EXPECTED_TABLES
    assert len(EXPECTED_TABLES) == 21


def test_every_table_has_a_named_primary_key_constraint() -> None:
    for table in Base.metadata.tables.values():
        assert table.primary_key.name == f"pk_{table.name}"


def test_foreign_keys_use_the_naming_convention() -> None:
    # FK.name stays None on the Python object — the naming convention is
    # applied at DDL-compile time (confirmed by Alembic's own autogenerate
    # output using the same conventional names), so compile the DDL to
    # observe it, rather than inspecting the uncompiled constraint object.
    cases_table = Base.metadata.tables["cases"]
    ddl = str(CreateTable(cases_table).compile(dialect=sqlite.dialect()))
    assert "fk_cases_user_id_users" in ddl
