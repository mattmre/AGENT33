# Session 53: Phase 31 Dedup-Aware Trend Analytics and Reporting

Date: 2026-03-04
Scope: Priority 4 from `docs/next-session.md`

## Problem

Phase 31 currently summarizes recent learning signals, but reporting is still coarse:

- no dedicated trend report contract by signal dimension
- no explicit current-window vs previous-window comparison by type/severity
- no dedupe-aware occurrence weighting in trend reporting

This limits operational tuning and makes it hard to distinguish rising unique incidents from repeated occurrences of the same deduped incident.

## Existing baseline reviewed

- `engine/src/agent33/improvement/models.py`
- `engine/src/agent33/improvement/service.py`
- `engine/src/agent33/api/routes/improvements.py`
- `engine/tests/test_phase31_learning_signals.py`

## Design

Add a dedicated trend-report contract and endpoint:

- Service method: `trend_learning_signals(window_days, dimension, tenant_id)`
- Dimensions:
  - `signal_type`
  - `severity`
- Report compares:
  - current window (`now - window_days` to `now`)
  - previous equal-sized window
- For each dimension key, emit:
  - signal counts
  - dedupe-aware occurrence counts (`occurrence_count`)
  - deltas
  - direction (`up|down|stable`)

Endpoint:

- `GET /v1/improvements/learning/trends`
  - query: `window_days`, `dimension`, optional `tenant_id`
  - feature-gated behind `improvement_learning_enabled`

## Why this shape

- Keeps existing summary endpoint stable.
- Adds explicit analytics contract for downstream dashboards and operations workflows.
- Makes deduped signal dynamics visible without changing persistence semantics.

## Non-goals

- No persistence schema change.
- No automatic threshold mutation in this PR.
- No frontend work in this PR.
