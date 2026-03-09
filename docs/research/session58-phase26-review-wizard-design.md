# Session 58 – Phase 26 Review Wizard Design

**Date:** 2026-03-08  
**Scope:** Phase 26 Stage 3 approval flows and Phase 27 wizard UX completion  
**Branch:** `codex/session58-phase26-wizard`

## Problem

The current frontend exposes the raw explanation, review, and tool-approval endpoints, but operators still have to manually stitch them together. That leaves the "plan-review/diff-review approval flow" and "improvement-cycle wizard" backlog items effectively incomplete even though the underlying routes exist.

The missing deliverable is a guided frontend path that:

1. generates a review artifact (`plan-review` or `diff-review`);
2. creates a review record that retains linkage to that artifact;
3. advances the review through the actual L1/L2 approval lifecycle; and
4. surfaces pending tool approvals in the same operator workflow.

## Existing Constraints

- Phase 27 preset wiring already exists on top of PR `#150`, so the wizard should build on that work rather than re-implementing workflow preset selection.
- `ReviewRecord` currently stores only `task_id`, `branch`, and `pr_number`; it does not persist any link back to the explanation artifact.
- Tool approvals already have list/get/decision APIs, but there is no frontend surface integrating them into the review workflow.

## Design Decision

### 1. Add review artifact linkage in the backend

Extend `ReviewRecord` with a lightweight `artifacts` collection so the frontend can create reviews that persist references to generated explanation artifacts.

Proposed shape:

```json
{
  "kind": "explanation",
  "artifact_id": "expl-123",
  "label": "plan-review",
  "mode": "plan_review"
}
```

This avoids a shallow client-only implementation where the relationship is lost as soon as the page reloads.

### 2. Add a dedicated `ImprovementCycleWizard` frontend panel

Render a custom wizard panel within the `workflows` domain in the advanced control plane. The workflow domain is the right anchor because:

- Phase 27 presets already live there;
- the operator starts from a workflow/improvement-cycle context; and
- it avoids scattering a single guided flow across three technical domains.

### 3. Wizard stages

The wizard should expose four concrete stages:

1. **Artifact**
   - choose `plan_review` or `diff_review`
   - optionally apply an improvement-cycle preset
   - generate an explanation artifact and preview it inline

2. **Review Draft**
   - create a review record linked to the explanation artifact
   - assess risk with explicit trigger selection

3. **Signoff**
   - mark ready
   - assign L1
   - submit L1 decision
   - if required, assign and submit L2
   - finalize approval and merge

4. **Tool Approvals**
   - list pending tool approvals
   - approve or reject them without leaving the workflow

### 4. Testing strategy

Frontend DOM tests should verify:

- generating a plan-review artifact and creating a linked review;
- the L2 branch becoming active for a high-risk review; and
- pending tool approvals being listed and actionable.

Backend tests should verify:

- `ReviewService.create()` persists artifacts;
- the review create API accepts and returns artifacts; and
- existing review flows remain intact.

## Non-Goals

- Building a brand-new backend workflow orchestration endpoint for the wizard.
- Replacing raw operation cards; the wizard complements them.
- Persisting a stronger relational model than the minimal artifact link needed for operator continuity.

## Follow-On Work

- Phase 25/26 docs should document the new guided flow after implementation.
- Phase 22 validation should exercise the new wizard surface in addition to the raw endpoint cards.
