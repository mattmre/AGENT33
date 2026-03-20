# Session 96 P0.3 Config / Secrets Scope

Date: 2026-03-20
Baseline: `origin/main` at `d3f2818` (`feat(deploy): add kubernetes manifest baseline (#233)`)
Target slice: `P0.3` deployment configuration and secrets wiring

## Goal

Turn the merged `deploy/k8s/base/` manifest baseline into a production-shaped
configuration contract without expanding into observability or cloud-specific
packaging.

## Included Work

1. Normalize the base config surface so non-secret runtime settings live in the
   API `ConfigMap` and secret material stays in example `Secret` manifests.
2. Remove the remaining duplicated password material from
   `postgres-secret.example.yaml` by dropping `DATABASE_URL` from the PostgreSQL
   example secret and relying on the API deployment's derived `DATABASE_URL`.
3. Add a production overlay under `deploy/k8s/overlays/production/` that
   captures the first rollout-specific configuration:
   - registry/image placeholder contract
   - single-instance production rollout settings that do not overpromise safe
     horizontal scaling before `P1.1` / `P1.2`
   - apply flow rooted in `kustomize`
4. Update deployment docs so bootstrap auth is treated as a temporary,
   operator-driven setup step rather than the default production posture.

## File Targets

- `deploy/k8s/base/api-configmap.yaml`
- `deploy/k8s/base/api-secret.example.yaml`
- `deploy/k8s/base/postgres-secret.example.yaml`
- `deploy/k8s/base/README.md`
- `deploy/k8s/overlays/production/kustomization.yaml`
- `deploy/k8s/overlays/production/api-deployment-patch.yaml`
- `deploy/k8s/overlays/production/README.md`

## Explicit Non-Goals

- metrics / Prometheus / Grafana (`P0.4` / `P0.5`)
- ingress or TLS termination
- autoscaling or PodDisruptionBudget tuning
- secret-manager integration beyond Kubernetes `Secret` manifests
- frontend deployment
- cloud-vendor annotations or Helm packaging

## Validation Plan

- `kubectl kustomize deploy/k8s/base`
- `kubectl kustomize deploy/k8s/overlays/production`
- YAML parse of all manifest files under `deploy/k8s/base` and
  `deploy/k8s/overlays/production`
- `git diff --check`

## Notes

- The merged `P0.2` baseline already derives `DATABASE_URL` in
  `api-deployment.yaml`; the remaining duplicated key is contract drift, not a
  runtime blocker.
- `AUTH_BOOTSTRAP_ENABLED`, `AUTH_BOOTSTRAP_ADMIN_USERNAME`, and
  `OPENAI_BASE_URL` are configuration, not secret material, and should move out
  of the example API secret.
