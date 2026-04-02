# Next Session Briefing

Last updated: 2026-04-02 (post-Session-117)

## Current State

- **Branch posture**: root checkout is intentionally dirty and may lag `origin/main`; do not implement from it directly
- **Open PRs**: 0
- **Latest implementation PR on `main`**: #359
- **Canonical roadmap**: `docs/phases/ROADMAP-REBASE-2026-03-26.md`
- **Latest committed session log on clean `main`**: `docs/sessions/session-117-2026-04-02.md`

## What Main Already Includes

All previously planned implementation clusters are closed on `main`. Session 117 additionally
closed the three immediate priorities that remained after Session 116:

- **ARCH-AEP Loop 3 medium fixes**: PR #357 (event_sink typing, last_messages accessor, browser scope doc, PTC fixture)
- **Phase status reconciliation**: PR #358 (Phases 26/27/28/33 confirmed complete with PR evidence)
- **Cross-feature integration tests**: PR #359 (12 tests + MoA hyphen bug fix)

Prior cluster summary (unchanged):

- **Cluster 0** (`0.1`-`0.6`) shipped via PRs `#341`-`#347`
- **Cluster A `A1`-`A4`** shipped via PRs `#348`-`#351`
- **Phase 50 / `A5`** already shipped via PR `#316`
- **Phase 51 / `A6`** already shipped via PR `#288`
- **Phase 57 / `A7`** already shipped via PRs `#287`, `#318`, and `#339`
- **Cluster B** (`Phase 53`, `54`, `47`, `58`, `59`) is already shipped on `main`
- **Phase 35 / `C1`** is already shipped via PR `#324`

The main queue failure mode is now documentation drift, not missing implementation.

## Priorities

1. **Run a real scored SkillsBench evaluation once a live provider is reachable**
   - Blockers remain in `docs/research/session114-d7-skillsbench-readiness-report.md`
   - This is an environment/readiness problem, not an unmerged-code problem

### Optional follow-up only if requested

2. **Audit the older `.claude/worktrees/*` history tree**
   - Treat this as a separate hygiene pass

## Key References

- Canonical roadmap: `docs/phases/ROADMAP-REBASE-2026-03-26.md`
- Session 117 log: `docs/sessions/session-117-2026-04-02.md`
- Session 116 log: `docs/sessions/session-116-2026-03-29.md`
- SkillsBench blocker report: `docs/research/session114-d7-skillsbench-readiness-report.md`
- Active execution queue: `task_plan.md`
- Active execution log: `progress.md`

## Architectural Decisions Still In Force

- **Constructor injection remains the standard**; do not revive `ToolContext.metadata`
- **`run()` and `run_stream()` parity is mandatory** for any tool-loop changes
- **Context compression replaces, not duplicates, summarization behavior**
- **Dual pricing path**: `CostTracker` uses `PricingCatalog` in production, dict fallback in tests
- **Fail-open pattern**: observability features log and continue instead of failing the main operation
- **event_sink callback pattern**: now typed to `Callable[[ToolLoopEvent], Awaitable[None]]` (completed in PR #357)
- **Integration hardening P14 is complete**: the live lifespan path now has direct regression coverage for builtin tool-registry wiring, including `ptc_execute`

## Environmental Notes

- Start any new implementation from a fresh worktree on `origin/main`
- Read `task_plan.md`, `findings.md`, and `progress.md` before coding
- Create `engine/.venv` inside the worktree before Python validation
- Run `npm install` inside worktree-local `frontend/` before frontend checks
- Frontend Docker builds must use repo root as the build context
- In PowerShell, quote `gh --json` field lists, for example `gh pr list --json "number,title,url"`
