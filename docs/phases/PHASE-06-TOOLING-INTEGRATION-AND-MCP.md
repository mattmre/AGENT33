# Phase 06: Tooling Integration & MCP

## Overview
- **Phase**: 06 of 10
- **Category**: Tooling
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Define MCP discovery and tool registry practices.
- Create tools-as-code guidance to minimize schema bloat.
- Document tool trust and provenance requirements.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- MCP registry guidance and allowlist policy.
- Tools-as-code workflow notes and example structure.
- Tool provenance checklist for new integrations.

## Acceptance Criteria
- [ ] Tool discovery process is documented with governance checkpoints.
- [ ] Tools-as-code guidance specifies progressive disclosure practices.
- [ ] Provenance checklist is referenced in integration workflows.

## Dependencies
- Phase 05

## Blocks
- Phase 07

## Orchestration Guidance
- Architecture agent validates MCP governance alignment.
- Testing agent defines how to validate tool integrations.
- Record decisions for any new tooling assumptions.

## Coding Direction
- Keep integration guidance model-agnostic.
- Avoid endorsing specific vendors unless required.
- Make network access opt-in and explicit.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.

## References
- `core/orchestrator/TOOL_GOVERNANCE.md`
- `core/orchestrator/TOOLS_AS_CODE.md`
