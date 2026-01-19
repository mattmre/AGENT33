# Phase 14: Security Hardening & Prompt Injection Defense

## Overview
- **Phase**: 14 of 20
- **Category**: Security
- **Release Target**: TBD
- **Estimated Sprints**: TBD

## Objectives
- Codify sandboxing and approval gates for risky actions.
- Define prompt injection defenses and content sanitization.
- Standardize secrets handling and network allowlists.

## Scope Outline
- Planning: confirm requirements, inputs/outputs, and success metrics.
- Implementation: build minimal, composable components and integration seams.
- Validation: create deterministic checks and evidence.
- Documentation: add concise usage notes and examples.

## Deliverables
- Security control checklist for tooling and network access.
- Prompt injection defense guidance and red-team scenarios.
- Secrets handling and allowlist policy additions.

## Acceptance Criteria
- [x] Prompt injection controls are documented with examples.
- [x] Network and command allowlist governance is explicit.
- [x] Secrets handling guidance is documented.

## Key Artifacts
- `core/orchestrator/SECURITY_HARDENING.md` - Prompt injection defense, sandbox approvals, secrets handling
- `core/packs/policy-pack-v1/RISK_TRIGGERS.md` - Updated with prompt injection and sandbox triggers

## Dependencies
- Phase 13

## Blocks
- Phase 15

## Orchestration Guidance
- Security agent validates control coverage.
- Orchestrator ensures approvals are documented in TASKS.
- Reviewer confirms guidance is actionable.

## Coding Direction
- Default deny for network and tools.
- Require explicit approval for expanded permissions.
- Sanitize external inputs before use.

## Review Checklist
- [ ] Interfaces/contracts reviewed and approved.
- [ ] Tests/fixtures or evidence added.
- [ ] Documentation updated and verified.
- [ ] Scope remains within this phase only.
