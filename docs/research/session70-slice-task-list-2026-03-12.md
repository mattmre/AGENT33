# Session 70 Slice Task List

**Date:** 2026-03-12  
**Purpose:** Single-file sequential queue for the remaining roadmap slices.  
**Use:** Read this file first when resuming after interruption.

## Resume Steps

1. Read `task_plan.md`, `findings.md`, and `progress.md`.
2. Find the first slice below that is not marked `done`.
3. Start from the first unchecked phase item for that slice.
4. Do not work on later slices until the current slice is merged and post-merge verification is recorded.

## Status Key

- `pending`: not started
- `active`: current slice
- `blocked`: waiting on dependency or decision
- `done`: merged and verified

## Slice Queue

| Slice | Status | Depends on | Goal |
| --- | --- | --- | --- |
| S1 | done | none | Phase 46 closeout audit and status reconciliation |
| S2 | done | S1 | OpenClaw Track 3 plugin lifecycle platform (merged as `#178`, verified from fresh `origin/main`) |
| S3 | done | S2 | OpenClaw Track 4 pack distribution hardening (merged as `#179`, verified from fresh `origin/main`) |
| S4 | done | S3 | OpenClaw Track 5A `apply_patch` runtime foundation (merged as `#180`, verified from fresh `origin/main`) |
| S5 | done | S4 | OpenClaw Track 5B process manager (merged as `#181`, verified from fresh `origin/main`) |
| S6 | done | S5 | OpenClaw Track 6A backup manifest/create/verify (merged as `#182`, verified from fresh `origin/main`) |
| S7 | done | S6 | OpenClaw Track 6B restore planning / preview (merged as `#183`, verified from fresh `origin/main`) |
| S8 | done | S7 | Phase 25 SSE hardening + frontend tests (merged as `#184`, verified from fresh `origin/main`) |
| S9 | active (`research`) | S8 | Phase 38 Docker kernel hardening |
| S10 | pending | S9 | Phase 30 production trace tuning |
| S11 | pending | S10 | Phase 47 capability pack expansion |
| S12 | pending | S11 | Phase 35 / 48 voice convergence decision |
| S13 | pending | S12 | Phase 48 operator UX and production hardening |
| S14 | pending | S13 | OpenClaw Track 7 web research and trust |
| S15 | pending | S14 | OpenClaw Track 8 sessions and context UX |
| S16 | pending | S15 | OpenClaw Track 9 operations, config, and doctor |
| S17 | pending | S16 | OpenClaw Track 10 provenance, FE hardening, closeout |

## Standard Phase Checklist

Apply this checklist to every slice.

- [ ] Research refresh complete
- [ ] Scope lock written down
- [ ] Fresh `origin/main` worktree created
- [ ] Implementation complete
- [ ] Targeted tests passed
- [ ] Lint / format / type / build checks passed as applicable
- [ ] PR opened
- [ ] Review comments handled
- [ ] CI green
- [ ] PR merged
- [ ] Fresh merged-baseline verification recorded
- [ ] Planning files updated

## Slice Notes

### S1

- Close out the remaining delta after PRs `#172` and `#173`.
- Likely outputs: status doc refresh, any missing Phase 46 glue, tests.

### S2

- Focus on plugin install/update/link, config persistence, doctor, permissions, and lifecycle events.

### S3

- Extend existing marketplace/provenance work. Do not rebuild the already-merged local marketplace baseline.

### S4

- Keep scope to governed patch operations and mutation auditability.

### S5

- Keep scope to process/session management for long-running commands.
- Merged as PR `#181`.
- Fresh post-merge verification passed from `worktrees/session75-s5-postmerge-verify`.

### S6

- Create manifest/create/verify first.
- Start from merged baseline `41565ad` with fresh-context research refresh.
- Worktree: `worktrees/session76-s6-backup-foundation`
- Scope memo: `docs/research/session76-s6-backup-foundation-scope.md`
- Merged as PR `#182`.
- Fresh post-merge verification passed from `worktrees/session76-s6-postmerge-verify`.

### S7

- Restore preview and destructive-flow safety only after S6 is merged.
- Worktree: `worktrees/session77-s7-restore-preview`
- Scope memo: `docs/research/session77-s7-restore-preview-scope.md`
- Merged as PR `#183`.
- Fresh post-merge verification passed from `worktrees/session77-s7-postmerge-verify`.

### S8

- Treat Phase 25 as a hardening/test wave, not a first implementation.
- Worktree: `worktrees/session78-s8-sse-hardening`
- Scope memo: `docs/research/session78-s8-sse-hardening-scope.md`
- Merged as PR `#184`.
- Fresh post-merge verification passed from `worktrees/session78-s8-postmerge-verify`.

### S9

- Treat Docker kernels as already built; harden and test them.
- Worktree: `worktrees/session79-s9-docker-hardening`
- Scope memo: `docs/research/session79-s9-docker-hardening-scope.md`

### S10

- Focus on correlation and production tuning, not unrelated observability work.

### S11

- Depends on Phase 46 being truly closed so the discovery surface is stable.

### S12

- This slice may end as a decision memo plus minimal compatibility code rather than a large implementation.

### S13

- This is the real operator voice/status-line hardening slice.

### S14-S17

- Keep each track in its own PR even though they are grouped at the queue tail.
