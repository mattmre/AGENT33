# LeWorldModel Paper Panels — AGENT-33 Update Strategy

**Date:** 2026-04-21  
**Program:** AGENT-33 research program  
**Artifact type:** Supplemental paper-integration strategy artifact — not a final roadmap

---

## Status and framing

This artifact integrates a targeted three-panel review of the paper:

- **LeWorldModel: Stable End-to-End Joint-Embedding Predictive Architecture from Pixels**
- arXiv: `2603.19312v2`

The paper does **not** replace the existing Loop 5 direction. It is used as a **discipline check** on the current AGENT-33 plan, especially around:

- task-specific agents and harnessed models
- hallucination reduction through bounded execution
- compact state and faster planning
- surprise / implausibility scoring
- reward graphing as a future evaluation direction

This is **not**:

- a proposal to turn AGENT-33 into a learned world-model platform
- a justification for adding RL-first architecture
- a replacement for explicit contracts, evidence, replay, and operator trust surfaces

---

## Repo and plan context used

This update was evaluated against the current research direction established by:

- `docs/research/loop5a-vision-realignment-panels-2026-04-21.md`
- `docs/research/loop5b-ecosystem-architecture-panels-2026-04-21.md`
- `docs/research/loop5c-anti-hallucination-and-context-limit-panels-2026-04-21.md`
- `docs/functionality-and-workflows.md`
- `docs/default-policy-packs.md`
- `docs/research/session126-p69b-api-contract.md`
- `docs/research/session126-p69b-ux-spec.md`

Important current-repo realities:

- AGENT-33 already has strong conceptual surfaces for **traces**, **evaluations**, **autonomy budgets**, **improvement operations**, and **replay-like review flows**
- several of those surfaces are still **in-memory** or partially wired, so new ideas should layer onto existing substrate rather than create a second disconnected control system
- the current plan already favors:
  - specialized cadres
  - shared harnesses
  - bounded execution
  - evidence-bound outputs
  - deterministic validation where possible

---

## Panels run

Three panel-style reviews were executed:

1. **Architecture & Planning Panel**
2. **Feasibility Research Panel**
3. **Data / ML / Reward Graph Panel**

### Cross-panel convergence in one sentence

The paper is **highly useful as a design analogy for stable bounded planning, compact run state, and probeable validation signals**, but it is **not** a direct architecture template for AGENT-33.

---

## What transfers directly vs metaphorically vs not at all

### Directly transferable

1. **Compact bounded state helps planning and validity**
   - For AGENT-33 this means **compact task-state capsules** and **frozen handoff bundles**, not large ambient conversational state.

2. **Task-agnostic substrate with task-specific execution**
   - This reinforces the current AGENT-33 direction:
     - shared harness
     - specialist cadres
     - job-specific contracts
     - route-by-task-class execution

3. **Simplicity-first operating discipline**
   - The paper’s value is partly that it reduces moving parts and avoids heuristic sprawl.
   - For AGENT-33 this supports:
     - deterministic-first repetitive-task modes
     - fewer overlapping heuristics
     - more stable contracts and validators

4. **Probing and surprise as evaluation tools**
   - This maps well to:
     - implausibility monitors
     - unsupported-claim detection
     - route anomaly detection
     - handoff drift checks

### Metaphorical only

1. **Anti-collapse regularization**
   - For AGENT-33 this is a useful analogy, not a direct algorithm.
   - The practical anti-collapse mechanism is:
     - specialist cadres
     - bounded task classes
     - narrow I/O contracts
     - reward graphs that do not collapse quality into one score

2. **Latent planning**
   - AGENT-33 should plan over:
     - task graphs
     - segment bundles
     - evidence artifacts
     - validation outcomes
   - not over learned continuous latent trajectories

3. **Compact latent geometry**
   - The useful translation is **normalized run-state cards** and **compact execution summaries**, not Gaussian latent-space engineering.

### Should be rejected for the near-term roadmap

1. A learned JEPA/world-model runtime for general AGENT-33 execution
2. Replacing explicit evidence and contracts with learned latent control
3. Treating surprise as truth rather than as a review signal
4. Treating reward-free as evaluation-free

---

## Main strategic update

The paper strengthens the existing Loop 5 conclusion:

> **AGENT-33 should be a harness-and-skills-driven ecosystem of specialized agents whose execution is bounded, compactly represented, replayable, and probeable.**

The important update is not “build a world model.”  
The important update is:

- make specialist execution more **compact**
- make handoffs more **frozen and typed**
- make improvement signals more **graphable**
- make anomaly detection more **structured**

---

## Reward graphing: proposed AGENT-33 definition

### Definition

**Reward graphing** should mean a **lineage-linked validity graph** over:

- runs
- segments
- contracts
- evidence
- policy events
- interventions
- outcomes
- promotions / rollbacks

It should **not** mean a single opaque scalar reward score.

### Why this fits AGENT-33

This gives the platform:

- credit assignment without premature RL coupling
- clearer skill and routing evaluation
- better promotion evidence
- post-run anomaly localization
- a shared evaluation surface across specialist cadres

### Minimum graph objects

**Nodes**

- `Run`
- `Segment`
- `Artifact`
- `ContractCheck`
- `PolicyEvent`
- `Intervention`
- `SkillVersion`
- `ModelRoute`
- `LearningSignal`

**Edges**

- `produced`
- `validated_by`
- `violated_by`
- `cites`
- `escalated_to`
- `routed_via`
- `promoted_from`
- `rolled_back_to`

### Signal families

Do **not** collapse these into one undifferentiated score:

1. **Evidence coverage**
2. **Contract adherence**
3. **Convergence / stall behavior**
4. **Replayability**
5. **Policy / governance hygiene**
6. **Operator burden**
7. **Novelty / reuse**
8. **Outcome quality**
9. **Implausibility / surprise**

### Deterministic vs model-scored

**Deterministic first**

- schema validity
- tool scope compliance
- exact-diff checks
- evidence refs present
- replay completeness
- intervention counts
- policy exceptions
- benchmark / gate pass-fail
- lineage integrity

**Model-scored second**

- semantic evidence relevance
- contradiction likelihood
- novelty
- implausibility / anomaly ranking
- fuzzy claim-support alignment

Rule:

> **Deterministic signals gate; model-scored signals rank, route, or request review.**

---

## Proposed update strategy for the plan

### Add

1. **Compact Task-State Capsule standard**
   - define a small machine-readable bundle for segment handoffs
   - include:
     - task class
     - active skills
     - allowed tools
     - budget refs
     - evidence refs
     - contract refs
     - last stable output refs

2. **State-root / frozen handoff bundle spike**
   - validate the smallest viable durable execution state for pause, resume, replay, and specialist handoff

3. **Deterministic-first reward graph MVP**
   - use current traces/evaluations/improvement surfaces as the starting substrate
   - graph deterministic validity signals first
   - add model-scored overlays later

4. **Surprise / implausibility monitors**
   - advisory monitors for:
     - unsupported-claim leaps
     - abnormal retry storms
     - unexpected route changes
     - contract transition anomalies
     - missing evidence where evidence is normally expected

5. **Simplicity-first repetitive-task mode**
   - for repeated task classes:
     - pin specialist agent
     - pin skill bundle
     - pin validator set
     - reduce heuristic routing variance

### Modify

1. **Shared harness phase framing**
   - Phase A should explicitly include compact run-state and handoff semantics, not only governance/control semantics.

2. **Durable execution framing**
   - Durable execution should emphasize **frozen segment bundles** and **bounded recovery**, not only event normalization.

3. **Lineage and memory framing**
   - Lineage should capture:
     - why a claim was accepted
     - what evidence supported it
     - what validators passed
     - what anomaly flags were raised

4. **Improvement and learning framing**
   - improvement should be driven by:
     - reward-graph outcomes
     - validator trends
     - operator burden
     - rollback history
   - not vague global “agent quality”

### Defer

1. Learned execution world models
2. RL-style reward optimization as a primary control mechanism
3. General latent planners replacing explicit task graphs
4. Any large new training substrate before trace/replay/evaluation instrumentation matures

---

## Repo-fit recommendations

The best next moves fit the current repo because AGENT-33 already has adjacent surfaces for:

- traces
- evaluations
- autonomy budgets
- reviews
- improvements
- policy packs

That means the near-term strategy should be:

1. **extend existing instrumentation**
2. **normalize run-validity schemas**
3. **improve handoff/state discipline**
4. **avoid creating a second planning stack**

The most important repo-fit warning is:

> do not add a separate world-model-like runtime that competes with workflows, traces, evaluations, and policy surfaces already present in AGENT-33.

---

## Minimal viable artifacts to add later

These are **not** implementation commitments yet, but they are the clearest candidate outputs from this paper review:

1. `docs/research/run-validity-graph-schema.md`
2. `docs/research/compact-task-state-capsule.md`
3. `docs/research/surprise-and-implausibility-monitors.md`

Possible future code targets once the roadmap is locked:

1. `engine/src/agent33/evaluation/reward_graph_models.py`
2. additions to trace/evaluation/improvement surfaces for graph emission

---

## Top failure modes if this paper is over-applied

1. **Domain mismatch**
   - physical-control world models do not map directly onto symbolic tool-using agents

2. **Metric collapse**
   - one reward number hides real trade-offs between safety, truthfulness, usefulness, and cost

3. **False-confidence anomaly scoring**
   - surprise is a useful alarm, not a correctness proof

4. **Overcompression**
   - bounded state is good, but overcompressed state can destroy evidence fidelity

5. **Second-system runtime sprawl**
   - building a new learned planning layer beside existing workflows/replay/evaluation surfaces would increase complexity without immediate payoff

---

## Final cross-panel recommendations

1. **Adopt compact task-state / frozen handoff concepts into the plan**
2. **Define reward graphing as a lineage-backed validity graph, not scalar RL reward**
3. **Use deterministic-first signals as the foundation for reward graphing**
4. **Add surprise / implausibility monitors as advisory validation signals**
5. **Strengthen simplicity-first repetitive-task harnesses**
6. **Defer learned world-model ambitions**

### Final position

The paper is a **strong confirmation artifact** for the current AGENT-33 direction when interpreted correctly.

It supports:

- specialist agents
- bounded execution
- compact state
- probeable runtime quality
- structured anomaly detection
- graph-based improvement signals

It does **not** justify replacing the current explicit-contract, evidence-bound, replayable architecture with a learned latent planner.
