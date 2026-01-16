# AGENT-33 Phase Planning

Purpose: Consolidate agentic workflows and orchestration assets into a canonical, reusable system for all projects.

## Vision
AGENT-33 is the master 'queen bee' repo that centralizes agentic workflows, orchestration templates, and governance patterns.

## Current State
- Raw ingest from multiple repos under `collected/`.
- Manifest recorded in `manifest.md`.
- Initial governance docs: `README.md`, `sync-plan.md`, `dedup-policy.md`.

## Phase 1: Inventory And Triage
- Validate completeness of `collected/` across all source repos.
- Normalize naming collisions (suffixes) into a tracking table.
- Identify candidate canonical files for `core/`.

## Phase 2: Canonicalization
- Create `core/` structure and move best-of versions.
- Record decisions in `core/CHANGELOG.md`.
- Map each canonical file back to its sources.

## Phase 3: Distribution
- Define sync rules for downstream repos.
- Create PR templates for controlled rollout.
- Automate sync using a script or checklist.

## Risks
- Drift between source repos and core canonical files.
- Overwriting project-specific nuances without review.

## Success Criteria
- A stable `core/` library with documented provenance.
- A repeatable ingest -> normalize -> distribute cycle.
- Downstream repos updated via controlled PRs.
