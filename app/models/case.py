from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.agent_log import AgentLog
    from app.models.document import Complaint, Document
    from app.models.emergency_assessment import EmergencyAssessment
    from app.models.evidence import Evidence
    from app.models.evidence_report import EvidenceReport
    from app.models.explainability_report import ExplainabilityReport
    from app.models.government_scheme_match import GovernmentSchemeMatch
    from app.models.judge_opinion import JudgeOpinion
    from app.models.lawyer import CaseLawyerMatch
    from app.models.legal_research import LegalResearchResult
    from app.models.memory import ConversationMemory
    from app.models.opposition import OppositionRound
    from app.models.risk import RiskScore
    from app.models.strategy import Strategy
    from app.models.timeline import CaseTimelineEvent
    from app.models.user import User


class Case(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "cases"
    __table_args__ = (Index("ix_cases_user_id_status", "user_id", "status"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    incident_category: Mapped[str | None] = mapped_column(String(64))
    case_profile: Mapped[dict[str, Any] | None] = mapped_column(JSONBType)
    preferred_language: Mapped[str] = mapped_column(
        String(8), default="en", server_default="en", index=True
    )
    stress_test_requested: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    awaiting_evidence_upload: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    evidence_pause_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    max_rounds: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    round_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    user: Mapped["User"] = relationship(back_populates="cases")
    timeline_events: Mapped[list["CaseTimelineEvent"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseTimelineEvent.sequence_order",
    )
    evidence_items: Mapped[list["Evidence"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    evidence_reports: Mapped[list["EvidenceReport"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    legal_research_results: Mapped[list["LegalResearchResult"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    emergency_assessments: Mapped[list["EmergencyAssessment"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    government_scheme_matches: Mapped[list["GovernmentSchemeMatch"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    explainability_reports: Mapped[list["ExplainabilityReport"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    risk_scores: Mapped[list["RiskScore"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    strategies: Mapped[list["Strategy"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    complaints: Mapped[list["Complaint"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    lawyer_matches: Mapped[list["CaseLawyerMatch"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    opposition_rounds: Mapped[list["OppositionRound"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="OppositionRound.round_number",
    )
    judge_opinion: Mapped["JudgeOpinion | None"] = relationship(
        back_populates="case", cascade="all, delete-orphan", uselist=False
    )
    agent_logs: Mapped[list["AgentLog"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    conversation_memory: Mapped[list["ConversationMemory"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
