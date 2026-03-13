# OpenClaw Parity 10-Phase Roadmap

Date: 2026-03-09
Primary source backlog: [openclaw-six-month-parity-backlog-2026-03-09.md](../research/openclaw-six-month-parity-backlog-2026-03-09.md)

## Purpose

This roadmap turns the 222-item OpenClaw parity backlog into a 10-phase execution track that can run across upcoming AGENT-33 sessions without destabilizing the existing phase system.

This is not a new "replace everything" roadmap. It is an operator-surface acceleration plan layered on top of the current AGENT-33 architecture.

## Design Principles

1. Preserve AGENT-33's governance-first architecture.
2. Prioritize operator experience over consumer-channel breadth.
3. Build runtime truth surfaces before frontend polish.
4. Ship safe mutating capabilities only with governance and audit integration.
5. Prefer schema-driven, introspectable surfaces over hardcoded UI assumptions.
6. Land each phase with tests, docs, and clear handoff criteria.

## Architectural Pillars

### Pillar A: Control Plane Reset

- Route-based operator UI
- task-oriented information architecture
- dedicated pages for tools, plugins, packs, backups, sessions, and automation

### Pillar B: Runtime Metadata as Source of Truth

- runtime tool catalog
- config schema lookup
- provenance metadata
- health and lifecycle inventories

### Pillar C: Extension and Distribution Platform

- plugin install/update/doctor
- pack marketplace and trust
- schema-aware plugin and pack config UI

### Pillar D: Safe Operator Power Tools

- structured patch tool
- background process manager
- archive-level backup and restore
- web-grounded research surfaces

### Pillar E: Delegation and Context Durability

- session catalog and subagent controls
- context-engine slotting
- compaction durability
- session provenance receipts

### Pillar F: Operational Confidence

- doctor and update ergonomics
- restart and deployment hardening
- frontend accessibility and test coverage
- exportable audit flows

## Phase Summary

| Track Phase | Title | Core Outcome | Backlog Focus |
| --- | --- | --- | --- |
| 1 | Operator Shell Reset | Route-based control plane and new information architecture | UI, FE foundation |
| 2 | Runtime Catalog Surfaces | Runtime tool catalog plus schema lookup and discoverability | Tool catalog, config schema |
| 3 | Plugin Lifecycle Platform | Install/update/doctor/config flows for plugins | Plugin lifecycle |
| 4 | Pack Distribution Platform | Marketplace, trust, provenance, and tenant enablement for packs | Packs, marketplace |
| 5 | Safe Mutation and Process Control | `apply_patch`, policy groups, process manager, mutation audit | Mutation and execution governance |
| 6 | Backup and Restore Confidence | Archive-grade backup create/verify/restore planning | Backup and recovery |
| 7 | Web Research and Trust | Multi-provider web search/fetch with source trust affordances | Web grounding |
| 8 | Sessions and Context Engine UX | Session catalog, subagent UX, context-engine slotting | Sessions, context |
| 9 | Operations, Config, and Doctor | Cron parity, config apply, onboarding, update, doctor flows | Ops and config |
| 10 | Provenance, Hardening, and Closeout | Receipts, audit exports, FE quality, runtime hardening | Provenance, FE, runtime |

## Execution Policy

- Treat each track phase as 1-3 PRs, not one mega-branch.
- Finish backend contracts before frontend integration for each phase.
- Keep each phase independently reviewable and testable.
- Do not start the next phase until the current phase has at least skeleton docs and tests.

## Phase 1: Operator Shell Reset

### Objective

Replace the current monolithic shell with a route-based operator UI that exposes clear destinations for the capabilities AGENT-33 already has.

### Backlog Coverage

- `OC-UI-001` through `OC-UI-010`
- `OC-FE-001` through `OC-FE-006`

### Architecture Work

- introduce route-based app shell
- split end-user chat from operator control plane
- create dedicated top-level pages for operations, tools, plugins, packs, sessions, and backups
- add persistent status, notifications, and docs-link affordances

### Likely Files

- `frontend/src/App.tsx`
- new route modules under `frontend/src/features/`
- `frontend/src/styles.css`
- shared nav and layout components

### Exit Criteria

- route-based shell lands
- advanced settings no longer acts as the dumping ground for operator features
- navigation is testable and keyboard-accessible
- next session can add new pages without further shell rework

## Phase 2: Runtime Catalog Surfaces

### Objective

Make runtime metadata the UI source of truth for tools and configuration.

### Backlog Coverage

- `OC-TOOL-001` through `OC-TOOL-016`
- `OC-CONFIG-003`
- `OC-CONFIG-004`

### Architecture Work

- add tool catalog API models and endpoint
- expose grouped tool metadata, source labels, effective availability, and schemas
- add config schema lookup endpoint for targeted form rendering
- build frontend tool catalog views with runtime fallback behavior

### Likely Files

- `engine/src/agent33/tools/registry.py`
- new API route under `engine/src/agent33/api/routes/`
- frontend tools page and schema-form support modules

### Exit Criteria

- frontend no longer hardcodes tool assumptions
- tool pages show runtime truth and fallback cleanly
- config-driven forms become practical for later plugin and pack phases

## Phase 3: Plugin Lifecycle Platform

### Objective

Turn AGENT-33 plugins from "discover and toggle" into a real installable, diagnosable extension surface.

### Backlog Coverage

- `OC-PLUG-001` through `OC-PLUG-018`
- `OC-CONFIG-005`

### Architecture Work

- add install/update/link provenance
- persist plugin config
- add health, permission, route, and command inventory
- wire plugin config schemas into UI
- add operator doctor path for plugins

### Likely Files

- `engine/src/agent33/api/routes/plugins.py`
- plugin registry and persistence modules
- frontend plugin management views

### Exit Criteria

- plugins can be installed and managed intentionally
- config changes persist
- operators can explain plugin failures without reading code

## Phase 4: Pack Distribution Platform

### Objective

Finish the ecosystem story for packs with marketplace, trust, and lifecycle control.

### Backlog Coverage

- `OC-PACK-001` through `OC-PACK-016`

### Architecture Work

- add marketplace sources
- add pack provenance and signature workflows to UI
- add dependency/conflict inspection
- add enablement matrix and rollback

### Likely Files

- `engine/src/agent33/packs/registry.py`
- `engine/src/agent33/packs/provenance.py`
- `engine/src/agent33/api/routes/packs.py`
- frontend pack pages

### Exit Criteria

- packs are no longer local-only
- trust policy is visible and enforceable
- pack install path is operator-safe

## Phase 5: Safe Mutation and Process Control

### Objective

Ship a safe, reviewable mutating tool surface for file edits and runtime processes.

### Backlog Coverage

- `OC-MUTATE-001` through `OC-MUTATE-016`

### Architecture Work

- add `apply_patch` tool contract
- integrate with autonomy and approvals
- add filesystem boundary enforcement
- add process manager UI and log tailing
- add mutation audit trail

### Likely Files

- `engine/src/agent33/tools/`
- `engine/src/agent33/api/routes/tool_approvals.py`
- `engine/src/agent33/autonomy/`
- frontend tools/process pages

### Exit Criteria

- patch tool works with workspace containment
- mutation flows are auditable and governable
- operators can manage background sessions from UI

## Phase 6: Backup and Restore Confidence

### Objective

Create archive-grade backup and verify flows for AGENT-33 runtime state.

### Backlog Coverage

- `OC-BACKUP-001` through `OC-BACKUP-016`

### Architecture Work

- define backup manifest schema
- implement create and verify services
- add restore planning and inventory browsing
- integrate backup guidance into destructive flows

### Likely Files

- new backup service package under `engine/src/agent33/`
- backup API routes
- frontend backup pages
- improvement backup endpoints refactored into broader backup architecture

### Exit Criteria

- AGENT-33 can create and verify platform backups
- restore has a safe preview path
- backup is no longer limited to improvement learning state

## Phase 7: Web Research and Trust

### Objective

Upgrade AGENT-33 from a simple search wrapper to a provider-aware grounded research layer.

### Backlog Coverage

- `OC-WEB-001` through `OC-WEB-016`

### Architecture Work

- add provider abstraction
- add structured result models
- add source trust labels
- add citation cards and provider diagnostics

### Likely Files

- `engine/src/agent33/tools/builtin/search.py`
- `engine/src/agent33/tools/builtin/web_fetch.py`
- frontend research and chat surfaces

### Exit Criteria

- multiple providers supported coherently
- research outputs carry explicit trust semantics
- operators can see provider capability and auth state

## Phase 8: Sessions and Context Engine UX

### Objective

Make delegation, session state, and context management visible and operable.

### Backlog Coverage

- `OC-SESSION-001` through `OC-SESSION-014`
- `OC-CONTEXT-001` through `OC-CONTEXT-014`

### Architecture Work

- add session catalog and lineage tree
- add subagent spawn forms and overrides
- add context-engine slot abstraction and lifecycle hooks
- add compaction durability controls and diagnostics

### Likely Files

- session APIs and services
- memory and context modules
- frontend sessions page

### Exit Criteria

- operators can understand delegation and context behavior
- context-engine substitution is explicit and testable
- compaction no longer feels opaque

## Phase 9: Operations, Config, and Doctor

### Objective

Close the operator-experience gap on cron, onboarding, config writes, and diagnostics.

### Backlog Coverage

- `OC-OPS-001` through `OC-OPS-014`
- `OC-CONFIG-001` through `OC-CONFIG-016`
- selected `OC-RUNTIME-*` restart and doctor items

### Architecture Work

- finish cron parity in UI
- add schema-driven config apply flows
- add doctor, onboarding, and update surfaces
- add restart validation and failure reporting

### Likely Files

- operations routes and frontend pages
- config APIs
- startup and restart handling in `engine/src/agent33/main.py`

### Exit Criteria

- cron and config become first-class operator flows
- update and doctor paths are no longer doc-only or CLI-only assumptions
- restart safety improves materially

## Phase 10: Provenance, Hardening, and Closeout

### Objective

Finish the track with explicit provenance UX, stronger test coverage, and platform hardening.

### Backlog Coverage

- `OC-PROV-001` through `OC-PROV-014`
- `OC-FE-007` through `OC-FE-018`
- remaining `OC-RUNTIME-001` through `OC-RUNTIME-016`

### Architecture Work

- add visible receipts and audit exports
- complete FE test matrix and accessibility work
- finish runtime packaging, logging, doctor, migration, and release-hardening improvements

### Likely Files

- observability and lineage modules
- frontend shared components
- deployment and packaging scripts

### Exit Criteria

- provenance is visible to operators, not just stored internally
- frontend quality bar is raised for long-term maintainability
- the OpenClaw parity track can be closed and folded into normal roadmap maintenance

## Recommended Session Sequencing

Session block 1:

- Track Phase 1
- Track Phase 2

Session block 2:

- Track Phase 3
- Track Phase 4

Session block 3:

- Track Phase 5
- Track Phase 6

Session block 4:

- Track Phase 7
- Track Phase 8

Session block 5:

- Track Phase 9
- Track Phase 10

## Immediate Next-Session Starting Point

Start with Track Phase 1 and Track Phase 2 together:

- shell reset
- route-based operator pages
- runtime tool catalog
- schema lookup contract

That combination unlocks almost every later phase because it gives AGENT-33 both a better operator shell and a runtime-truth contract for frontend discoverability.
