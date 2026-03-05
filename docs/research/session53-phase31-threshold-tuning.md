# Session 53: Phase 31 Threshold Calibration for Retention and Auto-Intake

Date: 2026-03-04
Scope: Priority 5 from `docs/next-session.md`

## Problem

Phase 31 now supports dedupe, retention, and quality gates, but threshold tuning is manual. We need an evidence-backed calibration helper to tune:

- retention horizon (`retention_days`)
- auto-intake quality threshold
- auto-intake severity floor
- auto-intake max items per cycle

based on production-like signal distributions.

## Baseline reviewed

- `engine/src/agent33/improvement/service.py`
- `engine/src/agent33/improvement/quality.py`
- `engine/src/agent33/api/routes/improvements.py`
- `engine/tests/test_phase31_learning_signals.py`

## Design

Add a deterministic calibration report method and endpoint:

- Service: `calibrate_learning_thresholds(window_days, target_auto_intakes_per_window, tenant_id)`
- Route: `GET /v1/improvements/learning/calibration`

The report computes:

1. Sample stats over the requested window:
   - signal count
   - dedupe-aware occurrence count
   - daily occurrence rate
   - average quality score
   - quality percentiles (p75, p90)
   - high/critical severity ratio
2. Suggested policy values:
   - `recommended_auto_intake_min_quality`
   - `recommended_auto_intake_min_severity`
   - `recommended_auto_intake_max_items`
   - `recommended_retention_days`
3. Current policy snapshot for comparison.

## Algorithm notes

- Quality threshold recommendation is driven by top-N quality scores where `N = target_auto_intakes_per_window`.
- Severity recommendation is conservative (`high` when high/critical ratio is elevated; otherwise `medium`).
- Retention recommendation is capacity-aware and bounded, derived from current max signal capacity and observed daily occurrence rate.

## Non-goals

- No automatic config mutation.
- No scheduler/job integration.
- No frontend dashboard changes in this slice.
