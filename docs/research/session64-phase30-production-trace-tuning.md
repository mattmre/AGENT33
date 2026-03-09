# Session 64: Phase 30 Production Trace Tuning

**Date:** 2026-03-09
**Scope:** Phase 30 operational hardening for effort-routing telemetry and trace correlation.

## Problem

Phase 30's effort router already exposes deterministic routing decisions, cost estimates,
and calibration metadata, but the exported telemetry remained too sparse for production
tuning:

- non-streaming API routes exported only `{timestamp, routing}`
- streaming agent execution did not export routing telemetry at all
- routing records lacked stable invocation-level correlation fields
- completion-only facts such as final token usage and termination reason were not carried
  into the exported payload

That made it difficult to compare standard, iterative, and streaming executions or join
effort-routing exports back to session-level operational traces.

## Design

Keep the existing routing contract and metrics intact, but enrich the routing metadata with
stable, low-risk correlation fields:

- `invocation_id`
- `invocation_mode`
- `session_id`
- `agent_name`
- `requested_model`
- `default_model`
- `input_field_count`
- `input_char_count`
- `requested_max_iterations`
- `actual_model`
- `tokens_used`
- `iterations`
- `tool_calls_made`
- `tools_used`
- `termination_reason`
- `completion_status`

The API routes now pass the runtime session identifier through from
`x-agent-session-id`, `x-session-id`, or `request.state.session_id`.

## Streaming Alignment

The streaming path now matches the non-streaming paths operationally:

1. the stream route passes tenant/domain/session context into `AgentRuntime`
2. `AgentRuntime.invoke_iterative_stream()` updates routing metadata from the terminal
   `completed` event
3. the API route exports routing telemetry immediately before yielding the terminal
   `completed` event

If telemetry is configured as fail-closed and export fails on the stream route, the route
emits a terminal SSE `error` payload rather than silently claiming success.

## Non-Goals

- No new dashboard metrics were added in this slice
- No trace collector schema changes were introduced
- No heuristic tuning logic changed; this is observability hardening only

## Acceptance

- standard invoke responses include enriched routing metadata
- iterative invoke telemetry includes completion stats
- iterative streaming exports routing telemetry on completion
- session/domain context is preserved consistently across invoke modes
- targeted Phase 30 regression tests cover the new metadata and stream export path
