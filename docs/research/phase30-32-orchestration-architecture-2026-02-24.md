# Phase 30–32 Orchestration Architecture Blueprint (2026-02-24)

## Scope

This document defines an implementation blueprint for:

1. **Phase 30 hardening** (post-MVP effort routing)
2. **Phase 31 persistence + signal quality** (post-MVP learning signals)
3. **Phase 32 kickoff** (middleware-chain + connector governance + circuit-breaker primitives)

It is grounded in:

- `docs/next-session.md` (priorities for follow-on work)
- `docs/research/phase29_3-31-mvp-implementation-summary-2026-02-24.md`
- Current backend structure under `engine/src/agent33/`

---

## Current State

### Phase 30 (Effort Routing MVP)

- Implemented in:
  - `engine/src/agent33/agents/effort.py`
  - `engine/src/agent33/agents/runtime.py`
  - `engine/src/agent33/api/routes/agents.py`
  - `engine/src/agent33/config.py`
- Behavior:
  - Supports `low|medium|high` effort.
  - Resolves model and token multiplier from static settings.
  - Works for both `invoke()` and `invoke_iterative()`.
- Limit:
  - Routing is static; no automatic classifier, tenant policy, or explicit cost telemetry.

### Phase 31 (Learning Signals MVP)

- Implemented in:
  - `engine/src/agent33/improvement/models.py`
  - `engine/src/agent33/improvement/service.py`
  - `engine/src/agent33/api/routes/improvements.py`
  - `engine/src/agent33/config.py`
- Behavior:
  - Feature-gated signal ingest/list/summary endpoints.
  - In-memory signal store with severity/type filtering.
  - Optional auto-intake generation with idempotency map.
- Limit:
  - Signals/intakes are in-memory only.
  - No enrichment/scoring pipeline.
  - Summary does not provide time-window trend analytics or tenant scoping.

### Phase 32 readiness baseline

- Existing pieces that can be reused:
  - API middleware pattern in `engine/src/agent33/main.py` and `engine/src/agent33/security/middleware.py`
  - Tool governance in `engine/src/agent33/tools/governance.py`
  - Connector entry points in `engine/src/agent33/tools/mcp_bridge.py`, `engine/src/agent33/tools/mcp_client.py`, and `engine/src/agent33/api/routes/mcp.py`
- Missing:
  - Generic connector middleware chain abstraction.
  - Circuit breaker primitive for outbound connector/tool boundaries.
  - Unified connector governance contract and instrumentation.

---

## Gaps (done / partial / missing)

| Area | Done | Partial | Missing |
|---|---|---|---|
| Phase 30 effort routing | Enum/router + runtime integration + API input | Single global static policy | Heuristic classifier, tenant/domain policy layer, cost-aware decision telemetry |
| Phase 31 learning | Feature-gated endpoints + summary + idempotent intake mapping | Signal filtering and threshold-based intake generation | Durable persistence, tenant-scoped analytics, enrichment/scoring pipeline, trend windows |
| Phase 32 orchestration | Existing middleware/tool governance primitives and MCP integration points | Connector behavior spread across modules without shared lifecycle model | Middleware chain framework, connector governance registry, circuit breaker + boundary health model |

---

## Proposed Design by PR Slice

## PR-1 — Phase 30 hardening (effort classifier + policy + telemetry)

### Design goals

- Keep current API contract backward-compatible.
- Add automatic effort selection when client does not explicitly pass `effort`.
- Support tenant/domain routing policies without hardcoding logic in routes.
- Emit cost-aware telemetry for every routing decision.

### Proposed architecture

1. **Effort classifier module**
   - Add `engine/src/agent33/agents/effort_classifier.py`.
   - Input: invocation context (agent name, domain, input size/shape, iterative mode, tool-loop settings).
   - Output: predicted effort + confidence + reasons.
   - Start rule-based (deterministic), leave interface ready for model-based classifier.

2. **Policy layer**
   - Add `engine/src/agent33/agents/effort_policy.py`.
   - Merge sources in order:
     1) request explicit effort
     2) tenant/domain policy override
     3) classifier output
     4) default setting
   - Support per-tenant/per-domain keys (initially config-backed, with later DB-backed provider).

3. **Cost telemetry**
   - Extend routing decision metadata with:
     - selected effort source (`request|policy|classifier|default`)
     - token multiplier applied
     - estimated token budget
     - optional model-cost estimate (if pricing table configured)
   - Attach to structured logs/trace events (do not break existing response contract in first slice).

4. **Wiring updates**
   - Initialize shared effort components in app lifespan (app state) in `engine/src/agent33/main.py`.
   - Remove hidden divergence between module singleton and app-state path in routes.

---

## PR-2 — Phase 31 persistence + signal quality

### Design goals

- Persist learning signals and generated intake mappings.
- Improve automated intake quality using a deterministic scoring pipeline.
- Add summary windows and tenant-scoped analytics.

### Proposed architecture

1. **Persistent store**
   - Add `engine/src/agent33/improvement/store.py` (SQLAlchemy async, aligned with `training/store.py` style).
   - Initial tables:
     - `improvement_learning_signals`
     - `improvement_learning_signal_intake_links`
   - Columns include tenant_id, signal fingerprint/hash, severity/type, source, timestamps, enrichment fields.

2. **Service split**
   - Keep `ImprovementService` as orchestration layer.
   - Introduce repository interface (`in-memory` + `postgres` implementations).
   - Route singleton keeps same behavior when persistence disabled (safe fallback).

3. **Signal quality pipeline**
   - Add `engine/src/agent33/improvement/learning_pipeline.py`.
   - Steps:
     1) normalization (canonical source/type mapping)
     2) dedupe fingerprint generation
     3) quality score computation (`severity`, `signal_type`, `source_reliability`, `recency`, repetition)
     4) recommended intake priority output
   - Intake generation uses score threshold + severity threshold (not severity threshold alone).

4. **API extension**
   - Extend `GET /v1/improvements/learning/summary` with optional:
     - `window_days`
     - `group_by` (`day|week|severity|type`)
   - Enforce tenant context from authenticated user for list/summary persistence queries.

---

## PR-3 — Phase 32 kickoff (middleware-chain + connector governance base)

### Design goals

- Introduce a shared boundary execution model for external connectors/tools.
- Provide first-class reliability controls (timeouts, retries, circuit breaker).
- Enable policy and observability consistency across MCP and future connectors.

### Proposed architecture

1. **Connector middleware chain**
   - Add package `engine/src/agent33/connectors/`:
     - `models.py` (`ConnectorRequest`, `ConnectorResponse`, `ConnectorContext`)
     - `middleware.py` (chain protocol + composition helper)
     - `executor.py` (single execution entrypoint)
   - Initial middleware set:
     - timeout budget guard
     - retry policy (bounded, idempotent-safe)
     - circuit breaker check/open/half-open transition
     - audit/metrics emission

2. **Circuit breaker primitive**
   - Add `engine/src/agent33/connectors/circuit_breaker.py`.
   - Key behavior:
     - rolling failure counter per connector key
     - open state with cooldown
     - half-open probe path
     - explicit failure taxonomy (transport, timeout, 5xx, policy denied)

3. **Connector governance base**
   - Add `engine/src/agent33/connectors/governance.py`.
   - Map connector IDs to policies (allowed tenants/domains, rate caps, timeout profiles).
   - Integrate with existing `tools/governance.py` rather than replacing it.

4. **Kickoff integration targets**
   - Wrap `MCPServerConnection._rpc()` in `tools/mcp_bridge.py` with connector executor.
   - Keep `api/routes/mcp.py` interface stable; improve reliability internally first.

---

## File-level Impact

### PR-1 (Phase 30 hardening)

- **Add**
  - `engine/src/agent33/agents/effort_classifier.py`
  - `engine/src/agent33/agents/effort_policy.py`
- **Modify**
  - `engine/src/agent33/agents/effort.py` (decision metadata expansion)
  - `engine/src/agent33/agents/runtime.py` (policy/classifier integration)
  - `engine/src/agent33/api/routes/agents.py` (context plumbing, no breaking API)
  - `engine/src/agent33/main.py` (shared component lifecycle wiring)
  - `engine/src/agent33/config.py` (classifier/policy/telemetry flags)
  - `engine/tests/test_phase30_effort_routing.py` (+ new policy/classifier tests)

### PR-2 (Phase 31 persistence + quality)

- **Add**
  - `engine/src/agent33/improvement/store.py`
  - `engine/src/agent33/improvement/learning_pipeline.py`
  - `engine/tests/test_improvement_learning_store.py`
- **Modify**
  - `engine/src/agent33/improvement/service.py` (repository + pipeline orchestration)
  - `engine/src/agent33/api/routes/improvements.py` (tenant-aware query + windowed summary)
  - `engine/src/agent33/improvement/models.py` (enrichment/score fields where needed)
  - `engine/src/agent33/main.py` (optional store init + shutdown)
  - `engine/src/agent33/config.py` (persistence + scoring config)
  - `engine/tests/test_phase31_learning_signals.py` (persistence + scoring + window tests)

### PR-3 (Phase 32 kickoff)

- **Add**
  - `engine/src/agent33/connectors/models.py`
  - `engine/src/agent33/connectors/middleware.py`
  - `engine/src/agent33/connectors/executor.py`
  - `engine/src/agent33/connectors/circuit_breaker.py`
  - `engine/src/agent33/connectors/governance.py`
  - `engine/tests/test_connector_middleware.py`
  - `engine/tests/test_circuit_breaker.py`
- **Modify**
  - `engine/src/agent33/tools/mcp_bridge.py` (execute RPC through connector chain)
  - `engine/src/agent33/tools/mcp_client.py` (align retry/error handling taxonomy)
  - `engine/src/agent33/main.py` (connector registry/governance lifecycle)
  - `engine/src/agent33/api/routes/mcp.py` (optional status exposure only; no contract break)

---

## Test Strategy

1. **PR-1**
   - Unit: classifier deterministic cases, policy precedence, routing telemetry fields.
   - Integration: invoke and invoke-iterative pass expected routed model/max_tokens under tenant/domain contexts.

2. **PR-2**
   - Unit: store CRUD + dedupe + tenant isolation.
   - Service: quality score behavior, intake generation thresholds, idempotency with persistence.
   - API: feature flag off/on, windowed summary output, tenant-scoped filtering.

3. **PR-3**
   - Unit: middleware ordering, timeout/retry behavior, circuit state transitions.
   - Integration: MCP connector failure/open-circuit behavior and recovery.
   - Regression: re-run Phase 30/31 suites to verify no behavioral drift.

Recommended command set (aligned to existing suites):

```bash
cd engine
python -m pytest tests/test_phase30_effort_routing.py -q
python -m pytest tests/test_phase31_learning_signals.py -q
python -m pytest tests/test_improvement_learning_store.py -q
python -m pytest tests/test_connector_middleware.py tests/test_circuit_breaker.py -q
python -m pytest tests/test_reasoning.py tests/test_stuck_detector.py tests/test_chat.py tests/test_health.py -q
```

---

## Risks and Mitigations

- **Risk: policy complexity causes non-deterministic routing**
  - Mitigation: explicit precedence contract + structured decision reason in logs.
- **Risk: persistence rollout breaks current in-memory assumptions**
  - Mitigation: dual-mode repository (in-memory fallback), migration-safe feature flag.
- **Risk: circuit breaker over-trips in noisy environments**
  - Mitigation: conservative defaults, per-connector tuning, half-open probe logic.
- **Risk: cross-tenant data leakage in Phase 31 persistence**
  - Mitigation: mandatory tenant_id index/filter at repository boundary + API tests.
- **Risk: connector chain introduces latency**
  - Mitigation: lightweight middleware, measurable per-stage timing, budget-based timeouts.

---

## Rollout Notes

1. **Release as three PR slices** (PR-1, PR-2, PR-3) with feature flags default-off for new behavior.
2. **Deploy order**
   - Merge PR-1 first (safe hardening, no schema).
   - Merge PR-2 second (introduces persistence and data model).
   - Merge PR-3 third (connector boundary reliability framework).
3. **Operational checks after each slice**
   - Validate route health and smoke tests.
   - Validate telemetry logs for routing decisions and connector events.
   - Confirm fallback behavior when new flags are disabled.
4. **Documentation follow-up**
   - Update `docs/next-session.md` after each merged slice.
   - Add phase progress log entries (Phase 30 hardening, Phase 31 persistence, Phase 32 kickoff).

