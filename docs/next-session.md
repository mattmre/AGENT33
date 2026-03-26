# Next Session Briefing

Last updated: 2026-03-26 (Session 110 — 6 PRs merged, 8/15 tasks done)

## Current State

- **Branch**: `main`
- **Latest commit**: `a97c587` (PR #299 — secret rotation runbook)
- **Open PRs**: 0
- **PRs merged this session**: 6 (#294-#299)
- **Tests added this session**: 215 (201 coverage + 3 DAG + 11 security lifespan)
- **Task plan**: `docs/research/session110-task-plan.md` (7 remaining items)
- **Session log**: `docs/sessions/session-110-2026-03-26.md`

## Immediate Priorities (7 remaining from Session 110 plan)

1. **OpenClaw Track 7**: Web research and trust — research + implement
2. **OpenClaw Track 8**: Sessions and context UX — research + implement
3. **OpenClaw Track 9**: Operations, config, and doctor — research + implement
4. **OpenClaw Track 10**: Provenance, FE hardening, closeout — research + implement
5. **Phase 31 residuals**: Learning analytics and signal tuning
6. **Phase 32 residuals**: Middleware operational hardening (circuit-breaker tuning)
7. **Phase 35**: Voice sidecar finalization (Phase 48 replacement)

## Known Bugs to Fix

1. **ArtifactFilter closure bug** (`engine/src/agent33/automation/filters.py`): Late-binding closure in multi-predicate composition — only the last predicate evaluates when chaining 2+ `by_regex()`/`by_predicate()` calls. Has xfail test in `test_automation_filters.py`.
2. **run_stream() has 6 parity gaps** with run(): handoff interceptor, double-confirmation, LLM retry, budget enforcement, error reset, observation recording. See `docs/research/session110-p03-stream-parity.md`.

## Architectural Decisions (Session 110)

- **P-01 superseded**: Constructor injection (established by Phases 53/55/56) is the de facto standard for tool service access. ToolContext remains frozen/slots. Do not add metadata dict.
- **Lifespan pattern is standard**: AEP-B01 confirmed that all service init should go through FastAPI lifespan, not module-level singletons.

## Phase Status Summary

| Phase / Track | Status | Notes |
| --- | --- | --- |
| 01-21 | Complete | Foundation stable |
| 22-29 | Complete | UI, review, and planning foundations merged |
| 30 | Complete | Production trace tuning confirmed on `main` |
| 31-33 | Mostly Complete | Residual analytics/signal tuning remains (Task 13) |
| 32 | Mostly Complete | Residual middleware hardening remains (Task 14) |
| 35 | In Progress | Voice sidecar finalization needed (Task 15) |
| 36-46 | Complete | Includes later hardening slices |
| 47-48 | Planned | Capability packs, voice sidecar, production hardening |
| 55-56 | Complete | Browser automation (#294), programmatic tool calling (#292) |
| P4.13-P4.17 | Complete | Coverage push, secret runbook, Alembic safety, load tests, plugin SDK |
| OpenClaw T1-T6 | Complete | Closed in PRs `#167`, `#171`, `#178`-`#183` |
| OpenClaw T7-T10 | Planned | Research/trust, session UX, ops/doctor, provenance closeout |

## Session 110 Completed Work

| PR | Description | Tests |
|----|-------------|-------|
| #294 | Phase 55: browser vision & cloud backend | 32 pass |
| #295 | AEP-A01: DAG retrying status in visualization | 3 new |
| #296 | AEP-B01: Security scan lifespan init + shutdown | 11 new |
| #297 | P-04: Handoff system prompt preservation | — |
| #298 | P4.13: Coverage push across 10 modules | 201 new |
| #299 | P4.14: K8s secret rotation runbook (42 secrets) | — |

## Key Paths

- Session 110 log: `docs/sessions/session-110-2026-03-26.md`
- Session 110 task plan: `docs/research/session110-task-plan.md`
- Coverage analysis: `docs/research/session110-p413-coverage-analysis.md`
- Stream parity research: `docs/research/session110-p03-stream-parity.md`
- Phase roadmaps:
  - `docs/phases/PHASE-44-48-EVOKORE-INTEGRATION-ROADMAP.md`
  - `docs/phases/PHASE-49-59-HERMES-ADOPTION-ROADMAP.md`
  - `docs/phases/OPENCLAW-PARITY-10-PHASE-ROADMAP.md`

## Environmental Notes

- Use a fresh worktree from `origin/main` for each new implementation slice
- Read task plan and research docs before starting work
- Create `engine/.venv` inside worktree before running Python checks
- Run `npm install` inside worktree-local `frontend/` before frontend checks
- Frontend Docker builds must use repo root as the build context
- Leave `temp_report.txt` and `temp_search_results.txt` in place unless approved for deletion
