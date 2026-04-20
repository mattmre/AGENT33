# Session 129 Slice 1: P-PACK A/B Review Hardening

**Date:** 2026-04-20  
**Scope:** Post-merge remediation for still-valid P-PACK A/B hardening issues from
the merged review feedback on the POST-4.4 / POST-4.5 slices, on top of merged
baseline commit 5de4f78 (PR #410).

## Decision

This slice implements a focused set of hardening fixes for the P-PACK v3 A/B
harness that were identified in the merged review debt around the POST-4.4 /
POST-4.5 slices and deferred to avoid widening those earlier PRs. These fixes
improve API error handling, data integrity, and test coverage.

## Baseline Reviewed

- Latest merged baseline: commit `5de4f78` (PR #410)
- PR #406 review feedback on GitHub
- `engine/src/agent33/api/routes/outcomes.py`
- `engine/src/agent33/evaluation/ppack_ab_service.py`
- `engine/src/agent33/evaluation/ppack_ab_persistence.py`
- `engine/tests/test_outcomes_api.py`
- `engine/src/agent33/outcomes/service.py`
- `engine/src/agent33/outcomes/persistence.py`

## Findings

### 1. Outcomes API Error Handling Gap

**Issue:** The P-PACK v3 assignment/retrieval endpoints (`POST /ppack-v3/assignments`,
`GET /ppack-v3/assignments/{session_id}`, `GET /ppack-v3/reports/{report_id}`)
catch `RuntimeError` and return 503, but do not explicitly catch `sqlite3.Error`.

If SQLite persistence fails (e.g., database locked, disk I/O error, integrity
constraint violation), the exception would bubble up as a raw 500 instead of
a consistent 503 service-unavailable response.

The report generation endpoint already handles `sqlite3.Error` correctly (line 295
in outcomes.py).

**Impact:** Inconsistent error responses for persistence failures. Operators
cannot reliably distinguish transient SQLite issues from application bugs.

**Fix:** Add explicit `sqlite3.Error` exception handling to the three affected
endpoints, mapping them to 503 with a descriptive detail message matching the
pattern used in the report endpoint.

### 2. Assignment/Report Variant Integrity

**Issue:** The `_resolve_event_variant` method in `PPackABService` (lines 308-323)
trusts caller-supplied `metadata['ppack_variant']` before falling back to the
persisted assignment record.

This creates a data-integrity risk: a client could spoof variant assignments by
sending incorrect metadata, polluting the A/B comparison buckets.

The persisted assignment (retrieved via `assign_variant` and stored in SQLite)
should be the single source of truth for variant resolution.

**Impact:** Report accuracy depends on client honesty. Malicious or buggy clients
could skew A/B results.

**Fix:** Remove the caller-metadata fallback. Always resolve variant from the
persisted assignment lookup via `assignments_by_session`.

### 3. Test Hygiene: Resource Cleanup

**Issue:** The `reset_outcomes_service` autouse fixture in `test_outcomes_api.py`
creates a fresh `PPackABService` with an in-memory SQLite connection on each test,
but does not explicitly close the service (and its underlying persistence
connection) during teardown.

While Python's garbage collector will eventually close these connections, explicit
cleanup is more reliable and prevents resource warnings in test output.

**Impact:** Minor resource leak in test suite. No production impact.

**Fix:** Add `outcomes_mod._ppack_ab_service.close()` in the fixture's teardown
section (after `yield`, before restoring saved state).

### 4. Test Coverage: Tenant Scoping

**Issue:** The `test_dashboard_contract` test creates events for both `tenant-a`
and `tenant-b`, but only asserts on the summary/trends fields. It does not verify
that `recent_events` respects tenant boundaries.

This is a regression: earlier versions of the test included this assertion, which
was removed during a refactor.

**Impact:** Reduced test coverage for multi-tenant isolation.

**Fix:** Restore the assertion:
```python
recent_events = payload["recent_events"]
assert len(recent_events) == 2
assert all(event["tenant_id"] == "tenant-a" for event in recent_events)
```

### 5. Test Coverage: New Hardening Behaviors

**Issue:** The fixes in findings 1-2 introduce new behavior (sqlite error mapping,
variant integrity) but lack focused regression tests.

**Fix:** Add three new tests:
- `test_ppack_variant_resolution_uses_persisted_assignment`: Verify that spoofed
  caller metadata does not affect variant resolution.
- `test_ppack_assignment_sqlite_error_returns_503`: Verify that assignment
  persistence failures map to 503.
- `test_ppack_get_assignment_sqlite_error_returns_503`: Verify that assignment
  retrieval persistence failures map to 503.
- `test_ppack_get_report_sqlite_error_returns_503`: Verify that report retrieval
  persistence failures map to 503.

### 6. Window Semantics Audit: "All Time" Wording

**Investigation:** The P-PACK v3 report markdown rendering (line 277 in
`ppack_ab_service.py`) displays `'all time'` when `report.since is None`.

However, the underlying `OutcomesPersistence.load_events` method has a hard
`LIMIT 1000` cap (line 86 in `outcomes/persistence.py`). This means that "all time"
is misleading — it actually means "the 1000 most recent events."

**Current API Path Analysis:**
- The `/ppack-v3/report` route (lines 274-305 in `outcomes.py`) has two code paths:
  1. When `body.since is None and body.until is None`, it calls
     `generate_weekly_report`, which ALWAYS sets both `since` and `until`
     (lines 124-125 in `ppack_ab_service.py`).
  2. When either `body.since` or `body.until` is not None, it calls
     `generate_report(since=body.since, until=body.until)`.

- Therefore, `since=None` can only reach `load_historical` if:
  - A caller explicitly passes `since=None, until=<some_value>` (or vice versa)
    to the API route.
  - Direct service-layer code bypasses the route and calls `generate_report`
    with `since=None`.

**User Visibility:** The markdown field is returned in the API response
(`report["markdown"]`), so if `since=None` were ever used, the misleading
"all time" wording would be visible to API clients.

**Conclusion:** In the current normal API usage path (weekly report or explicit
time range), `since=None` does not occur, so "all time" is not directly
user-visible. However, the API contract allows it, and the wording would be
misleading if it were used.

**Decision:** This is a low-priority issue because the current normal paths do not
trigger it. Fixing it would require either:
1. Surfacing the 1000-event cap in the markdown when `since=None` (honest but
   adds complexity).
2. Forbidding `since=None` entirely at the service layer (breaking change).
3. Removing the LIMIT or making it configurable (scope creep).

**Intentional Defer:** None of these options are surgical. The finding is
documented here for future consideration, but this slice does NOT expand scope
to fix it. The current behavior is technically correct (it does return all
available historical events, up to the persistence layer's cap), just poorly
worded in the edge case.

## Execution Summary

### Files Changed

1. **`engine/src/agent33/api/routes/outcomes.py`**
   - Added `sqlite3.Error` exception handling to `assign_ppack_variant`,
     `get_ppack_assignment`, and `get_ppack_report` endpoints.
   - Map SQLite errors to 503 with descriptive detail messages.

2. **`engine/src/agent33/evaluation/ppack_ab_service.py`**
   - Removed caller-metadata fallback in `_resolve_event_variant`.
   - Variant resolution now exclusively uses persisted assignment records.

3. **`engine/tests/test_outcomes_api.py`**
   - Added `sqlite3` import.
   - Added `outcomes_mod._ppack_ab_service.close()` call in
     `reset_outcomes_service` fixture teardown.
   - Restored tenant-scoping assertion in `test_dashboard_contract`.
   - Added four new regression tests for error handling and variant integrity.

### Review Findings Fixed

1. ✅ Outcomes API hardening: SQLite errors now map to 503 consistently.
2. ✅ Assignment/report integrity: Persisted assignment is the authority for
   variant resolution.
3. ✅ Test hygiene: P-PACK A/B service resources explicitly closed in teardown.
4. ✅ Test coverage: Recent events tenant-scoping assertion restored.
5. ✅ Test coverage: Regression tests added for new error-handling and
   variant-integrity behavior.

### Intentionally Deferred

1. **Window semantics "all time" wording:** The edge-case issue is documented
   above but not fixed in this slice. The wording is only misleading when
   `since=None` is explicitly passed, which does not occur in the current normal
   API paths (weekly report or explicit time range). Fixing it would require
   non-surgical changes (API contract restrictions, UI changes, or persistence
   layer redesign). Defer to a future slice if real usage patterns make this
   visible.

## Validation Commands

```bash
# Targeted pytest for touched outcomes/PPACK tests
cd C:\GitHub\repos\AGENT33\worktrees\session129-s1-ppack-review-hardening
$env:PYTHONPATH="C:\GitHub\repos\AGENT33\worktrees\session129-s1-ppack-review-hardening\engine\src"
pytest engine/tests/test_outcomes_api.py --no-cov -v

# Ruff check
ruff check engine/src/agent33/api/routes/outcomes.py engine/src/agent33/evaluation/ppack_ab_service.py engine/tests/test_outcomes_api.py

# Ruff format check
ruff format --check engine/src/agent33/api/routes/outcomes.py engine/src/agent33/evaluation/ppack_ab_service.py engine/tests/test_outcomes_api.py

# Mypy
mypy engine/src/agent33/api/routes/outcomes.py engine/src/agent33/evaluation/ppack_ab_service.py --config-file engine/pyproject.toml
```

## Branch State

- Branch: `session129-s1-ppack-review-hardening`
- Ready for PR creation: pending validation results
