# OpenClaw Six-Month Feature Parity Backlog

Date: 2026-03-09
Target repo: [openclaw/openclaw](https://github.com/openclaw/openclaw)
Comparison repo: AGENT-33

## Scope

This scan covers the user-requested six-month window from September 9, 2025 through March 9, 2026.

Important reality check:

- The `openclaw/openclaw` repository was created on November 24, 2025.
- The public release stream visible in the current repo starts on January 5, 2026 (`v2026.1.5`).
- There is no public September to December 2025 release history in the current repository or current changelog snapshot.

So the six-month review is honest but asymmetric:

- repo existence window: November 24, 2025 through March 9, 2026
- public release-backed implementation window: January 5, 2026 through March 9, 2026

The release notes were used as an index, but the implementation source of truth for recommendations is the latest OpenClaw source tree on `main`, not old point-in-time code.

## Primary Sources

OpenClaw latest-source validation:

- [OpenClaw README](https://github.com/openclaw/openclaw/blob/main/README.md)
- [OpenClaw CHANGELOG](https://github.com/openclaw/openclaw/blob/main/CHANGELOG.md)
- [OpenClaw appcast](https://github.com/openclaw/openclaw/blob/main/appcast.xml)
- [OpenClaw tools docs](https://github.com/openclaw/openclaw/blob/main/docs/tools/index.md)
- [OpenClaw plugin docs](https://github.com/openclaw/openclaw/blob/main/docs/tools/plugin.md)
- [OpenClaw web tools docs](https://github.com/openclaw/openclaw/blob/main/docs/tools/web.md)
- [OpenClaw Control UI docs](https://github.com/openclaw/openclaw/blob/main/docs/web/control-ui.md)
- [OpenClaw WebChat docs](https://github.com/openclaw/openclaw/blob/main/docs/web/webchat.md)
- [OpenClaw tool catalog source](https://github.com/openclaw/openclaw/blob/main/src/agents/tool-catalog.ts)
- [OpenClaw apply_patch source](https://github.com/openclaw/openclaw/blob/main/src/agents/apply-patch.ts)
- [OpenClaw backup create source](https://github.com/openclaw/openclaw/blob/main/src/commands/backup.ts)
- [OpenClaw backup verify source](https://github.com/openclaw/openclaw/blob/main/src/commands/backup-verify.ts)
- [OpenClaw ACP provenance source](https://github.com/openclaw/openclaw/blob/main/src/acp/translator.ts)

AGENT-33 current-baseline evidence:

- [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md)
- [frontend/src/App.tsx](/D:/GITHUB/AGENT33/frontend/src/App.tsx)
- [engine/src/agent33/api/routes/plugins.py](/D:/GITHUB/AGENT33/engine/src/agent33/api/routes/plugins.py)
- [engine/src/agent33/packs/registry.py](/D:/GITHUB/AGENT33/engine/src/agent33/packs/registry.py)
- [engine/src/agent33/packs/provenance.py](/D:/GITHUB/AGENT33/engine/src/agent33/packs/provenance.py)
- [engine/src/agent33/tools/registry.py](/D:/GITHUB/AGENT33/engine/src/agent33/tools/registry.py)
- [engine/src/agent33/tools/builtin/search.py](/D:/GITHUB/AGENT33/engine/src/agent33/tools/builtin/search.py)
- [engine/src/agent33/api/routes/improvements.py](/D:/GITHUB/AGENT33/engine/src/agent33/api/routes/improvements.py)

## Executive Read

OpenClaw's strongest recent work is not "more channels." The highest-value learnings for AGENT-33 are the operator-facing patterns around:

- runtime-discovered tool surfaces
- safe structured file mutation
- plugin install and health lifecycle
- archive-grade backup and verification
- visible provenance receipts
- provider-aware web grounding
- configuration, onboarding, and doctor ergonomics
- session and automation usability

AGENT-33 is already stronger than OpenClaw in governance, review automation, release management, evaluation, autonomy controls, and enterprise-style lifecycle structure. The repo is weaker in the layer that operators feel every day:

- discoverability
- information architecture
- runtime affordances
- install/update/doctor flows
- backup confidence
- plugin and pack UX
- safe-but-usable mutating tools
- lightweight browser-facing control surfaces

## What To Copy vs What Not To Copy

Copy or adapt:

- runtime catalog pattern
- schema-driven config and plugin surfaces
- backup manifest plus verify model
- explicit safety gates on mutating tools
- provenance receipts
- provider-specific web-grounding modes
- plugin install/update/doctor flow
- operator UX fallback behavior when runtime metadata is unavailable

Do not copy directly:

- channel sprawl as a product strategy
- mobile and telephony features that do not map to AGENT-33 goals
- personal-assistant assumptions in session and auth flows
- single-user UX shortcuts that weaken tenant-aware enterprise boundaries

## Release Pattern Summary

OpenClaw shipped extremely rapidly between January 5, 2026 and March 9, 2026. The changelog contains well over two thousand individual `Changes`, `Fixes`, and `Breaking` bullets across that window. The durable themes that survived into current `main` are:

1. Pluginization of optional capabilities and channels
2. Runtime tool policy, profiles, and runtime tool catalog surfacing
3. Safe `apply_patch`-style editing with filesystem boundary hardening
4. Backup archive creation and verification
5. Richer web search and fetch with multiple providers and grounding modes
6. Control UI and WebChat backed directly by runtime APIs
7. Context engine plugin slots and compaction lifecycle hooks
8. Explicit provenance propagation and visible receipts
9. Stronger onboarding, doctor, config, and update ergonomics
10. High operational attention to restart, auth, browser relay, and platform edge cases

## AGENT-33 Gap Map

High-confidence gaps confirmed locally:

- No OpenClaw-equivalent runtime `tools.catalog` surface was found in AGENT-33.
- No safe `apply_patch` runtime tool was found in AGENT-33.
- AGENT-33 backup/restore is currently subsystem-specific for improvement learning state, not archive-level platform backup.
- Plugin APIs exist, but install/update/doctor/distribution ergonomics are materially behind OpenClaw.
- Packs have provenance concepts, but marketplace sources are explicitly not yet supported.
- Web search is currently SearXNG-centric, not provider-aware or grounding-mode-aware.
- The frontend shell is still a monolithic app-level navigation surface, not a discoverable operator information architecture.
- Several UI refinements in `docs/next-session.md` are already known pending work, which aligns with the parity gaps surfaced here.

## Priority Waves

Wave 0, immediate parity foundation:

- runtime tool catalog
- structured patch tool
- archive backup and verify
- plugin and pack lifecycle UX
- web research provider abstraction
- UI information architecture reset

Wave 1, operator trust and usability:

- provenance receipts
- onboarding and config schema UX
- session and subagent usability
- cron and operations parity
- backup restore workflows

Wave 2, durability and polish:

- context engine slotting
- stronger doctor and update flows
- frontend test coverage and accessibility
- deployment and restart hardening

## 222-Item Backlog

### Category A: Operator UI and Information Architecture

Evidence:

- OpenClaw current sources: README, `docs/web/control-ui.md`, `docs/web/webchat.md`
- AGENT-33 current sources: [frontend/src/App.tsx](/D:/GITHUB/AGENT33/frontend/src/App.tsx), [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md)

1. `OC-UI-001 | P0 | Parity` Replace the monolithic tab shell with route-based navigation that separates operator mode from end-user interaction mode.
2. `OC-UI-002 | P0 | Parity` Add a dedicated operator home page that surfaces current system health, active runs, pending approvals, and recent failures.
3. `OC-UI-003 | P0 | Parity` Add task-oriented navigation labels instead of domain-taxonomy-first navigation.
4. `OC-UI-004 | P0 | Parity` Add a persistent "what can I do next" panel for onboarding and idle states.
5. `OC-UI-005 | P1 | Parity` Add workspace-aware landing behavior so the current workspace or tenant opens to its most relevant view.
6. `OC-UI-006 | P1 | Parity` Add dedicated pages for plugins, packs, tools, backups, sessions, and automations instead of burying them under advanced settings.
7. `OC-UI-007 | P1 | Parity` Add operator-visible badges for runtime availability, degraded modes, and missing integrations.
8. `OC-UI-008 | P1 | Uplift` Add a command palette for fast navigation, actions, and entity lookup.
9. `OC-UI-009 | P1 | Parity` Add a filterable notifications center for warnings, approvals, migrations, and runtime repairs.
10. `OC-UI-010 | P1 | Parity` Add contextual docs links directly in each settings and operations surface.
11. `OC-UI-011 | P1 | Uplift` Add a universal search result view that spans agents, workflows, plugins, packs, traces, and docs.
12. `OC-UI-012 | P1 | Parity` Add dedicated empty states with recovery actions for every operational surface.
13. `OC-UI-013 | P1 | Uplift` Add role-specific landing presets for operator, reviewer, researcher, and developer.
14. `OC-UI-014 | P1 | Parity` Add a focused current-run drawer that follows the operator across pages.
15. `OC-UI-015 | P2 | Parity` Add a recent-activity rail scoped by tenant and workspace.
16. `OC-UI-016 | P2 | Uplift` Add a persistent feedback and "report issue" action that attaches runtime context automatically.
17. `OC-UI-017 | P2 | Parity` Add page-level "why is this unavailable?" explainers when features are gated by config or auth.
18. `OC-UI-018 | P2 | Uplift` Add keyboard shortcut discovery and a first-run operator tour.

### Category B: Runtime Tool Catalog and Discoverability

Evidence:

- OpenClaw current sources: `src/agents/tool-catalog.ts`, `docs/tools/index.md`, `docs/web/webchat.md`
- AGENT-33 current sources: [engine/src/agent33/tools/registry.py](/D:/GITHUB/AGENT33/engine/src/agent33/tools/registry.py), [frontend/src/App.tsx](/D:/GITHUB/AGENT33/frontend/src/App.tsx)

19. `OC-TOOL-001 | P0 | Parity` Add a runtime tool catalog endpoint that returns grouped tool metadata rather than relying on frontend assumptions.
20. `OC-TOOL-002 | P0 | Parity` Group tools into first-class sections such as files, runtime, web, sessions, automation, messaging, media, and UI.
21. `OC-TOOL-003 | P0 | Parity` Expose tool provenance labels like `core`, `plugin:<id>`, and `pack:<id>` in the catalog.
22. `OC-TOOL-004 | P0 | Parity` Expose effective tool availability per agent, not just global registry presence.
23. `OC-TOOL-005 | P1 | Parity` Add tool profiles such as minimal, coding, messaging, and full.
24. `OC-TOOL-006 | P1 | Parity` Add provider-specific tool restriction metadata to the catalog and UI.
25. `OC-TOOL-007 | P1 | Parity` Add a tool schema lookup surface for targeted parameter introspection.
26. `OC-TOOL-008 | P1 | Parity` Add live refresh of runtime catalog data when plugins or packs change.
27. `OC-TOOL-009 | P1 | Uplift` Add search and filtering within the tool catalog.
28. `OC-TOOL-010 | P1 | Parity` Show unsupported and disabled reasons for each tool.
29. `OC-TOOL-011 | P1 | Uplift` Add recent tool usage statistics per agent and per tenant.
30. `OC-TOOL-012 | P1 | Parity` Add static fallback catalogs for UI resilience when runtime introspection fails.
31. `OC-TOOL-013 | P2 | Uplift` Add side-by-side comparison of tool access across agents.
32. `OC-TOOL-014 | P2 | Parity` Expose sandbox, gateway, or node execution context in the catalog.
33. `OC-TOOL-015 | P2 | Uplift` Add direct links from tools to examples, approval policy, and docs.
34. `OC-TOOL-016 | P2 | Uplift` Add validation that the prompt-disclosed tool set and the runtime schema set remain aligned.

### Category C: Plugin Lifecycle and Extension Platform

Evidence:

- OpenClaw current sources: `docs/tools/plugin.md`
- AGENT-33 current sources: [engine/src/agent33/api/routes/plugins.py](/D:/GITHUB/AGENT33/engine/src/agent33/api/routes/plugins.py), [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md)

35. `OC-PLUG-001 | P0 | Parity` Add plugin install from local path in AGENT-33 operator surfaces.
36. `OC-PLUG-002 | P0 | Parity` Add plugin install from archive artifacts such as `.zip` or `.tgz`.
37. `OC-PLUG-003 | P0 | Parity` Add plugin install from registry package specs.
38. `OC-PLUG-004 | P0 | Parity` Add exact-version and dist-tag pinning for plugin installs.
39. `OC-PLUG-005 | P0 | Parity` Add prerelease opt-in guardrails instead of silently taking prereleases.
40. `OC-PLUG-006 | P0 | Parity` Add plugin update for one plugin and bulk update flows.
41. `OC-PLUG-007 | P1 | Parity` Add plugin link mode for local development.
42. `OC-PLUG-008 | P1 | Parity` Persist plugin config updates instead of treating them as in-memory placeholders.
43. `OC-PLUG-009 | P1 | Parity` Add plugin doctor output with actionable remediation.
44. `OC-PLUG-010 | P1 | Parity` Add plugin discovery cache invalidation and status refresh flows.
45. `OC-PLUG-011 | P1 | Parity` Record plugin install provenance including source, version, and integrity.
46. `OC-PLUG-012 | P1 | Parity` Add plugin allowlist and denylist policy surfaces.
47. `OC-PLUG-013 | P1 | Parity` Show plugin permission grants and denials in the UI.
48. `OC-PLUG-014 | P1 | Parity` Add plugin config schema plus `uiHints`-style UI metadata.
49. `OC-PLUG-015 | P1 | Parity` Add plugin health checks and last-failure reporting.
50. `OC-PLUG-016 | P2 | Parity` Add plugin-exposed route and command inventory pages.
51. `OC-PLUG-017 | P2 | Uplift` Add plugin lifecycle events for install, enable, disable, update, and rollback.
52. `OC-PLUG-018 | P2 | Uplift` Add hot-reload diagnostics and safe-reload fallback behavior.

### Category D: Packs, Marketplace, and Distribution

Evidence:

- OpenClaw current sources: `docs/tools/plugin.md`, README skill registry references
- AGENT-33 current sources: [engine/src/agent33/packs/registry.py](/D:/GITHUB/AGENT33/engine/src/agent33/packs/registry.py), [engine/src/agent33/packs/provenance.py](/D:/GITHUB/AGENT33/engine/src/agent33/packs/provenance.py), [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md)

53. `OC-PACK-001 | P0 | Parity` Add remote marketplace sources for packs instead of local-only install.
54. `OC-PACK-002 | P0 | Parity` Add marketplace index fetch and caching.
55. `OC-PACK-003 | P0 | Parity` Add pack install by name and version from trusted registries.
56. `OC-PACK-004 | P0 | Parity` Add pack version pinning and lock recording.
57. `OC-PACK-005 | P1 | Parity` Add pack upgrade and downgrade commands plus UI.
58. `OC-PACK-006 | P1 | Parity` Add pack dependency graph inspection before install or remove.
59. `OC-PACK-007 | P1 | Parity` Add pack trust policy management in the operator UI.
60. `OC-PACK-008 | P1 | Parity` Add checksum verification visibility on install.
61. `OC-PACK-009 | P1 | Parity` Add signature verification workflows and signer policy configuration.
62. `OC-PACK-010 | P1 | Parity` Add provenance receipts for pack source and signer.
63. `OC-PACK-011 | P1 | Parity` Add tenant enablement and disablement matrix views.
64. `OC-PACK-012 | P1 | Parity` Add conflict detection with clear resolution guidance when skills collide.
65. `OC-PACK-013 | P1 | Uplift` Add pack preview pages with README, manifest, and contribution inventory before install.
66. `OC-PACK-014 | P2 | Uplift` Add rollback to prior pack revision with preserved tenant enablement.
67. `OC-PACK-015 | P2 | Parity` Add pack health status and post-install smoke checks.
68. `OC-PACK-016 | P2 | Uplift` Add per-pack audit trails and change history.

### Category E: Safe Workspace Mutation and Execution Governance

Evidence:

- OpenClaw current sources: `src/agents/apply-patch.ts`, `docs/tools/apply-patch.md`, `docs/tools/index.md`
- AGENT-33 current sources: [engine/src/agent33/tools/registry.py](/D:/GITHUB/AGENT33/engine/src/agent33/tools/registry.py)

69. `OC-MUTATE-001 | P0 | Parity` Add a first-class runtime `apply_patch` tool to AGENT-33.
70. `OC-MUTATE-002 | P0 | Parity` Gate `apply_patch` behind explicit config enablement.
71. `OC-MUTATE-003 | P0 | Parity` Restrict `apply_patch` to allowlisted models by default.
72. `OC-MUTATE-004 | P0 | Parity` Make workspace-only containment the default behavior.
73. `OC-MUTATE-005 | P0 | Parity` Require explicit operator opt-in for out-of-workspace mutation.
74. `OC-MUTATE-006 | P0 | Parity` Add symlink, hardlink, traversal, and alias escape defenses for patch paths.
75. `OC-MUTATE-007 | P1 | Parity` Add patch dry-run preview before execution.
76. `OC-MUTATE-008 | P1 | Parity` Render patch diffs in the frontend.
77. `OC-MUTATE-009 | P1 | Parity` Route mutating patch execution through existing AGENT-33 approval and governance controls.
78. `OC-MUTATE-010 | P1 | Parity` Persist an audit log for every patch application.
79. `OC-MUTATE-011 | P1 | Parity` Add grouped policy shorthands for file, runtime, web, session, and automation tools.
80. `OC-MUTATE-012 | P1 | Parity` Add a process manager UI for background command sessions.
81. `OC-MUTATE-013 | P1 | Parity` Add live log tailing, write, kill, clear, and cleanup for background processes.
82. `OC-MUTATE-014 | P1 | Uplift` Add loop-detection guardrails for repetitive tool invocations.
83. `OC-MUTATE-015 | P2 | Uplift` Add "explain why this command was denied" feedback tied to policy rules.
84. `OC-MUTATE-016 | P2 | Uplift` Add policy simulation to preview what an agent may mutate before execution.

### Category F: Web Research, Grounding, and Source Trust

Evidence:

- OpenClaw current sources: `docs/tools/web.md`, `CHANGELOG.md`
- AGENT-33 current sources: [engine/src/agent33/tools/builtin/search.py](/D:/GITHUB/AGENT33/engine/src/agent33/tools/builtin/search.py)

85. `OC-WEB-001 | P0 | Parity` Replace the single-provider search posture with a provider abstraction for search and grounding.
86. `OC-WEB-002 | P0 | Parity` Add provider selection during onboarding and in settings.
87. `OC-WEB-003 | P0 | Parity` Add support for language, region, and freshness filters.
88. `OC-WEB-004 | P0 | Parity` Add explicit provider capability matrices instead of silent degradation.
89. `OC-WEB-005 | P0 | Parity` Support both search-snippet and `llm-context`-style grounding modes.
90. `OC-WEB-006 | P1 | Parity` Return structured search payloads with source metadata instead of plain formatted strings only.
91. `OC-WEB-007 | P1 | Parity` Mark web-derived content as untrusted in tool and UI outputs.
92. `OC-WEB-008 | P1 | Parity` Add `web_fetch` extract modes for markdown and text.
93. `OC-WEB-009 | P1 | Parity` Add configurable content-size caps and truncation messaging.
94. `OC-WEB-010 | P1 | Parity` Add cache hit and freshness indicators for repeated searches and fetches.
95. `OC-WEB-011 | P1 | Parity` Surface provider auth status and setup errors in the UI.
96. `OC-WEB-012 | P1 | Parity` Add direct citation cards in chat and research views.
97. `OC-WEB-013 | P1 | Parity` Reject unsupported filter combinations explicitly.
98. `OC-WEB-014 | P1 | Uplift` Add per-provider cost, quota, and latency telemetry.
99. `OC-WEB-015 | P2 | Parity` Add optional anti-bot or JS-heavy page fallback strategies.
100. `OC-WEB-016 | P2 | Uplift` Add source-trust scoring and filtering for research workflows.

### Category G: Backup, Restore, and Recovery

Evidence:

- OpenClaw current sources: `src/commands/backup.ts`, `src/commands/backup-verify.ts`
- AGENT-33 current sources: [engine/src/agent33/api/routes/improvements.py](/D:/GITHUB/AGENT33/engine/src/agent33/api/routes/improvements.py), [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md)

101. `OC-BACKUP-001 | P0 | Parity` Add platform-level backup create flows covering runtime state beyond improvement learning signals.
102. `OC-BACKUP-002 | P0 | Parity` Add platform-level backup verify flows.
103. `OC-BACKUP-003 | P0 | Parity` Add config-only backup mode.
104. `OC-BACKUP-004 | P0 | Parity` Add no-workspace backup mode.
105. `OC-BACKUP-005 | P0 | Parity` Define a versioned backup manifest schema.
106. `OC-BACKUP-006 | P0 | Parity` Record runtime version, platform, and archive root in the manifest.
107. `OC-BACKUP-007 | P1 | Parity` Validate archive-root containment during verify.
108. `OC-BACKUP-008 | P1 | Parity` Validate payload coverage against manifest-declared assets.
109. `OC-BACKUP-009 | P1 | Parity` Detect duplicate normalized archive entries during verify.
110. `OC-BACKUP-010 | P1 | Parity` Add backup-first recommendations before destructive operations.
111. `OC-BACKUP-011 | P1 | Parity` Improve archive naming for lexical date sorting.
112. `OC-BACKUP-012 | P1 | Parity` Prevent backup outputs from being written inside source roots.
113. `OC-BACKUP-013 | P1 | Parity` Publish backup archives atomically through temp files.
114. `OC-BACKUP-014 | P1 | Uplift` Add restore planning previews before restore execution.
115. `OC-BACKUP-015 | P2 | Uplift` Add scheduled backups and retention policies.
116. `OC-BACKUP-016 | P2 | Uplift` Add a backup inventory browser and restore drill history.

### Category H: Sessions, Subagents, and Collaboration UX

Evidence:

- OpenClaw current sources: README, `docs/tools/index.md`, `docs/web/webchat.md`, `src/acp/translator.ts`
- AGENT-33 current sources: [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md), [frontend/src/App.tsx](/D:/GITHUB/AGENT33/frontend/src/App.tsx)

117. `OC-SESSION-001 | P0 | Parity` Add a dedicated sessions catalog view with status, type, and recent activity.
118. `OC-SESSION-002 | P0 | Parity` Add transcript history browsing for active and archived sessions.
119. `OC-SESSION-003 | P0 | Parity` Add a UI for agent-to-agent send and announce patterns.
120. `OC-SESSION-004 | P0 | Parity` Add subagent spawn forms with reusable templates.
121. `OC-SESSION-005 | P1 | Parity` Expose one-shot versus persistent subagent modes explicitly.
122. `OC-SESSION-006 | P1 | Parity` Add announce and reply-back policy controls for delegated runs.
123. `OC-SESSION-007 | P1 | Parity` Add inline file attachments for delegated tasks where safe.
124. `OC-SESSION-008 | P1 | Parity` Add session-visibility policy configuration for session tools.
125. `OC-SESSION-009 | P1 | Parity` Add a spawned-session tree view to show lineage.
126. `OC-SESSION-010 | P1 | Parity` Add current active-run indicators and per-session cancellation controls.
127. `OC-SESSION-011 | P1 | Uplift` Add archive and cleanup workflows for stale sessions.
128. `OC-SESSION-012 | P1 | Parity` Add per-session model, effort, and verbosity overrides in the frontend.
129. `OC-SESSION-013 | P2 | Uplift` Infer the most likely agent or workspace target from the current operating context.
130. `OC-SESSION-014 | P2 | Parity` Add explicit receipts when a session is spawned or addressed by an external source.

### Category I: Context Engine, Memory, and Compaction Durability

Evidence:

- OpenClaw current sources: `CHANGELOG.md`, `docs/tools/plugin.md`
- AGENT-33 current sources: [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md)

131. `OC-CONTEXT-001 | P1 | Parity` Add a pluggable context-engine slot in AGENT-33 runtime configuration.
132. `OC-CONTEXT-002 | P1 | Parity` Add a context-engine registry UI showing active engine and alternatives.
133. `OC-CONTEXT-003 | P1 | Parity` Add lifecycle hooks for bootstrap, ingest, assemble, compact, and post-turn.
134. `OC-CONTEXT-004 | P1 | Parity` Emit before and after compaction events for automation and debugging.
135. `OC-CONTEXT-005 | P1 | Parity` Flush durable memory before compaction.
136. `OC-CONTEXT-006 | P1 | Parity` Reserve token headroom before compaction.
137. `OC-CONTEXT-007 | P1 | Parity` Add configurable post-compaction reinjection sections.
138. `OC-CONTEXT-008 | P1 | Parity` Make memory plugin slot selection first-class in the UI.
139. `OC-CONTEXT-009 | P2 | Uplift` Add health reporting for memory and context-engine providers.
140. `OC-CONTEXT-010 | P2 | Uplift` Add context-assembly diagnostics so operators can see what was assembled and why.
141. `OC-CONTEXT-011 | P2 | Parity` Add subagent context handoff hooks.
142. `OC-CONTEXT-012 | P2 | Uplift` Record compaction history and failure reasons.
143. `OC-CONTEXT-013 | P2 | Parity` Skip unnecessary compaction on idle or empty sessions.
144. `OC-CONTEXT-014 | P2 | Uplift` Attach provenance metadata to memory recall and context assembly.

### Category J: Config, Onboarding, Doctor, and Update Flows

Evidence:

- OpenClaw current sources: README, `docs/web/control-ui.md`, `docs/tools/plugin.md`, `CHANGELOG.md`
- AGENT-33 current sources: [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md), [frontend/src/App.tsx](/D:/GITHUB/AGENT33/frontend/src/App.tsx)

145. `OC-CONFIG-001 | P0 | Parity` Add modular config include support if AGENT-33 config continues to grow.
146. `OC-CONFIG-002 | P0 | Parity` Add safe include-path validation with root and symlink protections.
147. `OC-CONFIG-003 | P0 | Parity` Add targeted config schema lookup endpoints for UI forms.
148. `OC-CONFIG-004 | P0 | Parity` Expand schema-driven frontend forms across plugins, packs, tools, and automation.
149. `OC-CONFIG-005 | P1 | Parity` Surface secret-source provenance rather than flattening everything into plain values.
150. `OC-CONFIG-006 | P1 | Parity` Add onboarding flows for web research providers, plugins, packs, and backup policy.
151. `OC-CONFIG-007 | P1 | Parity` Add remote gateway token-style UX for secure remote control-plane connections.
152. `OC-CONFIG-008 | P1 | Uplift` Add SecretRef-like abstractions consistently across operator configuration flows.
153. `OC-CONFIG-009 | P1 | Parity` Make doctor and status commands work in read-only degraded mode without requiring full runtime credentials.
154. `OC-CONFIG-010 | P1 | Parity` Add update channel management for stable, beta, and dev tracks where relevant.
155. `OC-CONFIG-011 | P1 | Parity` Add update-run reports that summarize restart and migration outcomes.
156. `OC-CONFIG-012 | P1 | Uplift` Add environment-versus-file precedence inspection tools.
157. `OC-CONFIG-013 | P1 | Parity` Add config apply flows that validate, write, restart, and wake the last active context safely.
158. `OC-CONFIG-014 | P2 | Parity` Move frontend token persistence to safer session-scoped behavior where applicable.
159. `OC-CONFIG-015 | P2 | Uplift` Add setup guides and docs deep-linking directly from failed validation messages.
160. `OC-CONFIG-016 | P2 | Parity` Add restart guards that validate configuration before bringing services back up.

### Category K: Workflow, Automation, and Operations Hub Parity

Evidence:

- OpenClaw current sources: `docs/web/control-ui.md`, `docs/tools/index.md`, `CHANGELOG.md`
- AGENT-33 current sources: [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md), [frontend/src/App.tsx](/D:/GITHUB/AGENT33/frontend/src/App.tsx)

161. `OC-OPS-001 | P0 | Parity` Complete cron CRUD parity in the frontend with a dedicated page.
162. `OC-OPS-002 | P0 | Parity` Add cron run history filters and detailed run views.
163. `OC-OPS-003 | P1 | Parity` Add cron delivery-mode controls beyond the current basic scheduling UX.
164. `OC-OPS-004 | P1 | Parity` Add webhook delivery mode for automation outputs.
165. `OC-OPS-005 | P1 | Parity` Expose advanced per-job overrides for agent, model, and effort level.
166. `OC-OPS-006 | P1 | Parity` Add strict versus best-effort delivery controls.
167. `OC-OPS-007 | P1 | Parity` Add webhook token configuration and validation.
168. `OC-OPS-008 | P1 | Parity` Add restart catch-up and replay policy controls.
169. `OC-OPS-009 | P1 | Parity` Finish SSE fallback for workflow status graphs already called out in `docs/next-session.md`.
170. `OC-OPS-010 | P1 | Uplift` Add include-selectors and saved views to the operations hub.
171. `OC-OPS-011 | P1 | Uplift` Add live stream filters for workflows, reviews, budgets, traces, and improvements.
172. `OC-OPS-012 | P2 | Uplift` Add a unified queue view across workflows, reviews, releases, and improvement tasks.
173. `OC-OPS-013 | P2 | Parity` Add pause, resume, cancel, and retry controls consistently across long-running processes.
174. `OC-OPS-014 | P2 | Uplift` Attach provenance and delivery receipts to automation outputs.

### Category L: Provenance, Receipts, and Audit UX

Evidence:

- OpenClaw current sources: `src/acp/translator.ts`, `CHANGELOG.md`, `docs/web/webchat.md`
- AGENT-33 current sources: [engine/src/agent33/packs/provenance.py](/D:/GITHUB/AGENT33/engine/src/agent33/packs/provenance.py)

175. `OC-PROV-001 | P0 | Parity` Add visible provenance receipt blocks for delegated or external ingress.
176. `OC-PROV-002 | P0 | Parity` Add machine-readable ingress provenance metadata on inbound session creation and delegated runs.
177. `OC-PROV-003 | P1 | Parity` Expose source host, cwd, session id, and target session in operator-visible receipts where appropriate.
178. `OC-PROV-004 | P1 | Parity` Show trace identifiers in the UI so operators can connect visible activity to backend traces.
179. `OC-PROV-005 | P1 | Parity` Preserve provenance across spawned sessions and replay flows.
180. `OC-PROV-006 | P1 | Parity` Carry provenance into announce and reply-back flows.
181. `OC-PROV-007 | P1 | Parity` Attach plugin and tool provenance to activity stream events.
182. `OC-PROV-008 | P1 | Uplift` Track who changed config, packs, plugins, and policies in a unified audit timeline.
183. `OC-PROV-009 | P1 | Uplift` Record backup provenance chain including creator, source roots, and verify result.
184. `OC-PROV-010 | P1 | Uplift` Attach provenance to competitive research intake records and imports.
185. `OC-PROV-011 | P2 | Parity` Label external web content trust status at the point of use.
186. `OC-PROV-012 | P2 | Uplift` Add exportable audit bundles for runs, backups, and delegated tasks.
187. `OC-PROV-013 | P2 | Uplift` Persist approval-decision provenance across governance workflows.
188. `OC-PROV-014 | P2 | Uplift` Add source-of-truth receipt templates for external integrations and connectors.

### Category M: Frontend Quality, Accessibility, and Testing

Evidence:

- OpenClaw current sources: `docs/web/control-ui.md`, `ui/` runtime-catalog tests
- AGENT-33 current sources: [frontend/src/App.tsx](/D:/GITHUB/AGENT33/frontend/src/App.tsx), [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md)

189. `OC-FE-001 | P0 | Parity` Refactor the frontend from a single-shell component into a route-based application.
190. `OC-FE-002 | P0 | Parity` Create dedicated pages for chat, operations, plugins, packs, tools, backups, sessions, and config.
191. `OC-FE-003 | P1 | Parity` Make all operator pages responsive and mobile-safe.
192. `OC-FE-004 | P1 | Parity` Standardize empty, loading, and error states.
193. `OC-FE-005 | P1 | Parity` Add keyboard-accessible navigation and focus management.
194. `OC-FE-006 | P1 | Parity` Add landmarks, labels, and screen-reader support across control-plane surfaces.
195. `OC-FE-007 | P1 | Parity` Add component-level render and interaction tests using Testing Library.
196. `OC-FE-008 | P1 | Parity` Add end-to-end frontend workflows for operator-critical flows.
197. `OC-FE-009 | P1 | Parity` Add websocket reconnect and degraded-runtime UI tests.
198. `OC-FE-010 | P1 | Parity` Add schema-form interaction tests for plugin and config pages.
199. `OC-FE-011 | P2 | Uplift` Add provenance receipt rendering tests.
200. `OC-FE-012 | P2 | Uplift` Add backup and restore workflow tests in the UI layer.
201. `OC-FE-013 | P2 | Parity` Add plugin install, enable, update, and failure-path UI tests.
202. `OC-FE-014 | P2 | Parity` Add runtime tool catalog fallback tests.
203. `OC-FE-015 | P2 | Uplift` Add command palette and keyboard-shortcut tests.
204. `OC-FE-016 | P2 | Uplift` Add localization foundations and locale-switch tests.
205. `OC-FE-017 | P2 | Uplift` Add walkthrough documentation for the operator UI.
206. `OC-FE-018 | P2 | Uplift` Add contextual help and glossary overlays for operator terminology.

### Category N: Runtime, Deployment, and Platform Hardening

Evidence:

- OpenClaw current sources: `docs/web/control-ui.md`, `CHANGELOG.md`, README
- AGENT-33 current sources: [docs/next-session.md](/D:/GITHUB/AGENT33/docs/next-session.md), [frontend/src/App.tsx](/D:/GITHUB/AGENT33/frontend/src/App.tsx)

207. `OC-RUNTIME-001 | P1 | Parity` Harden frontend asset-root resolution so packaged and relocated deployments do not break.
208. `OC-RUNTIME-002 | P1 | Uplift` Reduce frontend and runtime artifact size for operator deployments.
209. `OC-RUNTIME-003 | P1 | Parity` Add declarative dependency baking for optional extensions in container builds.
210. `OC-RUNTIME-004 | P1 | Parity` Add explicit browser relay bind-host configuration for cross-namespace setups.
211. `OC-RUNTIME-005 | P1 | Parity` Add CDP URL normalization and host rewrite handling for remote browsers.
212. `OC-RUNTIME-006 | P1 | Parity` Add direct relay diagnostics for browser and remote UI surfaces.
213. `OC-RUNTIME-007 | P1 | Parity` Make restart operations fail visibly when shutdown drains time out.
214. `OC-RUNTIME-008 | P1 | Parity` Validate config before service restart and prevent restart loops on bad config.
215. `OC-RUNTIME-009 | P1 | Parity` Teach the runtime to detect supervised restarts and avoid inappropriate self-respawn behavior.
216. `OC-RUNTIME-010 | P1 | Uplift` Add startup repair flows for stale service tokens and config drift.
217. `OC-RUNTIME-011 | P1 | Parity` Calibrate browser and device auth rate limits so healthy sessions are not penalized by bad clients.
218. `OC-RUNTIME-012 | P2 | Parity` Add live logs tail and export surfaces to the frontend.
219. `OC-RUNTIME-013 | P2 | Parity` Surface runtime version plus short git hash in the UI and CLI.
220. `OC-RUNTIME-014 | P2 | Parity` Improve doctor parity across local, container, and remote deployments.
221. `OC-RUNTIME-015 | P2 | Uplift` Add migration assistants for old config and persisted state versions.
222. `OC-RUNTIME-016 | P2 | Uplift` Add packaged release artifact verification in deployment workflows.

## Highest-Value Implementation Tracks

If AGENT-33 wants fast parity gains without wasting effort on OpenClaw-specific product sprawl, the best implementation tracks are:

1. Runtime discoverability track
   - `OC-TOOL-001` through `OC-TOOL-016`
   - `OC-UI-001` through `OC-UI-010`
   - `OC-FE-001` through `OC-FE-010`

2. Safe mutation and backup confidence track
   - `OC-MUTATE-001` through `OC-MUTATE-016`
   - `OC-BACKUP-001` through `OC-BACKUP-016`

3. Plugin, pack, and onboarding track
   - `OC-PLUG-001` through `OC-PLUG-018`
   - `OC-PACK-001` through `OC-PACK-016`
   - `OC-CONFIG-001` through `OC-CONFIG-016`

4. Research and provenance track
   - `OC-WEB-001` through `OC-WEB-016`
   - `OC-PROV-001` through `OC-PROV-014`

5. Session and operations usability track
   - `OC-SESSION-001` through `OC-SESSION-014`
   - `OC-OPS-001` through `OC-OPS-014`

## Suggested Execution Order

Phase A, 2-3 sessions:

- runtime tool catalog
- UI route reset
- plugin and pack management pages

Phase B, 2-3 sessions:

- `apply_patch` runtime tool
- process manager
- backup create and verify APIs plus UI

Phase C, 2-3 sessions:

- provider-aware web research
- provenance receipts
- session and subagent usability

Phase D, ongoing:

- onboarding, doctor, update, accessibility, and deployment hardening

## Bottom Line

OpenClaw's latest repo should not push AGENT-33 toward a broader consumer product surface. It should push AGENT-33 toward a much better operator surface.

The core parity gap is not "missing capabilities in principle." It is "missing capability packaging, discoverability, and trust affordances in practice."

If AGENT-33 ships the Wave 0 items above, it will close the most important operator-facing parity gap with OpenClaw quickly while keeping its stronger governance-first architecture intact.
