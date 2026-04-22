# Loop 4 Initial Architecture and Phase Proposal

**Date:** 2026-04-21  
**Program:** AGENT-33 research program  
**Loop:** 4  
**Artifact type:** Initial draft proposal only — research artifact, not the final roadmap

---

## Status and framing

This document is the **first draft** of AGENT-33 evolution after the settled Loop 1-3 outputs.

It is **not**:

- the final official roadmap
- an implementation-ready MVP lock
- a final acceptance list
- a final information architecture
- a final sequencing commitment

Its purpose is to turn the Loop 3 synthesis into a **coherent draft architecture direction**, a **provisional phase decomposition**, and a **challengeable assumptions list** for Loop 5 panels.

---

## Inputs used

- Research program document: `C:\Users\mattm\.copilot\session-state\00d3a405-8501-4e95-9e95-2614f9b754a1\plan.md`
- Loop 3 synthesis: `docs/research/loop3-cross-batch-capability-synthesis-2026-04-21.md`
- Current baseline cross-checks used to preserve AGENT-33 strengths:
  - `docs/functionality-and-workflows.md`
  - `docs/default-policy-packs.md`
  - `docs/research/session126-p69b-ux-spec.md`

---

## 1) Settled starting point from Loops 1-3

Loop settlement used here:

- **Loop 1 complete:** top-20 repo corpus scanned
- **Loop 2 complete:** all 20 repos panel-reviewed
- **Loop 3 complete:** additive capability inventory and AGENT-33 gap map

Cross-batch conclusion from Loop 3:

> AGENT-33 does not mainly lack breadth. It mainly lacks the next-order **runtime integration layer** that unifies governance, interruptible events, bounded memory, durable replay, deterministic monitoring, safer mutation contracts, and governed skill lineage.

Current strengths that should be **preserved and composed forward**, not replaced blindly:

- governance baseline: policy packs, budgets, `allow|deny|ask` direction, approval surfaces
- workflow breadth: DAG execution, scheduling, delegation, approval-blocked flow concepts
- memory/RAG baseline: PostgreSQL + pgvector, BM25/hybrid retrieval, progressive recall
- operator/runtime assets: dashboards, traces, replay, runbooks, first-party web UI
- packaging ecosystem: packs, plugins, trust analytics, bootstrap/devbox footing

---

## 2) Proposed target architecture direction

### Direction statement

AGENT-33 should evolve toward a **governance-first, event-normalized, dual-surface agent platform**:

- a **layman-first task shell** for simple intent-to-outcome flows
- an **advanced operator workspace** for approvals, checkpoints, replay, budgets, and diagnosis
- a shared **runtime control plane** that makes policy, interrupts, memory lineage, execution state, and review contracts explicit across every capability layer

### Target shape

1. **Experience layer**
   - layman shell
   - operator workspace
   - research/replay/evidence views

2. **Control-plane layer**
   - unified governance operating model
   - directive inbox / approval surfaces
   - budgets, deny lists, permission diagnosis
   - operator-visible policy state

3. **Runtime spine**
   - normalized action-observation-event contract
   - interrupt-capable streaming
   - durable queue + checkpoint/resume
   - inspector chains + deterministic monitors
   - read-before-write and exact-diff mutation discipline

4. **State layer**
   - bounded working memory
   - frozen snapshots and lineage/state roots
   - durable replay/event history
   - memory views over shared lineage data

5. **Capability modules**
   - tools
   - workflows
   - browser/computer use
   - packs/plugins/skills

6. **Distribution layer**
   - web-first by default
   - packaging/form-factor decisions deferred until later evidence

### Architectural posture

- **Compose, do not clone.**
- **Preserve AGENT-33 strengths first.**
- **Treat browser/computer use as a separable governed subsystem.**
- **Make UX and runtime one program, not two disconnected tracks.**

---

## 3) Scope posture for this draft

| Bucket | Items |
|---|---|
| **Definitely in** | governance operating model; unified permission plane; normalized event contract; interrupt-capable replay/streaming substrate; inspector chains + zero-LLM monitors; read-before-write and exact-diff contracts; layman shell + operator workspace direction; checkpoint/review/inbox/cost visibility surfaces; durable execution + resume semantics |
| **Likely in** | bounded two-tier memory; frozen snapshots and lineage/state roots; directive inbox as cross-runtime control surface; durable queue for workflow/tool execution; skill lineage/version/promotion history; browser/computer-use supervision hooks and replay events |
| **Maybe in** | pairing/allowlist trust; graph/vector/timeline memory views; chat gateway unification; permission doctor; visual cursor; desktop/browser shell packaging; expanded bootstrap ergonomics beyond current devbox footing |
| **Not now** | importing whole external stacks; OpenHands V0 / enterprise leakage; unconstrained durable auto-memory; desktop-first rewrite; full browser autonomy before governance/event substrate hardens; final MVP cut line; exact final IA; official roadmap lock |

---

## 4) Concise phase table

| Phase | Focus | Primary posture | Depends on | Why it matters |
|---|---|---|---|---|
| **A** | Runtime control plane unification | Definitely in | Current governance + trace baseline | Turns scattered controls into one visible operating model |
| **B** | Dual-surface UX reset | Definitely in | A | Fixes API-centric UX and makes operator control first-class |
| **C** | Durable execution and replay spine | Definitely in | A | Makes runs queueable, resumable, inspectable, and approval-aware |
| **D** | Bounded memory and lineage layer | Likely in | A, C | Closes the clearest structural gap from Loop 3 |
| **E** | Governed browser/computer-use substrate | Likely in / Maybe in | A, C, partial B | Adds supervision to browser/computer use instead of raw actuation only |
| **F** | Skill supply chain and packaging decisions | Likely in / Maybe in | A, D, partial B | Extends packs/plugins into governed lineage and resolves packaging questions later |

> Sequencing is provisional. Loop 5 should challenge whether B and C can partially progress in parallel once A contracts stabilize.

---

## 5) Detailed phase decomposition

### Phase A — Runtime control plane unification

**Objective**  
Create one explicit control-plane contract spanning tools, workflows, prompts, approvals, and future browser/computer actions.

**Why this phase exists**  
AGENT-33 already has governance pieces, but Loop 3 showed that they behave more like adjacent features than one operating model. This phase is the architectural anchor for everything else.

**Key capabilities included**

- governance operating model and state-root concepts
- universal permission plane (`allow`, `ask`, deny lists, approval triggers)
- operator-visible policy state and reason surfaces
- normalized action-observation-event schema
- interrupt-capable SSE/streaming contract
- inspector-chain insertion points
- deterministic zero-LLM monitor hooks
- read-before-write + exact-match diff baseline for mutation surfaces

**Dependencies**

- existing policy packs
- autonomy budgets and approval work
- current traces/SSE/dashboard surfaces

**Explicitly out of scope**

- final browser watchdog design
- desktop packaging decisions
- complete memory compaction policy
- final layman/operator IA

**Needs later validation / spikes**

- minimal event schema that spans tools, DAG nodes, approvals, interrupts, and browser events
- which governance policies must be model-visible vs only operator-visible
- deterministic vs model-mediated inspector boundaries

---

### Phase B — Dual-surface UX reset

**Objective**  
Define AGENT-33 as two coordinated product surfaces: a layman-first task shell and an advanced operator workspace.

**Why this phase exists**  
The current frontend is too subsystem-centric. Loop 3 indicates that operator UX is part of the runtime contract, while the product also needs a simpler primary surface for non-expert users.

**Key capabilities included**

- layman-first task entry and guided run surfaces
- advanced operator workspace for checkpoints, approvals, replay, and budgets
- directive inbox concepts for operator intervention
- checkpoint/review UX informed by Cline/CoreCoder/HolyClaude patterns
- cost/token transparency
- permission/context panels tied to the control plane
- research/evidence/replay visibility for long-running work

**Dependencies**

- Phase A event and policy contracts
- current first-party web UI and dashboard base

**Explicitly out of scope**

- final visual design system lock
- desktop shell commitment
- hard decision on one app vs multiple shells
- full browser visual cursor UX

**Needs later validation / spikes**

- how separate the layman shell and operator workspace should be
- whether approvals, checkpoints, and operator tasks belong in one directive inbox
- operator cognitive-load tradeoffs for cost/policy/replay density

---

### Phase C — Durable execution and replay spine

**Objective**  
Make execution durable, queueable, resumable, and inspectable across workflows and tool-driven runs.

**Why this phase exists**  
AGENT-33 already executes workflows, but Loop 3 showed missing durable queue/checkpoint semantics, normalized replay, and first-class interrupt/resume behavior.

**Key capabilities included**

- durable queue and checkpoint/resume semantics
- approval-blocked execution that survives restarts
- unified replay/event history joining workflow, tool, approval, and monitor events
- interruption-safe run lifecycle
- inspector-chain attachments to execution stages
- consistent operator review points for blocked or resumed work

**Dependencies**

- Phase A event/control contracts
- current workflow DAG and execution baseline

**Explicitly out of scope**

- final autonomous throughput tuning
- full marketplace/multi-agent openness
- memory retention policy details

**Needs later validation / spikes**

- canonical checkpoint unit: invocation, node, tool call, browser step, or snapshot
- event log vs queue item vs state snapshot as source of truth
- operator-latency cost of additional pause points

---

### Phase D — Bounded memory and lineage layer

**Objective**  
Upgrade AGENT-33 memory from broad retrieval plus persistence into bounded, layered, lineage-aware state.

**Why this phase exists**  
Loop 3 identified memory as the clearest structural gap: AGENT-33 has strong retrieval, but not enough bounded working-state, frozen snapshots, or unified lineage semantics.

**Key capabilities included**

- bounded two-tier memory model
- frozen snapshots and lineage/state roots
- directive persistence linked to runs
- retention/compaction discipline for durable memory
- views over shared lineage data (graph/vector/timeline candidates)
- stronger linkage between memory, replay, and execution state

**Dependencies**

- Phase A normalized event/control model
- Phase C durable replay spine
- current Postgres/pgvector memory baseline

**Explicitly out of scope**

- unconstrained auto-memory accumulation
- tenant-wide background collection without governance
- committing to multiple separate memory backends prematurely

**Needs later validation / spikes**

- freeze/summarize/forget rules
- storage cost and staleness behavior for snapshots/lineage
- whether graph/vector/timeline should be distinct systems or views on one lineage store

---

### Phase E — Governed browser/computer-use substrate

**Objective**  
Treat browser/computer use as a supervised capability layer built on the same control-plane and replay contracts as the rest of the runtime.

**Why this phase exists**  
AGENT-33 already has browser primitives, but Loop 3 showed that raw actuation is not enough; browser/computer use needs policy, supervision, replay, and interruption discipline.

**Key capabilities included**

- browser/computer events on the shared event spine
- approval and policy hooks aligned to the unified permission plane
- supervised session lifecycle and richer replay
- watchdog/judge insertion points
- permission-overlay concepts for risky actions
- compatibility with visible and headless execution paths

**Dependencies**

- Phase A control-plane contracts
- Phase C durable execution/replay
- partial benefit from Phase B operator surfaces

**Explicitly out of scope**

- committing to a full visual cursor stack now
- high-autonomy computer use without hardened supervision
- desktop-only assumptions

**Needs later validation / spikes**

- which browser safety signals are canonical
- visible replay vs headless reproducibility tradeoffs
- whether watchdog/judge loops should remain deterministic, model-assisted, or layered

---

### Phase F — Skill supply chain and packaging decisions

**Objective**  
Extend AGENT-33 packs/plugins into governed lineage objects, while postponing packaging/form-factor choices until evidence is stronger.

**Why this phase exists**  
AGENT-33 already has packs, plugins, and trust analytics. The missing additive layer is lineage, promotion history, rollback ancestry, and a clearer answer on whether packaging affects capability or only adoption.

**Key capabilities included**

- skill/pack lineage and version DAG concepts
- frozen bundle snapshots
- promotion, rollback, and trust history surfaces
- governed import/promotion model for external skills
- packaging evaluation track rather than immediate packaging rewrite

**Dependencies**

- Phase A governance model
- Phase D lineage/state concepts
- existing pack/plugin lifecycle and trust analytics

**Explicitly out of scope**

- open marketplace by default
- shell packaging as a foregone decision
- replacing the current web-first posture

**Needs later validation / spikes**

- trust model for open vs curated ecosystems
- signature/provenance requirements
- whether desktop/browser shell packaging meaningfully changes adoption

---

## 6) What this draft preserves from AGENT-33

This proposal is intentionally **additive**. It does **not** assume that AGENT-33 should throw away its current posture.

Preservation rules:

1. **Keep the current governance baseline** and turn it into a more explicit operating model.
2. **Keep workflow/DAG breadth** and add durability, replay, and checkpoint semantics.
3. **Keep the current memory/RAG foundation** and add bounded state, snapshots, and lineage.
4. **Keep packs/plugins/trust analytics** and evolve them into governed supply-chain objects.
5. **Keep the web-first shell and devbox footing** unless later evidence proves packaging changes more than distribution.

---

## 7) Tensions and contradictions Loop 5 panels must challenge

1. **Bounded memory vs durable auto-memory**
   - Should AGENT-33 prioritize freezing and compaction, or accumulation and recall depth?

2. **Operator control vs autonomy throughput**
   - Where are pauses mandatory, and where are they optional?

3. **Unified event substrate vs rich UX metaphors**
   - Can the runtime stay normalized while the UX becomes more human-friendly?

4. **Exact diff discipline vs flexible semantic mutation**
   - Which mutation classes must remain exact-match, and which can tolerate looser transforms?

5. **Directive inbox unification vs separate control surfaces**
   - Should approvals, checkpoints, interrupts, and operator tasks share one inbox?

6. **Web-first sufficiency vs desktop packaging**
   - Does packaging change capability, trust, and adoption, or only form factor?

7. **Open skill ecosystems vs trust-constrained promotion**
   - How open can AGENT-33 be without losing supply-chain control?

8. **Visible browser supervision vs headless reproducibility**
   - Which telemetry becomes canonical for replay, diagnosis, and safety?

9. **Immutable state roots vs resumable execution**
   - What is the correct frozen unit when runs can pause, branch, and resume?

10. **Governance visible to the model vs hidden in the control plane**
    - How much policy should the model explicitly see?

---

## 8) Unresolved assumptions for Loop 5

These assumptions should be challenged before any official roadmap is locked:

1. A **single normalized event schema** can cover tools, workflows, approvals, interrupts, browser actions, and replay without fragmenting.
2. **Inspector chains** can stay mostly deterministic and avoid drifting into expensive, hard-to-audit model review.
3. **Frozen snapshots and lineage** can be persisted affordably without replay-tree sprawl.
4. **Bounded memory plus compaction** is a better AGENT-33 default than broad durable accumulation.
5. One **permission plane** can span tools, prompts, workflows, browser actions, pairing, and allowlists without becoming confusing.
6. **Read-before-write and exact-diff discipline** can generalize beyond code/file editing to other mutation surfaces.
7. A clear **checkpoint unit** exists and is practical enough for pause/resume, replay, and approval recovery.
8. A **directive inbox** can unify approvals, checkpoints, and interrupts without overloading operators.
9. **Skill lineage/version DAGs** can fit AGENT-33’s existing pack/plugin/trust structures without a parallel system.
10. **Browser/computer-use supervision** can be added safely before committing to highly autonomous computer control.
11. **Desktop/browser shell packaging** may improve adoption, but does not yet justify a product-direction override.
12. The best next step is still **composition across sources**, not alignment to any single reference repo.

---

## 9) Draft bottom line

The current best draft direction is:

- **preserve AGENT-33’s broad runtime strengths**
- **add a shared governance-and-event spine**
- **reset the product into layman shell + operator workspace**
- **make execution durable, replayable, and interruptible**
- **treat memory, browser use, and skill lifecycle as governed layers on top of that spine**

That is the proposed Loop 4 direction. It is intentionally **provisional** and should be treated as the artifact Loop 5 panels are supposed to challenge, refine, and potentially reorder.
