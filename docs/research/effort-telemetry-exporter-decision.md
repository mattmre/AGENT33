# Effort Telemetry Exporter Decision

## Decision Summary

Operational follow-through decision: **a durable exporter is required** for effort-routing telemetry beyond in-memory dashboard metrics.

Decision constraints:

- **Opt-in activation**: exporter remains disabled by default unless explicitly enabled.
- **Fail-open default**: exporter failures must not block runtime request handling.
- **Durability target**: telemetry should survive process restarts and support later analysis/replay.

## Implementation Scope (PR-4)

PR-4 implements the telemetry-exporter track for effort-routing events, including:

1. Export path from runtime effort telemetry emission into a durable sink.
2. Append-only JSONL file exporter with parent-directory creation.
3. Non-blocking error handling with fail-open default and optional fail-closed mode.
4. Focused test coverage for exporter behavior and existing phase30 routing compatibility.

## Configuration Keys

PR-4 introduces exporter-specific configuration for enablement, destination, and failure behavior:

- `observability_effort_export_enabled` / `OBSERVABILITY_EFFORT_EXPORT_ENABLED` (bool, opt-in gate)
- `observability_effort_export_path` / `OBSERVABILITY_EFFORT_EXPORT_PATH` (string sink path)
- `observability_effort_export_fail_closed` / `OBSERVABILITY_EFFORT_EXPORT_FAIL_CLOSED` (bool, default `false`)

## Branch / PR References

- PR-4 implementation branch: `feat/phase33-effort-telemetry-exporter`
- Review PR: **PR #70**

This document records the decision outcome and references the implementation now available for review.
