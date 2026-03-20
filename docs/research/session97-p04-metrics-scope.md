# Session 97 P0.4 Metrics and Scrape Surface Scope

## Baseline

- Merged baseline: `origin/main` at `db59c44` after `P0.3`
- Clean worktree: `worktrees/session97-p04-metrics`
- Branch: `codex/session97-p04-metrics`

## Problem

The repo already collects runtime counters and observations in
`engine/src/agent33/observability/metrics.py`, but the only exposed route is the
JSON dashboard summary at `GET /v1/dashboard/metrics`. The Kubernetes API
`Service` also lacks scrape metadata, so the current deployment baseline cannot
be scraped by a standard Prometheus-style collector without custom knowledge.

## Included Work

1. Add a public Prometheus-format `GET /metrics` endpoint.
2. Keep `GET /v1/dashboard/metrics` unchanged as the existing JSON contract.
3. Exempt `/metrics` from auth and rate limiting.
4. Add scrape annotations to `deploy/k8s/base/api-service.yaml`.
5. Update deployment/API documentation for the route split.
6. Add focused tests for endpoint shape and public access.

## Non-Goals

- Grafana dashboards or dashboard JSON redesign
- Alert rules or alert wiring
- Prometheus Operator `ServiceMonitor` / `PodMonitor` resources
- Replacing the in-memory collector with a new metrics backend
- Broader observability or tracing refactors

## Implementation Notes

- Reuse the existing in-memory `MetricsCollector`; do not add a new dependency
  unless the current collector proves insufficient for a small text renderer.
- Prefer a top-level `/metrics` route so scrape configuration is conventional
  and does not overload the dashboard prefix semantics.
- Keep the public-access exception explicit in middleware rather than relying on
  dashboard-prefix bypass behavior.

## Validation Plan

- Focused pytest coverage for:
  - public `/metrics`
  - unchanged `/v1/dashboard/metrics`
  - auth/rate-limit bypass behavior for `/metrics`
- `ruff check` on touched Python files
- `ruff format --check` on touched Python files
- `kubectl kustomize deploy/k8s/base`
- YAML parse for the touched manifest/docs surface if needed
