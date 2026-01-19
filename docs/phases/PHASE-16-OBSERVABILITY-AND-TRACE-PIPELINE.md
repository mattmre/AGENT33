# Phase 16: Observability & Trace Pipeline

## Overview
- **Phase**: 16 of 20
- **Category**: Observability
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Define a trace schema for agent runs.
- Standardize logs, artifacts, and failure taxonomy.
- Enable audit-friendly run reconstruction.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Trace schema (run id, task id, commands, outputs, artifacts).
- Failure taxonomy and classification guidance.
- Artifact retention and storage rules.

## Acceptance Criteria
- [x] Trace schema documented and referenced in logs.
- [x] Failure taxonomy is defined with examples.
- [x] Artifact storage paths are standardized.

## Key Artifacts
- `core/orchestrator/TRACE_SCHEMA.md` - Trace schema, failure taxonomy, artifact retention
- `core/orchestrator/handoff/EVIDENCE_CAPTURE.md` - Updated with trace references

## Dependencies
- Phase 15

## Blocks
- Phase 17

## Orchestration Guidance
- QA agent validates log completeness.
- Orchestrator ensures trace ids are recorded in TASKS.
- Reviewer checks auditability of runs.

## Coding Direction
- Use stable identifiers and predictable paths.
- Keep logs machine-readable when possible.
- Capture failures with actionable tags.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
