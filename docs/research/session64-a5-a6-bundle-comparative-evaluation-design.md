# Session 64: A5/A6 Bundle Comparative Evaluation Design

Date: 2026-03-09
Scope: Current `main` priority 1 from `docs/next-session.md`

## Problem

AGENT-33 has both halves of the A5/A6 story, but they stop short of each other:

- A5 synthetic environment bundles are persisted and can survive service restart.
- A6 comparative scoring can rank agents, but it has no contract for validating or evaluating scores against persisted synthetic bundles.

Without bundle-aware validation and task alignment, comparative scoring can drift across unrelated tasks and produce misleading bundle-level rankings.

## Design

Add a first bundle-scoped integration layer on top of the existing comparative service:

1. Preserve full `AgentScore` records in the population tracker instead of keeping values only.
2. Namespace bundle task IDs as `bundle_id::task_id` when recording bundle-scoped scores.
3. Validate submitted bundle scores against the persisted synthetic bundle before recording them.
4. Generate bundle-specific leaderboards using only the task IDs shared across the evaluated agent population.
5. Run pairwise comparisons against that shared task subset so each comparison is task-aligned.

## API Surface

- `POST /v1/evaluation/comparative/bundles/{bundle_id}/scores`
  - Validates bundle existence and task membership.
  - Records comparative scores with canonical bundle task IDs.
- `POST /v1/evaluation/comparative/bundles/{bundle_id}/evaluate`
  - Builds a task-aligned bundle leaderboard for one metric.
  - Returns pairwise comparisons and the bundle-scoped leaderboard snapshot.

## Non-Goals

- No agent-execution harness yet. This slice records and evaluates bundle scores; it does not run agents against the bundle automatically.
- No cross-bundle global Elo mutation for bundle-specific evaluations. Bundle evaluation returns a scoped leaderboard instead of rewriting the global leaderboard contract.
- No persistent storage for comparative snapshots beyond the existing in-memory service behavior.

## Acceptance Criteria

- Bundle score recording rejects unknown task IDs and environment/task mismatches.
- Bundle evaluation fails closed when fewer than two agents have bundle data or when no shared tasks exist.
- Pairwise comparisons use only task IDs shared across the evaluated population.
- Regression coverage proves task-aligned scoring behavior and route-level validation.
