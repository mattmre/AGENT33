# Roadmap Rebase - 2026-03-26

## Purpose

This file is the canonical roadmap checkpoint for the post-Session-115 / post-Session-116 merged
baseline. It exists to keep `docs/next-session.md`, `task_plan.md`, and the phase index aligned
with what is actually on `main`.

## Canonical Planning Rules

1. One canonical roadmap: this file.
2. One active execution queue: `task_plan.md`.
3. One short operator handoff: `docs/next-session.md`.
4. Do not reopen a roadmap slice without auditing clean `origin/main` first.
5. Docs-only reconciliation PRs are valid when queue accuracy is the primary deliverable.

## Status Checkpoint — 2026-03-29

The implementation baseline on `main` is materially ahead of the older queue notes.

Already shipped on `main`:

- Cluster 0 (`0.1`-`0.6`) via PRs `#341`-`#347`
- Cluster A `A1`-`A4` via PRs `#348`-`#351`
- `A5` Phase 50 via PR `#316`
- `A6` Phase 51 via PR `#288`
- `A7` Phase 57 via PRs `#287`, `#318`, and `#339`
- Cluster B (`B1`-`B5`) via PRs `#320`, `#282`, `#321`, `#323`, `#322`, `#319`, `#327`, and `#336`
- Cluster C `C1` Phase 35 via PR `#324`

Queue items that looked unfinished from the dirty root checkout but are already merged:

- Phase 50 context compression wiring
- Phase 51 prompt caching integration
- Phase 57 analytics wiring
- Cluster B composition slices
- Phase 35 voice sidecar finalization

## Active Priorities After The Merged Wave

These are the first genuine remaining priorities:

1. Real scored SkillsBench execution once a live provider is reachable.
2. Integration hardening:
   - delegation + skills + MoA end-to-end coverage
   - PTC through-lifespan integration test coverage
3. ARCH-AEP Loop 3 medium findings:
   - browser `_sessions` process-global mutable state
   - `_last_accumulated_messages` coupling between tool loop and runtime
   - `ToolContext.event_sink` typing hardening
4. Status reconciliation for parked phase records:
   - Phase `26`
   - Phase `27`
   - Phase `28`
   - Phase `33`
5. Optional audited cleanup of the historical `.claude/worktrees/*` archive.

## Key References

- `docs/next-session.md`
- `task_plan.md`
- `progress.md`
- `docs/research/session114-d7-skillsbench-readiness-report.md`
- `docs/research/session116-p13-queue-reconciliation-scope.md`
