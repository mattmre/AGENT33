# S26: SkillsBench 86-Task Benchmark Harness -- Scope Document

**Session**: 89
**Slice**: S26
**Date**: 2026-03-15
**Status**: Implementation complete

## Overview

Implements a benchmark harness modeled after the SkillsBench evaluation
framework.  The harness supports 86-task style benchmark evaluations with
binary reward (all-or-nothing) scoring, multi-trial execution (default 5
trials per task), and skills impact measurement.

## Deliverables

### New Files

1. **`engine/src/agent33/evaluation/benchmark.py`** -- Core harness
   - `BenchmarkTaskCategory` (StrEnum): 10 category values
   - `BenchmarkTask` model: task definition with verification config
   - `TrialResult` model: single trial outcome
   - `TaskBenchmarkResult` model: aggregated task results
   - `BenchmarkRun` model: full run with summary metrics
   - `BenchmarkConfig` model: run configuration with filters
   - `BenchmarkHarness` class: orchestrates execution, comparison, CTRF export

2. **`engine/src/agent33/evaluation/benchmark_catalog.py`** -- Default catalog
   - 20 representative tasks across 10 categories
   - `DEFAULT_BENCHMARK_CATALOG` constant

3. **`engine/tests/test_benchmark_harness.py`** -- Comprehensive tests
   - Model validation, filtering, trial execution, run management
   - Catalog loading from file, comparison, CTRF conversion
   - API route tests via TestClient

4. **`docs/research/session89-s26-skillsbench-scope.md`** -- This document

### Modified Files

5. **`engine/src/agent33/config.py`** -- Two new settings:
   - `evaluation_benchmark_catalog_path: str = ""`
   - `evaluation_benchmark_default_trials: int = 5`

6. **`engine/src/agent33/api/routes/evaluations.py`** -- Six new endpoints:
   - `GET /v1/evaluations/benchmark/catalog` (agents:read)
   - `POST /v1/evaluations/benchmark/run` (admin)
   - `GET /v1/evaluations/benchmark/runs` (agents:read)
   - `GET /v1/evaluations/benchmark/runs/{run_id}` (agents:read)
   - `GET /v1/evaluations/benchmark/runs/{run_id}/ctrf` (agents:read)
   - `POST /v1/evaluations/benchmark/compare` (agents:read)

7. **`engine/src/agent33/main.py`** -- Lifespan wiring:
   - Creates `BenchmarkHarness` with default or custom catalog
   - Stores on `app.state.benchmark_harness`
   - Sets harness on evaluations router

## Architecture Decisions

### Simulated Trial Execution

Trial execution uses deterministic hash-based simulation by default.
This is intentional: real agent invocation requires runtime context
(model router, agent runtime, tool registry) that varies by deployment.
The harness is designed to accept a pluggable trial executor for
production use.

### Integration with Existing Evaluation System

The benchmark harness is independent from but complementary to the
existing evaluation subsystem (golden tasks, metrics, gates, regression
detection).  It shares CTRF reporting via `CTRFReportGenerator` and
lives in the same `evaluation/` package.

### Category Subset

The 10 categories are a representative subset of SkillsBench's 62+
categories, chosen to cover the breadth of typical agent tasks without
requiring full SkillsBench infrastructure.

## Dependencies

- `agent33.evaluation.ctrf` (CTRF report generation)
- No new external dependencies
