# Phase 17: Evaluation Suite Expansion & Regression Gates

## Status: Complete

## Overview
- **Phase**: 17 of 20
- **Category**: Evaluation
- **Completed**: 2026-02-14
- **Tests Added**: 77

## Objectives
- Expand golden task coverage and regression gates.
- Define gating thresholds for agent performance.
- Create a triage playbook for regressions.

## Implementation

| # | Component | Module | Description |
|---|-----------|--------|-------------|
| 1 | Data models | `evaluation/models.py` | GateType (4), MetricId (5), GoldenTag (5), TaskResult (4), RegressionIndicator (5), RegressionSeverity (4), TriageStatus (6), ThresholdOperator (5), plus 10 Pydantic models |
| 2 | Golden tasks | `evaluation/golden_tasks.py` | GT-01..GT-07 task definitions, GC-01..GC-04 case definitions, tag-based lookup helpers |
| 3 | Metrics calculator | `evaluation/metrics.py` | M-01 (success rate), M-02 (time-to-green), M-03 (rework rate), M-04 (diff size), M-05 (scope adherence) |
| 4 | Gate enforcer | `evaluation/gates.py` | 8 default thresholds (v1.0.0), gate execution matrix, threshold checking, golden task gating |
| 5 | Regression detector | `evaluation/regression.py` | RI-01 (task regression), RI-02 (threshold breach), RI-04 (TTG increase), plus RegressionRecorder with CRUD and triage lifecycle |
| 6 | Evaluation service | `evaluation/service.py` | Full pipeline: create run, submit results, compute metrics, check gate, detect regressions, manage baselines |
| 7 | Evaluation API | `api/routes/evaluations.py` | 12 REST endpoints under `/v1/evaluations` with scope-based auth |
| 8 | Router registration | `main.py` | Evaluations router added to FastAPI app |

### Gate Thresholds (v1.0.0)
| Metric | G-PR | G-MRG | G-REL |
|--------|------|-------|-------|
| M-01 Success Rate | >= 80% (block) | >= 90% (block) | >= 95% (block) |
| M-03 Rework Rate | <= 30% (warn) | <= 20% (block) | <= 10% (block) |
| M-05 Scope Adherence | >= 90% (block) | = 100% (block) | — |

### Golden Task Tags → Gate Mapping
| Gate | Required Tag | Items |
|------|-------------|-------|
| G-PR | GT-SMOKE | GT-01, GT-04, GC-01 |
| G-MRG | GT-CRITICAL | GT-01, GT-02, GT-05, GT-06, GC-02, GC-03 |
| G-REL | GT-RELEASE | GT-03, GT-04, GT-07, GC-02, GC-04 |
| G-MON | GT-OPTIONAL | (tracked, non-blocking) |

### API Endpoints
| Method | Path | Scope | Description |
|--------|------|-------|-------------|
| GET | `/v1/evaluations/golden-tasks` | workflows:read | List golden task defs |
| GET | `/v1/evaluations/golden-cases` | workflows:read | List golden case defs |
| GET | `/v1/evaluations/gates/{gate}/tasks` | workflows:read | Tasks for a gate |
| POST | `/v1/evaluations/runs` | tools:execute | Create evaluation run |
| GET | `/v1/evaluations/runs` | workflows:read | List runs |
| GET | `/v1/evaluations/runs/{id}` | workflows:read | Get run detail |
| POST | `/v1/evaluations/runs/{id}/results` | tools:execute | Submit results |
| POST | `/v1/evaluations/runs/{id}/baseline` | tools:execute | Save as baseline |
| GET | `/v1/evaluations/baselines` | workflows:read | List baselines |
| GET | `/v1/evaluations/regressions` | workflows:read | List regressions |
| PATCH | `/v1/evaluations/regressions/{id}/triage` | tools:execute | Update triage |
| POST | `/v1/evaluations/regressions/{id}/resolve` | tools:execute | Resolve regression |

## Acceptance Criteria
- [x] Gating thresholds are documented and versioned.
- [x] Triage playbook exists for failures.
- [x] Golden tasks are tagged for gating use.
- [x] Engine implementation with full evaluation pipeline.
- [x] 77 tests covering registry, metrics, gates, regression, service, and API.

## Key Artifacts
- `core/arch/REGRESSION_GATES.md` - Regression gates, triage playbook, golden task tags
- `core/arch/evaluation-harness.md` - Updated with regression gates reference
- `engine/src/agent33/evaluation/` - Evaluation module (6 files)
- `engine/src/agent33/api/routes/evaluations.py` - Evaluation API endpoints
- `engine/tests/test_phase17_evaluation.py` - 77 tests

## Dependencies
- Phase 16

## Blocks
- Phase 18

## Review Checklist
- [x] Interfaces/contracts reviewed and approved.
- [x] Tests/fixtures or evidence added.
- [x] Documentation updated and verified.
- [x] Scope remains within this phase only.
