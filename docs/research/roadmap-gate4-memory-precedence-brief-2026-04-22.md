# Roadmap Gate 4 Spike Brief - Memory Lifecycle, Provenance, and Precedence

**Date:** 2026-04-22  
**Program:** AGENT-33 research program  
**Artifact type:** Detailed spike brief - not implementation authorization

---

## Purpose

Define the memory policy rules that decide what AGENT-33 remembers, what it retrieves, what outranks what, and how evidence lineage stays reviewable and correctable.

This spike exists to answer:

> **What memory discipline prevents retrieval from becoming a hidden source of hallucination, drift, or contaminated authority?**

---

## Why this spike is in the first backbone set

Gate 4 is the trust backbone for:

- Phase D evidence memory, lineage, and ingestion
- Phase F skill promotion and improvement sandbox

It also constrains Gate 3 telemetry because routing, skill activation, and evaluation signals are only useful if the memory substrate has stable precedence and provenance rules.

---

## Inputs and prior signals

Primary grounding inputs:

- `docs/research/loop5b-ecosystem-architecture-panels-2026-04-21.md`
- `docs/research/loop5c-anti-hallucination-and-context-limit-panels-2026-04-21.md`
- `docs/research/world-model-platform-feasibility-panels-2026-04-21.md`
- `docs/research/paper-lewm-panel-update-strategy-2026-04-21.md`
- `docs/functionality-and-workflows.md`
- `docs/research/gated-phased-roadmap-draft-2026-04-22.md`

Strong inherited signals:

- memory should support evidence and recovery, not act as ambient authority
- retrieval must explain why something was selected
- frozen snapshots and operator directives need stronger priority than fuzzy recall
- learning and promotion need lineage-backed validity, not opaque memory accumulation

---

## Core design questions

This spike must resolve:

1. What memory classes exist in AGENT-33?
2. What outranks what during retrieval or context assembly?
3. How are provenance and claim-to-evidence lineage represented?
4. How do correction, forgetting, redaction, and pruning work?
5. What memory should be reusable across cadres, and what must stay siloed?
6. How do memory rules stay compatible with routing, evaluation, and improvement promotion?

---

## Proposed memory classes

This brief recommends the following policy-level memory classes:

1. **Operator directives**
   - explicit human instructions, overrides, denials, approvals

2. **Policy and governance references**
   - default policy packs, trust rules, budget limits

3. **Frozen execution snapshots**
   - checkpoints, handoff bundles, replay-linked state cards

4. **Working memory**
   - bounded run-local context for the active segment

5. **Evidence memory**
   - citations, evidence bundles, research dossiers, validated outputs

6. **Semantic long-term memory**
   - generalized facts, summaries, extracted concepts

7. **Procedural / skill memory**
   - stable patterns for repeated work, manifests, workflows, checklists

8. **Negative-example and correction memory**
   - prior failures, rejected claims, rollbacks, known bad routes

9. **Evaluation and routing observations**
   - telemetry-derived observations used for tuning and review

---

## Proposed precedence policy

This spike should prove a clear precedence table. Recommended default order:

1. **Operator directives**
2. **Policy / governance references**
3. **Frozen snapshots and checkpoint-linked facts**
4. **Evidence memory with citations**
5. **Negative-example and correction memory**
6. **Procedural / skill memory**
7. **Semantic long-term memory**
8. **Evaluation / routing observations**
9. **Unvalidated working hypotheses**

Two important rules:

- higher-ranked sources should not be silently overridden by lower-ranked recall
- semantic memory should never outrank checkpoint-linked or citation-backed facts for the active run

---

## Provenance and lineage requirements

Every retrieved memory that influences output, routing, or promotion should be able to answer:

- where it came from
- when it was created
- what run, segment, or artifact produced it
- whether it was validated, corrected, rolled back, or superseded
- what claim or decision it supports

Minimum lineage objects to connect:

- `MemoryEntry`
- `Artifact`
- `Run`
- `Segment`
- `PolicyEvent`
- `Intervention`
- `PromotionProposal`
- `RollbackRecord`

---

## Retrieval introspection requirement

Gate 4 should require a **why retrieved** explanation model.

At minimum, every retrieval surface should be able to report:

- selected memory ids
- class and rank
- retrieval reason
- matching factors or policy basis
- suppression reason for excluded higher-risk alternatives

This is essential for trust, debugging, and future evaluation.

---

## Correction, forget, and redaction semantics

The spike should define separate semantics for:

1. **Correct**
   - update or supersede an incorrect memory while preserving lineage

2. **Forget**
   - remove or disable a memory from future retrieval use

3. **Redact**
   - preserve auditability while hiding sensitive content from routine surfaces

4. **Prune**
   - remove low-value or stale memory according to lifecycle policy

These must not be treated as the same action.

---

## Cross-cadre sharing rule

Not all memory should be globally shared.

Recommended default:

- policy refs and approved procedural memory may be shared broadly
- active working memory remains segment-local
- environment evidence stays bounded to specialist contexts unless promoted
- negative examples may be shared only after validation that they describe a generalizable failure mode

---

## Required outputs

This spike should produce:

1. memory class taxonomy
2. precedence matrix
3. provenance and lineage model
4. lifecycle policy for retain / decay / consolidate / prune
5. retrieval introspection model
6. correction / forget / redaction semantics
7. at least one worked example for:
   - retrieval with precedence explanation
   - correction flow
   - rollback-aware memory supersession

---

## Validators

Gate 4 is only satisfied when:

1. retrieval decisions can be explained in terms of precedence and provenance
2. semantic memory does not override snapshot-linked or citation-backed active facts
3. a correction or forget workflow can be demonstrated without lineage loss
4. routing and evaluation ingestion remain compatible with memory policy instead of bypassing it
5. at least one cross-cadre sharing case and one non-sharing case are both justified clearly

---

## Non-goals

This spike must **not**:

- choose one database or index strategy as policy truth
- define all telemetry metrics
- imply that more memory is always better
- allow global reuse of every artifact by default
- collapse provenance into a single free-text note

---

## Rollback and containment boundaries

Reject proposals that:

- let storage convenience define precedence truth
- blur checkpoint-linked facts with generalized semantic memory
- allow silent mutation of previously validated memory
- treat operator correction as just another low-rank observation

---

## Lock recommendation threshold

Recommend roadmap lock for Gate 4 only if the spike can show:

- a stable memory taxonomy
- a defensible precedence order
- explicit provenance and lineage links
- retrieval introspection
- workable correction and forgetting semantics

Otherwise, the roadmap remains unlocked for Phase D and any promotion or learning claims in Phase F should stay heavily provisional.
