# Phase 19: Release & Sync Automation

## Overview
- **Phase**: 19 of 20
- **Category**: Distribution
- **Status**: Complete
- **Tests**: 66 new tests

## Objectives
- Define release cadence and sync automation.
- Standardize release notes and rollback guidance.
- Ensure provenance and evidence travel with releases.

## Implementation

| # | Component | Module | Description |
|---|-----------|--------|-------------|
| 1 | Data models | `release/models.py` | 8 enums (ReleaseType, ReleaseStatus, CheckStatus, SyncStrategy, SyncFrequency, SyncStatus, RollbackType, RollbackStatus), 8+ Pydantic models |
| 2 | Pre-release checklist | `release/checklist.py` | RL-01..RL-08 checks, RL-07 major-only, ChecklistEvaluator |
| 3 | Sync engine | `release/sync.py` | Rule matching (fnmatch), dry-run support, execution, validation, checksum |
| 4 | Rollback manager | `release/rollback.py` | Decision matrix (severity x impact), lifecycle (create/approve/step/complete/fail) |
| 5 | Release service | `release/service.py` | CRUD, lifecycle state machine, checklist, sync delegation, rollback delegation |
| 6 | Release API | `api/routes/releases.py` | 18 REST endpoints under `/v1/releases` |

### Release Lifecycle State Machine

```
PLANNED -> FROZEN -> RC -> VALIDATING -> RELEASED -> ROLLED_BACK -> PLANNED
                                      -> FAILED   -> PLANNED
                  -> PLANNED (unfreeze)
```

### Pre-Release Checklist (RL-01..RL-08)

| Check | ID | Required |
|-------|-----|----------|
| All PRs merged | RL-01 | Always |
| Gates pass | RL-02 | Always |
| Changelog updated | RL-03 | Always |
| Version bumped | RL-04 | Always |
| Documentation updated | RL-05 | Always |
| Security review | RL-06 | Always |
| Rollback tested | RL-07 | Major only |
| Release notes drafted | RL-08 | Always |

### Rollback Decision Matrix

| Severity | Impact | Type | Approval |
|----------|--------|------|----------|
| Critical | High | Immediate | On-call |
| Critical | Medium | Immediate | On-call |
| High | High | Immediate | Team lead |
| Medium | Medium | Partial | Team lead |
| Low | Low | Config | Engineer |

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/releases` | Create release |
| GET | `/v1/releases` | List releases |
| GET | `/v1/releases/{id}` | Get release |
| POST | `/v1/releases/{id}/freeze` | Feature freeze |
| POST | `/v1/releases/{id}/rc` | Cut release candidate |
| POST | `/v1/releases/{id}/validate` | Start validation |
| POST | `/v1/releases/{id}/publish` | Publish release |
| GET | `/v1/releases/{id}/checklist` | Get checklist |
| PATCH | `/v1/releases/{id}/checklist` | Update check |
| POST | `/v1/releases/sync/rules` | Create sync rule |
| GET | `/v1/releases/sync/rules` | List sync rules |
| POST | `/v1/releases/sync/rules/{id}/dry-run` | Dry-run sync |
| POST | `/v1/releases/sync/rules/{id}/execute` | Execute sync |
| POST | `/v1/releases/{id}/rollback` | Initiate rollback |
| GET | `/v1/releases/rollbacks` | List rollbacks |
| POST | `/v1/releases/rollback/recommend` | Get recommendation |

## Acceptance Criteria
- [x] Release cadence is documented and approved.
- [x] Sync automation includes a dry-run step.
- [x] Rollback steps are documented and tested when feasible.

## Key Artifacts
- `core/orchestrator/RELEASE_CADENCE.md` - Release cadence, sync automation, rollback procedures
- `core/orchestrator/distribution/DISTRIBUTION_SYNC_SPEC.md` - Distribution sync architecture

## Dependencies
- Phase 18

## Blocks
- Phase 20

## Review Checklist
- [x] Interfaces/contracts reviewed and approved.
- [x] Tests/fixtures or evidence added.
- [x] Documentation updated and verified.
- [x] Scope remains within this phase only.
