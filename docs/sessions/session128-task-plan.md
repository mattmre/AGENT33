# Session 128 — Master Task Plan

**Created:** 2026-04-18  
**Owner:** Session 128  
**Scope:** merged-review remediation from PRs `#406`-`#408` plus the remaining
POST-CLUSTER roadmap slices

---

## Current State

- `origin/main` is at `943b683` after PR `#408`.
- There are `0` open PRs on `mattmre/AGENT33`.
- POST-1 through POST-4 are COMPLETE on `main`.
- POST-CLUSTER public launch preparation is COMPLETE in PR `#407`.
- POST-CLUSTER P-ENV v2 is COMPLETE in PR `#408`.
- The remaining roadmap slices are:
  - Pack marketplace web UI
  - Community submissions
- Before those slices continue, the merged review feedback from PRs `#406`-`#408`
  must be remediated in follow-up PRs.

## Session 128 Execution Queue

| # | Task | Type | Branch / Worktree | Depends On | Status |
|---|------|------|-------------------|------------|--------|
| R0 | Audit merged review feedback and planning drift | research/docs | `session128-s1-review-remediation` | — | complete |
| R1 | Follow-up PR: pack/session lifecycle hardening | code/test | `session128-s1-review-remediation` | R0 | validation complete, PR prep active |
| R2 | Follow-up PR: P-ENV v2 and launch-doc reliability fixes | code/test/docs | `session128-s2-penv2-hardening` | R1 merged | queued |
| R3 | POST-CLUSTER — Pack marketplace web UI | product/frontend | `session128-s3-pack-marketplace` | R2 merged | queued |
| R4 | POST-CLUSTER — Community submissions | ecosystem/runtime | `session128-s4-community-submissions` | R3 merged | queued |

## Resume Protocol

If execution stops mid-slice:

1. Read `task_plan.md`, `progress.md`, and this file.
2. Read `docs/research/session128-postmerge-review-remediation-plan.md`.
3. Check which queue item is still active.
4. Inspect the referenced worktree and run `git status`.
5. Determine the current phase:
   - `research`
   - `scope_lock`
   - `implementation`
   - `validation`
   - `pr_open`
   - `ci_wait`
   - `merged`
   - `verified`
6. Continue from the first incomplete step for that slice only.

---

## R1 — Follow-Up PR: Pack/Session Lifecycle Hardening

**Goal:** clear session-scoped pack tracking when sessions reach terminal
lifecycle states while preserving suspended sessions that must remain resumable.

**Concrete scope:**
- integrate `PackRegistry.clear_session_state()` with terminal session lifecycle
  paths
- ensure suspended sessions keep their session-scoped pack state
- clear tracking on archive or equivalent terminal cleanup paths
- add focused regression tests

**Primary files:**
- `engine/src/agent33/packs/registry.py`
- `engine/src/agent33/sessions/service.py`
- `engine/src/agent33/sessions/archive.py`
- relevant session / packs tests

**Validation target:**
- focused pytest for session lifecycle and session-scoped pack behavior
- `ruff check`
- `ruff format --check`
- `mypy` on touched Python files

**Implemented:**
- added a narrow `session_cleanup_callback` to `OperatorSessionService`
- wired `pack_registry.clear_session_state` from `main.py`
- clear terminal session state on completed end, archive, and archived cleanup
- preserve session-scoped pack state for suspended sessions
- fixed archive logging to report the real previous status

**Validation completed:**
- `PYTHONPATH=C:\GitHub\repos\AGENT33\worktrees\session128-s1-review-remediation\engine\src pytest engine/tests/test_phase44_session_service.py engine/tests/test_session_catalog.py --no-cov -q`
- `PYTHONPATH=C:\GitHub\repos\AGENT33\worktrees\session128-s1-review-remediation\engine\src pytest engine/tests/test_phase44_integration.py --no-cov -q`
- `PYTHONPATH=C:\GitHub\repos\AGENT33\worktrees\session128-s1-review-remediation\engine\src pytest engine/tests/test_integration_wiring.py -k "lifespan or expected_attributes" --no-cov -q`
- `PYTHONPATH=C:\GitHub\repos\AGENT33\worktrees\session128-s1-review-remediation\engine\src ruff check engine/src/agent33/sessions/service.py engine/src/agent33/sessions/archive.py engine/src/agent33/main.py engine/tests/test_phase44_session_service.py engine/tests/test_session_catalog.py`
- `PYTHONPATH=C:\GitHub\repos\AGENT33\worktrees\session128-s1-review-remediation\engine\src ruff format --check engine/src/agent33/sessions/service.py engine/src/agent33/sessions/archive.py engine/src/agent33/main.py engine/tests/test_phase44_session_service.py engine/tests/test_session_catalog.py`
- `PYTHONPATH=C:\GitHub\repos\AGENT33\worktrees\session128-s1-review-remediation\engine\src mypy engine/src/agent33/sessions/service.py engine/src/agent33/sessions/archive.py engine/src/agent33/main.py --config-file engine/pyproject.toml`

---

## R2 — Follow-Up PR: P-ENV V2 And Launch-Doc Reliability Fixes

**Goal:** make the P-ENV v2 bootstrap path internally consistent and repair the
operator-facing correctness issues left by PRs `#407` and `#408`.

**Concrete scope:**
- align runtime env-file loading with wizard/bootstrap output
- standardize the canonical Ollama default model string across config, CLI, and docs
- fix bundled-start docs so they describe a real first-time startup path
- narrow the broad `TypeError` fallback in wizard env refresh
- surface bundled `docker compose` stderr/stdout when startup fails
- raise or parameterize the Ollama pull timeout for larger recommended models

**Primary files:**
- `engine/src/agent33/config.py`
- `engine/src/agent33/env/detect.py`
- `engine/src/agent33/env/ollama_setup.py`
- `engine/src/agent33/cli/wizard.py`
- `engine/src/agent33/cli/bootstrap.py`
- setup and onboarding docs touched by `#407` / `#408`

---

## R3 — POST-CLUSTER Pack Marketplace Web UI

**Goal:** implement the remaining marketplace UI slice from fresh `origin/main`
after the remediation PRs land.

**Notes:**
- the clean forward-looking baseline remains
  `worktrees/session127-s12-pack-marketplace`
- start from a fresh worktree again after R2 merges

---

## R4 — POST-CLUSTER Community Submissions

**Goal:** implement the community-submission slice only after the marketplace UI
and approval flow are in place.

---

## Merge Plan

1. R1 — pack/session lifecycle hardening
2. R2 — P-ENV v2 and launch-doc reliability fixes
3. R3 — pack marketplace web UI
4. R4 — community submissions

Every slice must:

- start from fresh `origin/main`
- use one fresh agent/worktree
- open one PR
- merge only after green targeted validation and review
- run a fresh-main verification pass before the next slice begins
