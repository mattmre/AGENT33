# Session 98 P0.5 Dashboards and Alert Rules Scope

## Baseline

- Merged baseline: `origin/main` at `969178f` after `P0.4`
- Clean worktree: `worktrees/session98-p05-dashboards`
- Branch: `codex/session98-p05-dashboards`

## Problem

The repo now exposes a real scrape surface at `GET /metrics`, but there are no
checked-in monitoring artifacts that operators can import into Grafana or
Prometheus. The current backend dashboard routes are useful for ad hoc JSON/HTML
inspection, but they are not the production-facing dashboard and alert assets
called for in `P0.5`.

## Included Work

1. Add a checked-in Grafana dashboard JSON that visualizes the current
   effort-routing metrics and scrape health.
2. Add a generic Prometheus alert-rule YAML file for the first production
   operator alerts against the current metrics contract.
3. Add `deploy/monitoring/` documentation describing how operators should load
   the dashboard and rule assets.
4. Add focused validation tests so the JSON/YAML assets remain parseable and
   continue referencing the intended metrics.

## Non-Goals

- Deploying Prometheus or Grafana infrastructure
- Prometheus Operator `ServiceMonitor`, `PodMonitor`, or `PrometheusRule` CRDs
- Reopening the `/metrics` route or collector design from `P0.4`
- SLI/SLO policy and paging ownership work reserved for `P0.8`
- Broad UI redesign of the existing HTML dashboard

## Implementation Notes

- Keep the monitoring assets generic and importable:
  - Grafana dashboard as plain JSON
  - Prometheus rules as plain `groups:` YAML
- Build the first alert rules only on metrics already exposed today:
  - `effort_routing_decisions_total`
  - `effort_routing_high_effort_total`
  - `effort_routing_export_failures_total`
  - `effort_routing_estimated_cost_usd_*`
- Avoid environment-specific label assumptions that would force a specific job or
  namespace name into every rule.

## Validation Plan

- Focused asset validation covering:
  - Grafana dashboard JSON parse
  - Prometheus rule YAML parse
  - expected metric references in both assets
- `ruff check` and `ruff format --check` on any new Python tests
- `pytest` for the focused asset validation file
- `git diff --check`
