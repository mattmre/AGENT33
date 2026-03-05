# Session 55: Phase 30 API Policy Fixtures & Operational Tuning Docs

Date: 2026-03-07
Scope: Phase 30 refinement — API-level integration tests and operational documentation

## Problem

Phase 30 (Strategic User Outcome Improvement Loops) core was fully merged with
comprehensive unit tests for the effort router, heuristic classifier, and runtime
integration. However, two gaps remained:

1. **No API-level integration tests** verified that different `effort` params in
   `POST /v1/agents/{id}/invoke` request bodies actually route through the effort
   router and surface calibration metadata in HTTP responses.
2. **No operational documentation** explained the tuning cadence for effort
   thresholds, alert ownership, or escalation paths.

## Baseline reviewed

- `engine/src/agent33/agents/effort.py` — the effort router and heuristic classifier
- `engine/src/agent33/api/routes/agents.py` — the invoke endpoint wiring
- `engine/tests/test_phase30_effort_routing.py` — existing unit and runtime tests
- `engine/tests/conftest.py` — test client and auth token fixtures
- `docs/research/session53-phase30-threshold-calibration.md` — threshold design
- `docs/research/session53-phase30-outcome-acceptance.md` — acceptance matrix design

## Changes made

### 1. API-level integration tests (`TestEffortAPIRouting`)

Added a new test class to `engine/tests/test_phase30_effort_routing.py` with tests
that exercise the HTTP layer end-to-end:

| Test | Verifies |
|------|----------|
| `test_invoke_with_explicit_effort_routes_through_effort_router` | `effort=high` in request body reaches the runtime constructor |
| `test_invoke_with_low_effort_routes_correctly` | `effort=low` routing path |
| `test_invoke_without_effort_falls_through_to_heuristic` | Omitting effort triggers heuristic source |
| `test_invoke_tenant_policy_fixture_routes_via_policy` | Tenant-level policy key appears in response routing |
| `test_invoke_domain_policy_fixture_routes_via_domain` | Domain-level policy key + domain forwarding to runtime |
| `test_invoke_response_contains_calibration_metadata` | Heuristic score, thresholds, confidence, and reasons in response |
| `test_invoke_with_medium_effort_populates_routing_in_response` | Routing dict is always present when effort routing is active |

All tests use the existing `client` fixture from `conftest.py` (token with
`sub="test-user"`, `scopes=["admin"]`) and mock `AgentRuntime` at the API boundary
to isolate the HTTP contract from LLM calls.

### 2. Alert ownership documentation

Added an operational tuning guide as the module docstring of
`engine/src/agent33/agents/effort.py`. It covers:

- **Weekly ops review**: cost drift dashboards, high-effort trend monitoring
- **Monthly calibration**: threshold re-evaluation against production profiles
- **Quarterly review**: model pricing reassessment, policy archival
- **Alert ownership table**: maps each metric alert to its owning team and
  escalation target

### 3. Non-goals

- No changes to effort routing logic or heuristic weights.
- No changes to the API contract (request/response models unchanged).
- No new configuration settings introduced.

## Verification

```bash
cd engine
python -m ruff check src/ tests/
python -m ruff format src/ tests/
python -m pytest tests/test_phase30_effort_routing.py -q --no-cov
```

## Expected effect

- API-level regression safety net for effort routing through the invoke endpoint.
- Clear operational runbook for teams tuning effort thresholds in production.
- Completes Phase 30 refinement backlog items from the session 55 plan.
