# S28: Iterative Tool-Use Loop Scoring

**Session**: 89
**Slice**: S28
**Status**: Implementation

## Objective

Add scoring and retry infrastructure for iterative tool-use loops.  This
enables the system to track per-tool effectiveness (success rate, latency,
retry frequency), detect convergence across iterations, and make
policy-driven retry decisions with exponential backoff.

## Scope

### New module: `engine/src/agent33/tools/loop_scoring.py`

Core data models:

| Model | Purpose |
|-------|---------|
| `ToolCallRecord` | Single tool call with outcome, timing, and dedup hash |
| `ToolEffectivenessScore` | Composite score for one tool (0-1) |
| `LoopIteration` | Per-iteration snapshot with convergence flag |
| `ToolLoopSummary` | Full loop analytics |
| `RetryPolicy` | Configurable retry limits and backoff parameters |

Scorer class (`ToolLoopScorer`):

- `record_call()` -- record individual tool call outcomes
- `get_tool_score(tool_name)` -- single-tool effectiveness
- `get_all_scores()` -- all tools
- `get_loop_summary()` -- full analytics
- `should_retry(tool_name, attempt, error)` -- policy-driven retry decision
- `start_iteration()` / `detect_convergence()` -- iteration tracking
- `reset()` -- clear state

### Score formula

```
score = success_rate * 0.4 + (1 - retry_rate) * 0.3 + speed_score * 0.3
```

where `speed_score = max(0, 1 - avg_duration_ms / 10000)`.

### API endpoint

`GET /v1/agents/tool-loop/scores` (scope: `agents:read`) -- returns the
current `ToolLoopSummary` from `app.state.tool_loop_scorer`, or an empty
response if no scorer is installed.

### Config additions

| Key | Default | Purpose |
|-----|---------|---------|
| `agent_tool_loop_max_retries` | 3 | Max retry attempts |
| `agent_tool_loop_backoff_base_ms` | 100 | Base backoff delay |

## Out of scope

- Integrating the scorer into `ToolLoop.run()` (future follow-up)
- Persisting scoring data across restarts
- UI for score visualisation

## Test coverage

- Model construction and defaults
- Single and multi-tool scoring
- Retry policy: within limits, exceeded, error filtering
- Exponential backoff calculation with cap
- Iteration tracking and convergence detection
- Loop summary assembly
- Input dedup hash detection
- Reset behaviour
- API route (empty state and populated state)
