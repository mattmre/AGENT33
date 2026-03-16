# S45: Scheduled Evaluation Gates -- Scope & Architecture

**Session**: 91
**Slice**: S45
**Status**: Implementation
**Date**: 2026-03-15

## Objective

Add cron-driven regression gate enforcement. The system can schedule periodic
evaluation runs that check gate thresholds and detect regressions automatically,
serving as an early-warning monitoring layer.

## Architecture Decisions

### Own APScheduler Instance

The `ScheduledGateService` creates its own `AsyncIOScheduler` rather than
sharing with `WorkflowScheduler`. This avoids coupling the evaluation schedule
lifecycle to workflow scheduling and prevents a crashed gate execution from
affecting workflow triggers.

### G-MON Gate Thresholds

The G-MON gate type was defined but had zero thresholds, making it a no-op.
S45 adds relaxed monitoring thresholds (M-01 >= 85%, M-03 <= 25%) with WARN
action, since scheduled gates serve as early warnings rather than hard blocks.

### In-Memory State

Schedule configs and history are stored in memory with bounded retention
(configurable via `scheduled_gates_history_retention`). This matches the
existing `EvaluationService` pattern and keeps the feature self-contained.

### Opt-In Activation

The feature is gated behind `scheduled_gates_enabled = False` (default off).
When disabled, the API routes return 503 and no scheduler is started.

## Deliverables

| File | Purpose |
|------|---------|
| `engine/src/agent33/evaluation/scheduled_gates.py` | Models + ScheduledGateService |
| `engine/src/agent33/api/routes/scheduled_gates.py` | REST API (6 endpoints) |
| `engine/src/agent33/config.py` | 3 new settings |
| `engine/src/agent33/main.py` | Lifespan wiring |
| `engine/tests/test_scheduled_gates.py` | Comprehensive test suite |

## API Surface

```
POST   /v1/evaluations/schedules              -- create schedule
GET    /v1/evaluations/schedules              -- list schedules
GET    /v1/evaluations/schedules/{id}         -- get schedule detail
DELETE /v1/evaluations/schedules/{id}         -- remove schedule
POST   /v1/evaluations/schedules/{id}/trigger -- manual trigger
GET    /v1/evaluations/schedules/{id}/history -- get execution history
```
