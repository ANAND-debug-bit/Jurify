# 7. Class Diagram

> **Revision note (v2)**: adds `SupervisorAgent` (constrained to `RoutingDecision` output only, §8.11) and 4 new pipeline agents to the hierarchy; adds their services.

## 7.1 Agent hierarchy

```mermaid
classDiagram
    class AgentPort {
        <<Protocol>>
        +str name
        +type input_schema
        +type output_schema
        +run(state: CaseState) AgentResult
    }

    class BaseAgent {
        <<abstract>>
        #ChatModel llm
        #PromptTemplate system_prompt
        #int max_retries
        +run(state: CaseState) AgentResult
        #_build_input(state) BaseModel
        #_parse_output(raw) BaseModel
        #_persist(result) None
    }

    class AgentResult~T~ {
        +T output
        +int latency_ms
        +int tokens_input
        +int tokens_output
        +int retry_count
        +bool success
    }

    class SupervisorAgent {
        +run(state: CaseState) AgentResult~RoutingDecision~
        Note: only imports schemas/routing.py
    }

    AgentPort <|.. BaseAgent
    BaseAgent <|-- SupervisorAgent
    BaseAgent <|-- CaseIntakeAgent
    BaseAgent <|-- EmergencyDetectionAgent
    BaseAgent <|-- EmergencyAgent
    BaseAgent <|-- CaseReconstructionAgent
    BaseAgent <|-- LegalResearchAgent
    BaseAgent <|-- VerificationAgent
    BaseAgent <|-- EvidenceAnalysisAgent
    BaseAgent <|-- RiskAssessmentAgent
    BaseAgent <|-- LegalStrategyAgent
    BaseAgent <|-- GovernmentSchemeAgent
    BaseAgent <|-- ComplaintGenerationAgent
    BaseAgent <|-- LawyerRecommendationAgent
    BaseAgent <|-- ExplainabilityAgent
    BaseAgent <|-- OppositionLawyerAgent
    BaseAgent <|-- CounterStrategyAgent
    BaseAgent <|-- JudgeAgent

    LegalResearchAgent --> VectorStorePort : uses
    VerificationAgent --> VectorStorePort : re-checks citations against
    BaseAgent --> AgentResult : produces
```

## 7.2 Service / Repository / DI layers

```mermaid
classDiagram
    class CaseService {
        -CaseRepository case_repo
        -AgentOrchestrator orchestrator
        +create_case(dto) Case
        +get_case(case_id) Case
        +mark_downstream_stale(case_id, from_stage) None
    }

    class IntakeService {
        -AgentOrchestrator orchestrator
        -ConversationMemory memory
        +submit_message(case_id, message) IntakeResponse
    }

    class EvidenceService {
        -EvidenceRepository evidence_repo
        -AgentOrchestrator orchestrator
        +submit_evidence(case_id, items) EvidenceReport
    }

    class AdversarialService {
        -AgentOrchestrator orchestrator
        -OppositionRepository opposition_repo
        +run_loop(case_id, single_round) list~OppositionRound~
    }

    class DashboardService {
        -DashboardReadRepository read_repo
        +get_dashboard(case_id) DashboardResponse
    }

    class AgentOrchestrator {
        -CompiledGraph graph
        +invoke(case_id, input) CaseState
        +resume(case_id) CaseState
    }

    class CaseRepository {
        <<interface>>
        +get(case_id) Case
        +save(case) None
        +list_by_user(user_id) list~Case~
    }

    class SQLAlchemyCaseRepository {
        -AsyncSession session
        +get(case_id) Case
        +save(case) None
        +list_by_user(user_id) list~Case~
    }

    class UnitOfWork {
        -AsyncSession session
        +commit() None
        +rollback() None
        +case_repo CaseRepository
        +evidence_repo EvidenceRepository
    }

    class Container {
        +case_service() CaseService
        +intake_service() IntakeService
        +evidence_service() EvidenceService
        +orchestrator() AgentOrchestrator
    }

    CaseService --> CaseRepository
    CaseService --> AgentOrchestrator
    IntakeService --> AgentOrchestrator
    EvidenceService --> AgentOrchestrator
    AdversarialService --> AgentOrchestrator
    CaseRepository <|.. SQLAlchemyCaseRepository
    SQLAlchemyCaseRepository --> UnitOfWork
    Container --> CaseService : constructs
    Container --> IntakeService : constructs
    Container --> AgentOrchestrator : constructs
    AgentOrchestrator --> BaseAgent : invokes via graph nodes
```

## 7.3 Notes

- `AgentOrchestrator` is the **only** class that knows about LangGraph's `CompiledGraph` — services depend on `AgentOrchestrator`'s narrow interface (`invoke`/`resume`), not on LangGraph types, so the orchestration engine could be replaced without touching any service.
- `UnitOfWork` is injected into repositories, not the reverse — a single request/graph-node opens one UoW, all repository writes within it share the same `AsyncSession`, and `Container` scopes UoW lifetime to the request/task boundary.
- `Container` (in `core/container.py`) is the single composition root — the only place concrete implementations (`SQLAlchemyCaseRepository`, `GemmaChatModel`, `ChromaVectorStore`) are wired to interfaces. Every other file references interfaces/protocols only.

Continue to [08-pydantic-schemas.md](08-pydantic-schemas.md).
