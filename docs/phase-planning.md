# AGENT-33 Phase Planning

Purpose: Consolidate agentic workflows and orchestration assets into a canonical, reusable system for all projects.

## Vision
AGENT-33 is the master 'queen bee' repo that centralizes agentic workflows, orchestration templates, and governance patterns.

## Current State
- Raw ingest from multiple repos under `collected/`.
- Manifest recorded in `manifest.md`.
- Initial governance docs: `README.md`, `sync-plan.md`, `dedup-policy.md`.
- Generic phase templates available in `core/phases/README.md` and `core/phases/PHASE-*.md`.

## Phase 1: Foundation & Inventory
- Validate completeness of `collected/` across all source repos.
- Normalize naming collisions (suffixes) into a tracking table.
- Identify candidate canonical files for `core/`.

## Phase 2: Canonical Core Architecture
- Create `core/` structure and promote best-of versions.
- Record decisions in `core/CHANGELOG.md`.
- Map each canonical file back to its sources.

## Phase 3: Spec-First Orchestration Workflow
- Standardize PLAN/TASKS/STATUS/DECISIONS/PRIORITIES workflow.
- Define acceptance checks and autonomy budgets for agent tasks.
- Align evidence-first execution with templates.

## Phase 4: Agent Harness & Runtime
- Define initializer steps, progress logs, and clean-state guarantees.
- Document sandbox and command allowlist expectations.
- Capture baseline harness evidence.

## Phase 5: Policy Pack & Risk Triggers
- Build portable policy pack for downstream sync.
- Extend risk triggers for prompt injection, sandbox escape, secrets, supply chain.
- Update promotion criteria with evidence requirements.

## Phase 6: Tooling Integration & MCP
- Define MCP discovery and tool registry governance.
- Document tools-as-code and progressive disclosure guidance.
- Establish tool provenance checklist.

## Phase 7: Evidence & Verification Pipeline
- Formalize evidence capture templates and verification log indexing.
- Extend test matrix guidance for agent workflows.
- Align session wrap and handoff templates with evidence capture.

## Phase 8: Evaluation & Benchmarking
- Define golden tasks and regression metrics.
- Establish evaluation harness and baseline measurements.
- Track success rate, time-to-green, and rework metrics.

## Phase 9: Distribution & Sync
- Define sync rules for downstream repos.
- Create PR templates for controlled rollout.
- Automate sync checks or playbooks.

## Phase 10: Governance & Community
- Define contribution standards, review roles, and escalation paths.
- Document maintenance cadence and onboarding guidance.

## Phase 11: Agent Registry & Capability Catalog
- Define agent registry schema and capability taxonomy.
- Update routing map to reference registry entries.
- Document onboarding steps for new agent roles.

## Phase 12: Tool Registry Operations & Change Control
- Establish tool registry operations with versioning and ownership.
- Add change control, deprecation, and rollback guidance.
- Tie allowlist updates to registry changes.

## Phase 13: Code Execution Layer & Tools-as-Code Integration
- Define execution layer contract and adapter patterns.
- Document progressive disclosure for tool schemas.
- Capture deterministic execution and caching guidance.

## Phase 14: Security Hardening & Prompt Injection Defense
- Document sandboxing, approvals, and allowlists.
- Add prompt injection defenses and sanitization guidance.
- Standardize secrets handling expectations.

## Phase 15: Review Automation & Two-Layer Review
- Formalize two-layer review for high-risk changes.
- Document reviewer assignment rules and signoff workflow.
- Update review capture guidance.

## Phase 16: Observability & Trace Pipeline
- Define trace schema, artifact paths, and failure taxonomy.
- Standardize run identifiers and audit trail requirements.

## Phase 17: Evaluation Suite Expansion & Regression Gates
- Expand golden tasks and define regression gates.
- Create triage playbook for evaluation failures.

## Phase 18: Autonomy Budget Enforcement & Policy Automation
- Define preflight enforcement for autonomy budgets.
- Automate policy checks where feasible.
- Codify stop conditions and escalation paths.

## Phase 19: Release & Sync Automation
- Define release cadence and sync automation with dry-run steps.
- Add rollback procedures and release notes guidance.

## Phase 20: Continuous Improvement & Research Intake
- Establish research intake and periodic roadmap refresh.
- Capture lessons learned and update governance artifacts.

## Phase 21: Extensibility Patterns Integration
- Integrate proven extensibility patterns from research dossiers.
- Add relationship typing, provenance, and change event documentation.
- Keep improvements documentation-first and model-agnostic.

## Phase 22: Unified UI Platform & Access Layer
- Deliver a first-party AGENT-33 frontend with full API domain coverage.
- Provide easy human operation flows and token/API-key service access.
- Ship containerized local/VPS deployment and full end-to-end verification.
- Status: Completed on 2026-02-16 (see `docs/progress/phase-22-ui-log.md`).

## Phase Template Guidance (Generic)
Use the generic phase templates in `core/phases/` for structure, and the AGENT-33 phase plans in `docs/phases/` for sequencing:
- Start with `docs/phases/README.md` to select the next phase.
- Each phase file contains objectives, deliverables, acceptance criteria, orchestration guidance, and coding direction.
- Keep phase scope tight and avoid cross-phase feature creep.
- Record evidence for each phase outcome (commands, tests, outputs).

## Orchestration Alignment
- Use `core/ORCHESTRATION_INDEX.md` as the entry point for handoff protocols.
- Track tasks in `core/orchestrator/handoff/TASKS.md` with acceptance criteria and verification steps.
- Log verification evidence in `core/arch/verification-log.md` (or per-cycle logs when active).

## Risks
- Drift between source repos and core canonical files.
- Overwriting project-specific nuances without review.

## Success Criteria
- A stable `core/` library with documented provenance.
- A repeatable ingest -> normalize -> distribute cycle.
- Downstream repos updated via controlled PRs.
