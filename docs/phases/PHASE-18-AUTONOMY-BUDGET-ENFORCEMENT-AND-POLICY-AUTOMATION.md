# Phase 18: Autonomy Budget Enforcement & Policy Automation

## Overview
- **Phase**: 18 of 20
- **Category**: Governance
- **Status**: Complete
- **Tests**: 94 new tests

## Objectives
- Enforce autonomy budgets with preflight checks.
- Automate policy validation where feasible.
- Define stop conditions and escalation paths.

## Implementation

| # | Component | Module | Description |
|---|-----------|--------|-------------|
| 1 | Data models | `autonomy/models.py` | 7 enums (BudgetState, StopAction, EscalationUrgency, PolicyAction, EnforcementResult, PreflightStatus), 10+ Pydantic models |
| 2 | Preflight checker | `autonomy/preflight.py` | PF-01..PF-10 checks (budget exists, valid, not expired, scope, files, commands, network, limits, stop conditions, escalation path) |
| 3 | Runtime enforcer | `autonomy/enforcement.py` | EF-01..EF-08 (file read/write, command, network, iteration, duration, files modified, lines changed), stop condition evaluation, escalation |
| 4 | Autonomy service | `autonomy/service.py` | Budget CRUD, lifecycle state machine (DRAFT->ACTIVE->COMPLETED), preflight, enforcement, escalation management |
| 5 | Autonomy API | `api/routes/autonomy.py` | 18 REST endpoints under `/v1/autonomy` |

### Budget Lifecycle State Machine

```
DRAFT -> PENDING_APPROVAL -> ACTIVE -> SUSPENDED -> ACTIVE (resume)
DRAFT -> ACTIVE (skip approval)                  -> EXPIRED
                              ACTIVE -> COMPLETED
                              ACTIVE -> EXPIRED
PENDING_APPROVAL -> REJECTED -> DRAFT (retry)
```

### Enforcement Points

| ID | Check | Scope |
|----|-------|-------|
| EF-01 | File read | fnmatch against deny/read allowlist patterns |
| EF-02 | File write | fnmatch against deny/write allowlist patterns + file/line limits |
| EF-03 | Command execution | denied list, approval list, allowlist with args_pattern regex |
| EF-04 | Network request | enabled check, denied domains, allowed domains, request limit |
| EF-05 | Iteration limit | Count vs max_iterations |
| EF-06 | Duration limit | Elapsed minutes vs max_duration_minutes |
| EF-07 | Files modified limit | Count vs max_files_modified |
| EF-08 | Lines changed limit | Count vs max_lines_changed |

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/autonomy/budgets` | Create budget |
| GET | `/v1/autonomy/budgets` | List budgets |
| GET | `/v1/autonomy/budgets/{id}` | Get budget |
| DELETE | `/v1/autonomy/budgets/{id}` | Delete budget |
| POST | `/v1/autonomy/budgets/{id}/transition` | Transition state |
| POST | `/v1/autonomy/budgets/{id}/activate` | Activate |
| POST | `/v1/autonomy/budgets/{id}/suspend` | Suspend |
| POST | `/v1/autonomy/budgets/{id}/complete` | Complete |
| GET | `/v1/autonomy/budgets/{id}/preflight` | Run preflight |
| POST | `/v1/autonomy/budgets/{id}/enforcer` | Create enforcer |
| POST | `/v1/autonomy/budgets/{id}/enforce/file` | Check file access |
| POST | `/v1/autonomy/budgets/{id}/enforce/command` | Check command |
| POST | `/v1/autonomy/budgets/{id}/enforce/network` | Check network |
| POST | `/v1/autonomy/budgets/{id}/escalate` | Trigger escalation |
| GET | `/v1/autonomy/escalations` | List escalations |
| POST | `/v1/autonomy/escalations/{id}/acknowledge` | Acknowledge |
| POST | `/v1/autonomy/escalations/{id}/resolve` | Resolve |

## Acceptance Criteria
- [x] Autonomy budgets include command, file, and network scope.
- [x] Preflight enforcement steps are documented.
- [x] Stop conditions and escalation paths are explicit.

## Key Artifacts
- `core/orchestrator/AUTONOMY_ENFORCEMENT.md` - Preflight checks, enforcement, escalation
- `core/orchestrator/handoff/AUTONOMY_BUDGET.md` - Updated with enforcement reference

## Dependencies
- Phase 17

## Blocks
- Phase 19

## Review Checklist
- [x] Interfaces/contracts reviewed and approved.
- [x] Tests/fixtures or evidence added.
- [x] Documentation updated and verified.
- [x] Scope remains within this phase only.
