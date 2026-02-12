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
- [x] 25-entry spec capability taxonomy (P/I/V/R/X) with human-readable catalog.
- [x] Agent definitions loaded from JSON at startup via configurable directory.
- [x] FastAPI search endpoints: by role, capability, category, status, agent ID.
- [x] Workflow executor bridge: definition registry fallback for invoke-agent steps.
- [x] Backward-compatible role mapping (worker->implementer, validator->qa).
- [x] 28 tests covering model, search, discover, routes, and workflow bridge.

## Dependencies
- Phase 10

## Blocks
- Phase 12

## Implementation Status
- **PR #21** merged 2026-02-12 — cherry-picked from stale `feat/phase-11-agent-registry`, rebased onto current main, added tests and input validation.
- Engine files: `agents/capabilities.py`, `agents/definition.py`, `agents/registry.py`, `api/routes/agents.py`, `workflows/actions/invoke_agent.py`, `main.py`, `config.py`
- Agent definitions: `orchestrator.json`, `director.json`, `worker.json`, `qa.json`, `researcher.json`, `browser-agent.json`
- Tests: `tests/test_agent_registry.py` (28 tests)

## Orchestration Guidance
- Architecture agent validates taxonomy consistency.
- Orchestrator confirms routing rules align to registry.
- Reviewer checks for completeness and clarity.

## Coding Direction
- Keep registry format lightweight and machine-readable.
- Avoid model-specific terminology.
- Prefer explicit ownership and accountability fields.

## Review Checklist
- [x] Interfaces/contracts reviewed and approved.
- [x] Tests/fixtures or evidence added.
- [x] Documentation updated and verified.
- [x] Scope remains within this phase only.
