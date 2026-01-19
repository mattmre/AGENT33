# Phase 3–8 Workflow Plan (Architecture + Project Engineering)

Purpose: define execution workflow, dependencies, and sequencing for Phase 3–8 tasks. This plan is aligned with the AGENT-33 phase templates in `docs/phases/`.

## Dependency Chain (macro)
1. Phase 3 (Spec-first workflow) → unblocks Phase 4–8
2. Phase 4 (Harness/runtime) → unblocks policy and evidence operationalization
3. Phase 5 (Policy pack/risk) → required before tool registry and downstream sync
4. Phase 6 (Tooling/MCP) → depends on policy governance
5. Phase 7 (Evidence/verification) → required before evaluation baselines
6. Phase 8 (Evaluation/benchmarks) → depends on evidence pipeline
7. Phase 9-20 sequencing is defined in `docs/phases/PHASE-11-20-WORKFLOW-PLAN.md`

## Task Mapping (Phase 3–8)
| Phase | Task ID | Owner | Dependencies | Outputs |
| --- | --- | --- | --- | --- |
| 03 | T4 | Architect Agent | Phase 2 complete | Spec-first checklist + handoff alignment |
| 03 | T5 | Project Engineering Agent | T4 | Autonomy budget template + escalation guidance |
| 04 | T6 | Runtime Agent | T5 | Harness initializer + clean-state protocol |
| 04 | T7 | QA/Reporter Agent | T6 | Progress log format + rotation guidance |
| 05 | T8 | Documentation Agent | T7 | Policy pack v1 skeleton |
| 05 | T9 | Security Agent | T8 | Risk triggers extension |
| 05 | T10 | Architect Agent | T8 | Promotion criteria updates |
| 06 | T11 | Architect Agent | T9 | MCP/tool registry governance |
| 06 | T12 | Project Engineering Agent | T11 | Tools-as-code guidance |
| 07 | T13 | QA/Reporter Agent | T12 | Evidence capture + verification alignment |
| 07 | T14 | Test Engineer | T13 | Test matrix extension |
| 08 | T15 | Architect Agent | T14 | Evaluation harness + golden tasks |
| 08 | T16 | QA/Reporter Agent | T15 | Evaluation reporting template |

## Workflow Notes
- Each phase should produce a short summary entry in `core/arch/verification-log.md` once evidence is captured.
- Policy pack artifacts must be complete before MCP governance documentation is finalized.
- Evaluation metrics should not be tracked until evidence templates are stable.
- Phase 9-20 work should follow the extended dependency chain in the Phase 11-20 workflow plan.

## Review Gates
- Phase 3: architecture + process review required.
- Phase 4: operational review required (runtime safety).
- Phase 5: security review required for risk triggers.
- Phase 6: architecture review required for tool governance.
- Phase 7: QA review required for evidence consistency.
- Phase 8: architecture review required for evaluation methodology.
