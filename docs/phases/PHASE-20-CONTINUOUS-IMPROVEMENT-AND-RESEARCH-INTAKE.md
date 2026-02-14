# Phase 20: Continuous Improvement & Research Intake

## Overview
- **Phase**: 20 of 20
- **Category**: Research
- **Status**: Complete
- **Tests**: 72 new tests

## Objectives
- Establish research intake and periodic roadmap refresh.
- Capture lessons learned and update governance artifacts.
- Maintain a continuous improvement cadence.

## Implementation

| # | Component | Module | Description |
|---|-----------|--------|-------------|
| 1 | Data models | `improvement/models.py` | 8 enums (ResearchType, IntakeStatus, LessonEventType, LessonActionStatus, MetricTrend, ChecklistPeriod, RefreshScope, ResearchUrgency), 12+ Pydantic models |
| 2 | Checklists | `improvement/checklists.py` | CI-01..CI-15 canonical checks (per-release, monthly, quarterly), ChecklistEvaluator |
| 3 | Metrics tracker | `improvement/metrics.py` | IM-01..IM-05 canonical metrics, trend computation, snapshot storage |
| 4 | Improvement service | `improvement/service.py` | Research intake lifecycle, lessons learned CRUD, checklist management, metrics, roadmap refresh |
| 5 | Improvement API | `api/routes/improvements.py` | 22 REST endpoints under `/v1/improvements` |

### Research Intake Lifecycle State Machine

```
SUBMITTED -> TRIAGED -> ANALYZING -> ACCEPTED -> TRACKED
                                  -> DEFERRED -> TRIAGED (re-triage)
                                  -> REJECTED
```

### Improvement Checklists (CI-01..CI-15)

| Period | Checks | IDs |
|--------|--------|-----|
| Per Release | 5 | CI-01..CI-05 |
| Monthly | 5 | CI-06..CI-10 |
| Quarterly | 5 | CI-11..CI-15 |

### Improvement Metrics (IM-01..IM-05)

| Metric | ID | Target |
|--------|-----|--------|
| Cycle time | IM-01 | Decreasing trend |
| Rework rate | IM-02 | < 15% |
| First-pass success | IM-03 | > 85% |
| Documentation lag | IM-04 | < 1 sprint |
| Research intake velocity | IM-05 | 5+ items/quarter |

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/improvements/intakes` | Submit research intake |
| GET | `/v1/improvements/intakes` | List intakes (filterable) |
| GET | `/v1/improvements/intakes/{id}` | Get intake |
| POST | `/v1/improvements/intakes/{id}/transition` | Transition intake |
| POST | `/v1/improvements/lessons` | Record lesson learned |
| GET | `/v1/improvements/lessons` | List lessons |
| GET | `/v1/improvements/lessons/{id}` | Get lesson |
| POST | `/v1/improvements/lessons/{id}/complete-action` | Complete action |
| POST | `/v1/improvements/lessons/{id}/verify` | Verify lesson |
| POST | `/v1/improvements/checklists` | Create checklist |
| GET | `/v1/improvements/checklists` | List checklists |
| GET | `/v1/improvements/checklists/{id}` | Get checklist |
| POST | `/v1/improvements/checklists/{id}/complete` | Complete item |
| GET | `/v1/improvements/checklists/{id}/evaluate` | Evaluate checklist |
| GET | `/v1/improvements/metrics` | Latest metrics |
| GET | `/v1/improvements/metrics/history` | Metrics history |
| POST | `/v1/improvements/metrics/snapshot` | Save snapshot |
| POST | `/v1/improvements/metrics/default-snapshot` | Create default |
| GET | `/v1/improvements/metrics/trend/{id}` | Metric trend |
| POST | `/v1/improvements/refreshes` | Record refresh |
| GET | `/v1/improvements/refreshes` | List refreshes |
| GET | `/v1/improvements/refreshes/{id}` | Get refresh |
| POST | `/v1/improvements/refreshes/{id}/complete` | Complete refresh |

## Acceptance Criteria
- [x] Intake template exists and is referenced from planning docs.
- [x] Roadmap refresh cadence is documented.
- [x] Lessons learned are recorded in a consistent location.

## Key Artifacts
- `core/orchestrator/CONTINUOUS_IMPROVEMENT.md` - Research intake, roadmap refresh, continuous improvement

## Dependencies
- Phase 19

## Blocks
- None

## Review Checklist
- [x] Interfaces/contracts reviewed and approved.
- [x] Tests/fixtures or evidence added.
- [x] Documentation updated and verified.
- [x] Scope remains within this phase only.
