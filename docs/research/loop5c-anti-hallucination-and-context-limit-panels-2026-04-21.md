# Loop 5C Anti-Hallucination and Context-Limit Panel Extension

**Date:** 2026-04-21  
**Program:** AGENT-33 research program  
**Loop:** 5C  
**Artifact type:** Research-extension artifact only — not a final roadmap

---

## Status and framing

This Loop 5C artifact extends Loop 3 and Loop 4 specifically where the current evidence is still thin on **hallucination control**, **context failure**, and **repeatable specialist-agent reliability**.

It centers the user vision that:

- agents hallucinate under harness pressure and limited context
- repetitive tasks need known inputs, known outputs, and stronger contracts
- harnesses, skills, markdown guidance, segmentation, and evidence should reduce ambiguity
- siloed specialized agents should be more reliable because their scope is narrower
- the platform should keep learning from new repos, models, and workflows without losing trustworthiness

This document is intentionally **not** a roadmap. It is a research extension for later Loop 5 critique and council audit.

## Inputs used

- Session-local `plan.md`
- `docs/research/loop3-cross-batch-capability-synthesis-2026-04-21.md`
- `docs/research/loop4-initial-architecture-phase-proposal-2026-04-21.md`
- Supporting baseline and evidence references:
  - `docs/functionality-and-workflows.md`
  - `docs/default-policy-packs.md`
  - `docs/research/session89-s27-context-window-scope.md`
  - `docs/research/session89-s28-tool-loop-scope.md`
  - `docs/research/session89-s29-skill-matching-scope.md`
  - `docs/research/session89-s23-trust-dashboard-scope.md`
  - `docs/research/session116-p1-runtime-boundaries-scope.md`
  - `docs/research/session116-p2-state-roots-scope.md`
  - `docs/research/session126-p69b-api-contract.md`
  - `docs/research/session126-p69b-ux-spec.md`
  - `docs/research/session50-skill-packs-architecture.md`
  - `docs/research/repo_dossiers/system-prompts-ai-tools.md`
  - `docs/research/repo_dossiers/ai-researcher.md`

---

## Panel method and evidence posture

| Lens | Strong current signal | Thin evidence that still needs extension |
|---|---|---|
| **Architecture panel** | Loop 3 strongly supports explicit governance, normalized events, bounded memory, exact-diff discipline, and governed skill lineage | Still underspecified: segmentation unit, context-assembly policy, claim-to-evidence contract, and specialist-agent handoff rules |
| **Evaluation / research panel** | Strong signal for deterministic monitors, replay, citation UX, and structured evaluation surfaces | Weak signal on which hallucination metrics should gate progress, and how to benchmark context collapse vs normal task failure |
| **DX panel** | Strong signal for progressive disclosure, skill packaging, operator-visible context/policy panels, and clearer tool guidance | Thin signal on how much markdown guidance helps before it becomes token bloat or conflicting instruction load |
| **Security / trust panel** | Strong signal for deny/ask/approval policies, trust dashboards, provenance, state roots, and durable pause/resume flows | Thin signal on how to separate side-effect governance from truthfulness governance, and how to detect unsupported claims without heavy human review |

### Synthesis across the panel

The strongest cross-source conclusion is that AGENT-33 should fight hallucination mainly by **shrinking ambiguity at runtime**, not by adding large governance ceremony.

That means the center of gravity should be:

1. narrower task scope
2. smaller and budgeted context assemblies
3. deterministic I/O and evidence contracts
4. automated monitors and harness checks
5. operator review only at exception points

---

## 1) Framework for reducing hallucination and context failure without relying primarily on heavy governance overhead

### Proposed framework: **Contracted Narrowing Loop**

AGENT-33 should treat anti-hallucination as a five-layer runtime discipline.

### Layer A — Scope shaping before the model call

Reduce ambiguity before inference starts.

- choose a **specialist agent** or skill bundle instead of a generalist whenever the task is repetitive or well-scoped
- activate only the tools, skills, and guidance relevant to that slice
- use proactive context budgeting before the first call, not only reactive summarization during overflow
- prefer harnessed task modes when inputs/outputs are already known

**Why this matters:** most hallucination pressure is created before generation, when too many tools, instructions, memories, and goals are loaded together.

### Layer B — Segmented execution with frozen handoffs

Break long work into bounded segments.

- each segment should have one job, one contract, and one bounded working set
- handoffs should pass a **frozen artifact bundle** rather than a prose-only summary when possible
- specialist agents should inherit only the subset of context needed for their segment
- replay should preserve segment boundaries so later review can isolate where drift began

**Why this matters:** long multi-purpose loops accumulate ambiguity faster than they accumulate truth.

### Layer C — Deterministic execution contracts

Make repeated work machine-checkable.

- require structured inputs and outputs for repetitive tasks
- use exact-diff and read-before-write rules on mutation surfaces
- prefer schema checks, invariant checks, and harness assertions over model self-certification
- keep tool usage and retry policy executable in code, not only in prompt prose

**Why this matters:** the system should not need to “trust the model more” for repeated work. It should need to trust the contract more.

### Layer D — Evidence-bound answering

Separate acting from claiming.

- tool permissions answer **“may the agent do this?”**
- evidence requirements answer **“may the agent claim this?”**
- final outputs should carry citations, source artifacts, trace IDs, or “insufficient evidence” markers depending on task type
- unsupported claims should be treated as validation failures, not style issues

**Why this matters:** current governance work is stronger on side effects than on truthfulness. Anti-hallucination needs both.

### Layer E — Exception-driven oversight

Use humans and expensive models mostly for disagreements, not routine flow.

- deterministic monitors should run first
- loop scoring should detect stalled or repetitive tool behavior
- approval, checkpoint, or review surfaces should appear when thresholds trip, not on every task
- operator panels should show context budget, evidence coverage, contract status, and blocked reasons

**Why this matters:** trust improves when review is targeted and legible, not when every run is slowed by blanket governance overhead.

### Design rule

**Default strategy:** reduce the model’s room to improvise before adding more reviewers.

That is the key Loop 5C anti-hallucination posture.

---

## 2) Recommended roles for skills, markdown guidance, harness constraints, segmentation, I/O contracts, and evidence requirements

| Mechanism | Primary role | Anti-hallucination benefit | Failure mode if underspecified |
|---|---|---|---|
| **Skills** | Package narrow instructions, allowed/disallowed tools, defaults, approvals, and reusable task heuristics | Reduce task ambiguity and activate only relevant capabilities | Skills become prompt bloat or conflicting meta-prompts rather than scope reducers |
| **Markdown guidance** | Provide stable human-authored heuristics, checklists, templates, and decision rules | Gives compact, durable domain guidance without retraining | Guidance drifts, duplicates tool docs, or grows beyond context budget usefulness |
| **Harness constraints** | Enforce executable limits: fixtures, schemas, retries, timeout, sandbox, approval thresholds | Converts repeated tasks from open-ended reasoning into bounded execution | Harnesses stay too loose, so “tested” runs still allow fabricated intermediate states |
| **Segmentation** | Divide work into small bounded stages with frozen outputs and narrow context inheritance | Prevents whole-run context collapse and makes failure localization possible | Handoffs become lossy summaries that introduce new hallucinations |
| **I/O contracts** | Define exact inputs, outputs, invariants, and acceptable side effects | Makes repeated/siloed tasks checkable without human interpretation | Agents produce plausible but non-conforming outputs that slip through |
| **Evidence requirements** | Force claims to attach to artifacts, citations, traces, or explicit unknown-state markers | Prevents fluent unsupported assertions from being treated as success | The system can act safely but still explain falsely |

### Specific recommended role by mechanism

#### Skills

Skills should become **runtime narrowing objects**, not just reusable instructions.

Recommended minimum role:

- declare intended task class
- declare allowed/disallowed tools
- declare approval-required operations
- declare expected input and output shape for repetitive work
- declare evidence expectations where applicable
- declare instruction size ceilings so skills do not silently consume the context budget

The existing skill architecture already points in this direction through frontmatter, governance fields, progressive disclosure, and instruction limits. The anti-hallucination extension is to make those fields matter at runtime selection time, not only at packaging time.

#### Markdown guidance

Markdown guidance should serve as **compressed operational judgment**.

Use it for:

- task checklists
- failure pattern reminders
- “when to use / when not to use” tool guidance
- report templates and output skeletons
- evidence rubrics

Do **not** use it as a dumping ground for large background knowledge. If it is too long to survive context budgeting, it is no longer guidance; it is context pollution.

#### Harness constraints

Harnesses should carry most of the repeatability burden.

Recommended role:

- provide known input fixtures or task envelopes
- define allowed actions and retries
- define expected output schema or acceptance checks
- expose explicit fail states for unsupported claims, malformed outputs, or repeated non-convergent loops

This is especially important for repetitive tasks. The more repeatable the task, the less the system should rely on free-form reasoning.

#### Segmentation

Segmentation should be the default for:

- long research runs
- browser/computer-use tasks
- code-editing runs that touch multiple files or stages
- any workflow likely to exceed a safe context assembly

Recommended segmentation rule:

- one segment = one main decision surface + one bounded artifact handoff

The handoff should prefer artifact bundles, schemas, or exact diffs over narrative summaries.

#### I/O contracts

I/O contracts should be mandatory for repeated or specialist work.

At minimum they should answer:

- what input shape is accepted
- what output shape is required
- what side effects are allowed
- what evidence must accompany the output
- what validator determines pass/fail

This is the strongest non-governance lever for repeated reliability.

#### Evidence requirements

Evidence requirements should be tiered by task type.

- **Research / external claims:** citations or fetched artifacts required
- **Code / file mutation:** exact diffs, file paths, validation output, and trace references required
- **Browser / computer-use:** action log plus canonical page-state evidence required
- **Planning / synthesis:** source section references or explicit uncertainty markers required

The platform should support **“insufficient evidence” as a first-class acceptable outcome**.

---

## 3) Which parts of the Loop 4 draft are underspecified relative to anti-hallucination needs

| Loop 4 area | What is underspecified | Why it matters for anti-hallucination |
|---|---|---|
| **Phase A — runtime control plane** | It names a normalized event contract, but not a **claim/evidence contract**, context-assembly rules, or segment handoff schema | The control plane can govern actions while still allowing unsupported or over-contexted answers |
| **Phase A — permission plane** | It is strong on `allow|ask|deny`, but weak on when the system must say **unknown / insufficient evidence** | Side-effect safety and truthfulness safety are adjacent but not identical |
| **Phase B — dual-surface UX** | It proposes context/policy panels, but not explicit unsupported-claim warnings, evidence coverage indicators, or context-budget exhaustion UX | Operators need to see reliability state, not only cost and approvals |
| **Phase C — durable execution** | It does not yet define checkpoint contents as artifact bundle vs summary vs state snapshot | Poor checkpoint design can preserve execution while losing factual grounding |
| **Phase C — replay** | Replay is discussed mainly as execution history, not as proof of why an answer was justified | Anti-hallucination review requires claim lineage, not only event lineage |
| **Phase D — bounded memory** | It lacks source precedence rules between working memory, retrieval memory, snapshots, and operator directives | Without precedence rules, memory can become contamination rather than support |
| **Phase D — lineage** | Lineage is present, but the draft does not define what unit of context becomes frozen and reusable | Reliable reuse needs frozen, trusted units rather than arbitrary summaries |
| **Phase E — browser/computer use** | Supervision hooks are named, but canonical evidence artifacts are not | Browser tasks are especially prone to hallucinated page state unless evidence is standardized |
| **Phase F — skill supply chain** | It covers lineage and promotion but not runtime fields for input schema, output schema, evidence policy, or max context footprint | Skill trust is incomplete if runtime contract quality is invisible |
| **Overall Loop 4 posture** | It treats hallucination mostly as a downstream effect of governance, memory, and replay gaps | Loop 5C suggests hallucination also needs explicit **task narrowing, contracting, and evidence gating** as first-class design objects |

### Bottom-line critique of Loop 4

Loop 4 is directionally strong, but it is still stronger on **control-plane architecture** than on **truth-production architecture**.

For anti-hallucination purposes, the missing first-class concepts are:

1. context assembly policy
2. segmentation and handoff contract
3. claim-to-evidence policy
4. repeated-task I/O contracts
5. runtime skill narrowing rules
6. explicit unknown-state handling

---

## 4) Specific additional research questions or repo-pattern follow-ups needed for a clearer answer

### Highest-priority research questions

1. **What should the minimal runtime contract schema be for repetitive tasks?**  
   Candidate fields: `task_type`, `input_schema`, `output_schema`, `validator`, `allowed_tools`, `evidence_required`, `max_context_tokens`, `handoff_artifacts`.

2. **How often does current AGENT-33 prompt assembly exceed or nearly exceed safe context budgets in real runs?**  
   Loop 5 needs measured distribution data, not only the existence of S27.

3. **Which parts of skill injection improve accuracy, and which parts only increase token load?**  
   S29 gives matching infrastructure, but not outcome evidence on wrong-skill activation vs no-skill activation.

4. **What is the best handoff unit between specialist agents?**  
   Options include artifact bundle, typed summary, frozen state root, exact diff set, or mixed bundle.

5. **Which deterministic monitors best detect hallucination-like failures?**  
   Candidate classes: missing citation, schema mismatch, impossible tool reference, contradictory summary, repeated tool-loop convergence failure, stale evidence source.

6. **How should AGENT-33 represent “unknown” and “insufficient evidence” in the UX and APIs?**  
   This needs to be a contract state, not just wording advice.

7. **Where should memory be allowed to influence truth claims versus only retrieval suggestions?**  
   Not all recalled context should have equal epistemic weight.

8. **Which browser/computer-use evidence artifacts are canonical enough to support replay and truth checks?**  
   Possible candidates: DOM snapshot, accessibility tree delta, screenshot, action trace, network trace.

### Repo-pattern follow-ups worth reopening

1. **OpenHarness / GBrain**  
   Re-check actual deterministic inspector stages and monitor boundaries, not just high-level descriptions.

2. **Nanobot / OpenClaw / CoreCoder / HolyClaude**  
   Re-check how far read-before-write and exact-diff discipline can generalize beyond file editing.

3. **Hermes / Hermes WebUI / HolyClaude**  
   Re-check how snapshot, bounded memory, and replay are kept small enough to stay usable under context pressure.

4. **AI-Researcher**  
   Re-check atomic decomposition, bidirectional mapping, and hierarchical synthesis as anti-hallucination patterns for long-form outputs.

5. **system-prompts-ai-tools**  
   Re-check structural prompt patterns only: progressive disclosure, explicit “when to use / when not to use,” citation rules, and uncertainty handling. Do not treat archived prompts as authoritative content.

### AGENT-33-internal follow-ups that would sharpen the answer

1. Instrument real context-budget telemetry across agent invocations.
2. Compare LLM-selected vs hybrid-selected skill activation on repeated tasks.
3. Audit which existing APIs already imply hidden I/O contracts that could be formalized.
4. Sample replay traces for loop-degeneration patterns once S28-style scoring is wired end-to-end.
5. Audit where operator docs or runbooks already encode tacit contracts that should move into machine-readable skill or harness metadata.

---

## 5) Refined list of platform capabilities that most directly improve reliability for repeated/siloed agent work

### Highest-impact capabilities

1. **Proactive context assembly and budget enforcement**  
   Per-component token budgeting, progressive disclosure, and preflight warnings before the first model call.

2. **Contract-aware skill activation**  
   Skills selected by task fit, bounded by size, and carrying executable governance plus I/O metadata.

3. **Segment planner with frozen handoff bundles**  
   Long tasks automatically split into bounded specialist segments with artifact-based handoffs.

4. **Harness templates for repeated task classes**  
   Known fixtures, validators, retry policy, and fail states for common workflows.

5. **Deterministic validation and monitor chain**  
   Schema checks, diff checks, evidence checks, and loop-degeneration checks before model-mediated review.

6. **Evidence receipt model**  
   Every important answer artifact can point to citations, traces, snapshots, diffs, or explicit insufficient-evidence state.

7. **Exact mutation contracts across side-effect surfaces**  
   Read-before-write, exact-match diffing, and bounded mutation scopes generalized where safe.

8. **Checkpoint and lineage model tied to factual handoffs**  
   Checkpoints should preserve not only execution state but also the supporting evidence bundle for the next stage.

9. **Capability-scoped specialist-agent runtime**  
   Specialists should inherit narrower tools, smaller context, and tighter task schema than a general orchestrator.

10. **Trust/provenance surface for skills, packs, and plugins**  
   Provenance should cover not only where a skill came from, but whether its runtime contract is mature and validated.

### Important qualifier

These capabilities improve reliability most when combined as a **narrowing stack**:

- budget less context
- activate fewer tools
- run smaller segments
- require stronger outputs
- escalate only on exceptions

---

## 6) Challenge list for the later council audit

The later council audit should explicitly challenge the plan with the following questions:

1. **Are we actually shrinking ambiguity, or just adding more governance surfaces?**
2. **Do specialist agents have materially narrower context and permissions than general agents, or only different names?**
3. **Does every repeated task class have a machine-checkable input/output contract?**
4. **Can the system return “insufficient evidence” without treating that as a failure of UX polish?**
5. **Are skills improving task fit, or are they becoming uncontrolled prompt expansion?**
6. **Do context budgets account for tool definitions, skill instructions, memory inserts, and evidence payloads together?**
7. **Can an operator see why a claim was made, not just what actions occurred?**
8. **Are monitors deterministic first, with model review reserved for ambiguity and dispute?**
9. **Do checkpoints preserve factual grounding, or only resumability?**
10. **Does memory have provenance and precedence rules strong enough to avoid contamination of the working set?**
11. **For browser/computer use, is the canonical evidence model clear enough to support trustable replay?**
12. **Are approval queues exception-driven, or are we creating operator overload that hides the important failures?**
13. **Which hallucination failures remain after contracts, harnesses, and segmentation are added, and how are they measured?**
14. **Have we overfit to one repo pattern where evidence is still mostly descriptive rather than code-backed?**
15. **Does the platform still learn from new repos, models, and workflows through governed ingestion, or does added trust machinery freeze improvement?**

---

## Research-extension bottom line

Loop 5C suggests that AGENT-33 should frame anti-hallucination primarily as a **runtime narrowing and evidence-binding problem**.

The most reliable path is not heavy process overhead. It is:

- narrower specialist scope
- smaller context assemblies
- stronger segment handoffs
- explicit I/O and evidence contracts
- deterministic monitors before human or model review

Loop 4 already points toward the right control-plane direction. The missing extension is to make **truth-production contracts** as explicit as **permission and execution contracts**.
