# Session 55 — Phase 27: Operations Hub Cleanup & Domain Config Alignment

## Date

2026-03-06

## Scope

Operations Hub frontend/backend alignment and stale code removal.

## Problem Statement

The frontend operations hub domain config (`frontend/src/data/domains/operationsHub.ts`) contained endpoint paths that did not match the actual backend routes in `engine/src/agent33/api/routes/operations_hub.py`. Additionally, three legacy React components (`OperationsHub.tsx`, `ProcessList.tsx`, `ControlPanel.tsx`) used these stale paths via hardcoded `fetch()` calls and had been fully superseded by the unified `OperationsHubPanel.tsx` component.

## Backend Routes (Source of Truth)

From `engine/src/agent33/api/routes/operations_hub.py`:

| Endpoint | Method | Path | Scope |
|----------|--------|------|-------|
| Hub overview | GET | `/v1/operations/hub` | `workflows:read` |
| SSE stream | GET | `/v1/operations/stream` | `workflows:read` |
| Process detail | GET | `/v1/operations/processes/{process_id}` | `workflows:read` |
| Process control | POST | `/v1/operations/processes/{process_id}/control` | `workflows:execute` |

Router prefix: `/v1/operations`

## What Was Wrong

### Domain Config Mismatches

| Operation | Old Path (wrong) | Correct Path |
|-----------|-----------------|--------------|
| List/overview | `GET /v1/operations/processes` | `GET /v1/operations/hub` |
| Lifecycle control | `POST /v1/operations/processes/{process_id}/lifecycle` | `POST /v1/operations/processes/{process_id}/control` |
| Process detail | _(missing)_ | `GET /v1/operations/processes/{process_id}` |

The old domain config also lacked `defaultQuery` parameters for the hub overview endpoint (which supports `include`, `since`, `status`, `limit` query params) and used a non-standard `defaultPathParams` value (`agent-session-1234` instead of a placeholder).

### Stale Components

| File | Issue | Replacement |
|------|-------|-------------|
| `OperationsHub.tsx` | Composed `ProcessList` + `ControlPanel` with stale paths | `OperationsHubPanel.tsx` |
| `ProcessList.tsx` | Hardcoded `fetch()` to `GET /v1/operations/processes` | `OperationsHubPanel.tsx` via `api.ts` |
| `ControlPanel.tsx` | Hardcoded `fetch()` to `POST .../lifecycle` | `OperationsHubPanel.tsx` via `api.ts` |

Import chain before cleanup:
- `DomainPanel.tsx` → `OperationsHub.tsx` → `ProcessList.tsx` + `ControlPanel.tsx`
- `App.tsx` → `OperationsHubPanel.tsx` (correct, already using `api.ts`)

The `OperationsHubPanel.tsx` component (with its supporting `api.ts`, `helpers.ts`, `types.ts`) already uses the correct endpoints and was the active replacement.

## Changes Made

### 1. Domain Config (`operationsHub.ts`)

- **Fixed** hub overview: `GET /v1/operations/hub` with `defaultQuery` for `include` and `limit`
- **Added** process detail: `GET /v1/operations/processes/{process_id}`
- **Fixed** process control: `POST /v1/operations/processes/{process_id}/control` with `reason` field in body
- Updated operation IDs to be more descriptive (`operations-hub-overview`, `operations-process-detail`, `operations-process-control`)
- Used `replace-with-process-id` placeholder consistent with other domain configs

### 2. Stale Component Removal

- **`OperationsHub.tsx`**: Gutted and replaced with deprecation comment
- **`ProcessList.tsx`**: Gutted and replaced with deprecation comment
- **`ControlPanel.tsx`**: Gutted and replaced with deprecation comment
- **`DomainPanel.tsx`**: Removed `OperationsHub` import and the `{domain.id === "operations"}` conditional block

The `OperationsHubPanel.tsx`, `api.ts`, `helpers.ts`, `helpers.test.ts`, and `types.ts` files are **retained** — they are the active implementation.

### 3. Domain Config Tests

- Created `operationsHub.test.ts` following the established pattern from `componentSecurity.test.ts`
- Tests validate: domain ID, metadata, operation count, field presence, unique IDs, correct backend route mapping, valid default body, path params, and absence of stale paths

### 4. Improvement Cycle Templates

Created two improvement cycle workflow templates at `core/workflows/`:
- `improvement-cycle-retrospective.md` — Structured retrospective workflow for qualitative session review
- `improvement-cycle-metrics-review.md` — Periodic quantitative metrics review workflow

Both follow the existing workflow template format used in `core/workflows/commands/` and `core/workflows/skills/`.

> **Note**: The intended final location is `core/workflows/improvement-cycle/` as a subdirectory. The files include a header noting this. They can be moved once the directory is created.

## Files Modified

| File | Action |
|------|--------|
| `frontend/src/data/domains/operationsHub.ts` | Updated — fixed all endpoint paths |
| `frontend/src/components/DomainPanel.tsx` | Updated — removed stale OperationsHub import/usage |
| `frontend/src/features/operations-hub/OperationsHub.tsx` | Deprecated — replaced with comment |
| `frontend/src/features/operations-hub/ProcessList.tsx` | Deprecated — replaced with comment |
| `frontend/src/features/operations-hub/ControlPanel.tsx` | Deprecated — replaced with comment |
| `frontend/src/data/domains/operationsHub.test.ts` | Created — domain config tests |
| `core/workflows/improvement-cycle-retrospective.md` | Created — retro template |
| `core/workflows/improvement-cycle-metrics-review.md` | Created — metrics review template |
| `docs/research/session55-phase27-hub-alignment.md` | Created — this document |

## Verification

- `api.ts` endpoints already matched backend (confirmed: `/v1/operations/hub`, `/v1/operations/processes/{process_id}`, `/v1/operations/processes/{process_id}/control`)
- `helpers.test.ts` existing tests remain valid — they test helper functions, not API paths
- No other files import the removed components (verified via grep)
- TypeScript type-check passes with `npx tsc --noEmit`

## Risk Assessment

- **Low risk**: The stale components were already non-functional (calling endpoints that don't exist in the backend)
- **No breaking changes**: `OperationsHubPanel.tsx` in `App.tsx` is the active UI and is untouched
- **Domain config** is now aligned with backend — the explorer panel will call correct endpoints
