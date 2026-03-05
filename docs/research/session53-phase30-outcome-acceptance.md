# Session 53: Phase 30 Outcome-Focused Routing Acceptance Matrix

Date: 2026-03-04
Scope: Priority 3 from `docs/next-session.md` (Phase 30 verification)

## Problem

Phase 30 has unit coverage for individual router behaviors, but we need acceptance-style checks that verify routing outcomes across realistic request shapes. The goal is to catch regressions where the classifier/policy precedence still "works" in isolated tests but drifts on end-to-end routing decisions.

## Existing baseline reviewed

- `engine/src/agent33/agents/effort.py`
- `engine/src/agent33/agents/runtime.py`
- `engine/tests/test_phase30_effort_routing.py`
- `docs/phases/PHASE-29-33-WORKFLOW-PLAN.md` (Phase 30 correctness gate)

## Acceptance strategy

Add a deterministic matrix test suite that validates:

1. Explicit effort requests produce request-sourced routing.
2. Tenant/domain policy matches override heuristics.
3. Heuristic classification maps canonical request profiles to expected effort bands.
4. Iterative mode metadata remains consistent with routed token budgets and selected model.

The tests focus on output routing decisions (`effort`, `effort_source`, model, token budget, and heuristic context) rather than only internal helper behavior.

## Non-goals

- No API contract changes.
- No heuristic logic changes in this slice.
- No cost model tuning in this slice.

## Expected effect

This creates a regression safety net that enforces Phase 30's correctness gate with realistic routing outcomes while preserving current runtime behavior.
