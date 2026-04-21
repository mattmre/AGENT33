# Evolver Clean-Room Guardrails

**Authority**: Architectural Decisions #17 and #18 in `docs/phases/PHASE-PLAN-POST-P72-2026.md`  
**Research basis**: `docs/research/evolver-adaptive-ingestion-2026-04-20.md`  
**Ingestion decision**: `docs/research/evolver-ingestion-task-2026-04-20.md`  
**Date locked**: 2026-04-20  
**Status**: Binding for all Evolver-inspired implementation sprints (Sprints 1–5)

---

## 1. Legal Boundary

### Why GPL-3.0 vs MIT Matters

AGENT33 is published under the **MIT license**, which permits commercial use, modification,
distribution, and sublicensing with minimal restrictions. The MIT license requires only
attribution; it does not impose copyleft or share-alike obligations on downstream users.

The EvoMap/Evolver project presents **conflicting license signals**:

- The repository metadata and `package.json` indicate `GPL-3.0` or `GPL-3.0-or-later`.
- The `SKILL.md` file ends with `MIT`.

Until Evolver's upstream resolves this inconsistency, AGENT33 must **assume GPL-3.0
constraints apply**. This is not optional caution — it is the only legally defensible
default when faced with ambiguous signals in an open-source dependency.

**What GPL-3.0 copyleft would require of AGENT33 if triggered:**

- Any work that incorporates or distributes GPL-3.0 code must itself be distributed
  under GPL-3.0.
- This would force AGENT33 to relicense from MIT to GPL-3.0, eliminating the right
  of downstream users to incorporate AGENT33 into proprietary or non-GPL software.
- Even if AGENT33 never distributes the Evolver code directly, derivative works and
  combined works that share linked execution with GPL code can be subject to copyleft.

**The mitigation: clean-room adaptation.**

Clean-room adaptation means working from a description of *what* a system does
(its concepts, patterns, and goals) rather than *how* it does it (its source code,
data structures, and prose documentation). The result is an independently created
implementation that can demonstrate it did not originate from the GPL-licensed work.

### What "Clean-Room" Means in Practice

1. **No code copy-paste.** Not a single function, method, class, variable name, or
   comment may be copied or transcribed from Evolver source files into AGENT33.

2. **No prose reuse.** Documentation text, protocol descriptions, and architectural
   prose from Evolver docs or `SKILL.md` must not be reproduced verbatim or in
   lightly paraphrased form in AGENT33 files.

3. **Conceptual reference only.** The research in
   `docs/research/evolver-adaptive-ingestion-2026-04-20.md` identified and described
   the *ideas* present in Evolver. All AGENT33 implementations must be derived from
   those described ideas using AGENT33-native vocabulary and design decisions — not
   from reading Evolver source directly.

4. **First-principles defensibility.** Every design decision in an Evolver-inspired
   slice must be explainable without citing Evolver as the source. The authority is
   always AGENT33's own architectural decisions (#17, #18) and the pre-existing
   AGENT33 governance, provenance, and lifecycle model.

5. **Authority references.** Comments, docstrings, and documentation must cite
   `docs/phases/PHASE-PLAN-POST-P72-2026.md` decision #17 or #18 — not Evolver — as
   the mandate for any pattern that was inspired by the research.

---

## 2. What We Are Adapting

The following six conceptual patterns were identified in
`docs/research/evolver-adaptive-ingestion-2026-04-20.md` as carrying genuine value
and being translatable into AGENT33's architecture without legal or architectural risk.
All six are re-expressed here in AGENT33-native terms. No Evolver text is reproduced.

### Pattern 1: Proxy / Mailbox Isolation

**The concept.** Keep a thin boundary between the local runtime and any remote
coordination surface. The local authority is never disrupted by remote unavailability.
Incoming coordination messages are buffered and processed asynchronously rather than
flowing directly into the core runtime.

**AGENT33 adaptation.** A future thin coordination layer (Sprint 3) will isolate remote
hub or A2A traffic from the core engine. The local engine remains authoritative whether
or not the remote layer is reachable. No Evolver-specific protocol names or API shapes
are to be used.

### Pattern 2: Candidate Intake with Lowered Confidence for External Assets

**The concept.** Any asset received from an external or community source should enter
the system with a reduced trust level and a non-executable state. Trust is earned through
explicit review, not assumed from origin.

**AGENT33 adaptation.** Incoming external assets land in `CANDIDATE` status with
`ConfidenceLevel.LOW` assigned automatically. The asset cannot be used in production
workflows until it has been explicitly promoted. This maps directly into the AGENT33
provenance and trust model already present in `engine/src/agent33/packs/`.

### Pattern 3: Append-Only Operational Journals

**The concept.** Intake, review, promotion, and revocation decisions should produce
durable records that can be replayed for auditing and debugging. These records are
subordinate to the canonical lifecycle state — they are evidence, not the source of truth.

**AGENT33 adaptation.** Sprint 2 will add append-only intake and decision journal records
tied to AGENT33's existing lineage and provenance IDs. The canonical state remains in the
`CandidateAsset` lifecycle model. Journals are evidence that can be replayed; they do not
replace or override lifecycle state.

### Pattern 4: Heartbeat / Task Metrics

**The concept.** Coordination flows should emit observable signals: heartbeat, task
start/end, and retry/failure events. These signals belong in the operator view, not
buried in logs.

**AGENT33 adaptation.** Sprint 3 introduces heartbeat and task-level metrics surfaced
through AGENT33's existing observability layer. The design will reuse the metrics and
tracing infrastructure already in `engine/src/agent33/observability/`.

### Pattern 5: Explicit Lifecycle Verbs

**The concept.** The vocabulary of asset operations should be unambiguous. Operators
should be able to understand exactly what step is required next by reading the current
state and the available actions on it.

**AGENT33 adaptation.** Sprint 4 formalizes the following verbs as first-class
operations in AGENT33's API and CLI:

- `ingest` — bring an external asset into the system at `CANDIDATE` status
- `validate` — advance a `CANDIDATE` to `VALIDATED` after review checks pass
- `report` — produce a human-readable summary of an asset's current lifecycle state
- `promote` — advance a `VALIDATED` asset to `PUBLISHED` (makes it executable)
- `export` — package an asset for distribution to another system or tenant

These verbs do not use Evolver naming. They are derived from AGENT33's existing
governance model and the lifecycle states defined in architectural decision #18.

### Pattern 6: Offline-First Operation with Optional Remote Participation

**The concept.** The system must be fully operational without any remote dependency.
Remote sync, catalog participation, and hub communication are opt-in features that add
value when available but are never required for the core runtime to function.

**AGENT33 adaptation.** AGENT33 is already local-first. Sprints 3 and 4 will strengthen
the documentation of this posture. Remote participation features will be guarded by
explicit configuration flags and documented as optional extensions. No Sprint 0–5 work
will introduce any mandatory remote dependency.

---

## 3. What We Are NOT Adapting

The following Evolver patterns were evaluated and explicitly rejected. No future sprint
may implement these behaviors, even in spirit.

### Self-Mutating Repair Behavior

Evolver includes a skill monitor that can detect issues and automatically apply remediation
steps — including rewriting stubs, installing dependencies, and modifying configuration —
without operator approval. This conflicts with AGENT33's governance model.

**AGENT33 position.** Sprint 5 will implement a "detect-only skills doctor." Detection
runs without mutation. Any proposed repair is presented as a dry-run plan for operator
review. No repair action executes automatically. Silent mutation of any AGENT33 artifact
is prohibited.

### Report-Generation Architecture Inflation

Evolver's reporting scripts (`analyze_by_skill.js`, `human_report.js`) are downstream
aggregation utilities built on top of accumulated history. They are not evidence of a
superior modular workflow architecture. Treating history-report output as an architectural
signal inflated the apparent depth of Evolver's workflow design in early analysis rounds.

**AGENT33 position.** AGENT33 has a first-party observability and evaluation layer. New
reporting surfaces will be added only where there is a genuine operator need, and they
will be implemented within the existing observability module rather than as standalone
accumulation scripts.

### Committed Obfuscated Source Patterns

Two important GEP files in the Evolver repository were found in committed obfuscated
form. Obfuscated committed source is incompatible with AGENT33's reviewability and
provenance requirements. AGENT33 cannot verify what obfuscated code does, cannot audit
it for security issues, and cannot rely on it as a design reference.

**AGENT33 position.** All AGENT33 source is reviewable. No obfuscated or pre-compiled
artifact may be committed as source in the `engine/src/` tree. Any committed binary or
compiled asset must pass the pack signing and provenance checks defined in the packs
subsystem.

### Auto-Heal Posture

Related to self-mutating repair: any pattern that allows the system to assume correctness
of an action and execute it without explicit operator confirmation is out of bounds.
"Auto-heal" framing treats silent remediation as a feature. AGENT33 treats it as a
governance violation.

**AGENT33 position.** All remediation actions require explicit operator authorization.
The burden of proof for any repair is the operator's deliberate invocation, not the
system's judgment that repair is needed.

---

## 4. Implementation Rules for Sprints 1–5

Every implementation sprint that builds Evolver-inspired functionality must follow these
rules without exception. These rules exist to protect AGENT33's legal posture, governance
model, and long-term maintainability.

### Rule 1: No Evolver-Derived Code

No function, class, method, variable name, constant, or comment in any AGENT33 file may
originate from Evolver source. "Originate" includes:

- copy-paste from any Evolver file
- transcription from memory of Evolver code
- paraphrase of Evolver code structure or variable naming that produces functionally
  equivalent Python from the same mental model as the Evolver JavaScript

If a reviewer cannot verify that a piece of code was invented independently, it must be
rewritten.

### Rule 2: First-Principles Justification

Every design decision in an Evolver-inspired sprint must be expressible from first
principles without citing Evolver as the authority. For example:

- Do not write: "we use append-only stores because Evolver does"
- Do write: "we use append-only stores because they provide replayable evidence for
  operator review, which is required by AGENT33's lineage and provenance model
  (architectural decision #17)"

The same pattern from different reasoning leads to the same implementation but with
verifiable provenance.

### Rule 3: Cite AGENT33 Authority, Not Evolver

All new code, docstrings, and documentation that implement Evolver-inspired patterns
must cite AGENT33's own architectural decisions as the authority:

- Decision #17: "Evolver ingestion boundary: concept-only clean-room adaptation"
- Decision #18: "Imported-asset lifecycle: `candidate -> validated -> published ->
  revoked`, with confidence/trust labels layered onto those states"

These decisions are in `docs/phases/PHASE-PLAN-POST-P72-2026.md`.

### Rule 4: No Hub-Specific Semantics as Runtime Primitives

Evolver's A2A and hub naming conventions must not become core AGENT33 abstractions.
AGENT33 has its own vocabulary. Use AGENT33-native terms in all code and documentation.
If a future remote coordination layer uses a hub protocol, it must be an optional adapter
behind a stable AGENT33-native interface, not a first-class runtime primitive.

### Rule 5: No Mandatory Remote Dependency

No code added in Sprints 1–5 may require a remote service to function. Remote sync,
catalog participation, and hub communication must be guarded by explicit configuration
flags with documented defaults of disabled or optional.

### Rule 6: Reviewable Source Only

All code committed to AGENT33 must be human-readable, un-obfuscated Python. This applies
to the `ingestion` module and all future sprint deliverables. Any asset that cannot be
reviewed line-by-line by a human auditor has no place in the AGENT33 source tree.

---

## 5. Canonical Lifecycle

Architectural decision #18 defines the canonical imported-asset lifecycle. This section
documents the full lifecycle contract that all sprints must implement against.

```
candidate -> validated -> published -> revoked
```

### Stage: CANDIDATE

**Entry condition.** An asset enters `CANDIDATE` status when it is first ingested from
any external or community source. First-party assets created internally may skip this
stage if they are authored directly into `PUBLISHED` state by an authorized operator.

**Confidence label.** Assets arriving from unreviewed external or community submissions
receive `ConfidenceLevel.LOW`. Assets arriving from community-reviewed sources with
known reputation may receive `ConfidenceLevel.MEDIUM`.

**Behavior.** A `CANDIDATE` asset is non-executable. It may be inspected, documented,
and reviewed, but no AGENT33 workflow, agent, or tool may invoke it as an active
dependency.

**Required before transition.** An operator must explicitly run the `validate` verb
against the asset after completing review checks.

### Stage: VALIDATED

**Entry condition.** A `CANDIDATE` asset is promoted to `VALIDATED` when all configured
review checks pass and an authorized operator invokes the `validate` lifecycle verb.

**Confidence label.** Confidence may be upgraded from `LOW` to `MEDIUM` at this stage
if review checks confirm the asset's origin, integrity, and behavioral claims. `HIGH`
confidence is reserved for first-party assets.

**Behavior.** A `VALIDATED` asset is still non-executable in production. It may be used
in sandboxed evaluation runs and dry-run checks. A `VALIDATED` asset can be demoted back
to `CANDIDATE` if review findings are subsequently reversed.

**Required before transition.** An operator must explicitly run the `promote` verb after
satisfying any publication requirements.

### Stage: PUBLISHED

**Entry condition.** A `VALIDATED` asset is promoted to `PUBLISHED` when an authorized
operator invokes the `promote` lifecycle verb and any required publication gates pass.

**Confidence label.** `ConfidenceLevel.HIGH` is only assigned at this stage for assets
that were both validated and promoted with full provenance documentation. Community-origin
assets may remain at `MEDIUM` confidence even after publication if their upstream cannot
be fully audited.

**Behavior.** A `PUBLISHED` asset is executable by agents and workflows according to
its pack permissions and tenant governance policies.

**Required before transition.** An operator may invoke the `revoke` verb at any time
to remove the asset from active use.

### Stage: REVOKED

**Entry condition.** A `PUBLISHED` or `VALIDATED` asset is moved to `REVOKED` when an
operator determines it should no longer be usable. The revocation must include a reason.

**Confidence label.** Confidence is set to `LOW` on revocation, regardless of prior level.

**Behavior.** A `REVOKED` asset is non-executable. It remains in the system for audit
and provenance purposes. It cannot be re-promoted directly — it must re-enter the
lifecycle as a new `CANDIDATE` if re-evaluation is needed.

**Revocation record.** The `revoked_at` timestamp and `revocation_reason` are recorded
permanently on the `CandidateAsset` model. These fields are append-only once set.

### Confidence / Trust Label Summary

| Stage     | Default Confidence         | Notes                                     |
|-----------|---------------------------|-------------------------------------------|
| CANDIDATE | LOW                        | All external / community intake           |
| CANDIDATE | MEDIUM                     | Community-reviewed, known reputation      |
| VALIDATED | MEDIUM                     | Review checks passed                      |
| VALIDATED | HIGH                       | First-party only                          |
| PUBLISHED | MEDIUM or HIGH             | HIGH only with full provenance audit      |
| REVOKED   | LOW                        | Forced to LOW on revocation               |

---

## 6. Sprint Plan (Sprints 1–5)

### Sprint 1 — Safe Ingestion State Model

**Goal.** Formalize the asset lifecycle and schema without adding runtime behavior.

**What it implements.**
- `CandidateAsset` Pydantic model (started in Sprint 0 stub; Sprint 1 adds validation rules)
- Provenance, decision, and operational journal schema definitions
- Policy rule: candidate assets are explicitly non-executable
- Unit tests verifying lifecycle transition validity

**Authority.** Architectural decisions #17 and #18. Research in
`docs/research/evolver-adaptive-ingestion-2026-04-20.md` Sprint 1 plan.

**Acceptance criteria.**
- Lifecycle states, confidence labels, and schema are defined and tested
- No candidate asset can be marked executable by policy
- No Evolver code or prose is present

### Sprint 2 — Candidate Intake and Publication Pipeline

**Goal.** Implement the highest-value Evolver-inspired capability: governed intake,
validation, promotion, and revocation with append-only evidence journaling.

**What it implements.**
- Intake workflow: external asset arrives, provenance/integrity check hooks run,
  `CANDIDATE` + `LOW` confidence assigned automatically
- Validation workflow: operator-triggered, review checks pass, advance to `VALIDATED`
- Publication workflow: operator-triggered `promote`, publication gates pass, `PUBLISHED`
- Revocation workflow: operator-triggered, reason recorded, `REVOKED`
- Append-only intake and decision journal tied to lineage/provenance IDs
- API and CLI surface for the lifecycle verbs

**Acceptance criteria.**
- External assets land in `CANDIDATE` by default
- Publication requires explicit operator review
- Revocation path exists and reason is recorded
- All state transitions are journaled

### Sprint 3 — Thin Mailbox / Heartbeat Pilot

**Goal.** Add a thin coordination boundary without displacing the local runtime.

**What it implements.**
- Thin coordination facade that buffers incoming remote messages
- Local runtime remains authoritative with no remote dependency
- Heartbeat and task metrics emitted through the existing observability layer
- Append-only coordination journal for replay and debugging
- Hub sync / catalog participation guarded by explicit opt-in configuration

**Acceptance criteria.**
- Local runtime works with no remote service
- Proxy boundary is additive, not a parallel runtime
- Heartbeat and failure/retry signals are observable
- Pilot is subordinate to existing workflow/state model

### Sprint 4 — Lifecycle Verbs and Operator UX

**Goal.** Make the asset lifecycle legible and easy to operate.

**What it implements.**
- Explicit CLI and API workflow verbs: `ingest`, `validate`, `report`, `promote`, `export`
- Frontend or operator surface for lifecycle state visibility
- Role-based documentation navigation: operator / developer / integrator / contributor
- Local-first quickstart docs lane that works without any remote service
- Separation of product docs, protocol docs, runtime docs, and safety docs

**Acceptance criteria.**
- Operators can read the current state and required next step without reading source code
- Lifecycle verbs are consistent between API, CLI, and documentation
- Docs no longer overload one surface with all concerns

### Sprint 5 — Detect-Only Skills Doctor

**Goal.** Adapt the skill-monitor concept without auto-heal behavior.

**What it implements.**
- Health scan for skill, package, and documentation issues
- Dry-run repair proposals with full pre-execution disclosure
- Auditable repair execution path, operator-triggered only
- No silent installs, no automatic stub generation, no hidden mutations

**Acceptance criteria.**
- Detection works without any mutation
- Repair actions are logged and shown before execution
- Operator must take an explicit action to apply any repair
- No hidden installs or stub generation occur automatically
