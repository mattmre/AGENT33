# Session 116 P8: Phase 31 Tuning Coherence Scope

Date: 2026-03-28
Slice: `P8 / A1`
Branch: `codex/session116-p8-a1-phase31`

## Why this slice exists

The remaining Phase 31 work on current `main` is not a missing analytics
dashboard. The analytics service, dashboard routes, and their regression suite
already exist. The residual gap is that the tuning loop does not currently
control the live auto-intake behavior it claims to tune.

## Baseline audited

- `engine/src/agent33/improvement/service.py`
- `engine/src/agent33/improvement/tuning.py`
- `engine/src/agent33/api/routes/improvements.py`
- `engine/src/agent33/config.py`
- `engine/src/agent33/config_apply.py`
- `engine/tests/test_phase31_learning_signals.py`
- `engine/tests/test_improvement_tuning.py`
- `docs/research/session53-phase31-threshold-tuning.md`
- `docs/research/session55-phase31-production-tuning.md`
- `docs/research/session89-s18-analytics-dashboards-scope.md`
- `docs/research/session89-s19-tuning-loop-scope.md`

## Confirmed residuals

1. The tuning loop records and applies `auto_intake_min_severity` and
   `auto_intake_max_items`, but the summary auto-intake route still reads the
   static settings values instead of the live service policy.
2. The tuning loop currently reuses `max_generated_intakes` as if it were the
   per-window auto-intake cap, which conflates retention of generated intakes
   with the threshold used to create them.
3. The tuning loop's optional config-apply integration is wired to the real
   `ConfigApplyService`, but it calls it with the wrong shape and therefore does
   not safely propagate live threshold updates back into runtime settings.
4. Calibration snapshots report the wrong policy field for
   `recommended_auto_intake_max_items`, so operators cannot reliably compare
   recommendations with the active runtime policy.

## Included work

- Extend the live Phase 31 policy contract so it carries:
  - auto-intake severity floor
  - auto-intake max items per generation cycle
- Make `generate_intakes_from_learning_signals()` default to the live policy
  when explicit overrides are not provided.
- Make `/v1/improvements/learning/summary` and related tuning flows consume the
  live policy instead of stale settings values.
- Align tuning-loop config application with the real config-apply service and
  the actual settings field names.
- Add regression tests that prove:
  - a tuning cycle changes live auto-intake behavior
  - config-apply receives the correct settings updates
  - calibration snapshots reflect the active runtime policy

## Explicit non-goals

- No new analytics dashboard endpoints.
- No UI work for tuning visibility.
- No persistence redesign for tuning history.
- No multi-tenant tuning isolation changes.
