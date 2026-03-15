# S19: Phase 31 Tuning Loop Automation -- Scope Memo

**Session:** 89
**Slice:** S19
**Date:** 2026-03-14
**Status:** In Progress

## Objective

Automate the calibration of Phase 31 learning thresholds (quality floor,
retention window, intake limits, severity floor) via a periodic tuning loop
with safety clamping and optional approval gates.

## Scope

### In Scope

- `TuningLoopService`: Periodic calibration cycle orchestrator
  - Calls `ImprovementService.calibrate_learning_thresholds()` for recommendations
  - Applies safety-clamped deltas to live `LearningPersistencePolicy`
  - Supports dry-run, require-approval, and auto-apply modes
  - Stores bounded in-memory history of cycle records

- `TuningLoopScheduler`: asyncio background task (follows `TrainingScheduler` pattern)
  - Configurable interval (default 24h)
  - Graceful start/stop lifecycle

- Safety constraints:
  - `auto_intake_min_quality`: max delta +/- 0.15
  - `retention_days`: max delta +/- 30 days
  - `auto_intake_max_items`: max delta +/- 2
  - `auto_intake_min_severity`: never relax below "medium"
  - Skip cycle when sample_size < 10

- Config settings (6 new fields on `Settings`)
- API endpoints (4 routes under `/v1/improvements/tuning/`)
- `ImprovementService.update_policy()` for live policy swaps

### Out of Scope

- Persistent storage of tuning cycle history (in-memory only for now)
- Multi-tenant tuning isolation (single global loop)
- ML-based threshold optimization
- UI for tuning loop management

## Architecture Decisions

1. **In-memory history** -- Bounded to 100 records. Adequate for operational
   monitoring; persistent audit trail can be added later via the existing
   learning signal persistence infrastructure.

2. **ConfigApplyService protocol** -- Optional dependency for pushing tuning
   changes to external config stores. Default is no-op; the primary mutation
   path is `ImprovementService.update_policy()`.

3. **Safety clamping over optimization** -- Deliberately conservative: small
   max deltas, minimum sample size, approval gate by default. The goal is
   preventing config drift, not maximizing throughput.

## Files

| File | Action |
|------|--------|
| `engine/src/agent33/improvement/tuning.py` | New |
| `engine/src/agent33/improvement/service.py` | Modified (add `update_policy`) |
| `engine/src/agent33/config.py` | Modified (6 new settings) |
| `engine/src/agent33/api/routes/improvements.py` | Modified (4 new endpoints) |
| `engine/src/agent33/main.py` | Modified (scheduler wiring) |
| `engine/tests/test_improvement_tuning.py` | New |
| `docs/research/session89-s19-tuning-loop-scope.md` | New (this file) |
