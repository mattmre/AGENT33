# P2.5: WebSocket Streaming Backend Transport -- Scope Memo

**Session**: 104
**Slice**: P2.5
**Date**: 2026-03-24

## Current Agent Invocation Flow

Agent invocation is currently synchronous (request-response):

1. Client sends `POST /v1/agents/{name}/invoke` with JSON body (`inputs`, `model`, etc.)
2. `AgentRuntime.invoke()` constructs a system prompt, calls the LLM via `ModelRouter.complete()`, and returns `AgentResult`.
3. The route handler serializes the result as a single JSON response.

There is also an iterative SSE streaming endpoint at `POST /{name}/invoke-iterative/stream` that uses `StreamingResponse` with `text/event-stream`. This is HTTP-based SSE, not WebSocket.

For workflow status, a WebSocket endpoint already exists at `/v1/workflows/{run_id}/ws` backed by `WorkflowWSManager`. This streams workflow-level events (step started, completed, failed) but does not stream agent-level thinking/tool-call events.

## Proposed WebSocket Streaming Endpoint

### Endpoint

`GET /v1/stream/agent/{agent_id}` -- WebSocket upgrade

### Authentication

WebSocket handshake cannot always carry custom HTTP headers (browser limitation). The endpoint supports:

1. `Authorization: Bearer <jwt>` header (standard, works in non-browser clients)
2. `?token=<jwt>` query parameter (browser-compatible fallback)
3. `?api_key=<key>` query parameter (API key auth fallback)

Follows the same credential extraction pattern as `workflow_ws.py`: exactly one credential source must be provided; ambiguous multi-source requests are rejected. Required scope: `agents:invoke`.

### Message Protocol

After WebSocket connection is accepted, the client sends a single JSON message to initiate:

```json
{"input": "user query string", "context": {"key": "value"}}
```

The server then streams progress events back as JSON messages:

```json
{
  "event": "thinking" | "tool_call" | "response" | "error" | "done",
  "data": { ... },
  "seq": 1,
  "timestamp": "2026-03-24T12:00:00.000Z"
}
```

Event types:
- `thinking` -- LLM is processing (heartbeat / progress indicator)
- `tool_call` -- A tool invocation is happening (includes tool name and arguments)
- `response` -- Partial or final response text from the agent
- `error` -- An error occurred during processing
- `done` -- Processing complete; connection will be closed by server

### StreamingManager

A lightweight connection manager that:
- Tracks active WebSocket connections keyed by `session_id`
- Enforces `streaming_max_connections` limit (default 100)
- Provides `connect()`, `disconnect()`, and `broadcast()` methods
- Provides `active_count` property for observability

### Configuration

New settings in `config.py`:
- `streaming_max_connections: int = 100`
- `streaming_ping_interval_seconds: int = 30`

## Non-Goals

- **Frontend integration** -- That is P2.6, a separate slice.
- **Agent tool-loop integration** -- This slice provides the transport layer. Wiring `AgentRuntime.invoke_iterative_stream()` events through the WebSocket is out of scope; the endpoint currently emits synthetic thinking/response events to prove the transport works end-to-end.
- **Reconnection / resume protocol** -- No `Last-Event-ID` or replay buffer. The client must reconnect and re-submit if the connection drops.
- **Multi-agent fan-out** -- Each WebSocket connection is scoped to a single agent invocation.

## Files Changed

- `engine/src/agent33/api/routes/streaming.py` (new)
- `engine/src/agent33/config.py` (add 2 settings)
- `engine/src/agent33/main.py` (import + include router)
- `engine/tests/test_streaming_backend.py` (new)
- `docs/research/session104-p25-ws-streaming-scope.md` (this file)
