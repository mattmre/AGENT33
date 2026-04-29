# Roadmap Gate 3 Spike Brief - Context-Budget, Routing, and Skill-Activation Telemetry

**Date:** 2026-04-22  
**Program:** AGENT-33 research program  
**Artifact type:** Detailed spike brief - not implementation authorization

---

## Purpose

Define the telemetry model that shows whether compact state, specialist routing, and skill activation are actually improving outcomes rather than merely adding complexity, prompt weight, or operator burden.

This spike exists to answer:

> **What observability surfaces are required to tell whether AGENT-33's narrowing and routing strategy is helping, stalling, or quietly failing?**

---

## Why this spike follows the backbone set

Gate 3 depends on earlier clarity from:

- Gate 1 contract objects and event families
- Gate 2 checkpoint and replay boundaries
- Gate 4 memory precedence and lineage rules

It supports:

- Phase D evidence memory, lineage, and ingestion
- later tuning of Phase B evidence/judgment surfaces
- later tuning of Phase F skill promotion and improvement decisions

---

## Inputs and prior signals

Primary grounding inputs:

- `docs/research/loop5c-anti-hallucination-and-context-limit-panels-2026-04-21.md`
- `docs/research/loop5b-ecosystem-architecture-panels-2026-04-21.md`
- `docs/research/paper-lewm-panel-update-strategy-2026-04-21.md`
- `docs/research/effort-telemetry-exporter-decision.md`
- `docs/functionality-and-workflows.md`
- `docs/research/gated-phased-roadmap-draft-2026-04-22.md`

Strong inherited signals:

- anti-hallucination should be driven by shrinking ambiguity, not just adding reviewers
- telemetry should survive restarts and support later analysis / replay
- deterministic checks gate; model-scored signals advise
- routing must be explainable by job type, risk, and repetition rather than opaque model choice

---

## Core design questions

This spike must resolve:

1. How is context pressure measured before and during a run?
2. What shows that a skill reduced ambiguity rather than adding prompt bloat?
3. What proves that routing improved time-to-success, evidence coverage, or operator burden?
4. How does the system explain why a route or skill was chosen?
5. Which telemetry belongs in runtime traces versus durable analysis exports?
6. What telemetry remains advisory and must never become an automatic truth oracle?

---

## Proposed telemetry model

This brief recommends a **two-layer telemetry posture**:

1. **Runtime observability events**
   - emitted in-process for live dashboards, traces, and alerts

2. **Durable analysis export**
   - append-only, replay-friendly export for after-action review and improvement decisions

The exporter decision already established three important rules:

- opt-in activation
- fail-open default
- durability for later analysis

Gate 3 should inherit those rules instead of inventing a second telemetry posture.

---

## Telemetry dimensions to capture

### 1. Context-budget telemetry

Measure:

- planned context budget
- actual prompt / context pressure
- compaction or summarization invoked
- context overrun attempts
- context pressure at checkpoint boundaries

### 2. Routing telemetry

Measure:

- selected cadre and model route
- route reason basis: job type, risk, repetition, escalation, policy
- route changes and escalations
- fallback to stronger model or operator review

### 3. Skill-activation telemetry

Measure:

- candidate skills considered
- selected skills
- skill activation reason
- activation size / instruction footprint
- whether activated skill changed output quality, retries, or ambiguity

### 4. Outcome and burden telemetry

Measure:

- time-to-first-success
- retry storms
- blocked-run frequency
- operator escalations
- docs-to-success path
- evidence coverage and insufficient-evidence outcomes

### 5. Stability and anomaly telemetry

Measure:

- stall behavior
- repeated loop behavior
- route churn
- unsupported-claim signals
- handoff drift or checkpoint failure patterns

---

## Proposed explanation model

Gate 3 should require explicit **why routed** and **why activated** records.

Minimum explanation fields:

- `run_id`
- `segment_id`
- `decision_type`
- `selected_target`
- `candidate_targets`
- `decision_basis`
- `policy_refs`
- `budget_refs`
- `evidence_refs`
- `lineage_refs`
- `fallback_path`
- `operator_visible_summary`

This explanation model should be consumable by:

- dashboards
- replay views
- exported telemetry analysis

---

## Metric families that matter

This spike should explicitly prioritize metrics that change roadmap decisions:

1. **Time-to-first-success**
2. **Retry storm rate**
3. **Discovery / activation failure**
4. **Operator escalation rate**
5. **Evidence coverage**
6. **Insufficient-evidence rate**
7. **Route stability**
8. **Context-pressure frequency**

Metrics without a clear operator or roadmap decision use should not be promoted.

---

## Required outputs

This spike should produce:

1. telemetry event taxonomy for context, routing, skill activation, and anomaly signals
2. metric definitions and formulas
3. explanation-record schema for route and skill decisions
4. durable export rules aligned with the exporter decision
5. at least one reporting view or report format for analysis
6. one worked example for:
   - beneficial skill activation
   - defensible null-result skill activation
   - route escalation under ambiguity

---

## Validators

Gate 3 is only satisfied when:

1. telemetry is visible on representative runs
2. durable export survives restart and remains replay-usable
3. at least one routing or skill scenario shows measurable benefit or a defensible null result
4. the system can explain why a route or skill was selected
5. the telemetry model does not depend on hidden memory precedence assumptions that Gate 4 would reject

---

## Non-goals

This spike must **not**:

- turn telemetry into a hard truth gate by itself
- collect vanity metrics with no decision value
- replace deterministic contract checks with score dashboards
- require all telemetry to be online or real-time to be useful
- create a second disconnected observability system

---

## Rollback and containment boundaries

Reject proposals that:

- silently promote advisory anomaly scores into auto-blocking truth signals
- make routing explanations unreadable to operators
- couple telemetry validity to one storage or dashboard choice
- treat prompt size alone as equivalent to context quality

---

## Lock recommendation threshold

Recommend roadmap lock for Gate 3 only if the spike can show:

- durable and replay-usable telemetry
- route and skill explanation records
- metrics tied to real operator and roadmap decisions
- evidence that at least some narrowing/routing choices are materially useful

Otherwise, the roadmap remains unlocked for telemetry-dependent tuning and Phase F promotion logic should not rely on unsupported score signals.
