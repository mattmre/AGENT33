# S40: Agent Performance Profiling -- Scope Document

**Session**: 89
**Date**: 2026-03-15
**Status**: In Progress

## Objective

Add per-agent invocation profiling with phase-level timing breakdown, summary
statistics, bottleneck detection, and hot-path identification. This enables
operators to identify performance regressions and optimization opportunities
across the agent fleet.

## Deliverables

### 1. `engine/src/agent33/agents/profiling.py`

Core profiling module with:

- **AgentInvocationProfile** -- Pydantic model capturing per-invocation timing
  (prompt construction, LLM call, tool execution, post-processing), token
  counts, model ID, and success status.

- **AgentPerformanceSummary** -- Aggregated statistics per agent: average and
  p95 duration, per-phase averages, success rate, token averages, and
  dominant bottleneck phase.

- **AgentProfiler** -- Thread-safe profiler using a bounded ring buffer
  (configurable via `AGENT_PROFILER_MAX_PROFILES`, default 1000). Methods:
  - `record_profile()` -- store with FIFO eviction
  - `get_agent_summary()` / `get_all_summaries()` -- compute stats
  - `get_profiles()` -- retrieve raw profiles (filtered, paginated)
  - `detect_bottlenecks()` -- flag agents where one phase > 60% of duration
  - `get_hot_paths()` -- rank slowest agent/model combinations

### 2. API Endpoints (on `/v1/agents/profiling/`)

| Route | Method | Scope | Description |
|-------|--------|-------|-------------|
| `/profiling/summaries` | GET | agents:read | All agent summaries |
| `/profiling/{agent_name}` | GET | agents:read | Single agent summary |
| `/profiling/bottlenecks` | GET | agents:read | Detected bottlenecks |
| `/profiling/profiles` | GET | agents:read | Raw profiles (filterable) |
| `/profiling/hot-paths` | GET | agents:read | Slowest agent/model combos |

### 3. Lifespan Wiring (`main.py`)

`AgentProfiler` instantiated during startup and stored on `app.state.agent_profiler`.

### 4. Configuration (`config.py`)

- `AGENT_PROFILER_MAX_PROFILES` (int, default 1000) -- ring buffer capacity.

### 5. Tests (`engine/tests/test_agent_profiling.py`)

- Profile recording and retrieval
- Summary computation (averages, p95, success rate, bottleneck detection)
- Ring buffer eviction semantics
- Multiple agent summaries
- Bottleneck detection (LLM-bound, tool-bound scenarios)
- Hot path identification
- Empty profiler edge case
- API route tests with mocked profiler on app.state

## Design Decisions

1. **Ring buffer over database**: Profiles are ephemeral diagnostic data, not
   audit records. In-memory storage avoids DB overhead and matches the existing
   MetricsCollector pattern.

2. **Thread-safe via threading.Lock**: The profiler may be written from async
   handlers running on different threads. A simple lock is sufficient given the
   low-contention write pattern.

3. **Percentile via linear interpolation**: The p95 calculation uses the
   standard linear interpolation method, consistent with numpy's default.

4. **Bottleneck threshold at 60%**: A phase is flagged as a bottleneck when it
   dominates more than 60% of average total duration. This threshold balances
   sensitivity with noise.

## Non-Goals (This Slice)

- Instrumenting AgentRuntime.invoke() / invoke_iterative() with actual timing
  calls (requires coordinating with runtime changes -- future slice).
- Persistent profile storage (DB-backed).
- Real-time alerting on performance degradation.
- Profile sampling / probabilistic recording.
