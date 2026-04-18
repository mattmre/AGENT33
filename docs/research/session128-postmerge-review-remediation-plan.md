# Session 128 Research: Post-Merge Review Remediation Plan

**Date:** 2026-04-18  
**Scope:** audit merged review feedback from PRs `#406`, `#407`, and `#408`, then
sequence the required follow-up work before the remaining POST-CLUSTER slices
continue

## Decision

There are no open PRs to review. The immediate queue shifts to post-merge
remediation for the actionable review findings that were left behind after the
recent merge wave.

Those fixes should land before the remaining roadmap work (`Pack marketplace web
UI`, then `Community submissions`) so the next slices start from a stable,
accurate baseline.

## Baseline Reviewed

- `docs/next-session.md`
- `docs/phases/PHASE-PLAN-POST-P72-2026.md`
- `task_plan.md`
- `progress.md`
- `docs/sessions/session126-task-plan.md`
- PR review threads for `#406`, `#407`, and `#408`
- `engine/src/agent33/packs/registry.py`
- `engine/src/agent33/api/routes/agents.py`
- `engine/src/agent33/sessions/service.py`
- `engine/src/agent33/sessions/archive.py`
- `engine/src/agent33/env/detect.py`
- `engine/src/agent33/env/ollama_setup.py`
- `engine/src/agent33/cli/wizard.py`
- `engine/src/agent33/config.py`
- launch and setup documentation touched by `#407` and `#408`

## Findings

1. **Pack session-state cleanup is incomplete.**
   `PackRegistry.clear_session_state()` exists, but it is only reached when the
   last session pack is explicitly disabled. Terminal session lifecycle paths
   do not clear the session-scoped pack tracking dictionaries.

2. **P-ENV v2 has an env-file contract mismatch.**
   The wizard/bootstrap happy path writes `.env.local`, but runtime settings
   still default to `.env`. That means the new first-run flow can report success
   while `agent33 start` ignores the generated settings.

3. **P-ENV v2 model naming drifted across runtime and docs.**
   The implementation moved toward tagged model names like `llama3.2:3b`, while
   config defaults and some fallback docs still reference untagged `llama3.2`.

4. **Launch/bootstrap docs still have a few operator-facing correctness issues.**
   The bundled-Ollama startup command in the docs starts only the Ollama
   service, not the stack described by the guide. Some documentation links and
   credential references are also still rough.

5. **The root planning docs are stale.**
   The root checkout still points at the pre-`#405` state, while `origin/main`
   is already through `#408`.

## Execution Order

1. **PR 1: pack/session lifecycle hardening**
   - Wire pack state cleanup into terminal session lifecycle paths
   - Preserve suspended-session resumability
   - Add focused regression tests

2. **PR 2: P-ENV v2 and launch-doc reliability fixes**
   - Unify env-file consumption
   - Standardize canonical default model naming
   - Improve bundled-start diagnostics and docs
   - Tighten the wizard env-refresh error handling

3. **PR 3: POST-CLUSTER pack marketplace web UI**

4. **PR 4: POST-CLUSTER community submissions**

## Non-Goals

- No reopening of POST-4 roadmap decisions that are already locked
- No broad roadmap reshuffle beyond inserting the necessary remediation PRs
- No community-submission work before the pack marketplace slice is complete
