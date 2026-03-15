# S33: WS-first SSE Fallback Transport

**Session**: 89
**Slice**: S33
**Status**: Implemented
**Branch**: `feat/session89-s33-ws-sse`

## Objective

Add a transport negotiation layer that prefers WebSocket connections for
real-time workflow event streaming but falls back to SSE for clients that
cannot upgrade (proxies, browser restrictions, load balancers that strip
Upgrade headers).

## Architecture

### New module: `engine/src/agent33/workflows/transport.py`

- **TransportType** (StrEnum): WEBSOCKET, SSE, AUTO
- **TransportNegotiation** (Pydantic model): outcome of a negotiation handshake
- **TransportConfig** (Pydantic model): tuning knobs (ping interval, retry, reconnect)
- **WebSocketEventBridge**: per-run fan-out delivery bridge for WebSocket subscribers
- **WorkflowTransportManager**: unified transport manager with negotiation, handler
  factories, and stats tracking

### New route module: `engine/src/agent33/api/routes/workflow_transport.py`

- `GET /v1/workflows/transport/config` -- current transport configuration
- `GET /v1/workflows/transport/stats` -- live transport statistics
- `GET /v1/workflows/transport/negotiate` -- probe which transport the server
  would select for the current request

### Config additions: `engine/src/agent33/config.py`

- `workflow_transport_preferred` (auto | websocket | sse)
- `workflow_ws_ping_interval` (float, seconds)
- `workflow_ws_ping_timeout` (float, seconds)

### Lifespan wiring: `engine/src/agent33/main.py`

WorkflowTransportManager is instantiated immediately after WorkflowWSManager
in the lifespan, receiving the ws_manager reference and a TransportConfig
built from Settings.

## Integration

The transport layer is **additive**. It does not replace or modify the
existing `workflow_ws.py` or `workflow_sse.py` route handlers. Those
continue to function independently. The transport manager provides:

1. A negotiation API so clients can discover the recommended transport
   before connecting.
2. An independent WebSocketEventBridge for scenarios where the caller
   wants fan-out delivery without going through WorkflowWSManager.
3. Unified statistics that aggregate WS and SSE connection counts.

## Test coverage

`engine/tests/test_workflow_transport.py` covers:

- TransportType enum values
- TransportConfig defaults and validation
- TransportNegotiation model serialization
- negotiate() with Upgrade header -> WEBSOCKET
- negotiate() without Upgrade header -> SSE fallback
- negotiate() with preferred=SSE -> always SSE
- negotiate() with preferred=WEBSOCKET -> always WEBSOCKET
- WebSocketEventBridge subscribe/unsubscribe/count
- WebSocketEventBridge multiple subscribers per run
- WebSocketEventBridge broadcast delivery and isolation
- WebSocketEventBridge dead connection cleanup
- create_ws_handler() subscribe lifecycle and stats
- create_sse_handler() with/without ws_manager
- create_sse_handler() replay and stats
- Transport stats initial state and config reflection
- Config field defaults and validation
- API route tests for /config, /stats, /negotiate (with and without manager)
- Auth enforcement on all transport routes
