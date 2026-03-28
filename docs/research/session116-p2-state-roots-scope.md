# Session 116 P2 Scope Lock: Cluster 0.2 State Roots and Run-History Contracts

Date: 2026-03-28
Slice: `P2 / Cluster 0.2`
Worktree: `worktrees/session116-p2-state-roots`

## Objective

Publish one executable source of truth for where AGENT-33 stores durable state
and tighten the workflow run-history contract around canonical `run_id`
ownership.

## Inputs

- roadmap baseline from the root planning checkout:
  - `docs/phases/ROADMAP-REBASE-2026-03-26.md`
  - `docs/next-session.md`
- scaling/state audit:
  - `docs/operators/horizontal-scaling-architecture.md`
  - `docs/research/session103-p12-shared-state-scope.md`
- merged implementation baseline:
  - `origin/main` at `3fcd0e9`

## Current Gaps Confirmed On `main`

1. Durable paths are resolved ad hoc across `main.py`, `backup/service.py`,
   and runtime helpers using a mix of `Path.cwd()`, `Path.home()`, and raw
   relative settings.
2. There is no single helper that answers whether a write target belongs under
   repo-local paths, `var/`, or `~/.agent33/`.
3. Workflow execution history is stored as loose dict blobs in
   `api/routes/workflows.py`, while operations-hub lookup still identifies
   workflow records by `workflow_name + timestamp` rather than canonical
   `run_id`.

## In Scope

- one path-resolution helper for approved runtime state roots
- one short state-roots contract document
- one short run-history / artifact-authority contract document
- workflow run-history normalization around canonical `run_id`
- tests for path resolution, approved-root enforcement, and workflow history identity

## Out Of Scope

- migrating every mutable runtime surface to a shared backend
- replacing in-memory workflow registry/history with Redis or PostgreSQL
- changing every historical path setting in one slice
- redesigning cron storage or scheduler ownership in this PR

## Deferred Follow-Ups

- `scripts/hooks/session.checkpoint--status-line.py` still falls back to
  `~/.agent33/sessions` independently; move that script to the shared resolver
  in a follow-up slice so hook-side status rendering stays aligned with the
  canonical session root.
- a few older tests still mention legacy `workflow:<name>:<timestamp>` IDs
  directly for compatibility scenarios; keep those limited to compatibility
  coverage and avoid reintroducing them as the primary runtime identifier.

## Exit Criteria

- implementers can answer where a durable artifact belongs from one document
- new runtime code uses the approved path-resolution helper
- workflow history records have a canonical identity contract centered on `run_id`
- tests cover root resolution and run-history compatibility behavior
