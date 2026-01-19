# AGENT-33 Next Session

## Objective
- Execute Phase 8 (Evaluation Harness) tasks, then confirm Phase 11-20 owner assignments.

## Open PR
- **PR #1**: https://github.com/agent-33/AGENT-33/pull/1
- **Branch**: `ask/T4-7-spec-first-harness`
- **Scope**: Phase 3-7 work (spec-first workflow + runtime + evidence pipeline)

## Tasks
1) Execute Phase 8 tasks (T15-T16) per workflow plan.
2) Confirm owners and sequencing for Phase 11-20 tasks (T17-T28).
3) Merge or review PR #1 for Phase 3-7 work.
4) Record verification evidence in `core/arch/verification-log.md`.
5) Capture session log(s) for Phase 8 work.

## Inputs
- `docs/phases/PHASE-03-08-WORKFLOW-PLAN.md`
- `docs/phases/PHASE-08-EVALUATION-AND-METRICS.md`
- `docs/phases/PHASE-11-20-WORKFLOW-PLAN.md`
- `core/orchestrator/handoff/TASKS.md`
- `core/orchestrator/handoff/REVIEW_CHECKLIST.md`
- `core/orchestrator/handoff/REVIEW_CAPTURE.md`
- `core/arch/test-matrix.md` (updated with agentic guidance)

## Status Update (2026-01-16)
- Phase 7 COMPLETED: T13-T14 executed.
  - Evidence templates updated with primary/secondary verification slots, diff summary.
  - Verification log updated with partial run guidance and indexing rules.
  - Test matrix extended with agentic task guidance and partial run protocol.
- Phase 3-7 complete; Phase 8-20 pending.
- PR #1 open with all Phase 3-7 changes ready for merge.
- Tests/CI: N/A (docs-only repo; no test harness).
- CLAUDE instructions at `core/agents/CLAUDE.md` (RSMFConverter project context).

## Sequenced Backlog

### Completed Phases
| Phase | Tasks | Status | Evidence |
|-------|-------|--------|----------|
| 3 | T4-T5 | Done (review pending) | SPEC_FIRST_CHECKLIST.md, AUTONOMY_BUDGET.md |
| 4 | T6-T7 | Done | HARNESS_INITIALIZER.md, PROGRESS_LOG_FORMAT.md |
| 5 | T8-T10 | Done | policy-pack-v1/*, PROMOTION_CRITERIA.md |
| 6 | T11-T12 | Done | TOOL_GOVERNANCE.md, TOOLS_AS_CODE.md |
| 7 | T13-T14 | Done | EVIDENCE_CAPTURE.md, test-matrix.md |

### Next Tasks (Priority Order)
| Priority | Task | Phase | Owner | Reviewer Required |
|----------|------|-------|-------|-------------------|
| 1 | T15: Evaluation harness + golden tasks plan | 8 | Architect Agent | Yes (architecture) |
| 2 | T16: Baseline evaluation reporting template | 8 | QA/Reporter Agent | No |
| 3 | T17: Agent registry schema + capability taxonomy | 11 | Architect Agent | Yes (architecture) |
| 4 | T18: Routing map + onboarding updates | 11 | Project Engineering Agent | No |

### Pending Review
- T4-T6 (Phase 3-4): Awaiting reviewer signoff for architecture/process/operational changes.

## Next Session Priorities
1) Execute Phase 8 tasks (T15-T16).
2) Confirm owners for Phase 11-20 tasks.
3) Capture Phase 3-4 reviewer signoff if available.
4) Continue agentic orchestration cycles (Planner, Repo Auditor, Test Engineer, Follow-up Engineer, QA/Reporter).
