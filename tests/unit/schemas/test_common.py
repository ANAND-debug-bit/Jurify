"""Generic guarantees that must hold for every schema in app.schemas,
per docs/architecture/08-pydantic-schemas.md §8.18 rule #1: every schema
uses extra="forbid".

Importing every schema module below is what makes
NyayaBaseModel.__subclasses__() complete — Python only registers a
subclass once its defining module has executed.
"""

from __future__ import annotations

import pytest

# noqa: F401 -- imported for the side effect of registering every
# NyayaBaseModel subclass before this file's enumeration test runs.
import app.schemas.case  # noqa: F401
import app.schemas.document  # noqa: F401
import app.schemas.emergency  # noqa: F401
import app.schemas.evidence  # noqa: F401
import app.schemas.explainability  # noqa: F401
import app.schemas.government_scheme  # noqa: F401
import app.schemas.judge  # noqa: F401
import app.schemas.lawyer  # noqa: F401
import app.schemas.legal_research  # noqa: F401
import app.schemas.opposition  # noqa: F401
import app.schemas.risk  # noqa: F401
import app.schemas.routing  # noqa: F401
import app.schemas.strategy  # noqa: F401
import app.schemas.timeline  # noqa: F401
import app.schemas.verification  # noqa: F401
from app.schemas._common import CaseStatus, NyayaBaseModel, UrgencyLevel


def _all_schema_subclasses() -> list[type[NyayaBaseModel]]:
    seen: set[type[NyayaBaseModel]] = set()
    stack = list(NyayaBaseModel.__subclasses__())
    while stack:
        cls = stack.pop()
        if cls not in seen:
            seen.add(cls)
            stack.extend(cls.__subclasses__())
    return sorted(seen, key=lambda c: c.__name__)


ALL_SCHEMAS = _all_schema_subclasses()


def test_at_least_thirty_schemas_are_registered() -> None:
    # Sanity check that the enumeration above actually found everything —
    # guards against a future refactor silently un-importing a module.
    assert len(ALL_SCHEMAS) >= 30


@pytest.mark.parametrize("schema_cls", ALL_SCHEMAS, ids=lambda c: c.__name__)
def test_every_schema_forbids_extra_fields(schema_cls: type[NyayaBaseModel]) -> None:
    assert schema_cls.model_config.get("extra") == "forbid"


def test_case_status_v2_values_present() -> None:
    # See app/schemas/_common.py docstring: v2 reconciled with
    # docs/architecture/03-langgraph-workflow.md §3.2's expanded list.
    v2_only = {
        CaseStatus.EMERGENCY_DETECTED,
        CaseStatus.EMERGENCY_HANDLING,
        CaseStatus.VERIFYING_CITATIONS,
        CaseStatus.AWAITING_EVIDENCE_UPLOAD,
        CaseStatus.CHECKING_GOV_SCHEMES,
        CaseStatus.EXPLAINING,
    }
    assert v2_only.issubset(set(CaseStatus))


def test_urgency_level_has_four_ordered_severities() -> None:
    assert [level.value for level in UrgencyLevel] == ["low", "medium", "high", "critical"]
