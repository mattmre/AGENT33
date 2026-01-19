# Phase 11-20 Workflow Plan (Orchestration + Governance)

Purpose: define execution workflow, dependencies, and sequencing for Phase 11-20 tasks.

## Dependency Chain (macro)
1. Phase 11 (Agent registry) unblocks tool registry operations.
2. Phase 12 (Tool registry operations) unblocks tools-as-code execution guidance.
3. Phase 13 (Code execution layer) unblocks security hardening for tool usage.
4. Phase 14 (Security hardening) unblocks two-layer review workflow.
5. Phase 15 (Review automation) unblocks trace pipeline requirements.
6. Phase 16 (Observability/trace) unblocks evaluation gate expansion.
7. Phase 17 (Evaluation gates) unblocks autonomy enforcement policy automation.
8. Phase 18 (Autonomy enforcement) unblocks release and sync automation.
9. Phase 19 (Release/sync automation) unblocks continuous improvement intake.
10. Phase 20 (Continuous improvement) closes the Phase 11-20 loop.

## Task Mapping (Phase 11-20)
Task IDs mirror `core/orchestrator/handoff/TASKS.md`.

| Phase | Task ID | Owner | Dependencies | Outputs |
| --- | --- | --- | --- | --- |
| 11 | T17 | Architect Agent | Phase 10 complete | Agent registry schema + capability taxonomy |
| 11 | T18 | Project Engineering Agent | T17 | Routing map updates + onboarding notes |
| 12 | T19 | Security Agent | T18 | Tool registry change control + provenance update flow |
| 12 | T20 | Documentation Agent | T19 | Deprecation + rollback guidance |
| 13 | T21 | Runtime Agent | T20 | Code execution contract + adapter template |
| 14 | T22 | Security Agent | T21 | Prompt injection defenses + sandbox approvals |
| 15 | T23 | QA/Reporter Agent | T22 | Two-layer review checklist + signoff flow |
| 16 | T24 | QA/Reporter Agent | T23 | Trace schema + artifact retention rules |
| 17 | T25 | Test Engineer | T24 | Regression gates + triage playbook |
| 18 | T26 | Project Engineering Agent | T25 | Autonomy budget enforcement |
| 19 | T27 | Documentation Agent | T26 | Release cadence + sync automation plan |
| 20 | T28 | Orchestrator | T27 | Research intake + continuous improvement cadence |

## Workflow Notes
- Each phase should produce a short summary entry in `core/arch/verification-log.md` once evidence is captured.
- Phase 14 and Phase 18 require explicit security review signoff.
- Phase 17 should reuse the Phase 8 evaluation artifacts and expand them.
- Phase 19 should include rollback and dry-run steps before any release/sync automation.

## Review Gates
- Phase 11: architecture review required.
- Phase 12: security review required.
- Phase 13: runtime review required.
- Phase 14: security review required.
- Phase 15: QA review required.
- Phase 16: QA review required.
- Phase 17: architecture review required.
- Phase 18: security + governance review required.
- Phase 19: operational review required.
- Phase 20: governance review required.
