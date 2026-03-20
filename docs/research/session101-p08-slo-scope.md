# Session 101 P0.8 SLA / SLI Definition and Alert Wiring Scope

Date: 2026-03-20
Slice: `P0.8` SLA / SLI definition and alert wiring
Baseline: `origin/main` at `e0c03f6` after `P0.7`

## Goal

Define the first internal objective baseline against the metrics the repo
already exports, wire the thresholds that are honestly supportable today, and
document the objectives that remain deferred because the required Prometheus
series do not exist yet.

## Why This Slice Exists Now

The repo now has:

- a scrape-ready `/metrics` endpoint
- importable Prometheus and Grafana assets under `deploy/monitoring/`
- a deployment runbook
- incident playbooks tied to the current runtime and operator surfaces

What it did not yet have was a single place that says:

- which current alerts are formal objectives versus operational guardrails
- what the initial error-budget policy is
- which important reliability objectives remain deferred because the current
  metrics are missing

## Locked Inclusions

1. Add one service-objectives document under `docs/operators/`.
2. Keep all Prometheus rule wiring inside the existing
   `deploy/monitoring/prometheus/agent33-alerts.rules.yaml` file.
3. Keep the measurable objective set bounded to the current exported
   effort-routing metrics:
   - formal telemetry export reliability objective
   - high-effort ratio, cost drift, and token-budget context as guardrails
4. Update the monitoring and operator docs to cross-link the bounded objective
   baseline and the deferred-objective inventory.
5. Add focused validation for the docs and merged Prometheus rule file.

## Locked Non-Goals

- new exported application metrics
- new `ServiceMonitor`, `PodMonitor`, or `PrometheusRule` resources
- Grafana dashboard redesign
- request-availability, request-latency, readiness-rate, evaluation-regression,
  webhook-backlog, or connector-fleet SLOs backed by non-existent metrics
- assumptions about external Prometheus target labels such as
  `up{service="agent33-api"}`
- broad SRE boilerplate, customer SLA text, or on-call process redesign

## Current Measurable Versus Deferred Surface

### Can be wired now

- `effort_routing_export_failures_total`
- `effort_routing_high_effort_total`
- `effort_routing_decisions_total`
- `effort_routing_estimated_cost_usd_avg`
- `effort_routing_estimated_token_budget_avg`

### Must remain documented as deferred

- API availability success rate
- request latency
- dependency readiness success rate
- evaluation regression rate
- webhook backlog / dead-letter rate
- connector fleet reliability

Reason: the repo does not currently export request counters, request-duration
histograms, readiness counters, evaluation counters, webhook backlog metrics,
or connector fleet metrics through `/metrics`.

## Intended Deliverable Shape

- one operator doc with:
  - SLA / SLO / SLI boundary
  - current measurable objective inventory
  - error-budget policy
  - deferred-objective list with explicit reasons
  - threshold map tying Prometheus rules and in-app dashboard alerts together
- one merged Prometheus rule file with:
  - recording rules for the effort-routing telemetry objective and guardrails
  - the existing three alert names preserved
- focused tests validating:
  - parseability
  - expected recording-rule and alert names
  - required metric references only
  - explicit deferred-objective statements in the docs
