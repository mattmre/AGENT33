# Session 116 P13 Queue Reconciliation Audit

**Date**: 2026-03-29
**Purpose**: reconcile the stale roadmap/queue docs against the actual merged state on `main`

## Summary

The clean `origin/main` baseline is materially ahead of the queue state described in
`docs/next-session.md`. Several slices that still appear queued in the root planning files are
already merged on `main`. The immediate operational risk is not missing code; it is roadmap drift.

## Merged / Shipped Evidence

### Cluster 0 — Borrowed Platform Contracts

- `0.1` runtime architecture boundary map and enforcement — `3fcd0e9` / PR `#341`
- `0.2` canonical state roots and run-history contracts — `9a47810` / PR `#342`
- `0.3` agent/runtime compatibility drift CI — `8e0a26e` / PR `#343`
- `0.4` operator verification and process-registry runbooks — `952b132` / PR `#344`
- `0.5` lightweight ingestion task artifacts — `98194ed` / PR `#345`
- `0.6` ARCH-AEP Loop 0 — `0d80a2f` / PR `#346`
- Cluster 0 follow-up remediation — `4ef1f4a` / PR `#347`

### Cluster A — Runtime Intelligence Foundation

- `A1` Phase 31 residual analytics and signal tuning — `cc073b6` / PR `#348`
- `A2` Phase 32 residual middleware hardening — `16434ba` / PR `#349`
- `A3` Phase 49 pricing catalog and effort heuristic — `ed5e9ec` / PR `#350`
- `A4` Phase 52 secret redaction pipeline (managed-process residual) — `3fa40bc` / PR `#351`
- `A5` Phase 50 context compression engine — already merged earlier:
  - `c66194d` / PR `#285` core compressor
  - `3b1e153` / PR `#316` runtime/lifespan wiring
- `A6` Phase 51 prompt caching integration — already merged earlier:
  - `58a83ca` / PR `#288` core prompt caching
  - `68f4d0d` / PR `#312` stream cache-usage logging + end-to-end test
- `A7` Phase 57 session analytics — already merged earlier:
  - `a5f1dbf` / PR `#287` analytics engine
  - `71d2500` / PR `#318` tenant-isolation hardening
  - `d1d6e9b` / PR `#339` frontend dashboard integration

### Cluster B — Composition and Orchestration

- `B1` Phase 53 subagent delegation framework — `8bb5362` / PR `#320`
- `B2` Phase 54 slash-command interface — `f4eb742` / PR `#321`
- `B3` Phase 47 capability pack system — `ca8614d` / PR `#323`
- `B4` Phase 58 Mixture-of-Agents template — `f97db9f` / PR `#322`
- `B5` Phase 59 titles and trajectories — merged across:
  - `48648d9` / PR `#319`
  - `1860fb0` / PR `#327`
  - `ecac45e` / PR `#336`

### Cluster C

- `C1` Phase 35 voice sidecar finalization — `6a96329` / PR `#324`

## Stale Queue Statements To Correct

- `docs/next-session.md` on `main` still reports Session 111 as the latest state.
- The queued “remaining items” still include slices that are already merged:
  - Cluster 0
  - A1-A4
  - A5-A7
  - B1-B5
  - C1
- The canonical roadmap file referenced by newer local planning (`docs/phases/ROADMAP-REBASE-2026-03-26.md`) is not present on clean `main`.

## First Genuine Remaining Priorities

After reconciling the shipped slices above, the next real priorities are:

1. Run a real scored SkillsBench evaluation once a live provider is reachable.
2. Address the remaining ARCH-AEP Loop 3 medium findings:
   - browser `_sessions` process-global mutable dict
   - `_last_accumulated_messages` coupling
   - `ToolContext.event_sink` typing
   - missing PTC-through-lifespan integration test
3. Finish integration hardening:
   - delegation + skills + MoA end-to-end coverage
   - PTC-through-lifespan integration coverage
4. Reconcile parked status/docs debt:
   - Phase 26
   - Phase 27
   - Phase 28
   - Phase 33 residual status
5. Optional hygiene only if requested:
   - archived `.claude/worktrees/*` history tree audit

## Minimal Docs Write-Set

- `docs/phases/ROADMAP-REBASE-2026-03-26.md`
  - add a current-status checkpoint or shipped-slices addendum
  - replace “active queue” guidance so it matches the merged baseline
- `docs/next-session.md`
  - rewrite from the stale Session 111 handoff to the current post-Session-116 state
  - point at the real remaining priorities above
- `docs/research/session116-p13-queue-reconciliation-audit.md`
  - preserve the evidence trail for the reconciliation
