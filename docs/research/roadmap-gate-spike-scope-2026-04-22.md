# Roadmap Gate Spike Scope - 2026-04-22

**Purpose:** convert the six roadmap gates into explicit spike scopes with deliverables, validators, sequencing, and rollback boundaries before any official roadmap lock is attempted.

---

## Operating rule

These spikes are not implementation phases. They are **validation spikes** that determine whether the refined roadmap is safe to lock.

Each spike must produce:

1. required artifacts
2. validators or measurable checks
3. rollback / containment boundaries
4. a lock recommendation for the affected roadmap phases

---

## Recommended execution order

1. **Gate 1 - Event / report-back / handoff schema**
2. **Gate 2 - Frozen handoff / checkpoint unit**
3. **Gate 4 - Memory lifecycle / provenance / precedence**
4. **Gate 3 - Context-budget and skill telemetry**
5. **Gate 5 - Browser/computer-use evidence and watchdogs**
6. **Gate 6 - Skill promotion / rollback / containment**

This order reflects dependency weight rather than surface importance: contracts, state, and memory discipline come before telemetry, environment specialists, and improvement promotion.

---

## Scope summary

| Gate | Goal | Primary outputs | Unlocks |
|---|---|---|---|
| Gate 1 | Stable cross-cadre contracts | Versioned schemas, validators, examples, error taxonomy | A1, A2, C |
| Gate 2 | Trustworthy frozen handoffs and replay | Checkpoint unit, handoff bundle, replay / resume / repair rules | B, C |
| Gate 3 | Evidence that routing and skill use help | Telemetry events, metrics, reports, routing explanations | D, later tuning of B/F |
| Gate 4 | Memory discipline and retrieval truthfulness | Precedence matrix, lifecycle policy, provenance and introspection rules | D, F |
| Gate 5 | Bounded and auditable environment work | Canonical evidence bundle, watchdog taxonomy, intervention guidance | E |
| Gate 6 | Reversible skill and improvement promotion | Promotion scorecard, evaluation harness, rollback ancestry, containment rules | F |

---

## Gate 1 - Event / report-back / handoff schema

**Why this spike exists**

Every later phase depends on stable envelopes for invocation, progress, interruption, results, and specialist-to-specialist handoffs.

**Scope questions**

- What must every specialist invocation receive?
- What must every specialist emit on progress, interruption, completion, and failure?
- What belongs in a handoff bundle versus an attached artifact?
- How are domain events separated from integration events and audit / replay events?

**Required outputs**

- versioned schemas for invocation, progress, interrupt, result, and handoff events
- a schema registry with examples
- structured error taxonomy
- retry / idempotency semantics
- compatibility rules and change policy
- reference adapters proven across at least three cadres

**Validators**

- schema validators pass against exemplar runs
- three-cadre handoff flow works without bespoke envelope forks
- UI, CLI, and automation surfaces can consume the same contracts

**Rollback / containment boundary**

- do not freeze transport or storage implementation choices here
- do not collapse domain, integration, and replay events into one blob schema

---

## Gate 2 - Compact task-state / frozen handoff / checkpoint unit

**Why this spike exists**

Durable execution only helps if pause, resume, replay, and handoff preserve the right truth and drop the wrong noise.

**Scope questions**

- What is the minimal checkpoint unit?
- What is a frozen handoff bundle made of?
- What survives pause / resume / replay?
- How do inspect, repair, retry, and rollback work from that bundle?

**Required outputs**

- checkpoint unit definition
- frozen handoff bundle specification
- inspect / replay / resume / repair semantics
- partial-failure handling rules
- rollback-point definition
- one operator recovery walkthrough

**Validators**

- replay succeeds from a frozen artifact bundle without relying on prose-only continuity
- a blocked run can be inspected, repaired, and resumed through the defined model
- handoff bundles stay compact under realistic specialist workflows

**Rollback / containment boundary**

- do not silently widen the bundle until it becomes a context dump
- do not couple the bundle format to one UI or storage adapter

---

## Gate 3 - Context-budget and skill-activation telemetry

**Why this spike exists**

The roadmap assumes specialist routing, skills, and compact state actually help. This spike measures whether that is true.

**Scope questions**

- Are context budgets being respected?
- Do skills reduce ambiguity or add prompt bloat?
- Does routing improve time-to-success and operator burden?
- Can the system explain why a route or skill was chosen?

**Required outputs**

- telemetry event set for context pressure, routing, and skill activation
- metrics definitions for time-to-first-success, retry storms, discovery failure, and operator escalations
- routing / skill explanation model
- reporting surface or report format for analysis

**Validators**

- telemetry is visible on representative runs
- at least one skill/routing scenario shows measurable benefit or a defensible null result
- the system can explain why a skill or route was selected

**Rollback / containment boundary**

- do not turn advisory telemetry into hard truth signals
- do not collect metrics that have no operator or roadmap decision value

---

## Gate 4 - Memory lifecycle + provenance / precedence

**Why this spike exists**

Memory and retrieval will corrupt trust unless the system can explain what outranks what, why something was retrieved, and how stale or incorrect material is corrected.

**Scope questions**

- Which memory classes exist?
- What outranks what at retrieval time?
- How are provenance and claim-to-evidence lineage preserved?
- How can operators correct, forget, or redact memory?

**Required outputs**

- memory class taxonomy
- precedence matrix across operator directives, frozen snapshots, retrieval, working memory, and long-term memory
- provenance model and lineage rules
- lifecycle policy for retain / decay / consolidate / prune
- retrieval introspection and correct / forget / redaction semantics

**Validators**

- retrieval decisions can be explained in terms of precedence and provenance
- at least one correction / forget workflow is demonstrated
- memory rules remain compatible with routing and evaluation ingestion

**Rollback / containment boundary**

- do not let storage choices define retrieval truth rules
- do not allow untraceable memory fusion across cadres

---

## Gate 5 - Browser/computer-use evidence and watchdog signals

**Why this spike exists**

Environment specialists create the highest audit and trust risk. They need tighter evidence and watchdog semantics than general tool use.

**Scope questions**

- What counts as canonical browser/computer-use evidence?
- What watchdog signals matter and how are they labeled?
- How should intervention and replay work for risky environment actions?
- How is sensitive evidence redacted without destroying auditability?

**Required outputs**

- canonical environment evidence bundle
- watchdog taxonomy and threshold guidance
- replay attachment model
- intervention and triage states
- sensitive-evidence handling rules

**Validators**

- at least one environment workflow is replay-auditable through the canonical bundle
- watchdog-triggered intervention states are understandable to operators
- redaction preserves enough evidence for review

**Rollback / containment boundary**

- do not generalize browser/computer evidence rules into all tool work
- do not ship environment autonomy before the evidence bundle is stable

---

## Gate 6 - Self-improvement promotion / rollback / containment

**Why this spike exists**

Improvement must stay reversible, reviewable, and bounded. Promotion without lineage, scorecards, and rollback would make the platform harder to trust and maintain.

**Scope questions**

- Which changes remain proposal-only?
- What evidence qualifies a skill or improvement for promotion?
- How is rollback ancestry preserved?
- What containment rules apply to promoted changes?

**Required outputs**

- promotion scorecard
- evaluation harness
- rollback ancestry model
- containment rules
- skill / plugin compatibility and validation policy
- release and deprecation guidance

**Validators**

- a proposed change can be scored, promoted, and rolled back through the defined model
- third-party and internal skills follow the same compatibility discipline
- promotion remains blocked when evidence is insufficient

**Rollback / containment boundary**

- do not permit direct self-mutation outside proposal and promotion paths
- do not allow ecosystem growth to bypass compatibility and rollback discipline

---

## Recommended immediate follow-on

After this grouped scope artifact, the next concrete move should be:

1. create an individual design brief for **Gate 1**
2. create an individual design brief for **Gate 2**
3. create an individual design brief for **Gate 4**

Those three spikes define the contract, state, and memory backbone that the other three spikes depend on.
