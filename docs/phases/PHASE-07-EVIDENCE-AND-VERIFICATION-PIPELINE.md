# Phase 07: Evidence & Verification Pipeline

## Overview
- **Phase**: 07 of 20
- **Category**: Quality
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Formalize evidence capture and verification logging.
- Define primary vs secondary verification expectations.
- Extend test matrix guidance for agent tasks and partial runs.
- Create audit-friendly evidence storage conventions.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Evidence capture template with primary/secondary verification slots.
- Test matrix extensions for agentic workflows and partial runs.
- Verification log indexing and naming rules with artifact references.
- Example evidence entry in a session log.

## Acceptance Criteria
- [ ] Evidence templates are referenced in session wrap and handoff docs.
- [ ] Verification logs include commands, outputs, and artifact paths.
- [ ] Test matrix includes guidance for partial runs and minimal-diff checks.
- [ ] Primary vs secondary verification expectations are documented.

## Dependencies
- Phase 06

## Blocks
- Phase 08

## Orchestration Guidance
- QA agent reviews evidence consistency and artifact links.
- Orchestrator validates linkage between TASKS and verification logs.
- Reviewer confirms verification coverage for high-risk changes.

## Coding Direction
- Keep evidence formats lightweight and searchable.
- Avoid long narrative blocks; use structured lists.
- Ensure evidence paths are stable and predictable.
- Record command, output summary, and artifact path for each check.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
