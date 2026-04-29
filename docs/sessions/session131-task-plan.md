# Session 131 — Master Task Plan

**Date**: 2026-04-20  
**Session owner**: Claude (orchestrator)  
**Baseline**: PR `#414` / commit `f016b35` on `origin/main`  
**Open PRs at session start**: 0  
**Goal**: Execute T1–T10 sequentially from fresh `origin/main` worktrees, one PR per slice.

---

## Execution Queue

| # | Task | Slice Label | Status | PR | Notes |
|---|------|-------------|--------|----|-------|
| T1 | P68-Lite monitoring — verify `outcomes` table populates on merged baseline; add alert if missing | `session131-t1-p68lite` | **MERGED #415** `e8cd352` | #415 | Complete |
| T2 | P69b persistence reconciliation — align `P69bService` with persisted `PausedInvocation` design intent | `session131-t2-p69b-persist` | **MERGED #416** `1cd556a` | #416 | Complete |
| T3 | SSE migration-path docs — document client upgrade path before any schema-v2 work begins | `session131-t3-sse-docs` | **MERGED #417** `9da0f9d` | #417 | Complete |
| T4 | Security scan / merge-policy cleanup — fix `Dependency CVE Scan` + `Container Image Scan` baseline failures | `session131-t4-security` | **MERGED #418** `cb11b73` | #418 | Complete — CVEs fixed, scans green |
| T5 | Evolver Sprint 0 — clean-room guardrails (legal + arch boundary codified in code + docs) | `session131-t5-evolver-s0` | **MERGED #419** `9e0dadb` | #419 | Complete |
| T6 | Evolver Sprint 1 — candidate state model (`candidate→validated→published→revoked`) | `session131-t6-evolver-s1` | **MERGED #420** `35ab23e` | #420 | Complete |
| T7 | Evolver Sprint 2 — candidate publication pipeline (intake with lowered confidence) | `session131-t7-evolver-s2` | **MERGED #421** `e9c2f24` | #421 | Complete |
| T8 | Evolver Sprint 3 — mailbox / heartbeat pilot (thin proxy seam + task metrics) | `session131-t8-evolver-s3` | **MERGED #422** `0c0c615` | #422 | Complete |
| T9 | Evolver Sprint 4 — lifecycle verbs and operator UX (append-only journals + operator controls) | `session131-t9-evolver-s4` | **MERGED #423** `a2a4582` | #423 | Complete |
| T10 | Evolver Sprint 5 — detect-only skills doctor (read-only diagnostics for imported-asset health) | `session131-t10-evolver-s5` | **MERGED #424** `9352715` | #424 | Complete |

---

## Execution Rules

1. One fresh worktree per slice from updated `origin/main`.
2. One disposable agent per slice — dispose after PR is merged and verified.
3. One PR per slice.
4. No later slice starts before the current slice is merged and verified from fresh `origin/main`.
5. If CI fails on a slice, fix within the same worktree and re-push before moving on.
6. After each merge, update this file, `progress.md`, `findings.md`, and `docs/next-session.md`.

---

## Per-Slice Phase Protocol

Every slice must move through these phases in order:

| Phase | Required output |
|-------|-----------------|
| 1. Research refresh | Read relevant source files; note delta vs `main` in findings |
| 2. Scope lock | Define exact included work + explicit non-goals + branch name |
| 3. Implementation | Code / docs changes scoped to this slice only |
| 4. Validation | `pytest` (targeted) + `ruff check` + `ruff format --check` + `mypy` |
| 5. PR prep | PR body summarizing changes + risks |
| 6. CI watch | Confirm green; fix if red |
| 7. Merge | Squash merge after green CI |
| 8. Post-merge verify | Run targeted tests from fresh `origin/main` worktree |
| 9. Handoff update | Update `task_plan.md`, `progress.md`, `findings.md`, `docs/next-session.md`, this file |

---

## Architectural Context

### T1 — P68-Lite monitoring
- Surface: `engine/src/agent33/outcomes/` (`models.py`, `persistence.py`, `service.py`)
- Route: `engine/src/agent33/api/routes/outcomes.py`
- Goal: Confirm `outcomes` table is populated during agent invocation rollout; implement alert if empty >24h per architectural decision #15.
- Research needed: Read `outcomes/service.py`, `outcomes/persistence.py`, check if alert hook exists.

### T2 — P69b persistence reconciliation
- Surface: `engine/src/agent33/autonomy/p69b_service.py`, `p69b_models.py`
- Design specs: `docs/research/session126-p69b-ux-spec.md`, `docs/research/session126-p69b-api-contract.md`
- Current state: `P69bService` is in-memory only (intentional in PR #401 scope).
- Goal: Evaluate whether the UX spec / API contract requires DB persistence; if yes, add `PausedInvocation` DB-backed store with Alembic migration; if no, document the decision and add a clear comment to the service.
- Research needed: Re-read specs to determine if persistence was deferred or explicitly out-of-scope.

### T3 — SSE migration-path docs
- Surface: `engine/src/agent33/workflows/events.py` (schema v1 in place since PR #400)
- Goal: Write `docs/research/sse-schema-v2-migration-path.md` documenting the v2 upgrade path for clients before any v2 work begins.
- Research needed: Review events.py schema, `check_schema_version()`, strict rejection model.

### T4 — Security scan cleanup
- Surface: `.github/workflows/` (Dependency CVE Scan, Container Image Scan)
- Goal: Identify what's failing, either fix the underlying finding (pin deps, update Dockerfile base image) or adjust the workflow rules so routine PRs are not blocked by stale baseline.
- Research needed: Check workflow files, identify scan tool (Trivy? Dependabot? Snyk?), review recent failure logs.

### T5–T10 — Evolver clean-room adaptation
- Research complete: `docs/research/evolver-adaptive-ingestion-2026-04-20.md`
- Legal constraint: GPL-3.0 conflict → concept-only, zero direct code or prose reuse.
- Canonical lifecycle: `candidate → validated → published → revoked`
- Sprint 0 goal: Codify no-reuse guardrails as code comments + module docstrings + a `docs/research/evolver-clean-room-guardrails.md` fence document; add lint/import guards.
- Sprints 1-5: Implement the lifecycle model, publication pipeline, mailbox/heartbeat, operator UX, and skills doctor incrementally.

---

## Session State Tracking

### T1 state
- Worktree: `worktrees/session131-t1-p68lite` (disposed)
- Branch: `session131-t1-p68lite`
- PR: #415
- Status: `MERGED` — commit `e8cd352`

### T2 state
- Worktree: pending
- Branch: pending
- PR: pending
- Status: `pending`

### T3 state
- Worktree: pending
- Branch: pending
- PR: pending
- Status: `pending`

### T4 state
- Worktree: pending
- Branch: pending
- PR: pending
- Status: `pending`

### T5 state
- Worktree: pending
- Branch: pending
- PR: pending
- Status: `pending`

### T6 state
- Worktree: `worktrees/session131-t6-evolver-s1` (disposed)
- Branch: `session131-t6-evolver-s1`
- PR: #420
- Status: `MERGED` — commit `35ab23e`

### T7 state
- Worktree: `worktrees/session131-t7-evolver-s2` (disposed)
- Branch: `session131-t7-evolver-s2`
- PR: #421
- Status: `MERGED` — commit `e9c2f24`

### T8 state
- Worktree: `worktrees/session131-t8-evolver-s3` (disposed)
- Branch: `session131-t8-evolver-s3`
- PR: #422
- Status: `MERGED` — commit `0c0c615`

### T9 state
- Worktree: `worktrees/session131-t9-evolver-s4` (disposed)
- Branch: `session131-t9-evolver-s4`
- PR: #423
- Status: `MERGED` — commit `a2a4582`

### T10 state
- Worktree: `worktrees/session131-t10-evolver-s5` (disposed)
- Branch: `session131-t10-evolver-s5`
- PR: #424
- Status: `MERGED` — commit `9352715`

---

## Resume Protocol

If session is interrupted:
1. Read this file to find the current slice and its status.
2. Read `progress.md` for the last merge state.
3. Read `findings.md` for any implementation notes from the last agent.
4. If a PR is open, check its CI status and any review comments.
5. If mid-implementation, check the worktree branch listed under that task's state section.
6. Resume from the first incomplete phase step for that slice only.
