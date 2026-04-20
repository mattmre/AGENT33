# Session 129 Slice 2: Operator Docs Review Debt

**Date:** 2026-04-20  
**Scope:** final pre-marketplace remediation for stale roadmap/handoff docs and
remaining operator-facing documentation drift on top of merged baseline
`8f1cbe3` (PR `#411`).

## Why this slice exists

PRs `#409`, `#410`, and `#411` completed the functional post-merge remediation
work, but the repo's operator-facing docs and queue trackers were still pinned
to the older `#408` baseline. That leaves recovery paths, onboarding guidance,
and Ollama instructions slightly out of sync with the real merged state.

This slice intentionally stays docs/operator-only so the next product slice
(pack marketplace UI) starts from a clean, trustworthy handoff layer.

## Inputs reviewed

- `docs/next-session.md`
- `docs/phases/PHASE-PLAN-POST-P72-2026.md`
- `docs/sessions/session128-task-plan.md`
- `docs/sessions/session-129-2026-04-20.md`
- `docs/research/session128-postmerge-review-remediation-plan.md`
- `docs/ONBOARDING.md`
- `docs/getting-started.md`
- `frontend/README.md`
- `engine/README.md`
- `docs/operators/production-deployment-runbook.md`
- `docs/operators/incident-response-playbooks.md`
- `deploy/k8s/base/README.md`
- `deploy/k8s/base/api-configmap.yaml`
- `deploy/k8s/base/ollama-deployment.yaml`

## Findings

### 1. Queue and handoff state drift

The repo handoff files still described `#408` as the latest merged baseline and
still pointed recovery to Session 128 state, even though:

- `#409` lifecycle cleanup is merged
- `#410` P-ENV/docs reliability is merged
- `#411` P-PACK hardening is merged and verified

This makes recovery unnecessarily error-prone and risks starting marketplace
work before the last docs/operator cleanup lands.

### 2. Operator docs still carry small launch/P-ENV drift

The remaining operator-facing issues are narrow:

- `docs/ONBOARDING.md` still includes raw `docs/...` bullets instead of proper
  relative links
- `docs/getting-started.md` does not clearly call out the default
  `OLLAMA_BASE_URL=http://host.docker.internal:11434` contract before the
  bundled-Ollama override path
- `frontend/README.md` points vaguely at `.env.example` for bootstrap
  credentials instead of the actual `engine/.env` path used locally
- several operator/runtime docs still reference untagged `llama3.2` instead of
  the repo's current default `llama3.2:3b`
- the checked-in k8s base config still used untagged `llama3.2` in both
  `OLLAMA_DEFAULT_MODEL` and the Ollama readiness probe

### 3. Duplicate Session 129 note remains on main

Both of these files exist:

- `docs/sessions/session-129-2026-04-19.md`
- `docs/sessions/session-129-2026-04-20.md`

The `2026-04-20` note is the intended canonical Session 129 record; the
`2026-04-19` duplicate should be removed to keep session indexing/search clean.

### 4. Verification environment caveat

Fresh-main validation in this environment must pin `PYTHONPATH` to the active
worktree's `engine\src`. The editable install otherwise resolves `agent33` from
the stale root checkout and can produce false regressions while validating a
fresh worktree.

## Scope lock

Included:

- queue/handoff sync through `#411`
- operator-facing documentation wording and link cleanup
- Session 129 note dedupe
- tracker updates (`task_plan.md`, `progress.md`, `findings.md`) required for
  clean recovery

Excluded:

- pack marketplace UI
- community submissions
- new runtime code
- security scan / ruleset remediation
- broader model-name normalization outside the touched operator docs

## Validation plan

Use content validation plus targeted startup-contract tests only if the docs
changes widen into runtime/config edits:

```bash
rg -n "#408|#409|#410|#411|943b683|0918881|5de4f78|8f1cbe3" docs/next-session.md docs/phases/PHASE-PLAN-POST-P72-2026.md docs/sessions/session128-task-plan.md task_plan.md progress.md
rg -n "docs/walkthroughs.md|docs/use-cases.md|llama3.2(?!:3b)|engine/.env.example|host.docker.internal:11434" docs/ONBOARDING.md docs/getting-started.md frontend/README.md engine/README.md docs/operators/production-deployment-runbook.md docs/operators/incident-response-playbooks.md deploy/k8s/base/README.md
```

If any runtime/config source files become touched, extend validation with:

```bash
PYTHONPATH=C:\GitHub\repos\AGENT33\worktrees\session129-s2-operator-docs\engine\src pytest engine/tests/test_env_detect.py engine/tests/test_ollama_setup.py engine/tests/test_wizard.py engine/tests/test_bootstrap.py engine/tests/test_diagnose.py --no-cov -q
```
