# AGENT33 vs AGENTS33 — Product Split Analysis

**Status:** Draft / planning. Local only.
**Branch:** `claude/plan-analysis-tool-yAI8I`
**Date:** 2026-04-29
**Companion:** `docs/research/opensearch-agent-observability-analysis.md` (rev-2)

## 1. The proposal

Split the project into two products with their own brand, audience, repo,
roadmap, and license posture:

- **AGENT33** — current name, kept. A singular-focus autonomous-agent
  product. Personal-scale workspaces, skills, autonomous coding / research
  agents. Comparable to OpenClaw, Hermes, Claude Code, OpenHands. The user
  is one operator running one (or a small handful of) agents on their
  workstation.
- **AGENTS33** — new product, domain already owned. An orchestration and
  engineering platform for AI agents at enterprise scale. Audience is AI
  engineers and AI architects responsible for fleets — thousands of agents,
  hundreds of users, AI-enriched data-driven processes that need
  observability, evals, fine-tuning, governance, and dashboards.

This document is the strategic case for the split, the architectural
relationship between the two, and the open questions that have to be
answered before any restructure happens.

## 2. Why this resolves the rev-2 friction

The rev-2 OpenSearch plan kept hitting tension points because we were
trying to make one codebase serve both products. The split makes those
tensions disappear:

| Tension in rev-2 (single product) | Resolved by split (two products) |
|---|---|
| Replace `AgentRuntime` with LangGraph / ML Commons V2 / Claude Agent SDK? | **AGENT33** keeps its runtime — that's the product. **AGENTS33** doesn't have *a* runtime; it has a **control plane** that manages many runtimes (AGENT33, LangGraph, Claude Agent SDK, ML Commons V2, CrewAI). |
| Replace pgvector with k-NN? | **AGENT33** keeps pgvector for personal scale. **AGENTS33** uses OpenSearch k-NN for fleet scale. Different scales, different answers. |
| Path X / Y / Z (OpenSearch only / Langfuse+Dify only / compose)? | **AGENT33** doesn't need any of them — the existing in-process trace collector is right-sized. **AGENTS33** is the only consumer of the strategic fork; the question becomes tractable. |
| Multi-tenancy: per-tenant index vs shared with field-level filter? | **AGENT33** is single-tenant by design. **AGENTS33** is multi-tenant from day 1. |
| Resell / embed / commercial features? | **AGENT33** stays open and operator-owned. **AGENTS33** can be source-available + commercial-features. |
| Docker footprint of full observability stack? | **AGENT33** stays light. **AGENTS33** ships the heavy stack — that's its job. |

Each row was a forced compromise in rev-2. None of them are compromises
once the products are separate.

## 3. Audience and positioning

### AGENT33

- **User:** solo operator, developer, researcher, hobbyist.
- **Scale:** 1 user, 1–10 concurrent agent sessions, local box.
- **Value prop:** "an autonomous agent that learns my workspace and skills."
- **Comparables:** OpenClaw, Hermes, Claude Code, OpenHands, Continue,
  Cline, Aider.
- **Distribution:** open source (MIT or similar), pip install, docker run.
- **UX:** CLI + lightweight cockpit UI. Markdown-native config.
- **Lifecycle:** ship as a package; users self-update.

### AGENTS33

- **User:** AI engineer, AI architect, platform team, enterprise ops.
- **Scale:** 100s of users, 1000s of agents, multi-region.
- **Value prop:** "the management OS for an AI agent fleet — observability,
  evals, fine-tuning, governance, dashboards, marketplaces."
- **Comparables:** Langfuse + Dify + LangSmith + Datadog LLM, but
  composed as one product with stronger search/anomaly via OpenSearch.
- **Distribution:** source-available core + commercial enterprise features
  (SSO, fleet RBAC, audit, SLAs). Helm chart + cloud SaaS.
- **UX:** web app, embedded dashboards, role-based.
- **Lifecycle:** versioned releases; managed-upgrade story; tenant
  isolation.

The two products are not competitors. AGENTS33 *manages* fleets that include
AGENT33 instances (and other framework agents). AGENT33 emits the data
AGENTS33 consumes.

## 4. Architectural relationship — three options

### Option A — Fully separate repos, no shared code

- `github.com/mattmre/agent33` and `github.com/mattmre/agents33` evolve
  independently. Each owns its own primitives.
- *Pros:* maximum independence. Each team / contributor pool is clean.
- *Cons:* duplication of the agent-definitions schema, capability
  taxonomy, trace conventions, tool schema protocol. Drift is inevitable.

### Option B — Monorepo with two product roots

- One repo. `agent33/` and `agents33/` directories. Shared `core/`.
- *Pros:* shared substrate is enforced by build. One CI.
- *Cons:* mixes "small autonomous agent product" and "enterprise platform
  product" in one tree. Different release cadences fight each other.
  Unclear where contributors land.

### Option C — AGENTS33 consumes AGENT33 as a library (recommended)

- `agent33` becomes a published library / package
  (`pip install agent33`, `npm install @agent33/core`).
- `agents33` (separate repo) imports and extends it. AGENT33's primitives
  (agent definitions, capability taxonomy, trace conventions, tool schema,
  skill manifest, workflow YAML) are the contract surface.
- *Pros:* the relationship matches the product narrative. AGENT33 stays a
  product *and* becomes the SDK that AGENTS33 builds on. License
  separation is clean. Contributors pick the project that matches their
  interest.
- *Cons:* AGENT33 has to commit to a stable public API. Breaking changes
  cost more.

**Recommendation: Option C.** It mirrors the product story
("one agent → many agents") and makes the contract surface explicit.

## 5. Shared substrate (the contract surface, lives in AGENT33)

These primitives are versioned, documented, and stable in AGENT33. AGENTS33
treats them as contracts — it does not fork or reinvent them.

| Primitive | Today's location |
|---|---|
| Agent-definition JSON schema | `engine/agent-definitions/` + `agents/definition.py` |
| Capability taxonomy (P/I/V/R/X, 25 entries) | `engine/src/agent33/agents/capabilities.py` |
| Trace conventions (`gen_ai.*`, `tenant_id`, F-* failure taxonomy) | `engine/src/agent33/observability/trace_models.py`, `failure.py` |
| Tool schema protocol (`SchemaAwareTool`, `validated_execute`) | `engine/src/agent33/tools/registry.py` |
| Skill manifest format (SKILL.md w/ frontmatter) | `engine/src/agent33/skills/` |
| Workflow definition (DAG, YAML) | `core/workflows/` (Markdown-native) + `engine/src/agent33/workflows/definition.py` |
| Auth model (API key + JWT, tenant scoping) | `engine/src/agent33/security/` |
| OTel `gen_ai` span conventions | (would be added by Phase OS-1 in AGENT33 first) |

These are exactly the things rev-2 was trying to replace. Under the split,
they stay where they are. AGENT33 owns them. AGENTS33 reads them.

## 6. Diverging stacks

| Layer | AGENT33 | AGENTS33 |
|---|---|---|
| Agent runtime | Current `AgentRuntime` (kept). | **Control plane** that manages many runtimes — AGENT33, LangGraph, Claude Agent SDK, ML Commons V2, CrewAI, AutoGen. Pluggable adapter pattern. |
| Workflow engine | Current DAG executor (kept). | Above the runtime — orchestrates *across* agent fleets, not *inside* one. |
| Vector store | pgvector + BM25 (kept). | OpenSearch k-NN with 1-bit quantisation, scales to 100M+ docs. |
| Trace storage | In-memory + file-backed (kept for personal use). | OpenSearch Agent Traces + Langfuse for trace UX. |
| Dashboards | Lightweight cockpit (kept). | OpenSearch Dashboards Investigation + Langfuse + custom AGENTS33 shell. |
| Alerting | Current `AlertManager` (kept). | OpenSearch Alerting + anomaly detection. |
| Frontend | Current React cockpit (kept). | New web app, possibly Dify-derived for the workflow / agent-builder surfaces. |
| Auth | API key + JWT (kept). | Same primitives + SSO + fleet RBAC + audit. |

## 7. What moves where (in-flight roadmap items)

- **POST-1 / POST-2 (already merged):** stay in AGENT33. Foundation,
  SkillsBench. Personal-scale matters.
- **POST-3 Pack Ecosystem (queued):** splits. *Skill packs* and
  *agent-definition packs* land in AGENT33. *Fleet-deployment packs*
  (multi-agent compositions, dashboard packs, eval pack bundles) land in
  AGENTS33.
- **OpenSearch + Langfuse + Dify integration plan (rev-2):** moves
  entirely to AGENTS33. AGENT33 is unaffected by it.
- **Phase OS-0 decision spike:** runs in AGENTS33 from day 1. AGENT33
  stays out of it.
- **POST-4 onward:** to be triaged against the two products as they get
  defined.

## 8. License posture (open question)

| Product | Current implied | Proposal |
|---|---|---|
| AGENT33 | MIT-leaning | MIT or Apache 2.0. Stay simple. |
| AGENTS33 | n/a | Source-available core (SSPL or BSL or Elastic v2) + commercial enterprise features (SSO, fleet RBAC, audit, SLAs). Same model as Langfuse / Posthog / Sentry. |

This is the posture that lets us resell to clients without giving away the
enterprise edge.

## 9. Risks

1. **Contract-surface stability.** Option C only works if AGENT33 commits
   to a stable public API. Breaking changes hurt AGENTS33 directly.
   Mitigation: version the primitives, deprecate via at least one minor.
2. **Brand confusion.** AGENT33 vs AGENTS33 differs by one letter. Domain
   is owned, but operators will still mix them up. Mitigation: clear
   product-page copy and a "which one do I want?" decision tree.
3. **Engineering bandwidth.** Two products is more surface than one.
   Mitigation: AGENT33 is feature-complete-ish for its scope; AGENTS33
   gets the new investment.
4. **Looped agent on the other machine.** That agent is presumably driving
   AGENT33's roadmap. The split introduces a coordination question — does
   that agent know about the split, or does it keep landing single-product
   commits? Real risk if the split isn't communicated to it.
5. **Licence-fork risk.** If AGENTS33 adopts source-available, contributors
   from AGENT33 may not auto-port to AGENTS33. Plan for this.

## 10. Open questions (operator gate)

These need answers before any restructure work starts. None are decided
here.

**Structural:**
1. Repo structure: Option A (separate, no share), B (monorepo with
   `core/`), or C (library + platform — recommended)?
2. Where does the shared substrate physically live — in AGENT33's `core/`,
   in a third `agent33-core` repo, or vendored?
3. Polyglot? AGENTS33 control plane in Python (matches AGENT33), or
   Go / Rust for fleet performance?

**Productisation:**
4. License posture for AGENTS33 — MIT, Apache 2.0, source-available, or
   open-core?
5. Distribution: pip + docker for AGENT33; what for AGENTS33 (Helm? SaaS?
   AMI? both)?
6. Is `agents33.com` already pointing somewhere, or a fresh start?

**Scope:**
7. Does AGENTS33 launch managing AGENT33 only, or framework-agnostic
   (LangGraph, Claude Agent SDK, etc.) from day 1?
8. Path X / Y / Z for AGENTS33 (OpenSearch only / Langfuse + Dify /
   compose) — recommend Path Z, but it's now an AGENTS33 question.

**Sequencing:**
9. Do we ship AGENTS33 v0 with OpenSearch backbone first, or Langfuse +
   Dify first (faster)?
10. Does the looped agent on the other machine continue working on
    AGENT33 only, or does it also pick up AGENTS33 scaffolding?

## 11. Recommended sequencing (if the split is approved)

1. **Operator confirms the split** (this doc). Locks the product names,
   answers Q1 (repo structure) and Q4 (license).
2. **Stabilise the contract surface** in AGENT33 — version
   `agent-definitions/`, capability taxonomy, trace conventions, tool
   schema. Tag a `core-1.0` release.
3. **Create the AGENTS33 repo** (or directory, depending on Q1).
4. **Move the OpenSearch + Langfuse + Dify plan** there as its founding
   roadmap.
5. **Run Phase OS-0 (decision spike)** in AGENTS33. Pick Path X / Y / Z.
6. **AGENT33 continues its current roadmap unchanged.**

## 12. What stays local until the operator approves

This doc and the rev-2 OpenSearch doc (`opensearch-agent-observability-
analysis.md`). Neither has been pushed. Neither should be pushed until the
split is confirmed and the looped agent on the other machine has been
informed — otherwise we risk the looped agent stepping on the
restructure.

## 13. Sources informing this split

- The competitive landscape research in
  `docs/research/opensearch-agent-observability-analysis.md` §5.
- Langfuse / Posthog / Sentry as reference for the
  open-source-core + commercial-enterprise license model.
- Dify as reference for what an "AI platform product" looks like at scale.
- AGENT33's existing CLAUDE.md framing of `core/` (Markdown-native specs)
  vs `engine/` (Python runtime) — the split already exists at the
  product-level boundary; this doc just names what that boundary is for.
