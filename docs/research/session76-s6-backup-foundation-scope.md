# Session 76 S6 Scope Lock

Date: 2026-03-12
Slice: `S6 - OpenClaw Track 6A platform backup manifest/create/verify`
Worktree: `D:\GITHUB\AGENT33\worktrees\session76-s6-backup-foundation`
Branch: `codex/session76-s6-backup-foundation`

## Goal

Add a platform-level backup service that can inventory managed assets, create versioned backup archives, list existing backups, load backup detail, and verify archive integrity.

## Included

- New `agent33.backup` package with manifest/result models and archive helpers
- `BackupService` covering:
  - inventory preview
  - archive creation
  - archive verification
  - backup listing
  - backup detail loading
- New `/v1/backups` API routes for:
  - `POST /v1/backups`
  - `GET /v1/backups`
  - `GET /v1/backups/inventory`
  - `GET /v1/backups/{backup_id}`
  - `POST /v1/backups/{backup_id}/verify`
- App startup wiring and config for a dedicated backup directory
- Operator backup catalog delegation to the platform backup service when present
- Focused service/API regression tests

## Explicit Non-Goals

- Restore execution
- Restore-plan preview APIs
- Destructive-flow governance prompts for backup recommendations
- Database dump/export beyond manifesting that external database export is not implemented yet
- Frontend/operator UI beyond existing JSON surfaces

## Implementation Notes

- The current improvement-learning backup remains intact and is treated as a subsystem-specific backup, not the platform archive format.
- The initial platform backup will prioritize managed file/system assets already represented by current settings and registries.
- Workspace backup support stays optional; the runtime wiring will avoid recursive archive generation by not enabling workspace capture from the repo root in this slice.
