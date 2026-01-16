# Release Notes - 2026-01-16

## Summary
- Established a model-agnostic orchestration system with clear roles, handoff protocol, and evidence capture.
- Consolidated canonical documentation in `core/` and linked entrypoints across orchestration and AEP workflows.
- Added workflow promotion criteria and sources index for reusable CI templates.

## Highlights
- Orchestrator handoff: PLAN, TASKS, STATUS, DECISIONS, PRIORITIES, DoD, review and evidence templates.
- Role system: Director, Orchestrator, Worker (Impl/QA), Reviewer, Researcher, Documentation.
- Operator tooling: cheat sheet, routing map, escalation paths, glossary, session wrap.

## Entry Points
- `core/ORCHESTRATION_INDEX.md`
- `core/orchestrator/README.md`
- `core/arch/workflow.md`
- `core/workflows/README.md`
