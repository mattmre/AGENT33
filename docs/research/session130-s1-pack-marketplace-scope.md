# Session 130 S1 — Pack Marketplace Web UI Scope

## Goal

Ship the missing frontend marketplace surface on top of the existing backend
contract so operators can browse marketplace packs, inspect curation/trust
state, and install packs from the web UI.

## Scope Lock

### In scope

- Add a first-class `Marketplace` tab to the frontend app shell
- Render marketplace pack summaries from `/v1/marketplace/packs`
- Filter locally by search text and category
- Enrich the UI with:
  - featured packs from `/v1/marketplace/featured`
  - curation state from `/v1/marketplace/curation`
  - installed state from `/v1/packs`
  - trust posture from `/v1/packs/{name}/trust`
- Provide a detail panel with version selection
- Install a selected marketplace version through `POST /v1/marketplace/install`
- Add focused frontend coverage for the new page

### Explicit non-goals

- Community submission / approval flows
- Admin curation controls
- New backend marketplace endpoints
- Broader trust dashboard or enablement-matrix UX
- Unrelated docs cleanup

## Design Notes

- The backend marketplace APIs already exist on `main`, so the safest slice is
  frontend-first.
- The page uses client-side filtering over the marketplace list instead of
  introducing new search/category wiring in the backend.
- Featured and curation calls are optional enrichments; failure there should not
  block the core marketplace list.
- Pack cards must keep native button semantics for accessibility and for
  reliable Testing Library queries.

## Validation

- `npx vitest run src/features/pack-marketplace/PackMarketplacePage.test.tsx --pool=forks --poolOptions.forks.singleFork --testTimeout=10000 --hookTimeout=10000`
- `npm run lint`
- `npm run build`

## Environment Caveat

On this Windows host, Vitest's default worker pool can hang for this spec. The
single-fork invocation above is the stable local command for reruns.
