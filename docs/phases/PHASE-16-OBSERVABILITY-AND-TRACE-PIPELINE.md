# Phase 16: Observability & Trace Pipeline

## Status: Complete

## Overview
- **Phase**: 16 of 20
- **Category**: Observability
- **Completed**: 2026-02-14
- **Tests Added**: 54

## Objectives
- Define a trace schema for agent runs.
- Standardize logs, artifacts, and failure taxonomy.
- Enable audit-friendly run reconstruction.

## Implementation

| # | Component | Module | Description |
|---|-----------|--------|-------------|
| 1 | Trace models | `observability/trace_models.py` | TraceRecord, TraceStep, TraceAction, TraceStatus (6 states), ActionStatus (4 states), ArtifactType (9 types), TraceContext, TraceOutcome |
| 2 | Failure taxonomy | `observability/failure.py` | FailureCategory (10 categories: F-ENV through F-UNK), FailureSeverity (4 levels), retryable/escalation metadata, `from_exception()` classmethod |
| 3 | Trace collector | `observability/trace_collector.py` | In-memory trace/failure CRUD with tenant, status, task filters; auto-creates steps; completes open steps on trace completion |
| 4 | Retention policies | `observability/retention.py` | 9 artifact types with tiered storage (hot/warm/cold), retention periods (7d–permanent), standardized storage paths |
| 5 | Trace API | `api/routes/traces.py` | 7 REST endpoints under `/v1/traces` with scope-based auth |
| 6 | Router registration | `main.py` | Traces router added to FastAPI app |

### Trace ID Format
`TRC-YYYYMMDD-HHMMSS-XXXX` (timestamp + 4 hex chars)

### Failure Categories
| Code | Category | Retryable | Escalate After |
|------|----------|-----------|----------------|
| F-ENV | Environment | Yes | 3 retries |
| F-INP | Input/validation | No | immediate |
| F-EXE | Execution | Yes | 2 retries |
| F-TMO | Timeout | Yes | 2 retries |
| F-RES | Resource exhaustion | Yes | 1 retry |
| F-SEC | Security violation | No | immediate |
| F-DEP | Dependency failure | Yes | 3 retries |
| F-VAL | Validation failure | No | immediate |
| F-REV | Review rejection | No | immediate |
| F-UNK | Unknown | No | immediate |

### Retention Policies
| Artifact | Retention | Initial Tier | Transitions |
|----------|-----------|-------------|-------------|
| TMP | 7 days | hot | — |
| LOG, OUT | 30 days | hot | → warm@30d |
| DIF, TST, SES, CFG | 90 days | warm | → cold@90d |
| REV, EVD | permanent | cold | — |

### API Endpoints
| Method | Path | Scope | Description |
|--------|------|-------|-------------|
| POST | `/v1/traces/` | tools:execute | Start a trace |
| GET | `/v1/traces/` | workflows:read | List traces (filterable) |
| GET | `/v1/traces/{id}` | workflows:read | Get trace detail |
| POST | `/v1/traces/{id}/actions` | tools:execute | Add action to trace |
| POST | `/v1/traces/{id}/complete` | tools:execute | Complete a trace |
| POST | `/v1/traces/{id}/failures` | tools:execute | Record a failure |
| GET | `/v1/traces/{id}/failures` | workflows:read | List failures for trace |

## Acceptance Criteria
- [x] Trace schema documented and referenced in logs.
- [x] Failure taxonomy is defined with examples.
- [x] Artifact storage paths are standardized.
- [x] Engine implementation with full CRUD and lifecycle.
- [x] 54 tests covering models, taxonomy, collector, retention, and API.

## Key Artifacts
- `core/orchestrator/TRACE_SCHEMA.md` - Trace schema, failure taxonomy, artifact retention
- `core/orchestrator/handoff/EVIDENCE_CAPTURE.md` - Updated with trace references
- `engine/src/agent33/observability/trace_models.py` - Trace data models
- `engine/src/agent33/observability/failure.py` - Failure taxonomy
- `engine/src/agent33/observability/trace_collector.py` - Trace collection service
- `engine/src/agent33/observability/retention.py` - Retention policies
- `engine/src/agent33/api/routes/traces.py` - Trace API endpoints
- `engine/tests/test_phase16_observability.py` - 54 tests

## Dependencies
- Phase 15

## Blocks
- Phase 17

## Review Checklist
- [x] Interfaces/contracts reviewed and approved.
- [x] Tests/fixtures or evidence added.
- [x] Documentation updated and verified.
- [x] Scope remains within this phase only.
