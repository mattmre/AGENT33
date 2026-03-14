# Session 88 S15 Track 8 Scope Lock

Date: 2026-03-14
Branch: `codex/session88-s15-track8`
Worktree: `worktrees/session88-s15-track8`

## Goal

Land the backend slice of OpenClaw Track 8 by making session delegation, context management, and session state visible and operable for operators.

## Current Baseline

- `OperatorSessionService` handles lifecycle (start, end, resume, checkpoint), task tracking, crash detection, and replay
- `FileSessionStorage` persists per-session directories
- `/v1/sessions` routes expose CRUD, replay, and task management
- `OperatorService.get_sessions()` returns an empty list (placeholder)
- `OperatorSession.parent_session_id` exists but no lineage builder
- No context engine abstraction — memory is wired directly
- No session spawn templates or per-session overrides

## Included Work

1. SessionCatalog — bridge OperatorSessionService into operator control plane
2. SessionLineage — build trees from parent_session_id chains
3. SessionSpawnService — template-based subagent spawning
4. SessionArchiveService — archive and cleanup completed/crashed sessions
5. ContextEngine package — pluggable context engine slots with protocol, registry, and diagnostics
6. API routes for catalog, lineage, spawn, archive, and context
7. Config additions for context engine, spawn templates, archive retention
8. Wire into main.py lifespan and OperatorService

## Explicit Non-Goals

- Track 9 cron/config/doctor work
- Track 10 provenance work
- Frontend session or context UI
- Memory/RAG pipeline changes
- Context engine compaction (deferred to follow-up)

## Exit Criteria

- Operators can browse a real session catalog (not empty)
- Session delegation is visible via lineage trees
- Subagent sessions can be spawned with templates
- Completed sessions can be archived
- Context engine is abstracted with a registry
- API routes are tested and functional
