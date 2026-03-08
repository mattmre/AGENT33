# Session 57 Wave 1 UX Implementation Brief

**Date:** 2026-03-06
**Scope:** Frontend testing foundation, Phase 25 SSE fallback, Phase 26 approval flows, Phase 27 improvement-cycle wizard wiring, Phase 25/26 docs, and Phase 22 validation.

## Key Findings
- Frontend lacks DOM-capable test tooling: no `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`, or `jsdom` in `frontend/package.json`, and no Vitest DOM setup in `frontend/vite.config.ts`.
- Workflow live updates are only half-wired: the backend WS stack exists, but there is no workflow SSE endpoint, `WorkflowGraph.tsx` does not reliably react to updated props, and `OperationCard` renders the graph without refresh wiring.
- Existing authenticated SSE precedent is `frontend/src/components/ObservationStream.tsx`, which uses `fetch` stream parsing instead of native `EventSource`; this should be reused for workflow SSE fallback.
- Phase 26 backend primitives exist (`api/routes/explanations.py`, `explanation/renderer.py`, `api/routes/reviews.py`, `api/routes/tool_approvals.py`), but there is no dedicated frontend flow tying explanations, reviews, and approvals together.
- Phase 27 template canon is inconsistent: current templates live at `core/workflows/improvement-cycle-retrospective.md` and `core/workflows/improvement-cycle-metrics-review.md`, while the intended final location is `core/workflows/improvement-cycle/`.
- `frontend/src/data/domains/improvements.ts` is out of sync with `engine/src/agent33/api/routes/improvements.py` and must be corrected before building the improvement-cycle wizard.

## Dependency-Ordered Plan
1. Add DOM/render testing infrastructure to the frontend and create the first component interaction tests.
2. Align raw frontend domain contracts (`improvements`, `explanations`, `reviews`) with the current backend APIs.
3. Implement Phase 25 SSE fallback and make `WorkflowGraph` react to live prop updates.
4. Canonicalize Phase 27 workflow templates and wire preset selection into the frontend.
5. Build the Phase 26/27 improvement-cycle wizard and plan/diff approval flows in the frontend.
6. Write Phase 25/26 user docs and run Phase 22 extension validation against the new surfaces.

## Recommended PR Boundaries
- PR 1: Frontend testing foundation + frontend domain contract alignment
- PR 2: Phase 25 live workflow transport (WS/SSE/poll fallback) + graph refresh fixes
- PR 3: Phase 27 template canon + frontend preset wiring
- PR 4: Phase 26/27 wizard + plan/diff approval orchestration
- PR 5: User docs + Phase 22 integration validation

## Key Files
- `frontend/package.json`, `frontend/vite.config.ts`, frontend test setup files
- `frontend/src/components/WorkflowGraph.tsx`, `OperationCard.tsx`, `ExplanationView.tsx`
- `frontend/src/features/operations-hub/OperationsHubPanel.tsx`
- `frontend/src/features/improvement-cycle/*` (new)
- `frontend/src/data/domains/improvements.ts`, `reviews.ts`, `explanations.ts`
- `engine/src/agent33/api/routes/workflow_ws.py` or sibling SSE route module
- `engine/src/agent33/workflows/events.py`, `executor.py`, `main.py`

## Recommended New Research/Validation Docs
- `docs/research/session57-phase25-sse-fallback-design.md`
- `docs/research/session57-phase26-27-improvement-cycle-wizard-design.md`
- `docs/research/session57-phase26-review-artifact-linkage.md`
- `docs/research/session57-phase27-template-catalog-source-of-truth.md`
- `docs/validation/phase22-phase25-27-surface-validation.md`

## Highest-Risk Integration Points
- `WorkflowGraph` currently discards incoming prop updates after initialization.
- Workflow SSE fallback must use authenticated `fetch` streaming, not native `EventSource`.
- Review records do not yet persist strong linkage back to explanation artifacts.
- The frontend improvements domain config is stale and will cause false negatives if left unfixed.
