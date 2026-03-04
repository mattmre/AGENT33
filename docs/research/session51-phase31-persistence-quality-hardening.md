# Session 51: Phase 31 Persistence + Quality Hardening

Date: 2026-03-04  
Owner: Session 51 implementation workstream (`feat/session51-phase31-persistence-quality-hardening`)

## Why this slice

Phase 31 already had signal capture, persistence backends, and auto-intake generation, but three operational risks remained:

1. Learning state could grow unbounded over long-running sessions.
2. Repeated duplicate incidents inflated signal volume and generated noisy summaries.
3. Auto-intake generation only used severity and did not enforce a minimum signal quality bar.

## Implemented architecture

The hardening keeps the existing model shape and APIs while introducing a policy object in `ImprovementService`:

- `LearningPersistencePolicy`
  - `dedupe_window_minutes`
  - `retention_days`
  - `max_signals`
  - `max_generated_intakes`
  - `auto_intake_min_quality`

### Dedupe behavior

- Fingerprint scope: `tenant_id + signal_type + normalized(summary) + normalized(source)`.
- If a duplicate arrives inside the configured dedupe window:
  - `occurrence_count` increments.
  - `last_seen_at` is updated.
  - Higher severity is retained.
  - Richer details/context are merged.
  - Existing signal is enriched/persisted and returned (no new signal ID created).

### Retention/pruning behavior

Before each persistence save:

- Signals older than `retention_days` are pruned (if enabled).
- Signals are capped by recency via `max_signals`.
- Generated intakes are capped by recency via `max_generated_intakes`.
- Signal-intake links are cleaned so no stale references remain.

### Auto-intake quality gate

- Existing severity gate remains.
- New quality gate: `signal.quality_score >= auto_intake_min_quality`.
- Prevents low-information high-severity signals from auto-opening research intake noise.

## Config additions

Added settings in `engine/src/agent33/config.py`:

- `improvement_learning_dedupe_window_minutes` (default `30`)
- `improvement_learning_retention_days` (default `180`)
- `improvement_learning_max_signals` (default `5000`)
- `improvement_learning_max_generated_intakes` (default `1000`)
- `improvement_learning_auto_intake_min_quality` (default `0.45`)

Validation rules:

- All count/window settings must be non-negative.
- Quality threshold must be in `[0.0, 1.0]`.

## Wiring

`engine/src/agent33/api/routes/improvements.py` now builds `ImprovementService` with a `LearningPersistencePolicy` derived from settings, keeping route behavior configurable without changing endpoint contracts.

## Test coverage added

Extended `engine/tests/test_phase31_learning_signals.py` with:

- quality-threshold config validation
- dedupe window merge behavior
- max-history pruning behavior (signals + generated intakes)
- retention-days pruning behavior
- service-level min-quality intake gating
- route-level quality-threshold gating

## Backward compatibility notes

- Existing endpoints and payloads remain compatible.
- New signal fields are additive (`occurrence_count`, `first_seen_at`, `last_seen_at`).
- Default policy values preserve prior behavior except for route-level dedupe/quality defaults (explicitly test-configurable).
