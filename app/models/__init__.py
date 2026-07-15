"""Import every ORM model so they register on Base.metadata as a side
effect of importing this package. alembic/env.py and anything needing the
complete schema (create_all in tests, autogenerate) must import
app.models — not individual model modules — to guarantee nothing is
missing from the registered metadata.
"""

from app.models.agent_log import AgentLog
from app.models.case import Case
from app.models.document import Complaint, Document
from app.models.emergency_assessment import EmergencyAssessment
from app.models.evidence import Evidence
from app.models.evidence_report import EvidenceReport
from app.models.explainability_report import ExplainabilityReport
from app.models.government_scheme_match import GovernmentSchemeMatch
from app.models.judge_opinion import JudgeOpinion
from app.models.lawyer import CaseLawyerMatch, Lawyer
from app.models.legal_research import LegalCitation, LegalResearchResult
from app.models.memory import ConversationMemory, LongTermMemory
from app.models.opposition import OppositionRound
from app.models.risk import RiskScore
from app.models.strategy import Strategy
from app.models.timeline import CaseTimelineEvent
from app.models.user import User

__all__ = [
    "AgentLog",
    "Case",
    "CaseLawyerMatch",
    "CaseTimelineEvent",
    "Complaint",
    "ConversationMemory",
    "Document",
    "EmergencyAssessment",
    "Evidence",
    "EvidenceReport",
    "ExplainabilityReport",
    "GovernmentSchemeMatch",
    "JudgeOpinion",
    "Lawyer",
    "LegalCitation",
    "LegalResearchResult",
    "LongTermMemory",
    "OppositionRound",
    "RiskScore",
    "Strategy",
    "User",
]
