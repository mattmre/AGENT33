# Session 78 S8: Phase 25 SSE Hardening Scope

**Date:** 2026-03-12  
**Slice:** `S8 - Phase 25 SSE hardening + frontend test expansion`

## Baseline

The merged `S7` baseline already has:

- authenticated workflow SSE at `GET /v1/workflows/{run_id}/events`
- a shared workflow live snapshot manager for WS and SSE consumers
- a frontend `workflowLiveTransport` helper used by `OperationCard` and the improvement-cycle execution step

The remaining hardening gap is operational resilience, not first implementation:

- no client reconnect/backoff when the fetch stream drops
- no `Last-Event-ID` support, so reconnects can miss in-flight workflow events
- SSE frames do not expose stable event ids
- frontend live-transport tests only cover the happy-path single connection

## Included Work

1. Add bounded per-run replay state to the workflow live manager.
2. Extend the workflow SSE route to:
   - emit SSE `id:` frames
   - honor `Last-Event-ID`
   - replay buffered workflow events after reconnect
3. Harden the frontend SSE helper with:
   - exponential reconnect backoff
   - persisted last-seen event id across reconnects
   - no reconnect on terminal workflow completion/failure
   - no blind retry for clearly permanent auth/not-found failures
4. Expand frontend coverage for reconnect/resume behavior and a live workflow consumer path.

## Explicit Non-Goals

- restoring a WebSocket-first transport path
- changing graph-refresh semantics away from backend refetch
- broad workflow UI redesign
- unrelated Phase 38 streaming changes

## Acceptance

- reconnecting SSE clients can resume from the last delivered event id
- replay uses a bounded in-memory buffer per run
- terminal workflow events stop reconnect attempts
- auth/404 failures surface immediately instead of entering retry loops
- backend and frontend tests cover replay and reconnect behavior
