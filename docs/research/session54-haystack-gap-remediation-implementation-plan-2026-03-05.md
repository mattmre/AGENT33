# Session 54 Architecture — Haystack Gap Remediation Implementation Plan (2026-03-05)

This plan translates the Haystack deep-dive findings into a concrete, five-phase execution program for AGENT-33.

## Objectives

1. Close production-readiness gaps in MCP and workflow route durability.
2. Improve composition maturity (routing, retrieval, HITL policy, tool invocation).
3. Add reusable workflow component contracts and evaluator parity without breaking existing APIs.

## Delivery model

- Small, reviewable PR slices with feature flags.
- Backward-compatible API behavior by default.
- Ruff + mypy + targeted pytest gates on every slice.

## Phase 1 — Workflow durability foundation

### Scope
- Replace route-level in-memory workflow registry/history with durable state-backed service.
- Keep route contracts stable while making restart behavior deterministic.

### Primary touchpoints
- `engine/src/agent33/api/routes/workflows.py`
- `engine/src/agent33/services/orchestration_state.py`
- `engine/src/agent33/main.py`
- new `engine/src/agent33/services/workflow_route_state.py`

### API/data notes
- Preserve existing workflow endpoints and payloads.
- Persist namespace for:
  - `registry`
  - `execution_history`
  - `scheduled_jobs`
  - `schema_version`

### Flags
- `workflow_route_durability_enabled` (default: `true`)

### Tests
- New persistence round-trip and restart recovery tests.
- Existing workflow API and scheduling tests must remain green.

## Phase 2 — MCP production hardening

### Scope
- Replace placeholder MCP transport behavior with bounded session lifecycle and strict request validation.

### Primary touchpoints
- `engine/src/agent33/api/routes/mcp.py`
- `engine/src/agent33/main.py`
- `engine/src/agent33/config.py`
- new `engine/src/agent33/services/mcp_gateway.py`

### API notes
- Keep:
  - `GET /v1/mcp/sse`
  - `POST /v1/mcp/messages`
- Add:
  - `GET /v1/mcp/status`
- Enforce JSON-RPC payload validation and content type checks.

### Flags
- `mcp_server_enabled`
- `mcp_server_max_sessions`
- `mcp_server_session_ttl_seconds`

### Tests
- Route tests for schema/content-type enforcement.
- Session lifecycle tests (TTL, max sessions, reject paths).
- Missing dependency path returns explicit non-success status.

## Phase 3 — Router pack v1 + trace enrichment baseline

### Scope
- Standardize router registration.
- Add request/correlation metadata enrichment for traceability.

### Primary touchpoints
- `engine/src/agent33/main.py`
- `engine/src/agent33/api/routes/traces.py`
- new `engine/src/agent33/api/router_pack.py`
- new `engine/src/agent33/observability/request_context.py`

### API notes
- No endpoint removals.
- Add `X-Request-Id` header for request correlation.
- Keep existing route prefixes/tags unchanged.

### Flags
- `api_router_pack_v1_enabled`
- `request_tracing_enrichment_enabled`

### Tests
- Router inclusion integrity test (no duplicate includes).
- Request-id propagation and trace metadata assertions.

## Phase 4 — Modular composition layer

### Scope
- Introduce typed retrieval stage interfaces.
- Add HITL strategy adapters over current approval lifecycle.
- Standardize tool invocation path through a shared invoker.

### Primary touchpoints
- `engine/src/agent33/memory/rag.py`
- `engine/src/agent33/agents/tool_loop.py`
- `engine/src/agent33/agents/runtime.py`
- `engine/src/agent33/tools/governance.py`
- new `engine/src/agent33/retrieval/interfaces.py`
- new `engine/src/agent33/retrieval/stages.py`
- new `engine/src/agent33/tools/hitl_strategy.py`
- new `engine/src/agent33/tools/invoker.py`

### API notes
- Keep current route contracts and `RAGPipeline` call signatures stable.
- Internal contracts become explicit/typed for stage composition.

### Flags
- `retrieval_stage_interface_v1_enabled`
- `hitl_strategy_adapters_enabled`
- `tool_invoker_standardization_enabled`

### Tests
- Stage contract tests for retriever/joiner/ranker flow.
- HITL strategy matrix tests (`allow`/`ask`/`deny`).
- Tool invoker parity tests against existing tool-loop behavior.

## Phase 5 — Super-components + typed contracts + evaluator parity

### Scope
- Add reusable workflow super-components with typed input/output contracts.
- Align evaluator/training scoring contracts for consistent quality loops.

### Primary touchpoints
- `engine/src/agent33/workflows/definition.py`
- `engine/src/agent33/workflows/executor.py`
- `engine/src/agent33/evaluation/service.py`
- `engine/src/agent33/training/evaluator.py`
- `engine/src/agent33/api/routes/evaluations.py`
- new `engine/src/agent33/workflows/components/contracts.py`
- new `engine/src/agent33/workflows/components/registry.py`
- new `engine/src/agent33/workflows/components/builtin.py`
- new `engine/src/agent33/evaluation/contracts.py`

### API notes
- Additive only: legacy action-based workflow steps remain valid.
- Optional evaluator parity endpoint can be added without altering existing endpoints.

### Flags
- `workflow_super_components_v1_enabled`
- `workflow_typed_contracts_enforced` (warn-only rollout first)
- `evaluation_contract_parity_enabled`

### Tests
- Mixed workflow execution tests (legacy + component steps).
- Contract validation tests.
- Evaluator parity tests for consistent score semantics.

## PR slicing strategy

1. `phase1-workflow-durability-foundation`
2. `phase2-mcp-hardening`
3. `phase3-router-pack-trace-enrichment`
4. `phase4-modular-composition`
5. `phase5-supercomponents-contract-parity`

Each phase should be split into 2-4 PRs if needed to keep diffs reviewable and risk-contained.

## Quality gates per phase

- `python -m ruff check src tests`
- `python -m ruff format --check src tests`
- `python -m mypy src --config-file pyproject.toml` (or targeted modules when baseline unrelated issues are unchanged)
- `python -m pytest tests/ -q` (targeted suite for touched surfaces; full suite before final merge wave)

