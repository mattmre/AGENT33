# Phase 08: Evaluation & Benchmarking

## Overview
- **Phase**: 08 of 20
- **Category**: Evaluation
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Define internal evaluation suites for agent regressions.
- Establish golden tasks and golden diffs for comparison.
- Add golden PR/issue cases to track review quality and diff size.
- Track success rate, time-to-green, rework, and diff-size metrics.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Golden task list with expected outcomes.
- Golden PR/issue cases with expected diffs or acceptance checks.
- Metric definitions and reporting template.
- Evaluation execution playbook with baseline capture steps.

## Key Artifacts
- **Evaluation Harness**: `core/arch/evaluation-harness.md` (golden tasks, cases, metrics, playbook)
- **Evaluation Report Template**: `core/arch/evaluation-report-template.md`
- **Evidence Capture Reference**: `core/orchestrator/handoff/EVIDENCE_CAPTURE.md`

## Acceptance Criteria
- [x] At least 5 golden tasks are defined with expected results (GT-01 through GT-07: 7 tasks).
- [x] At least 3 golden PR/issue cases are defined with acceptance checks (GC-01 through GC-04: 4 cases).
- [x] Metrics list includes success rate, time-to-green, rework, and diff size (M-01 through M-05: 5 metrics).
- [x] Evaluation playbook references evidence capture and baseline runs.

## Dependencies
- Phase 07

## Blocks
- Phase 09

## Orchestration Guidance
- Testing agent designs evaluation harness structure.
- Architecture agent reviews metric relevance.
- Capture initial baseline measurements and store artifacts.

## Coding Direction
- Prefer deterministic tasks with stable outputs.
- Keep evaluation tooling lightweight and scriptable.
- Record baseline results before optimization.
- Preserve golden artifacts for regression checks.

## Review Checklist
- [x] Interfaces/contracts reviewed and approved.
- [x] Tests/fixtures or evidence added.
- [x] Documentation updated and verified.
- [x] Scope remains within this phase only.
