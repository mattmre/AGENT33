# Phase 35 Connector Boundary — Wave 2 (Messaging + Multimodal Async-Governance Follow-up)

## Context from Prior Next-Session Priorities

Session 43 left three immediate priorities:

1. Plan and sequence **Phase 35 Wave 2** connector-boundary adoption.
2. Inventory **multimodal synchronous governance** call sites and define an async convergence plan.
3. Preserve regression-gate continuity with explicit command groups.

This wave addresses (1) with implementation, completes multimodal convergence through Phase D, and keeps (3) as validation follow-through.

## Implemented Scope This Wave (Messaging Boundary Wrappers)

Wave 2 implementation added connector-boundary wrappers for messaging adapters so `send`, `health_check`, and receive-loop calls flow through centralized governance/error mapping:

- New helper:
  - `engine/src/agent33/messaging/boundary.py`
    - `execute_messaging_boundary_call(...)`
    - Uses `build_connector_boundary_executor(...)`
    - Normalizes failures with `map_connector_exception(...)`
- Messaging adapters now call the helper for both `send` and `health_check` operations:
  - `engine/src/agent33/messaging/slack.py`
  - `engine/src/agent33/messaging/discord.py`
  - `engine/src/agent33/messaging/telegram.py`
  - `engine/src/agent33/messaging/whatsapp.py`
  - `engine/src/agent33/messaging/signal.py`
  - `engine/src/agent33/messaging/matrix.py`
  - `engine/src/agent33/messaging/imessage.py`
- Coverage added:
  - `engine/tests/test_connector_boundary_messaging_adapters.py`
  - Verifies governance-denied connectors do not execute outbound HTTP calls for `send`, `health_check`, and receive-loop operations.

## Multimodal Async-Governance Convergence (Phase B/C Completed)

Phase B/C convergence is now implemented and validated:

- New helper:
  - `engine/src/agent33/multimodal/boundary.py`
    - `execute_multimodal_boundary_call(...)`
    - Uses `build_connector_boundary_executor(...)`
    - Normalizes failures with `map_connector_exception(...)`
- Multimodal adapters now expose an async execution contract routed through connector boundary middleware:
  - `engine/src/agent33/multimodal/adapters.py`
    - `STTAdapter.run_async(...)`
    - `TTSAdapter.run_async(...)`
    - `VisionAdapter.run_async(...)`
- Service + route async alignment implemented:
  - `engine/src/agent33/multimodal/service.py`
    - `execute_request(...)` is async and awaits `adapter.run_async(...)`
  - `engine/src/agent33/api/routes/multimodal.py`
    - create/execute endpoints await service execution path
- Coverage updated:
  - `engine/tests/test_connector_boundary_multimodal_adapters.py`
  - `engine/tests/test_multimodal_api.py`

## Connector Naming Contract (Messaging + Existing Multimodal)

Phase 35 naming remains connector-family explicit to support policy and telemetry targeting.

### Messaging (Wave 2)

- Connector format: `messaging:<platform>`
- Adopted connectors:
  - `messaging:slack`
  - `messaging:discord`
  - `messaging:telegram`
  - `messaging:whatsapp`
  - `messaging:signal`
  - `messaging:matrix`
  - `messaging:imessage`
- Standard operations in this wave:
  - `send`
  - `health_check`
  - `poll_updates` (telegram loop)
  - `sync_loop` (matrix loop)

### Existing Multimodal (Wave 1 baseline retained)

- Connector format: `multimodal:<modality>`
- Current connectors:
  - `multimodal:speech_to_text`
  - `multimodal:text_to_speech`
  - `multimodal:vision_analysis`
- Current operation:
  - `run`

## Multimodal Async-Governance Follow-up

### Call-site Inventory (Updated)

Legacy synchronous governance dependency is now retired from multimodal adapters, and both runtime entry paths route through the async boundary path:

- `engine/src/agent33/multimodal/adapters.py`
  - `STTAdapter.run_async(...)` / `TTSAdapter.run_async(...)` / `VisionAdapter.run_async(...)` route through `execute_multimodal_boundary_call(...)`
  - `run(...)` remains as a compatibility wrapper that delegates to `run_async(...)` outside active event loops

Route/service execution path is now async:

- `engine/src/agent33/api/routes/multimodal.py`
  - `create_request(...)` (when `execute_now=True`) awaits `_service.execute_request(...)`
  - `execute_request(...)` awaits `_service.execute_request(...)`
- `engine/src/agent33/multimodal/service.py`
  - `execute_request(...)` is async and awaits `adapter.run_async(...)`

### Phased Convergence Plan (Updated)

1. **Phase A — Complete (this wave): inventory + contract lock**
   - Call sites documented above.
   - Connector naming contract preserved; no runtime behavior changes to multimodal path.

2. **Phase B — Complete: async adapter boundary path**
   - Async multimodal adapter execution contract (`async run_async(...)`) is implemented.
   - Multimodal provider calls route through async connector boundary execution helper.

3. **Phase C — Complete: service + route async alignment**
   - Multimodal service execute path converted to async.
   - API routes updated to `await` service execution directly.

4. **Phase D — Complete: sync-governance retirement**
    - Removed multimodal dependency on legacy synchronous governance helper path in adapters.
    - Kept connector names unchanged (`multimodal:*`) and preserved boundary-based error normalization.

## Validation Plan and Commands

```bash
cd engine
python -m pytest tests/test_phase30_effort_routing.py tests/test_phase31_learning_signals.py tests/test_phase32_connector_boundary.py tests/test_tool_loop.py tests/test_invoke_iterative.py tests/test_skill_matching.py tests/test_context_manager.py -q
python -m pytest tests/test_connector_boundary_messaging_adapters.py tests/test_phase32_connector_boundary.py -q
python -m pytest tests/test_connector_boundary_multimodal_adapters.py tests/test_multimodal_api.py tests/test_phase32_connector_boundary.py -q
python -m pytest tests/test_connector_boundary_llm_memory.py tests/test_performance_fixes.py tests/test_phase32_connector_boundary.py -q
python -m pytest tests/test_chat.py tests/test_phase32_connector_boundary.py -q
```

- Validation evidence:
  - Phase30/31/32 + tool-loop/invoke-iterative/skill/context: **213 passed, 1 skipped**
  - Messaging boundary + phase32: **29 passed, 1 skipped**
  - Multimodal boundary + phase32: **40 passed, 1 skipped**
  - LLM/embeddings boundary + phase32: **40 passed, 1 skipped**
  - Chat boundary + phase32: **17 passed, 1 skipped**
  - Aggregate across batches: **339 passed, 5 skipped**
