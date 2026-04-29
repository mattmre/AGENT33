# EvoMap Evolver vs AGENT33 — Adaptive Ingestion Comparison

Date: 2026-04-20

## Executive Summary

AGENT33 should **ingest Evolver as a design reference, not as a code donor**.
The strongest reusable ideas are **operational boundary patterns**, not a new
core architecture:

1. **local proxy/mailbox isolation** between remote coordination and the core runtime
2. **candidate intake with lowered confidence** for external/community assets
3. **append-only operational journals** for intake, decisions, and replayable evidence
4. **heartbeat/task metrics** around coordination flows
5. **offline-first operation** with optional remote participation
6. **explicit lifecycle verbs** for ingest/validate/report/promote/export flows

The biggest blocker is legal and must be treated as decisive: Evolver exposes
**conflicting license signals**. Repository metadata and `package.json` indicate
`GPL-3.0` / `GPL-3.0-or-later`, while `SKILL.md` ends with `MIT`. Until upstream
clarifies that inconsistency, AGENT33 should assume **GPL constraints apply** and
avoid direct code or prose ingestion.

The deeper code-introspection round tightened the recommendation further:
Evolver’s real strength is a **proxy-coordinated runtime shell plus append-only
artifact stores and operator utilities**. AGENT33 is already stronger in
**explicit lifecycle, provenance, trust, and curation governance**. That means
AGENT33 should borrow Evolver’s edge patterns, while rejecting its weaker or
riskier traits: report-driven architecture inflation, self-mutating repair
behavior, and committed obfuscated source.

## Evidence Baseline

### AGENT33 baseline

- MIT-licensed autonomous orchestration platform
- local-first runtime with explicit governance and durable planning discipline
- main surfaces: `engine/`, `frontend/`, `core/`, `docs/`
- 27 first-party skills across 8 pack families
- relevant internal skills:
  - `repo-ingestor`
  - `docs-architect`
  - `mcp-builder`

### Evolver baseline

- `EvoMap/evolver`
- JavaScript self-evolution engine centered on GEP/A2A/Proxy concepts
- approx. 6k stars / 570 forks / active 2026-04-21 push
- main surfaces: `src/`, `scripts/`, `test/`, `examples/`, `SKILL.md`
- representative implementation signals:
  - `src/proxy/index.js` — local proxy/mailbox boundary, sync/lifecycle/task handlers
  - `scripts/a2a_ingest.js` — verify asset IDs, lower external confidence, quarantine/stage
  - `src/ops/skills_monitor.js` — detect and auto-heal skill issues
  - `examples/hello-world.md` — offline-first quickstart and review loop

## Panel-of-Experts Results

### Panel 1 — Repo Ingestion

**Verdict:** **Adopt with modifications** — concepts only, not direct code ingestion.

**Key findings**

- Evolver is active enough to merit study, but AGENT33 should treat it as a
  **pattern source**, not an integration dependency.
- The most valuable pattern is **governed external-asset ingestion**:
  verify -> reduce confidence -> quarantine -> review -> promote.
- Evolver’s docs are usable, but operational truth is spread across README,
  example docs, env declarations, and `SKILL.md`.
- `skills_monitor.js` is operationally interesting, but its auto-heal posture is
  too aggressive for AGENT33’s governance model.
- The license inconsistency is the hard stop for direct ingestion.

**Adopt conceptually**

- proxy/mailbox isolation
- quarantine/staged promotion
- confidence downgrade for external assets
- explicit decision logs and human review
- offline-first, remote-optional posture

**Do not ingest directly**

- GPL code
- Evolver protocol prose
- auto-install / auto-stub behavior
- hub-specific semantics as AGENT33 runtime primitives

### Panel 2 — Architecture & Planning

**Consensus target state:** AGENT33 should become a
**policy-governed local orchestration platform with staged adaptation**, not a
self-modifying evolution engine.

**Recommended target-state layers**

1. **Governance & Evidence Plane**
   - asset verification
   - confidence scoring
   - quarantine/staging/promotion
   - append-only decision/event ledger
   - lineage and provenance tracking
2. **Runtime Control Plane**
   - thin local mailbox/proxy boundary
   - offline-first local authority
   - optional hub/catalog/sync participation
3. **Skill Operations Plane**
   - lifecycle-aware asset/skill workflows
   - detect-first monitoring
   - rollback suggestions and policy-gated repair
4. **Operator Surface**
   - review queue
   - health/drift visibility
   - provenance and promotion history

**Strongest architectural fit**

- thin mailbox/proxy edge
- quarantine/stage/promote asset pipeline
- append-only logs for approvals/imports/promotions/revocations
- A2A-style import/export/promote concepts mapped into AGENT33-native contracts

**Architectural non-goals**

- no replacement of AGENT33’s pack/skill/workflow model
- no append-only rewrite of all mutable state
- no autonomous self-mutation loop
- no mandatory network hub
- no second competing distribution ecosystem

### Panel 3 — Workflow / DX / Skills

**Consensus:** Evolver is stronger at **lifecycle clarity**, while AGENT33 is
stronger at **modularity, docs discipline, UI, and durable planning**.

**What AGENT33 should adapt**

- a clearer **local-first quickstart lane**
- first-class workflow verbs:
  - `ingest`
  - `validate`
  - `report`
  - `promote`
  - `export`
- explicit lifecycle states:
  - `candidate`
  - `validated`
  - `published`
  - `revoked`
- a bounded **skills doctor** posture:
  - dry-run detection
  - explicit repair proposals
  - auditable changes only
- a dedicated adaptation-oriented pack instead of scattering the logic
- role-based documentation navigation for operator / developer / integrator / contributor lanes

**What AGENT33 should preserve**

- multi-pack modular architecture
- first-party frontend/control plane
- durable research and planning artifacts
- human review and scoped-PR discipline

**What AGENT33 should avoid**

- collapsing into a monolithic “one super skill” model
- hidden auto-installs / hidden mutations
- overloading one `SKILL.md` with product, protocol, env, safety, and ops

### Panel 4 — Code Workflow / Security Delta

**Consensus:** the code-level round makes Evolver look like a
**proxy/runtime envelope with append-only stores, task monitoring, and
reporting utilities**, not a superior governed workflow core.

**Confirmed code-level patterns**

- `index.js` and `src/proxy/index.js` assemble a local runtime shell around
  mailbox, sync, lifecycle, task, session, DM, and HTTP proxy components
- `src/proxy/server/routes.js` exposes explicit coordination verbs for mailbox,
  task, session, asset, and DM flows
- `src/proxy/task/monitor.js` persists heartbeat and task metrics
- `scripts/a2a_ingest.js` stages external assets with reduced confidence and
  decision emission
- `src/gep/assetStore.js` uses append-only JSON / JSONL stores for candidates,
  events, failed assets, and related runtime artifacts
- `scripts/analyze_by_skill.js` and `scripts/human_report.js` are downstream
  reporting layers over accumulated history, not the workflow core

**What the code round changed**

- the **thin mailbox / proxy seam** is more concrete and valuable than the
  first report gave it credit for
- **append-only operational journaling** is worth adapting, but only as a
  subordinate evidence layer beneath AGENT33’s lineage / provenance model
- Evolver’s workflow shape is **more implicit and route/event-driven** than
  AGENT33’s existing curation and trust model, so AGENT33 should not replace
  its state-machine approach
- direct runtime adoption is even less attractive because two important GEP
  files appeared committed in **obfuscated form**

**New caution flags**

- do not mistake history-report scripts for proof of deeper modular workflow
  architecture
- do not import or trust self-healing behaviors that mutate dependencies or
  write stub docs without explicit review
- treat obfuscated committed source as incompatible with AGENT33’s normal
  reviewability and provenance expectations

## Comparative Assessment

| Area | AGENT33 today | Evolver | Recommended AGENT33 response |
|---|---|---|---|
| License posture | MIT, internally controlled | GPL signals with doc inconsistency | Treat Evolver as concept-only reference |
| Runtime shape | Python engine + Node frontend + packs | JS-centric evolution engine | Preserve AGENT33 shape |
| Governance | Strong, explicit, PR-scoped | More aggressive automation | Keep AGENT33 governance model |
| Offline posture | Strong local-first direction | Explicit offline-first story | Strengthen AGENT33 docs around this |
| Asset ingestion | Present, but less lifecycle-explicit | Explicit candidate staging, confidence demotion, decision emission | Add lifecycle states, confidence labels, and review queue |
| Skill operations | Pack-based, modular | Proxy shell + scripts + monitor + reporting utilities | Add narrow monitoring/journal workflows, not monolith |
| Docs quality | Broader and stronger overall | Faster onboarding but mixed concerns | Keep AGENT33 docs discipline; adopt clearer quickstart |
| UI/operator surface | First-party frontend | CLI-centered | Reinterpret Evolver ideas through AGENT33 UI |

## Clean-Room Adoption Boundary

### Safe to adopt as concepts

- proxy/mailbox boundary pattern
- external-asset confidence downgrade
- candidate / validated / published / revoked lifecycle
- append-only intake / decision / heartbeat journals subordinate to lineage
- offline-first/remote-optional operational contract
- explicit lifecycle command vocabulary
- task heartbeat / metrics visibility

### Unsafe to import directly

- source code
- docs/protocol text
- licensing assumptions from `SKILL.md`
- autonomous self-heal behavior in production
- obfuscated or unreadable committed source paths
- hub/A2A naming as core AGENT33 abstractions
- report-generated narratives treated as proof of runtime architecture

## Recommended AGENT33-Native Adaptations

### New/extended workflow surfaces

1. **Governed candidate intake**
   - import external/community asset
   - verify provenance and integrity
   - assign reduced-confidence and candidate state
   - require validation and publication before active use

2. **Operational evidence journal**
   - append-only records for intake, validation, publication, revocation, and
     task heartbeat events
   - lineage / provenance remain canonical semantic truth
   - replayable evidence for operator review and debugging

3. **Asset promotion workflow**
   - explicit operator approval
   - ledgered decision
   - reversible promotion / revocation

4. **Thin mailbox / heartbeat pilot**
   - narrow mailbox/session/task facade for coordination experiments
   - local runtime remains authoritative
   - heartbeat and task metrics surfaced to operators

5. **Skills doctor**
   - detect-only health report first
   - optional dry-run remediation plan
   - explicit operator-run repair, never silent mutation

6. **Local-first docs lane**
   - “works locally without remote services” quickstart
   - remote collaboration/hub features documented as optional

### Candidate pack or capability name

- `governed-adaptation`
- `asset-lifecycle-ops`
- `evolution-ops` (only if terminology stays AGENT33-native inside implementation)

## Improvement Sprint / Phase Plan

### Sprint 0 — Clean-Room Guardrails

**Goal:** lock legal and architectural boundaries before code.

**Scope**

- record Evolver adoption boundary
- document GPL constraint and direct-code prohibition
- define AGENT33-native terminology for imported concepts
- define lifecycle states and trust / confidence labels
- ban obfuscated committed review-source in trusted adaptation paths

**Acceptance criteria**

- a clean-room ADR or equivalent research note exists
- no planned task depends on copying Evolver code or prose
- lifecycle vocabulary is fixed for follow-on implementation

### Sprint 1 — Safe Ingestion State Model

**Goal:** formalize the asset lifecycle without runtime disruption.

**Scope**

- define asset states:
  - `candidate`
  - `validated`
  - `published`
  - `revoked`
- define trust / confidence labels layered onto those states
- define provenance, decision, and operational journal schema
- wire durable research/planning references for ingestion work

**Acceptance criteria**

- lifecycle states are documented and referenced in implementation planning
- provenance, decision, and journal schema are defined
- candidate assets are explicitly non-executable by policy

### Sprint 2 — Candidate Intake / Publication Pipeline

**Goal:** implement the highest-value Evolver-inspired capability in AGENT33-native form.

**Scope**

- intake workflow for external/community assets
- integrity/provenance check hooks
- automatic reduced-confidence assignment for external sources
- validation/publication/revocation workflow with operator approval
- append-only intake and decision journals tied to lineage/provenance IDs

**Acceptance criteria**

- imported external assets land in candidate mode by default
- publication requires explicit review
- revocation path exists
- lifecycle is visible in durable logs or UI-adjacent surfaces

### Sprint 3 — Thin Mailbox / Heartbeat Pilot

**Goal:** borrow Evolver’s strongest runtime seam without changing AGENT33’s core architecture.

**Scope**

- pilot a thin mailbox/proxy edge for remote coordination and auth isolation
- add heartbeat/task metrics and replay-friendly coordination journaling
- keep local runtime authoritative
- keep hub sync/catalog participation optional and flag-gated
- prove the seam adds value before expanding any broader proxy surface

**Acceptance criteria**

- local runtime still works with no remote dependency
- proxy boundary is additive, not a parallel runtime
- heartbeat and failure/retry signals are explicit
- the pilot is clearly subordinate to AGENT33’s existing workflow/state model

### Sprint 4 — Lifecycle Verbs and Operator UX

**Goal:** make the lifecycle legible and easy to operate.

**Scope**

- introduce explicit workflow verbs:
  - ingest
  - validate
  - report
  - promote
  - export
- add or update operator docs and frontend surfaces for lifecycle visibility
- add role-based docs navigation and a local-only quickstart lane
- split product docs from protocol/runtime/safety docs where needed

**Acceptance criteria**

- operators can understand asset state and required next step quickly
- docs no longer overload one surface with all concerns
- lifecycle verbs are reflected consistently in docs and tooling
- docs index provides clearer entry lanes by user role

### Sprint 5 — Detect-Only Skills Doctor

**Goal:** adapt Evolver’s skill-monitor value without losing governance.

**Scope**

- health scan for skill/package/doc issues
- dry-run repair proposals
- auditable repair path, operator-triggered only

**Acceptance criteria**

- detection works without mutation
- repair actions are logged before execution
- no hidden installs or stub generation occur automatically

## Priority Decision

If AGENT33 only does one Evolver-inspired adaptation soon, it should be:

**Sprint 2 — candidate intake / publication with append-only evidence journaling**

That is the best combination of:

- high leverage
- strong governance fit
- low legal risk
- minimal platform drift

The **next-most valuable follow-up** after that is:

**Sprint 3 — thin mailbox / heartbeat pilot**

That captures Evolver’s clearest code-level operational strength without
displacing AGENT33’s existing lifecycle, trust, or curation model.

## Recommendation

**Proceed with concept-only clean-room adaptation.**  
Do **not** ingest Evolver code, docs, or licensing assumptions. Convert the
highest-value ideas into AGENT33-native slices, starting with governed
candidate intake, explicit publication gates, append-only operational evidence,
and then a narrow mailbox / heartbeat pilot.
