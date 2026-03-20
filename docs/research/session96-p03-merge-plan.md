# Session 96 P0.3 Merge Plan

Date: 2026-03-20
PR target: `P0.3` deployment configuration and secrets wiring

## Review Focus

1. Confirm the base config surface now matches the `P0.3a` policy:
   - non-secret settings in `api-configmap.yaml`
   - secret material only in example `Secret` manifests
2. Confirm `postgres-secret.example.yaml` no longer duplicates password material
   inside `DATABASE_URL`.
3. Confirm the new production overlay stays bounded to rollout/image config and
   does not drift into ingress, metrics, or cloud-specific packaging.
4. Confirm bootstrap-auth guidance is explicit and production-safe.

## Validation Completed

- `kubectl kustomize deploy/k8s/base`
- `kubectl kustomize deploy/k8s/overlays/production`
- YAML parse of all manifest files under `deploy/k8s/base` and
  `deploy/k8s/overlays/production`
- `git diff --check`

## Merge Gates

1. Self-review the config/secret classification and production-overlay scope.
2. Open PR for `P0.3` only.
3. Address any review comments before starting `P0.4`.
4. After merge, create a fresh `origin/main` verification worktree and rerun:
   - `kubectl kustomize deploy/k8s/base`
   - `kubectl kustomize deploy/k8s/overlays/production`
   - YAML parse validation
5. Only after post-merge verification should the next slice move to `P0.4`.
