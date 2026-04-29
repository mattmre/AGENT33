# Roadmap Gate 2 Spike Brief - Compact Task-State, Frozen Handoffs, and Checkpoint Unit

**Date:** 2026-04-22  
**Program:** AGENT-33 research program  
**Artifact type:** Detailed spike brief - not implementation authorization

---

## Purpose

Define the minimal durable state unit for specialist execution so replay, resume, inspection, repair, and handoff work from compact typed artifacts rather than sprawling ambient context.

This spike exists to answer:

> **What is the smallest frozen unit of state that preserves truth, supports recovery, and does not collapse back into a context dump?**

---

## Why this spike follows Gate 1

Gate 2 depends on Gate 1 contract objects, especially:

- invocation envelopes
- progress / interrupt events
- result envelopes
- handoff bundles
- structured errors

It is the execution backbone for:

- Phase B evidence and judgment surfaces
- Phase C bounded execution, frozen handoffs, and replay

---

## Inputs and prior signals

Primary grounding inputs:

- `docs/research/loop5c-anti-hallucination-and-context-limit-panels-2026-04-21.md`
- `docs/research/paper-lewm-panel-update-strategy-2026-04-21.md`
- `docs/research/loop5b-ecosystem-architecture-panels-2026-04-21.md`
- `docs/functionality-and-workflows.md`
- `docs/research/gated-phased-roadmap-draft-2026-04-22.md`

Strong inherited signals:

- long multi-purpose loops accumulate ambiguity faster than truth
- segmentation should be the default for long, risky, or multi-stage work
- frozen handoffs should prefer artifact bundles over narrative continuity
- compact state should act like a run-state card, not a compressed transcript dump

---

## Core design questions

This spike must resolve:

1. What exactly is a checkpoint unit?
2. What exactly is a frozen handoff bundle?
3. What survives pause, resume, replay, and operator repair?
4. What can be recomputed instead of persisted?
5. How are blocked states, approvals, and rollback points represented?
6. How compact is compact enough before fidelity is lost?

---

## Proposed checkpoint model

This brief recommends separating **checkpoint unit** from **handoff bundle**.

### Checkpoint unit

The checkpoint unit should be the smallest durable recovery record for one bounded segment.

Minimum fields:

- `checkpoint_id`
- `run_id`
- `segment_id`
- `agent_class`
- `objective`
- `constraints_ref`
- `policy_refs`
- `allowed_tools_ref`
- `input_artifact_refs`
- `latest_validated_outputs`
- `open_approvals`
- `blocked_reasons`
- `budget_snapshot`
- `lineage_refs`
- `resume_strategy`
- `created_at`

### Frozen handoff bundle

The handoff bundle should be the transportable package another specialist can consume without inheriting the whole prior run.

Minimum contents:

- handoff metadata
- relevant checkpoint ref
- required artifact refs
- required contract refs
- unresolved questions
- required validations not yet satisfied
- expected output schema
- evidence coverage snapshot

### Replay span

Replay should not mean replaying the whole run every time. It should support:

- segment replay
- checkpoint-to-checkpoint replay
- exception replay around failure or approval points

---

## Persistence rule

The spike should define three buckets:

1. **Must persist**
   - checkpoint identity
   - artifact refs
   - unresolved blockers
   - approvals and operator decisions
   - latest validated outputs

2. **May recompute**
   - derived summaries
   - presentation-layer views
   - convenience rollups

3. **Must not persist as frozen truth**
   - speculative chain-of-thought style reasoning
   - noisy intermediate guesses
   - broad conversational context with unclear status

---

## Recovery semantics to prove

Gate 2 should define explicit flows for:

1. **Inspect**
   - operator or system asks why a segment is blocked or failed

2. **Replay**
   - reconstruct evidence and decision path from checkpoint and artifact refs

3. **Repair**
   - replace or patch a bad input artifact, validator, or routing choice without rewriting history

4. **Resume**
   - continue from a valid checkpoint without reloading the whole session context

5. **Rollback**
   - return to a prior stable checkpoint or handoff boundary

---

## Proposed compactness rules

To avoid durable wrongness, the frozen unit should obey:

1. **One segment, one main decision surface**
2. **Artifacts over narrative**
3. **Validated outputs over raw generated text**
4. **Open questions explicitly named, not implied**
5. **References over copied blobs whenever possible**

If a checkpoint or handoff bundle cannot be reviewed by a human or validator in bounded time, it is likely too large.

---

## Required outputs

This spike should produce:

1. checkpoint unit definition
2. frozen handoff bundle definition
3. replay / inspect / repair / resume / rollback semantics
4. partial-failure handling rules
5. blocked-state vocabulary
6. one worked example for:
   - normal replay
   - blocked run repair
   - cross-cadre handoff

---

## Validators

Gate 2 is only satisfied when:

1. replay succeeds from frozen artifacts without prose-only continuity
2. a blocked run can be inspected, repaired, and resumed through the defined model
3. the handoff bundle stays compact under realistic specialist workflows
4. checkpoint boundaries align with operator-visible evidence and judgment surfaces
5. rollback lands on a stable unit that still has lineage and evidence integrity

---

## Non-goals

This spike must **not**:

- define the full telemetry layer
- define all long-term memory classes
- choose a final storage engine
- preserve every intermediate model thought
- turn the checkpoint into a catch-all debugging blob

---

## Rollback and containment boundaries

Reject proposals that:

- silently widen compact state into transcript persistence
- confuse a UI replay card with the runtime checkpoint unit
- make checkpoint format dependent on one cadre's convenience
- treat summaries as a substitute for artifact references

---

## Lock recommendation threshold

Recommend roadmap lock for Gate 2 only if the spike can show:

- a stable checkpoint unit
- a transportable frozen handoff bundle
- bounded recovery semantics
- operator-legible replay
- compactness without truth loss

Otherwise, Phase C remains conditional and Environment / Improvement work should not assume reliable replay exists.
