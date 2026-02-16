# Phase 22 PR-04: Workflow Scheduling and Execution History

## Scope
- Add operator-facing schedule management for workflows.
- Add additive repeat/autonomous execution controls.
- Add workflow execution history endpoint for observability.

## Key Changes
- Updated `engine/src/agent33/api/routes/workflows.py`:
  - Extended execute request with `repeat_count`, `repeat_interval_seconds`, `autonomous`
  - Added `POST /v1/workflows/{name}/schedule`
  - Added `GET /v1/workflows/schedules`
  - Added `DELETE /v1/workflows/schedules/{job_id}`
  - Added `GET /v1/workflows/{name}/history`
  - Added in-memory execution history capture for manual + scheduled runs
  - Preserved default execute response shape for non-repeat/non-autonomous requests
- Added `engine/tests/test_workflow_scheduling_api.py`:
  - schedule CRUD coverage
  - history coverage
  - repeat/autonomous coverage
  - backward compatibility assertions
  - scope/access coverage

## Validation
- `cd engine && python -m ruff check src/agent33/api/routes/workflows.py tests/test_workflow_scheduling_api.py`
- `cd engine && python -m pytest tests/test_workflow_scheduling_api.py tests/test_idor_access_control.py -q`

