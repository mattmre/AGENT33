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
- Base `ConfigMap` and placeholder `Secret` manifests

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

The committed Secret manifests contain placeholder values so the base remains
structurally deployable. Replace them before real production use.

The PostgreSQL Secret currently carries both:

- discrete database fields for the Postgres container
- `DATABASE_URL` for the API

This duplication is intentional for the first baseline and will be cleaned up in
the follow-up config/secrets wiring slice.

## Apply

```bash
kubectl apply -k deploy/k8s/base
```

## Notes

- The current runtime still assumes an internal Ollama endpoint by default.
- `/health` is the current API probe surface.
- `/v1/dashboard/metrics` is JSON, not Prometheus exposition format.
