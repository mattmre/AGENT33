# P1.4: Bottleneck Report -- Query Profiling Results

**Date:** 2026-03-24
**Session:** 104
**Slice:** P1.4

## Instrumented Operations

| Operation | Module | Prometheus Label | Expected Baseline Latency |
|-----------|--------|-----------------|--------------------------|
| `LongTermMemory.search()` | `memory/long_term.py` | `operation=memory_search, table=memory_records` | 5-50ms (pgvector cosine distance, depends on table size and index state) |
| `LongTermMemory.store()` | `memory/long_term.py` | `operation=memory_store, table=memory_records` | 2-20ms (single INSERT with vector column) |
| `LongTermMemory.scan()` | `memory/long_term.py` | `operation=memory_scan, table=memory_records` | 10-200ms per page (sequential scan, 100-200 rows per page) |
| `HybridSearcher.search()` | `memory/hybrid.py` | `operation=hybrid_search, table=memory_records` | 20-150ms (compounds vector search + BM25 + RRF fusion) |
| `ProgressiveRecall.search()` | `memory/progressive_recall.py` | `operation=progressive_recall_search, table=memory_records` | 10-80ms (embedding + vector search, similar to LTM search) |

## Expected Baseline Latency Ranges

These ranges are estimates based on:
- Typical pgvector cosine-distance query performance on tables with 1K-100K rows
- Single-node PostgreSQL without dedicated HNSW/IVFFlat index tuning
- Default connection pool settings (P1.3 scope)

**Under 10K records:** All operations expected under 50ms.
**10K-100K records:** `memory_search` and `hybrid_search` may approach 100-200ms without HNSW index.
**100K+ records:** `memory_scan` pages will stay constant (sequential scan with LIMIT/OFFSET), but `memory_search` can exceed 500ms without index optimization.

## Prometheus Metric Details

**Metric name:** `db_query_duration_seconds`
**Type:** Observation (rendered as count/sum/avg/min/max in current MetricsCollector)
**Labels:**
- `operation`: Identifies the specific data-access operation
- `table`: The logical table/store being accessed

**Scrape endpoint:** `GET /metrics` (existing Prometheus endpoint)

## What P1.5 (Load-Test Harness) Should Measure

The load-test harness should:
1. Run concurrent agent invocations that exercise the RAG pipeline (hybrid search path)
2. Monitor `db_query_duration_seconds` P50/P95/P99 under load
3. Watch for slow-query WARNING log frequency increasing with concurrency
4. Track `memory_search` vs `hybrid_search` latency divergence (hybrid should be ~2x vector-only)
5. Measure `memory_store` throughput under write-heavy ingestion scenarios

## Optimizations Deferred to P1.6

| Optimization | Why Deferred | Expected Impact |
|-------------|-------------|-----------------|
| HNSW index on embedding column | Schema change, requires migration | 10-50x speedup on `memory_search` for >10K rows |
| Connection pool tuning | P1.3 scope (already in progress) | Reduced connection acquisition latency |
| Prepared statements for hot queries | Query rewrite, needs careful testing | 10-30% reduction in parse/plan overhead |
| Batch embedding inserts | Changes `store()` API contract | 3-5x throughput improvement for bulk ingestion |
| BM25 index pre-warming parallelization | Changes startup sequence | Faster cold-start for large memory stores |
| Explicit Prometheus client histograms with bucket boundaries | Requires `prometheus_client` dependency | Proper percentile computation (P50/P95/P99) |
