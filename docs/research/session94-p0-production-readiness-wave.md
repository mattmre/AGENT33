# Session 94 Production Readiness Wave

Date: 2026-03-19
Scope: `P0.1` implementation plus `P0.2a` / `P0.3a` research freeze

## Current State

- The production runtime image is built from `engine/Dockerfile` and consumed by `engine/docker-compose.prod.yml`.
- The repo already runs a Trivy container-image scan in `.github/workflows/security-scan.yml`, but it only enforces generic severity gates and did not explicitly verify the known libc finding called out in `docs/next-session.md`.
- There are no checked-in Kubernetes manifests, Helm charts, or deployment overlays in the repo today.
- Runtime configuration is already environment-variable driven from `engine/src/agent33/config.py` and Compose files, which makes a manifest-first deployment path viable without reworking application config.

## P0.1 Decision

Implement `P0.1` as a narrow image-hardening slice:

1. Pin the runtime image to a fixed Python slim Trivy-safe baseline on Debian Trixie.
2. Force CI image builds to pull the current base image during the security scan.
3. Add a targeted image-scan assertion that fails if `CVE-2026-0861` appears in the built runtime image.

Included files:

- `engine/Dockerfile`
- `.github/workflows/security-scan.yml`

Explicit non-goals:

- Kubernetes manifests
- rollout overlays
- secret-manager integration
- metrics, dashboards, or alerting

## P0.2a Decision

Use plain Kubernetes manifests as the first deployment target decision.

Recommended structure for the next slice:

- `deploy/k8s/base/namespace.yaml`
- `deploy/k8s/base/api-deployment.yaml`
- `deploy/k8s/base/api-service.yaml`
- `deploy/k8s/base/postgres-statefulset.yaml`
- `deploy/k8s/base/redis-deployment.yaml`
- `deploy/k8s/base/nats-deployment.yaml`
- `deploy/k8s/base/kustomization.yaml`

Rationale:

- The repo has no deployment baseline yet, so raw manifests keep the first deployable shape reviewable.
- Helm or cloud-vendor packaging would add policy and template surface before the base topology is agreed.
- Kustomize can still be added later without discarding a manifest-first baseline.

## P0.3a Decision

Keep the production config model environment-variable based, split into:

- non-secret runtime settings in a Kubernetes `ConfigMap`
- credentials and tokens in a Kubernetes `Secret`
- local `.env` support unchanged for developer workflows

Policy decisions for the next slice:

- no committed real secret values
- one shared manifest contract for env var names, reusing the existing `engine/src/agent33/config.py` surface
- secret source integration beyond Kubernetes `Secret` objects stays out of the first deployment PR

## Risks To Watch

- `engine/docker-compose.prod.yml` is the only production-shaped asset today, so the first manifest slice must explicitly map Compose-only assumptions like health checks, resource hints, and inter-service URLs.
- `engine/Dockerfile.airllm` and GPU/integration services remain outside this first runtime-image slice; do not expand the P0.1 PR to cover those images.
- The current merged `origin/main` handoff docs are stale relative to the root planning files, so session tracking must be refreshed separately from the clean implementation worktree.

## Existing References

- `docs/next-session.md`
- `CLAUDE.md`
- `engine/Dockerfile`
- `engine/docker-compose.yml`
- `engine/docker-compose.prod.yml`
- `.github/workflows/security-scan.yml`
- `docs/research/repo_dossiers/trivy.md`
