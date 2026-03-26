# Session 110 Task Plan (2026-03-26)

## Overview
Full sequential implementation of 15 remaining priority items. PR-per-item workflow with review, fix, test, lint, merge cycle. Agentic orchestration with fresh agents per task to prevent context rot.

## Recovery Protocol
If session crashes:
1. Read this file + `docs/sessions/session-110-2026-03-26.md`
2. Check task statuses via TaskList
3. Check `gh pr list --state open` for in-flight PRs
4. Resume from first non-completed task

## Execution Sequence

### Tier 1 — In-Flight + Arch Fixes (Tasks 1-5)

| Task | Item | Status | PR | Notes |
|------|------|--------|----|----|
| 1 | PR #294 fix + merge (Phase 55) | DONE | #294 | All 6 Copilot issues already addressed; rebased and merged |
| 2 | AEP-A01: Workflow graph retry refresh | DONE | #295 | Main bug already fixed; DAGVisualization.tsx gap closed, 3 new tests |
| 3 | AEP-B01: Wire component-security persistence | DONE | #296 | Moved to lifespan init with shutdown cleanup, 11 new tests |
| 12 | P-04: Fix tool_loop IndexError | DONE | #297 | 1-line fix: save system prompt before clear |
| 4 | P4.13: Coverage push to 90% | DONE | #298 | 201 new tests across 10 modules, found ArtifactFilter closure bug |
| 5 | P4.14: Secret rotation runbook | DONE | #299 | 42 secrets, 676-line runbook |

### Tier 2 — Arch Prerequisites (Tasks 10-11)

| Task | Item | Status | PR | Notes |
|------|------|--------|----|----|
| 10 | P-01: ToolContext metadata field | SKIPPED | — | Superseded by constructor injection (Phases 53/55/56) |
| 11 | P-03: run_stream() parity | DONE (research) | — | 3/3 target features have parity; 6 other gaps documented |

### Tier 3 — OpenClaw Tracks (Tasks 6-9)

| Task | Item | Status | PR | Notes |
|------|------|--------|----|----|
| 6 | OpenClaw Track 7: Web research trust | REMAINING | — | Research + implement |
| 7 | OpenClaw Track 8: Sessions UX | REMAINING | — | Research + implement |
| 8 | OpenClaw Track 9: Ops doctor | REMAINING | — | Research + implement |
| 9 | OpenClaw Track 10: Provenance closeout | REMAINING | — | Research + implement |

### Tier 4 — Residual Hardening (Tasks 13-15)

| Task | Item | Status | PR | Notes |
|------|------|--------|----|----|
| 13 | Phase 31 residuals: Analytics | REMAINING | — | Research + implement |
| 14 | Phase 32 residuals: Middleware | REMAINING | — | Research + implement |
| 15 | Phase 35: Voice sidecar | REMAINING | — | Research + implement |

## Agent Orchestration Pattern
- Each task: Research Agent → Plan/Architect Agent → Implementer Agent → Tester Agent → PR
- Fresh agent per phase, dispose after completion
- All research saved to docs/research/
- Session log updated after each task completion
