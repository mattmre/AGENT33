# Session 88 S16 Track 9 Scope Lock

Date: 2026-03-14
Branch: TBD (will be `codex/session88-s16-track9`)
Worktree: TBD

## Goal

Close the operator-experience gap on cron management, configuration introspection and apply, onboarding, and diagnostics.

## Current Baseline

- `WorkflowScheduler` has schedule_cron/interval, remove, list_jobs — but no REST API, no run history, no delivery mode controls
- Config is a flat 455-line Pydantic Settings class with no schema lookup, no config apply flow
- Doctor has DOC-01 through DOC-10 covering infrastructure and core registries
- Missing doctor checks: sessions, hooks, scheduler, MCP, voice, backup, context

## Included Work

1. Cron CRUD API (`automation/models.py`, `automation/job_history.py`, `api/routes/cron.py`)
2. Config Schema Introspection (`config_schema.py`)
3. Config Apply Service (`config_apply.py`)
4. Doctor Expansion (DOC-11 through DOC-17)
5. Onboarding Checklist (`operator/onboarding.py`)
6. API routes for cron, config, onboarding
7. Config additions
8. Tests

## Explicit Non-Goals

- Track 10 provenance work
- Frontend cron/config UI
- Config includes (deferred)
- Full restart automation

## Exit Criteria

- Cron jobs manageable via REST API
- Config schema inspectable by operators
- Config changes validatable and applicable
- Doctor covers all major subsystems
- Onboarding status computable from runtime state
