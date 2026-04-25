# Loop 5B Ecosystem Architecture Panels

**Date:** 2026-04-21  
**Program:** AGENT-33 research program  
**Loop:** 5B  
**Artifact type:** Ecosystem-refinement artifact only — not a roadmap

---

## Status and framing

This artifact refines the Loop 4 draft away from mostly platform/control-plane language and toward an **ecosystem of specialized agents**.

It is **not**:

- a final roadmap
- a sequencing commitment
- an implementation-ready architecture lock
- a final product IA
- a final self-improvement/autonomous-learning approval

Its purpose is to answer a narrower question:

> If AGENT-33 is centered as a system of tailored agents with explicit jobs, model postures, tool scopes, and reporting contracts, what ecosystem shape best fits the Loop 3 evidence and where does Loop 4 need reframing?

---

## Inputs used

- Research program document: session-local `plan.md`
- Loop 3 synthesis: `docs/research/loop3-cross-batch-capability-synthesis-2026-04-21.md`
- Loop 4 draft: `docs/research/loop4-initial-architecture-phase-proposal-2026-04-21.md`

---

## Panel method used

This refinement used a panel-style synthesis through four lenses:

1. **Architecture lens** — what classes of agents and boundaries make the system coherent
2. **Integration lens** — what shared contracts and ingestion paths make siloed agents composable
3. **Feasibility lens** — what is plausible now versus speculative, especially around self-learning and browser supervision
4. **Developer-ergonomics lens** — what keeps the ecosystem legible for builders and operators

### Panel consensus in one sentence

Loop 4 is directionally right about governance, events, memory, replay, and skill lineage, but it still describes mostly a **platform skeleton**; Loop 5B should restate AGENT-33 as a **shared harness plus explicit specialist cadres** whose outputs flow back into a visible main improvement loop.

---

## 1) Proposed ecosystem taxonomy of AGENT-33 agent classes/cadres

### Core framing

AGENT-33 should not be described as one general assistant with optional helpers. It should be described as:

- a **main coordinator / ingestion loop** that routes work, receives artifacts, and governs promotion
- a set of **specialized cadres** with narrow responsibilities
- a **shared harness** that standardizes governance, replay, memory, budgets, approvals, and lineage

### Proposed cadre taxonomy

| Cadre | Representative agent classes | Primary job | Default model posture | Tool scope posture | Primary output contract | Near-term posture |
|---|---|---|---|---|---|---|
| **Governance & Safety Cadre** | policy steward, approval router, zero-LLM monitor, risk gate | enforce policy, budgets, allow/ask/deny, deterministic review | deterministic first; LLM only as exception advisor | policy store, audit trail, approval queue, monitors | `PolicyVerdict`, `ApprovalRequest`, `MonitorAlert` | **Adopt now** |
| **Research & Ingestion Cadre** | repo ingestion agent, auto-research agent, evidence packager | scan repos, extract capabilities, assemble dossiers, detect drift | cheap-to-mid models for repetitive extraction; stronger model for synthesis | read-heavy repo analysis, search, retrieval, evidence formatting | `EvidenceBundle`, `ResearchDossier`, `CorpusDelta` | **Adopt / distill now** |
| **Synthesis & Judgment Cadre** | panel judge, contradiction checker, refinement agent, proposal synthesizer | compare evidence, challenge assumptions, refine drafts, arbitrate competing proposals | stronger reasoning models; multi-model panel for ambiguous high-impact judgments | read-only over evidence, specs, prior runs | `JudgmentRecord`, `RefinementDraft`, `ChallengeMemo` | **Distill now** |
| **Execution & Orchestration Cadre** | task planner, workflow steward, tool worker, queue/resume steward | decompose work, execute tool-bounded steps, persist checkpoints, resume safely | mid-tier models for planning/execution; deterministic queue semantics | scoped tools only, read-before-write, exact-diff where possible | `TaskGraph`, `RunTranscript`, `CheckpointRecord`, `MutationProposal` | **Adopt / distill now** |
| **Environment Specialist Cadre** | browser supervisor, computer-use watchdog, domain-specific tool specialist | handle risky or domain-bound action loops under extra supervision | specialized models only inside bounded harnesses; deterministic fallback required | restricted domain tools, browser/computer events, permission overlays | `EnvironmentActionRecord`, `WatchdogVerdict`, `ReplayAttachment` | **Observe / partial distill** |
| **Improvement & Learning Cadre** | skill curator, self-improvement analyst, self-learning sandbox agent, promotion judge | analyze runs, evolve packs/skills/harness settings, propose improvements, manage lineage | cheap models for scoring/classification; stronger models for synthesis; deterministic promotion checks | registry, evaluation harness, lineage store, markdown/spec diffs | `ImprovementProposal`, `SkillPromotionRecord`, `RollbackLineage`, `LearningCandidate` | **Partial now; self-learning remains provisional** |

### Taxonomy notes

1. **Governance is a cadre, not just a subsystem.** Loop 3 repeatedly shows that governance has become an explicit operating model.
2. **Research and judgment should be separate cadres.** Repo ingestion and evidence packaging should not also be the final judge on whether their findings are adopted.
3. **Execution agents should be narrow.** Planner, executor, and queue/resume stewardship should not collapse into one personified agent.
4. **Environment specialists should stay siloed.** Browser/computer-use and other high-risk domains need tighter harnesses than general tool work.
5. **Improvement should split into safe curation vs speculative self-learning.** Skill curation and run analysis are plausible; autonomous self-learning remains high-risk and should begin as proposal-only.

---

## 2) Recommended silo boundaries, reporting contracts, and ingestion pathways

### Recommended silo boundaries

The critical rule is:

> agents may share the same harness and lineage store, but they should not share the same job.

Recommended boundary rules:

1. **Governance agents do not plan or execute.** They approve, block, score risk, and emit policy state.
2. **Research agents do not self-promote their findings.** They emit evidence bundles for review and ingestion.
3. **Judgment agents do not mutate production state directly.** They produce verdicts, rankings, and challenge records.
4. **Execution agents do not rewrite their own mission.** They consume scoped task graphs and emit transcripts/checkpoints/mutation proposals.
5. **Improvement agents do not auto-apply high-risk changes.** They propose pack, prompt, harness, or routing deltas that pass through promotion gates.
6. **Environment specialists do not bypass shared policy or replay rules.** They may be more specialized, but not more sovereign.

### Minimum shared reporting contracts

Every cadre should speak a common contract family, even when payloads differ.

#### A. Invocation envelope

Every agent invocation should carry:

- `agent_class`
- `task_id` / `run_id`
- `objective`
- `constraints`
- `policy_refs`
- `budget_refs`
- `allowed_tools`
- `input_artifact_refs`
- `expected_output_schema`
- `confidence_target`

#### B. Progress / interrupt events

Every agent should emit a normalized event stream with at least:

- `event_type` (`started`, `step`, `paused`, `approval_required`, `completed`, `failed`)
- `agent_class`
- `run_id`
- `state_ref`
- `operator_action_required`
- `evidence_refs`
- `cost_or_budget_delta`

#### C. Result bundle

Every agent completion should emit:

- `summary`
- `structured_payload`
- `confidence`
- `citations`
- `lineage_refs`
- `follow_on_recommendations`
- `promotion_or_review_required`

### Cadre-specific output contracts

| Agent family | Required payload |
|---|---|
| Governance & Safety | policy verdict, rule references, reason codes, escalation flag |
| Research & Ingestion | evidence bundle, citations, extracted patterns, confidence notes, unresolved questions |
| Synthesis & Judgment | verdict, ranking or critique, contradiction list, assumptions challenged |
| Execution & Orchestration | task graph, run transcript, checkpoint record, mutation proposal, exact diff when applicable |
| Environment Specialist | environment action log, safety verdict, replay attachment, escalation trigger |
| Improvement & Learning | improvement proposal, evaluation scorecard, promotion request, rollback ancestry |

### Ingestion pathways back to the main system

The main AGENT-33 loop should ingest artifacts through three distinct pathways:

1. **Hot path — operator-facing control ingestion**
   - approvals
   - interrupts
   - high-risk verdicts
   - promotion gates
   - blocked-run recovery

2. **Warm path — memory / lineage ingestion**
   - evidence bundles
   - run transcripts
   - citations
   - checkpoints
   - routing outcomes
   - skill ancestry links

3. **Cold path — evaluation / ecosystem improvement ingestion**
   - benchmark outputs
   - routing performance summaries
   - false-positive / false-negative review data
   - candidate prompt/skill/harness deltas
   - longitudinal repo drift findings

### Recommended ingestion rule

No specialized agent should directly mutate the global system state without creating an artifact that is:

- reviewable
- replay-linked
- attributable to a source run
- eligible for rollback or rejection

That rule is what makes the ecosystem feed the main improvement loop instead of fragmenting into local, untraceable silos.

---

## 3) How model routing should relate to agent purpose, risk, and repetition

### Routing principle

Model routing should be based on **job type first**, then **risk**, then **repetition economics**.

### Recommended routing posture

| Work type | Recommended routing posture | Why |
|---|---|---|
| deterministic governance, monitors, diff validation, policy checks | **no LLM or deterministic-first** | high-risk but low-ambiguity work should not depend on generative judgment |
| repetitive extraction, tagging, classification, report normalization | **cheap small model first** | these jobs are frequent and schema-bound; cost matters more than maximal reasoning depth |
| planning, bounded execution, repo synthesis, draft refinement | **mid-tier model** | these tasks need reasoning but happen often enough that premium models should not be the default |
| ambiguous architecture judgments, panel arbitration, high-impact synthesis | **strong model or multi-model panel** | low-frequency, high-consequence decisions justify premium reasoning or cross-model disagreement checks |
| browser/computer-use supervision | **specialized model inside a bounded harness plus deterministic fallback** | high-risk domain; model output must be overridable by policy and watchdog rules |

### Routing rules by risk and repetition

1. **High-risk, low-ambiguity work** should move downward toward deterministic systems, not upward toward stronger models.
2. **Low-risk, high-frequency work** should prefer cheaper pinned models for consistency and cost control.
3. **High-ambiguity, high-consequence work** is where premium reasoning and/or multi-model judgment makes sense.
4. **Repeated tasks should keep a stable pinned model unless evidence says otherwise.** Otherwise replay, audit, and benchmark comparisons degrade.
5. **Escalation should be explicit.** Cheap model → stronger model → panel review → operator, rather than silent model switching.

### Specific ecosystem guidance

- **Governance & Safety Cadre:** deterministic first; model only for advisory diagnosis, never as the sole policy source.
- **Research & Ingestion Cadre:** cheap models for extraction; stronger model when merging many findings into one dossier.
- **Synthesis & Judgment Cadre:** best place for multi-model routing because disagreement is informative.
- **Execution & Orchestration Cadre:** mid-tier default, but mutation validation stays deterministic wherever possible.
- **Environment Specialists:** model choice should be scoped per harness, not globally reusable as a general controller.
- **Improvement & Learning Cadre:** keep self-learning read-only until routing, audit, and rollback evidence exists.

### Core caution

Loop 4 should stop implying that one generalized runtime will choose models uniformly. In an ecosystem framing, **model association is part of each cadre’s contract**.

---

## 4) Which capabilities belong in shared infrastructure versus agent-specific harnesses/skills

### Shared infrastructure

The following should be shared across the ecosystem:

- normalized invocation / result schemas
- policy and approval plane
- budget accounting and cost visibility
- event ledger and replay store
- checkpoint / resume protocol
- lineage and artifact IDs
- shared memory tiers and retrieval layer
- model routing service and pinning records
- operator inbox / dashboard surfaces
- evaluation and benchmark harnesses
- promotion / rollback registry

### Agent-specific harnesses or skills

The following should stay local to individual cadres or agent classes:

- prompt scaffolds and context assembly logic
- domain scoring rubrics
- tool allowlists and stop conditions per role
- domain validators beyond the shared baseline
- specialized evidence extractors
- repo/workflow adaptation logic
- browser/computer safety heuristics beyond canonical shared signals
- improvement heuristics for packs, prompts, or skills

### Practical split

| Shared infrastructure concern | Agent-specific concern |
|---|---|
| one approval router | agent-specific risk thresholds and escalation copy |
| one replay/event spine | agent-specific event annotations and summaries |
| one lineage/artifact identity model | agent-specific payload schemas |
| one model router and pin registry | per-agent routing policy and fallback ladder |
| one memory substrate | per-agent memory views, context assemblers, compaction hints |
| one promotion/rollback mechanism | per-agent quality criteria for promotion |

### Why this split matters

If approvals, replay, routing, and lineage live inside each agent harness, AGENT-33 will become a pile of bespoke mini-systems. If every domain heuristic is forced into shared infrastructure, the harness will become bloated and agent specialization will become fake. The correct shape is:

> shared operating substrate, agent-specific cognition and domain logic.

---

## 5) How the Loop 4 phases should be rewritten around ecosystem building

Loop 4’s current phases are still useful, but they should be restated as ecosystem-building steps rather than mostly control-plane construction.

| Current Loop 4 wording | Ecosystem rewrite | What changes in emphasis |
|---|---|---|
| **Phase A — Runtime control plane unification** | **Phase A — Cadre contracts and shared harness** | start by defining agent classes, common invocation/result schemas, policy/replay/budget contracts |
| **Phase B — Dual-surface UX reset** | **Phase B — Layman shell and operator workspace as ecosystem surfaces** | the UI becomes the place where agent work is requested, reviewed, paused, and ingested |
| **Phase C — Durable execution and replay spine** | **Phase C — Execution cadre and durable handoffs** | emphasize planner/executor/queue steward roles and checkpointable inter-agent transfers |
| **Phase D — Bounded memory and lineage layer** | **Phase D — Lineage and ingestion fabric** | memory is framed as the shared evidence/report-back substrate for all cadres |
| **Phase E — Governed browser/computer-use substrate** | **Phase E — Environment specialist cadres** | browser/computer use becomes one specialized cadre with tighter contracts, not a generalized extension of every agent |
| **Phase F — Skill supply chain and packaging decisions** | **Phase F — Improvement cadre and curated skill ecology** | focus on promotion, rollback, lineage, and safe improvement loops instead of packaging alone |

### What Loop 4 language should keep

Loop 4 is still right to emphasize:

- governance as explicit
- normalized events
- bounded memory and lineage
- replay and interruption
- skill lineage and promotion discipline

### What Loop 4 language should change

Loop 4 should stop leading with phrases like:

- control plane
- runtime spine
- capability modules
- platform direction

and instead lead with:

- specialist cadres
- shared harness
- reporting contracts
- ingestion loop
- operator-visible review and promotion

That reframing keeps the architecture grounded in what the agents actually are and how they cooperate.

---

## 6) Additional research gaps needed for a clearer non-hallucinated answer

Loop 3 already surfaced several blocking questions. Loop 5B adds a few ecosystem-specific gaps that should be answered before stronger claims are made.

### Existing Loop 3 gaps that remain central

1. the minimal normalized event schema across tools, workflows, browser use, approvals, and interrupts
2. deterministic vs model-mediated inspector boundaries and their false-positive rates
3. snapshot/lineage storage cost and replay-tree staleness behavior
4. retention and compaction policy for bounded but durable memory
5. the correct boundary between `allow`, `ask`, deny lists, pairing, and operator approval
6. the correct resumable checkpoint unit
7. which browser/computer-use safety signals are actually canonical
8. whether approvals, checkpoints, and operator tasks belong in one directive inbox
9. the right data model for skill lineage / quality / version DAGs

### Additional ecosystem-specific gaps

10. **What is the canonical agent-to-agent handoff schema?**
    - Is the same event model sufficient for inter-agent requests, or is a higher-level artifact contract needed?

11. **How much repo/workflow adaptation should be learned versus declared?**
    - Should each agent class have hand-authored adaptation rules, or can routing/harness layers infer them safely?

12. **What is the promotion rule for self-improvement outputs?**
    - When does an improvement proposal become a promoted pack/prompt/harness change, and what evidence is required?

13. **What are the failure-containment rules for self-learning?**
    - Can a self-learning sandbox ever write directly, or must it remain proposal-only with explicit promotion and rollback?

14. **What panel-consensus mechanism is appropriate for high-impact judgments?**
    - simple strong-model choice, multi-model voting, adversarial review, or operator arbitration?

15. **How should routing performance be measured per cadre?**
    - cost, latency, success rate, operator interruptions, replay fidelity, and promotion outcomes all need cadre-level metrics.

16. **What is the minimum viable operator surface for ecosystem legibility?**
    - if the operator cannot see who acted, why, with what evidence, and what changed, the ecosystem will feel magical rather than trustworthy.

### Most important caution

The most speculative part of the user vision remains **self-learning / self-improvement that changes the system autonomously**. The current evidence supports:

- run analysis
- proposal generation
- skill lineage
- governed promotion

It does **not yet support** claiming that AGENT-33 should autonomously rewrite itself without stricter promotion, rollback, and audit contracts.

---

## Bottom line

The clearest Loop 5B refinement is:

- AGENT-33 should be framed as a **shared harness plus specialist cadres**
- each cadre should have a **known model posture, tool posture, and output contract**
- artifacts should flow back through **hot control ingestion, warm lineage ingestion, and cold evaluation ingestion**
- model routing should follow **purpose, risk, and repetition**, not one generic runtime rule
- Loop 4 should be rewritten around **ecosystem-building**, not mostly platform/control-plane language
- self-learning should remain **proposal-first and promotion-gated** until stronger evidence exists

That framing keeps the architecture closer to the user vision while staying grounded in Loop 3’s actual evidence and Loop 4’s best structural insights.
