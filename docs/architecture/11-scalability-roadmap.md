# 11. Future Scalability

> **Revision note (v2)**: multilingual support (§9 of the change list) is now a **day-one** requirement, not future work — see [12-multilingual-architecture.md](12-multilingual-architecture.md). §11.6 (Voice) and §11.7 (OCR) below are unaffected by this and remain future work; both are described as adapters in front of/around the same pipeline, which is exactly how multilingual support was ultimately built too (§12.1) — this roadmap's "adapter at the edge, not a new agent" pattern held up.

## 11.1 Horizontal scaling (multi-user, thousands of concurrent cases)

- **API tier**: stateless FastAPI processes (uvicorn workers behind gunicorn or a process supervisor), N replicas behind a load balancer. Statelessness is guaranteed by ADR-9 (JWT) and ADR-1 (LangGraph Postgres checkpointing) — any replica can serve any request for any case, no sticky sessions.
- **Pipeline execution tier**: long graph runs execute in Celery/Arq workers, not inside the API request path (§5.3). Worker pool scales independently of API replica count — case-processing load (LLM-bound) and API request load (I/O-bound, cheap) have different scaling curves and shouldn't share a pool.
- **Database**: single primary for writes; read replicas for the dashboard read-model (`DashboardReadRepository`) and `agent_logs` queries, which are read-heavy and tolerate slight replication lag. Connection pooling via PgBouncer once replica count grows past what direct SQLAlchemy pools handle comfortably.
- **LLM serving**: Gemma served via vLLM with continuous batching behind its own autoscaled pool (GPU-bound, scales on queue depth / p99 latency, not on API replica count). The `llm/gemma_client.py` wrapper talks to this pool over HTTP — the API/worker tiers never load the model in-process.

## 11.2 Multi-tenancy

- Every table is already scoped by `user_id`/`case_id` (§4). At scale, add row-level security (Postgres RLS) as a defense-in-depth layer so a repository bug can't leak cross-tenant data even if a `WHERE user_id = ...` clause is accidentally dropped.
- Partition `agent_logs` and `conversation_memory` by time (monthly range partitions) once volume justifies it — these are the two highest-write-volume, append-only tables and the ones most likely to need pruning/archival independent of case data.

## 11.3 Vector store scale path

- **Now**: ChromaDB (embedded/local) for the statute corpus — fine for a bounded, curated legal corpus (Constitution, BNS, BNSS, BSA, Consumer Protection Act, Motor Vehicles Act, Labour Laws, Cyber Laws, state acts) that changes infrequently.
- **Next**: migrate to `pgvector` if we want retrieval to live next to the relational data (simpler ops, one database to reason about) — reasonable once corpus size is in the low millions of chunks.
- **At real scale / high QPS**: move to a dedicated vector service (Qdrant or Weaviate) for independent scaling of retrieval QPS away from the primary Postgres, with the same `VectorStorePort` interface (ADR-4) meaning this swap touches one adapter file, not the agents.
- `long_term_memory.embedding` (user cross-case memory, §4.2) is a *different* corpus with different growth characteristics (grows per-user, per-case, essentially unbounded over the product's lifetime) — it's kept on `pgvector` from day one specifically so it scales via normal Postgres partitioning/read-replica strategy rather than needing its own service prematurely.

## 11.4 Caching strategy at scale

- RAG retrieval results cache (§9.4) has a high hit rate because statute questions cluster around common incident categories — worth moving to a dedicated Redis cluster (separate from rate-limit/broker Redis, ADR-8) once traffic volume makes contention a real risk rather than a theoretical one.
- Add a CDN/edge cache for `GET /lawyers` (directory search) — read-heavy, low personalization, cheap to cache by query-param key with a short TTL.

## 11.5 Mobile app

- The REST/SSE API surface (doc 5) is already client-agnostic — a mobile app is a new consumer of the same `/api/v1` contract, no backend changes required beyond possibly adding push-notification hooks (case status changes → mobile push) as a new background task subscriber on the same `case.status` transition events.

## 11.6 Voice support

- Modeled as a new adapter in front of the Case Intake Agent, not a new agent: `POST /case/intake/voice` accepts audio, runs STT (e.g., Whisper-class model) to transcript, then calls the exact same `IntakeService.submit_message` path. TTS on the response is a symmetric adapter on the way out. The graph and agents never know whether input originated as text or voice — this is why `CaseState.messages` is text-only (§3.2, §8.11).

## 11.7 Document/image OCR

- New `POST /case/evidence/upload` accepts files, runs OCR (Tesseract or a Gemma vision variant) as a background task, and feeds extracted text into the *existing* `EvidenceAnalysisAgent` input as another `EvidenceItem` — again, a new adapter at the edge, not a new agent or a new schema. This is the payoff of ADR-3 (strict typed contracts): OCR output just needs to become a valid `EvidenceItem`, and everything downstream (completeness scoring, risk assessment, strategy) already knows how to consume it.

## 11.8 Court judgment prediction (future agent)

- A 12th agent (`JudgmentPredictionAgent`) becomes viable once there's a labeled outcome dataset (real or synthetic case outcomes correlated with `RiskAssessment` + `JudgeOpinion` history). It would slot into the graph as an optional node after `judge_agent`, consuming the same `CaseState` — the graph's extensibility (ADR-1) is exactly what makes adding a 12th node later a graph-definition change, not an architecture change.

## 11.9 Fine-tuned models

- `agent_logs` + stored `AgentResult`s are, from day one, a training-data-in-waiting: every (prompt, structured output, downstream outcome) triple is already captured. A future fine-tuning pipeline (LoRA on Gemma) for specific agents (Opposition Lawyer's adversarial reasoning and Judge Agent's calibration are the two most likely candidates) can be built as an offline batch job reading `agent_logs`, without any change to how agents are invoked at runtime — `llm/gemma_client.py` just points at a new model artifact.

## 11.10 What we are explicitly *not* over-building now

Per the project's own instructions and this package's engineering values (§1.1): no Kubernetes manifests, no multi-region failover design, no dedicated microservice split, and no fine-tuning pipeline are being built in the first implementation pass. Docker Compose (single-host: API, worker, Postgres, Redis, vLLM) is the correct starting deployment target — everything above is a documented *path*, not a day-one requirement, so the initial build stays shippable instead of speculative.

---

**End of architecture package.** See [00-README.md](00-README.md) for the full index. Awaiting approval before module-by-module implementation begins.
