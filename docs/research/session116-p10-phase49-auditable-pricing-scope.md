# Session 116 -- P10 / Cluster A3: Auditable Pricing Residual Scope

**Date**: 2026-03-29
**Branch**: `codex/session116-p10-a3-phase49`
**Base**: `origin/main`

## Current Mainline Reality

Phase 49 core mechanics are already present on `main`:

- `engine/src/agent33/llm/pricing.py` ships the per-model pricing catalog with
  `source`, `source_url`, and `fetched_at` metadata.
- `engine/src/agent33/agents/effort.py` ships the simple-message fast path and
  catalog-backed cost estimation.
- `engine/src/agent33/agents/runtime.py` already derives provider context and
  passes it into the effort router.
- `engine/src/agent33/api/routes/agents.py` already wires the live heuristic
  settings into the shared `AgentEffortRouter`.

The older Phase 49 research note that called out missing route/runtime wiring is
stale against the current codebase.

## Real Residual

The roadmap requirement for "auditable per-model pricing" is still not fully
closed at the operator-contract level.

- The pricing catalog provenance exists only inside Python objects.
- No stable MCP resource or operator runbook exposes the effective catalog with
  source attribution and live heuristic thresholds.
- Current operator-facing docs cover SLOs and connector policy, but not how to
  inspect or verify the Phase 49 economics baseline.

## Bounded Slice

Implement the smallest auditable closure:

1. Add a read-only MCP resource for the effective pricing catalog and live
   effort-routing heuristic settings.
2. Document the verification workflow in operator docs.
3. Add regression coverage for the resource contract, auth mapping, and docs.

## Explicit Non-Goals

- No dynamic pricing refresh from provider APIs.
- No billing or chargeback UI.
- No changes to routing heuristics themselves unless required for the inspection
  contract.
