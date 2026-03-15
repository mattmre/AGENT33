# S18: Phase 31 Analytics Dashboards — Scope Memo

**Session**: 89
**Date**: 2026-03-14
**Baseline**: `origin/main` at `d7106f2`

## Summary

Adds cross-domain analytics aggregation endpoints to the improvement subsystem. Backend-first: 8 new GET endpoints under `/v1/improvements/analytics/`, plus metrics snapshot persistence.

## Included Work

1. **AnalyticsService** (`improvement/analytics.py`) — read-only aggregation over ImprovementService data
2. **12 response models** — chart-ready data structures (funnels, histograms, time-series, etc.)
3. **8 API endpoints** — dashboard summary, intake funnel, lesson actions, checklist completion, signal-to-intake conversion, quality distribution, metrics timeseries, refresh cadence
4. **Metrics snapshot persistence** — `metrics_snapshots` added to `LearningPersistenceState`
5. **5 accessor methods** on ImprovementService — `all_intakes`, `all_lessons`, `all_signals`, `all_refreshes`, `all_metrics_snapshots`
6. **Module-level `percentile()`** extracted from private method for reuse
7. **Config**: `improvement_learning_max_metrics_snapshots` (default 100)
8. **41 tests** covering all analytics methods, persistence, and API routes

## Non-Goals

- Cross-subsystem correlation (traces ↔ signals) — belongs to operations-hub analytics
- Tuning loop automation (S19)
- Frontend visualization components
- Real-time streaming analytics
- Caching layer

## Gaps Addressed

| Gap | Status |
|-----|--------|
| No cross-domain analytics endpoint | Resolved: DashboardSummary |
| No time-series export for metrics | Resolved: MetricsTimeSeries |
| No intake funnel analytics | Resolved: IntakeFunnelReport |
| No lesson action completion rates | Resolved: LessonActionCompletionReport |
| No checklist completion rates | Resolved: ChecklistCompletionReport |
| No signal-to-intake conversion | Resolved: SignalToIntakeReport |
| No quality distribution histogram | Resolved: QualityDistribution |
| No refresh cadence reporting | Resolved: RefreshCadenceReport |
| Metrics snapshots in-memory only | Resolved: persisted via LearningPersistenceState |
| Cross-subsystem correlation | Deferred (operations-hub scope) |
