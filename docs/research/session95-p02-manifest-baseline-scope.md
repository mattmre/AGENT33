# Session 95 P0.2 Manifest Baseline Scope

Date: 2026-03-20
Slice: `P0.2` initial Kubernetes manifests baseline

## Scope Lock

This slice adds the first plain-Kubernetes deployment baseline for the AGENT-33
engine and the minimum runtime-image packaging changes needed to keep that
baseline honest.

Included:

- `deploy/k8s/base/` manifest set
- base `kustomization.yaml`
- API, PostgreSQL, Redis, NATS, and Ollama manifests
- placeholder ConfigMap / Secret contract
- runtime image fix to include engine-local definitions and packs
- deployment README

Excluded:

- ingress
- autoscaling
- cloud-vendor packaging
- Prometheus / Grafana assets
- secret-manager integration
- frontend deployment

## Why Ollama Is Included

Although the earlier Session 94 memo listed a smaller manifest set, the current
runtime still assumes an internal Ollama endpoint by default:

- `ollama_base_url` defaults to `http://ollama:11434`
- runtime initialization uses Ollama-backed model and embedding paths
- `/health` probes the configured Ollama endpoint
- `engine/docker-compose.prod.yml` still includes an `ollama` service

Because of that, omitting Ollama here would create a deployment baseline that
looks complete but boots into a degraded configuration by default.

## Image Packaging Correction

The engine image previously copied only `src/` and `templates/`, but the app
expects additional on-disk runtime assets such as:

- `agent-definitions/`
- `workflow-definitions/`
- `tool-definitions/`
- `packs/`

This slice updates `engine/Dockerfile` to copy those directories into `/app` so
the Kubernetes deployment can run the same engine-local assets that the code
expects.

## Residual Risks

- The repo-root `core/workflows/` catalog is still outside the engine Docker
  build context, so this slice preserves the current image boundary rather than
  widening build context policy in the same PR.
- The committed Secret manifests intentionally use placeholder values and must
  be replaced before real production use.
- Local `kubectl apply --dry-run=client` still attempted cluster discovery in
  this environment, so render validation relies on `kubectl kustomize` and YAML
  parsing instead of a live schema fetch.
