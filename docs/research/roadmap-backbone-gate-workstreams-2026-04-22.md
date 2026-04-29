# Roadmap Backbone Gate Workstreams - 2026-04-22

**Purpose:** decompose Gate 1, Gate 2, and Gate 4 into concrete execution workstreams so the spike program can move from brief-level planning into bounded design and validation work without reopening the roadmap.

---

## Why these gates first

The six-gate set is now stable enough to sequence real work. The first execution frontier should remain:

1. **Gate 1 - Event / report-back / handoff schema**
2. **Gate 2 - Compact task-state / frozen handoff / checkpoint unit**
3. **Gate 4 - Memory lifecycle / provenance / precedence**

These three gates form the contract, state, and memory backbone for the other three:

- Gate 3 telemetry needs stable contracts, replay boundaries, and memory provenance
- Gate 5 environment evidence needs contract-bound replay and bounded memory rules
- Gate 6 promotion and containment need replay, telemetry, and lineage-backed validity

---

## Workstream decomposition principles

Each workstream should:

1. produce a bounded artifact or decision set
2. have a clear dependency boundary
3. avoid hidden implementation commitments
4. preserve replayability, provenance, and rollback posture

These are still **design workstreams**, not implementation slices.

---

## Recommended execution order

### Wave 1 - Contract backbone

1. **G1-W1 - Contract object inventory and boundary rules**
2. **G1-W2 - Event families, statuses, and error semantics**
3. **G1-W3 - Cross-cadre exemplar flows and schema validation pack**

### Wave 2 - Frozen state and handoff backbone

4. **G2-W1 - Checkpoint unit and frozen handoff bundle**
5. **G2-W2 - Recovery semantics and blocked-state vocabulary**
6. **G2-W3 - Compactness validation and worked replay examples**

### Wave 3 - Memory policy backbone**

7. **G4-W1 - Memory classes and sharing boundaries**
8. **G4-W2 - Precedence matrix and retrieval assembly rules**
9. **G4-W3 - Provenance, lineage, and why-retrieved model**
10. **G4-W4 - Correction / forget / redact / prune lifecycle**

This order preserves the intended dependency chain:

- contracts before checkpoints
- checkpoints before replay examples
- contracts and checkpoints before memory precedence and provenance

---

## Workstream table

| Workstream | Parent gate | Goal | Primary output | Depends on |
|---|---|---|---|---|
| `G1-W1` | Gate 1 | Define the stable contract object set and boundaries | Contract object inventory + schema-boundary rules | none |
| `G1-W2` | Gate 1 | Define normalized event families, status states, and structured errors | Event taxonomy + status table + error semantics | `G1-W1` |
| `G1-W3` | Gate 1 | Prove cross-cadre reuse and validation posture | Exemplar flows + schema validators + change policy | `G1-W1`, `G1-W2` |
| `G2-W1` | Gate 2 | Define the checkpoint unit and frozen handoff bundle | Checkpoint model + handoff bundle spec | `G1-W3` |
| `G2-W2` | Gate 2 | Define inspect/replay/repair/resume/rollback semantics | Recovery semantics + blocked-state vocabulary | `G2-W1` |
| `G2-W3` | Gate 2 | Prove compactness and replay behavior on worked examples | Worked replay pack + compactness rules | `G2-W1`, `G2-W2` |
| `G4-W1` | Gate 4 | Define memory classes and sharing boundaries | Memory taxonomy + sharing rules | `G1-W3`, `G2-W1` |
| `G4-W2` | Gate 4 | Define retrieval precedence and assembly rules | Precedence matrix + retrieval assembly rules | `G4-W1` |
| `G4-W3` | Gate 4 | Define provenance and why-retrieved linkage | Lineage model + retrieval introspection model | `G4-W1`, `G4-W2` |
| `G4-W4` | Gate 4 | Define correction and decay lifecycle controls | Correction / forget / redact / prune semantics + worked examples | `G4-W2`, `G4-W3` |

---

## Detailed workstream scopes

## G1-W1 - Contract object inventory and boundary rules

**Goal**

Name and bound the common runtime contract objects so later work does not blur invocation, event, result, handoff, and error surfaces.

**Should produce**

- contract object inventory
- object-by-object field responsibility map
- boundary rule for what belongs in:
  - invocation envelope
  - progress / interrupt event
  - result envelope
  - handoff bundle
  - error envelope

**Must avoid**

- transport binding
- persistence binding
- UI-first redesign of runtime objects

---

## G1-W2 - Event families, statuses, and error semantics

**Goal**

Lock the event-family separation and status vocabulary so execution, approvals, and replay do not collapse into one ambiguous stream.

**Should produce**

- domain / integration / audit event taxonomy
- normalized status state table
- structured error classes
- retry / idempotency semantics
- approval-required and resume mapping

**Must avoid**

- turning policy verdicts into generic execution status
- mixing audit facts and workflow events into one flat event type

---

## G1-W3 - Cross-cadre exemplar flows and schema validation pack

**Goal**

Prove that the contract family is reusable across the minimum three-cadre set before any downstream gate depends on it.

**Should produce**

- three exemplar flows:
  - Research & Ingestion
  - Execution & Orchestration
  - Synthesis & Judgment
- schema validation pack
- additive vs breaking change policy
- UI / CLI / automation consumption check

**Exit signal**

This is the workstream that makes Gate 1 usable by Gate 2 and Gate 4.

---

## G2-W1 - Checkpoint unit and frozen handoff bundle

**Goal**

Define the minimal durable state record and the transportable handoff package without turning either into a transcript dump.

**Should produce**

- checkpoint unit definition
- frozen handoff bundle definition
- persist / recompute / never-freeze rules
- checkpoint-to-contract linkage rules

**Must avoid**

- storing broad ambient context as frozen truth
- letting one cadre's convenience bloat the state model

---

## G2-W2 - Recovery semantics and blocked-state vocabulary

**Goal**

Define how the system and operator interact with blocked, failed, paused, replayed, repaired, resumed, and rolled-back segments.

**Should produce**

- inspect semantics
- replay semantics
- repair semantics
- resume semantics
- rollback semantics
- blocked-state vocabulary

**Must avoid**

- describing UI cards instead of runtime recovery rules
- relying on prose summaries as the recovery substrate

---

## G2-W3 - Compactness validation and worked replay examples

**Goal**

Stress the checkpoint and handoff design against realistic specialist workflows to prove compactness without truth loss.

**Should produce**

- worked example: normal replay
- worked example: blocked-run repair
- worked example: cross-cadre handoff
- compactness review checklist
- operator-legibility check for replay artifacts

**Exit signal**

This workstream is the proving ground for whether Gate 2 remains narrow enough to support Gate 5 and Gate 6 later.

---

## G4-W1 - Memory classes and sharing boundaries

**Goal**

Define what memory types exist and what may or may not be shared across cadres.

**Should produce**

- memory taxonomy
- sharing-boundary rules
- segment-local vs shareable rules
- environment evidence containment rule

**Must avoid**

- treating all persisted information as one memory class
- defaulting to global reuse

---

## G4-W2 - Precedence matrix and retrieval assembly rules

**Goal**

Define what outranks what during retrieval and context assembly so the system cannot silently privilege fuzzy recall over operator or checkpoint truth.

**Should produce**

- precedence matrix
- retrieval assembly rules
- higher-rank suppression rules
- snapshot / evidence / semantic conflict rules

**Must avoid**

- storage-driven truth
- semantic memory outranking active-run checkpoint facts

---

## G4-W3 - Provenance, lineage, and why-retrieved model

**Goal**

Make every material retrieval decision explainable and traceable.

**Should produce**

- provenance object map
- lineage linkage rules
- why-retrieved record model
- retrieval explanation examples

**Must avoid**

- lineage-free retrieval
- free-text provenance notes that cannot support replay or review

---

## G4-W4 - Correction / forget / redact / prune lifecycle

**Goal**

Define how AGENT-33 corrects, suppresses, redacts, or removes memory without losing auditability or rollback reasoning.

**Should produce**

- correction semantics
- forget semantics
- redaction semantics
- prune / decay rules
- rollback-aware supersession example

**Must avoid**

- silent mutation of validated memory
- treating operator correction as low-rank noise

---

## Suggested near-term batching

For practical execution, the safest initial batch is:

1. `G1-W1`
2. `G1-W2`
3. `G2-W1`
4. `G4-W1`

That batch creates the minimum shared vocabulary needed before proving flows, replay semantics, and retrieval precedence in deeper detail.

The second batch should then be:

5. `G1-W3`
6. `G2-W2`
7. `G4-W2`
8. `G4-W3`

The final batch should be:

9. `G2-W3`
10. `G4-W4`

This keeps the early work on foundations and delays worked-example pressure until the object models are stable enough.

---

## Exit condition for the backbone workstream program

The backbone program is only complete when:

- Gate 1 has reusable validated schema objects
- Gate 2 has replayable compact state and frozen handoff semantics
- Gate 4 has defensible memory precedence and lineage rules

At that point, the program can safely intensify work on:

- Gate 3 telemetry
- Gate 5 environment evidence
- Gate 6 promotion and containment

without letting those later gates invent their own incompatible assumptions.
