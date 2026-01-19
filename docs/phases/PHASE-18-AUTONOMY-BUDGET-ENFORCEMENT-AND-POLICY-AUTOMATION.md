# Phase 18: Autonomy Budget Enforcement & Policy Automation

## Overview
- **Phase**: 18 of 20
- **Category**: Governance
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Enforce autonomy budgets with preflight checks.
- Automate policy validation where feasible.
- Define stop conditions and escalation paths.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Preflight checklist for autonomy budget enforcement.
- Policy automation guidance and examples.
- Escalation and stop-condition rules.

## Acceptance Criteria
- [x] Autonomy budgets include command, file, and network scope.
- [x] Preflight enforcement steps are documented.
- [x] Stop conditions and escalation paths are explicit.

## Key Artifacts
- `core/orchestrator/AUTONOMY_ENFORCEMENT.md` - Preflight checks, enforcement, escalation
- `core/orchestrator/handoff/AUTONOMY_BUDGET.md` - Updated with enforcement reference

## Dependencies
- Phase 17

## Blocks
- Phase 19

## Orchestration Guidance
- Orchestrator validates autonomy budgets per task.
- Reviewer confirms enforcement evidence.
- QA agent checks policy logs.

## Coding Direction
- Enforce least privilege by default.
- Prefer deterministic enforcement rules.
- Keep policy automation transparent.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
