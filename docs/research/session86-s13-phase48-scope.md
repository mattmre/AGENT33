# Session 86: S13 Phase 48 Scope Lock

**Date:** 2026-03-14  
**Slice:** `S13 - Phase 48 operator UX and production hardening`  
**Worktree:** `D:\GITHUB\AGENT33\worktrees\session86-s13-phase48`  
**Branch:** `codex/session86-s13-phase48`  
**Status:** scope locked

## Why this slice exists

Phase 35 deliberately stopped at a multimodal voice control plane and a stub transport. Session 85 then made that deferment explicit by rejecting direct in-process `livekit` usage and reserving real media transport for Phase 48. The next safe step is therefore not a broad multimodal rewrite, but a bounded operator-facing uplift that:

- introduces a real standalone voice sidecar package and startup entrypoint
- lets the main API runtime talk to that sidecar through a client/probe boundary instead of embedding realtime transport
- publishes a live status snapshot from the Phase 44 continuity layer
- exposes both surfaces through health and operator status APIs

## Current baseline

- `engine/src/agent33/multimodal/voice_daemon.py` is now an explicit compatibility shim.
- `engine/src/agent33/multimodal/service.py` still manages voice sessions in-process and only knows `stub` and deferred `livekit`.
- `engine/src/agent33/sessions/` already persists operator session cache state, but nothing currently writes a Phase 48 status-line snapshot into `OperatorSession.cache`.
- hook discovery currently defaults to `<cwd>/.claude/hooks`, while the Phase 44 architecture and operator docs also describe `scripts/hooks/`.
- `GET /health` and `GET /v1/operator/status` do not currently surface sidecar/status-line health.

## Included work

1. Add a new `agent33.voice` package that provides:
   - a standalone FastAPI sidecar app
   - a WebSocket endpoint for session traffic
   - persona loading from `voices.json`
   - artifact persistence to disk
   - graceful shutdown support
   - a runnable module entrypoint for local operator startup
2. Add a sidecar client/probe boundary in the main runtime:
   - a client-backed daemon implementation for `voice_daemon_transport=sidecar`
   - sidecar health probing that can be attached to `app.state`
   - config needed to run and inspect the sidecar without reusing the deprecated `livekit` path
3. Add a Phase 48 status snapshot service:
   - collect tool/skill/pack/plugin/hook/process counts
   - include git branch/commit/dirty metadata when available
   - include voice runtime / sidecar health summary
   - persist a renderable snapshot into `OperatorSession.cache["status_line"]`
4. Add project hook support for the status line:
   - prefer `scripts/hooks/` when present before falling back to `.claude/hooks/`
   - add a repo-tracked `session.checkpoint` status-line hook script that renders from the persisted cache
5. Expose the new surfaces:
   - extend `/health`
   - extend `/v1/operator/status`
   - add focused backend regression coverage
6. Update operator docs for startup, transport choice, and failure modes.

## Explicit non-goals

- no direct in-process `livekit` implementation
- no ElevenLabs MCP proxy integration in this PR beyond health/config awareness
- no frontend redesign beyond what existing API consumers get automatically from the new health data
- no OpenClaw Track 7 or Track 8 work
- no broad hook framework redesign beyond the project hook directory fallback needed for `scripts/hooks/`

## File targets

- `engine/src/agent33/voice/`
- `engine/src/agent33/multimodal/service.py`
- `engine/src/agent33/main.py`
- `engine/src/agent33/config.py`
- `engine/src/agent33/api/routes/health.py`
- `engine/src/agent33/operator/models.py`
- `engine/src/agent33/operator/service.py`
- `engine/src/agent33/sessions/service.py`
- `scripts/hooks/`
- `docs/operators/voice-daemon-runbook.md`
- focused tests under `engine/tests/`

## Validation plan

- `pytest` on new voice-sidecar, health, operator, session-cache, and hook fallback regressions
- `ruff check`
- `ruff format --check`
- `mypy` on the touched source files

## Merge readiness criteria

- main runtime can start voice sessions against a configured standalone sidecar transport
- operator sessions persist a status-line snapshot during checkpoint lifecycle
- `/health` and `/v1/operator/status` show sidecar/status-line state without crashing when the sidecar is absent
- the repo contains a tracked `scripts/hooks/` status-line script and hook discovery will find it by default
