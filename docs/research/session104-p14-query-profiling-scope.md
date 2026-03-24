# P1.4: Query Profiling and Hot-Path Optimization -- Scope Memo

**Date:** 2026-03-24
**Session:** 104
**Slice:** P1.4
**Branch:** `feat/session104-p14-query-profiling`

## Objective

Add lightweight query profiling instrumentation and slow-path detection to the
AGENT-33 engine. This provides the observability foundation needed to identify
database and data-access bottlenecks before optimizing them in P1.6.

## Hot Paths Identified

After analyzing the engine source, these are the highest-frequency/latency-risk
data operations:

| # | Operation | Module | Why it matters |
|---|-----------|--------|----------------|
| 1 | `LongTermMemory.search()` | `memory/long_term.py` | pgvector cosine-distance query on every RAG retrieval and progressive-recall search. Called on every agent invocation with memory enabled. |
| 2 | `LongTermMemory.store()` | `memory/long_term.py` | INSERT with embedding vector on every memory ingestion. High-write path during active sessions. |
| 3 | `LongTermMemory.scan()` | `memory/long_term.py` | Paginated full-table scan used for BM25 warm-up at startup. Can be slow on large memory stores. |
| 4 | `HybridSearcher.search()` | `memory/hybrid.py` | Orchestrates both vector search and BM25 search, then fuses results. Compounds latency from path #1. |
| 5 | `ProgressiveRecall.search()` | `memory/progressive_recall.py` | Chains embedding + vector search for 3-layer recall. Called on agent invocations with progressive recall enabled. |

**Non-DB hot paths noted but not instrumented in this slice:**
- `AgentRegistry.get()` / `AgentRegistry.search()` -- in-memory dict lookups, sub-microsecond. Not worth instrumenting.
- `OperatorSessionService.get_session()` -- in-memory cache with filesystem fallback. Latency is dominated by filesystem I/O, not DB queries. Could be instrumented in a future slice.

## What Was Instrumented

1. **`track_query` async context manager** in `observability/query_profiling.py`:
   - Measures wall-clock time of any async DB/data operation
   - Logs a `WARNING` when duration exceeds `slow_query_threshold_ms` (configurable)
   - Records duration to the `db_query_duration_seconds` Prometheus histogram
   - Labels: `operation` (e.g. `memory_search`, `memory_store`) and `table` (e.g. `memory_records`)

2. **`db_query_duration_seconds` histogram** added to the Prometheus observation allowlist in `observability/metrics.py`:
   - Exposed via `GET /metrics` with labels `operation` and `table`
   - Buckets implicit (the existing MetricsCollector uses observation-based aggregation, not histogram buckets; P1.6 can introduce a dedicated Prometheus client with explicit bucket boundaries if needed)

3. **`slow_query_threshold_ms` config field** added to `config.py` with default `100`.

4. **Wiring** into the 5 identified hot paths:
   - `LongTermMemory.search()`, `.store()`, `.scan()` -- wrapped with `track_query`
   - `HybridSearcher.search()` -- wrapped with `track_query`
   - `ProgressiveRecall.search()` -- wrapped with `track_query`

## Explicit Non-Goals

- **No schema changes.** No new indexes, no column additions, no migrations.
- **No query rewrites.** The actual SQL in `long_term.py` is not modified.
- **No connection pooling changes.** That is P1.3 scope.
- **No Prometheus client library introduction.** The existing `MetricsCollector` observation-based system is used. A real `prometheus_client` Histogram with explicit buckets is deferred to P1.6.
- **No load testing.** P1.5 already provides the load-test harness; this slice provides the metrics it will measure against.

## Validation Plan

1. Unit tests in `tests/test_query_profiling.py`:
   - Verify `track_query` context manager fires WARNING logs when threshold exceeded
   - Verify `track_query` does NOT fire WARNING when under threshold
   - Verify Prometheus histogram observation is recorded with correct labels
   - Verify `slow_query_threshold_ms` config field exists with correct default
2. Lint: `ruff check` + `ruff format --check` clean
3. Type check: `mypy` strict clean
