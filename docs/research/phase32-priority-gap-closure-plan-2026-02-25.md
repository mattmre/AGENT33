# Phase 32 Priority Gap-Closure Plan (2026-02-25)

## Baseline verified

Baseline is taken from current repo code plus `docs/next-session.md` and review packets (`docs/review-packets/*`).

- **PR-1 (Phase32 adoption) baseline exists**
  - Connector boundary primitives are implemented (`engine/src/agent33/connectors/{executor.py,middleware.py,governance.py,circuit_breaker.py,boundary.py}`).
  - Boundary wiring is already present for MCP bridge and key HTTP surfaces:
    - `engine/src/agent33/tools/mcp_bridge.py`
    - `engine/src/agent33/tools/builtin/web_fetch.py`
    - `engine/src/agent33/tools/builtin/search.py`
    - `engine/src/agent33/workflows/actions/http_request.py`
  - Session validation gates recorded: **11 / 92 / 187**.

- **PR-2 (persistence hardening) baseline exists**
  - Backends and migration/backup/restore primitives are implemented:
    - `InMemoryLearningSignalStore`, `FileLearningSignalStore`, `SQLiteLearningSignalStore`
    - `migrate_file_learning_state_to_db`, `backup_learning_state`, `restore_learning_state`
    - Files: `engine/src/agent33/improvement/persistence.py`, `.../service.py`, `.../api/routes/improvements.py`
  - Session validation gates recorded: **14 / 187**.

- **PR-3 (observability integration) baseline exists**
  - Effort routing decision metadata is emitted from runtime (`engine/src/agent33/agents/runtime.py`) and exported to metrics in agent routes (`engine/src/agent33/api/routes/agents.py`).
  - Dashboard metrics/alerts routes and startup alert-rule wiring are present:
    - `engine/src/agent33/api/routes/dashboard.py`
    - `engine/src/agent33/observability/{metrics.py,alerts.py}`
    - `engine/src/agent33/main.py`
  - Session validation gates recorded: **38 / 15 / 187**.

## Gap matrix

| PR | Gap | Current evidence | Closure action |
|---|---|---|---|
| PR-1 | Connector-boundary adoption is not yet guaranteed for every external connector surface | Boundary is active for MCP/web_fetch/search/http_request, but adoption target in `docs/next-session.md` explicitly says “expand beyond MCP” and “route/service integration points” | Inventory all outbound connector call sites and route each through `build_connector_boundary_executor` + `map_connector_exception`; add missing tests per adopted surface |
| PR-1 | Policy-pack behavior is implemented but not fully tied to per-surface defaults in code docs/runbooks | Policy packs exist in `engine/src/agent33/connectors/boundary.py` and `docs/default-policy-packs.md` | Set explicit pack selection at each connector entry point (where needed), and document expected default/override behavior in operator-facing docs |
| PR-2 | Persistence hardening lacks explicit operational playbook controls around migration/backup/recovery execution path | Primitives exist, but route/service flow currently only auto-migrates on startup flag; no explicit API/CLI-triggered backup/restore path | Add explicit operator entry points (API or command task) for backup/restore and migration status; enforce deterministic error contract for corruption and restore failure paths |
| PR-2 | DB corruption handling is reset-oriented but lacks explicit verification/telemetry gate | SQLite load currently deletes invalid payload row and returns empty state | Add explicit corruption event telemetry/logging and tests that verify behavior + auditability |
| PR-3 | Observability is in-memory only; no durable/export sink integration defined | `MetricsCollector` is process-local memory; dashboard reads local summary only | Add metrics export integration path (Prometheus/OpenTelemetry-compatible adapter or equivalent project standard) while keeping current dashboard contract stable |
| PR-3 | Alert thresholds exist, but operational ownership/tuning loop is not formalized | Alert rules are configured in `main.py` from settings | Define threshold ownership + review cadence; add config validation/tests for threshold regressions |

## File-level change list per PR

### PR-1 — Phase32 adoption

1. **Connector adoption inventory + wiring**
   - `engine/src/agent33/tools/` (all external-call tools, including MCP clients)
   - `engine/src/agent33/workflows/actions/` (all outbound network actions)
   - `engine/src/agent33/connectors/boundary.py` (only if new pack/default behavior is required)
2. **Policy-pack/default behavior documentation alignment**
   - `docs/default-policy-packs.md` (update only if pack semantics or defaults change)
3. **Test coverage for each newly adopted connector surface**
   - `engine/tests/test_phase32_connector_boundary.py`
   - Additional connector-regression tests already used in the 92-count gate

### PR-2 — Persistence hardening

1. **Operational hardening + deterministic failure behavior**
   - `engine/src/agent33/improvement/persistence.py`
   - `engine/src/agent33/improvement/service.py`
   - `engine/src/agent33/api/routes/improvements.py`
2. **Migration/backup/restore operator flow**
   - `engine/src/agent33/api/routes/improvements.py` (if API-triggered)
   - `docs/` operator notes/runbook location per current docs convention
3. **Regression tests**
   - `engine/tests/test_phase31_learning_signals.py`

### PR-3 — Observability integration

1. **Routing telemetry continuity and export**
   - `engine/src/agent33/agents/runtime.py`
   - `engine/src/agent33/api/routes/agents.py`
   - `engine/src/agent33/observability/metrics.py`
   - `engine/src/agent33/api/routes/dashboard.py`
2. **Alerting integration/tuning controls**
   - `engine/src/agent33/main.py`
   - `engine/src/agent33/observability/alerts.py`
   - `engine/src/agent33/config.py` (if threshold/config contract expands)
3. **Regression tests**
   - `engine/tests/test_phase30_effort_routing.py`
   - `engine/tests/test_integration_wiring.py`

## Acceptance criteria

### PR-1
- All identified outbound connector surfaces execute through connector boundary middleware.
- Middleware order and behavior remain deterministic (governance -> timeout/retry -> circuit breaker -> metrics, as configured).
- Policy-pack behavior is explicit per connector entry point and documented.
- PR-1 gates reproduce: **11 passed**, **92 passed**, **187 passed**.

### PR-2
- Migration from file to DB remains deterministic and idempotent.
- Backup/restore path is executable and validated (success + failure paths).
- Corruption behavior is explicit, tested, and observable.
- Existing learning routes remain backward compatible.
- PR-2 gates reproduce: **14 passed**, **187 passed**.

### PR-3
- Effort-routing telemetry remains continuous from decision -> API response -> metrics summary.
- Alert rules for high effort/cost/token patterns trigger correctly under test.
- No routing behavior regressions versus phase30 baseline.
- PR-3 gates reproduce: **38 passed**, **15 passed**, **187 passed**.

## Required tests / gates

Execute in strict sequence (`PR-1` -> `PR-2` -> `PR-3`) and stop on first gate failure.

### PR-1 gate
- `cd engine && python -m pytest tests/test_phase32_connector_boundary.py -q` → **11 passed**
- Connector regression group (session baseline) → **92 passed**
- Baseline targeted regression set → **187 passed**

### PR-2 gate
- `cd engine && python -m pytest tests/test_phase31_learning_signals.py -q` → **14 passed**
- Baseline targeted regression set → **187 passed**

### PR-3 gate
- `cd engine && python -m pytest tests/test_phase30_effort_routing.py tests/test_integration_wiring.py -q` → **38 passed**
- `cd engine && python -m pytest tests/test_phase30_effort_routing.py -q` → **15 passed**
- Baseline targeted regression set → **187 passed**

## Risks / rollback notes

- **PR-1 risk:** over-blocking from policy-pack changes can break connector paths unexpectedly.  
  **Rollback:** revert per-surface boundary adoption commits; keep existing MCP/web/search/http_request behavior unchanged; re-run 11/92/187 gates.

- **PR-2 risk:** migration or restore logic can produce silent data reset when payloads are invalid.  
  **Rollback:** switch backend to prior mode (`memory`/`file`) via settings, restore last known-good backup, re-run 14/187 gates.

- **PR-3 risk:** metric naming or label changes can break alert evaluation/dashboard expectations.  
  **Rollback:** preserve current metric keys (`effort_routing_*`) and revert exporter/alert wiring changes; re-run 38/15/187 gates.

- **Sequence risk:** merging out of order invalidates dependency assumptions between priorities 12–14.  
  **Rollback:** enforce merge order from `docs/review-packets/merge-sequencing.md` and hold downstream PRs until upstream gate counts are green.
