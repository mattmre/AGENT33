# Session 54 Delta: HITL Approval Lifecycle

## Goal
Add an explicit human-in-the-loop approval lifecycle for governed tool operations that are:
- `ask`-gated by tool policies
- destructive in supervised autonomy mode

## Implementation Summary
- Added approval domain models/service:
  - `engine/src/agent33/tools/approvals.py`
  - request statuses: pending, approved, rejected, consumed, expired
  - reasons: `tool_policy_ask`, `supervised_destructive`
- Extended `ToolContext` with request attribution:
  - `requested_by`, `tenant_id`
- Integrated approvals into governance:
  - `engine/src/agent33/tools/governance.py`
  - blocked requests now create approval records
  - approved requests can be consumed via `__approval_id`
- Enforced supervised governance in iterative execution:
  - `ToolLoop` now passes the agent autonomy level into governance checks
- Added operator endpoints:
  - `GET /v1/approvals/tools`
  - `GET /v1/approvals/tools/{approval_id}`
  - `POST /v1/approvals/tools/{approval_id}/decision`

## Validation
- `ruff` and `mypy` on changed modules passed.
- pytest passed:
  - `tests/test_hitl_approvals.py`
  - `tests/test_phase14_security.py`

## Next
- Follow-on slice: modular retrieval stages and retrieval diagnostics while preserving current RAG contracts.
