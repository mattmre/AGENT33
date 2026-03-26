# P4.16: WebSocket Streaming Load Testing -- Scope

**Session:** 109
**Slice:** P4.16
**Branch:** `feat/p416-ws-load-testing`
**Status:** In progress

## Included Work

1. **`engine/tests/test_websocket_load.py`** -- pytest-based load test harness
   - Concurrent WebSocket connection tests at 10, 50, 100 connection levels
   - Message throughput measurement per connection
   - Connection stability over sustained duration
   - Graceful disconnect handling under concurrent load
   - All tests marked `@pytest.mark.integration` (no real server in CI)

2. **`scripts/ws-load-profile.py`** -- Standalone load profile script
   - Executable outside pytest for ad-hoc load profiling
   - Configurable concurrency levels, message counts, and target URL
   - Reports connection success rate, message latency percentiles, throughput

3. **This scope document**

## Explicit Non-Goals

- No Locust-based WebSocket load testing (Locust's WebSocket support requires
  gevent patches that conflict with pytest; the existing `load-tests/locustfile.py`
  covers HTTP load testing)
- No changes to the production WebSocket endpoint code
- No infrastructure provisioning (CI pipelines, Docker Compose profiles, etc.)
- No SSE load testing (SSE is a different transport covered by separate work)

## Implementation Notes

### Existing Infrastructure

- Two WebSocket endpoints exist:
  - `/v1/stream/agent/{agent_id}` -- agent invocation streaming (P2.5)
  - `/v1/workflows/{run_id}/ws` -- workflow run-scoped event streaming
- `StreamingManager` tracks connections with configurable `max_connections`
- `WorkflowWSManager` handles workflow WS subscriptions and snapshots
- `websockets>=13,<17` is a core dependency; `locust>=2.29,<3` is dev-only
- The `streaming_client.py` module provides a Python client for the streaming endpoint

### Test Strategy

The load tests use Starlette's `TestClient` WebSocket support to test against
the actual FastAPI application in-process. This exercises the real endpoint
handler code (authentication, message validation, event streaming, connection
management) without requiring a running server.

For the standalone script, the `websockets` library is used directly against
a live server endpoint.

### Concurrency Approach

Since `TestClient.websocket_connect()` is synchronous, concurrency tests for
the `StreamingManager` use direct async calls with `asyncio.gather()` to
simulate parallel connection pressure. The integration tests verify that the
manager correctly handles concurrent connect/disconnect/broadcast under load.

## Validation Plan

1. `python -m pytest tests/test_websocket_load.py -v -m integration` -- all tests pass
2. `python -m ruff check engine/tests/test_websocket_load.py scripts/ws-load-profile.py`
3. `python -m ruff format --check engine/tests/test_websocket_load.py scripts/ws-load-profile.py`
4. `python -m mypy engine/tests/test_websocket_load.py scripts/ws-load-profile.py` (if applicable)
5. `python scripts/ws-load-profile.py --help` -- script is importable and shows usage
