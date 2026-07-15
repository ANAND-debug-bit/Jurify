# NyayaOS — Architecture Package

**NyayaOS**: An Agentic AI Legal Operating System powered by Gemma.

This folder is the architecture source of truth. Implementation proceeds module-by-module against it, strictly in the order defined in [14-testing-and-implementation-plan.md](14-testing-and-implementation-plan.md) §14.3 — never as one monolithic generation.

**v2 summary**: the original 11-agent linear pipeline is now a 16-agent, **Supervisor-routed** graph — see the revision notes at the top of docs 02–11 for exactly what changed and why. Highlights: a Supervisor Agent that routes (never reasons) between stages; Emergency Detection that can short-circuit the pipeline from any intake turn; a Verification Agent that gates every legal citation shown to the user; an Explainability Agent that justifies every dashboard conclusion; a Government Scheme Agent; adaptive evidence collection that pauses/resumes via LangGraph checkpointing; Lawyer Recommendation and the Opposition↔Counter↔Judge adversarial loop both made conditional/opt-in instead of automatic; and day-one multilingual support across 11 Indian languages.

## Index

| # | Document | Contents |
|---|----------|----------|
| 1 | [01-architecture-overview.md](01-architecture-overview.md) | Clean Architecture layers, DDD bounded contexts, tech stack rationale |
| 2 | [02-agent-architecture.md](02-agent-architecture.md) | 16 agents, responsibilities, base agent contract, supervisor-routed interaction diagram |
| 3 | [03-langgraph-workflow.md](03-langgraph-workflow.md) | Supervisor-routed graph, v2 state schema, emergency short-circuit, adaptive evidence pause/resume, opt-in adversarial subgraph, checkpointing |
| 4 | [04-database-design.md](04-database-design.md) | ER diagram (v2 tables), table definitions, indexing/partitioning notes |
| 5 | [05-api-specification.md](05-api-specification.md) | REST endpoints incl. `/case/stress-test`, `/case/evidence` resume flow, language params, auth |
| 6 | [06-folder-structure.md](06-folder-structure.md) | Full production folder layout incl. `i18n/` and new agents/nodes |
| 7 | [07-class-diagram.md](07-class-diagram.md) | Core class diagrams — agents (incl. Supervisor), services, repositories |
| 8 | [08-pydantic-schemas.md](08-pydantic-schemas.md) | Canonical Pydantic v2 schemas for every agent output, incl. `RoutingDecision`, `EmergencyAssessment`, `VerifiedLegalResearchResult`, `GovernmentSchemeReport`, `ExplainabilityReport`, `SupportedLanguage` |
| 9 | [09-sequence-diagrams.md](09-sequence-diagrams.md) | Happy path, interactive intake, opposition↔counter loop, RAG retrieval, **emergency short-circuit**, **adaptive evidence pause/resume** |
| 10 | [10-design-decisions.md](10-design-decisions.md) | ADR-style rationale — 11 original + 3 new (Supervisor input restriction, opt-in adversarial branch, edge-only translation) |
| 11 | [11-scalability-roadmap.md](11-scalability-roadmap.md) | Horizontal scaling, multi-tenancy, voice/OCR/mobile, fine-tuning path |
| 12 | [12-multilingual-architecture.md](12-multilingual-architecture.md) | Language detection → translate → agent pipeline → translate-back; 11 supported languages; extensibility |
| 13 | [13-configuration-and-devops.md](13-configuration-and-devops.md) | Full `.env.example`, Pydantic Settings design, `.gitignore`, Docker/Compose (API, worker, Postgres, Redis, Ollama/vLLM, Prometheus, Grafana) |
| 14 | [14-testing-and-implementation-plan.md](14-testing-and-implementation-plan.md) | Testing pyramid per module type; the strict 28-step implementation order with stop/verify checkpoints |

## Reading order

New to the design → read 1 → 2 → 3 → 4 → 5 in order (system shape, then agents, then orchestration, then persistence, then surface), then 12 (multilingual) and 13 (config/devops). Diagrams (7, 9) are reference material. 10–11 explain *why* and *what's next*. 14 governs how implementation actually proceeds.

## Status

**Approved for implementation.** Implementation proceeds incrementally per the 28-step order in doc 14 — one module at a time, each verified and tested before the next begins. See the top-level conversation/session log for current progress against that order.
