# OpenSearch 3.6 + Agentic Platform Backbone — Integration Analysis

**Status:** Draft / planning.
**Branch:** `claude/plan-analysis-tool-yAI8I`
**Date:** 2026-04-29
**Revision:** rev-2 (broadened scope — strategic backbone, not just observability)

> **rev-3 framing note (2026-04-29):** The operator has proposed a product
> split. Under that split, this entire plan targets **TIKNAS** — the
> internal codename for the enterprise orchestration platform that will
> launch publicly as **AGENTS33** on `agents33.com` — not AGENT33 (the
> singular autonomous agent product). See
> `docs/research/agent33-vs-tiknas-product-split.md` for the strategic
> case, the naming convention, and the open structural questions. The
> phase plan, tier matrices, and Path X / Y / Z fork below all become
> TIKNAS concerns; AGENT33 is unaffected by them. This header note is
> the only change made to this doc as a result — the body is preserved
> as the founding roadmap for TIKNAS once the split is confirmed.

## 1. Framing

The original framing of this doc was "use OpenSearch for observability." That
frame is too narrow for where we want AGENT-33 to land.

The revised vision is an **AI management / orchestration / refinement OS**:

- A library of canned workflows and canned agents, each with declared
  capabilities, costs, and provenance.
- A meta-monitoring layer that sees every agent, every tool call, every
  retrieval, every workflow step across the fleet — at enterprise scale
  (thousands of agents, hundreds of users).
- A search and analytics surface where every session is a queryable,
  rankable, replayable record.
- An extensible platform we can resell, embed in client systems, or operate
  ourselves.

In that frame the question is no longer "should we wire OpenSearch to our
TraceCollector?" — it is "what is the right backbone for an agentic
platform we plan to scale and sell, and how much of our existing stack do we
keep vs replace?"

This document answers that question with three things:
1. A revised adopt / evaluate / reject matrix for OpenSearch 3.6 capabilities,
   reopened per operator direction.
2. A competitive landscape — the OSS projects already doing this work, with
   honest comparisons.
3. Decision matrices for the swap-out questions
   (`AgentRuntime` vs alternatives; `pgvector` vs k-NN; etc.).

The three original needles still hold, but they are now sub-goals of the
platform vision:

1. **Agent introspection** — span-level visibility across LLM calls, tool
   calls, retrieval, sub-agents.
2. **Workflow refinement** — hypothesis-driven debugging fed back into our
   review / improvement loop (Phases 15, 17, 20).
3. **Session-as-search-corpus** — sessions become first-class searchable
   records with proper text + vector + structured query.

OpenSearch 3.6 is the first LTS release of the project. Its agent-tracing
work is built on standard OpenTelemetry semantic conventions (`gen_ai.*`),
which makes it a stable, vendor-neutral substrate. That stability matters
more than feature parity in any single area — we are picking a substrate to
build on for years, not a tool to use for one quarter.

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

## 4. Revised tier matrix (rev-2)

The original rev-1 tiers were challenged by the operator on two grounds:
former Tier C should adopt, not evaluate; and Tier D should be reopened
because the goal is to rebuild the backbone, not preserve our current
internals out of inertia. The new matrix reflects that direction with
explicit decision gates rather than blind acceptance — "reopen" is not the
same as "adopt unconditionally."

### Tier A — Adopt (high confidence; fills real gaps)

| # | Capability | Replaces / fills |
|---|---|---|
| A1 | **Agent Traces** (Dashboards plugin + OTel ingest) | Missing exporter on `tracing.py`. Missing trace-tree / Gantt / span-detail UI. Missing per-session token + cost rollup. |
| A2 | **Observability Stack bundle** (OTel Collector + Data Prepper + OpenSearch + Dashboards) | Absent backend. Ships as a single deployable. |
| A3 | **Dashboards Investigation** | Phase 15 review walk-throughs, Phase 20 lessons-learned capture. Markdown → structured artifact attached to trace. |
| A4 | **PPL + Query Insights + Top-N visualisations** | "Search our sessions" use case. Replaces ad-hoc SQL/log queries. |
| A5 | **APM (RED metrics + auto service topology)** | Hand-built `MetricsCollector` + `InsightsEngine`. |
| A6 | **Alerting plugin** | Migrate `AlertManager` rules to OpenSearch monitors. Webhooks loop back to `automation/webhooks` for HITL. |
| A7 | **Anomaly Detection** | Failure-rate spikes, token-usage outliers, tool-latency drift, auth-failure clustering. |
| A8 | **Search Relevance Workbench (Recall@K, MRR, DCG@K)** | Objective RAG quality bar wired to `evaluation/`. |

### Tier B — Adopt with explicit decision gates (formerly Tier C)

These move from "evaluate" to "adopt as default direction" per operator
direction, but each carries a **kill-switch criterion** that must be checked
before code changes ship. Adopting without gates is the substitution
anti-pattern.

| # | Capability | Adoption gate |
|---|---|---|
| B1 | **k-NN with 1-bit quantisation + vector prefetch** as **pgvector replacement** | Benchmark gate: against GT-01..GT-07 + a synthetic 1M-doc workload, k-NN must show **≥10% Recall@10 improvement at equal-or-better p95 latency**, OR ≥30% storage reduction at equal recall. If neither, keep pgvector and document. |
| B2 | **ML Commons Agentic Memory (semantic + hybrid memory APIs)** as **memory backend replacement** | API parity gate: it must support our existing memory features — per-tenant scoping, retention tiers, observation/summary ingestion, and progressive recall — without losing functionality. Spike implementation must run for 2 weeks against shadow traffic before full cutover. |
| B3 | **OpenSearch Launchpad** for local dev provisioning | Cost-benefit gate: only adopt if onboarding time-to-first-trace drops by ≥50% vs current docker-compose. |

### Tier C — Reopened with mandatory decision matrices (formerly Tier D)

Per operator direction, every former Tier D item is reopened. None of these
should be adopted on the strength of "OpenSearch ships it"; each gets a
matrix comparison against the best-in-class alternative before any code
moves. The matrices live in §6.

| # | Capability | Mandatory comparison |
|---|---|---|
| C1 | **ML Commons V2 Chat Agent** as `AgentRuntime` replacement | Matrix: vs current AgentRuntime + LangGraph + Claude Agent SDK + CrewAI. **OpenSearch's offering is not assumed to win.** |
| C2 | **Plan-Execute-Reflect agents** as workflow-engine replacement | Matrix: vs current DAG executor + LangGraph + CrewAI Crews + AutoGen GroupChat. |
| C3 | **Security Analytics** (SIEM) as security-event substrate | Matrix: vs current `security/` + Wazuh + Falco. Determine whether adoption broadens or narrows our security posture. |
| C4 | **SQL endpoint + Prometheus rules via SQL** as ops query layer | Matrix: vs current API + Prometheus + Grafana path. Decide whether SQL adds power or duplicates surface. |
| C5 | **Field-Level Security + gRPC auth** as authz substrate | Matrix: vs current `AuthMiddleware`. Multi-tenant routing requirements drive this — do not collapse FLS unless a clear operational simplification exists. |
| C6 | **Terraform anomaly automation** as infra-as-code layer | Matrix: only relevant after we adopt IaC at all. Defer until that decision is made. |

### Tier D — Hard reject (unchanged)

These remain rejected because they are out of scope for an AI-platform
product, not because they overlap our internals:

- **None at this revision.** Every former rejection has been promoted to
  Tier B or C. Document any new rejections inline with reasoning when they
  arise.

## 5. Competitive landscape — what already exists in this space

This is the most important section of rev-2. Before deciding to build the
"agentic platform backbone" on OpenSearch, we have to be honest about who is
already shipping that backbone and how much of it is overlap.

### 5.1 LLM / agent observability platforms

| Project | Stars | License | Self-host | Verdict for AGENT-33 |
|---|---|---|---|---|
| **Langfuse** | ~21k | MIT | Yes (battle-tested) | **The elephant in the room.** Tracing, evals, prompt management, datasets, playground, annotations. OTel-native ingest. Already does ~80% of what "AGENT-33 + OpenSearch Agent Traces" would do for the observability layer. Strongest single-project alternative to building on OS for this slice. |
| **Arize Phoenix** | ~4–5k | Elastic v2 | Yes (notebook + Docker) | OTel-native, strong on evals + prompt playground. Notebook-first. Less enterprise-grade than Langfuse, more researcher-grade. |
| **AgentOps** | ~3–4k | MIT | Yes | Multi-agent specific. Time-travel debugging is a real differentiator. Less general than Langfuse. |
| **OpenLLMetry / Traceloop** | ~3–4k | Apache 2.0 | Backend-agnostic | Pure decorator library that emits OTel spans. **Not a platform** — pairs with Langfuse / Phoenix / OS as the emit-side SDK. Likely useful in any path. |
| **Helicone** | ~3–4k | Apache 2.0 | Yes (proxy model) | Proxy-based capture. Different shape — sits between app and LLM. Does not fit our internal-instrumentation model as cleanly. |
| **LangSmith** | n/a | Closed | No (SaaS) | Strongest agent observability product, but closed source. Not viable for a self-host / resell platform. |

### 5.2 Full agentic platforms (workflow + agents + dashboards)

| Project | Stars | License | Self-host | Verdict for AGENT-33 |
|---|---|---|---|---|
| **Dify** | ~90k+ | Dify OSS (Apache-derived w/ multi-tenant clause) | Yes | **The other elephant.** Workflow builder, RAG, agent definitions, dashboards, datasets, evals, API publishing. Closest existing match to the "AI management OS" vision. Must be evaluated explicitly as build-on-top-of vs build-against. |
| **Langflow** (DataStax) | ~40–60k | MIT | Yes | Visual flow builder for LangChain/LangGraph. Strong frontend, weaker on observability and evals. |
| **Flowise** | ~30k+ | Apache 2.0 | Yes | Visual builder, LangChain-based. Lighter weight than Dify, less platform. |
| **n8n** | ~70k+ | Sustainable Use License | Yes | Generic workflow automation with AI nodes. Adjacent rather than direct competitor — the workflow primitives are the win. |
| **AutoGen Studio** | (part of AutoGen ~30k) | MIT | Yes | UI for Microsoft AutoGen. Multi-agent orchestration UI. Research-grade. |

### 5.3 "Agent OS" experiments

These define the design space rather than offer a drop-in option:

| Project | Stars | Notes |
|---|---|---|
| **AIOS (agiresearch)** | research-grade | Kernel abstraction over LLM/memory/storage/tools. Academic reference design. |
| **SmythOS SRE** | medium | Cloud-native runtime with 40+ production components, OS-level abstractions over LLMs/vector DBs/storage/caching. Closest to "agentic OS" as a product. |
| **Rivet agent-os** | small/medium | WASM + V8 isolate runtime. Solves the "fast cold start" sandbox problem. Different layer than what we need. |
| **awesome-agentOS** | n/a | Curated list of related projects. Useful as a discovery surface. |

### 5.4 Agent runtime frameworks (the C1 / C2 matrix candidates)

| Project | Stars | License | Notes |
|---|---|---|---|
| **LangChain + LangGraph** | ~97k | MIT | Dominant ecosystem. LangGraph is the stateful-workflow piece. |
| **CrewAI** | ~30k | MIT | Role-based multi-agent. A2A protocol support. |
| **AutoGen** | ~30k+ | MIT | Microsoft. GroupChat / actor model. |
| **Strands Agents** | early | Apache 2.0 | AWS, deeply Bedrock-coupled. Less portable. |
| **Claude Agent SDK** | early | Open | Extracted from Claude Code. Closest model fit for our existing Anthropic-heavy stack. |
| **OpenSearch ML Commons V2 Chat Agent** | bundled in OS | Apache 2.0 | Notably absent from every 2026 framework comparison we found — it's positioned as observability-adjacent, not as a top-tier agent runtime. |

### 5.5 Honest read of the landscape

Three things stand out:

1. **OpenSearch is the strongest pick for the indexing / search / dashboards
   / anomaly-detection layer.** PPL, Query Insights, k-NN at scale, and
   Dashboards Investigation have no OSS equivalents at the same maturity.
2. **OpenSearch is not the strongest pick for the agent runtime layer.** ML
   Commons V2 doesn't appear in serious framework comparisons. LangGraph,
   Claude Agent SDK, and CrewAI are where the runtime mind-share has
   consolidated.
3. **Langfuse and Dify already exist and already do much of what we want.**
   Pretending they don't and rebuilding on raw OpenSearch is a
   multi-quarter detour.

The strategic implication is in §7.

## 6. Decision matrices for the swap-out questions

Each Tier B and Tier C item gets a matrix here. None of these are decided —
they are the work to be done before any code change ships.

### 6.1 `AgentRuntime` replacement (Tier C1)

Comparison axes — the same axes apply across all candidates so the result is
a real ranking, not a feature-checklist beauty contest.

| Axis | Current AgentRuntime | LangGraph | Claude Agent SDK | CrewAI | ML Commons V2 |
|---|---|---|---|---|---|
| Multi-tenancy | First-class (`tenant_id` everywhere) | Manual | Manual | Manual | Index-level |
| Capability taxonomy | 25-entry P/I/V/R/X catalogue | Tool-level only | Tool-level only | Tool-level only | Plugin-level |
| Skills / progressive disclosure | L0/L1/L2 injector | n/a | n/a | n/a | n/a |
| Agent-definition format | JSON, file-loaded | Python code | Python code | Python code | OS API |
| Streaming + retry parity | `run_stream()` w/ regression contracts | LangGraph streams | SDK streams | Crew streams | OS streams |
| Workflow integration | DAG via `workflows/` | Native | Manual | Native | Manual |
| Observability hook | TraceCollector (today) | LangSmith / OTel | OTel | OTel | OS native |
| Cost model | Effort-routing telemetry | Manual | Manual | Manual | OS metering |
| Production maturity | In-house | Very high | High (new) | High | Lower |
| Resell / embed friendliness | Ours, full control | License compatible | License compatible | License compatible | Tied to OS |

**Decision rule:** rank each axis 1–5, weight axes by importance to the
platform vision (multi-tenancy, observability hook, resell friendliness
weighted highest), and pick the top-2 to spike. Do not pick on a single
axis.

### 6.2 Workflow engine replacement (Tier C2)

Axes: stateful checkpoint, resume-after-failure, parallel groups, conditional
branching, sub-workflow composition, observability hook, expression
language, retries+timeouts policy, multi-tenancy, codebase footprint.

Candidates: current `workflows/` DAG executor, LangGraph, AutoGen GroupChat,
CrewAI Crews, Plan-Execute-Reflect agents.

### 6.3 Memory backend replacement (Tier B2)

Axes: vector recall, hybrid (BM25 + vector) RRF support, per-tenant scoping,
retention tiers, ingestion throughput, observation-summarisation hook,
progressive-recall API, embedding-cache integration, multi-region, cost.

Candidates: current `memory/` (pgvector + BM25 + RAG), ML Commons Agentic
Memory, Letta (formerly MemGPT), Zep, Mem0.

### 6.4 Vector substrate replacement (Tier B1)

Axes: recall@K against GT cases, p50/p95/p99 latency, storage footprint,
update throughput, ANN algorithm choice, GPU acceleration, multi-tenancy,
license.

Candidates: current pgvector, OpenSearch k-NN with 1-bit quantisation,
Weaviate, Qdrant, Milvus.

### 6.5 Authz substrate (Tier C5)

Axes: tenant isolation guarantees, audit trail, integration with our
`AuthMiddleware`, blast radius of misconfiguration, ease of multi-tenant
routing, RBAC complexity.

Candidates: current `AuthMiddleware`, OpenSearch FLS + gRPC auth, OPA
policy layer.

### 6.6 Security event substrate (Tier C3)

Axes: prompt-injection coverage, auth-failure detection, tenant isolation,
SIEM integration, alert routing.

Candidates: current `security/` (prompt injection + allowlists), OpenSearch
Security Analytics, Wazuh, Falco.

## 7. Strategic fork — Langfuse vs OpenSearch vs both

This is the question rev-2 has to put on the table:

**Path X — Build on OpenSearch only.** Treat OpenSearch as the unified
backbone for traces, search, indexing, anomaly detection, dashboards,
alerting. Build our own UI shell on top.
- *Pros:* Single backend. LTS support. Strongest at-scale search.
- *Cons:* Reinvent the LLM-observability UX (trace evals, prompt mgmt,
  dataset workflows) that Langfuse already ships. Bigger frontend effort.

**Path Y — Build on Langfuse + Dify only.** Adopt Langfuse for observability
and Dify for the platform layer. Skip OpenSearch.
- *Pros:* Fastest time-to-product. Two strong projects to compose.
- *Cons:* Inherits both projects' constraints. Langfuse uses ClickHouse +
  Postgres, not OpenSearch — search/PPL is out. No first-class anomaly
  detection. Dify has its own opinions about workflow + agent shapes that
  may not match ours.

**Path Z — Compose: Langfuse for observability UX, OpenSearch for
search/anomaly/dashboards backbone, our engine on top.** Use Langfuse as the
LLM-trace UI; export the same OTel spans into OpenSearch for PPL queries,
Dashboards Investigation, anomaly detection, and Search Relevance
Workbench. Treat them as complementary layers, not competitors.
- *Pros:* Each tool used at its strength. Operators get Langfuse's polished
  trace UI for day-to-day; engineers get OpenSearch's power for fleet-scale
  analytics.
- *Cons:* Two backends to operate. Slight duplication of trace storage.

**Recommendation (open for operator override):** Path Z is the strongest
default. It uses Langfuse where Langfuse already wins (trace UX, evals,
prompt management) and OpenSearch where OpenSearch already wins (PPL, k-NN
at scale, anomaly detection, dashboards). It also reduces the "rip out our
backend" surface area — most of our existing code (AgentRuntime, workflows,
memory) stays, and we add two complementary substrates underneath.

If the operator decision is Path X (OpenSearch only), the phase plan in §9
needs an additional Phase OS-3.5 for "build the LLM-trace UI we would have
gotten from Langfuse." That is a real cost and should be sized before the
choice is locked.

## 8. Target architecture (Path Z draft)

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

## 9. Phased plan

Each phase is sized to be a single PR or a tight pair of PRs. Nothing in
this plan should be published yet. Rev-2 adds Phase OS-0 — the landscape
spike has to land before any code change.

### Phase OS-0 — Decision spike (no production code)

**Goal:** retire the open questions in §7 and §6 with evidence, not opinion.

**Deliverables:**
- Stand up Langfuse self-host locally (docker compose). Send a real AGENT-33
  session through it via OTel decorators. Capture screenshots, latency, UX
  notes.
- Stand up OpenSearch 3.6 + Dashboards locally. Send the same session
  through it. Capture the same evidence.
- Stand up Dify locally. Recreate one canned workflow we already have.
  Document where Dify's primitives match vs diverge from our DAG.
- Run the matrices in §6 with rough scoring (1–5 per axis, weighted). At
  least axes 6.1 (AgentRuntime), 6.3 (memory), 6.4 (vector) before any
  Tier B/C decision is locked.
- Output: `docs/research/opensearch-spike-results.md` with hard data.

**Exit criteria:** the operator can pick Path X / Y / Z (§7) on evidence,
not on this doc's recommendation.

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

## 10. Risks and unresolved decisions

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

## 11. Out of scope (named explicitly)

Rev-2 narrows this list because most of the original rejections are now in
Tier C with mandatory matrices.

- Self-hosting OpenSearch in production tenants by default. We ship a
  compose profile; ops owners decide managed vs self-hosted.
- Dashboard duplication in our own React tree where Dashboards Investigation
  + Langfuse already cover the use case (we embed / link out instead).
- Replacing battle-tested OSS components with hand-built equivalents when
  the OSS project is healthy and licence-compatible. The `simplify` rule.

## 12. Open questions for the operator

These should be answered during Phase OS-0. Draft notes for now — not
ready for publication.

**Strategic (block Phase OS-1):**
1. **Path X / Y / Z (§7):** OpenSearch only, Langfuse + Dify only, or
   compose Path Z? Recommendation: Path Z. Operator choice locks the rest
   of the plan.
2. **AgentRuntime replacement (Tier C1):** keep current, swap to LangGraph,
   swap to Claude Agent SDK, swap to ML Commons V2, or run a 4-way spike?
3. **Memory backend replacement (Tier B2):** keep pgvector + BM25, or run
   the parity gate against ML Commons Agentic Memory?

**Tactical (block Phase OS-3):**
4. Self-hosted OpenSearch (compose) vs managed AWS OpenSearch Service?
   Affects the auth path (SigV4 vs basic / OIDC).
5. Tenant model: per-tenant index, or shared with field-level filtering?
6. Codex / Copilot shim — Phase OS-2 priority, or punt to a later wave?

**Productisation (block any resell story):**
7. Do we want the resulting platform to be open source, source-available,
   or proprietary? Affects which OSS licences we can build on (Dify's
   multi-tenant clause, Langfuse MIT, OpenSearch Apache 2.0, n8n SUL).
8. Do we publish AGENT-33 packs (canned workflows, canned agents) as a
   marketplace? If yes, packaging format becomes a Phase OS-3 concern.

## 13. Sources

OpenSearch 3.6 + Agent Traces:
- OpenSearch 3.6 release notes — `github.com/opensearch-project/opensearch-build/blob/main/release-notes/opensearch-release-notes-3.6.0.md`
- AWS unified observability blog (Agent Traces ingest details, SDK package
  name, `gen_ai.*` semantic conventions) —
  `aws.amazon.com/blogs/big-data/unified-observability-in-amazon-opensearch-service-metrics-traces-and-ai-agent-debugging-in-a-single-interface/`
- OpenSearch trace getting-started — `docs.opensearch.org/latest/observing-your-data/trace/getting-started/`
- AWS OpenSearch AI observability docs — `docs.aws.amazon.com/opensearch-service/latest/developerguide/observability-ai.html`

Claude Code OTLP path:
- Claude Code observability docs (OTLP env vars) —
  `code.claude.com/docs/en/agent-sdk/observability`

Competitive landscape (rev-2 research):
- Langfuse — `github.com/langfuse/langfuse` (~21k stars, MIT)
- Arize Phoenix — `github.com/arize-ai/phoenix`
- Dify — `github.com/langgenius/dify` (~90k+ stars)
- Langflow — DataStax; visual LangGraph builder (~40–60k stars)
- Flowise — `flowiseai.com` (~30k stars)
- AIOS — `github.com/agiresearch/AIOS`
- SmythOS SRE — `github.com/SmythOS/sre`
- Rivet agent-os — `github.com/rivet-dev/agent-os`
- awesome-agentOS — `github.com/Egv2/awesome-agentOS`
- OpenLLMetry / Traceloop — Apache 2.0 OTel decorator library
- AgentOps — multi-agent observability (~3–4k stars)

Agent runtime frameworks (Tier C1 matrix candidates):
- LangGraph + LangChain — ~97k stars, MIT
- CrewAI — ~30k stars, MIT, A2A protocol
- AutoGen — ~30k+ stars, MIT
- Strands Agents — AWS, Bedrock-coupled
- Claude Agent SDK — extracted from Claude Code

## 14. Codebase touch-list (for the eventual implementation phase)

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
