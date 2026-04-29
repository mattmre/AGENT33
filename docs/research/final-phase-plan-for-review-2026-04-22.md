# AGENT-33 Final Phase Plan for Review - 2026-04-22

**Date:** 2026-04-22  
**Program:** AGENT-33 research program  
**Artifact type:** Review-ready phase plan - architected and fully fleshed out, pending final review rather than unconditional roadmap lock

---

## 1. Plan posture

This document is the current **final review plan** for AGENT-33.

It integrates:

- the preserved research corpus
- the council final audit
- the gated roadmap draft
- the second-pass roadmap refinement panels
- the six gate briefs
- the backbone workstream decomposition

It is intended to answer:

> **If AGENT-33 is to move from research and synthesis into a real build program, what is the architected phase plan, what must happen first, and how do we keep the platform aligned with bounded specialist agents, layman-usable surfaces, and reversible improvement?**

This document is:

- review-ready
- architected around bounded contexts, contracts, and validation
- explicit about dependencies and gates
- suitable for final expert review

This document is **not**:

- proof that the six gates are already solved
- authorization to skip spike work
- a claim that official plan lock is already approved

---

## 2. Core strategic position

AGENT-33 should be built as:

> **a shared harness plus specialist-cadre ecosystem with bounded execution, evidence-bound reporting, frozen handoffs, lineage-backed evaluation, summary-first operator surfaces, and proposal-only reversible improvement**

The platform should optimize for:

1. **specialized agents over broad general-agent sprawl**
2. **artifacts and evidence over ambient context**
3. **bounded execution over loose long-run continuity**
4. **operator-legible judgment over hidden automation**
5. **reversible improvement over silent self-mutation**
6. **layman usability through guided evidence surfaces, not cryptic subsystem menus**

---

## 3. Governing constraints

The following constraints govern the entire plan:

### Constraint A - Six-gate requirement

Official roadmap lock remains blocked until the following are sufficiently validated:

1. event / report-back / handoff schema
2. compact task-state / frozen handoff / checkpoint unit
3. context-budget and skill-activation telemetry
4. memory lifecycle / provenance / precedence
5. browser/computer-use evidence and watchdog signals
6. self-improvement promotion / rollback / containment

### Constraint B - Architecture separation

The plan must preserve explicit separation among:

- domain core
- use cases
- adapters
- infrastructure

### Constraint C - Product legibility

The product surface must remain layman-usable and operator-legible from the first meaningful release.

That means the plan must explicitly provide:

- a simple ask -> answer -> why flow for layman users
- a real operator dashboard / inbox, not just backend wiring
- summary-first evidence with drill-down levels
- progressive disclosure between layman and operator views
- approval-wait and blocked-run states explained in user language
- exception-oriented intervention posture rather than governance-first friction

### Constraint D - Improvement containment

No phase may introduce silent high-impact self-mutation.

---

## 4. Architectural foundation

## 4.1 Bounded contexts

The program should continue to use the following bounded-context map:

| Bounded context | Core objects | Primary concern |
|---|---|---|
| Shared harness and platform ports | `InvocationEnvelope`, `ProgressEvent`, `ResultEnvelope`, `HandoffBundle`, `ArtifactRef` | stable runtime contracts |
| Governance and exception review | `ApprovalRequest`, `PolicyVerdict`, `TrustDecision`, `RecoveryDirective` | approvals, policy, exception handling |
| Execution orchestration | `TaskGraph`, `CheckpointRecord`, `ReplaySpan`, `ExecutionAttempt` | bounded execution and resumability |
| Synthesis and judgment | `EvidenceBundle`, `JudgmentReport`, `ClaimCoverage`, `BlockedReason` | evidence interpretation and human-legible judgment |
| Research and ingestion | `IngestionRecord`, `LineageRecord`, `MemoryEntry`, `RoutingObservation` | evidence intake, lineage, memory, evaluation observations |
| Environment specialists | `EnvironmentEvidenceBundle`, `WatchdogSignal`, `InterventionTrace` | browser/computer-use under stronger supervision |
| Skill ecology and improvement | `SkillManifest`, `PromotionProposal`, `ReleaseRecord`, `RollbackRecord` | proposal-driven improvement and reversible promotion |

## 4.2 Cross-cutting rules

These rules apply to every phase:

1. **Artifacts over prose**
2. **Replay-linked truth over ambient history**
3. **Deterministic checks gate; model-scored signals advise**
4. **Policy links remain visible; policy control remains sparse**
5. **UI consumes runtime truth; UI does not define runtime truth**
6. **Memory never silently outranks operator or checkpoint-backed facts**
7. **Environment evidence remains bounded by default**
8. **Improvement remains proposal-only until explicitly promoted**

---

## 5. Program structure

The full plan should be executed in two layers:

1. **Layer 0 - Validation and architecture-hardening program**
   - resolves the six gates to a proof-grade level

2. **Layer 1 - Implementation phase program**
   - builds the durable shared harness, surfaces, and specialist ecosystem on top of those validated assumptions

This is the key design correction from earlier drafts:

- the plan must not jump straight from research into feature buildout
- it must first validate the contract/state/memory/evidence/containment backbone

---

## 6. Layer 0 - Validation and architecture-hardening program

## Phase 0 - Gate program

**Goal**

Resolve the six gates well enough that the implementation phases can proceed on validated assumptions rather than optimistic architecture.

### 0.1 Gate order

The program order remains:

1. **Gate 1 - Event / report-back / handoff schema**
2. **Gate 2 - Compact task-state / frozen handoff / checkpoint unit**
3. **Gate 4 - Memory lifecycle / provenance / precedence**
4. **Gate 3 - Context-budget and skill-activation telemetry**
5. **Gate 5 - Browser/computer-use evidence and watchdog signals**
6. **Gate 6 - Self-improvement promotion / rollback / containment**

### 0.2 Why this order

- Gate 1 defines the shared contract family
- Gate 2 defines the frozen state and replay substrate
- Gate 4 defines memory truth discipline on top of contract and checkpoint objects
- Gate 3 then measures whether narrowing and routing actually help
- Gate 5 and Gate 6 use those validated assumptions for high-risk environment work and improvement

### 0.3 Backbone workstream program

The first workstream program should remain:

#### Batch 1

1. `G1-W1 - Contract object inventory and boundary rules`
2. `G1-W2 - Event families, statuses, and error semantics`
3. `G2-W1 - Checkpoint unit and frozen handoff bundle`
4. `G4-W1 - Memory classes and sharing boundaries`

#### Batch 2

5. `G1-W3 - Cross-cadre exemplar flows and schema validation pack`
6. `G2-W2 - Recovery semantics and blocked-state vocabulary`
7. `G4-W2 - Precedence matrix and retrieval assembly rules`
8. `G4-W3 - Provenance, lineage, and why-retrieved model`

#### Batch 3

9. `G2-W3 - Compactness validation and worked replay examples`
10. `G4-W4 - Correction / forget / redact / prune lifecycle`

### 0.4 Later-gate workstream program

The later three gates should also be decomposed explicitly before implementation lock:

#### Gate 3 workstreams

1. `G3-W1 - Telemetry event taxonomy and durable export rules`
2. `G3-W2 - Routing / skill explanation records and metric definitions`
3. `G3-W3 - Decision-relevant reporting views and worked telemetry examples`

#### Gate 5 workstreams

4. `G5-W1 - Environment evidence bundle and replay attachments`
5. `G5-W2 - Watchdog taxonomy, intervention states, and redaction-aware auditability`
6. `G5-W3 - Environment evidence promotion path into general memory`

#### Gate 6 workstreams

7. `G6-W1 - Improvement lifecycle and promotion scorecard`
8. `G6-W2 - Evaluation harness, blast-radius matrix, and staged rollout policy`
9. `G6-W3 - Rollback ancestry, rollback triggers, rollback-failure escalation, and cascade rollback semantics`

### 0.5 Proof-grade output of Layer 0

Layer 0 should yield:

- validated contract family
- stable frozen-state and replay model
- defensible memory precedence and lineage rules
- explainable telemetry and routing evidence
- canonical environment evidence bundle
- promotion and containment model for improvement

For this plan, **proof-grade** means each gate has:

1. named artifacts and schemas
2. worked examples against realistic flows
3. deterministic validators where applicable
4. explicit rollback / containment boundaries
5. a clear statement of what remains advisory only

### 0.6 Exit criteria for Layer 0

Layer 0 is complete only when:

1. **Gate 1** has reusable schemas, validators, and three-cadre exemplar flows
2. **Gate 2** has a stable checkpoint unit, frozen handoff bundle, and worked inspect / replay / repair / resume / rollback examples
3. **Gate 3** has durable replay-usable telemetry, route/skill explanation records, and decision-relevant metrics
4. **Gate 4** has a memory taxonomy, precedence matrix, provenance model, why-retrieved explanations, and correction lifecycle
5. **Gate 5** has a canonical environment evidence bundle, watchdog taxonomy, replay attachments, and redaction-aware auditability
6. **Gate 6** has an improvement lifecycle, promotion scorecards, evaluation harness, rollback ancestry, staged rollout policy, blast-radius matrix, rollback triggers, rollback-failure escalation, and cascade rollback semantics
7. no downstream phase depends on unvalidated hidden assumptions
8. the program has passed a named **Layer 0 -> Layer 1 decision gate**

### 0.7 Layer 0 -> Layer 1 decision gate

At the end of Layer 0, the program must take one of three outcomes:

1. **GO**
   - all six gate outputs are strong enough to begin Layer 1 sequencing, and the cross-gate integration gate (§0.8) has been formally evaluated and passed with designated reviewers having reviewed the integration evidence artifacts

2. **REVISE**
   - implementation phases remain plausible, but one or more gate or interface areas need another bounded validation pass

3. **STOP**
   - a critical assumption has failed and the implementation sequence must not be locked as currently framed

### 0.8 Cross-gate integration gate

Layer 0 is not complete if the gates only pass in isolation. The program must also prove:

1. telemetry observations remain advisory under Gate 4 precedence rules
2. checkpoint, lineage, artifact, and retrieval references use one compatible namespace across Gate 2 and Gate 4
3. environment evidence promotion into shared memory is validated under Gate 4 rules rather than bypassing them
4. promotion scorecards and rollback ancestry in Gate 6 consume Gate 3 and Gate 4 outputs without turning telemetry into de facto authority

The cross-gate integration gate is not passed by assertion. It requires a designated human reviewer to sign off on evidence that each of the four integration requirements has been satisfied across the combined gate output set. This sign-off is a prerequisite for a GO outcome at the Layer 0 -> Layer 1 decision gate.

---

## 7. Layer 1 - Implementation phase program

Layer 1 is the actual build program once the backbone has been sufficiently validated.

## Phase 1 - Shared harness and contract runtime

**Source phase:** Phase A1  
**Primary aim:** turn the Gate 1 contract family into the stable shared runtime substrate

### Scope

- versioned invocation / progress / interrupt / result contracts
- handoff artifact schema
- artifact identity and reference model
- routing and pinning hooks
- contract registry and validators
- structured error taxonomy

### Architecture focus

- ports and adapters around core contract objects
- no god-platform drift
- runtime-first boundaries

### Depends on

- Gate 1 complete

### Deliverables

- shared contract registry
- reference adapter set
- validator pack
- compatibility policy

### Exit criteria

- three cadres use the same contract family without bespoke forks
- UI, CLI, and automation can consume the same contract objects
- error and retry semantics are machine-usable and reviewable
- the shared contract family already carries the references needed for approval, checkpoint, and lineage attachment

### Non-goals

- final operator surface buildout
- full checkpoint / replay semantics
- memory-policy decisions

---

## Phase 2 - Governance and exception review

**Source phase:** Phase A2  
**Primary aim:** define policy, approval, escalation, and recovery semantics as bounded runtime meaning rather than letting them drift into ad hoc product behavior

### Scope

- approval and policy semantics
- policy verdict semantics
- exception thresholds
- deterministic gates vs advisory signals
- approval message primitives
- intervention vocabulary
- rollback and recovery directives

### Architecture focus

- governance as a separate bounded context
- exception-oriented control, not blanket ceremony
- deterministic enforcement attachment over generic policy prose

### Depends on

- Phase 1
- validated approval and event semantics from Gate 1

### Deliverables

- policy and approval use-case layer
- approval message primitives and message types
- status vocabulary for paused / blocked / approval-required / resumable
- one worked example of policy verdict gating execution through runtime contracts

### Exit criteria

- approvals and interventions attach cleanly to runtime contracts
- exception states are replay-auditable
- policy logic does not collapse into generic execution state
- deterministic gates are separated from advisory signals

### Non-goals

- broad layman UX buildout
- environment specialist controls

---

## Phase 3 - Evidence and judgment surfaces

**Source phase:** Phase B  
**Primary aim:** deliver the layman/operator product surfaces as evidence and judgment flows rather than subsystem menus

### Scope

- layman ask -> answer -> why flow
- operator dashboard / inbox shell
- approval-wait and blocked-run explanation states
- summary-first evidence ladder
- explicit judgment view
- replay artifact surface
- onboarding, progressive disclosure, and status vocabulary
- UI / CLI / automation parity for core flows

### Product surface model

#### Layman flow

- ask
- progress
- `progress` means task name, current stage, and run status are visible while subsystem internals remain hidden from the layman view
- the default view on first run is the layman view; transition to the operator view is an explicit opt-in through role selection at onboarding or deploying-operator configuration; operator features must not force additional complexity into the layman view
- approval wait if needed
- answer
- why this answer / why not more confidence
- `low_confidence` and `insufficient_evidence` results surface their caveat within the why-answer explanation in user language; the raw status token is not the standalone layman-facing output

#### Operator inbox and dashboard

- approval requests
- blocked runs
- low-confidence / insufficient-evidence notices
- escalations
- promotion review items *(surface slot reserved in Phase 3; inactive until Phase 7 delivers the promotion lifecycle and operator opt-in is confirmed)*

#### Evidence ladder levels

1. **Level 1 - Summary**
2. **Level 2 - Cited artifacts**
3. **Level 3 - Checkpoints and replay spans**
4. **Level 4 - Challenged assumptions and unresolved questions**

#### Approval UX expectations

- approval-wait copy must explain what is waiting and why
- blocked-state copy must explain what is missing or denied
- approval surfaces should be context-rich, not governance-first clutter
- all shared status vocabulary states that surface to layman users must carry user-language descriptions, not only machine-readable labels; `low_confidence`, `insufficient_evidence`, and `resumable` each require plain-language explanation

#### Shared status vocabulary

- `running`
- `approval_required`
- `blocked`
- `resumable`
- `low_confidence`
- `insufficient_evidence`
- `completed`

### Architecture focus

- surface grammar driven by evidence and checkpoint truth
- exception-oriented intervention
- accessibility and cognitive-load control
- replay as explanation surface, not only recovery plumbing

### Depends on

- Phase 1
- Phase 2
- Gate 2 complete
- Gate 4 complete

### Deliverables

- layman shell flow model
- operator dashboard / inbox model
- replay and evidence drill-down model
- evidence ladder and approval UX model
- role-based onboarding model, including a first-run path from zero to submitted first question to answered question without requiring architecture knowledge; minimal required steps for install, model connection, role selection, and first task; and confirmation that the layman role is the default entry point

### Exit criteria

- one end-to-end task works across UI and CLI / automation
- replay is summary-first and checkpoint-backed
- operators can understand blocked reasons, approvals, and evidence sufficiency without reading subsystem internals
- the layman ask -> answer -> why loop is explicit and testable as a product flow
- progressive disclosure between layman and operator views is demonstrably functional end to end
- a first-run user can move from install and model connection through role selection to a first answered question without needing architecture documentation

### Non-goals

- raw API/admin shell as the primary product identity
- full environment specialist UI

---

## Phase 4 - Bounded execution, frozen handoffs, and replay

**Source phase:** Phase C  
**Primary aim:** make specialist execution durable, replayable, resumable, and factually grounded

### Scope

- planner / executor / queue steward use cases
- checkpoint / resume
- frozen handoff bundles
- inspect / replay / repair / resume / rollback flows
- partial-failure handling

### Architecture focus

- execution use cases over typed artifacts
- checkpoint service and replay service boundaries
- no transcript-dump durability

### Depends on

- Phase 1
- Gate 2 complete

Phase 4 planning and schema work may begin after Gate 2 completes. Checkpoint and replay implementation is blocked until Phase 3 has locked the replay and evidence drill-down surface model required by the Phase 3 <-> Phase 4 interface contract.

### Deliverables

- checkpoint model implementation plan
- replay model implementation plan
- blocked-state and recovery semantics
- cross-cadre handoff model

### Exit criteria

- replay succeeds from frozen artifact bundles
- blocked-run repair and resume are explicit and bounded
- execution surfaces do not rely on ambient prior conversation

### Non-goals

- long-run unbounded autonomous continuity
- environment specialist evidence rules

---

## Phase 5 - Evidence memory, lineage, ingestion, and telemetry

**Source phase:** Phase D  
**Primary aim:** turn evidence, memory, and lineage into bounded services with explicit precedence and measurable routing/skill observations

### Scope

- hot / warm / cold ingestion
- memory lifecycle rules
- provenance and precedence
- retrieval introspection
- routing and evaluation observations
- context-budget and skill telemetry

### Architecture focus

- memory policy separated from storage substrate
- telemetry as durable analysis and runtime observability, not truth oracle
- lineage as a shared audit backbone
- telemetry remains advisory unless explicitly re-approved by policy and human review

### Depends on

- Phase 1
- Phase 4
- Gate 3 complete
- Gate 4 complete

### Deliverables

- memory policy service plan
- lineage and provenance model
- routing / skill telemetry model
- retrieval explanation surfaces

### Exit criteria

- retrieval can explain what was chosen and why
- telemetry is replay-usable and decision-relevant
- semantic memory cannot outrank operator or checkpoint-backed truth
- telemetry-derived observations do not gain authority without explicit re-approval

### Non-goals

- unconstrained long-term memory growth
- metric theater without roadmap or operator value

---

## Phase 6 - Environment specialist cadres

**Source phase:** Phase E  
**Primary aim:** add browser/computer-use as bounded specialist capabilities with canonical evidence and watchdog posture

### Scope

- environment specialist cadre model
- environment evidence bundles
- replay attachments
- watchdog taxonomy and triage
- redaction-aware environment review

### Architecture focus

- stronger evidence and watchdog semantics than ordinary tool work
- environment evidence stays bounded by default
- any promotion of environment evidence into shared memory must re-enter through Gate 4 precedence and provenance rules

### Depends on

- Phase 4
- Phase 5
- Gate 5 complete

### Deliverables

- environment evidence bundle model
- intervention and triage model
- local/cloud-capable evidence posture
- explicit promotion path from environment evidence to general memory

### Exit criteria

- environment workflows are replay-auditable
- watchdogs are operator-readable
- redaction preserves auditability
- environment evidence ownership and promotion boundaries are explicit

### Non-goals

- broad autonomous browser behavior without audit-grade evidence
- turning environment specialists into general super-agents

---

## Phase 7 - Skill promotion and improvement sandbox

**Source phase:** Phase F  
**Primary aim:** make ecosystem growth and self-improvement proposal-driven, lineage-backed, and reversible

### Scope

- skill / pack / prompt / routing candidate lifecycle
- promotion scorecards
- evaluation harnesses
- rollback ancestry
- revocation / deprecation
- proposal-only sandbox for self-improvement

### Architecture focus

- candidate -> validated -> review_required -> promoted / published -> revoked / rolled_back
- low-trust candidate posture
- no silent high-impact mutation
- staged rollout and blast-radius control are mandatory, not optional
- cascade rollback propagates to assets with declared dependency on the rolled-back asset; assets outside that dependency boundary stay untouched unless the operator explicitly extends scope; blast-radius class sets the maximum cascade propagation scope

### Depends on

- Phase 5
- Phase 6 (partial - core promotion lifecycle work can begin after Phase 5; environment-related improvement assets remain blocked until Phase 6 delivers the environment evidence bundle and promotion path)
- Gate 6 complete

### Deliverables

- promotion and rollback policy
- evaluation harness plan
- improvement asset lifecycle model
- containment rules for internal and third-party assets
- blast-radius matrix
- staged rollout policy
- rollback triggers, rollback-failure escalation, and cascade rollback semantics

### Exit criteria

- improvements can be proposed, scored, promoted, and rolled back through one consistent model
- internal and external assets follow the same validation discipline
- proposal journals and approved lifecycle state remain distinct
- no environment or runtime-facing improvement path bypasses proposal-only containment
- blast-radius matrix has been exercised against at least one worked multi-asset promotion and one worked rollback scenario, demonstrating that scope boundaries are correctly enforced
- a rollback-failure escalation path and a cascade rollback scenario have been worked against realistic flows, not only documented as policy

### Non-goals

- autonomous self-learning deployment
- scalar-reward-driven self-modification

---

## 7.5 Cross-phase interface contracts

The following interfaces must be explicit before implementation sequencing is treated as stable:

### Phase 1 <-> Phase 2

- approval and policy semantics attach to contract objects by reference
- Phase 2 does not redefine runtime objects owned by Phase 1

### Phase 2 <-> Phase 3

- Phase 3 consumes the shared status vocabulary defined in Phase 2 without redefining its semantics
- approval-wait and blocked-run states shown in Phase 3 derive their content from Phase 2 policy verdict and recovery directive objects rather than ad hoc UX copy
- Phase 3 renders Phase 2 outputs in user-legible form; it does not own or extend governance logic

### Phase 2 <-> Phase 4

- blocked-state and recovery enforcement use one shared status vocabulary
- policy verdicts can gate execution and replay without duplicating checkpoint logic

### Phase 3 <-> Phase 4

- Phase 3 defines the replay explanation surface model while Phase 4 implements checkpoint and replay mechanics; both must use the same Gate 2 replay and checkpoint object shapes
- Phase 3 may not invent replay surface vocabulary that Phase 4 mechanics cannot directly produce
- the replay and evidence drill-down model produced in Phase 3 becomes an interface commitment that Phase 4 is required to satisfy

### Phase 4 <-> Phase 5

- checkpoint, lineage, artifact, and retrieval references use one compatible namespace
- Phase 5 extends Phase 4 artifacts; it must not invent a parallel replay or lineage substrate

### Phase 5 <-> Phase 6

- environment evidence stays bounded by default
- promotion from environment evidence into shared memory requires explicit Gate 4-style precedence and provenance handling

### Phase 5 <-> Phase 7

- telemetry remains advisory in promotion scorecards unless explicitly elevated by policy and human review
- rollback ancestry and lineage refs consume the same traceable identifiers as replay and memory surfaces

---

## 8. First implementation-ready slices

The build program should avoid trying to ship the full platform at once. The first slices should be:

### Slice 1 - Layman ask -> answer -> why loop

Cadres:

- layman shell
- operator dashboard / inbox
- Synthesis & Judgment
- operator review

Why first:

- highest direct value for layman and operator usability
- proves the product surface is not just backend framing
- exercises summary-first evidence, approval wait, and explanation posture early

Dependency note:

- a thinner pre-slice prototype of ask -> answer with evidence summary only may be used for internal validation after Gate 2 completion; pre-prototype outputs must not be exposed to layman users before Gate 4 completes, and Slice 1 is not considered shippable until the why-depth is grounded in retrieval explanations

Guardrails:

- only operator directives, policy refs, checkpoint-backed facts, and citation-backed evidence may feed first-release judgment surfaces
- telemetry observations remain advisory only

### Slice 2 - Research dossier loop

Cadres:

- Research & Ingestion
- Synthesis & Judgment
- operator review

Why second:

- strongest existing research alignment
- high evidence density
- lower action-risk than environment or self-improvement flows

### Slice 3 - Bounded execution loop

Cadres:

- planner
- executor
- queue / checkpoint steward
- operator recovery

Why third:

- proves replay and repair posture on real execution work after explanation surfaces are concrete

### Slice 4 - Environment specialist loop

Cadres:

- browser/computer specialist
- watchdog / approval surfaces

Why later:

- highest audit and trust sensitivity

### Slice 5 - Improvement sandbox loop

Cadres:

- improvement analyst
- skill curator
- promotion judge

Why last:

- depends on the strongest lineage, telemetry, and rollback posture

---

## 9. Major program risks and mitigations

| Risk | Why it matters | Mitigation in this plan |
|---|---|---|
| Shared harness becomes a god-platform | destroys replaceability and clarity | preserve bounded contexts and contract-first ports |
| Checkpoints become transcript dumps | durable wrongness replaces durable truth | Gate 2 compactness rules and worked replay validation |
| Telemetry becomes theater or false authority | weakens operator trust and improvement quality | Gate 3 keeps advisory signals advisory and requires decision value |
| Memory becomes ambient authority | retrieval silently overrules evidence and operators | Gate 4 precedence matrix and provenance model |
| UI stabilizes unstable assumptions | major churn and misleading product behavior | Phase 3 depends on Gate 2 and Gate 4 completion, not early recovery semantics |
| Improvement outruns validation | ecosystem drift and silent regression | Gate 6 proposal-only lifecycle, scorecards, rollback ancestry, staged rollout, and blast-radius controls |
| Rollback fails or cascades unpredictably | partial reversions can worsen trust and operations | Gate 6 requires rollback triggers, rollback-failure escalation, and cascade rollback semantics |
| Environment evidence leaks into shared memory incorrectly | high-risk artifacts can distort future decisions | Phase 5 <-> Phase 6 interface forces re-validation under Gate 4 precedence rules |

---

## 10. What remains deferred

The following remain explicitly out of scope for the near-term implementation plan:

- learned world-model runtime
- latent planner replacement of explicit workflows
- scalar reward collapse
- autonomous self-learning without explicit promotion gates
- broad governance-heavy product identity

---

## 11. Final sequencing recommendation

The program should proceed in the following order:

1. finish **Layer 0** gate validation with the backbone batches first
2. validate telemetry, environment evidence, and improvement containment on top of that backbone
3. pass the Layer 0 -> Layer 1 **GO / REVISE / STOP** decision gate plus the cross-gate integration gate
4. lock the implementation sequence only after the gate evidence is accepted
5. execute **Layer 1** beginning with:
   - Phase 1 shared harness and contract runtime
   - Phase 2 governance and exception review
   - Phase 3 evidence and judgment surfaces
6. ship the first implementation-ready slice through the layman ask -> answer -> why loop inside the operator dashboard / inbox shell
7. ship the research dossier loop second
8. intensify into bounded execution, memory/lineage/telemetry, environment specialists, and improvement sandbox in that order

---

## 12. Final position for review

This is the strongest current plan because it does all of the following at once:

- preserves the harness-first, specialist-agent vision
- addresses layman/operator UX as real flows rather than abstract surfaces
- gives the backend clear bounded contexts and dependency structure
- treats replay, memory, telemetry, and improvement as first-class architectural concerns
- keeps high-risk capabilities gated behind evidence and rollback discipline

The plan is now detailed enough for:

- final expert review
- another adversarial challenge round if desired
- later conversion into execution tracking without rewriting the architecture from scratch

It is not yet an approved lock.

It is the **final review plan**.
