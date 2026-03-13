# OpenClaw Feature Parity Research

Date: 2026-03-09

Scope: Review OpenClaw changes from January 9, 2026 through March 9, 2026, identify major new features, fixes, and implementation approaches, and map them against AGENT-33.

Primary sources:

- [OpenClaw README](https://github.com/openclaw/openclaw)
- [OpenClaw changelog](https://github.com/openclaw/openclaw/blob/main/CHANGELOG.md)
- [OpenClaw release 2026.1.11](https://github.com/openclaw/openclaw/releases/tag/v2026.1.11)
- [OpenClaw release 2026.2.22](https://github.com/openclaw/openclaw/releases/tag/v2026.2.22)
- [OpenClaw release 2026.2.24](https://github.com/openclaw/openclaw/releases/tag/v2026.2.24)
- [OpenClaw release 2026.2.26](https://github.com/openclaw/openclaw/releases/tag/v2026.2.26)
- [OpenClaw release 2026.3.8](https://github.com/openclaw/openclaw/releases/tag/v2026.3.8)

## Executive Summary

OpenClaw added meaningful capability in the last two months, but most of the high-value changes cluster around a few themes rather than dozens of unrelated net-new systems:

1. Plugins became a first-class product surface.
2. Config modularization and security hardening deepened quickly.
3. Web research tooling became more provider-aware and grounding-oriented.
4. Operator UX shifted toward runtime-discovered metadata instead of static frontend assumptions.
5. Backup, restore, and provenance became explicit operator-facing flows.
6. Agent editing and memory durability got safer and more ergonomic.

For AGENT-33, the highest-value parity targets are not OpenClaw's consumer-product surfaces (mobile, channels, telephony). They are the reusable infrastructure patterns behind them:

- runtime tool catalog surfacing
- safe patch-based file mutation
- archive-level backup and verification
- visible provenance receipts
- install/update/distribution UX for plugins and packs
- richer web-grounding modes with explicit trust metadata

AGENT-33 already exceeds OpenClaw in workflow orchestration, multi-tenancy, review automation, evaluation, autonomy budgets, and observability depth. The parity work is therefore selective, not wholesale.

## What OpenClaw Added

### 1. First-class plugin platform

OpenClaw's `2026.1.11` release is the turning point. Plugins moved from extension-like behavior to a clear product contract:

- loader for tools, RPC, CLI, services, skills
- `openclaw plugins install|list|info|enable|disable|doctor`
- manifest-declared `configSchema` and `uiHints`
- install sources from local path, archives, npm, or link mode
- flagship example plugin: `voice-call`

Implementation pattern:

- plugin config validation is manifest/schema-driven, not coupled to executing plugin code
- install provenance is tracked and surfaced in docs/CLI
- plugin-provided skills are part of the extension contract, not an afterthought

Why it matters:

- this is not just "support plugins"
- it is "make plugins operable"

### 2. Modular config with aggressive hardening

OpenClaw added top-level `$include` config support in `2026.1.11`, then spent February hardening it:

- constrain includes to trusted in-root files
- validate containment against traversal/symlink/hardlink tricks
- apply file-size limits
- preserve secret-shaped config values correctly through writes

Implementation pattern:

- ship usability first
- then harden boundary behavior quickly with explicit fail-closed checks

This is a strong example of how OpenClaw rolls out user-facing operator features without leaving them permanently under-protected.

### 3. Web research modes, not just web search

OpenClaw's web tooling evolved materially during the window:

- `web_search` / `web_fetch` established as first-class tools
- Brave freshness, country, and language support
- grounded Gemini provider support
- proxy-aware SSRF-guarded provider path
- Brave `llm-context` mode in `2026.3.8`

The important design choice is the mode split:

- classic search mode returns titles/URLs/snippets
- `llm-context` mode returns extracted grounding chunks and source metadata

It also rejects unsupported filter/mode combinations explicitly instead of silently degrading behavior.

### 4. Runtime-driven operator UI

In `2026.2.22`, OpenClaw's Control UI Tools panel became data-driven from runtime `tools.catalog`, with provenance labels:

- `core`
- `plugin:<id>`
- optional-marker when relevant

The frontend keeps a static fallback, but the runtime becomes the source of truth. This is a high-leverage pattern because it reduces drift between actual tool availability and what operators think exists.

### 5. Backup and verification as operator flows

In `2026.3.8`, OpenClaw added:

- `openclaw backup create`
- `openclaw backup verify`

The notable part is the verification design:

- archive manifest with schema version, runtime version, platform, paths, asset inventory, skipped entries
- archive-root normalization and containment checks
- payload coverage checks against manifest assets
- config-only and no-workspace modes
- destructive flows recommend backup first

This is much stronger than "export JSON" or "tar some files."

### 6. Provenance that is both machine-readable and human-visible

In `2026.3.8`, OpenClaw added ACP provenance modes:

- `off`
- `meta`
- `meta+receipt`

The key idea is visible receipt injection. Provenance is not only stored in metadata; it can also be rendered into a receipt block carrying source session and runtime context. That improves debuggability and operator trust when requests cross boundaries.

### 7. Safer agent-side patching

OpenClaw added an experimental `apply_patch` tool in `2026.1.11` and then hardened it heavily through February:

- opt-in gate
- model allowlisting
- workspace-only containment by default
- symlink/hardlink/path-alias defenses

This is a better mutation primitive than broad file overwrite for coding tasks.

### 8. Memory durability before compaction

OpenClaw added pre-compaction memory flush plus reserved headroom in `2026.1.11`, so durable writes can land before compaction runs. That is a targeted operational improvement rather than a headline feature, but it reflects a strong runtime instinct: preserve durable memory before summarization pressure causes loss.

## Important Fix Trends

The last two months also show strong ongoing investment in:

- channel and DM routing correctness
- restart/update reliability
- browser relay/CDP edge cases
- config snapshot integrity after writes
- plugin discovery precedence and plugin onboarding behavior
- SSRF and path-boundary hardening

This matters because OpenClaw is not only shipping features; it is actively reducing operational footguns around those features.

## AGENT-33 Comparison

### AGENT-33 is already stronger in:

- multi-agent DAG workflows
- governance and autonomy enforcement
- review automation and signoff state
- evaluation gates and regression detection
- observability breadth (traces, metrics, lineage, replay)
- multi-tenant API/service posture

### AGENT-33 already has partial overlap for:

- plugin SDK and registry APIs
- skill packs and provenance concepts
- tool registry and governance
- web search and browser automation
- backup/restore primitives
- provenance and lineage

### AGENT-33 still has real parity gaps

#### Gap 1. No runtime tool catalog surface equivalent to OpenClaw's `tools.catalog`

AGENT-33 has a real `ToolRegistry`, but the operator/UI surface is still registry-centric in backend code and incomplete in operator UX. OpenClaw's runtime-driven tool panel is ahead in surfacing actual tool availability with provenance labeling.

AGENT-33 evidence:

- `engine/src/agent33/tools/registry.py`
- `engine/src/agent33/tools/registry_entry.py`
- `docs/functionality-and-workflows.md`

Recommendation:

- add a `GET /v1/tools/catalog` or equivalent runtime endpoint
- include grouped tools, effective availability, provenance, optionality, and policy status
- wire frontend surfaces to that endpoint instead of maintaining static assumptions

Priority: P0

#### Gap 2. Backup/restore exists only as partial subsystem backup, not a holistic archive workflow

AGENT-33 already has learning-state backup and restore endpoints, but that is not comparable to OpenClaw's operator-facing archive creation and verification surface.

AGENT-33 evidence:

- `engine/src/agent33/api/routes/improvements.py`
- `docs/research/session55-phase31-production-tuning.md`
- `docs/next-session.md` still lists Phase 31 production-scale backup/restore validation as unfinished

Recommendation:

- introduce archive-level backup/verify for operator-relevant state
- include config, plugin/pack metadata, workflow/review/eval/autonomy/improvement state as appropriate
- use a manifest + payload verification design similar to OpenClaw's

Priority: P0

#### Gap 3. No human-visible provenance receipt injection for cross-boundary requests

AGENT-33 has lineage and pack/tool provenance, but it does not appear to expose a visible ingress receipt comparable to OpenClaw's ACP `meta+receipt` mode.

AGENT-33 evidence:

- `engine/src/agent33/observability/lineage.py`
- `engine/src/agent33/packs/provenance.py`
- `engine/src/agent33/tools/registry_entry.py`

Recommendation:

- add optional provenance receipt blocks for:
  - cross-agent delegation
  - MCP ingress
  - workflow-triggered agent runs
  - external webhook or automation-originated requests
- keep metadata form machine-readable and optionally inject a visible operator/debug receipt

Priority: P1

#### Gap 4. No safe `apply_patch`-style mutation tool in the runtime tool surface

AGENT-33 has tool governance and built-in file/shell/browser tools, but not a dedicated structured patch primitive comparable to OpenClaw's.

Recommendation:

- add a patch-based mutation tool with:
  - strict grammar
  - workspace-root containment
  - autonomy/tool-governance gate
  - model allowlist
  - trace capture of changed files

Priority: P0

#### Gap 5. Web search is present, but mode-aware grounding is weaker

AGENT-33's `search.py` is SearXNG-backed and returns formatted search results. That is useful, but it does not provide the same provider-aware mode split OpenClaw now has.

AGENT-33 evidence:

- `engine/src/agent33/tools/builtin/search.py`
- `engine/src/agent33/tools/builtin/web_fetch.py`

Recommendation:

- keep SearXNG as a baseline provider
- add optional grounding-oriented modes that return extracted content with source metadata
- fail explicitly on unsupported combinations rather than silently ignoring parameters
- label externally sourced grounding as untrusted in tool output metadata

Priority: P1

#### Gap 6. Plugin and pack infrastructure exists, but install/distribution UX is still behind

AGENT-33 already has:

- plugin routes
- plugin base/context/capability model
- pack registry
- provenance/trust primitives

But the repo's own docs still mark marketplace/distribution as incomplete.

AGENT-33 evidence:

- `engine/src/agent33/api/routes/plugins.py`
- `engine/src/agent33/packs/registry.py`
- `docs/research/session57-ops-hardening-implementation-brief.md`
- `docs/next-session.md`

Recommendation:

- focus on install/update/discover/doctor flows and operator-grade packaging UX
- complete pack marketplace/distribution work with stronger signing than current HMAC-only approach
- surface plugin/pack provenance in operator UI

Priority: P1

#### Gap 7. Memory compaction durability is worth adapting only if AGENT-33's summarization pressure grows

This is not an urgent parity item. AGENT-33 already has progressive recall, observation capture, and summarization subsystems. But if automatic compaction or summarization becomes more aggressive, OpenClaw's pre-compaction flush/headroom pattern is worth adopting.

Priority: P2

## Not Worth Chasing as Direct Parity

These are real OpenClaw features, but they are not immediate AGENT-33 parity priorities:

- remote gateway token onboarding
- top-level talk silence timeout
- voice-call plugin
- consumer messaging channel expansion
- macOS/iOS/Android app-specific UX

Those are product-layer choices tied to OpenClaw's personal-assistant positioning. AGENT-33 should learn from the infrastructure around them, not clone the surfaces blindly.

## Recommended AGENT-33 Follow-up Order

### P0

1. Runtime tool catalog endpoint + frontend provenance labels.
2. Structured patch-mutation tool with strict containment and governance.
3. Archive-level backup create/verify flow for operator state.

### P1

4. Visible provenance receipts for delegated and external ingress.
5. Mode-aware web grounding output with explicit trust metadata.
6. Plugin/pack install-update-doctor-distribution UX.

### P2

7. Config modularization if operator config surface becomes large enough to justify includes.
8. Memory pre-compaction flush/headroom if summarization pressure grows.

## Bottom Line

OpenClaw's strongest recent work is not "more features" in the abstract. It is turning previously implicit runtime capabilities into explicit operator products:

- plugins that can actually be installed and diagnosed
- tools that the UI can discover from runtime state
- web research modes with well-defined semantics
- backups that can be verified
- provenance that humans can inspect

That is the part AGENT-33 should match.

AGENT-33 does not need to imitate OpenClaw's consumer-assistant surface area. It does need to absorb the operator-grade packaging, runtime surfacing, and safety patterns that OpenClaw has been tightening over the last two months.
