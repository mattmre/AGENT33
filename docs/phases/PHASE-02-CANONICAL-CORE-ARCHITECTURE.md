# Phase 02: Canonical Core Architecture

## Overview
- **Phase**: 02 of 10
- **Category**: Core
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Define canonical layout rules for `core/`.
- Promote reusable assets into core with provenance tracking.
- Establish change log discipline for canonicalization decisions.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Core layout guide and ownership notes.
- Promoted canonical files with source mapping.
- Updated `core/CHANGELOG.md` entries with rationale.

## Acceptance Criteria
- [ ] Every promoted file lists sources and rationale.
- [ ] Core layout is documented and referenced from indexes.
- [ ] No content changes in `collected/`.

## Dependencies
- Phase 01

## Blocks
- Phase 03

## Orchestration Guidance
- Use a canonization checklist with reviewer signoff.
- Lock scope to high-value assets first (orchestration, templates).
- Log all file moves/promotions.

## Coding Direction
- Avoid functional changes to canonical content unless required.
- Prefer copying over refactoring when consolidating.
- Keep decisions logged in `core/CHANGELOG.md`.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
