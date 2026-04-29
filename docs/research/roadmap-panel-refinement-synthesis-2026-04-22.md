# Roadmap Panel Refinement Synthesis - 2026-04-22

**Purpose:** preserve the second-pass EVOKORE-guided critique of the gated roadmap draft and record the concrete roadmap changes adopted from those panels.

**Panels represented:**

1. Architecture and phase-planning panel
2. UI / wiring panel
3. Developer-experience panel
4. Backend architecture patterns panel

---

## Panel verdicts

| Panel | Verdict | Core message |
|---|---|---|
| Architecture / phase planning | **APPROVED WITH MODIFICATIONS** | The roadmap direction is strong, but the phase plan was too coarse and needed split phases plus measurable gates |
| UI / wiring | **NEEDS WORK** | Phase B described surfaces, not user flows; evidence, judgment, dashboard, and progressive disclosure needed stronger treatment |
| Developer experience | **NEEDS IMPROVEMENT** | The draft was too runtime-centric and under-specified CLI, automation, schemas, recovery, onboarding, and plugin authoring |
| Backend architecture | **Strong direction, not backend-lockable yet** | The draft mixed domain concepts, use cases, and infrastructure; it needed clearer bounded contexts and rollback-safe contracts |

---

## Strong convergence themes

All four panels converged on the following changes:

1. **Split the original Phase A**
   - shared contracts and harness concerns should not be blended with approvals and policy surfaces
   - adopted rewrite:
     - **Phase A1 - Contract narrowing and shared harness**
     - **Phase A2 - Governance and exception review**

2. **Narrow the UX phase around evidence and judgment**
   - the roadmap should describe user flows, not just product surfaces
   - Phase B should focus on:
     - layman request -> result path
     - operator triage / intervention / resume path
     - dashboard / inbox
     - replay and evidence drill-down

3. **Treat replay and recovery as core product behavior**
   - inspect / replay / repair / resume / rollback are not implementation details
   - durable execution without these flows would create durable wrongness rather than durable truth

4. **Separate memory policy from storage substrate**
   - memory lifecycle, precedence, provenance, and retrieval introspection are policy concerns
   - storage, indexing, and telemetry are supporting infrastructure

5. **Make all gates measurable**
   - the original draft described what needed to be studied
   - the refined draft must state what has to exist before roadmap lock is allowed

6. **Raise product ergonomics to first-class roadmap concerns**
   - UI / CLI / automation parity
   - shared status vocabulary
   - progressive disclosure
   - structured errors
   - onboarding and capability discovery
   - plugin and skill authoring ergonomics

---

## Concrete roadmap changes adopted

### 1. New phase structure

The roadmap was rewritten to use:

1. **Phase A1 - Contract narrowing and shared harness**
2. **Phase A2 - Governance and exception review**
3. **Phase B - Evidence and judgment surfaces**
4. **Phase C - Bounded execution, frozen handoffs, and replay**
5. **Phase D - Evidence memory, lineage, and ingestion**
6. **Phase E - Environment specialist cadres**
7. **Phase F - Skill promotion and improvement sandbox**

### 2. Explicit bounded contexts and domain objects

The refined roadmap now names explicit bounded-context homes for:

- shared harness and platform ports
- governance and exception review
- execution orchestration
- synthesis and judgment
- research and ingestion
- environment specialists
- skill ecology and improvement

Representative domain objects now include:

- `InvocationEnvelope`
- `HandoffBundle`
- `TaskGraph`
- `CheckpointRecord`
- `EvidenceBundle`
- `PolicyVerdict`
- `PromotionProposal`

### 3. UI-specific roadmap upgrades

The roadmap now explicitly requires:

- layman and operator user flows
- one operator dashboard / inbox
- summary-first evidence ladder
- explicit judgment views
- role-based onboarding and progressive disclosure
- exception-oriented intervention instead of default operator micromanagement

### 4. DX-specific roadmap upgrades

The roadmap now explicitly requires:

- versioned schemas and validators
- structured errors and retry semantics
- UI / CLI / automation parity
- inspect / replay / resume / repair verbs as core surfaces
- capability discovery and routing explanation
- plugin / skill authoring kit expectations in Phase F

### 5. Backend-specific roadmap upgrades

The roadmap now explicitly separates:

- domain core
- use cases
- adapters
- infrastructure

It also makes rollback, compatibility, and replaceability part of the gate framing rather than leaving them implicit.

---

## Gate upgrades adopted

The refined roadmap now treats the six spikes as **roadmap lock criteria**, not just open questions.

### Gate changes with highest impact

- **Gate 1** now requires versioned schemas, validators, compatibility rules, structured errors, and reference adapters
- **Gate 2** now requires a clear checkpoint unit plus inspect / replay / resume / repair behavior from frozen handoff bundles
- **Gate 3** now requires telemetry for context budgets, skill benefit, time-to-first-success, retry storms, and operator escalations
- **Gate 4** now requires a formal precedence table, provenance, why-retrieved introspection, and correct / forget controls
- **Gate 5** now requires canonical browser evidence bundles plus auditable watchdog and intervention traces
- **Gate 6** now requires proposal-only self-improvement, promotion scorecards, rollback ancestry, evaluation harnesses, and skill/plugin validation rules

---

## Important risks still called out

The refinement panels still warned about the following failure modes:

- the shared harness could become a god-platform if boundaries drift
- UI work could solidify unstable contracts too early
- replay could become durable hallucination if frozen handoffs are underspecified
- memory and lineage could become contaminated without precedence discipline
- improvement and plugin promotion could outrun contract maturity
- browser/computer-use could expand before canonical evidence is stable

These risks remain active until the six scoped spikes materially reduce them.

---

## Resulting posture

The roadmap is now stronger as:

- a strategic direction document
- a phase-structure document
- a product and backend boundary document

It is still not:

- the final roadmap lock
- an implementation authorization artifact
- proof that the six spike domains are resolved

The correct next move remains:

> **scope each gate as its own spike artifact and use those spike results to decide whether official roadmap lock is justified**
