# AGENT-33 Kubernetes Base

This directory contains the first plain-Kubernetes deployment baseline for the
AGENT-33 engine.

## Scope

Included in this base:

- API deployment and ClusterIP service
- PostgreSQL stateful service
- Redis deployment and service
- NATS deployment and service
- Ollama deployment and service
- SearXNG deployment and service
- Base `ConfigMap` plus example Secret manifests

Deferred to later slices:

- ingress
- autoscaling
- Prometheus / Grafana assets
- cloud-specific annotations
- secret-manager integration
- frontend deployment

## Image Contract

The API deployment references `agent33:latest`.

Build it locally before applying the base:

```bash
docker build -t agent33:latest ./engine
```

If your cluster cannot use local Docker images directly, retag and push the
image to your registry, then update `api-deployment.yaml` before applying.

## Secret Contract

The repo ships example Secret manifests only:

- `api-secret.example.yaml`
- `postgres-secret.example.yaml`

Create real secrets named `agent33-api-secrets` and `agent33-postgres-secrets`
before applying this base. The examples show the required keys but are not wired
into `kustomization.yaml` so the repo does not ship weak production secrets by
default.

The PostgreSQL secret contract currently carries both:

- discrete database fields for the Postgres container
- `DATABASE_URL` for the API

This duplication is intentional for the first baseline and will be cleaned up in
the follow-up config/secrets wiring slice.

## Apply

1. Copy each example Secret manifest and replace every placeholder value.
2. Apply the edited Secret manifests.
3. Apply the base Kustomize resources.

```bash
cp deploy/k8s/base/postgres-secret.example.yaml /tmp/postgres-secret.yaml
cp deploy/k8s/base/api-secret.example.yaml /tmp/api-secret.yaml

# Edit /tmp/postgres-secret.yaml and /tmp/api-secret.yaml before applying.

kubectl apply -f /tmp/postgres-secret.yaml
kubectl apply -f /tmp/api-secret.yaml
kubectl apply -k deploy/k8s/base
```

## Notes

- The current runtime still assumes an internal Ollama endpoint by default.
- The current runtime also assumes a reachable `SEARXNG_URL`, so this base now
  includes SearXNG to preserve built-in search behavior.
- The example API secret enables bootstrap auth by default so a fresh cluster
  can mint the first admin token. Rotate the bootstrap password immediately and
  disable bootstrap auth after initial access is established.
- Ollama readiness now requires the `llama3.2` model to be present. After the
  daemon starts, pull it with:

```bash
kubectl exec -n agent33 deploy/ollama -- ollama pull llama3.2
```

- `/health` is the current API probe surface.
- `/v1/dashboard/metrics` is JSON, not Prometheus exposition format.
