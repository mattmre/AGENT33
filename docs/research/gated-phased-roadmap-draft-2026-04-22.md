# Gated Phased Roadmap Draft - 2026-04-22

**Date:** 2026-04-22  
**Program:** AGENT-33 research program  
**Artifact type:** Conditional roadmap skeleton - refined after second-pass panel review, not final roadmap lock

---

## Status and framing

This document converts the preserved research corpus, the council final audit, and the second-pass EVOKORE-guided roadmap refinement panels into a **gated phased roadmap draft**.

It is:

- a **conditional roadmap skeleton**
- aligned to the Loop 5 corrections
- constrained by the council's **PASS WITH CONDITIONS** verdict
- refined by architecture, UI, DX, and backend critique

It is **not**:

- final official roadmap lock
- an unconditional sequencing commitment
- proof that all architecture assumptions have been validated
- a backend-lockable or implementation-lockable plan by itself

This draft exists so AGENT-33 can move from broad research toward a **phase-contract-oriented planning structure** without pretending that unresolved contracts, state models, and evidence semantics are already settled.

---

## Governing rules

### Rule 1 - Council audit constraint

The roadmap may be drafted, but it may only be **locked** after six required spikes are completed:

1. minimal normalized event + report-back + handoff schema
2. compact task-state / frozen handoff / checkpoint unit
3. context-budget and skill-activation telemetry
4. memory lifecycle + provenance / precedence
5. browser/computer-use evidence and watchdog signals
6. self-improvement promotion / rollback / containment

### Rule 2 - Second-pass panel constraint

The roadmap direction is **approved with modifications**, but the phase plan is not lock-grade unless it:

- separates domain concepts, use cases, adapters, and infrastructure more clearly
- narrows the UX phase around real user flows and evidence grammar
- upgrades all gates from open research questions to measurable lock criteria
- makes recovery, replay, introspection, and rollback first-class concerns

---

## Direction statement

AGENT-33 should evolve toward a:

> **shared harness plus specialist-cadre ecosystem with bounded execution, evidence-bound reporting, frozen handoffs, lineage-backed evaluation, summary-first operator surfaces, and sparse boundary-focused governance**

This draft keeps the strongest accepted direction from the research corpus:

- harness-first, not control-plane-first
- specialist agents over generalized sprawl
- evidence over ambient context
- silo first, ingest second
- deterministic validation where possible
- governance as supporting structure, not product identity
- UI as evidence and intervention surface, not subsystem exposure

---

## Core bounded contexts and domain objects

The roadmap is now framed so phases attach to explicit backend and product boundaries rather than blending everything into one platform layer.

| Bounded context / role | Core objects | Primary roadmap home |
|---|---|---|
| Shared harness and platform ports | `InvocationEnvelope`, `ProgressEvent`, `ResultEnvelope`, `HandoffBundle`, `ArtifactRef` | Phase A1 |
| Governance and exception review | `ApprovalRequest`, `PolicyVerdict`, `TrustDecision`, `RecoveryDirective` | Phase A2 |
| Execution orchestration | `TaskGraph`, `CheckpointRecord`, `ReplaySpan`, `ExecutionAttempt` | Phase C |
| Synthesis and judgment | `EvidenceBundle`, `JudgmentReport`, `ClaimCoverage`, `BlockedReason` | Phase B and Phase C |
| Research and ingestion | `IngestionRecord`, `LineageRecord`, `MemoryEntry`, `RoutingObservation` | Phase D |
| Environment specialists | `EnvironmentEvidenceBundle`, `WatchdogSignal`, `InterventionTrace` | Phase E |
| Skill ecology and improvement | `SkillManifest`, `PromotionProposal`, `ReleaseRecord`, `RollbackRecord` | Phase F |

---

## Pre-lock spike track

Before official roadmap lock, the six spikes are the validation workstreams that decide whether these phases are safe to lock.

The spikes are not side notes. They are the architecture-validation backbone for:

- stable contracts
- trustworthy replay and recovery
- memory precedence
- operator legibility
- bounded environment work
- reversible improvement

---

## Phase structure

### Phase A1 - Contract narrowing and shared harness

**Purpose**

Define the common operating substrate for specialist cadres without collapsing the harness into a god-platform.

**Includes**

- versioned invocation / progress / interrupt / result contracts
- handoff artifact schema
- artifact identity and reference rules
- context-budget policy hooks
- skill metadata and routing / pinning rules
- reference adapters and validators
- structured error taxonomy and retry / idempotency semantics

**Primary homes**

- shared harness
- execution entry/exit ports
- reusable contract registry

**Lock criteria**

- Gate 1 is satisfied
- contracts are UI-usable, CLI-usable, and automation-usable
- at least one reference flow works across three specialist cadres without bespoke envelope variants

---

### Phase A2 - Governance and exception review

**Purpose**

Keep governance sparse, visible, and exception-oriented by giving approvals, policy checks, and recovery semantics a stable home outside the core execution contracts.

**Includes**

- approval plane and review surfaces
- policy verdict semantics
- exception thresholds and escalation rules
- recovery directives and rollback triggers
- trust / intervention semantics visible to operators

**Primary homes**

- approval and policy use cases
- operator exception review
- boundary-focused control surfaces

**Lock criteria**

- approval and exception semantics are defined against Phase A1 contracts
- intervention states use a shared status vocabulary
- rollback and recovery directives are replay-auditable

---

### Phase B - Evidence and judgment surfaces

**Purpose**

Turn the product surface into a shared evidence grammar for layman and operator users instead of exposing raw subsystem menus.

**Includes**

- layman request -> progress -> approval wait -> result path
- operator triage -> blocked-run recovery -> intervention -> resume / close path
- one dashboard / inbox for approvals, blocked work, alerts, and promotions
- summary-first evidence ladder with drill-down into citations, checkpoints, and replay
- explicit judgment view: verdict, confidence, unresolved questions, challenged assumptions
- role-based onboarding, progressive disclosure, and shared status vocabulary
- UI / CLI / automation parity for core flows

**Primary homes**

- layman shell
- operator workspace
- synthesis and judgment presentation layer

**Lock criteria**

- Phase A1 and A2 outputs are consumable as stable product surfaces
- one end-to-end task is completable through both UI and CLI / automation surfaces
- replay is summary-first and checkpoint-backed
- intervention remains exception-oriented, not the default posture

---

### Phase C - Bounded execution, frozen handoffs, and replay

**Purpose**

Make specialist work durable, resumable, inspectable, and factually grounded through typed artifact bundles rather than loose prose continuity.

**Includes**

- planner / executor / queue steward use cases
- durable queue and checkpoint / resume
- frozen handoff bundle definition
- approval-aware execution and interruption-safe review points
- inspect / replay / repair / resume flows
- rollback points and partial-failure handling

**Primary homes**

- execution cadre
- handoff adapters
- checkpoint and replay services

**Lock criteria**

- Gate 1 is satisfied
- Gate 2 is satisfied
- replay and resume work from a frozen artifact bundle, not prose summary only
- operator recovery paths are defined for inspect, retry, repair, resume, and rollback

---

### Phase D - Evidence memory, lineage, and ingestion

**Purpose**

Turn memory and lineage into evidence-bound services with explicit precedence, provenance, and ingestion pathways rather than an undifferentiated persistence layer.

**Includes**

- hot / warm / cold ingestion paths
- memory lifecycle rules: retain, decay, consolidate, prune
- memory precedence across operator directives, snapshots, retrieval, and working memory
- claim-to-evidence lineage
- frozen reusable context units
- routing, evaluation, and skill-activation observations
- "why was this retrieved?" introspection and correct / forget controls

**Primary homes**

- research and ingestion cadre
- lineage services
- memory policy services

**Lock criteria**

- Gate 3 is satisfied
- Gate 4 is satisfied
- provenance and precedence are legible to operators and debuggable by developers
- routing and evaluation ingestion do not bypass lineage rules

---

### Phase E - Environment specialist cadres

**Purpose**

Treat browser/computer use as bounded specialist capability families with stronger evidence and watchdog requirements than normal tool work.

**Includes**

- browser/computer specialist cadre framing
- canonical evidence bundles and replay attachments
- watchdog and anomaly signals
- intervention clarity for risky environment actions
- redaction and triage ergonomics where evidence is sensitive

**Primary homes**

- environment specialists
- watchdog adapters
- environment replay evidence

**Lock criteria**

- Gate 5 is satisfied
- browser/computer work is replay-auditable through canonical evidence bundles
- watchdog-triggered intervention states are understandable to operators

---

### Phase F - Skill promotion and improvement sandbox

**Purpose**

Make skill evolution and self-improvement proposal-driven, lineage-aware, reversible, and safe for a growing ecosystem of specialist cadres.

**Includes**

- curated skill and plugin ecology
- skill manifests, compatibility rules, and deprecation policy
- skill / plugin authoring kit with validate and local test harness support
- promotion scorecards and release ancestry
- rollback records and containment boundaries
- proposal-only self-improvement sandbox tied to evidence and evaluation

**Primary homes**

- improvement cadre
- skill ecosystem maintenance
- promotion / release / rollback services

**Lock criteria**

- Gate 6 is satisfied
- third-party and internal skill promotion share the same compatibility and rollback discipline
- self-improvement remains proposal-only until promotion evidence clears containment rules

---

## Cross-phase operating principles

These principles apply across all phases:

1. **Shared operating substrate, agent-specific cognition**
2. **Domain core, use cases, adapters, and infrastructure stay separable**
3. **Evidence-bound outputs over ambient shared context**
4. **Compact state and frozen handoffs over sprawling run continuity**
5. **Summary-first evidence, drill-down second**
6. **Deterministic checks gate; model-scored signals advise**
7. **Governance stays sparse, visible, and exception-oriented**
8. **Recovery, replay, and rollback are product features, not debugging extras**
9. **UI, CLI, and automation should expose the same core truth**
10. **World-model ambition stays a horizon, not present identity**

---

## Spike gate definitions as roadmap lock criteria

### Gate 1 - Contract and handoff lock criteria

The roadmap is not lockable until there are:

- versioned invocation / progress / interrupt / result / handoff schemas
- machine-readable validators, examples, and compatibility tests
- a structured error taxonomy with retry / idempotency semantics
- reference adapters across at least three cadres
- explicit distinction among domain events, integration events, and audit / replay events

### Gate 2 - Frozen handoff and checkpoint lock criteria

The roadmap is not lockable until there is:

- a clear checkpoint unit and frozen handoff bundle definition
- inspect / replay / resume / repair semantics from that bundle
- idempotent retry and partial-failure recovery behavior
- at least one rollback point and one operator recovery walkthrough

### Gate 3 - Context-budget and skill telemetry lock criteria

The roadmap is not lockable until telemetry can show:

- context-budget behavior and compaction pressure
- skill-activation benefit or lack of benefit
- time-to-first-success
- discovery failure and retry-storm patterns
- operator escalation frequency and docs-to-success path quality
- why routing or skill matching occurred

### Gate 4 - Memory precedence and lineage lock criteria

The roadmap is not lockable until there is:

- a precedence table covering operator directives, frozen snapshots, retrieval, working memory, and long-term memory
- provenance and claim-to-evidence lineage on retrieved material
- "why retrieved" introspection
- correct / forget / redaction controls where applicable
- lifecycle rules for retention, decay, consolidation, and pruning

### Gate 5 - Browser evidence and watchdog lock criteria

The roadmap is not lockable until there is:

- a canonical browser/computer-use evidence bundle
- watchdog thresholds with operator-meaningful labels
- replay attachments and intervention traces
- bounded intervention states and triage guidance
- auditable handling for sensitive or redacted evidence

### Gate 6 - Skill promotion and improvement containment lock criteria

The roadmap is not lockable until there is:

- a proposal-only boundary for self-improvement changes
- a promotion scorecard and evaluation harness
- rollback ancestry and release traceability
- compatibility / deprecation / validation rules for skills and plugins
- executable containment rules for promoted changes

---

## Roadmap posture by certainty

| Bucket | Items |
|---|---|
| **Directionally settled** | shared harness; specialist cadres; evidence-bound outputs; frozen handoffs; contracted narrowing; validity-graph direction; summary-first operator surfaces |
| **Refined but still conditional** | A1/A2 split; evidence/judgment-first UX framing; execution replay and recovery discipline; memory precedence and introspection; skill promotion sandbox |
| **Spike-gated** | contract schemas; checkpoint units; telemetry thresholds; memory precedence; browser evidence; self-improvement containment |
| **Explicitly deferred** | learned world-model runtime; latent planners replacing workflows; scalar reward collapse; stronger autonomy claims without replayable evidence |

---

## What this draft unlocks

This roadmap draft is sufficient to start:

- planning work in a coherent phase-contract structure
- converting the six spikes into explicit scoped research / design artifacts
- aligning future sessions around shared bounded contexts and gate criteria
- preserving UI, DX, and backend concerns in the roadmap instead of bolting them on later

It does **not** unlock:

- final roadmap acceptance
- unconditional sequencing commitments
- implementation against unresolved contracts as if they were already settled

---

## Recommended next step

The immediate next move after this refined draft is:

> **turn each of the six gate domains into an explicit scoped spike artifact with required deliverables, validators, and rollback boundaries**

---

## Final position

AGENT-33 is now past the "research only, no structure" stage.

It is ready for:

- a **refined gated roadmap draft**
- a **spike-driven contract validation stage**

It is not yet ready for:

- final roadmap lock
- implementation sequencing commitments that assume the six gates are already resolved
