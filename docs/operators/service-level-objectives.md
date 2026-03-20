# Service Level Objectives

## Purpose

Define the first internal reliability objectives for the current AGENT-33
production baseline using only the monitoring surfaces that are already shipped
on `main`.

Use this document with:

- [`production-deployment-runbook.md`](production-deployment-runbook.md)
- [`incident-response-playbooks.md`](incident-response-playbooks.md)
- [`../../deploy/monitoring/README.md`](../../deploy/monitoring/README.md)
- [`../../deploy/monitoring/prometheus/agent33-alerts.rules.yaml`](../../deploy/monitoring/prometheus/agent33-alerts.rules.yaml)

## SLA, SLO, and SLI Boundary

- There is no external customer SLA defined in this repo today.
- `P0.8` establishes the first internal SLO baseline for the repo-owned
  effort-routing telemetry path.
- A metric only becomes a formal objective here if it is already exported by
  `GET /metrics` and can be wired without inventing new exporters, labels, or
  target assumptions.

## Current Measurable Objective Baseline

The current `/metrics` contract supports one narrow formal objective and a
small set of operational guardrails:

1. Formal internal objective:
   - effort-routing telemetry export reliability
2. Operational guardrails:
   - sustained high-effort routing ratio
   - persistent estimated cost lifetime-average elevation
   - in-app high-effort count and token-budget lifetime-average spot checks through
     `/v1/dashboard/alerts`

This slice does not claim user-facing API availability, latency, or dependency
readiness objectives because the repo does not export the required Prometheus
series yet.

## Formal Objective

### Effort Telemetry Export Reliability

Definition:

- SLI: rolling count of `effort_routing_export_failures_total`
- Recording rules:
  - `agent33:sli:effort_telemetry_export_failures:count_15m`
  - `agent33:sli:effort_telemetry_export_failures:count_28d`
- Window: `28d`
- Objective: `0` export failures over `28d`
- Error budget: `0` failures permitted over `28d`

This formal objective assumes Prometheus retains the exported time series for
at least `28d`. If retention is shorter, treat the `28d` rule as advisory and
do not claim the full objective window.

This objective is intentionally narrow. Export failures are treated as a
monitoring blind spot rather than a direct customer-facing outage, but they are
the only reliability signal that the current `/metrics` surface can measure
honestly end to end.

## Error Budget Policy

| Budget State | Policy |
| --- | --- |
| `0` failures in `28d` | normal deployment velocity |
| `> 0` failures in `28d` | investigate exporter health before risky monitoring changes |
| repeated `15m` failures | treat as active observability degradation and respond immediately |

The current baseline does not support classic burn-rate math because the
available metrics are counters and gauges for effort-routing behavior rather
than request-based availability ratios.

## Operational Guardrails

These stay alert-backed, but they are not promoted to full error-budgeted SLOs:

| Guardrail | Source | Threshold Surface |
| --- | --- | --- |
| high-effort routing ratio | `effort_routing_high_effort_total` and `effort_routing_decisions_total` | `agent33:sli:high_effort_routing_ratio:ratio_15m` |
| estimated cost lifetime average | `effort_routing_estimated_cost_usd_avg` | `agent33:sli:estimated_cost_usd_avg:max` |
| token-budget lifetime average | `effort_routing_estimated_token_budget_avg` | `agent33:sli:estimated_token_budget_avg:max` and `/v1/dashboard/alerts` |
| in-app high-effort count | in-memory routing summary | `AlertManager` threshold in `engine/src/agent33/main.py` |

The Prometheus guardrails and the in-app dashboard alerts are related, but they
are not identical. Prometheus is the production-facing alerting contract; the
dashboard route remains a local operator spot-check surface.

The exported `*_avg` series are process-lifetime averages computed by the
current metrics collector. They are useful for persistent elevation checks, but
they are not short-window drift or spike detectors.

## Deferred Objectives

The following objectives remain explicitly deferred in this slice:

| Objective | Deferred Reason |
| --- | --- |
| API availability success rate | `/metrics` does not export request counters or status-code totals |
| request latency | `/metrics` does not export a request-duration histogram |
| dependency readiness success rate | `/readyz` and `/health` exist as JSON endpoints, not Prometheus time series |
| evaluation regression rate | evaluation results live behind API routes, not `/metrics` |
| webhook backlog / dead-letter rate | webhook stats live behind admin routes, not `/metrics` |
| connector fleet reliability | connector monitoring is not exported through the public Prometheus surface |

These remain operationally important, but they require additional
instrumentation before they can become formal SLOs.

## Threshold Map

| Surface | Rule Family | Intent |
| --- | --- | --- |
| `deploy/monitoring/prometheus/agent33-alerts.rules.yaml` | recording rules + production alerts | formal telemetry objective and effort-routing guardrails |
| `/v1/dashboard/alerts` | in-app alert manager | local spot checks against the in-memory dashboard summary |
| `incident-response-playbooks.md` | operator procedures | manual handling for deferred evaluation and webhook incidents |

Current Prometheus-backed rule names:

- `Agent33EffortTelemetryExportFailures`
- `Agent33HighEffortRoutingRatio`
- `Agent33EstimatedCostDrift`

`Agent33EstimatedCostDrift` keeps its historical rule name for continuity, but
it currently alerts on persistent lifetime-average elevation rather than a true
rolling-window drift signal.

Current recording rules:

- `agent33:sli:effort_telemetry_export_failures:count_15m`
- `agent33:sli:effort_telemetry_export_failures:count_28d`
- `agent33:sli:high_effort_routing_ratio:ratio_15m`
- `agent33:sli:estimated_cost_usd_avg:max`
- `agent33:sli:estimated_token_budget_avg:max`

## Validation Sequence

1. Confirm the API service is scraped through `/metrics`.
2. Load `deploy/monitoring/prometheus/agent33-alerts.rules.yaml`.
3. Verify the recording rules and alert names above are present in Prometheus.
4. Confirm `/v1/dashboard/alerts` remains available for local operator checks.
5. Confirm evaluation and webhook incidents still route through the manual
   procedures in `incident-response-playbooks.md`.

## Notes

- This slice does not create a customer SLA.
- This slice does not claim user-facing availability or latency SLOs.
- Broader request, readiness, evaluation, webhook, and connector objectives
  remain deferred until the repo exports the required Prometheus metrics.
