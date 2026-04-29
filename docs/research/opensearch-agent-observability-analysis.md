# OpenSearch 3.6 Agent Observability — Integration Analysis

**Status:** Draft / planning. Local only — not yet committed.
**Branch:** `claude/plan-analysis-tool-yAI8I`
**Date:** 2026-04-29
**Author:** Planning pass (Claude Code)

## 1. Framing

We are not adopting "all of OpenSearch." We are adopting the parts of the
OpenSearch 3.6 stack that move three specific needles:

1. **Agent introspection** — what happened during a session, at the span level,
   across LLM calls, tool calls, retrieval, and sub-agent invocations.
2. **Workflow refinement** — the ability to look at a failed or slow run,
   form a hypothesis, query the corpus, and feed the answer back into our
   review / improvement loop (Phases 15, 17, 20).
3. **Session-as-search-corpus** — sessions become first-class searchable
   records with proper text + vector + structured query, replacing our current
   in-memory `TraceCollector` + file-backed `OrchestrationStateStore` path.

OpenSearch 3.6 is the first LTS release of the project and the agent-tracing
work is built on standard OpenTelemetry semantic conventions
(`gen_ai.*`). That makes it a stable, vendor-neutral substrate to bet on, not
a proprietary detour.

## 2. The "is this real?" question, settled

- **Agent Traces is GA, not a mock.** Released in OpenSearch 3.6 (LTS),
  Apache 2.0 licensed.
- **OTLP-native.** Any process that emits OpenTelemetry spans with
  `gen_ai.operation.name`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`,
  `gen_ai.tool.name`, etc., shows up correctly in the Dashboards UI. The
  OpenSearch GenAI Python SDK
  (`opensearch_genai_observability_sdk_py`) is one way to emit those spans,
  but it is not the only way.
- **Claude Code already emits OTLP** when `CLAUDE_CODE_ENABLE_TELEMETRY=1`
  plus the standard `OTEL_*_EXPORTER` / `OTEL_EXPORTER_OTLP_ENDPOINT` are set.
  No code change required to capture Claude Code sessions.
- **OpenAI Codex CLI and GitHub Copilot CLI do not emit OTLP today.** A thin
  proxy wrapper is required to attribute their tool calls and token usage.
  This is real engineering, not zero-config — it must be scoped honestly.

## 3. Where AGENT-33 stands today

Audit of the engine (file paths and lines from a fresh codebase pass):

**Observability subsystem** (`engine/src/agent33/observability/`):
- `trace_models.py` — Session → Run → Task → Step → Action hierarchy, plus
  `TraceContext`, `TraceEvidence`, `TraceMetadata` (lines 1–187).
- `trace_collector.py` — `TraceCollector` keeps traces and failures in an
  in-process dict and optionally serialises them to a file-backed
  `OrchestrationStateStore` namespace `"traces"` (lines 1–309).
- `failure.py` — failure taxonomy `F-ENV / F-INP / F-EXE / F-TMO / F-RES /
  F-SEC / F-DEP / F-VAL / F-REV / F-UNK` with retryable + escalate-after
  metadata (lines 1–190).
- `tracing.py` — optional OpenTelemetry hook, but **only wires
  `ConsoleSpanExporter`**. There is no real backend exporter (lines 1–71).
- `metrics.py`, `http_metrics.py`, `effort_telemetry.py` — in-memory metric
  collectors, no remote sink.
- `insights.py` — `InsightsEngine` aggregates metrics into an
  `InsightsReport`, but only exposes it via API; no dashboard.
- `alerts.py` — `AlertManager` evaluates threshold rules against in-memory
  metrics. No persistence, no cross-tenant view.

**API surface:** `/v1/traces` in `engine/src/agent33/api/routes/traces.py`
exposes `POST /`, `GET /`, `GET /{id}`, `POST /{id}/actions`,
`POST /{id}/complete`, `POST /{id}/failures`, `GET /{id}/failures`.

**Storage:** No Postgres trace tables. `engine/alembic/versions/001_initial.py`
creates `workflow_checkpoints`, `sessions`, `memory_documents` (pgvector).
Trace state lives in memory plus optional file persistence.

**Frontend:** `frontend/src/components/WorkflowGraph.tsx` (ReactFlow DAG of
workflow steps), `WorkflowStatusNode.tsx`, `ObservationStream.tsx`
(SSE listener for live events). **No span tree, no Gantt, no token-usage view,
no trace map.**

**OpenSearch / Elasticsearch / Kibana references:** zero.
**Real OTel exporter:** none.

So the gap to close is: ship a real exporter, ship persistence, ship the UI.
Most of that already exists in OpenSearch 3.6 — we should not rebuild it.

## 4. Shortlist — what to integrate, why, in priority order

### Tier A — Adopt (clearly wins; replaces or fills a real gap)

| # | OpenSearch capability | Replaces / fills |
|---|---|---|
| A1 | **Agent Traces (Dashboards plugin + OTel ingest)** | The missing exporter on `tracing.py`. The missing trace-tree / Gantt / span-detail UI. The missing per-session token + cost rollup. |
| A2 | **OpenSearch Observability Stack bundle** (OTel Collector + Data Prepper + OpenSearch + Dashboards) | Our absent backend. Ships as a single deployable. |
| A3 | **Dashboards Investigation** (3.6 feature: hypothesis, duration tracking, telemetry, log rerun) | Phase 15 review walk-throughs, Phase 20 lessons-learned capture. Today these are markdown notes; here they become structured artifacts attached to a trace. |
| A4 | **PPL + Query Insights + Top-N visualisations** | "Search our sessions" use case. Today we have BM25 + pgvector over memory docs; PPL gives operators a queryable language over the trace corpus directly, plus query-perf insights. |
| A5 | **Application Performance Monitoring (RED metrics, auto service topology)** | Hand-built `MetricsCollector` + `InsightsEngine`. APM auto-derives the agent-to-tool-to-model topology from spans. |

### Tier B — Adopt but smaller blast radius

| # | Capability | Notes |
|---|---|---|
| B1 | **Alerting plugin** | Migrate `AlertManager` rules to OpenSearch monitors. Alert webhooks loop back to our `automation/webhooks` so HITL escalation still flows through the engine. |
| B2 | **Anomaly Detection** | Detectors for: failure-rate spikes (per `gen_ai.failure.category`), token-usage outliers per session, tool-latency drift vs trailing-7d baseline, auth-failure clustering per tenant. |
| B3 | **Search Relevance Workbench (Recall@K, MRR, DCG@K)** | Wire against GT-01..GT-07 golden cases in `evaluation/`. Adds an objective measure to RAG changes. |

### Tier C — Evaluate, don't adopt blind

| # | Capability | Why evaluate |
|---|---|---|
| C1 | **ML Commons Agentic Memory (semantic + hybrid memory APIs)** | Overlaps `engine/src/agent33/memory/`. Could be a stronger long-term memory backend than pgvector + BM25, but only if it gives us multi-tenant routing and per-session retention controls. Spike, don't adopt. |
| C2 | **k-NN with 1-bit quantisation + vector prefetch** | Possible pgvector replacement (32× compression, +24% recall, −15% latency claimed). Benchmark against our golden cases. **Decision gate:** only consider replacing pgvector if Workbench shows ≥10% recall improvement at equal-or-better p95 latency. |
| C3 | **OpenSearch Launchpad** (AI-powered local provisioning) | Could replace parts of our docker-compose bootstrap. Low value if we're already running. Reconsider if onboarding friction shows up. |

### Tier D — Reject for our scope

| # | Capability | Reason |
|---|---|---|
| D1 | ML Commons V2 chat agent | Competes with `AgentRuntime`. Would balkanise our agent-definitions JSON catalogue. We use OpenSearch as the *observability* substrate, not the agent runtime. |
| D2 | Plan-Execute-Reflect agents | Same reason as D1. Our DAG workflow engine is already the orchestrator. |
| D3 | Security Analytics (SIEM) | Out of scope. `security/` covers prompt-injection + auth. Adding SIEM-grade detector packs is a different product. |
| D4 | SQL endpoint, Prometheus rules via SQL | Duplicates our existing metrics + API path. |
| D5 | Field-Level Security, gRPC auth | `AuthMiddleware` already handles tenant scoping at the API edge. |
| D6 | Terraform anomaly automation | We do not manage infra-as-code; premature. |

## 5. Target architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       AGENT-33 engine (Python)                      │
│                                                                     │
│   AgentRuntime  WorkflowExecutor  ToolRegistry  RAGPipeline         │
│       │              │                │              │              │
│       └──────────────┴────────┬───────┴──────────────┘              │
│                               ▼                                     │
│                   observability/exporters/otlp.py                   │
│                   (NEW — emits gen_ai.* spans)                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ OTLP gRPC
                                 ▼
                    ┌────────────────────────┐
                    │  OpenTelemetry Collector│ ◀── Claude Code CLI
                    │  (in observability      │     (CLAUDE_CODE_
                    │   docker profile)       │      ENABLE_TELEMETRY)
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Data Prepper          │
                    │  (gen_ai pipeline)     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  OpenSearch 3.6 LTS    │
                    │  - traces-* indices    │
                    │  - metrics-* indices   │
                    │  - investigations-*    │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼─────────────────┐
                ▼                ▼                 ▼
          Dashboards UI    Alerting plugin   Anomaly Detection
                │
                ▼
         Embedded in our frontend (iframe / deep-link)
```

Codex CLI / Copilot CLI sessions feed in only if we ship the optional shim
(see Phase OS-2). They are explicitly preview-quality.

## 6. Phased plan

Each phase is sized to be a single PR or a tight pair of PRs. None of this
gets pushed yet.

### Phase OS-1 — Telemetry backbone (foundation)

**Deliverables:**
- New module `engine/src/agent33/observability/exporters/otlp.py` that wires a
  real OTLP gRPC/HTTP exporter to `TracingManager`. Off by default;
  opt-in via `OTEL_EXPORTER_OTLP_ENDPOINT` already in our config style.
- Span emission added to:
  - `agents/runtime.py` — span per `invoke`, attributes:
    `gen_ai.operation.name=invoke_agent`, `gen_ai.agent.id`,
    `gen_ai.request.model`, `gen_ai.usage.input_tokens`,
    `gen_ai.usage.output_tokens`, `tenant.id`, `session.id`.
  - `workflows/execution.py` — span per step.
  - `tools/registry.py::validated_execute` — span per tool call,
    attribute `gen_ai.tool.name`.
  - `memory/rag.py` — span per retrieval, attribute
    `gen_ai.operation.name=retrieve`.
- `engine/docker-compose.yml` gains an opt-in `observability` profile:
  OpenSearch + Dashboards + OTel Collector + Data Prepper.
- Docs: `docs/operators/opensearch-observability-setup.md`.
- Tests: span-emission unit tests with the in-memory OTel SDK exporter; an
  integration test that brings the docker profile up and asserts at least one
  span lands in `traces-*`.

**Anti-corner-cutting note:** the integration test must assert on indexed
document shape, not just "200 OK" from OS. Tests that only check "OS is
reachable" are exactly the shallow pattern CLAUDE.md flags.

### Phase OS-2 — Multi-source CLI capture

**Deliverables:**
- Document the Claude Code → OpenSearch path (env vars + collector config) —
  no engine code change.
- Optional `tools/cli-otel-shim/` — a Python wrapper (~200 LoC) that proxies
  `codex` / `copilot` CLI invocations through a pseudo-tty, parses observable
  signals from stdout (model name, tool calls, token totals when surfaced),
  and emits `gen_ai`-attributed spans.
- **Honest scope label:** the shim is best-effort. Tools that don't surface
  structured stdout will produce sparse spans. Frontend must label these
  sessions as `(preview)` and we must not back SLOs with them. This is called
  out up-front so we don't ship "all CLIs supported" and quietly mean
  "Claude Code supported, the rest are sparse."

### Phase OS-3 — Investigation UI in the frontend

**Deliverables:**
- Provision saved Dashboards objects as NDJSON under
  `infrastructure/opensearch/dashboards/`:
  - "Agent Trace Overview" (uses the OS plugin's built-in views).
  - "Failure Taxonomy" — donut over `gen_ai.failure.category` mapped from
    our F-* enum.
  - "Token & Cost per Session" — sum of `gen_ai.usage.*tokens` × model rate.
  - "Tool Latency Heatmap" — p50/p95/p99 per `gen_ai.tool.name`.
- Use Dashboards Investigation templates as the canonical surface for
  Phase 15 review walk-throughs and Phase 20 lessons-learned. The hypothesis,
  attached spans, and rerun results live in OS, not in markdown notes.
- Frontend integration choice: **embedded iframe** with OS as the rendering
  layer, deep-linked from our session list. Simpler, faster, fewer custom
  components to maintain. Building a from-scratch span-tree in React is
  rejected on cost.

### Phase OS-4 — Alerting + Anomaly Detection

**Deliverables:**
- Migrate `observability/alerts.py` rules to OpenSearch Alerting monitors
  (NDJSON-defined, version-controlled).
- Define four anomaly detectors (listed in Tier B2 above).
- Wire OS alert webhooks back into our `automation/webhooks` so HITL
  escalation still flows through the engine and the existing review pipeline.

### Phase OS-5 — Search & evaluation augmentation

**Deliverables:**
- Mirror `memory/` corpus into a parallel OS index, **read-only beside
  pgvector**, not a replacement.
- Wire Search Relevance Workbench against GT-01..GT-07. Emit Recall@K, MRR,
  DCG@K back into `evaluation/` metrics.
- Decision gate written into the phase exit: only consider replacing pgvector
  if the Workbench numbers clear the +10% recall / equal-or-better p95
  latency bar. Otherwise document, stop, and keep pgvector.

### Phase OS-6 (deferred) — k-NN + ML Commons Agentic Memory spike

Spike only — produce a comparison memo. No production wiring.

## 7. Risks and unresolved decisions

1. **Docker footprint.** Full observability stack is heavy. Must remain an
   opt-in compose profile, not part of the default `docker compose up` path.
2. **`gen_ai` semantic conventions are still evolving.** Pin to OS 3.6 + a
   specific OTel SemConv version. Document the upgrade path.
3. **Multi-tenancy.** Every span must carry `tenant.id` as a resource
   attribute, and OS index lifecycle must enforce per-tenant routing or RBAC.
   Open question: per-tenant index, or shared index with field-level filter?
   Today our auth model is API-key + JWT in `AuthMiddleware`. Need a decision
   before Phase OS-3.
4. **Codex / Copilot shim quality.** Best-effort only. Must be labelled.
5. **Looped agent on the other machine.** This branch must avoid edits to
   `docs/phases/`, `docs/next-session.md`, and `docs/progress/` so we don't
   collide with whatever the other agent is doing. This doc deliberately
   lives under `docs/research/` for that reason.

## 8. Out of scope (named explicitly)

- Replacing `AgentRuntime` with ML Commons agents.
- Self-hosting OpenSearch in production tenants by default. We ship a
  compose profile; ops owners decide managed vs self-hosted.
- Security Analytics SIEM rule packs.
- Dashboard duplication in our own React tree (we embed instead).

## 9. Open questions for the operator

These should be answered before Phase OS-3 starts. Local notes for now —
nothing pushed.

1. Self-hosted OpenSearch (compose) vs managed AWS OpenSearch Service?
   Affects the auth path (SigV4 vs basic / OIDC).
2. Tenant model: per-tenant index, or shared with field-level filtering?
3. Phase OS-5: parallel-forever, or pgvector-replacement-as-goal?
4. Codex / Copilot shim — Phase OS-2 priority, or punt to a later wave?

## 10. Sources

- OpenSearch 3.6 release notes — `github.com/opensearch-project/opensearch-build/blob/main/release-notes/opensearch-release-notes-3.6.0.md`
- AWS unified observability blog (Agent Traces ingest details, SDK package
  name, `gen_ai.*` semantic conventions) —
  `aws.amazon.com/blogs/big-data/unified-observability-in-amazon-opensearch-service-metrics-traces-and-ai-agent-debugging-in-a-single-interface/`
- Claude Code observability docs (OTLP env vars) —
  `code.claude.com/docs/en/agent-sdk/observability`
- OpenSearch trace getting-started — `docs.opensearch.org/latest/observing-your-data/trace/getting-started/`
- AWS OpenSearch AI observability docs — `docs.aws.amazon.com/opensearch-service/latest/developerguide/observability-ai.html`

## 11. Codebase touch-list (for the eventual implementation phase)

Files this work would touch, so a future implementer can scope quickly:

- `engine/src/agent33/observability/tracing.py` — replace ConsoleSpanExporter wiring.
- `engine/src/agent33/observability/exporters/otlp.py` — **new**.
- `engine/src/agent33/observability/alerts.py` — migrate rules out.
- `engine/src/agent33/agents/runtime.py` — span instrumentation.
- `engine/src/agent33/workflows/execution.py` — span instrumentation.
- `engine/src/agent33/tools/registry.py` — span around `validated_execute`.
- `engine/src/agent33/memory/rag.py` — span around retrieval.
- `engine/src/agent33/config.py` — `OTELExporterSettings` block.
- `engine/docker-compose.yml` — `observability` profile.
- `engine/pyproject.toml` — add `opentelemetry-sdk`,
  `opentelemetry-exporter-otlp` to an `observability` extra.
- `infrastructure/opensearch/dashboards/*.ndjson` — **new**.
- `tools/cli-otel-shim/` — **new**, optional.
- `frontend/src/components/SessionDetail.tsx` — embed Dashboards iframe.
- `docs/operators/opensearch-observability-setup.md` — **new**.

No code changes have been made for this analysis. Branch is clean.
