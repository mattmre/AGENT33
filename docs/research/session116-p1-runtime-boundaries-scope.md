# Session 116 P1 Scope Lock: Cluster 0.1 Runtime Boundaries

Date: 2026-03-28
Slice: `P1 / Cluster 0.1`
Worktree: `D:\GITHUB\AGENT33\worktrees\session116-p1-boundaries`

## Objective

Add the first explicit runtime architecture boundary contract for AGENT-33 and make
it executable in both tests and CI.

## Inputs

- local roadmap baseline from the dirty root checkout:
  - `docs/phases/ROADMAP-REBASE-2026-03-26.md`
  - `docs/next-session.md`
- borrowed-improvements memo:
  - `docs/research/codex-autorunner-adaptive-ingestion-2026-03-28.md`
- current clean implementation baseline:
  - `origin/main` at `7a4f660`

## Current Structural Smells Confirmed On `main`

1. `agent33.services.operations_hub` imports `agent33.api.routes.*`
2. `agent33.api.routes.training` imports `agent33.main`
3. CI has no runtime import-boundary check today

## In Scope

- one terse runtime architecture map document
- one reusable AST-based import-boundary checker
- one repo test that enforces the current contract
- one CI entry point that fails on new violations
- an explicit, minimal allowlist for the two currently known exceptions

## Out Of Scope

- package moves
- broad layering refactors
- removing every existing boundary smell in this slice
- extending the checker to every possible import rule in the repo

## Exit Criteria

- the runtime layer contract is documented in one short file
- tests fail on new unexpected import-boundary violations
- CI runs the checker directly
- known exceptions are explicit, narrow, and reviewable
