# Session 116 P4 Operator Verification and Process-Registry Runbooks

## Baseline

- Merged baseline: `origin/main` at `8e0a26e`
- Clean worktree: `worktrees/session116-p4-operator-runbooks`
- Branch: `codex/session116-p4-operator-runbooks`

## Problem

The repo already ships the operator control plane, the managed process service,
and platform backup verification surfaces, but the operational steps for using
them are still scattered across prior scope notes and endpoint tests.

Cluster `0.4` should convert those already-shipped capabilities into canonical,
low-friction runbooks without broadening into new operator product work.

## Included Work

1. Add one process-registry runbook under `docs/operators/` that documents:
   - the current `/v1/processes` contract
   - lifecycle states that operators can actually observe
   - the restart-recovery path for `interrupted` processes
   - one bounded cleanup command
2. Add one operator verification runbook under `docs/operators/` that documents:
   - the canonical authenticated verification order for `/v1/operator/status`
     and `/v1/operator/doctor`
   - the highest-risk adjacent operator surfaces already shipped in this repo:
     managed-process verification and backup verification / restore preview
   - when the bounded `/v1/operator/reset` path is appropriate
3. Cross-link the new runbooks from the existing deployment and incident docs.
4. Add focused docs validation so the runbooks keep referencing real repo files
   and current operator/process/backup endpoints.

## Non-Goals

- New operator UX or dashboard work
- New process-manager endpoints or redesign
- New backup or restore execution features
- Workflow UI changes or broader operator reconciliation work from later clusters

## Implementation Notes

- Match the style of the existing operator docs:
  - `docs/operators/production-deployment-runbook.md`
  - `docs/operators/incident-response-playbooks.md`
  - `docs/operators/voice-daemon-runbook.md`
- Keep commands short and stable:
  - `curl /v1/operator/status`
  - `curl /v1/operator/doctor`
  - `curl /v1/processes`
  - `curl /v1/backups/*`
- Be explicit that managed processes recovered after restart are marked
  `interrupted`; the system does not claim live handle reattachment.

## Validation Plan

- Add focused `pytest` docs validation for the new runbooks
- Extend operator-doc cross-reference validation to include the new files
- Run targeted `ruff check`, `ruff format --check`, and `git diff --check`
