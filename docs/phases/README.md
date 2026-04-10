# AGENT-33 Phase Index

This index lists the AGENT-33 development phases. Each phase file is a single-phase plan using the same structure as the generic templates in `core/phases/`.

## Phases
| Phase | Title | Category | File |
| --- | --- | --- | --- |
| 01 | Foundation & Inventory | Foundation | `PHASE-01-FOUNDATION-AND-INVENTORY.md` |
| 02 | Canonical Core Architecture | Core | `PHASE-02-CANONICAL-CORE-ARCHITECTURE.md` |
| 03 | Spec-First Orchestration Workflow | Orchestration | `PHASE-03-SPEC-FIRST-ORCHESTRATION-WORKFLOW.md` |
| 04 | Agent Harness & Runtime | Runtime | `PHASE-04-AGENT-HARNESS-AND-RUNTIME.md` |
| 05 | Policy Pack & Risk Triggers | Governance | `PHASE-05-POLICY-PACK-AND-RISK-TRIGGERS.md` |
| 06 | Tooling Integration & MCP | Tooling | `PHASE-06-TOOLING-INTEGRATION-AND-MCP.md` |
| 07 | Evidence & Verification Pipeline | Quality | `PHASE-07-EVIDENCE-AND-VERIFICATION-PIPELINE.md` |
| 08 | Evaluation & Benchmarking | Evaluation | `PHASE-08-EVALUATION-AND-BENCHMARKING.md` |
| 09 | Distribution & Sync | Distribution | `PHASE-09-DISTRIBUTION-AND-SYNC.md` |
| 10 | Governance & Community | Governance | `PHASE-10-GOVERNANCE-AND-COMMUNITY.md` |
| 11 | Agent Registry & Capability Catalog | Orchestration | `PHASE-11-AGENT-REGISTRY-AND-CAPABILITY-CATALOG.md` |
| 12 | Tool Registry Operations & Change Control | Tooling | `PHASE-12-TOOL-REGISTRY-OPERATIONS-AND-CHANGE-CONTROL.md` |
| 13 | Code Execution Layer & Tools-as-Code Integration | Runtime | `PHASE-13-CODE-EXECUTION-LAYER-AND-TOOLS-AS-CODE.md` |
| 14 | Security Hardening & Prompt Injection Defense | Security | `PHASE-14-SECURITY-HARDENING-AND-PROMPT-INJECTION-DEFENSE.md` |
| 15 | Review Automation & Two-Layer Review | Quality | `PHASE-15-REVIEW-AUTOMATION-AND-TWO-LAYER-REVIEW.md` |
| 16 | Observability & Trace Pipeline | Observability | `PHASE-16-OBSERVABILITY-AND-TRACE-PIPELINE.md` |
| 17 | Evaluation Suite Expansion & Regression Gates | Evaluation | `PHASE-17-EVALUATION-SUITE-EXPANSION-AND-REGRESSION-GATES.md` |
| 18 | Autonomy Budget Enforcement & Policy Automation | Governance | `PHASE-18-AUTONOMY-BUDGET-ENFORCEMENT-AND-POLICY-AUTOMATION.md` |
| 19 | Release & Sync Automation | Distribution | `PHASE-19-RELEASE-AND-SYNC-AUTOMATION.md` |
| 20 | Continuous Improvement & Research Intake | Research | `PHASE-20-CONTINUOUS-IMPROVEMENT-AND-RESEARCH-INTAKE.md` |
| 21 | Extensibility Patterns Integration | Research/Core | `PHASE-21-EXTENSIBILITY-PATTERNS-INTEGRATION.md` |
| 22 | Unified UI Platform and Access Layer | Product/Runtime Access | `PHASE-22-UNIFIED-UI-PLATFORM-AND-ACCESS-LAYER.md` |
| 25 | Visual Explainer Integration | Observability/Operator UX | `PHASE-25-VISUAL-EXPLAINER-INTEGRATION.md` |
| 26 | Visual Explainer Decision and Review Pages | Product/Explainability UX | `PHASE-26-VISUAL-EXPLAINER-DECISION-AND-REVIEW-PAGES.md` |
| 27 | Spacebot-Inspired Website Operations and Improvement Cycles | Product/Multi-User Agent UX | `PHASE-27-SPACEBOT-INSPIRED-WEBSITE-OPERATIONS-AND-IMPROVEMENT-CYCLES.md` |
| 28 | Enterprise Security Scanning Integration | Security/Product Safety | `PHASE-28-PENTAGI-COMPONENT-SECURITY-TESTING-INTEGRATION.md` |
| 29 | Reasoning Protocol & ISC | Intelligence/Runtime | See `PHASE-29-33-WORKFLOW-PLAN.md` (merged: PR #55, #57) |
| 30 | Strategic User Outcome Improvement Loops | Adaptive Execution | See `PHASE-29-33-WORKFLOW-PLAN.md` (core routing work merged; remaining work is refinement/verification) |
| 31 | Continuous Learning & Signal Capture | Intelligence/Memory | See `PHASE-29-33-WORKFLOW-PLAN.md` (signal capture + persistence/quality hardening merged in PR `#109`; tuning/runtime coherence follow-up merged in PR `#348`) |
| 32 | Middleware Chain, MCP Connectors & Circuit Breakers | Extensibility/Integration | See `PHASE-29-33-WORKFLOW-PLAN.md` (H01/H02 merged via PRs `#98` and `#100`; residual contract-hardening follow-up merged in PR `#349`) |
| 33 | Skill Packs & Distribution | Ecosystem/Distribution | See `PHASE-29-33-WORKFLOW-PLAN.md` (core implementation merged via PR `#103`; any future ecosystem work should be tracked as a new scoped slice) |
| 35 | Multimodal Async-Governance Convergence | Runtime/Governance | No plan file (core merged in PR `#85`; regression convergence merged in PR `#99`; voice sidecar finalization merged in PR `#324`) |
| 36 | Text-Based Tool Call Parsing | Runtime/LLM | `qwen-adoption-phases.md` (merged: PR #133) |
| 37 | Multimodal Content Blocks | Runtime/LLM | `qwen-adoption-phases.md` (merged: PR #135) |
| 38 | Streaming Agent Loop | Runtime/UX | `qwen-adoption-phases.md` (merged: PR #137) |
| 39 | LLM Query Expansion for RAG | Memory/RAG | `qwen-adoption-phases.md` (merged: PR #134) |
| 40 | Agent Archetypes | Runtime/DX | `qwen-adoption-phases.md` (merged: PR #136) |
| 41 | GroupChat Workflow Action | Orchestration | `qwen-adoption-phases.md` (merged: PR #138) |
| 42 | Stateful Code Execution (Jupyter) | Runtime/Execution | `qwen-adoption-phases.md` (merged: PR #139) |
| 43 | Complete MCP Server | Interoperability | `qwen-adoption-phases.md` (merged: PR #140) |
| 56 | Programmatic Tool Calling (PTC) Execution | Runtime/Execution | `PHASE-49-59-HERMES-ADOPTION-ROADMAP.md` (merged: Session 109 core; Session 115 wiring) |

## Workflow Plans
- `PHASE-03-08-WORKFLOW-PLAN.md` (phase sequencing, task mapping, review gates)
- `PHASE-11-20-WORKFLOW-PLAN.md` (extended sequencing and task mapping)
- `PHASE-21-24-WORKFLOW-PLAN.md` (post-core product/access sequencing)
- `PHASE-29-33-WORKFLOW-PLAN.md` (agent intelligence + extensibility sequencing)
- `ROADMAP-REBASE-2026-03-26.md` (merged-baseline checkpoint and current remaining priority queue)
- `qwen-adoption-phases.md` (Qwen-Agent competitive adaptation — Phases 36-43)

## Post-P72 Roadmap (2026)
| Plan | Title | File |
| --- | --- | --- |
| POST-1-4 | POST-P72 Phase Plan — SkillsBench, Packs, Interruption, Distribution | `PHASE-PLAN-POST-P72-2026.md` |

## Notes
- Generic templates live in `core/phases/` and serve as structural examples.
- This index is the canonical plan for AGENT-33 execution sequencing.
