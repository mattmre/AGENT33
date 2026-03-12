# Session 72 S2: Plugin Lifecycle Scope Lock

Date: 2026-03-12
Slice: S2
Branch: `codex/session72-s2-plugin-lifecycle`

## Fresh Baseline

- Started from fresh `origin/main` at `adc90cf`.
- Re-read the canonical queue in `task_plan.md`, `findings.md`, and `progress.md`.
- Anchored the architecture on:
  - `docs/phases/OPENCLAW-PARITY-10-PHASE-ROADMAP.md`
  - `docs/research/session59-openclaw-tracks3-6-architecture.md`
  - committed plugin code under `engine/src/agent33/plugins/`

## What Already Exists

- Plugin manifests, capability grants, scoped registries, lifecycle states, and a registry exist.
- FastAPI routes already support list, detail, search, enable, disable, reload, config, health, and discover.
- Operator diagnostics already count plugins globally.

## Verified Gaps On `main`

- No install or link flow from local plugin paths.
- No update flow for already-managed plugins.
- Plugin config route is explicitly a stub and does not persist.
- No plugin lifecycle event history for audit or debugging.
- No plugin-specific doctor surface with source, dependency, permission, and health checks.
- No route to inspect plugin permission grants without reading raw code or logs.

## Included In S2

- Local plugin install and local dev link flows.
- Plugin update flow for locally managed plugins.
- File-backed plugin config persistence and install metadata persistence.
- Lifecycle event recording for registry transitions and install/update actions.
- Plugin doctor service plus API endpoints for one plugin and all plugins.
- Permission and event inventory endpoints.

## Explicit Non-Goals

- Remote plugin registry downloads.
- Archive install support.
- Frontend plugin management UI.
- Pack marketplace or trust-policy work from Track 4.
- Background process management from Track 5.

## Validation Target

- New unit tests for config persistence, install/update/link flows, doctor checks, and event recording.
- Expanded plugin route tests for the new API surface.
- Targeted `pytest`, `ruff`, and `mypy` on touched plugin modules and tests.
