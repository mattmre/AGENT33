# Roadmap Gate 6 Spike Brief - Skill Promotion, Rollback, and Improvement Containment

**Date:** 2026-04-22  
**Program:** AGENT-33 research program  
**Artifact type:** Detailed spike brief - not implementation authorization

---

## Purpose

Define the promotion and containment rules that let AGENT-33 evolve skills, packs, and improvement proposals without allowing silent self-mutation, lineage loss, or ecosystem drift.

This spike exists to answer:

> **What promotion path is strict enough to support improvement while preventing the system from silently rewriting itself past operator trust?**

---

## Why this spike is last in the set

Gate 6 depends on evidence from earlier gates:

- Gate 1 stable contracts
- Gate 2 replayable checkpoints and handoffs
- Gate 3 telemetry and evaluation signals
- Gate 4 memory provenance and correction rules

It is the policy backbone for:

- Phase F skill promotion and improvement sandbox

---

## Inputs and prior signals

Primary grounding inputs:

- `docs/research/loop5b-ecosystem-architecture-panels-2026-04-21.md`
- `docs/research/world-model-platform-feasibility-panels-2026-04-21.md`
- `docs/research/paper-lewm-panel-update-strategy-2026-04-21.md`
- `docs/self-improvement/intake-protocol.md`
- `docs/research/evolver-clean-room-guardrails.md`
- `docs/functionality-and-workflows.md`
- `docs/research/gated-phased-roadmap-draft-2026-04-22.md`

Strong inherited signals:

- improvement should be proposal-driven, not direct self-mutation
- journals and lineage are evidence, not substitutes for lifecycle state
- external or community assets should enter with reduced trust and non-executable status
- detect-only or dry-run posture is safer than silent repair or auto-heal posture

---

## Core design questions

This spike must resolve:

1. Which changes remain proposal-only and never auto-apply?
2. What evidence qualifies a skill, pack, prompt, harness, or routing change for promotion?
3. How is rollback ancestry represented?
4. What validation path applies equally to internal and third-party assets?
5. What containment rules stop ecosystem growth from bypassing operator trust?
6. How do intake, review, promotion, revocation, and rollback fit into one lifecycle?

---

## Proposed improvement lifecycle

This brief recommends a single improvement lifecycle with explicit non-executable entry states.

Suggested lifecycle:

1. `candidate`
2. `validated`
3. `review_required`
4. `promoted`
5. `published`
6. `revoked`
7. `rolled_back`

Important posture:

- incoming assets and proposals begin low-trust and non-executable
- validation and promotion are distinct steps
- rollback is a first-class state, not a patch-note footnote

---

## Proposed asset classes

Gate 6 should at minimum cover:

- skill manifests
- skill packs / markdown guidance
- prompt or template deltas
- harness configuration deltas
- routing policy deltas
- plugin or external asset candidates

These should share one containment philosophy even if they do not all share one storage model.

---

## Promotion scorecard requirement

Gate 6 should require a formal scorecard for promotion decisions.

Minimum scorecard dimensions:

1. contract compatibility
2. replayability and rollback readiness
3. evidence coverage
4. operator burden change
5. policy hygiene
6. regression / evaluation impact
7. provenance quality
8. blast radius

The scorecard should support both:

- promotion approval
- promotion denial or deferral

---

## Evaluation harness requirement

Promotion must not rely on narrative confidence alone.

Gate 6 should define an evaluation harness that can consume:

- exemplar tasks
- regression scenarios
- policy-sensitive scenarios
- rollback validation scenarios
- evidence sufficiency checks

Promotion without a reusable evaluation harness should be considered incomplete.

---

## Rollback ancestry requirement

Every promoted improvement should answer:

- what artifact or version it came from
- what it replaced
- what evaluations supported it
- what rollback target is valid
- what later artifacts depend on it
- what lineage refs and scorecard refs justify the promotion

Rollback ancestry must be durable enough to support:

- targeted rollback
- chain rollback
- post-incident review

---

## Containment rules

This spike should formalize at least the following containment rules:

1. **No direct self-mutation**
   - the system may propose but not silently apply high-impact changes

2. **Low-trust candidate posture**
   - external or new assets begin non-executable and low confidence

3. **Common validation discipline**
   - internal and third-party assets face the same compatibility and rollback rules

4. **Dry-run first for remediation**
   - "detect-only" posture before any mutating action

5. **Optional remote participation**
   - improvement and ecosystem sync remain local-first and opt-in

---

## Required outputs

This spike should produce:

1. improvement lifecycle definition
2. promotion scorecard
3. evaluation harness requirements
4. rollback ancestry model
5. promotion record schema with lineage refs, scorecard refs, and rollback target refs
6. containment and validation policy for skills, packs, prompts, routing deltas, and plugin-like assets
7. release / deprecation / revocation guidance
8. one worked example for:
   - promotion approval
   - promotion rejection
   - rollback after bad promotion

---

## Validators

Gate 6 is only satisfied when:

1. a proposed change can be scored, validated, promoted, and rolled back through the defined model
2. promotion remains blocked when evidence is insufficient
3. internal and third-party assets share the same compatibility discipline
4. rollback ancestry is explicit enough for post-incident review
5. no contained flow permits silent high-impact mutation

---

## Non-goals

This spike must **not**:

- authorize autonomous self-learning deployment
- replace evaluation with one scalar reward number
- treat proposal journals as equivalent to approved lifecycle state
- bypass legal or provenance review for external assets
- allow auto-heal behavior to sneak in under a softer name

---

## Rollback and containment boundaries

Reject proposals that:

- promote assets without reusable evaluation evidence
- make rollback ancestry optional
- treat "internal" changes as exempt from validation discipline
- allow silent repair or silent dependency mutation

---

## Lock recommendation threshold

Recommend roadmap lock for Gate 6 only if the spike can show:

- a strict proposal-to-promotion lifecycle
- scorecard and evaluation harness requirements
- rollback ancestry and revocation semantics
- explicit containment against silent self-mutation

Otherwise, Phase F remains conditional and any self-improvement language should stay sandboxed and proposal-only.
