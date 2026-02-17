# Phase 28 Stage 1 Backend Implementation Notes (2026-02-17)

## Context

This note captures final implementation decisions for Phase 28 Stage 1 after architecture/research review and code delivery.

## Implemented Scope

### Backend domain model
- Added `engine/src/agent33/component_security/models.py`:
  - `SecurityRun`, `SecurityFinding`, `FindingsSummary`
  - enums for profile/status/severity/category
  - target/options/metadata submodels

### Adapter/service layer
- Added `engine/src/agent33/services/pentagi_integration.py`:
  - `PentAGIService` run lifecycle (`pending -> running -> completed|failed|timeout|cancelled`)
  - Stage 1 quick-profile execution using:
    - `python -m bandit -r <target> -f json`
    - `gitleaks detect --report-format json`
  - explicit typed error classes (`RunNotFoundError`, `RunStateError`, `ToolExecutionError`)
  - normalized findings mapping for bandit + gitleaks output

### API layer
- Added `engine/src/agent33/api/routes/component_security.py`:
  - `POST /v1/component-security/runs`
  - `GET /v1/component-security/runs`
  - `GET /v1/component-security/runs/{run_id}`
  - `GET /v1/component-security/runs/{run_id}/status`
  - `GET /v1/component-security/runs/{run_id}/findings`
  - `POST /v1/component-security/runs/{run_id}/cancel`
  - `DELETE /v1/component-security/runs/{run_id}`
- Added route wiring in `engine/src/agent33/main.py`.
- Added permission scopes in `engine/src/agent33/security/permissions.py`:
  - `component-security:read`
  - `component-security:write`

### Test coverage
- Added `engine/tests/test_component_security_api.py`:
  - model defaults/aggregation
  - service quick-profile execution with mocked command runner
  - API lifecycle + scope enforcement paths

## Key Decisions

1. **Stage 1 runtime profile support is strict quick-only**
   - Rationale: Phase 28 Stage 1 explicitly targets quick profile delivery.
   - Forward-compatibility: `standard` and `deep` remain in the enum for Stage 2 expansion.

2. **Execution can be deferred (`execute_now=false`)**
   - Rationale: supports queued/manual workflows and deterministic tests.

3. **Tool execution failures become explicit run states**
   - Missing tools/invalid output/path errors map to `failed` with actionable `error_message`.
   - Timeouts map to `timeout`.

## Deferred to Stage 2+

- Full `standard` and `deep` execution matrices
- Findings deduplication across tool families
- Release gate policy model/enforcement wiring
- Frontend run/finding workspace
