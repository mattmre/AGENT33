# Session 57 Phase 25 SSE Fallback Design

**Date:** 2026-03-06  
**Scope:** Wave 1 PR2 for live workflow updates: authenticated SSE fallback, graph refresh fixes, and minimal frontend/backend wiring.

## Problem

The Wave 0 transport work provides a run-scoped workflow WebSocket contract, but the frontend still lacks a reliable live-update path. `WorkflowGraph.tsx` does not resync React Flow state when new graph data arrives, `OperationCard.tsx` does not wire any live refresh behavior, and the backend graph endpoint only overlays historical execution state rather than the current run snapshot. WebSocket also remains a poor fallback for API-key clients because browsers cannot send arbitrary headers during the handshake.

## Decisions

1. **Use WebSocket first, fetch-based SSE second.**
   - WebSocket remains the primary live transport for JWT-authenticated browser sessions.
   - SSE fallback uses authenticated `fetch`, so both Bearer tokens and API keys work without query-string secrets.
   - Native `EventSource` is intentionally excluded because it cannot attach the existing auth headers.

2. **Keep the backend graph API as the source of truth.**
   - Live transport events should trigger graph refetches rather than fully mutating graph state from event deltas in the browser.
   - This keeps node/edge/status derivation centralized on the backend and minimizes client-side drift.

3. **Add a run-scoped SSE endpoint that mirrors the WebSocket payload shape.**
   - Proposed route: `GET /v1/workflows/{run_id}/events`
   - Response type: `text/event-stream`
   - Event payloads should mirror the run-scoped workflow event contract from Wave 0 (`sync`, step events, terminal events, heartbeat).

4. **Extend graph reads with optional live-run overlay.**
   - `GET /v1/visualizations/workflows/{workflow_id}/graph` should accept `run_id`.
   - When `run_id` is present and a live snapshot exists, overlay step statuses from the current run before falling back to execution history.

5. **Limit the first pass to single-run live updates.**
   - Live wiring depends on caller-supplied `run_id` support from Wave 0.
   - Repeat/autonomous multi-run UX remains out of scope for this PR.

## Existing Patterns To Reuse

- Backend authenticated SSE precedent: `engine/src/agent33/api/routes/operations_hub.py`
- Frontend authenticated fetch-stream parsing precedent: `frontend/src/components/ObservationStream.tsx`
- Run-scoped workflow transport primitives: Wave 0 PR3 files under `engine/src/agent33/api/routes/workflow_ws.py`, `engine/src/agent33/workflows/events.py`, and `engine/src/agent33/workflows/ws_manager.py`

## Branch Strategy

This PR depends on both:

- PR #145 (`feat/session57-wave1-pr1-frontend-foundation`) for the jsdom/Testing Library frontend test foundation
- PR #148 (`feat/session57-wave0-pr3-workflow-ws-mcp`) for the run-scoped workflow live transport contract

To keep the Phase 25 PR diff reviewable, create a short-lived integration base branch that contains the heads of PR #145 and PR #148, then branch Wave 1 PR2 from that integration base. The PR itself should target the integration base branch until the dependencies merge.

## Planned File Touches

### Backend
- `engine/src/agent33/api/routes/workflow_sse.py` (new)
- `engine/src/agent33/api/routes/visualizations.py`
- `engine/src/agent33/main.py`
- `engine/src/agent33/workflows/ws_manager.py`
- `engine/tests/test_workflow_sse.py` (new)
- related visualization/workflow transport tests

### Frontend
- `frontend/src/components/WorkflowGraph.tsx`
- `frontend/src/components/OperationCard.tsx`
- `frontend/src/lib/workflowLiveTransport.ts` (new)
- `frontend/src/components/WorkflowGraph.test.tsx`
- live transport/component tests

## Test Plan

### Backend
- SSE auth success/failure for Bearer token and API key flows
- immediate `sync` event plus periodic heartbeat
- streamed step/terminal events for a registered run
- graph endpoint `run_id` overlay behavior

### Frontend
- `WorkflowGraph` rerender updates node/edge/selected-node state from new props
- live transport helper uses WebSocket first and falls back to SSE
- `OperationCard` refetches graph data on live transport events for single-run executions

## Risks

- branch skew while PR #145 and PR #148 are still open
- leaking WebSocket/SSE subscriptions on unmount
- over-refreshing on heartbeat events instead of only on graph-relevant events
- trying to reconstruct graph state from event deltas instead of refetching the canonical graph payload
