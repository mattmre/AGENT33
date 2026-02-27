# Phase 35 Wave 2 (Part B): Multimodal Async-Governance Convergence

## Goal
Convert the multimodal adapters to utilize the new asynchronous `ConnectorExecutor` boundary while preserving existing connector naming (`multimodal:*`) and error-shape compatibility.

## Implementation Steps
1. **Refactored Adapters (`engine/src/agent33/multimodal/adapters.py`)**:
   - Changed `STTAdapter`, `TTSAdapter`, and `VisionAdapter` to implement `async def run(...)`.
   - Replaced the synchronous `enforce_connector_governance` call with `build_connector_boundary_executor` and `executor.execute()`.
   - Wrapped underlying HTTP API requests using `httpx.AsyncClient` into `_handler` coroutines.
   - Used `ConnectorRequest` with `connector="multimodal:..."` to preserve policy enforcement shapes.
   - Mapped errors via `map_connector_exception` for backwards compatibility.
2. **Updated Service Orchestration (`engine/src/agent33/multimodal/service.py`)**:
   - Updated `MultimodalService.execute_request` to `async def` and awaited the adapter.
3. **Updated API Routes (`engine/src/agent33/api/routes/multimodal.py`)**:
   - Modified `create_request` and `execute_request` endpoints to await `_service.execute_request(...)`.
4. **Updated Tests (`engine/tests/test_multimodal_api.py`)**:
   - Changed `test_service_policy_and_lifecycle_contracts` to be an async test method since it calls `_service.execute_request` directly.

## Outcomes
- All `multimodal:*` operations now successfully transit the async boundary and trigger metrics, circuit breakers, and governance blocks appropriately.
- The entire `engine` test suite (1904 tests) remains green.