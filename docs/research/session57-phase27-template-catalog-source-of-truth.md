# Session 57 Phase 27 Stage 3A — Template Catalog Source of Truth

**Date:** 2026-03-06  
**Scope:** Canonical improvement-cycle templates plus lightweight frontend preset wiring.

## Problem

Phase 27 Stage 3 is still missing a practical launch path. The repo has draft markdown guidance for improvement-cycle workflows, but it does not yet have canonical executable workflow definitions under `core/workflows/improvement-cycle/`, and the frontend has no preset wiring that lets an operator instantiate those templates without hand-authoring JSON.

## Decisions

1. **Split Stage 3 into a smaller Stage 3A PR.**
   - This PR will deliver canonical template files plus preset wiring in the existing workflow create/execute UX.
   - The full wizard, backend template catalog, and broader approval/review orchestration stay out of scope for a later Stage 3B follow-up.

2. **Stack on top of PR #149.**
   - Preset wiring is likely to touch `frontend/src/components/OperationCard.tsx`, which already changed in PR #149.
   - Stacking on `feat/session57-wave1-pr2-phase25-sse-graph-refresh` reduces conflict risk and keeps workflow UX changes aligned.

3. **Make YAML the authoritative source of truth.**
   - Canonical workflow definitions will live in `core/workflows/improvement-cycle/*.workflow.yaml`.
   - Frontend preset metadata is a temporary projection of those canonical files until a backend template catalog exists.

4. **Keep the templates deterministic and executable today.**
   - Stage 3A templates should use only actions that already execute safely in the engine.
   - Avoid LLM/tool/network-heavy flows in this PR; prefer scaffold-oriented, deterministic workflow steps.

5. **Do not overbuild the UI.**
   - Add explicit preset controls to the existing workflow create/execute cards.
   - Preserve raw JSON editing and require an explicit “Apply preset” action instead of auto-overwriting user input.

## Planned Deliverables

### Canonical assets
- `core/workflows/improvement-cycle/README.md`
- `core/workflows/improvement-cycle/retrospective.workflow.yaml`
- `core/workflows/improvement-cycle/metrics-review.workflow.yaml`
- redirect/deprecation updates for:
  - `core/workflows/improvement-cycle-retrospective.md`
  - `core/workflows/improvement-cycle-metrics-review.md`

### Frontend preset wiring
- `frontend/src/features/improvement-cycle/presets.ts`
- small preset controls in `frontend/src/components/OperationCard.tsx`
- workflow domain/config updates so the create and execute cards expose preset-aware UX hints

### Tests
- engine tests that load and validate the canonical workflow YAML files
- frontend tests for preset builders and preset application behavior

## Risks

- **Template drift:** frontend presets can drift from the YAML files until a backend catalog exists.
- **Stack dependency:** if PR #149 rebases, this PR must rebase as well.
- **Old doc references:** the existing markdown draft files may still be linked elsewhere, so they should become redirect stubs instead of being removed outright.

## Acceptance Criteria

1. Two canonical improvement-cycle workflow definitions exist and validate successfully.
2. The workflows create/execute UX can apply those templates as presets without manual JSON authoring.
3. The preset workflow names align with the canonical YAML definitions.
4. Tests lock the YAML shape and the preset wiring behavior.
