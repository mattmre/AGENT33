# Session 95 P0.2 Merge Plan

Date: 2026-03-20
PR target: `P0.2` initial Kubernetes manifests baseline

## Review Focus

1. Confirm the manifest set matches the current runtime dependency boundary:
   API, PostgreSQL, Redis, NATS, Ollama, and SearXNG.
2. Confirm the Docker image now contains engine-local runtime assets required by
   startup and operator flows.
3. Confirm the example-secret and bootstrap-auth contract is explicit and
   documented rather than silently relying on local `.env` behavior.
4. Confirm this PR does not drift into `P0.3` secret-provider policy or `P0.4`
   observability/exporter work.

## Validation Completed

- `kubectl kustomize deploy/k8s/base`
- PyYAML parse of all manifest files under `deploy/k8s/base`
- `git diff --check`
- `docker build -t agent33:p02-manifest-baseline ./engine`
- container filesystem check for:
  - `/app/agent-definitions`
  - `/app/workflow-definitions`
  - `/app/tool-definitions`
  - `/app/packs`

## Known Limitation During Validation

- `kubectl apply --dry-run=client -k deploy/k8s/base` still attempted server
  discovery against the local kubeconfig target and failed because no cluster
  was reachable in this environment. This is an environment limitation, not a
  manifest render failure.

## Merge Gates

1. Self-review manifest topology and placeholder-secret documentation.
2. Open PR for `P0.2` only.
3. Address review comments before any `P0.3` work begins.
4. After merge, create a fresh `origin/main` worktree and rerun:
   - `kubectl kustomize deploy/k8s/base`
   - YAML parse validation
   - `docker build -t agent33:p02-postmerge ./engine`
   - runtime asset presence check inside the built image
5. Only after post-merge verification should the next slice move to `P0.3`.
