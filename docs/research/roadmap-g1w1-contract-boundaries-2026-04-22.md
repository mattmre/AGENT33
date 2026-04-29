# Roadmap G1-W1 - Contract Object Inventory and Boundary Rules

**Date:** 2026-04-22  
**Program:** AGENT-33 research program  
**Parent gate:** Gate 1 - Event / report-back / handoff schema  
**Workstream:** G1-W1

---

## Purpose

Define the common runtime object set for the Gate 1 contract family so later work can assign statuses, events, validators, replay links, and handoff semantics to the right object boundaries.

This workstream answers:

> **What are the core runtime contract objects, and what belongs in each one versus what must stay outside it?**

---

## Why this workstream exists

The Gate 1 brief identified five major contract objects:

1. `InvocationEnvelope`
2. `ProgressEvent`
3. `ResultEnvelope`
4. `HandoffBundle`
5. `ErrorEnvelope`

Without explicit boundary rules:

- status and policy semantics will leak across objects
- later checkpoint design will bloat to compensate
- result objects will silently become handoff or replay containers
- UI or transport assumptions will distort runtime contracts

---

## Contract object inventory

| Object | Primary role | Produced by | Consumed by | Must not become |
|---|---|---|---|---|
| `InvocationEnvelope` | Defines the bounded unit of work entering a segment | coordinator, planner, upstream cadre | active specialist, policy/preflight checks | a progress log, a checkpoint, or a result object |
| `ProgressEvent` | Emits segment-state facts during execution | active specialist or runtime harness | dashboards, replay, monitors, approvals, trace collectors | the source of truth for final outputs |
| `ResultEnvelope` | Carries the completion claim and structured output of a segment | active specialist after completion | downstream cadres, operator surfaces, evaluation, ingestion | a handoff package, a full checkpoint, or a failure transcript |
| `HandoffBundle` | Transfers only the bounded downstream context needed for the next specialist | upstream specialist or orchestrator | downstream specialist, replay, inspection | a full transcript dump or a universal context snapshot |
| `ErrorEnvelope` | Carries machine-usable failure and denial semantics | runtime harness, specialist, approval/policy layer | retry logic, operator surfaces, replay, evaluation | free-form prose-only diagnostics |

---

## Shared reference objects

The major contract objects should depend on shared reference types rather than embedding large blobs by default.

Recommended shared reference set:

- `ArtifactRef`
- `PolicyRef`
- `BudgetRef`
- `StateRef`
- `LineageRef`
- `ContractCheckRef`
- `CheckpointRef`

These references should remain stable across objects so replay, memory, and improvement work can attach to common identifiers rather than copied payloads.

---

## Boundary rules by object

## 1. `InvocationEnvelope`

**Role**

The `InvocationEnvelope` defines the bounded execution assignment for one segment.

**Owns**

- objective
- constraints
- policy refs
- budget refs
- allowed tools
- input artifact refs
- expected output schema
- caller / source identity

**Must not own**

- incremental progress history
- final structured output
- operator decision history
- replay attachments

**Boundary rule**

If a field exists only because execution has already started, it does not belong in the `InvocationEnvelope`.

---

## 2. `ProgressEvent`

**Role**

The `ProgressEvent` is the runtime emission unit for execution-state facts during a segment.

**Owns**

- event id
- event type
- run / segment identity
- current state ref
- status
- operator action required flag
- evidence refs available at that point
- budget delta
- timestamp

**Must not own**

- the authoritative task assignment
- the authoritative final output payload
- the entire downstream handoff package

**Boundary rule**

A `ProgressEvent` may point at state, evidence, or artifacts, but it must not replace the objects it references.

---

## 3. `ResultEnvelope`

**Role**

The `ResultEnvelope` is the completion claim for a segment.

**Owns**

- summary
- structured payload
- confidence
- citations
- lineage refs
- contract check refs
- follow-on recommendations
- promotion / review flag
- insufficient-evidence flag

**Must not own**

- incremental execution timeline
- full replay state
- downstream-specialist-specific transfer constraints
- retry semantics for errors

**Boundary rule**

The `ResultEnvelope` answers **what the segment claims it produced**, not **how the entire run unfolded**.

---

## 4. `HandoffBundle`

**Role**

The `HandoffBundle` is the bounded transfer package for another specialist.

**Owns**

- source and target agent classes
- objective transfer
- input artifact refs
- checkpoint ref
- required contract refs
- open questions
- blocked reasons
- expected output schema
- handoff reason

**Must not own**

- the full upstream transcript
- every upstream event
- global memory state
- operator-facing replay presentation

**Boundary rule**

If downstream success does not require a field, it should stay out of the `HandoffBundle`.

---

## 5. `ErrorEnvelope`

**Role**

The `ErrorEnvelope` is the machine-usable failure or denial unit.

**Owns**

- error code
- error class
- retryable flag
- idempotent reentry flag
- operator review requirement
- evidence refs
- caused-by ref

**Must not own**

- the full textual narrative of a run
- policy state as a generic failure substitute
- success payloads

**Boundary rule**

If a consumer needs to decide whether to retry, escalate, deny, or inspect, the answer belongs in the `ErrorEnvelope`, not buried in prose.

---

## Field ownership rules

The following high-risk field types should have only one primary home:

| Field type | Primary home | Why |
|---|---|---|
| objective / constraints | `InvocationEnvelope` | execution assignment should not drift across objects |
| status-in-time | `ProgressEvent` | timeline facts belong in event history |
| final structured claim | `ResultEnvelope` | completion output should not be reconstructed from event noise |
| downstream transfer constraints | `HandoffBundle` | handoff should stay bounded and explicit |
| retry / escalation semantics | `ErrorEnvelope` | failure handling must remain machine-usable |

---

## Boundary rules that apply across all objects

1. **References over copies**
   - prefer refs to artifacts, checkpoints, and lineage objects instead of duplicating payloads

2. **Runtime-first, not transport-first**
   - object shape should be defined by execution semantics, not event bus or storage convenience

3. **Replay-linked, not replay-bloated**
   - objects should be replay-addressable without each one becoming a replay dump

4. **UI-consuming, not UI-owned**
   - UI may consume these objects, but UI convenience must not define their boundaries

5. **Policy-linked, not policy-collapsed**
   - policy refs belong in objects where needed; policy verdicts should not blur execution assignment, progress, results, and errors into one surface

---

## Immediate implications for next workstreams

This workstream sets up:

- **G1-W2**
  - event families and statuses can now be assigned without object confusion

- **G2-W1**
  - checkpoint and handoff units can now reference stable contract objects rather than inventing new hybrid payloads

- **G4-W1**
  - memory taxonomy can now distinguish contract objects, checkpoints, artifacts, and downstream transfer packages correctly

---

## Exit condition

G1-W1 is complete when:

- the major contract objects have named roles
- each object's owned vs excluded fields are explicit
- shared reference types are named
- later workstreams can build on the object set without redefining boundaries

At that point, the next ready workstream is:

> **G1-W2 - Event families, statuses, and error semantics**
