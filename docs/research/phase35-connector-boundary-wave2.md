# Phase 35 Connector Boundary — Wave 2 (Messaging + Multimodal Async-Governance Follow-up)

## Context from Prior Next-Session Priorities

Session 43 left three immediate priorities:

1. Plan and sequence **Phase 35 Wave 2** connector-boundary adoption.
2. Inventory **multimodal synchronous governance** call sites and define an async convergence plan.
3. Preserve regression-gate continuity with explicit command groups.

This wave addresses (1) with implementation and (2) with documented/deferred convergence planning, while keeping (3) as validation follow-through.

## Implemented Scope This Wave (Messaging Boundary Wrappers)

Wave 2 implementation added connector-boundary wrappers for messaging adapters so `send` and `health_check` calls flow through centralized governance/error mapping:

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
  - Verifies governance-denied connectors do not execute outbound HTTP calls for `send` and `health_check`.

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

### Existing Multimodal (Wave 1 baseline retained)

- Connector format: `multimodal:<modality>`
- Current connectors:
  - `multimodal:speech_to_text`
  - `multimodal:text_to_speech`
  - `multimodal:vision_analysis`
- Current operation:
  - `run`

## Multimodal Async-Governance Follow-up

### Call-site Inventory (Documented)

Current synchronous governance enforcement inside multimodal adapters:

- `engine/src/agent33/multimodal/adapters.py`
  - `STTAdapter.run(...)` → `enforce_connector_governance("multimodal:speech_to_text", "run", ...)`
  - `TTSAdapter.run(...)` → `enforce_connector_governance("multimodal:text_to_speech", "run", ...)`
  - `VisionAdapter.run(...)` → `enforce_connector_governance("multimodal:vision_analysis", "run", ...)`

Async entry points invoking sync execution path:

- `engine/src/agent33/api/routes/multimodal.py`
  - `create_request(...)` (when `execute_now=True`) calls `_service.execute_request(...)`
  - `execute_request(...)` calls `_service.execute_request(...)`
- `engine/src/agent33/multimodal/service.py`
  - `execute_request(...)` is sync and calls `adapter.run(...)`

### Phased Convergence Plan (Documented / Deferred)

1. **Phase A — Complete (this wave): inventory + contract lock**
   - Call sites documented above.
   - Connector naming contract preserved; no runtime behavior changes to multimodal path.

2. **Phase B — Deferred: async adapter boundary path**
   - Introduce async multimodal adapter execution contract (e.g., `async run_async(...)`).
   - Route multimodal provider calls through async connector boundary execution helper.

3. **Phase C — Deferred: service + route async alignment**
   - Convert multimodal service execute path to async.
   - Update API routes to `await` service execution directly.

4. **Phase D — Deferred: sync-governance retirement**
    - Remove multimodal dependency on synchronous governance helper once async path is fully adopted.
    - Keep exception mapping and connector names unchanged to maintain policy/telemetry continuity.

### Additional Deferred Messaging Scope

- Telegram polling (`getUpdates`) and Matrix sync (`/sync`) receive-loop HTTP calls remain outside boundary wrapping in this wave.
- Wave 2 intentionally scopes messaging boundary adoption to `send` and `health_check`; receive-loop governance wrapping is tracked for a later hardening pass.

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
  - Messaging boundary + phase32: **27 passed, 1 skipped**
  - Multimodal boundary + phase32: **33 passed, 1 skipped**
  - LLM/embeddings boundary + phase32: **40 passed, 1 skipped**
  - Chat boundary + phase32: **17 passed, 1 skipped**
  - Aggregate across batches: **330 passed, 5 skipped**
