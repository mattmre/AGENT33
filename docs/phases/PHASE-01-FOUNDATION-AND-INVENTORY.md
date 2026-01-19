# Phase 01: Foundation & Inventory

## Overview
- **Phase**: 01 of 10
- **Category**: Foundation
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Establish AGENT-33 baseline structure, logs, and governance artifacts.
- Validate ingest completeness and map sources to canonical targets.
- Define scope boundaries and evidence capture requirements for Phase 1 work.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Inventory summary by repo and asset type.
- Collision map and dedup rules aligned with `dedup-policy.md`.
- Initial phase logs and evidence capture format.
- Updated `docs/phase-planning.md` and phase index.

## Acceptance Criteria
- [ ] Inventory summary covers all collected repos.
- [ ] Collision list includes every suffixed variant with proposed canonical picks.
- [ ] Evidence capture format is documented and used in session logs.

## Dependencies
- None

## Blocks
- Phase 02

## Orchestration Guidance
- Assign a repo-audit agent to validate ingest completeness.
- Require evidence of inventory commands and outputs.
- Do not touch `collected/` contents.

## Coding Direction
- Prefer documentation updates over code changes in this phase.
- Keep changes minimal and auditable.
- Document open questions for Phase 2.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
