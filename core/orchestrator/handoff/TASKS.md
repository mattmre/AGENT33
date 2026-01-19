# TASKS

## Queue (unassigned)
- [ ] T1: Create/update orchestration protocol files in repo and validate Qwen Code tool usage.
- [ ] T2: Add warmup/pin script and confirm model stays hot for 30+ minutes.
- [ ] T3: Run a small "real task" in this repo (e.g., improve scripts, README, add diagnostics).

## Phase 3-8 Queue (assigned)
- [ ] T8 (Phase 5): Policy pack v1 skeleton
  - Owner: Documentation Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Policy pack directory created with required files: AGENTS, ORCHESTRATION, EVIDENCE, RISK_TRIGGERS, ACCEPTANCE_CHECKS, PROMOTION_GUIDE.
    - All files are model-agnostic and repo-agnostic.
  - Verification steps:
    - Directory listing and file presence check recorded.
  - Reviewer required: yes (governance)
- [ ] T9 (Phase 5): Risk triggers extension (agentic security)
  - Owner: Security Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Risk triggers include prompt injection, sandbox escape, secrets, supply chain.
    - Review checklist references updated risk triggers.
  - Verification steps:
    - Confirm updates in risk trigger file and checklist references.
  - Reviewer required: yes (security)
- [ ] T10 (Phase 5): Promotion criteria update (traceability)
  - Owner: Architect Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Promotion criteria require rationale, acceptance checks, evidence compliance, security notes.
  - Verification steps:
    - Confirm changes in `core/workflows/PROMOTION_CRITERIA.md`.
  - Reviewer required: no

- [x] T11 (Phase 6): MCP/tool registry governance
  - Owner: Architect Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Tool discovery allowlist policy documented.
    - Provenance checklist defined for tools/MCP servers.
  - Verification steps:
    - Doc review and cross-links from orchestration guidance.
  - Reviewer required: yes (architecture)
- [x] T12 (Phase 6): Tools-as-code guidance
  - Owner: Project Engineering Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Progressive disclosure guidance documented.
    - Example tools-as-code folder structure provided.
  - Verification steps:
    - Confirm doc is linked from phase planning and orchestration index.
  - Reviewer required: no

- [x] T13 (Phase 7): Evidence capture + verification log alignment
  - Owner: QA/Reporter Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Evidence templates updated to require commands, outputs, artifacts, diff summary.
    - Verification log indexing updated with usage guidance for partial runs.
  - Verification steps:
    - Evidence template referenced in session wrap and handoff docs.
  - Reviewer required: no
  - Evidence: `core/orchestrator/handoff/EVIDENCE_CAPTURE.md` (primary/secondary verification, diff summary added), `core/arch/verification-log.md` (partial run guidance added), `core/orchestrator/handoff/SESSION_WRAP.md` (references evidence template)
- [x] T14 (Phase 7): Test matrix extension for agent workflows
  - Owner: Test Engineer
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Test matrix includes guidance for agentic tasks and partial test runs.
  - Verification steps:
    - Confirm updates in `core/arch/test-matrix.md`.
  - Reviewer required: no
  - Evidence: `core/arch/test-matrix.md` (agentic task guidance, agent-specific test selection, partial run protocol added)

- [ ] T15 (Phase 8): Evaluation harness + golden tasks plan
  - Owner: Architect Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Golden task list defined with expected outcomes.
    - Metrics list includes success rate, time-to-green, rework rate, diff size.
  - Verification steps:
    - Doc review for evaluation plan and cross-links in phase planning.
  - Reviewer required: yes (architecture)
- [ ] T16 (Phase 8): Baseline evaluation reporting template
  - Owner: QA/Reporter Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Reporting template includes metrics, evidence, and outcome summary.
  - Verification steps:
    - Template referenced from evaluation phase docs.
  - Reviewer required: no

## Phase 11-20 Queue (assigned)
- [ ] T17 (Phase 11): Agent registry schema + capability taxonomy
  - Owner: Architect Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Registry includes role, capabilities, constraints, and owner fields.
    - Capability taxonomy is defined and documented.
  - Verification steps:
    - Registry and taxonomy referenced from routing map.
  - Reviewer required: yes (architecture)
- [ ] T18 (Phase 11): Routing map + onboarding updates
  - Owner: Project Engineering Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Routing map references registry entries.
    - Onboarding steps for new roles documented.
  - Verification steps:
    - Links validated from orchestrator README or operator manual.
  - Reviewer required: no
- [ ] T19 (Phase 12): Tool registry change control
  - Owner: Security Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Change control checklist defined.
    - Provenance and allowlist update flow documented.
  - Verification steps:
    - Checklist referenced in tool governance docs.
  - Reviewer required: yes (security)
- [ ] T20 (Phase 12): Deprecation + rollback guidance
  - Owner: Documentation Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Deprecation workflow documented.
    - Rollback steps defined and linked.
  - Verification steps:
    - Guidance referenced from tool registry operations doc.
  - Reviewer required: no
- [ ] T21 (Phase 13): Code execution contract + adapter template
  - Owner: Runtime Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Execution contract defines inputs, outputs, and sandbox limits.
    - Adapter template documented with example.
  - Verification steps:
    - References added in tools-as-code guidance.
  - Reviewer required: yes (runtime)
- [ ] T22 (Phase 14): Prompt injection defenses + sandbox approvals
  - Owner: Security Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Prompt injection defenses documented with examples.
    - Approval gates for risky actions documented.
  - Verification steps:
    - Risk trigger references updated if needed.
  - Reviewer required: yes (security)
- [ ] T23 (Phase 15): Two-layer review checklist + signoff flow
  - Owner: QA/Reporter Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Reviewer assignment rules documented.
    - Two-layer review checklist added.
  - Verification steps:
    - Review capture template references new checklist.
  - Reviewer required: yes (QA)
- [ ] T24 (Phase 16): Trace schema + artifact retention rules
  - Owner: QA/Reporter Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Trace schema defined with run/task ids and artifacts.
    - Retention rules documented.
  - Verification steps:
    - Trace schema referenced in session logs guidance.
  - Reviewer required: no
- [ ] T25 (Phase 17): Regression gates + triage playbook
  - Owner: Test Engineer
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Regression gates documented with thresholds.
    - Triage playbook created.
  - Verification steps:
    - Evaluation docs reference regression gates.
  - Reviewer required: no
- [ ] T26 (Phase 18): Autonomy budget enforcement
  - Owner: Project Engineering Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Preflight enforcement steps documented.
    - Stop conditions and escalation paths explicit.
  - Verification steps:
    - Autonomy budget template references enforcement.
  - Reviewer required: yes (governance)
- [ ] T27 (Phase 19): Release cadence + sync automation plan
  - Owner: Documentation Agent
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Release cadence documented.
    - Sync automation plan includes dry-run step.
  - Verification steps:
    - Distribution docs reference release plan.
  - Reviewer required: no
- [ ] T28 (Phase 20): Research intake + continuous improvement
  - Owner: Orchestrator
  - Start date: 2026-01-16
  - Acceptance criteria:
    - Research intake template exists.
    - Continuous improvement cadence documented.
  - Verification steps:
    - References added in phase planning docs.
  - Reviewer required: no

## In Progress
- [ ] (agent) T#: status / notes / blockers

## Done
- [x] Bootstrap orchestration files created (this commit)
- [x] T4 (Phase 3): Spec-first workflow consolidation (spec-first checklist + handoff links; review pending)
  - Evidence: `core/orchestrator/handoff/SPEC_FIRST_CHECKLIST.md`, `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-3.md`
- [x] T5 (Phase 3): Autonomy budget + escalation guidance (autonomy template + handoff links; review pending)
  - Evidence: `core/orchestrator/handoff/AUTONOMY_BUDGET.md`, `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-3.md`
- [x] T6 (Phase 4): Harness initializer + clean-state protocol (initializer doc; review pending)
  - Evidence: `core/orchestrator/handoff/HARNESS_INITIALIZER.md`, `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-4.md`
- [x] T7 (Phase 4): Progress log format + rotation guidance (progress log format doc)
  - Evidence: `core/orchestrator/handoff/PROGRESS_LOG_FORMAT.md`, `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-4.md`

## Phase 5 Progress
- [x] T8 (Phase 5): Policy pack v1 skeleton
  - Evidence: `core/packs/policy-pack-v1/AGENTS.md`, `core/packs/policy-pack-v1/ORCHESTRATION.md`, `core/packs/policy-pack-v1/EVIDENCE.md`, `core/packs/policy-pack-v1/RISK_TRIGGERS.md`, `core/packs/policy-pack-v1/ACCEPTANCE_CHECKS.md`, `core/packs/policy-pack-v1/PROMOTION_GUIDE.md`
- [x] T9 (Phase 5): Risk triggers extension (agentic security)
  - Evidence: `core/packs/policy-pack-v1/RISK_TRIGGERS.md`, `core/orchestrator/handoff/REVIEW_CHECKLIST.md`
- [x] T10 (Phase 5): Promotion criteria update (traceability)
  - Evidence: `core/workflows/PROMOTION_CRITERIA.md`

## Phase 6 Progress
- [x] T11 (Phase 6): MCP/tool registry governance
  - Evidence: `core/orchestrator/TOOL_GOVERNANCE.md`, `core/ORCHESTRATION_INDEX.md`
- [x] T12 (Phase 6): Tools-as-code guidance
  - Evidence: `core/orchestrator/TOOLS_AS_CODE.md`, `core/ORCHESTRATION_INDEX.md`

## Phase 7 Progress
- [x] T13 (Phase 7): Evidence capture + verification log alignment
  - Evidence: `core/orchestrator/handoff/EVIDENCE_CAPTURE.md`, `core/arch/verification-log.md`, `core/orchestrator/handoff/SESSION_WRAP.md`
- [x] T14 (Phase 7): Test matrix extension for agent workflows
  - Evidence: `core/arch/test-matrix.md`, `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-7.md`

## Review-to-Backlog Checklist
- Capture review inputs in `handoff/REVIEW_CAPTURE.md` when required.
- Triage findings and assign severity tags.
- Decide accept/defer/reject with rationale.
- Convert accepted findings into TASKS entries with acceptance criteria + verification.
- Record evidence in `core/arch/verification-log.md`.

## Task Template
When you pick a task:
1) Create branch: 	ask/T#-short-name
2) Update TASKS.md In Progress line with your agent name + timestamp
3) Implement minimal changes
4) Run checks/tests (or explain why not possible)
5) Capture reviewer output (if risk triggers apply) using `handoff/REVIEW_CAPTURE.md`
6) Confirm Definition of Done checklist: `handoff/DEFINITION_OF_DONE.md`
7) Commit with message: T#: <summary>
8) Update TASKS Done with summary + commit hash + verification evidence

## Minimum Task Payload
- ID and title
- Owner and start date
- Acceptance criteria
- Verification steps
- Spec-first checklist reference (`handoff/SPEC_FIRST_CHECKLIST.md`)
- Autonomy budget (when scope or risk warrants) (`handoff/AUTONOMY_BUDGET.md`)
- Reviewer required (yes/no)

## Acceptance Criteria Examples
- "CLI command exits 0 and produces expected output file."
- "Unit tests for module X pass; new test covers edge case Y."
- "Documentation updated for new flag; examples added."

## Status Update Template
- Status:
- Progress:
- Blockers:
- Next action:
