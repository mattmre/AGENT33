# AGENT-33 Kubernetes Production Overlay

This overlay applies the first production-shaped rollout settings on top of the
plain manifest baseline in `deploy/k8s/base/`.

## What Changes

- API image switches from the local baseline placeholder to a registry-style
  placeholder:
  - `ghcr.io/mattmre/agent33:replace-with-release-tag`
- API rollout becomes production-oriented:
  - `replicas: 2`
  - rolling update with `maxUnavailable: 0`
  - `minReadySeconds: 10`
  - `terminationGracePeriodSeconds: 30`

## Secret Preparation

Create real secrets from the base examples before applying this overlay:

- `deploy/k8s/base/api-secret.example.yaml`
- `deploy/k8s/base/postgres-secret.example.yaml`

Bootstrap auth is disabled by default. If you need initial admin bootstrap:

1. Set `AUTH_BOOTSTRAP_ENABLED` to `true` in the rendered API config.
2. Set a strong `AUTH_BOOTSTRAP_ADMIN_PASSWORD` in the API secret.
3. Mint the first admin token.
4. Restore `AUTH_BOOTSTRAP_ENABLED=false`.

## Apply

1. Replace the API image placeholder in `api-deployment-patch.yaml` with your
   immutable release tag or digest.
2. Create and apply real Kubernetes secrets.
3. Apply the production overlay.

```bash
kubectl apply -f /tmp/postgres-secret.yaml
kubectl apply -f /tmp/api-secret.yaml
kubectl apply -k deploy/k8s/overlays/production
```
