# P1.6 Bottleneck Analysis Report

**Date**: 2026-03-24
**Scope**: Analysis of P1.3 (connection pool tuning), P1.4 (query profiling),
and P1.5 (load-test harness) infrastructure to identify performance
bottlenecks and inform P1.7 regression guardrails.

---

## Section 1: Load Test Architecture Review

### Harness Overview (P1.5)

The load-test harness lives in `load-tests/` and uses
[Locust](https://locust.io/) for Python-native scenario authoring. It defines
four user types (weighted by expected production traffic ratios) and three
scenario profiles.

### User Scenarios

| User Type | Weight | Wait Time | Endpoints Exercised |
| --- | --- | --- | --- |
| `HealthCheckUser` | 3 (~43%) | 0.1-0.5s | `GET /healthz`, `GET /readyz`, `GET /health` |
| `AgentInvokeUser` | 2 (~29%) | 1.0-3.0s | `POST /v1/agents/{name}/invoke` |
| `MetricsScrapeUser` | 1 (~14%) | 10.0-30.0s | `GET /metrics` |
| `SessionLifecycleUser` | 1 (~14%) | 2.0-5.0s | `POST /v1/sessions/` create, `GET /v1/sessions/{id}`, `GET /v1/sessions/?limit=10`, `POST /v1/sessions/{id}/end` |

**Design notes:**

- `HealthCheckUser` has the highest weight (3) to mirror real Kubernetes
  liveness/readiness probe traffic.
- `AgentInvokeUser` randomly selects from all 6 registered agent definitions
  (`orchestrator`, `director`, `code-worker`, `qa`, `researcher`,
  `browser-agent`) and uses lightweight prompt payloads.
- `MetricsScrapeUser` simulates Prometheus scrape intervals (10-30s).
- `SessionLifecycleUser` exercises the full create-query-list-end cycle;
  each iteration creates a fresh session, which stresses file-backed session
  storage under concurrency.
- All authenticated scenarios use Bearer token auth. Missing tokens are
  reported as failures (not silently skipped).

### Scenario Profiles

| Profile | Users | Spawn Rate | Duration | Intent |
| --- | --- | --- | --- | --- |
| `light.yaml` | 10 | 2/s | 60s | Post-deploy smoke validation |
| `standard.yaml` | 50 | 5/s | 120s | Sustained normal-load SLO check |
| `stress.yaml` | 200 | 10/s | 180s | Capacity ceiling discovery |

**Acceptance criteria** (from `profiles/single-instance-baseline.md`):

- Light: 0% failure rate, `/healthz` p95 < 50ms, agent invoke p95 < 5s.
- Standard: < 1% failure rate, no 5xx on health/metrics endpoints.
- Stress: < 5% failure rate, `/healthz` p95 < 200ms. Agent invoke degradation
  (p95 > 5s) is expected due to LLM inference queuing.

### Limitations Acknowledged in P1.5

1. **LLM inference dominates agent invoke latency** -- Ollama queue depth is
   the bottleneck, not the AGENT-33 API layer itself.
2. **File-backed session storage** can show contention under stress.
3. **Health probes synchronously call external dependencies** (Ollama, Redis,
   PostgreSQL, NATS), so readyz latency correlates with backing service load.

---

## Section 2: Connection Pool Configuration Impact

### Config Knobs Added in P1.3

| Setting | Default | Type | Location |
| --- | --- | --- | --- |
| `db_pool_size` | 10 | `int` | `config.py` line 39 |
| `db_max_overflow` | 20 | `int` | `config.py` line 40 |
| `db_pool_pre_ping` | `True` | `bool` | `config.py` line 41 |
| `db_pool_recycle` | 1800 | `int` (seconds) | `config.py` line 42 |
| `redis_max_connections` | 50 | `int` | `config.py` line 46 |

These are consumed in the lifespan:

- `LongTermMemory.__init__()` passes `pool_size`, `max_overflow`,
  `pool_pre_ping`, and `pool_recycle` directly to SQLAlchemy's
  `create_async_engine()`.
- The Redis client is created via `aioredis.from_url()` with
  `max_connections=settings.redis_max_connections`.

### Scenario-Specific Impact Analysis

| Parameter | Light (10 users) | Standard (50 users) | Stress (200 users) |
| --- | --- | --- | --- |
| `db_pool_size=10` | Sufficient. 10 concurrent users rarely saturate. | Adequate. Memory queries are fast; pool contention unlikely. | **Risk.** 200 users with concurrent memory search/store can exhaust 10 base connections, forcing overflow allocation. |
| `db_max_overflow=20` | Never reached. | Occasionally reached during burst. | **Critical.** Total pool ceiling is 30 connections (10+20). If >30 concurrent DB-bound coroutines execute simultaneously, additional requests will block waiting for a connection, causing latency spikes. |
| `db_pool_pre_ping=True` | Negligible overhead. Prevents stale-connection errors. | Same. Adds ~1ms RTT per connection checkout but prevents silent connection drops. | Same. The pre-ping overhead is negligible compared to query time; keep enabled. |
| `db_pool_recycle=1800` | No impact (test runs < 60s). | No impact (test runs 120s). | No impact (test runs 180s). Recycle matters for long-running production deployments where idle connections may be terminated by cloud PG proxies (e.g., PgBouncer, RDS proxy). |
| `redis_max_connections=50` | Sufficient. | Sufficient. | **Monitor.** 200 concurrent users with Redis cache lookups could approach 50 connections. Redis operations are fast (~0.1ms), so connection reuse is high, but burst patterns could spike. |

### Recommended Baseline Values

| Parameter | Current Default | Recommended | Rationale |
| --- | --- | --- | --- |
| `db_pool_size` | 10 | **10** | Appropriate for single-instance. Matches typical asyncpg connection count for one Uvicorn worker. Increase only if stress testing shows pool exhaustion. |
| `db_max_overflow` | 20 | **20** | 2x the pool size gives adequate burst headroom. Total ceiling 30 is reasonable for single-instance. |
| `db_pool_pre_ping` | `True` | **True** | Must stay enabled. Prevents `ConnectionRefusedError` after idle periods or PG restarts. The ~1ms overhead per checkout is negligible. |
| `db_pool_recycle` | 1800 | **1800** | 30 minutes is standard for cloud PostgreSQL. Prevents stale connections after proxy-level idle timeouts (AWS RDS default: 1800s). Reduce to 900 if behind PgBouncer with aggressive timeouts. |
| `redis_max_connections` | 50 | **50** | Sufficient for single-instance. Redis operations are sub-millisecond; connection reuse is high. Increase to 100 only if stress scenario shows `ConnectionPool` exhaustion. |

---

## Section 3: Query Profiling Coverage

### What P1.4 Added

| Component | File | Purpose |
| --- | --- | --- |
| `track_query` | `observability/query_profiling.py` | Async context manager measuring wall-clock duration of data-access operations |
| `configure_query_profiling` | `observability/query_profiling.py` | Module-level wiring to connect `MetricsCollector` at startup |
| `db_query_duration_seconds` | `observability/metrics.py` (allowlist) | Prometheus histogram for query durations, with `operation` and `table` labels |
| `slow_query_threshold_ms` | `config.py` | Config field (default: 100ms) controlling the WARNING log threshold |

### Currently Instrumented Operations

| Operation Label | Table Label | File | Call Site |
| --- | --- | --- | --- |
| `memory_store` | `memory_records` | `memory/long_term.py:94` | `LongTermMemory.store()` |
| `memory_search` | `memory_records` | `memory/long_term.py:118` | `LongTermMemory.search()` |
| `memory_scan` | `memory_records` | `memory/long_term.py:140` | `LongTermMemory.scan()` |
| `hybrid_search` | `memory_records` | `memory/hybrid.py:96` | `HybridSearcher.search()` |
| `progressive_recall_search` | `memory_records` | `memory/progressive_recall.py:62` | `ProgressiveRecall.search()` |

**Total instrumented operations: 5** -- all in the memory subsystem.

### Un-instrumented Hot Paths

The following subsystems perform data-access operations but have **zero**
`track_query` instrumentation:

| Subsystem | Key Operations | Risk |
| --- | --- | --- |
| **`sessions/service.py`** | Session create, get, list, end (file-backed I/O) | **High.** Session lifecycle is a load-test scenario; no visibility into per-operation latency. |
| **`agents/runtime.py`** | `invoke()`, `invoke_iterative()`, `invoke_iterative_stream()` -- includes LLM round-trips and tool execution | **High.** Agent invocation is the primary API workload. While LLM latency dominates, there is no profiling of the pre/post-processing overhead. |
| **`operator/service.py`** | `get_sessions()`, session checkpoint I/O | **Medium.** Operator session management is file-backed; I/O latency varies by platform. |
| **`workflows/checkpoint.py`** | `create_async_engine()` with no pool tuning, checkpoint save/load | **Medium.** Workflow checkpointing hits PostgreSQL but has no pool config and no profiling. Uses default SQLAlchemy pool settings, not the P1.3 tuned parameters. |
| **`training/store.py`** | Rollout storage/retrieval via PostgreSQL | **Medium.** Training store hits PG but has no pool tuning and no `track_query`. Uses default pool settings. |
| **`evaluation/service.py`** | Evaluation result storage/retrieval | **Low.** Evaluation runs are batch operations, not on the hot request path. |
| **`improvement/persistence.py`** | Learning signal persistence (file, SQLite, or DB backends) | **Low.** Improvement signals are background operations. |

---

## Section 4: Identified Bottlenecks

### Bottleneck 1: LLM Inference Queue Saturation

**What:** Agent invocation (`POST /v1/agents/{name}/invoke`) is the primary
API workload. Ollama processes requests sequentially per model; under
concurrent load, requests queue behind in-flight inference.

**Why it is a bottleneck risk:** Under the stress scenario (200 users, ~29%
agent invoke traffic), ~58 concurrent users will queue agent invoke requests.
With Ollama inference taking 1-10s per request, queue depth grows linearly.
The AGENT-33 API holds an open connection for each queued request, consuming
event loop resources.

**Mitigation:**
1. Implement request-level timeout on LLM calls (currently unbounded).
2. Add a concurrency semaphore in `AgentRuntime` to limit simultaneous LLM
   calls (e.g., 10 concurrent) and return 503 with retry-after header for
   overflow.
3. Instrument `agents/runtime.py` with `track_query("llm_inference", table="ollama")`
   to measure actual LLM round-trip vs. queue wait time.

### Bottleneck 2: File-Backed Session Storage Contention

**What:** The operator session service (`operator/service.py`,
`sessions/service.py`) uses file-system I/O for session state. Under
concurrent session create/query/end cycles, file operations serialize on
the OS-level file lock.

**Why it is a bottleneck risk:** The `SessionLifecycleUser` scenario creates
and ends sessions at 2-5s intervals per user. Under stress (200 users, ~14%
session traffic), ~28 users concurrently create/read/write session files. On
Windows, file I/O contention is especially pronounced due to mandatory file
locking. This is the "file-backed state contention" limitation already
documented in the horizontal-scaling architecture.

**Mitigation:**
1. Instrument session operations with `track_query("session_create", table="sessions")`
   etc. to measure actual file I/O latency.
2. Move session state to Redis or PostgreSQL for concurrent-safe access.
3. Short-term: add an asyncio lock around session file writes to prevent
   partial writes under concurrent access.

### Bottleneck 3: Workflow Checkpoint Store Untuned Pool

**What:** `workflows/checkpoint.py` creates its own `create_async_engine()`
with **no pool parameters** -- it uses SQLAlchemy defaults (pool_size=5,
max_overflow=10, no pre_ping, no recycle).

**Why it is a bottleneck risk:** The workflow checkpoint store operates on a
separate SQLAlchemy engine from `LongTermMemory`. Under sustained workflow
execution, checkpoint saves can exhaust the untuned pool's 5-connection
limit, causing checkpoint saves to block. Additionally, without
`pool_pre_ping=True`, idle connections can silently become stale after
PostgreSQL restarts or proxy timeouts.

**Mitigation:**
1. Pass the P1.3 pool parameters (`db_pool_size`, `db_max_overflow`,
   `db_pool_pre_ping`, `db_pool_recycle`) to the checkpoint engine.
2. Or: share the `LongTermMemory` engine instance with the checkpoint store
   rather than creating a second connection pool.
3. Add `track_query("checkpoint_save"/"checkpoint_load", table="workflow_checkpoints")`
   instrumentation.

### Bottleneck 4: Health Probe Dependency Cascade

**What:** `GET /readyz` and `GET /health` synchronously probe all backing
services (PostgreSQL, Redis, NATS, Ollama). Each probe runs sequentially
within the request handler.

**Why it is a bottleneck risk:** Under stress, the backing services themselves
may be slow to respond. Health probes that take >200ms will cause Kubernetes
to consider the pod unhealthy, triggering restarts under load -- exactly when
the pod should be absorbing traffic. The P1.5 stress scenario documents that
`/health p95 may exceed 100ms` under load.

**Mitigation:**
1. Run dependency probes concurrently (`asyncio.gather`) rather than
   sequentially.
2. Cache probe results with a short TTL (e.g., 5s) to avoid re-probing on
   every request.
3. Separate liveness (`/healthz` -- always fast, checks process is alive) from
   readiness (`/readyz` -- checks dependencies). This separation already
   exists; ensure Kubernetes uses `/healthz` for liveness and `/readyz` for
   readiness with appropriate timeout configuration.

### Bottleneck 5: Training Store Untuned Pool

**What:** `training/store.py` creates its own `create_async_engine()` with
no pool parameters, identical to the checkpoint store issue.

**Why it is a bottleneck risk:** If training is enabled
(`training_enabled=True`), rollout storage operations share the default
pool (5 connections). During intensive training loops
(`training_optimize_interval=100`), multiple concurrent rollout stores can
exhaust the pool.

**Mitigation:**
1. Same as Bottleneck 3: pass P1.3 pool parameters or share the engine.
2. Add `track_query("rollout_store"/"rollout_fetch", table="rollout_records")`
   instrumentation.

---

## Section 5: Recommended Next Steps (P1.7 Inputs)

### Concrete Thresholds for P1.7 Performance Regression Guardrails

These thresholds are derived from the P1.5 acceptance criteria and should be
enforced as CI gates in P1.7:

| Metric | Threshold | Source | Gate Type |
| --- | --- | --- | --- |
| `GET /healthz` p95 | < 50ms | Light scenario acceptance criteria | Hard fail |
| `GET /health` p95 | < 200ms | Standard scenario (relaxed from 100ms for CI environments) | Hard fail |
| `GET /readyz` p95 | < 300ms | Standard scenario (relaxed for dependency probe variance) | Soft warning |
| `GET /metrics` p95 | < 200ms | Standard scenario | Hard fail |
| `POST /v1/agents/{name}/invoke` p95 | < 10s | Stress scenario (LLM-dependent, doubled for CI) | Soft warning |
| Session lifecycle p95 | < 3s | Standard scenario (relaxed for file I/O variance) | Hard fail |
| Overall failure rate (light) | 0% | Light scenario acceptance | Hard fail |
| Overall failure rate (standard) | < 1% | Standard scenario acceptance | Hard fail |
| Overall failure rate (stress) | < 5% | Stress scenario acceptance | Soft warning |

### Slow-Query Budgets Per Operation Type

These budgets define the `threshold_ms` values to enforce via
`track_query` instrumentation. Operations exceeding their budget will
emit WARNING logs and can be surfaced in Grafana dashboards:

| Operation | Budget (ms) | Rationale |
| --- | --- | --- |
| `memory_store` | 50 | Single INSERT + flush. Should be well under 50ms with connection pool pre-allocated. |
| `memory_search` | 100 | pgvector cosine distance query with ORDER BY. Index-backed, but vector operations are CPU-bound. Current default threshold. |
| `memory_scan` | 200 | Paginated sequential scan (up to 200 rows per page for BM25 warm-up). Larger result sets take longer. |
| `hybrid_search` | 150 | Wraps `memory_search` + BM25 in-memory search + RRF fusion. BM25 is in-memory; the vector search is the bottleneck. |
| `progressive_recall_search` | 150 | Wraps `memory_search` + post-processing per detail level. Similar budget to hybrid_search. |
| `session_create` (proposed) | 50 | File-system write for session creation. Should be fast on SSD. |
| `session_get` (proposed) | 20 | File-system read for session lookup. |
| `checkpoint_save` (proposed) | 100 | PostgreSQL INSERT/UPDATE for workflow state. |
| `checkpoint_load` (proposed) | 50 | PostgreSQL SELECT by ID for workflow state. |
| `llm_inference` (proposed) | 10000 | LLM round-trip. 10s budget is generous; the real enforcement should be a hard timeout, not a warning. |

### Instrumentation Gaps to Close Before P1.7

These are the highest-priority instrumentation additions needed to make
the P1.7 regression guardrails meaningful:

1. **Session service** (`sessions/service.py`, `operator/service.py`):
   Add `track_query` around all file I/O operations. Without this, the
   session lifecycle load-test scenario produces no profiling data.

2. **Agent runtime** (`agents/runtime.py`): Add `track_query` around the
   LLM call in `invoke()` and `invoke_iterative()`. This separates API-layer
   overhead from LLM inference latency.

3. **Workflow checkpoint** (`workflows/checkpoint.py`): Add `track_query`
   and pass P1.3 pool parameters to `create_async_engine()`.

4. **Training store** (`training/store.py`): Add `track_query` and pass
   P1.3 pool parameters.

### Summary

The P1.3/P1.4/P1.5 infrastructure provides a solid foundation for performance
observability. The primary gaps are:

- **Coverage**: Only 5 operations in the memory subsystem are instrumented.
  The session, agent runtime, workflow checkpoint, and training subsystems
  have zero `track_query` coverage.
- **Pool consistency**: Two subsystems (workflow checkpoint, training store)
  create their own SQLAlchemy engines with default pool settings, bypassing
  the P1.3 tuned parameters.
- **Health probe performance**: Sequential dependency probes create a latency
  floor that scales with backing service count.

Closing these gaps before P1.7 will make the regression guardrails actionable
rather than aspirational.
