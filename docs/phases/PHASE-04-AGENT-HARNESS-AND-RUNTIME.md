# Phase 04: Agent Harness & Runtime

## Overview
- **Phase**: 04 of 10
- **Category**: Runtime
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Define a reproducible agent harness and initialization steps.
- Establish clean-state guarantees and progress logging.
- Codify command allowlists and sandbox expectations.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Initializer checklist (bootstrap, env validation, baseline checks).
- Progress log format and rotation guidance.
- Clean-state protocol and rollback expectations.

## Acceptance Criteria
- [ ] Initializer steps are documented with command examples.
- [ ] Progress logs include timestamps and task IDs.
- [ ] Clean-state rules are referenced in handoff docs.

## Dependencies
- Phase 03

## Blocks
- Phase 05

## Orchestration Guidance
- Assign a runtime agent to define harness steps.
- Review security constraints with a security-aware agent.
- Capture a sample session log with initializer output.

## Coding Direction
- Prefer scriptable steps over manual instructions.
- Avoid network access unless explicitly allowed.
- Document required environment variables.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
