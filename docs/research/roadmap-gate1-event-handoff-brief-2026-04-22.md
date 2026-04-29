# Roadmap Gate 1 Spike Brief - Event, Report-Back, and Handoff Schema

**Date:** 2026-04-22  
**Program:** AGENT-33 research program  
**Artifact type:** Detailed spike brief - not implementation authorization

---

## Purpose

Define the first lock-grade contract family for AGENT-33 so specialist cadres can be invoked, observed, interrupted, completed, and handed off through stable, versioned envelopes.

This spike exists to answer:

> **What is the minimum common schema family that all cadres must speak before the roadmap can be locked?**

---

## Why this spike is first

Gate 1 is the contract backbone for:

- Phase A1 contract narrowing and shared harness
- Phase A2 governance and exception review
- Phase C bounded execution and replay

Without this spike:

- Phase B risks designing UI around unstable semantics
- Gate 2 cannot define a frozen handoff bundle cleanly
- Gate 4 cannot attach provenance and lineage to stable objects

---

## Inputs and prior signals

Primary grounding inputs:

- `docs/research/loop5b-ecosystem-architecture-panels-2026-04-21.md`
- `docs/research/loop5c-anti-hallucination-and-context-limit-panels-2026-04-21.md`
- `docs/research/session126-p69b-api-contract.md`
- `docs/research/council-final-audit-2026-04-22.md`
- `docs/research/gated-phased-roadmap-draft-2026-04-22.md`

Strong inherited signals:

- every cadre should speak a common contract family even when payloads differ
- truthfulness requires evidence contracts, not only tool-permission contracts
- handoffs should prefer typed artifact bundles over prose-only continuity
- approvals and interrupts should integrate with, not replace, the execution contract family

---

## Core design questions

This spike must resolve:

1. What fields are required in every invocation envelope?
2. What is the minimum normalized event stream for progress, pause, approval-required, completion, and failure?
3. What does a result envelope contain beyond free-form summary text?
4. What makes a handoff bundle stable enough for replay and cross-cadre use?
5. How do domain events, integration events, and audit/replay events differ?
6. How are structured errors and retry / idempotency semantics represented?

---

## Proposed contract family

This brief recommends a **single contract family with distinct object types**, not a single blob schema.

### 1. Invocation envelope

Every cadre invocation should carry:

- `schema_version`
- `agent_class`
- `run_id`
- `task_id`
- `segment_id`
- `objective`
- `constraints`
- `policy_refs`
- `budget_refs`
- `allowed_tools`
- `input_artifact_refs`
- `expected_output_schema`
- `confidence_target`
- `caller_ref`

### 2. Progress and interrupt events

Every running segment should emit normalized events with:

- `schema_version`
- `event_id`
- `event_type`
- `run_id`
- `segment_id`
- `agent_class`
- `state_ref`
- `status`
- `operator_action_required`
- `evidence_refs`
- `budget_delta`
- `timestamp`

Minimum event-type family:

- `started`
- `step`
- `checkpoint_created`
- `paused`
- `approval_required`
- `resumed`
- `completed`
- `failed`
- `cancelled`

### 3. Result envelope

Every completion should emit:

- `summary`
- `structured_payload`
- `confidence`
- `citations`
- `lineage_refs`
- `contract_check_refs`
- `follow_on_recommendations`
- `promotion_or_review_required`
- `insufficient_evidence_flag`

### 4. Handoff bundle

Every specialist-to-specialist handoff should include:

- `handoff_id`
- `from_agent_class`
- `to_agent_class`
- `objective_transfer`
- `input_artifact_refs`
- `checkpoint_ref`
- `required_contract_refs`
- `open_questions`
- `blocked_reasons`
- `expected_output_schema`
- `handoff_reason`

### 5. Error envelope

Errors should not be free-text only. Every failure or denial surface should support:

- `error_code`
- `error_class`
- `retryable`
- `idempotent_reentry_supported`
- `operator_review_required`
- `evidence_refs`
- `caused_by_ref`

---

## Event partition rule

Gate 1 should explicitly separate three event families:

1. **Domain events**
   - execution and cadre-state facts
   - examples: `checkpoint_created`, `result_emitted`

2. **Integration events**
   - system-to-system coordination facts
   - examples: `approval_required`, `handoff_ready`, `route_selected`

3. **Audit / replay events**
   - traceability and replay scaffolding
   - examples: `contract_validated`, `artifact_attached`, `operator_decision_recorded`

The schema pack may share common fields, but these families should not be flattened into one undifferentiated log type.

---

## Cadre mapping requirement

The first lock-grade schema pack must prove compatibility across at least:

1. **Research & Ingestion Cadre**
2. **Execution & Orchestration Cadre**
3. **Synthesis & Judgment Cadre**

The approval flow from the P69b contract should be mapped as an exception-handling example, not treated as the whole runtime model.

---

## Required outputs

This spike should produce:

1. a versioned schema pack for:
   - invocation envelope
   - progress / interrupt events
   - result envelope
   - handoff bundle
   - error envelope
2. a schema registry page with examples
3. a state-transition table for normalized statuses
4. an error taxonomy with retry / idempotency semantics
5. change-policy rules for additive vs breaking revisions
6. three exemplar cross-cadre flows

---

## Validators

Gate 1 is only satisfied when:

1. schema validators pass against exemplar runs
2. the three-cadre flow works without bespoke envelope forks
3. UI, CLI, and automation surfaces can consume the same contract objects
4. approval-required and resume semantics attach cleanly to the normalized event family
5. a result can be marked **insufficient evidence** without being mistaken for transport failure

---

## Non-goals

This spike must **not**:

- freeze transport or storage implementation choices
- choose one event bus or persistence adapter
- define the full memory model
- define the checkpoint payload in full detail
- collapse all outputs into a single universal JSON blob

---

## Rollback and containment boundaries

If this spike starts drifting, stop and reject proposals that:

- make the contracts UI-first instead of runtime-first
- overfit one cadre's payload shape into all others
- force prose summaries to carry facts that should be artifact refs
- mix policy verdicts and execution state into one ambiguous status field

---

## Lock recommendation threshold

Recommend roadmap lock for Gate 1 only if the spike can show:

- stable object boundaries
- additive versioning discipline
- evidence-capable result envelopes
- exception-handling compatibility
- proven cross-cadre reuse

Otherwise, the roadmap remains unlocked and Gate 2 work should stay provisional.
