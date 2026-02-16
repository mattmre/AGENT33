# Phase 22 PR-05: Frontend Orchestration Usability Controls

## Scope
- Improve control-plane usability for high-frequency operator workflows.
- Wire UI for iterative invoke and workflow scheduling endpoints.
- Add guided controls for repeat/autonomous execution and schedule creation.

## Key Changes
- Updated domain operation catalogs:
  - `frontend/src/data/domains/workflows.ts`
    - schedule create/list/delete operations
    - workflow history operation
  - `frontend/src/data/domains/agents.ts`
    - iterative invoke operation (`/v1/agents/{name}/invoke-iterative`)
  - `frontend/src/data/domains/training.ts`
    - corrected rollout/optimize default payloads for existing backend contract
- Added UX hint typing:
  - `frontend/src/types/index.ts` (`OperationUxHint`)
- Upgraded `frontend/src/components/OperationCard.tsx`:
  - guided workflow execute controls (single/repeat/autonomous)
  - guided workflow schedule controls (interval/cron)
  - iterative strategy presets (quick/balanced/deep)
  - format/reset helpers for path/query/body JSON editors
  - lightweight response summaries for iterative/scheduled flows
- Updated `frontend/src/styles.css` for helper panels and JSON tooling controls.

## Validation
- `cd frontend && npm run lint`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`

