# Phase 27/29/30 Stage 1 Backend Architecture

Date: 2026-02-18  
Scope: Stage 1 backend only (no frontend implementation in this slice)

## Goals

1. **Phase 27**: Ship operations-hub aggregation and lifecycle controls.
2. **Phase 29**: Ship multimodal backend contracts (models + adapter interfaces + guarded API scaffolding).
3. **Phase 30**: Ship outcome event/trend backend contracts and baseline dashboard API.

## In Scope / Out of Scope

### In Scope
- Pydantic models + StrEnum state contracts
- In-memory services following current phase patterns
- FastAPI routes with scope enforcement and tenant filtering
- Backend tests for behavior, auth, and lifecycle transitions

### Out of Scope
- Frontend pages/components
- External provider integration for STT/TTS/vision (contract-first mocks only)
- Persistent DB schema changes (Stage 1 remains in-memory)
- Expanded strategic-loop features beyond requested outcome event/trend slice

## Shared Architecture Decisions

1. **Reuse existing route/service patterns** from `traces`, `autonomy`, `improvements`, and `component_security`.
2. **Use route-local singleton services** with test reset fixtures.
3. **Use `require_scope(...)` dependencies** for all new endpoints.
4. **Use tenant extraction from `request.state.user.tenant_id`** and enforce tenant-safe access in services.
5. **Use deterministic lifecycle maps** instead of implicit state mutation.

## Phase 27 Design (Operations Hub Stage 1)

### Files
- `engine/src/agent33/operations/models.py`
- `engine/src/agent33/services/operations_hub.py`
- `engine/src/agent33/api/routes/operations_hub.py`
- `engine/tests/test_operations_hub_api.py`

### API Contracts
- `GET /v1/operations/hub`  
  Aggregates traces, autonomy budgets, analyzing improvements, and recent workflow executions.
- `GET /v1/operations/processes/{process_id}`  
  Returns unified detail for a normalized process entry.
- `POST /v1/operations/processes/{process_id}/control`  
  Lifecycle actions (`pause`, `resume`, `cancel`) mapped to underlying subsystem actions.

### Guardrails
- Read endpoints require read scope.
- Control endpoint requires write/execute scope.
- Tenant filtering is applied before returning process entries.

## Phase 29 Design (Multimodal Stage 1)

### Files
- `engine/src/agent33/multimodal/models.py`
- `engine/src/agent33/multimodal/adapters.py`
- `engine/src/agent33/multimodal/service.py`
- `engine/src/agent33/api/routes/multimodal.py`
- `engine/tests/test_multimodal_api.py`

### API Contracts
- `POST /v1/multimodal/requests`
- `GET /v1/multimodal/requests`
- `GET /v1/multimodal/requests/{request_id}`
- `POST /v1/multimodal/requests/{request_id}/execute`
- `GET /v1/multimodal/requests/{request_id}/result`
- `POST /v1/multimodal/requests/{request_id}/cancel`

### Guardrails
- Policy validation (supported modality, max text/file constraints placeholder, timeout constraints).
- Tenant-safe ownership checks on get/list/execute/cancel.
- Status transitions enforced (`pending -> processing -> completed/failed/cancelled`).

## Phase 30 Design (Outcomes Stage 1)

### Files
- `engine/src/agent33/outcomes/models.py`
- `engine/src/agent33/outcomes/service.py`
- `engine/src/agent33/api/routes/outcomes.py`
- `engine/tests/test_outcomes_api.py`

### API Contracts
- `POST /v1/outcomes/events` (record outcome event)
- `GET /v1/outcomes/events` (filtered listing)
- `GET /v1/outcomes/trends/{metric_type}` (trend window contract)
- `GET /v1/outcomes/dashboard` (baseline trend dashboard contract)

### Guardrails
- Tenant-filtered event access.
- Explicit metric/event enums for stable contracts.
- Deterministic trend-direction output (`improving`, `stable`, `declining`).

## Testing Strategy

For each phase module:
- Model tests for defaults and enum contracts
- Service tests for lifecycle and tenant boundaries
- API tests for auth, success paths, and error paths

Validation commands:

```bash
cd engine
python -m ruff check src tests
python -m pytest tests/test_operations_hub_api.py -q
python -m pytest tests/test_multimodal_api.py -q
python -m pytest tests/test_outcomes_api.py -q
python -m pytest tests -q
```

## Implementation Order

1. Phase 27 backend slice (operations hub + tests)
2. Phase 29 backend contracts (multimodal + tests)
3. Phase 30 outcome slice (outcomes + tests)
4. Docs/progress/session logging + full validation + PR split preparation
