# Phase 11: Agent Registry & Capability Catalog

## Overview
- **Phase**: 11 of 20
- **Category**: Orchestration
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Define a canonical agent registry and capability taxonomy.
- Formalize role routing rules and ownership metadata.
- Provide onboarding guidance for new agents and roles.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Agent registry schema and baseline entries.
- Capability taxonomy and role metadata fields.
- Routing map updates tied to registry entries.
- Onboarding notes for new agent roles.

## Key Artifacts
- **Agent Registry**: `core/orchestrator/AGENT_REGISTRY.md` (10 agents, 25 capabilities, onboarding workflow)
- **Routing Map**: `core/orchestrator/AGENT_ROUTING_MAP.md` (registry references, escalation chains)

## Acceptance Criteria
- [x] Registry includes role, capabilities, constraints, and owner fields (AGT-001 to AGT-010).
- [x] Routing map references the registry entries (quick reference table with registry IDs).
- [x] Update workflow for adding agents is documented (Agent Onboarding section).

## Dependencies
- Phase 10

## Blocks
- Phase 12

## Orchestration Guidance
- Architecture agent validates taxonomy consistency.
- Orchestrator confirms routing rules align to registry.
- Reviewer checks for completeness and clarity.

## Coding Direction
- Keep registry format lightweight and machine-readable.
- Avoid model-specific terminology.
- Prefer explicit ownership and accountability fields.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
