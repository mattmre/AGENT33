# Session 77 S7 Scope Lock

Date: 2026-03-12
Slice: `S7 - OpenClaw Track 6B restore planning / preview`
Worktree: `D:\GITHUB\AGENT33\worktrees\session77-s7-restore-preview`
Branch: `codex/session77-s7-restore-preview`
Baseline: `aa69d9f` (`feat(backups): add platform backup foundation (#182)`)

## Goal

Add read-only restore planning on top of the merged platform backup service so operators can preview what a restore would do before any destructive execution exists.

## Included

- `agent33.backup.restore_planner` with:
  - archive manifest loading
  - current-target comparison against live source paths
  - per-asset restore actions (`create`, `overwrite`, `skip`)
  - conflict reporting for version/schema/current-file mismatches
- `POST /v1/backups/{backup_id}/restore-plan`
- operator guidance text for destructive flows if a lightweight integration point is available without widening scope
- focused planner/API tests

## Explicit Non-Goals

- Restore execution
- Any mutation of live files or registries
- Broad approval/governance rework outside a narrow backup recommendation hook
- Additional backup-create features already merged in S6

## Research Notes

- The S6 baseline now has manifest/detail/verify/list/inventory coverage and a stable archive format.
- There is still no restore planner implementation or `/restore-plan` route.
- Existing improvement-learning restore remains subsystem-specific and should not be reused as the platform restore mechanism.
- The planner should read the backup archive plus current filesystem state only; it should not extract or overwrite outside a temporary inspection path.
