# Session 65 Frontend Docker Build Context Fix

**Date:** 2026-03-09
**Scope:** Unblock the shared `build` CI check failing across the Session 64 PR stack.

## Problem

The frontend now imports canonical improvement-cycle workflow YAML directly from
`core/workflows/improvement-cycle/*.workflow.yaml` so the preset catalog stays
aligned with the backend source of truth. That works in a local checkout, but
the Docker build used by CI builds the frontend with `../frontend` as the build
context. The `core/` tree is therefore absent inside the image build context,
causing Vite to fail while resolving the raw YAML imports.

## Decision

Keep `core/workflows` as the source of truth and fix the container boundary
instead of copying the workflow YAML into the frontend package.

## Implementation

1. Change the frontend Docker Compose build context from `../frontend` to the
   repository root.
2. Point Compose at `frontend/Dockerfile`.
3. Update the Dockerfile to install and build from `/app/frontend` while also
   copying `core/` into `/app/core` so the existing relative imports remain
   valid.
4. Add a root `.dockerignore` to avoid sending worktrees, node modules, and
   other large generated directories into the new root-level build context.

## Why this shape

- No duplication of canonical workflow definitions.
- Local frontend development remains unchanged.
- CI and Docker builds now see the same canonical assets that local Vite builds
  already resolve.
- The fix is orthogonal to the active Phase 30-33 PRs, so it can be merged
  independently as a shared blocker cleanup.

## Validation target

- `npm run build` from `frontend/`
- `docker compose build frontend` from `engine/`
