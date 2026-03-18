# Session 93 Slice 3: Component-Security Read-Path Scaling

Date: 2026-03-18
Branch: `fix/session93-s3-component-security-scaling`

## Problem

`SecurityScanService.list_runs()` refreshed the full persisted run store on every call. That path loaded up to 10,000 runs, rebuilt each `SecurityRun`, then loaded findings for every run before applying in-memory filters and limits. As a result, `GET /v1/component-security/runs` paid whole-store refresh cost plus N findings queries even though list responses only need run summaries.

## Findings

1. The route layer already passes `tenant_id`, `status`, `profile`, and `limit` into `SecurityScanService.list_runs()`.
2. The SQLite store query only supported `tenant_id` and `limit`, so `status/profile` filtering happened after the read and after the limit was applied.
3. Findings are not required for the list path because each run row already carries `run_payload`; findings are loaded later through `fetch_findings()` and `get_run()`.
4. Existing tests already require list reads to remain store-backed for cross-instance freshness and restart visibility.

## Changes

1. Extended `SecurityScanStore.list_runs()` with optional `status` and `profile` filters and pushed those filters into SQL before `ORDER BY created_at DESC LIMIT ?`.
2. Changed `SecurityScanService.list_runs()` to read directly from the store when persistence is enabled, hydrate only the returned runs, and stop hydrating findings on the list path.
3. Kept startup hydration, `get_run()`, `fetch_findings()`, persistence writes, and cross-instance freshness behavior unchanged.
4. Added tests for:
   - SQL-side `status` filtering before limit
   - SQL-side `profile` filtering before limit
   - service list path using `store.list_runs()` without calling `store.get_findings()`

## Validation

- `python -m pytest engine/tests/test_security_persistence.py -q --no-cov` -> `34 passed`
- `python -m pytest engine/tests/test_component_security_api.py -q --no-cov` -> `21 passed`
- `python -m ruff check engine/src/agent33/component_security/persistence.py engine/src/agent33/services/security_scan.py engine/tests/test_security_persistence.py`
- `python -m mypy engine/src/agent33/component_security/persistence.py engine/src/agent33/services/security_scan.py --config-file engine/pyproject.toml`

## Scope Boundary

This slice reduces the expensive list-read path only. It does not change `get_run()` findings hydration, persistence write behavior, scanner execution, or route contracts outside the list semantics already exposed by the API.
