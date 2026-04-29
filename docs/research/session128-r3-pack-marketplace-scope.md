# Session 128 R3 scope lock - pack marketplace web UI

## Goal

Implement the remaining POST-CLUSTER pack marketplace web UI on top of the
already-merged backend marketplace APIs.

## Baseline

- Fresh worktree: `C:\GitHub\repos\AGENT33\worktrees\session128-s3-pack-marketplace`
- Branch: `session128-s3-pack-marketplace`
- Base commit: `5de4f78` (`Session 128: harden P-ENV v2 startup reliability (#410)`)
- R1 and R2 are merged and fresh-main verified.

## Fresh-main audit

- Marketplace backend APIs are already merged on main:
  - `engine/src/agent33/api/routes/marketplace.py`
  - `engine/src/agent33/packs/marketplace_aggregator.py`
  - `engine/src/agent33/packs/curation_service.py`
  - `engine/src/agent33/packs/categories.py`
- Main does **not** yet contain marketplace-specific frontend UI.
- The old worktree `session127-s12-pack-marketplace` contains useful research and
  backend-era context, but it did not deliver the frontend UI slice.

## In-scope R3 UI surfaces

1. Add a new frontend feature folder for pack marketplace UI.
2. Add marketplace entry/navigation from `frontend/src/App.tsx`.
3. Implement browse/search/install flows against the merged marketplace APIs.
4. Show installed packs using the existing packs endpoints.
5. Display trust/provenance/curation state in the UI.
6. Keep curation operations mostly read-only in R3; defer full submission/admin
   workflows to R4 where appropriate.

## Likely files

- `frontend/src/App.tsx`
- `frontend/src/types/index.ts`
- `frontend/src/features/pack-marketplace/*` (new)
- related frontend tests under `frontend/src/features/pack-marketplace/__tests__/`

## Validation target

- frontend tests for the new feature/components/hooks
- frontend lint/build test stack already used by the repo
- any targeted backend tests only if the UI work requires API shape adjustments

## Guardrails

- Consume real marketplace endpoints; do not hardcode pack data.
- Reuse existing frontend patterns from `tool-catalog/`, `workflows/`, and
  shared API helpers.
- Do not start the community-submission slice until this marketplace PR is
  merged and fresh-main verified.
