# Roadmap Gate 5 Spike Brief - Browser/Computer-Use Evidence and Watchdog Signals

**Date:** 2026-04-22  
**Program:** AGENT-33 research program  
**Artifact type:** Detailed spike brief - not implementation authorization

---

## Purpose

Define the canonical evidence and watchdog model for browser/computer-use work so environment specialists remain bounded, auditable, replayable, and safe to review.

This spike exists to answer:

> **What evidence bundle and watchdog semantics are strong enough to make environment actions reviewable without overgeneralizing them into all tool work?**

---

## Why this spike is later than the backbone set

Gate 5 depends on:

- Gate 1 event and handoff contracts
- Gate 2 checkpoint and replay semantics
- Gate 4 memory and provenance discipline

It is the safety backbone for:

- Phase E environment specialist cadres

The browser and computer-use surface is high-value, but it is also the most audit-sensitive and replay-sensitive capability family in the roadmap.

---

## Inputs and prior signals

Primary grounding inputs:

- `docs/research/loop5b-ecosystem-architecture-panels-2026-04-21.md`
- `docs/research/loop5c-anti-hallucination-and-context-limit-panels-2026-04-21.md`
- `docs/research/session109-phase55-browser-scope.md`
- `docs/research/session109-phase52-redaction-scope.md`
- `docs/research/gated-phased-roadmap-draft-2026-04-22.md`
- `docs/functionality-and-workflows.md`

Strong inherited signals:

- environment specialists should stay siloed and not become universal powers
- browser output currently has explicit redaction dependency and lifecycle caveats
- replay and evidence matter more here than clever autonomy
- watchdogs must support operator understanding, not just runtime suppression

---

## Core design questions

This spike must resolve:

1. What counts as canonical evidence for a browser/computer-use segment?
2. What watchdog signals matter and how should they be labeled?
3. What must be preserved for replay and operator review?
4. How do intervention and triage work when environment risk rises?
5. How is sensitive evidence redacted without destroying audit value?
6. Which environment facts may cross into general memory or other cadres, and which stay bounded?

---

## Proposed canonical evidence bundle

This brief recommends a dedicated **EnvironmentEvidenceBundle**, not a reuse of generic tool output.

Minimum contents:

- `environment_session_ref`
- `run_id`
- `segment_id`
- `action_log`
- `page_or_surface_refs`
- `screenshot_refs`
- `dom_or_text_extract_refs`
- `vision_analysis_refs` when used
- `watchdog_signal_refs`
- `intervention_refs`
- `redaction_refs`
- `checkpoint_ref`
- `operator_summary`

Evidence should favor references to durable artifacts rather than embedding all content directly inside one object.

---

## Proposed watchdog taxonomy

Gate 5 should define operator-meaningful watchdog classes, for example:

1. **Navigation risk**
   - unexpected redirect
   - cross-domain movement
   - login or payment surface reached

2. **Action risk**
   - destructive click or submit
   - repeated retry or loop behavior
   - high-impact input submission

3. **Evidence risk**
   - insufficient screenshot coverage
   - incomplete DOM/text capture
   - redaction made evidence non-reviewable

4. **Policy / permission risk**
   - action outside allowed overlay
   - tenant or session boundary issue
   - unsafe escalation attempt

Watchdogs should emit labels that are understandable in UI and logs, not only numeric thresholds.

---

## Replay and intervention model

Gate 5 should require:

1. **Replay attachment model**
   - screenshot timeline or equivalent evidence references
   - action-by-action reconstruction support
   - checkpoint-linked replay entry points

2. **Intervention states**
   - `watching`
   - `needs_review`
   - `approval_required`
   - `blocked`
   - `resumable`

3. **Triage guidance**
   - what the operator needs to review
   - what evidence is missing
   - what next action is permitted

Environment replay must support review of both action sequence and evidence sufficiency.

---

## Redaction and sensitive-evidence rule

The redaction slice already established strong log/tool-output redaction posture. Gate 5 should extend that posture carefully:

- redaction must preserve auditability through references and masks
- redaction cannot silently remove the existence of sensitive evidence
- browser vision output and extracted text should be redaction-aware before being promoted as review evidence

Gate 5 should therefore define **redaction-aware evidence bundles**, not merely "redacted strings."

---

## Cross-cadre boundary rule

Recommended default:

- environment evidence stays within the environment specialist boundary unless explicitly promoted
- derived non-sensitive conclusions may be handed off to other cadres through normal result and handoff contracts
- raw environment artifacts should not become ambient shared context

---

## Required outputs

This spike should produce:

1. canonical environment evidence bundle definition
2. watchdog taxonomy with labels and threshold guidance
3. replay attachment model
4. intervention state vocabulary and triage guidance
5. redaction-aware evidence handling rules
6. one worked example for:
   - normal environment replay
   - watchdog-triggered intervention
   - redacted-but-auditable evidence review

---

## Validators

Gate 5 is only satisfied when:

1. at least one environment workflow is replay-auditable through the canonical bundle
2. watchdog-triggered intervention states are understandable to operators
3. redaction preserves enough evidence for review
4. raw environment artifacts do not leak into general memory or unrelated cadres by default
5. the evidence bundle can coexist with both local and cloud-backed browser sessions

---

## Non-goals

This spike must **not**:

- generalize browser/computer-use evidence rules into all tool work
- finalize cloud backend selection
- assume browser autonomy is safe just because screenshots exist
- collapse sensitive evidence handling into blind deletion
- make environment specialists sovereign over policy or replay rules

---

## Rollback and containment boundaries

Reject proposals that:

- rely on prose summaries instead of evidence references for risky actions
- emit watchdog scores with no operator-readable meaning
- treat redaction as a reason to skip auditability
- turn environment evidence into always-shared memory by default

---

## Lock recommendation threshold

Recommend roadmap lock for Gate 5 only if the spike can show:

- a stable environment evidence bundle
- watchdog labels operators can understand
- replay and intervention tied to checkpoints and evidence refs
- redaction-aware auditability

Otherwise, Phase E remains conditional and browser/computer-use should stay bounded, partial, and explicitly non-authoritative.
