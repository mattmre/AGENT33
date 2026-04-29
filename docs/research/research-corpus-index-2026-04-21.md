# Research Corpus Index — 2026-04-21

**Purpose:** preserve the current AGENT-33 research corpus as durable work product, make the major session outputs discoverable, and establish a reusable reference surface for later distillation, introspection, and council audit work.

---

## Preservation policy

1. **Canonical repo-preserved research** lives under `docs/research/`.
2. **Session-local working state** may exist in session `plan.md`, checkpoints, and runtime history, but durable conclusions should be promoted into `docs/research/` artifacts.
3. **Panel outputs** should be preserved in one of two forms:
   - a dedicated synthesis artifact
   - a summary entry in the panel-output ledger
4. **Council audit and future roadmap distillation** should cite canonical repo files, not ad hoc chat summaries.

---

## Current strategic program — canonical artifacts

These are the primary artifacts for the current research-first overhaul program.

| Artifact | Role |
|---|---|
| `loop3-cross-batch-capability-synthesis-2026-04-21.md` | Cross-batch capability taxonomy, additive capability inventory, and gap map |
| `loop4-initial-architecture-phase-proposal-2026-04-21.md` | First provisional architecture/phase draft |
| `loop5a-vision-realignment-panels-2026-04-21.md` | Corrects governance-first bias and recenters the platform on harnesses, skills, and specialist agents |
| `loop5b-ecosystem-architecture-panels-2026-04-21.md` | Defines cadres, silos, model postures, shared harness boundaries, and reporting contracts |
| `loop5c-anti-hallucination-and-context-limit-panels-2026-04-21.md` | Defines contracted narrowing and the reliability/anti-hallucination extension |
| `paper-lewm-panel-update-strategy-2026-04-21.md` | Integrates the LeWorldModel paper as a design-discipline input, especially for compact state, probing, surprise, and reward graphing |
| `world-model-platform-feasibility-panels-2026-04-21.md` | Clarifies the difference between current specialist-agent orchestration and any future world-model-capable research horizon |
| `council-final-audit-2026-04-22.md` | Final council verdict on research readiness, unresolved conditions, and spike-gated roadmap guidance |
| `gated-phased-roadmap-draft-2026-04-22.md` | Conditional roadmap skeleton organized into phases and explicit spike gates prior to final roadmap lock |
| `roadmap-panel-refinement-synthesis-2026-04-22.md` | Preserved convergence report from architecture, UI, DX, and backend refinement panels and the concrete roadmap changes adopted from them |
| `roadmap-gate-spike-scope-2026-04-22.md` | Grouped scope artifact for the six roadmap gates, including deliverables, validators, sequencing, and rollback boundaries |
| `roadmap-gate1-event-handoff-brief-2026-04-22.md` | Detailed spike brief for the shared invocation, event, result, error, and handoff contract family |
| `roadmap-gate2-frozen-handoff-brief-2026-04-22.md` | Detailed spike brief for compact task-state, checkpoint units, replay, repair, and frozen handoff semantics |
| `roadmap-gate3-telemetry-brief-2026-04-22.md` | Detailed spike brief for context-budget, routing, and skill-activation telemetry with durable export and explanation requirements |
| `roadmap-gate4-memory-precedence-brief-2026-04-22.md` | Detailed spike brief for memory classes, precedence, provenance, retrieval introspection, and correction semantics |
| `roadmap-gate5-browser-evidence-brief-2026-04-22.md` | Detailed spike brief for canonical environment evidence bundles, watchdog labels, replay attachments, and redaction-aware auditability |
| `roadmap-gate6-improvement-containment-brief-2026-04-22.md` | Detailed spike brief for promotion scorecards, evaluation harnesses, rollback ancestry, and proposal-only improvement containment |
| `roadmap-gate-brief-consistency-audit-2026-04-22.md` | Consistency audit across all six detailed gate briefs, including dependency checks and minor harmonization fixes |
| `roadmap-backbone-gate-workstreams-2026-04-22.md` | Execution workstream decomposition for Gate 1, Gate 2, and Gate 4, including ordering, dependencies, outputs, and batching guidance |
| `roadmap-backbone-workstream-batch1-2026-04-22.md` | Selection and sequencing of the first bounded backbone workstream batch centered on contract objects, event semantics, frozen state units, and memory taxonomy |
| `roadmap-g1w1-contract-boundaries-2026-04-22.md` | Contract object inventory and boundary rules for the Gate 1 runtime contract family |
| `final-phase-plan-for-review-2026-04-22.md` | Final review plan integrating the validated roadmap direction, gate program, implementation phases, and product/containment architecture |
| `final-phase-plan-panel-audit-synthesis-2026-04-22.md` | Preserved synthesis of the three final-plan expert panel audits and the concrete revisions applied to the final review plan |
| `final-phase-plan-rerun-panel-sweep-2026-04-22.md` | Preserved synthesis of the second three-panel sweep against the current final plan text and the final targeted edits applied from that rerun |
| `final-phase-plan-final-sweep-2026-04-22.md` | Preserved synthesis of the third and final three-panel sweep against the current final plan text and the final layman-first clarity edits applied from that pass |
| `executive-summary-product-sprint-2026-04-22.html` | Self-contained HTML slide deck for product management summarizing the plan posture, sprint recommendation, layman-first UX commitments, Layer 0 gate posture, and key decisions before sprint start |
| `product-review-storyboard-mockups-2026-04-22.html` | Rich HTML review deck with executive summary framing, panel-sweep evolution, storyboard scenes, phase-by-phase visuals, and UI mockups for layman and operator surfaces |
| `panel-output-ledger-2026-04-21.md` | Preserved summary register of major panel outputs and where they were captured |

---

## Supporting source artifacts used by the current program

These documents were repeatedly used as baseline evidence or grounding context.

| Artifact | Role |
|---|---|
| `docs/functionality-and-workflows.md` | Current runtime capability and lifecycle map |
| `docs/default-policy-packs.md` | Governance / connector-boundary policy-pack baseline |
| `session126-p69b-api-contract.md` | Tool-approval API contract and pause/resume semantics |
| `session126-p69b-ux-spec.md` | Tool-approval UX behavior and state model |
| `README.md` | High-level research system notes and templates registry |

---

## Broad corpus buckets preserved in `docs/research/`

The research corpus is larger than the current initiative. The following buckets are part of the durable work product and remain available for later distillation and introspection.

| Bucket | Path / pattern | Notes |
|---|---|---|
| Current strategic overhaul artifacts | `docs/research/*2026-04-21*.md` and current loop artifacts | Current planning and panel-driven refinement corpus |
| Repo dossiers | `docs/research/repo_dossiers/` | Structured repo-ingestion research and comparative ecosystem notes |
| Session scope / phase research | `docs/research/session*.md` | Historical session research, scopes, audits, and architecture notes |
| Phase and roadmap analyses | `docs/research/phase*.md`, `docs/research/skillsbench*.md`, `docs/research/openclaw*.md` | Earlier phase planning, priority analyses, parity studies, and implementation research |
| Ingestion / evolver / landscape analyses | `docs/research/*ingestion*.md`, `docs/research/*landscape*.md`, `docs/research/*analysis*.md` | Research intake, ecosystem landscape work, and comparative studies |
| Research templates | `docs/research/templates/` | Reusable research artifact structures |
| Cleanup / patch support | `docs/research/cleanup-patches/` | Supporting cleanup material preserved with the corpus |

---

## Panel preservation status

Major panel-driven outputs from the current initiative are now preserved through:

1. **Loop 5 refinement artifacts**
2. **LeWorldModel paper integration artifact**
3. **World-model feasibility artifact**
4. **Council final audit artifact**
5. **Gated roadmap draft artifact**
6. **Roadmap panel refinement synthesis**
7. **Roadmap gate spike scope**
8. **Gate 1 detailed spike brief**
9. **Gate 2 detailed spike brief**
10. **Gate 3 detailed spike brief**
11. **Gate 4 detailed spike brief**
12. **Gate 5 detailed spike brief**
13. **Gate 6 detailed spike brief**
14. **Gate brief consistency audit**
15. **Backbone gate workstream decomposition**
16. **Backbone workstream batch 1**
17. **G1-W1 contract boundaries**
18. **Final review plan**
19. **Final plan panel audit synthesis**
20. **Final plan rerun panel sweep**
21. **Final plan final sweep**
22. **Panel output ledger**

This means the critical panel conclusions are now durable even when the original sub-agent transcripts are not stored as standalone files.

---

## How to use this corpus later

### For roadmap distillation

Start with:

1. `loop3-cross-batch-capability-synthesis-2026-04-21.md`
2. `loop5a-vision-realignment-panels-2026-04-21.md`
3. `loop5b-ecosystem-architecture-panels-2026-04-21.md`
4. `loop5c-anti-hallucination-and-context-limit-panels-2026-04-21.md`
5. `paper-lewm-panel-update-strategy-2026-04-21.md`
6. `world-model-platform-feasibility-panels-2026-04-21.md`
7. `council-final-audit-2026-04-22.md`
8. `gated-phased-roadmap-draft-2026-04-22.md`
9. `roadmap-panel-refinement-synthesis-2026-04-22.md`
10. `roadmap-gate-spike-scope-2026-04-22.md`
11. `roadmap-gate1-event-handoff-brief-2026-04-22.md`
12. `roadmap-gate2-frozen-handoff-brief-2026-04-22.md`
13. `roadmap-gate3-telemetry-brief-2026-04-22.md`
14. `roadmap-gate4-memory-precedence-brief-2026-04-22.md`
15. `roadmap-gate5-browser-evidence-brief-2026-04-22.md`
16. `roadmap-gate6-improvement-containment-brief-2026-04-22.md`
17. `roadmap-gate-brief-consistency-audit-2026-04-22.md`
18. `roadmap-backbone-gate-workstreams-2026-04-22.md`
19. `roadmap-backbone-workstream-batch1-2026-04-22.md`
20. `roadmap-g1w1-contract-boundaries-2026-04-22.md`
21. `final-phase-plan-for-review-2026-04-22.md`
22. `final-phase-plan-panel-audit-synthesis-2026-04-22.md`
23. `final-phase-plan-rerun-panel-sweep-2026-04-22.md`
24. `final-phase-plan-final-sweep-2026-04-22.md`

### For panel-introspection work

Start with:

1. `panel-output-ledger-2026-04-21.md`
2. linked synthesis artifacts

### For system introspection / self-improvement research

Use this corpus to mine:

- recurring capability gaps
- repeated panel consensus themes
- strong vs weak priors in the roadmap
- evidence for memory, reward-graph, trust, and specialist-agent design
- candidate evaluation suites and future spike topics

---

## Current preservation stance

As of this index:

- the current research-first overhaul program is preserved in repo docs
- the major panel outputs are preserved in canonical synthesized form
- the broader historical research corpus remains available in `docs/research/`
- future sessions should continue promoting durable conclusions into this directory rather than leaving them only in transient session state
