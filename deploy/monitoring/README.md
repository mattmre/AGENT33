# AGENT-33 Monitoring Assets

This directory contains the first production-facing monitoring artifacts for the
merged `/metrics` contract that landed in `P0.4`.

## Contents

- `grafana/agent33-production-overview.dashboard.json`
  - importable Grafana dashboard focused on current effort-routing and scrape
    health metrics
- `prometheus/agent33-alerts.rules.yaml`
  - generic Prometheus alert rules for the current effort-routing metrics

## Assumptions

- The API service is already scrape-ready through the merged `P0.4` baseline:
  - `GET /metrics`
  - `deploy/k8s/base/api-service.yaml` scrape annotations
- These assets are intentionally generic.
  - They do not assume a specific Prometheus Operator installation.
  - They do not deploy Grafana or Prometheus for you.

## Grafana Import

1. Open Grafana.
2. Import `grafana/agent33-production-overview.dashboard.json`.
3. Bind the `DS_PROMETHEUS` datasource variable to your Prometheus datasource.

The dashboard focuses on the metrics currently exported by AGENT-33:

- `effort_routing_decisions_total`
- `effort_routing_high_effort_total`
- `effort_routing_export_failures_total`
- `effort_routing_estimated_cost_usd_*`
- `effort_routing_estimated_token_budget_*`

## Prometheus Rule Loading

Load `prometheus/agent33-alerts.rules.yaml` through your Prometheus
`rule_files` configuration or transform it into your platform's equivalent
resource if you use a controller/operator-based installation.

The first rule set is intentionally small:

- telemetry export failures
- sustained high-effort routing ratio
- sustained cost drift

## Validation

For ad hoc verification after import:

- `GET /metrics` validates live scrape output
- `GET /v1/dashboard/alerts` shows the app's internal alert evaluation against
  the in-memory dashboard summary

The internal `/v1/dashboard/alerts` route is useful for operator spot checks,
but the Prometheus rule file here is the production-facing alerting asset for
this slice.

For the repo's current rollout, health-check, and rollback procedure, use:

- `docs/operators/production-deployment-runbook.md`

For the current incident triage procedures tied to these monitoring assets, use:

- `docs/operators/incident-response-playbooks.md`
