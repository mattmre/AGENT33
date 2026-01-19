# Phase 17: Evaluation Suite Expansion & Regression Gates

## Overview
- **Phase**: 17 of 20
- **Category**: Evaluation
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Expand golden task coverage and regression gates.
- Define gating thresholds for agent performance.
- Create a triage playbook for regressions.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Regression gate thresholds and enforcement guidance.
- Expanded golden task registry with tags and owners.
- Regression triage playbook.

## Acceptance Criteria
- [x] Gating thresholds are documented and versioned.
- [x] Triage playbook exists for failures.
- [x] Golden tasks are tagged for gating use.

## Key Artifacts
- `core/arch/REGRESSION_GATES.md` - Regression gates, triage playbook, golden task tags
- `core/arch/evaluation-harness.md` - Updated with regression gates reference

## Dependencies
- Phase 16

## Blocks
- Phase 18

## Orchestration Guidance
- Testing agent defines gating metrics.
- Orchestrator validates enforcement scope.
- Reviewer verifies triage clarity.

## Coding Direction
- Prefer deterministic gates over manual checks.
- Keep thresholds realistic and evidence-based.
- Track regressions with consistent tags.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
