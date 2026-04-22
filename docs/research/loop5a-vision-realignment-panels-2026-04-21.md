# Loop 5A Vision Realignment Panels

**Date:** 2026-04-21  
**Program:** AGENT-33 research program  
**Loop:** 5A  
**Artifact type:** Refinement artifact only — challenges the Loop 4 draft and does **not** finalize the roadmap

---

## Purpose

This artifact recenters the Loop 4 draft against the stated user vision using four panel lenses:

- architecture
- DX / operator ergonomics
- feasibility
- product strategy

Panel convergence was strong on one core point: **Loop 4 over-centered governance/control-plane framing and under-centered harness/skills-driven specialized-agent evolution.**

---

## Inputs used

- Research program: `C:\Users\mattm\.copilot\session-state\00d3a405-8501-4e95-9e95-2614f9b754a1\plan.md`
- Loop 3 synthesis: `docs/research/loop3-cross-batch-capability-synthesis-2026-04-21.md`
- Loop 4 draft: `docs/research/loop4-initial-architecture-phase-proposal-2026-04-21.md`

---

## 1) Direct critique of where Loop 4 overemphasizes governance/control-plane concepts

### Main critique

Loop 4 correctly preserved AGENT-33’s governance baseline, but it promoted governance from **guardrail/enabler** to **primary architectural identity**.

### Where the overemphasis appears

1. **The direction statement is governance-first.**  
   Loop 4 defines AGENT-33 as a **“governance-first, event-normalized, dual-surface agent platform.”** That framing is too control-plane centric for a system whose intended center is self-improvement, repo ingestion, self-learning, research, panel judgment, and refined specialized tool use.

2. **Phase A makes runtime control-plane unification the anchor phase.**  
   This turns explicit governance, permission planes, and operator-visible policy state into the dominant architectural program, even though the user vision says adaptive control should often live in **skills, markdown contracts, and harness behavior**.

3. **Checkpoint/review/directive-inbox concepts are treated as central operating primitives.**  
   The vision does not reject approvals or checkpoints, but it rejects letting their overhead dominate. Loop 4 risks building a platform optimized around intervention surfaces instead of high-signal autonomous execution inside bounded skill contracts.

4. **Normalized event/control concepts are treated as prerequisites rather than consequences.**  
   Loop 4 assumes a broad unified event substrate should lead the design. The panels converged on the reverse: **task segmentation, evidence packaging, skill I/O contracts, and siloed agent reporting** should define the runtime shape first; broader normalization should follow from those contracts.

5. **The product framing is too operator-control heavy.**  
   “Layman shell + operator workspace” is useful, but Loop 4 underweights the more important product identity: AGENT-33 as a **research-and-self-improvement harness** that produces clarity, judgments, ingestible artifacts, and specialized repetitive-task acceleration.

6. **Memory, browser use, and skill lifecycle are framed mainly as governed layers.**  
   That is only partially right. Under the user vision, they should be framed first as **specialized bounded capability types** with explicit contracts that reduce hallucination and context overload.

7. **Multi-model and cross-repo/workflow intelligence are underrepresented.**  
   Loop 4 preserves composability, but it does not make “ecosystem of tailored agents with explicit criteria, models, known inputs/outputs” the organizing center.

### Bottom-line critique

Loop 4 reads too much like **“build a better control plane for governed agents”** and not enough like **“build a harness-and-skills ecosystem for specialized agents that improve themselves, ingest evidence, operate in silos, and report back with high-clarity outputs.”**

---

## 2) Corrected architecture direction statement

### Corrected direction

AGENT-33 should evolve toward a **harness-and-skills-driven ecosystem of specialized agents**:

- a **thin runtime spine** that enforces bounded execution, evidence capture, replayability, and safe mutation contracts
- a **skills/harness layer** where adaptive control, retry logic, model choice, task criteria, and context discipline often live
- an **ecosystem of tailored agents** with explicit purpose, known inputs/outputs, model strategy, success criteria, and repetitive-task acceleration
- a **siloed execution model** where subagents work in bounded contexts and report back to the main agent for ingestion, synthesis, and judgment
- a **hallucination-reduction architecture** based on stronger contracts, task segmentation, evidence packaging, and constrained context windows
- a **multi-model, cross-repo, cross-workflow learning posture** that lets AGENT-33 compose evidence across sources without collapsing into one oversized general agent

### What governance becomes under this direction

Governance remains important, but it becomes:

- a **subordinate enabling layer**
- strongest at **skill boundaries and mutation boundaries**
- visible where needed for trust and recovery
- intentionally prevented from dominating normal execution flow

---

## 3) Which current Loop 4 phases should be reframed, merged, split, or renamed

| Current Loop 4 phase | Recommended change | Revised framing |
|---|---|---|
| **Phase A — Runtime control plane unification** | **Split and subordinate** | Split into **A1: skill/runtime contract layer** and **A2: governance semantics and operator policy surfaces**. The skill/harness contract should lead; the governance plane should support it. |
| **Phase B — Dual-surface UX reset** | **Rename and narrow** | Rename to **Agent/Operator Evidence Surfaces**. Focus less on control UX and more on evidence, judgment, replay, research clarity, and intervention only where necessary. |
| **Phase C — Durable execution and replay spine** | **Keep but reframe** | Keep as **Durable Bounded Execution and Evidence Replay**. Its purpose is not just durability; it is bounded subagent work plus ingestible evidence return. |
| **Phase D — Bounded memory and lineage layer** | **Merge partially with F** | Merge memory lineage with skill lineage into **Bounded Context, Evidence Memory, and Lineage**. Emphasize context-fit, summarization, and evidence retention rather than memory infrastructure for its own sake. |
| **Phase E — Governed browser/computer-use substrate** | **Reframe as a capability type** | Rename to **Browser/Computer Use as a Specialized Skill Class**. Treat it as one bounded skill family under harness contracts, not a quasi-separate governance program. |
| **Phase F — Skill supply chain and packaging decisions** | **Move earlier and expand** | Rename to **Specialized Agent and Skill Ecosystem**. Move earlier conceptually because this is closer to the real platform center than a late packaging concern. |

### Additional reframing guidance

- **Merge C + D conceptually** around bounded execution plus evidence-bearing memory.
- **Move F closer to A1/B** because the platform identity should be visible early as a specialized-agent ecosystem.
- **Do not let A2 dominate sequencing.** Governance semantics should not become the bottleneck for all other progress.

---

## 4) Core principles that should replace or subordinate governance-first framing

1. **Harness-first, not control-plane-first.**  
   The main design surface should be the bounded harness/skill contract, not centralized governance machinery.

2. **Specialized agents over generalized agent sprawl.**  
   AGENT-33 should favor tailored agents with explicit criteria, model choice, known inputs/outputs, and narrow task purpose.

3. **Evidence over ambient context.**  
   Agents should return structured findings, citations, diffs, artifacts, and judgments instead of relying on oversized shared conversational context.

4. **Silo first, ingest second.**  
   Subagents should work in bounded silos and report back to the main agent for synthesis rather than sharing one uncontrolled context pool.

5. **Contracts reduce hallucination.**  
   Strong I/O contracts, exact mutation rules where needed, bounded memory, and segmented tasks should be treated as first-class anti-hallucination design.

6. **Adaptive control should often live in skills and markdown.**  
   Retry behavior, model routing, escalation rules, evidence requirements, and stopping conditions should frequently be encoded at the harness/skill layer.

7. **Governance should be sparse, high-signal, and boundary-focused.**  
   Governance matters most at risky mutations, trust transitions, imports/promotions, and recovery points—not as constant procedural overhead.

8. **Multi-model and cross-workflow awareness are strategic, not optional.**  
   The future platform is not one monolithic agent loop; it is a compositional system informed by multiple models, repos, and workflows.

---

## 5) Strongest preserved AGENT-33 strengths under this revised vision

The revised direction does **not** discard the strongest Loop 4 preservation points. It keeps them, but re-centers them.

1. **Governance baseline remains a real strength.**  
   Policy packs, budgets, trust surfaces, and approval concepts still matter; they just stop being the primary product story.

2. **Workflow/DAG execution remains highly valuable.**  
   AGENT-33 already has broad orchestration footing. Under the revised vision, that becomes the execution substrate for bounded specialized agents.

3. **Memory/RAG foundations remain strong.**  
   PostgreSQL, pgvector, hybrid retrieval, and persistence remain useful, especially when redirected toward bounded evidence memory and repo-ingestion support.

4. **Replay, traces, dashboards, and operator tooling remain differentiators.**  
   These become evidence and diagnosis surfaces for specialized-agent work instead of justification for a governance-heavy operating model.

5. **Packs/plugins/trust analytics remain core ecosystem assets.**  
   These are natural foundations for an ecosystem of explicit, tailorable, promotable skills and agents.

6. **Web-first posture remains sound.**  
   The revised vision does not require a distribution reset; it strengthens the agent ecosystem inside the existing product footing.

7. **Compose-not-clone remains correct.**  
   Loop 4 was right to avoid copying one repo wholesale. That principle survives fully.

---

## 6) Key unresolved tensions that must pass to later loops

1. **Bounded memory vs durable learning depth**  
   How much should AGENT-33 freeze, summarize, forget, or accumulate when the system is meant to self-learn across runs and repos?

2. **Harness-encoded control vs operator-visible governance**  
   Which controls should stay in skill/harness contracts, and which must stay explicitly visible in operator policy surfaces?

3. **Checkpoint sparsity vs recovery confidence**  
   How few checkpoints can AGENT-33 use before it loses enough observability or recovery safety to become brittle?

4. **Specialized agent silos vs cross-agent shared context**  
   How much information should be shared directly between agents versus reported back through evidence packages to the main agent?

5. **Evidence-package architecture vs full event normalization**  
   Is a broad normalized event substrate truly necessary early, or can AGENT-33 get most of the value through strong evidence/report contracts first?

6. **Skill openness vs trust-constrained promotion**  
   How open should the future ecosystem be if AGENT-33 wants both high iteration velocity and strong supply-chain trust?

7. **Model-selected routing vs harness-selected routing**  
   Should model choice and routing mainly live in skill definitions, operator policy, or adaptive runtime heuristics?

8. **Browser/computer-use visibility vs reproducible bounded execution**  
   Should browser supervision optimize for human-visible clarity, deterministic replay, or a layered mix?

9. **Operator workspace breadth vs product focus**  
   How much operator surface is actually necessary once bounded specialized agents and better evidence contracts exist?

10. **Self-improvement velocity vs governance burden**  
    How can AGENT-33 improve itself, ingest repos, and refine skills quickly without reintroducing the very checkpoint overhead the user wants to avoid?

---

## Final Loop 5A position

The strongest Loop 5A correction is:

> **AGENT-33 should be framed primarily as a harness-and-skills ecosystem for specialized, evidence-producing, bounded agents — not primarily as a governance/control-plane platform.**

Governance remains important, but under this vision it is **supporting structure**, not the main identity.

This artifact is a refinement input for later loops, not a final roadmap.
