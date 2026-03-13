# Session 57 Priority Orchestration Plan

**Date:** 2026-03-06
**Purpose:** Convert the active `docs/next-session.md` priority queue into a dependency-ordered execution plan with carry-forward triage, research references, PR boundaries, and fresh-agent workflow guidance.

---

## Inputs Reviewed

- `CLAUDE.md`
- `docs/next-session.md`
- `docs/phases/README.md`
- `docs/sessions/session-57-2026-03-06.md`
- Local git status/worktree layout
- Session 56 PR carry-forward state (#141-#144)
- Historical research remnants in `docs/research/`

---

## Wave Plan

### Wave 0 — Session 56 carry-forward stabilization
1. Review PRs #141-#144 and confirm baseline readiness.
2. Use a fresh integration worktree from `main` for validation/rebase work.
3. Run confidence gates before treating the stack as a baseline.
4. Rework PRs #141 and #143 if their local implementations do not match the documented scope.

### Wave 1 — Frontend / UX foundation
1. Frontend render/interaction test harness (`@testing-library/react`).
2. Phase 25 SSE fallback.
3. Phase 27 improvement-cycle workflow template wiring.
4. Phase 26 approval flows + improvement-cycle wizard UX.
5. Phase 25/26 user docs.
6. Phase 22 integration validation against the new surfaces.

### Wave 2 — Runtime execution hardening
1. Phase 38 Docker container kernels for Jupyter adapter.

### Wave 3 — Benchmarking / evaluation uplift
1. SkillsBench reporting and result artifacts.
2. A5/A6 comparative scoring against persisted synthetic bundles.

### Wave 4 — Operational hardening
1. Phase 30 trace tuning.
2. Phase 31 backup/restore validation.
3. Phase 32 cross-service tenant verification.
4. Phase 33 marketplace/distribution integration.
5. Phase 35 voice daemon + policy tuning.

---

## Carry-Forward Assessment

### PR #141 — Phase 25 WebSocket workflow status streaming
- Remote PR exists and is open against `main`.
- Local inspection indicates usable backend plumbing, but the implementation appears workflow-scoped rather than run-scoped.
- This may be sufficient as an MVP, but it is a likely hotspot for the Phase 25 SSE fallback work.
- Recommendation: validate semantics before merge; patch if Phase 25 Stage 3 requires per-run transport contracts.

### PR #142 — Phase 28 LLMGuard + Garak adapters
- Narrow scope, focused file footprint, low conflict risk.
- Local inspection suggests it is the cleanest carry-forward branch.
- Recommendation: validate and merge early; it is a good baseline candidate.

### PR #143 — Phase 43 MCP resources + auth
- Remote PR exists, but local inspection suggests the documented lifespan/auth wiring is incomplete.
- `main.py` overlap with PR #141 makes this the highest integration-risk carry-forward item.
- Recommendation: do not merge unchanged; rework in a fresh integration worktree before using as baseline.

### PR #144 — Phase 38 token streaming + tool call reassembly
- Remote PR exists and looks close to merge-ready.
- Primary follow-up is validation of the non-delta fallback path and any downstream event consumers.
- Recommendation: validate and merge early; use as the Phase 38 baseline for Docker kernel work.

---

## Local Remnants Classification

### Keep as active research inputs
- `docs/research/session54-haystack-deep-dive-gap-analysis-2026-03-05.md`
- `docs/research/session54-haystack-gap-remediation-implementation-plan-2026-03-05.md`
- `docs/research/session47-priority-research-findings.md`

### Preserve as historical/session artifacts
- `docs/sessions/session-47-2026-02-26.md`
- `docs/sessions/session-48-2026-02-27.md`
- `docs/sessions/session-49-2026-02-27.md`
- `docs/research/salvaged-skillsbench-code/`
- `findings.md`, `progress.md`, `task_plan.md`
- legacy `pr*_review_comment.md`

### Safe local-only/generated cleanup candidates
- `engine/.coverage`
- root `node_modules/`
- root `package.json`
- root `package-lock.json`

### Explicit decision required before cleanup
- `docs/ARCH AGENTIC ENGINEERING AND PLANNING/pr-*.json`
- `docs/ARCH AGENTIC ENGINEERING AND PLANNING/pr-list.json`

---

## Recommended Branch / Worktree Strategy

- Treat the current root checkout (`feat/session56-phase25-websocket-workflow`) as a salvage/reference branch, not the long-term baseline.
- Create a fresh Session 57 integration worktree from `main` for Wave 0 merge/rebase/gating work.
- After Wave 0, create separate fresh worktrees per active PR/workstream to avoid context bleed.
- Do not continue new feature work directly on the existing `phase28`, `phase38`, or `phase43` worktrees; retire or refresh them after Wave 0 completes.

---

## Research Inputs by Wave

### Wave 1
- `docs/research/session55-phase25-status-graph-design.md`
- `docs/research/session55-phase26-html-preview-design.md`
- `docs/research/session55-phase27-hub-alignment.md`
- `docs/research/session54-delta-hitl-approvals-architecture-2026-03-05.md`
- `docs/research/session56-stage3-research.md`

### Wave 2
- `docs/research/session55-qwen-agent-analysis.md`
- `docs/phases/qwen-adoption-phases.md`
- `docs/sessions/session-57-2026-03-06.md`

### Wave 3
- `docs/research/skillsbench-analysis.md`
- `docs/research/session53-a5-bundle-persistence.md`
- `docs/research/session52-priority-and-phase-roadmap.md`

### Wave 4
- `docs/research/session55-phase30-api-policy-fixtures.md`
- `docs/research/session53-phase30-outcome-acceptance.md`
- `docs/research/session55-phase31-production-tuning.md`
- `docs/research/session53-phase31-trend-analytics.md`
- `docs/research/session53-phase31-threshold-tuning.md`
- `docs/research/session55-phase32-connector-boundary-audit.md`
- `docs/research/session55-phase33-provenance-architecture.md`
- `docs/research/session55-phase35-policy-calibration.md`

---

## Fresh-Agent Workflow Template

For each wave or PR-sized item, prefer:
1. **Researcher** — inspect docs + code, confirm gaps and acceptance criteria.
2. **Architect** — lock the implementation shape and PR boundary.
3. **Implementer** — make scoped code changes only for that workstream.
4. **Tester** — run targeted + repo-standard validation.
5. **Reviewer** — spot-check for logic/security/regression issues before PR packaging.

---

## Immediate Next Actions

1. Create Session 57 integration worktree from `main`.
2. Validate PRs #142 and #144 first.
3. Rework/verify PR #141 transport semantics.
4. Rework PR #143 before merge.
5. After Wave 0, start Wave 1 with frontend test harness + Phase 25 SSE fallback.
