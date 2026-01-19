# Phase 15: Review Automation & Two-Layer Review

## Overview
- **Phase**: 15 of 20
- **Category**: Quality
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Formalize two-layer review for high-risk work.
- Standardize reviewer roles and assignment rules.
- Improve review capture and signoff workflows.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Reviewer assignment matrix and rules.
- Two-layer review checklist and signoff guidance.
- Review capture template updates.

## Acceptance Criteria
- [x] High-risk tasks require reviewer signoff.
- [x] Reviewer assignment rules are documented.
- [x] Review capture includes required fixes and follow-ups.

## Key Artifacts
- `core/orchestrator/TWO_LAYER_REVIEW.md` - Two-layer review workflow, signoff flow
- `core/orchestrator/handoff/REVIEW_CHECKLIST.md` - Updated with two-layer references
- `core/orchestrator/handoff/REVIEW_CAPTURE.md` - Updated with L1/L2 sections

## Dependencies
- Phase 14

## Blocks
- Phase 16

## Orchestration Guidance
- Orchestrator enforces reviewer assignment.
- Reviewer validates evidence and risk triggers.
- QA agent confirms review artifacts are logged.

## Coding Direction
- Keep review artifacts short and structured.
- Require verification evidence with signoff.
- Avoid merging without explicit approval.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
