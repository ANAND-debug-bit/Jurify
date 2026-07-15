# 8. Pydantic Schemas (Canonical Contracts)

These are the **contracts**, not the implementation — every agent's `output_schema`, the graph state, and the API DTOs are built from these. All models use Pydantic v2 (`model_config = ConfigDict(...)`), live in `app/schemas/`, and are the single source of truth shared by agents, the database (JSONB columns), and the API layer. No agent may return anything that doesn't validate against its declared schema.

```python
# app/schemas/_common.py
from datetime import datetime
from enum import StrEnum
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class NyayaBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False, str_strip_whitespace=True)

class CaseStatus(StrEnum):
    INTAKE_IN_PROGRESS = "intake_in_progress"
    INTAKE_COMPLETE = "intake_complete"
    RECONSTRUCTING = "reconstructing"
    RESEARCHING = "researching"
    ANALYZING_EVIDENCE = "analyzing_evidence"
    ASSESSING_RISK = "assessing_risk"
    PLANNING_STRATEGY = "planning_strategy"
    GENERATING_DOCUMENTS = "generating_documents"
    MATCHING_LAWYERS = "matching_lawyers"
    SIMULATING_OPPOSITION = "simulating_opposition"
    JUDGED = "judged"
    COMPLETE = "complete"
    FAILED = "failed"

class UrgencyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

## 8.1 Case Intake Agent — `CaseProfile`

```python
# app/schemas/case.py
class PartyInfo(NyayaBaseModel):
    role: str                      # "complainant" | "respondent" | "witness"
    name: str | None = None
    relationship_to_user: str | None = None

class CaseProfile(NyayaBaseModel):
    incident_category: str          # e.g. "consumer_dispute", "motor_vehicle_accident"
    summary: str
    incident_date: datetime | None = None
    location: str | None = None
    parties: list[PartyInfo] = Field(default_factory=list)
    facts_collected: dict[str, str] = Field(default_factory=dict)
    evidence_mentioned: list[str] = Field(default_factory=list)
    user_goal: str | None = None    # what the user wants: compensation, criminal action, etc.
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
```

## 8.2 Case Reconstruction Agent — `Timeline`

```python
# app/schemas/timeline.py
class TimelineEvent(NyayaBaseModel):
    occurred_at: datetime | None = None
    description: str
    sequence_order: int
    is_inconsistent: bool = False
    inconsistency_note: str | None = None
    supporting_evidence_refs: list[str] = Field(default_factory=list)

class Timeline(NyayaBaseModel):
    events: list[TimelineEvent]
    inconsistencies: list[str] = Field(default_factory=list)
    reconstructed_summary: str
```

## 8.3 Legal Research Agent — `LegalResearchResult`

```python
# app/schemas/legal_research.py
class LegalCitation(NyayaBaseModel):
    act_name: str                  # "Bharatiya Nyaya Sanhita, 2023"
    section: str                   # "Section 318"
    source_url: str | None = None
    excerpt: str | None = None

class LegalProvision(NyayaBaseModel):
    title: str
    plain_explanation: str          # non-legalese explanation for the user
    applicable_rights: list[str] = Field(default_factory=list)
    punishments: list[str] = Field(default_factory=list)
    relevant_authority: str | None = None   # e.g. "Local Police Station", "Consumer Forum"
    citations: list[LegalCitation]

class LegalResearchResult(NyayaBaseModel):
    jurisdiction: str = "India"
    applicable_laws: list[LegalProvision]
    overall_summary: str
```

## 8.4 Evidence Analysis Agent — `EvidenceReport`

```python
# app/schemas/evidence.py
class EvidenceQuality(StrEnum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"

class EvidenceItem(NyayaBaseModel):
    evidence_type: str              # "photo", "document", "witness_statement", "receipt"
    description: str
    quality: EvidenceQuality
    notes: str | None = None

class EvidenceGap(NyayaBaseModel):
    description: str
    suggested_evidence: str
    priority: UrgencyLevel

class EvidenceReport(NyayaBaseModel):
    submitted_evidence: list[EvidenceItem]
    gaps: list[EvidenceGap]
    completeness_score: float = Field(ge=0.0, le=100.0)
    summary: str
```

## 8.5 Risk Assessment Agent — `RiskAssessment`

```python
# app/schemas/risk.py
class RiskAssessment(NyayaBaseModel):
    financial_risk: float = Field(ge=0.0, le=100.0)
    criminal_risk: float = Field(ge=0.0, le=100.0)
    urgency: UrgencyLevel
    needs_police: bool
    needs_lawyer: bool
    needs_medical: bool
    settlement_probability: float = Field(ge=0.0, le=100.0)
    case_strength: float = Field(ge=0.0, le=100.0)
    rationale: str
```

## 8.6 Legal Strategy Agent — `StrategyPlan`

```python
# app/schemas/strategy.py
class ForumType(StrEnum):
    POLICE_COMPLAINT = "police_complaint"
    CONSUMER_COURT = "consumer_court"
    CIVIL_COURT = "civil_court"
    CRIMINAL_COMPLAINT = "criminal_complaint"
    RTI = "rti"
    CYBER_CELL = "cyber_cell"
    WOMEN_CELL = "women_cell"
    LOK_ADALAT = "lok_adalat"

class StrategyOption(NyayaBaseModel):
    forum: ForumType
    description: str
    estimated_cost_inr: float
    estimated_time: str              # "2-4 weeks"
    difficulty: str                  # "low" | "medium" | "high"
    success_probability: float = Field(ge=0.0, le=100.0)
    required_specialization: str | None = None   # feeds Lawyer Recommendation Agent

class StrategyPlan(NyayaBaseModel):
    options: list[StrategyOption]
    recommended_option_index: int
    reasoning: str
```

## 8.7 Complaint Generation Agent — `GeneratedDocument`

```python
# app/schemas/document.py
class DocumentType(StrEnum):
    POLICE_COMPLAINT = "police_complaint"
    LEGAL_NOTICE = "legal_notice"
    CONSUMER_COMPLAINT = "consumer_complaint"
    RTI_APPLICATION = "rti_application"
    LABOUR_COMPLAINT = "labour_complaint"
    CYBER_COMPLAINT = "cyber_complaint"

class GeneratedDocument(NyayaBaseModel):
    document_type: DocumentType
    title: str
    content: str                     # fully formatted legal draft, ready to file
    recipient: str | None = None
    filing_authority: str | None = None
```

## 8.8 Lawyer Recommendation Agent — `LawyerMatch`

```python
# app/schemas/lawyer.py
class LawyerProfile(NyayaBaseModel):
    id: UUID
    full_name: str
    specialization: str
    city: str
    languages: list[str]
    fee_range_inr: tuple[float, float]
    rating: float = Field(ge=0.0, le=5.0)
    years_experience: int

class LawyerMatch(NyayaBaseModel):
    lawyer: LawyerProfile
    match_score: float = Field(ge=0.0, le=100.0)
    match_reason: str
```

## 8.9 Opposition Lawyer / Counter Strategy Agents

```python
# app/schemas/opposition.py
class ObjectionCategory(StrEnum):
    EVIDENCE = "evidence"
    TIMELINE = "timeline"
    WITNESS = "witness"
    CREDIBILITY = "credibility"
    JURISDICTION = "jurisdiction"
    LIMITATION = "limitation"

class Objection(NyayaBaseModel):
    category: ObjectionCategory
    argument: str
    severity: UrgencyLevel

class OppositionReport(NyayaBaseModel):
    round_number: int
    objections: list[Objection]

class Rebuttal(NyayaBaseModel):
    responds_to_category: ObjectionCategory
    argument: str
    additional_evidence_needed: str | None = None

class CounterReport(NyayaBaseModel):
    round_number: int
    rebuttals: list[Rebuttal]
    unresolved_objections: list[Objection] = Field(default_factory=list)

class OppositionRound(NyayaBaseModel):
    round_number: int
    role: str                        # "opposition" | "counter"
    content: OppositionReport | CounterReport
```

## 8.10 Judge Agent — `JudgeOpinion`

```python
# app/schemas/judge.py
class JudgeOpinion(NyayaBaseModel):
    strengths: list[str]
    weaknesses: list[str]
    likely_outcome: str
    settlement_recommendation: str
    recommended_improvements: list[str]
    overall_case_rating: float = Field(ge=0.0, le=100.0)
```

## 8.11 Supervisor Agent — `RoutingDecision` (NEW, Change 1)

```python
# app/schemas/routing.py
class NodeName(StrEnum):
    CASE_INTAKE = "case_intake"
    CASE_RECONSTRUCTION = "case_reconstruction"
    LEGAL_RESEARCH = "legal_research"
    EVIDENCE_ANALYSIS = "evidence_analysis"
    AWAITING_EVIDENCE_UPLOAD = "awaiting_evidence_upload"
    RISK_ASSESSMENT = "risk_assessment"
    STRATEGY_PLANNING = "strategy_planning"
    GOVERNMENT_SCHEME_AGENT = "government_scheme_agent"
    LAWYER_RECOMMENDATION = "lawyer_recommendation"
    COMPLAINT_GENERATION = "complaint_generation"
    EXPLAINABILITY_AGENT = "explainability_agent"
    FINALIZE_DASHBOARD = "finalize_dashboard"

class RoutingDecision(NyayaBaseModel):
    next_node: NodeName
    reason: str
    needs_user_input: bool = False
```

`RoutingDecision` deliberately has no field capable of carrying legal reasoning, evidence judgments, or free-form case commentary — `reason` is a short routing justification ("evidence completeness below threshold, pausing for upload"), not analysis. This is the schema-level enforcement of "the Supervisor should never perform legal reasoning itself" (Change 1).

## 8.12 Emergency Detection / Emergency Agent (NEW, Change 4)

```python
# app/schemas/emergency.py
class EmergencyCategory(StrEnum):
    DOMESTIC_VIOLENCE = "domestic_violence"
    CHILD_ABUSE = "child_abuse"
    ILLEGAL_DETENTION = "illegal_detention"
    HUMAN_TRAFFICKING = "human_trafficking"
    KIDNAPPING = "kidnapping"
    MEDICAL_EMERGENCY = "medical_emergency"
    IMMEDIATE_PHYSICAL_DANGER = "immediate_physical_danger"
    NONE = "none"

class EmergencyAssessment(NyayaBaseModel):
    is_emergency: bool
    category: EmergencyCategory
    severity: UrgencyLevel
    rationale: str

class HelplineInfo(NyayaBaseModel):
    name: str
    phone: str
    available: str          # e.g. "24x7"

class EmergencyGuidance(NyayaBaseModel):
    immediate_steps: list[str]
    evidence_preservation_checklist: list[str]
    helplines: list[HelplineInfo]
    recommended_authorities: list[str]
```

## 8.13 Verification Agent — `VerifiedLegalResearchResult` (NEW, Change 2)

```python
# app/schemas/verification.py
class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"

class CitationVerification(NyayaBaseModel):
    citation: LegalCitation
    status: VerificationStatus
    verification_notes: str

class VerifiedLegalResearchResult(NyayaBaseModel):
    jurisdiction: str
    verified_provisions: list[LegalProvision]      # citations here are VERIFIED only
    rejected_citations: list[CitationVerification]  # kept for audit, never shown as fact
    verification_summary: str
```

`LegalProvision.citations` inside `verified_provisions` is guaranteed (by construction — the Verification Agent builds this list, nothing upstream writes to it directly) to contain only citations with `status == VERIFIED`. The dashboard and Complaint Generation Agent consume `VerifiedLegalResearchResult`, never the raw `LegalResearchResult` — this is the enforcement mechanism behind "every law shown to the user must pass through this verification step."

## 8.14 Government Scheme Agent — `GovernmentSchemeReport` (NEW, Change 5)

```python
# app/schemas/government_scheme.py
class GovernmentScheme(StrEnum):
    FREE_LEGAL_AID = "free_legal_aid"
    GOVERNMENT_COMPENSATION = "government_compensation"
    AYUSHMAN_BHARAT = "ayushman_bharat"
    WIDOW_SCHEME = "widow_scheme"
    SENIOR_CITIZEN_SCHEME = "senior_citizen_scheme"
    LABOUR_WELFARE_SCHEME = "labour_welfare_scheme"
    WOMEN_PROTECTION_SCHEME = "women_protection_scheme"

class GovernmentSchemeMatch(NyayaBaseModel):
    scheme: GovernmentScheme
    eligible: bool
    confidence: float = Field(ge=0.0, le=100.0)
    documents_required: list[str]
    how_to_apply: str
    relevant_authority: str

class GovernmentSchemeReport(NyayaBaseModel):
    matches: list[GovernmentSchemeMatch]
```

## 8.15 Explainability Agent — `ExplainabilityReport` (NEW, Change 3)

```python
# app/schemas/explainability.py
class ExplainabilityItem(NyayaBaseModel):
    conclusion: str                              # e.g. "Recommended forum: Consumer Court"
    reasoning: str
    supporting_evidence_refs: list[str]           # references into EvidenceReport items
    supporting_legal_refs: list[str]              # references into VerifiedLegalResearchResult provisions
    confidence_score: float = Field(ge=0.0, le=100.0)
    missing_information: list[str] = Field(default_factory=list)

class ExplainabilityReport(NyayaBaseModel):
    items: list[ExplainabilityItem]
```

One `ExplainabilityItem` is produced per major dashboard conclusion (recommended strategy, risk rating, evidence completeness, top lawyer match if present) — the Explainability Agent's prompt explicitly enumerates which conclusions in the current `CaseState` need an item, so coverage is deterministic rather than left to the model's judgment of what's "important."

## 8.16 Multilingual support (NEW, Change 9)

```python
# app/schemas/language.py
class SupportedLanguage(StrEnum):
    EN = "en"   # English
    HI = "hi"   # Hindi
    BN = "bn"   # Bengali
    TA = "ta"   # Tamil
    TE = "te"   # Telugu
    MR = "mr"   # Marathi
    GU = "gu"   # Gujarati
    PA = "pa"   # Punjabi
    KN = "kn"   # Kannada
    ML = "ml"   # Malayalam
    UR = "ur"   # Urdu
```

See [12-multilingual-architecture.md](12-multilingual-architecture.md) for how `SupportedLanguage` flows through intake, agent prompting, and dashboard rendering. Structured fields (enums, scores, booleans) are **never** translated — only free-text fields (`summary`, `reasoning`, `argument`, document `content`, etc.) are language-dependent, which is why enums dominate this schema set (§8.17 below).

## 8.17 Graph state (composition root of all of the above)

```python
# app/graph/state.py
class CaseState(TypedDict):
    case_id: UUID
    user_id: UUID
    status: CaseStatus
    language: SupportedLanguage

    case_profile: CaseProfile | None
    emergency_assessment: EmergencyAssessment | None
    emergency_guidance: EmergencyGuidance | None
    timeline: Timeline | None
    legal_research: LegalResearchResult | None
    verified_legal_research: VerifiedLegalResearchResult | None
    evidence_report: EvidenceReport | None
    risk_assessment: RiskAssessment | None
    strategy_plan: StrategyPlan | None
    documents: list[GeneratedDocument]
    government_scheme_report: GovernmentSchemeReport | None
    lawyer_matches: list[LawyerMatch]
    explainability_report: ExplainabilityReport | None

    stress_test_requested: bool
    opposition_rounds: list[OppositionRound]
    round_count: int
    max_rounds: int
    judge_opinion: JudgeOpinion | None

    awaiting_evidence_upload: bool
    evidence_pause_count: int

    last_routing_decision: RoutingDecision | None

    missing_fields: list[str]
    errors: list[str]
    messages: list[BaseMessage]
```

## 8.18 Rules

- Every schema uses `extra="forbid"` — an agent hallucinating an extra field is a validation failure, not silently accepted data, which is what triggers `BaseAgent`'s retry-with-error-feedback loop.
- Enums (`StrEnum`) are used everywhere a value has a closed set of legal meanings (forum types, document types, objection categories, node names, languages, emergency categories, government schemes) so downstream code (`route_adversarial_loop`, `supervisor_route`, dashboard rendering, translation lookup) can switch on them safely instead of string-matching free text.
- Every top-level output model (`CaseProfile`, `Timeline`, `VerifiedLegalResearchResult`, `EmergencyAssessment`, `GovernmentSchemeReport`, `ExplainabilityReport`, …) maps 1:1 to a `jsonb`/dedicated table in [04-database-design.md](04-database-design.md) — no schema exists that isn't persisted somewhere, and no table stores a shape that isn't one of these schemas.
- `RoutingDecision` is the one schema that is **not** persisted to its own table — it's logged inline as part of `agent_logs` (§4.2), since it's a control-flow artifact, not case data.

Continue to [09-sequence-diagrams.md](09-sequence-diagrams.md).
