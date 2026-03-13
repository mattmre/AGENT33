# Session 81 Holdout Preservation Audit

Date: 2026-03-13

## Scope

Audit the remaining repo-only holdout worktrees after the first cleanup pass. The goal is to determine, for each remaining item, whether its contents are already preserved on `origin/main`, partially superseded, or still contain unique local work that would need explicit salvage before deletion.

Checked locations only:

- `D:\GITHUB\AGENT33\worktrees`
- `D:\GITHUB\AGENT33\.claude\worktrees`

No deletions were performed during this audit.

## Method

For each holdout, the audit captured:

- current branch / HEAD
- linked PR state when present
- committed diff versus `origin/main`
- local dirty state from `git status --porcelain`
- file-content comparison against `origin/main` rather than the stale root checkout

Classification terms:

- `keep-intact`: contains unique local code or a large branch-only diff; do not delete without preservation work
- `salvage-first`: mostly superseded but still has branch-only or local-only deltas worth extracting before deletion
- `low-value salvage`: appears largely superseded; extract a patch or summary if desired, then delete

## Highest-Risk Holdouts

These still contain substantive local work not preserved verbatim on `origin/main`.

### `.claude/worktrees/agent-a5a29d23`

- Branch: `feat/session59-openclaw-tracks3-4-plugins-packs`
- PR: none
- Status: 22 dirty paths
- Evidence:
  - local edits to `plugins.py`, `plugins/api_models.py`, and `plugins/models.py` differ from `origin/main`
  - local files such as `engine/src/agent33/plugins/config_store.py`, `engine/src/agent33/plugins/doctor.py`, `engine/src/agent33/plugins/events.py`, `engine/src/agent33/plugins/installer.py`, `engine/src/agent33/packs/rollback.py`, and `engine/src/agent33/packs/trust_manager.py` differ from the current merged versions or exist under now-abandoned names
  - test files are under old `test_openclaw_*` names and are not present on `origin/main`
- Assessment: `keep-intact`
- Recommendation: if you want to preserve the abandoned combined T3/T4 implementation style, export a patch bundle from this worktree before deletion. The merged PRs cover the feature area, but not this exact draft.

### `.claude/worktrees/agent-ab53cb8a`

- Branch: `feat/session59-wave5-refinements`
- PR: none
- Status: 12 dirty paths
- Evidence:
  - local edits to `workflow_sse.py`, `execution/adapters/jupyter.py`, `execution/models.py`, `workflows/ws_manager.py`, and related tests all differ from `origin/main`
  - extra frontend test files `AuthPanel.test.tsx`, `GlobalSearch.test.tsx`, `HealthPanel.test.tsx`, and `ObservationStream.test.tsx` are not on `origin/main`
- Assessment: `keep-intact`
- Recommendation: preserve if those additional frontend and runtime refinements still matter; otherwise this is a candidate to archive as a patch and drop.

### `.claude/worktrees/agent-ac4da72a`

- Branch: `feat/session59-openclaw-tracks5-6-mutation-backup`
- PR: none
- Status: 12 dirty paths
- Evidence:
  - local `backups.py`, `backup/`, and `apply_patch.py` differ from merged code
  - local-only files such as `mutations.py`, `patch_audit.py`, `patch_security.py`, and several `test_openclaw_t5_*` / `test_openclaw_t6_*` files are not on `origin/main`
- Assessment: `keep-intact`
- Recommendation: preserve if you want the pre-merge Track 5/6 design variants. The shipped PRs cover the feature area, but not this exact draft or file layout.

### `.claude/worktrees/agent-af722d5d`

- Branch: `feat/session59-phase46-dynamic-catalog`
- PR: none
- Status: 19 dirty paths
- Evidence:
  - local edits to `config.py`, `main.py`, and `api/routes/discovery.py` differ from `origin/main`
  - local-only files such as `skills/semantic.py`, `skills/semantic_resolver.py`, `tools/activation.py`, `tools/catalog_service.py`, and `test_phase46_*` are not on `origin/main`
- Assessment: `keep-intact`
- Recommendation: preserve if you want the earlier semantic-catalog implementation approach; the merged Phase 46 PRs superseded it functionally, but not verbatim.

### `worktrees/session57-wave0-integration`

- Branch: `feat/session57-wave0-integration`
- PR: none
- Status: 30 dirty paths
- Evidence:
  - some files now match `origin/main` (`agents/events.py`, `workflows/executor.py`, `llm/stream_assembler.py`, `llm/streaming.py`, `test_stream_assembler.py`)
  - most dirty files still differ from `origin/main`, including `tool_loop.py`, `api/routes/mcp.py`, `api/routes/workflows.py`, `llm/*.py`, `mcp_server/*`, `workflow_ws.py`, and multiple tests
- Assessment: `keep-intact`
- Recommendation: treat as a large integration scratch branch with unique local work; preserve via patch bundle if you want to reclaim anything from it.

### `worktrees/session57-wave0-pr1`

- Branch: `feat/session57-wave0-pr1-llm-security-adapters`
- PR: `#146` merged
- Status: 4 dirty paths
- Evidence:
  - local edits to `execution/adapters/jupyter.py`, `plugins/registry.py`, `testing/agent_harness.py`, and `test_multimodal_messages.py` all differ from `origin/main`
- Assessment: `keep-intact`
- Recommendation: preserve before deletion if these late edits still matter; they were not part of merged PR `#146`.

### `worktrees/session57-wave1-pr1`

- Branch: `feat/session57-wave1-pr1-frontend-foundation`
- PR: `#145` merged
- Status: 9 dirty paths
- Evidence:
  - `tests/test_multimodal_messages.py` and `frontend/package-lock.json` match `origin/main`
  - local edits to `api/routes/mcp.py`, `execution/adapters/jupyter.py`, `llm/base.py`, `mcp_server/server.py`, `plugins/registry.py`, `testing/agent_harness.py`, and `frontend/package.json` still differ from `origin/main`
- Assessment: `keep-intact`
- Recommendation: preserve the remaining local diff before deleting; this is not just coverage noise.

## Dirty But Smaller Holdouts

### `worktrees/nightly-merge-main`

- Branch: `temp/session67-post-merge-smoke-fix`
- PR: none
- Status: 2 dirty paths
- Evidence:
  - `.github/workflows/post-merge-smoke.yml` adds `--no-cov` to the smoke pytest command and differs from `origin/main`
  - tracked `engine/.coverage` is deleted locally
- Assessment: `salvage-first`
- Recommendation: decide explicitly whether the smoke workflow should adopt `--no-cov`. If yes, turn that single diff into a real docs/ci PR or patch file; then delete the worktree.

### `worktrees/phase28`

- Branch: `feat/session56-phase28-security-adapters`
- PR: `#142` closed
- Status: dirty `engine/pyproject.toml` plus local `.coverage`
- Committed branch diff versus `origin/main`: 3 files, all different
- Evidence:
  - branch-only differences remain in `component_security/llm_security.py`, `test_llm_security.py`, and `test_llm_security_adapters.py`
  - uncommitted `engine/pyproject.toml` also differs from `origin/main`
- Assessment: `keep-intact`
- Recommendation: this is not preserved on `main`; if it matters, salvage the branch or extract a patch before deletion.

### `worktrees/phase38`

- Branch: `feat/session56-phase38-token-streaming`
- PR: `#144` closed
- Status: dirty `engine/.coverage` only
- Committed branch diff versus `origin/main`: 11 files, all different
- Assessment: `keep-intact`
- Recommendation: ignore the coverage artifact, but do not delete the branch/worktree until you decide whether the closed Stage 2 streaming implementation still has archival value.

### `worktrees/session57-wave1-pr2`

- Branch: `feat/session57-wave1-pr2-phase25-sse-graph-refresh`
- PR: `#149` closed
- Status: dirty `engine/src/agent33/api/routes/visualizations.py`
- Committed branch diff versus `origin/main`: 39 files, 8 same / 30 different / 1 missing
- Assessment: `keep-intact`
- Recommendation: preserve if you want any of the closed SSE/graph branch; at minimum, inspect the uncommitted `visualizations.py` delta before deleting.

## Clean Historical Branches With Remaining Branch-Only Content

These are clean on disk, but their committed branch tips are not fully represented on `origin/main`.

### `worktrees/codex-main-final`

- Branch: `codex/session59-wrap`
- PR: `#153` closed
- Committed diff: 3 files, 2 different and 1 missing on `origin/main`
- Files: `CLAUDE.md`, `docs/next-session.md`, and missing `docs/sessions/session-58-2026-03-09.md`
- Assessment: `low-value salvage`
- Recommendation: archive as a patch or a note if you care about the abandoned handoff wording; otherwise likely safe to drop after capture.

### `worktrees/phase43`

- Branch: `feat/session56-phase43-mcp-resources-auth`
- PR: `#143` closed
- Committed diff: 8 files, all different from `origin/main`
- Assessment: `keep-intact`
- Recommendation: closed Stage 2 branch still contains a distinct MCP auth/resources variant. Preserve or consciously discard.

### `worktrees/session57-main-ci-fix`

- Branch: `temp/session57-main-ci-fix`
- PR: none
- Committed diff: 7 files, 6 different / 1 same
- Assessment: `salvage-first`
- Recommendation: likely a temporary rescue branch, but it still carries code not equal to `origin/main`; export patch before deletion.

### `worktrees/session57-merge-check`

- Branch: `temp/session57-merge-check`
- PR: none
- Committed diff: 25 files, 15 same / 9 different / 1 missing
- Assessment: `salvage-first`
- Recommendation: mostly superseded, but not fully. If you want a compact archive candidate, this is one of the better ones for a single patch export and then delete.

### `worktrees/session57-wave1-live-base`

- Branch: `feat/session57-wave1-live-workflow-base`
- PR: none
- Committed diff: 26 files, 4 same / 21 different / 1 missing
- Assessment: `keep-intact`
- Recommendation: base branch for the Wave 1 stack still diverges materially from `origin/main`; keep until explicitly archived or discarded.

### `worktrees/session57-wave1-pr3`

- Branch: `feat/session57-wave1-pr3-phase27-templates-presets`
- PR: `#150` closed
- Committed diff: 51 files, 21 same / 29 different / 1 missing
- Assessment: `keep-intact`
- Recommendation: a lot of the canonical template work is preserved, but the branch still has substantial branch-only deltas.

### `worktrees/session58-phase26-wizard`

- Branch: `codex/session58-phase26-wizard`
- PR: `#152` closed
- Committed diff: 58 files, 23 same / 34 different / 1 missing
- Assessment: `keep-intact`
- Recommendation: this branch is not safely disposable yet; it still carries a large alternate wizard implementation stack.

### `worktrees/session60-docs-validation`

- Branch: `codex/session60-phase22-docs-validation`
- PR: `#154` closed
- Committed diff: 63 files, 26 same / 36 different / 1 missing
- Assessment: `keep-intact`
- Recommendation: despite the docs-oriented title, this branch still includes significant code divergence inherited from its base stack.

### `worktrees/session61-phase38-docker-kernels`

- Branch: `codex/session61-phase38-docker-kernels`
- PR: `#155` closed
- Committed diff: 21 files, 6 same / 15 different
- Assessment: `keep-intact`
- Recommendation: partially preserved on `main`, but still materially different. Preserve before deletion if the closed Docker-kernel branch still matters historically.

### `worktrees/session62-skillsbench-reporting`

- Branch: `codex/session62-skillsbench-reporting`
- PR: `#156` closed
- Committed diff: 12 files, 10 same / 2 different
- Remaining different files:
  - `engine/src/agent33/api/routes/benchmarks.py`
  - `engine/src/agent33/config.py`
- Assessment: `low-value salvage`
- Recommendation: this is close to fully preserved. Export the 2-file diff if you want to keep the abandoned variant, then delete.

## Decision Summary

### Keep Intact For Now

- `.claude/worktrees/agent-a5a29d23`
- `.claude/worktrees/agent-ab53cb8a`
- `.claude/worktrees/agent-ac4da72a`
- `.claude/worktrees/agent-af722d5d`
- `worktrees/session57-wave0-integration`
- `worktrees/session57-wave0-pr1`
- `worktrees/session57-wave1-pr1`
- `worktrees/phase28`
- `worktrees/phase38`
- `worktrees/phase43`
- `worktrees/session57-wave1-pr2`
- `worktrees/session57-wave1-live-base`
- `worktrees/session57-wave1-pr3`
- `worktrees/session58-phase26-wizard`
- `worktrees/session60-docs-validation`
- `worktrees/session61-phase38-docker-kernels`

### Salvage First, Then Delete

- `worktrees/nightly-merge-main`
- `worktrees/session57-main-ci-fix`
- `worktrees/session57-merge-check`

### Low-Value Salvage Candidates

- `worktrees/codex-main-final`
- `worktrees/session62-skillsbench-reporting`

## Recommended Next Cleanup Sequence

1. Export patch files for the low-value salvage candidates.
2. Decide whether the `nightly-merge-main` workflow tweak should be promoted into a real PR; if not, archive the patch and remove the worktree.
3. For the Session 57 and Session 59 prototype trees, either:
   - convert the unique deltas into patch bundles under `docs/research/cleanup-patches/`, or
   - explicitly declare them abandoned and delete them afterward.
4. Leave the large closed implementation branches alone until you decide whether they are historical artifacts worth retaining.
