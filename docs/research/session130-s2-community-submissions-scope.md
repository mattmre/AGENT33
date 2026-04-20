# Session 130 S2 — Community Submissions Scope

## Goal

Ship the missing community-submission UX on top of the existing marketplace
curation backend so operators can submit installed packs for review, inspect
quality/status, and resubmit when changes are requested.

## In Scope

- Submission UX for already-installed packs
- Surface current curation status in the frontend
- Show quality assessment and review notes
- Allow resubmission for `changes_requested` and `unlisted` states
- Refresh roadmap / handoff trackers to reflect PR `#413` merged and this slice
  active

## Non-Goals

- Admin review / approval / feature / verify / deprecate controls
- New backend curation or PackHub endpoints
- Broader community registry browsing beyond the existing marketplace UI
- Unrelated platform/docs cleanup

## Existing Surfaces

- `POST /v1/marketplace/curation/submit`
- `GET /v1/marketplace/curation/{name}`
- `GET /v1/marketplace/curation`
- `GET /v1/marketplace/quality/{name}`
- Existing marketplace frontend under `frontend/src/features/pack-marketplace/`

## Proposed Shape

- Extend the marketplace detail experience with a community-submission section
- Reuse the existing marketplace page and curation data instead of introducing a
  separate admin-style console
- Keep quality informational: display it clearly, but do not hard-block submit

## Validation

- `npx vitest run src/features/pack-marketplace/PackMarketplacePage.test.tsx --pool=forks --poolOptions.forks.singleFork --testTimeout=10000 --hookTimeout=10000`
- `npm run lint`
- `npm run build`
- `PYTHONPATH=C:\GitHub\repos\AGENT33\worktrees\session130-s2-community-submissions\engine\src pytest engine/tests/test_marketplace_curation.py --no-cov -q`

## Environment Notes

- The backend contract already exists on `main`; this should stay primarily
  frontend-first.
- On this Windows host, use the single-fork Vitest invocation above for reliable
  frontend test runs.
