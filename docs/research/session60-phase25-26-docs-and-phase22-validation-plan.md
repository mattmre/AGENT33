# Session 60 – Phase 25/26 Docs and Phase 22 Validation Plan

**Date:** 2026-03-09  
**Branch:** `codex/session60-phase22-docs-validation`

## Objective

Package the remaining Wave 1 documentation and validation work on top of the Phase 26 review wizard branch so tomorrow's PR review has:

- a user-facing operator walkthrough for the new Phase 25/26 surfaces;
- a validation artifact proving the Phase 22 control plane hosts those surfaces correctly; and
- updated docs index links pointing reviewers at the new materials.

## Inputs Reviewed

- `docs/research/session55-phase25-status-graph-design.md`
- `docs/research/session55-phase26-html-preview-design.md`
- `docs/research/session57-wave1-ux-implementation-brief.md`
- `docs/research/session54-delta-hitl-approvals-architecture-2026-03-05.md`
- `docs/research/session58-phase26-review-wizard-design.md`
- `frontend/src/features/improvement-cycle/ImprovementCycleWizard.tsx`
- `frontend/src/components/OperationCard.tsx`
- `frontend/src/lib/workflowLiveTransport.ts`
- `engine/src/agent33/api/routes/workflow_sse.py`
- `engine/src/agent33/api/routes/workflow_ws.py`
- `engine/src/agent33/api/routes/reviews.py`
- `engine/src/agent33/api/routes/explanations.py`
- `engine/src/agent33/api/routes/tool_approvals.py`

## Decisions

| Decision | Rationale |
| --- | --- |
| Stack the docs/validation branch on `codex/session58-phase26-wizard` | The walkthrough must match the actual wizard and linked-review UX under review |
| Write a focused Phase 25/26 guide instead of overloading `walkthroughs.md` | The new flow spans frontend UI, live transport, explanations, reviews, and HITL approvals |
| Capture validation as a dedicated `docs/validation/` artifact | Keeps evidence separate from narrative docs and gives `pr-manager` a direct review target |
| Re-run targeted backend and frontend validation from the fresh worktree | Avoids shallow “expected to pass” claims and documents real branch-local results |

## Validation Commands

Backend:

```powershell
$env:PYTHONPATH='D:\GITHUB\AGENT33\worktrees\session60-docs-validation\engine\src'
python -m pytest tests/test_workflow_ws.py tests/test_workflow_sse.py tests/test_visualizations_api.py tests/test_phase15_review.py tests/test_improvement_cycle_templates.py -q --no-cov
```

Frontend:

```powershell
npm ci
npm run lint
npm test -- --run src/lib/workflowLiveTransport.test.ts src/components/WorkflowGraph.test.ts src/components/OperationCard.test.tsx src/features/improvement-cycle/presets.test.ts src/features/improvement-cycle/ImprovementCycleWizard.test.tsx src/data/domains/workflows.test.ts
npm run build
```

## Expected Deliverables

1. `docs/phase25-26-live-review-walkthrough.md`
2. `docs/validation/phase22-phase25-27-surface-validation.md`
3. `docs/research/session60-phase25-26-docs-and-phase22-validation-plan.md`
4. Index updates in `docs/README.md` and `docs/walkthroughs.md`
