# Session 99 P0.6 Operator Runbook Baseline Scope

## Baseline

- Merged baseline: `origin/main` at `77a9c71` after `P0.5`
- Clean worktree: `worktrees/session99-p06-runbook`
- Branch: `codex/session99-p06-runbook`

## Problem

The repo now ships a usable Kubernetes base, a production overlay, and the
first monitoring assets, but operators still do not have a single deployment
runbook that ties those pieces together into a concrete rollout and recovery
flow.

## Included Work

1. Add one production deployment runbook under `docs/operators/` for the
   current Kubernetes and monitoring baseline.
2. Cover the current single-instance rollout path only:
   - image/tag preparation
   - secret preparation
   - overlay apply
   - post-rollout health checks
   - monitoring checks
   - bounded rollback guidance
3. Cross-link the runbook from the existing deploy and monitoring docs.
4. Add focused validation so the runbook keeps referencing real repo files and
   current operator endpoints.

## Non-Goals

- Incident playbooks reserved for `P0.7`
- SLA / SLI policy and alert-threshold wiring reserved for `P0.8`
- New deployment manifests, Helm charts, ingress, autoscaling, or multi-replica
  guidance
- Prometheus or Grafana installation instructions beyond the already shipped
  importable assets

## Implementation Notes

- Match the style of existing operator/runbook docs:
  - `docs/operators/voice-daemon-runbook.md`
  - `docs/runbooks/jupyter-kernel-containers.md`
- Keep the rollback section honest about the current topology:
  - image/overlay rollback only
  - no claim that Kubernetes rollout is wired to the in-app release rollback
    APIs
- Prefer operator-check commands that can be executed against the current repo
  surfaces:
  - `kubectl rollout status`
  - `kubectl port-forward`
  - `curl /healthz`
  - `curl /readyz`
  - `curl /health`
  - `curl /metrics`
  - `curl /v1/dashboard/alerts`
  - `GET /v1/operator/status` with an authenticated token

## Validation Plan

- Add a focused docs validation test covering:
  - required runbook sections
  - expected endpoint references
  - expected repo path references that actually exist
- Run focused `pytest`, `ruff check`, `ruff format --check`, and
  `git diff --check`
