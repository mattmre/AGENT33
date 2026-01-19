# Phase 16: Source Parser H

## Overview
- **Phase**: 16 of 40
- **Category**: Ingestion
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Implement source adapters that map to canonical models.
- Handle malformed inputs with structured errors.
- Provide deterministic outputs with fixtures.
- Focus: Parser emphasizing large-volume performance.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic tests and fixtures, capture evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Parser implementation with options.
- Fixtures and golden outputs.
- Normalization rules and edge-case docs.

## Acceptance Criteria
- [ ] Outputs match goldens deterministically.
- [ ] Edge cases are covered by tests.
- [ ] Normalization rules are documented.

## Dependencies
- Phase 15

## Blocks
- Phase 17

## Orchestration Guidance
- Collect representative inputs before coding.
- Split parsing, normalization, and tests into tasks.
- Record performance metrics for large fixtures.

## Coding Direction
- Keep outputs order-stable.
- Isolate source quirks behind helpers.
- Validate and normalize explicitly.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures added with evidence.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
