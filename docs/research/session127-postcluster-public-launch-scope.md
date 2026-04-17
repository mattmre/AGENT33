# Session 127 Research Memo — POST-CLUSTER Public Launch Preparation

## Decision

Implement the first POST-CLUSTER slice as a **docs-first launch-preparation PR** with no runtime behavior changes.

## Why this scope

The roadmap explicitly calls out **"Public launch preparation (README as product page)"**. The strongest repo-backed gap is not missing backend capability; it is that the current top-level documentation does not present AGENT-33 as a coherent product to a new operator.

## Locked implementation surface

The slice should include:

1. Rewrite root `README.md` into a product-facing landing page
2. Add `docs/getting-started.md`
3. Add `docs/ONBOARDING.md`
4. Add `docs/RELEASE_CHECKLIST.md`
5. Refresh `docs/README.md`
6. Refresh `engine/README.md`
7. Refresh `frontend/README.md`
8. Sync roadmap/handoff docs so they point at the public-launch slice

## Non-goals

- No runtime/API behavior changes
- No new frontend features
- No deployment automation changes
- No pack marketplace/community submission implementation in this PR

## Required message to future sessions

Treat this PR as the launch-prep documentation foundation. The next POST-CLUSTER slices should build on these public/operator docs instead of reopening the same product-positioning work.
