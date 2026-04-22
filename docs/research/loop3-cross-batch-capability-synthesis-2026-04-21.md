# Loop 3 Cross-Batch Capability Synthesis

**Date:** 2026-04-21  
**Program:** AGENT-33 research program  
**Loop:** 3  
**Artifact type:** Research synthesis only — not an implementation roadmap

---

## Scope and method

This artifact synthesizes the panel-reviewed Top-20 corpus across four batches and maps the additive findings onto the current AGENT-33 runtime posture.

High-confidence corpus signals used:

- **Batch A:** Codex **ADOPT** for governance; Hermes **DISTILL** for bounded memory, frozen snapshots, lineage; Cline **DISTILL** for checkpoints and review UX; OpenHands **DISTILL** for action-observation-event normalization, while avoiding deprecated V0 / enterprise leakage; browser-use **OBSERVE** for browser watchdog / judge patterns.
- **Batch B:** OpenHarness **ADOPT**; GBrain **ADOPT**; Goose **DISTILL**; OpenClaude **DISTILL**; Cherry Studio **OBSERVE**. Top patterns: inspector chains, durable auto-memory, permission modes + deny lists, chat gateway / operator dashboard, graph/vector/timeline memory, desktop/browser shell packaging.
- **Batch C:** Nanobot **DISTILL**; OpenClaw **DISTILL**; open-multi-agent **DISTILL**; Claurst **OBSERVE**; OpenSpace **OBSERVE**. Top patterns: read-before-write, runtime DAG + queue + approval gates, layered durable memory, pairing / allowlist trust, skill lineage / quality / version DAG.
- **Batch D:** auto-deep-researcher-24x7 **ADOPT**; CoreCoder **DISTILL**; Hermes WebUI **DISTILL**; HolyClaude **DISTILL**; open-codex-computer-use **OBSERVE**. Top patterns: zero-LLM monitoring, bounded two-tier memory, directive inbox, interrupt-capable SSE event contract, exact-match edit + diff, transparent token/cost UX, optional devbox bootstrap, future visual cursor / permission doctor.

Current AGENT-33 baseline was cross-checked against:

- `docs/functionality-and-workflows.md`
- `docs/default-policy-packs.md`
- `docs/research/session109-phase55-browser-scope.md`
- `docs/research/session72-s2-plugin-lifecycle-scope.md`
- `docs/research/session89-s23-trust-dashboard-scope.md`
- `docs/research/session98-p05-dashboards-scope.md`
- `docs/research/session126-p69b-ux-spec.md`

---

## 1) Normalized capability taxonomy across the corpus

| Taxonomy | Normalized capability primitives | Canonical corpus signals |
|---|---|---|
| **Governance / trust** | policy modes, deny lists, approval gates, pairing / allowlists, state-root governance, operator-visible policy surfaces | Codex, OpenHarness, Goose, Nanobot, HolyClaude |
| **Memory** | bounded working memory, frozen snapshots, lineage, durable auto-memory, layered memory, graph/vector/timeline views, directive inbox | Hermes, GBrain, Goose, Hermes WebUI, HolyClaude |
| **Orchestration** | normalized action-observation-event contract, runtime DAG, durable queue, checkpoint/resume, approval-blocked execution, inspector chains | OpenHands, OpenHarness, Nanobot, open-multi-agent, auto-deep-researcher-24x7 |
| **UX / operator shell** | review UX, checkpoint UX, directive inbox, operator dashboard, chat gateway, token/cost visibility, permission doctor | Cline, OpenHarness, Cherry Studio, Hermes WebUI, HolyClaude |
| **Browser / computer use** | browser watchdog, judge loop, safe session supervision, visual cursor, permission overlays, browser/computer replay events | browser-use, open-codex-computer-use |
| **Packaging / bootstrap** | local-first shell packaging, desktop/browser shell, bootstrap wizardry, optional devbox, distribution ergonomics | Cherry Studio, Hermes WebUI, auto-deep-researcher-24x7 |
| **Observability / replay** | zero-LLM monitoring, inspector chains, interrupt-capable SSE, durable replay, event lineage, exact diffs for operator review | OpenHarness, GBrain, auto-deep-researcher-24x7, HolyClaude, CoreCoder |
| **Skill lifecycle** | skill provenance, trust scoring, lineage DAG, quality scoring, version DAG, frozen bundle snapshots | open-multi-agent, Nanobot, OpenSpace, Claurst |

### Normalized interpretation

Across the corpus, the same systems keep converging on eight meta-capabilities:

1. **Governance must be explicit, operator-visible, and interruption-capable.**
2. **Memory must be both durable and bounded.**
3. **Autonomy requires queueable orchestration plus human pause points.**
4. **Operator UX is now part of the runtime contract, not just polish.**
5. **Browser/computer use needs supervisory safety primitives, not only raw actuation.**
6. **Packaging matters because local-first adoption depends on bootstrap quality.**
7. **Observability is shifting from logs to normalized events, monitors, and replay.**
8. **Skills are becoming governed supply-chain objects, not loose prompt files.**

---

## 2) Ranked additive capability inventory for AGENT-33

### Scoring rubric

- **Maturity:** High = repeated strong signal and/or panel ADOPT; Medium = strong DISTILL signal; Low = OBSERVE / exploratory.
- **Transplant difficulty:** Low / Medium / High relative to current AGENT-33 architecture.
- **Governance risk:** Low / Medium / High based on blast radius, policy burden, and safety ambiguity.

| Rank | Capability | Source repos | Maturity | Difficulty | Governance risk | AGENT-33 posture |
|---:|---|---|---|---|---|---|
| 1 | **Governance operating model with explicit policy surfaces**: boundary contracts, state roots, deny-first defaults, operator-visible policy state | Codex, OpenHarness, Goose | High | Medium | Low | **ADOPT** |
| 2 | **Inspector chains + zero-LLM monitoring**: deterministic monitors before expensive or brittle model-side review | OpenHarness, GBrain, auto-deep-researcher-24x7 | High | Medium | Low | **ADOPT** |
| 3 | **Unified permission plane**: allow/ask/deny, deny lists, approval triggers, pairing / allowlist trust | OpenHarness, Goose, Nanobot, HolyClaude | High | Medium | Medium | **ADOPT** |
| 4 | **Bounded two-tier memory with frozen snapshots and lineage** | Hermes, Hermes WebUI, HolyClaude | High | High | Medium | **DISTILL** |
| 5 | **Normalized action-observation-event contract + interrupt-capable SSE** | OpenHands, open-multi-agent, HolyClaude | High | High | Medium | **ADOPT** |
| 6 | **Runtime DAG + durable queue + approval-blocked execution** | Nanobot, open-multi-agent, OpenHarness | High | High | Medium | **DISTILL** |
| 7 | **Checkpoint / review UX + directive inbox** | Cline, CoreCoder, HolyClaude | Medium | Medium | Low | **DISTILL** |
| 8 | **Layered durable auto-memory with graph/vector/timeline views** | GBrain, Goose, Hermes WebUI | Medium | High | Medium | **DISTILL** |
| 9 | **Read-before-write + exact-match edit + diff discipline** | Nanobot, CoreCoder, HolyClaude | High | Low | Low | **ADOPT** |
| 10 | **Skill lineage / quality / version DAG** | open-multi-agent, Nanobot, OpenSpace, Claurst | Medium | Medium | Medium | **DISTILL** |
| 11 | **Transparent token/cost UX for operators** | Hermes WebUI, HolyClaude | Medium | Low | Low | **ADOPT** |
| 12 | **Chat gateway / operator dashboard unification** | OpenHarness, Cherry Studio, HolyClaude | Medium | Medium | Medium | **DISTILL** |
| 13 | **Browser watchdog / judge + visual cursor + permission doctor** | browser-use, open-codex-computer-use | Low | High | High | **OBSERVE** |
| 14 | **Desktop/browser shell packaging and operator shell distribution** | Cherry Studio, Hermes WebUI | Low-Medium | Medium | Medium | **OBSERVE** |
| 15 | **Optional devbox bootstrap as first-class ergonomics** | auto-deep-researcher-24x7 | High | Low | Low | **OBSERVE** *(AGENT-33 already has devbox-like footing)* |
| 16 | **Deprecated V0 / enterprise leakage from OpenHands-era surfaces** | OpenHands | Legacy / mixed | Low | High | **AVOID** |

### Why this inventory is additive to AGENT-33

- **AGENT-33 is already strong** in baseline governance, workflow execution, memory/RAG, dashboards, packs/plugins, and operator-facing docs.
- The additive value is **not** raw feature count. It is the next layer of **runtime discipline**:
  - explicit policy/state roots,
  - bounded yet durable memory,
  - interruptible event contracts,
  - deterministic monitoring,
  - safer edit/review contracts,
  - governed skill lineage.

---

## 3) AGENT-33 gap map

| Category | Current AGENT-33 posture | Additive gaps surfaced by corpus | Gap level |
|---|---|---|---|
| **Governance / trust** | Strong baseline: connector policy packs, autonomy budgets, trust dashboard, and P69b-style `ask`/approval model are already present in docs/specs | Missing a single end-to-end governance operating model that spans tools, workflows, browser/computer use, prompts, pairing/allowlists, and operator-facing diagnosis | **Medium** |
| **Memory** | Strong baseline: PostgreSQL + pgvector, BM25/hybrid retrieval, progressive recall, session memory | Missing bounded two-tier memory, frozen snapshots, lineage/state roots, directive inbox semantics, graph/vector/timeline unification, and auto-memory compaction policy | **High** |
| **Orchestration** | Strong baseline: workflow DAG, scheduling, delegation, approval-blocking spec surfaces | Missing durable queue/checkpoint semantics across all execution layers, normalized action-observation-event contract, inspector chains, and first-class interrupt/resume semantics | **High** |
| **UX / operator shell** | Strong baseline: first-party UI, dashboards, runbooks, process registry, approval UX spec | Missing checkpoint/review UX parity with Cline-style flows, directive inbox, cost-transparent operator surfaces, and permission-doctor style guidance | **Medium-High** |
| **Browser / computer use** | Partial baseline: BrowserTool, browser vision, cloud browser module, ComputerUseTool entry point, approval hooks | Missing browser watchdog/judge loops, visual cursor, permission overlays, richer browser replay events, and stronger safe-supervision contracts | **High** |
| **Packaging / bootstrap** | Strong baseline: Docker/K8s, bootstrap docs, wizard, packs/plugins, devbox | Main gaps are shell packaging/distribution ergonomics; bootstrap itself is no longer the major deficit | **Low-Medium** |
| **Observability / replay** | Good baseline: traces, failure pipeline, replay, dashboards, metrics, SSE/WS surfaces | Missing durable unified replay/event store, zero-LLM monitors, inspector-chain composition, and lineage joining memory + orchestration + approval events | **High** |
| **Skill lifecycle** | Good baseline: packs, trust analytics, plugin lifecycle, registry, slash commands | Missing lineage/quality/version DAG, frozen bundle snapshots, richer trust graph, and promotion/rollback views anchored in skill ancestry | **Medium-High** |

### Category-level synthesis

#### Governance / trust

AGENT-33 already has meaningful pieces, but the corpus points to a stricter target shape: **governance as a visible operating model**, not a collection of controls. Codex and OpenHarness raise the bar here.

#### Memory

AGENT-33 has retrieval and persistence, but the corpus now treats memory as **bounded, layered, lineage-aware state** rather than only searchable storage. This is the clearest structural gap.

#### Orchestration

AGENT-33 can run workflows; the corpus suggests the next standard is **queueable, inspectable, interruption-safe orchestration** with a normalized event model.

#### UX / operator shell

The current UI is broad, but the corpus emphasizes **operator control loops**: checkpoints, inboxes, live approval context, and cost clarity.

#### Browser / computer use

AGENT-33 has browser primitives, but the corpus treats browser/computer use as requiring **supervisory safety tooling**, not only browser APIs.

#### Packaging / bootstrap

AGENT-33 is relatively mature here already. The remaining corpus signal is about **distribution form factor**, not core bootstrap capability.

#### Observability / replay

Current observability is useful but fragmented. The corpus favors **deterministic monitors + normalized event replay + interruption-aware streaming contracts**.

#### Skill lifecycle

AGENT-33 already thinks in packs/plugins; the corpus shifts the frontier toward **skill ancestry, quality, and governed promotion history**.

---

## 4) Capability-by-capability disposition sheet

| Capability | Source repos | Maturity | Difficulty | Governance risk | Recommended posture | Notes for AGENT-33 |
|---|---|---|---|---|---|---|
| Governance operating model / policy state roots | Codex, OpenHarness, Goose | High | Medium | Low | **ADOPT** | Best cross-batch fit because AGENT-33 already has the pieces but not the singular control model |
| Inspector chains | OpenHarness, GBrain | High | Medium | Low | **ADOPT** | High leverage for review, gating, replay, and debugging |
| Zero-LLM monitoring | auto-deep-researcher-24x7, GBrain | High | Medium | Low | **ADOPT** | Strong complement to current observability without increasing inference spend |
| Permission modes + deny lists | OpenHarness, Goose | High | Medium | Medium | **ADOPT** | AGENT-33 already points this way via `ask`; corpus suggests making it universal and operator legible |
| Pairing / allowlist trust | Nanobot, HolyClaude | Medium | Medium | Medium | **DISTILL** | Valuable, but must fit AGENT-33 tenant and pack trust surfaces |
| Bounded memory / frozen snapshots / lineage | Hermes, Hermes WebUI, HolyClaude | High | High | Medium | **DISTILL** | Key structural upgrade; requires careful integration with current memory APIs |
| Durable auto-memory | GBrain, Goose | Medium | High | Medium | **DISTILL** | Attractive but easy to over-collect; needs retention and compaction discipline |
| Graph/vector/timeline memory | GBrain, Hermes WebUI | Medium | High | Medium | **DISTILL** | Likely better as a view over a unified lineage store than as separate systems |
| Runtime DAG + durable queue | Nanobot, open-multi-agent | High | High | Medium | **DISTILL** | AGENT-33 already has DAGs; additive value is durability and approval-aware queueing |
| Action-observation-event normalization | OpenHands, open-multi-agent | High | High | Medium | **ADOPT** | High-value substrate for replay, browser/computer use, and operator UX |
| Checkpoints / review UX | Cline, CoreCoder | Medium | Medium | Low | **DISTILL** | Important operator-layer improvement once normalized events exist |
| Directive inbox | HolyClaude | Medium | Medium | Low | **DISTILL** | Useful synthesis point between approvals, interrupts, and operator tasks |
| Read-before-write discipline | Nanobot, OpenClaw | High | Low | Low | **ADOPT** | Near-term safety gain with low architectural risk |
| Exact-match edit + diff | CoreCoder, HolyClaude | High | Low | Low | **ADOPT** | Strong fit with AGENT-33 mutation/review surfaces |
| Token/cost transparency | Hermes WebUI, HolyClaude | Medium | Low | Low | **ADOPT** | Especially additive for operator trust and long-running runs |
| Chat gateway / operator dashboard | OpenHarness, Cherry Studio | Medium | Medium | Medium | **DISTILL** | Useful if AGENT-33 wants one operator entrypoint across shells/sessions |
| Desktop/browser shell packaging | Cherry Studio, Hermes WebUI | Low-Medium | Medium | Medium | **OBSERVE** | Possible distribution win, but not yet a core architectural gap |
| Browser watchdog / judge | browser-use | Low | High | High | **OBSERVE** | Promising, but should not outrun event normalization and policy maturity |
| Visual cursor / permission doctor | open-codex-computer-use | Low | High | High | **OBSERVE** | Good future-facing UX idea, not yet a Loop 3 transplant target |
| Deprecated V0 / enterprise leakage | OpenHands | Legacy / mixed | Low | High | **AVOID** | Explicit negative transplant: retain normalization lessons, reject stale surface leakage |

---

## 5) Contradictions and tensions that later loops must resolve

1. **Durable auto-memory vs bounded memory**
   - GBrain/Goose push persistent accumulation.
   - Hermes/HolyClaude push bounded, frozen, two-tier memory.
   - Later loops must determine where AGENT-33 should accumulate, freeze, summarize, and forget.

2. **Zero-LLM monitors vs model-mediated inspectors**
   - auto-deep-researcher-24x7 favors deterministic monitors.
   - Inspector-chain designs can drift toward LLM-mediated review.
   - AGENT-33 needs a layered monitor stack, not one monolithic reviewer.

3. **Operator control vs autonomy throughput**
   - Approval gates, deny lists, pairing, and checkpoints improve safety.
   - Durable queues and autonomous DAGs want to minimize operator pauses.
   - Later loops must identify where human interruption is mandatory versus optional.

4. **Exact-match editing vs flexible generation**
   - CoreCoder/HolyClaude favor precise diff contracts.
   - More autonomous systems often tolerate looser semantic edits.
   - AGENT-33 needs a rule for when exactness is mandatory and when semantic transforms are acceptable.

5. **Unified event normalization vs bespoke UX metaphors**
   - OpenHands/open-multi-agent imply a normalized substrate.
   - Cline/HolyClaude emphasize richer, human-friendly checkpoint/inbox UX.
   - The substrate and the UX layer cannot be allowed to diverge.

6. **Open skill ecosystems vs trust-constrained promotion**
   - OpenSpace/Claurst-style lineage and quality DAGs want openness and reuse.
   - Governance/trust systems want allowlists, signatures, promotion gates, and safe defaults.
   - AGENT-33 needs a supply-chain model that preserves both velocity and trust.

7. **Browser/computer-use visibility vs headless reproducibility**
   - browser-use and open-codex-computer-use surface cursor/visual feedback.
   - CI/headless orchestration wants deterministic, non-visual replay.
   - Later loops must decide which browser telemetry is canonical.

8. **Web UI sufficiency vs desktop shell packaging**
   - Cherry Studio-style packaging suggests distribution leverage.
   - AGENT-33 already has a web UI plus devbox.
   - The unresolved question is whether shell packaging changes capability or only form factor.

9. **Frozen state roots vs resumable execution**
   - Snapshot/lineage models prefer immutability.
   - Queue/checkpoint models prefer resumable mutation.
   - AGENT-33 must pick the durable unit: event log, snapshot, queue item, or all three.

10. **Governance in control plane vs governance visible to the model**
    - Codex/OpenHarness imply explicit governance contracts.
    - Many agent systems still keep critical policy outside model-visible context.
    - Later loops should decide how much policy must be surfaced to prompts without overloading the model.

---

## 6) Missing evidence and targeted research questions for Loop 5

1. **What is the minimal normalized event schema** that can cover tool loop, workflow DAG, browser/computer use, approvals, and operator interrupts without creating multiple incompatible event dialects?
2. **Which inspector-chain stages are deterministic versus model-based** in OpenHarness/GBrain-style systems, and what false-positive rates do they report?
3. **How do Hermes/Hermes WebUI/HolyClaude persist frozen snapshots and lineage** without exploding storage or creating stale replay trees?
4. **What retention/compaction policy makes durable auto-memory safe** for AGENT-33 tenants, especially when graph/vector/timeline views all coexist?
5. **Where should AGENT-33 place the boundary between `allow`, `ask`, deny lists, pairing, and operator approval**, and what is the operator-latency cost of each layer?
6. **Can read-before-write and exact-match diff discipline generalize across all mutation surfaces** (files, prompts, pack manifests, browser actions), or is it only safe for text/code edits?
7. **What is the correct resumable checkpoint unit** for AGENT-33: invocation, workflow node, tool call, browser step, or state-root snapshot?
8. **Which browser/computer-use safety signals actually matter** for a watchdog/judge design: screenshots, DOM diffs, accessibility tree deltas, action repetition, or timeouts?
9. **Should AGENT-33 unify approvals, checkpoints, and operator tasks into one directive inbox**, or keep them as separate control surfaces?
10. **What is the right data model for skill lineage / quality / version DAGs** given AGENT-33’s current pack, plugin, and trust-analytics structures?
11. **Which specific OpenHands-era surfaces must be explicitly excluded** to avoid deprecated V0 / enterprise leakage while still preserving normalization lessons?
12. **Does desktop/browser shell packaging materially improve operator adoption** compared with AGENT-33’s current web UI + devbox posture, or is it mostly a distribution preference?

---

## Bottom line

Loop 3 shows that AGENT-33 does **not** primarily lack broad capability coverage. It lacks the next-order **runtime integration layer** now visible across the corpus:

- explicit governance operating models,
- bounded yet durable memory,
- normalized interruptible events,
- deterministic monitoring,
- stronger edit/review contracts,
- and governed skill lineage.

That is the real cross-batch gap map.
