# 9. Sequence Diagrams

> **Revision note (v2)**: §9.1–9.4 remain structurally accurate — intake is still a resumable multi-turn loop, the pipeline still flows in this general shape, the opposition↔counter loop still bounds by `max_rounds`, RAG retrieval is unchanged. Read them with two updates in mind: (1) every stage transition in §9.2 is now a Supervisor-conditioned edge rather than a fixed `add_edge`, per [03-langgraph-workflow.md](03-langgraph-workflow.md) §3.5; (2) §9.3's opposition↔counter loop now starts only from `POST /case/stress-test`, never automatically (Change 6). Two genuinely new flows — emergency short-circuit and adaptive evidence pause/resume — are added below as §9.5 and §9.6.

## 9.1 Interactive intake loop

The only part of the pipeline that is multi-turn by nature — modeled as repeated calls into the same LangGraph thread, resumed from checkpoint each time.

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI /case/intake
    participant Svc as IntakeService
    participant Orch as AgentOrchestrator
    participant Graph as LangGraph (thread=case_id)
    participant Agent as CaseIntakeAgent
    participant DB as PostgreSQL

    User->>API: POST /case/intake {case_id, message}
    API->>Svc: submit_message(case_id, message)
    Svc->>Orch: invoke(case_id, message)
    Orch->>Graph: resume from last checkpoint
    Graph->>Agent: run(state)
    Agent->>Agent: LLM call -> CaseProfile (structured)
    Agent-->>Graph: CaseProfile{..., missing_fields}
    Graph->>DB: checkpoint state (thread=case_id)
    Graph->>Graph: route_intake(state)
    alt missing_fields non-empty
        Graph-->>Orch: paused, awaiting user
        Orch-->>Svc: IntakeResponse{missing_fields, status=INTAKE_IN_PROGRESS}
        Svc-->>API: 200 OK
        API-->>User: follow-up questions
        Note over User,API: user answers -> loop repeats
    else intake complete
        Graph->>Graph: advance to case_reconstruction (async, backgrounded)
        Graph-->>Orch: status=INTAKE_COMPLETE
        Orch-->>Svc: IntakeResponse{status=INTAKE_COMPLETE}
        Svc-->>API: 200 OK
        API-->>User: "Intake complete, building your case..."
    end
```

## 9.2 Full pipeline happy path (post-intake, single pass)

```mermaid
sequenceDiagram
    actor User
    participant API as /case/{id}/run
    participant Worker as Background Task (Celery/Arq)
    participant Graph as LangGraph
    participant DB as PostgreSQL
    participant VS as Vector Store

    User->>API: POST /case/{id}/run
    API->>Worker: enqueue run_case_pipeline(case_id)
    API-->>User: 202 {task_id}

    Worker->>Graph: invoke(case_id)
    loop reconstruction -> research -> evidence -> risk -> strategy -> documents -> lawyers
        Graph->>Graph: node executes agent, persists via UoW
        Graph->>DB: write agent-specific row(s) + agent_log
    end
    Graph->>VS: (legal_research node) hybrid retrieve(query)
    VS-->>Graph: ranked statute chunks + citations

    Graph->>Graph: opposition_lawyer <-> counter_strategy loop (see 9.3)
    Graph->>Graph: judge_agent node
    Graph->>DB: write judge_opinions
    Graph->>Graph: finalize_dashboard node
    Graph-->>Worker: CaseState{status=COMPLETE}
    Worker->>DB: update cases.status = COMPLETE

    User->>API: GET /case/{id}/status  (polled, or via SSE /case/{id}/stream)
    API-->>User: {status: COMPLETE}
    User->>API: GET /dashboard/{id}
    API-->>User: DashboardResponse (full aggregation)
```

## 9.3 Opposition ↔ Counter Strategy adversarial loop

```mermaid
sequenceDiagram
    participant Graph as LangGraph
    participant Opp as OppositionLawyerAgent
    participant Counter as CounterStrategyAgent
    participant DB as opposition_rounds

    Graph->>Opp: run(state)  [round=1]
    Opp-->>Graph: OppositionReport{objections: [...]}
    Graph->>DB: insert (round=1, role=opposition)

    Graph->>Counter: run(state)
    Counter-->>Graph: CounterReport{rebuttals, unresolved_objections}
    Graph->>DB: insert (round=1, role=counter)

    Graph->>Graph: route_adversarial_loop(state)
    alt unresolved_objections non-empty AND round_count < max_rounds
        Graph->>Opp: run(state)  [round=2, sees prior rebuttals]
        Opp-->>Graph: OppositionReport{new/refined objections}
        Graph->>DB: insert (round=2, role=opposition)
        Graph->>Counter: run(state)
        Counter-->>Graph: CounterReport{...}
        Graph->>DB: insert (round=2, role=counter)
        Note over Graph: repeats up to max_rounds
    else resolved OR round cap hit
        Graph->>Graph: proceed to judge_agent
    end
```

## 9.4 RAG legal research retrieval

```mermaid
sequenceDiagram
    participant Node as legal_research_node
    participant Agent as LegalResearchAgent
    participant Retriever as HybridRetriever
    participant VS as VectorStore (Chroma)
    participant KW as Keyword Index (Postgres full-text)
    participant Cache as Redis

    Node->>Agent: run(state)  [case_profile, timeline]
    Agent->>Agent: build query from incident_category + facts
    Agent->>Cache: GET cached_result(query_hash)
    alt cache hit
        Cache-->>Agent: cached LegalResearchResult
    else cache miss
        Agent->>Retriever: retrieve(query, top_k=8)
        par vector search
            Retriever->>VS: similarity_search(embedding(query))
            VS-->>Retriever: chunks_vector[]
        and keyword search
            Retriever->>KW: full-text search(query)
            KW-->>Retriever: chunks_keyword[]
        end
        Retriever->>Retriever: reciprocal-rank fusion (hybrid merge)
        Retriever-->>Agent: ranked chunks + metadata (act, section, source_url)
        Agent->>Agent: LLM call: synthesize plain-language explanation\n+ structured LegalProvision list, citing only retrieved chunks
        Agent->>Cache: SET cached_result(query_hash, ttl=24h)
    end
    Agent-->>Node: LegalResearchResult
```

## 9.5 Emergency short-circuit (NEW, Change 4)

```mermaid
sequenceDiagram
    actor User
    participant API as /case/intake
    participant Graph as LangGraph
    participant ED as EmergencyDetectionAgent
    participant EA as EmergencyAgent
    participant Sup as Supervisor Agent
    participant DB as PostgreSQL

    User->>API: POST /case/intake {message: "...he locked me in..."}
    API->>Graph: resume(case_id, message)
    Graph->>ED: run(state)  [every intake turn]
    ED-->>Graph: EmergencyAssessment{is_emergency=true, category=ILLEGAL_DETENTION, severity=CRITICAL}
    Graph->>DB: insert emergency_assessments
    Note over Graph: bypasses Supervisor for this hop —\nemergency routing is a hard rule, not a judgment call
    Graph->>EA: run(state)
    EA-->>Graph: EmergencyGuidance{immediate_steps, helplines, recommended_authorities}
    Graph->>DB: state.status = EMERGENCY_HANDLING
    Graph->>Sup: run(state)  [normal routing resumes]
    Sup-->>Graph: RoutingDecision{next_node=case_intake}  (more info still needed)
    Graph-->>API: IntakeResponse{missing_fields, emergency_guidance}
    API-->>User: guidance shown immediately, interview continues
```

## 9.6 Adaptive evidence collection — pause and resume (NEW, Change 7)

```mermaid
sequenceDiagram
    actor User
    participant API as /case/evidence
    participant Svc as EvidenceService
    participant Graph as LangGraph (thread=case_id)
    participant EAgent as EvidenceAnalysisAgent
    participant Sup as Supervisor Agent
    participant DB as PostgreSQL (checkpoints)

    User->>API: POST /case/evidence {items: [photo]}
    API->>Svc: submit_evidence(case_id, items)
    Svc->>Graph: resume(case_id)
    Graph->>EAgent: run(state)
    EAgent-->>Graph: EvidenceReport{completeness_score=35, gaps=[CRITICAL: "no purchase receipt"]}
    Graph->>Sup: run(state)  [legal_targets={awaiting_evidence_upload, risk_assessment}]
    Sup-->>Graph: RoutingDecision{next_node=awaiting_evidence_upload}
    Graph->>DB: checkpoint {status=AWAITING_EVIDENCE_UPLOAD, evidence_pause_count=1}
    Graph-->>Svc: paused
    Svc-->>API: EvidenceReport{..., still_awaiting_upload=true}
    API-->>User: "Please upload: purchase receipt"

    Note over User,API: time passes — user finds the receipt

    User->>API: POST /case/evidence {items: [receipt]}
    API->>Svc: submit_evidence(case_id, items)
    Svc->>Graph: resume(case_id)  [loads checkpoint, status=AWAITING_EVIDENCE_UPLOAD]
    Graph->>EAgent: run(state)  [re-scores with new item]
    EAgent-->>Graph: EvidenceReport{completeness_score=82, gaps=[]}
    Graph->>Sup: run(state)
    Sup-->>Graph: RoutingDecision{next_node=risk_assessment}
    Graph->>DB: checkpoint {status=ASSESSING_RISK}
    Graph-->>Svc: proceeding
    Svc-->>API: EvidenceReport{..., still_awaiting_upload=false}
    API-->>User: "Evidence sufficient, continuing analysis..."
```

Continue to [10-design-decisions.md](10-design-decisions.md).
