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
- `P0.8` established the first internal SLO baseline for the repo-owned
  effort-routing telemetry path.
- `P3.3` adds HTTP availability and latency SLOs backed by the new
  `http_requests_total` counter and `http_request_duration_seconds`
  observation emitted by `HTTPMetricsMiddleware`.
- `P3.10` adds webhook delivery reliability SLO backed by
  `webhook_delivery_total`, `webhook_delivery_failures_total`,
  `dead_letter_queue_captures_total` counters and
  `webhook_delivery_duration_seconds`, `dead_letter_queue_depth` observations
  emitted by `WebhookDeliveryManager` and `DeadLetterQueue`.
- A metric only becomes a formal objective here if it is already exported by
  `GET /metrics` and can be wired without inventing new exporters, labels, or
  target assumptions.

## Current Measurable Objective Baseline

The current `/metrics` contract supports four formal objectives and a
small set of operational guardrails:

1. Formal internal objectives:
   - effort-routing telemetry export reliability (P0.8)
   - HTTP availability (P3.3)
   - HTTP latency (P3.3)
   - webhook delivery reliability (P3.10)
2. Operational guardrails:
   - sustained high-effort routing ratio
   - persistent estimated cost lifetime-average elevation
   - in-app high-effort count and token-budget lifetime-average spot checks through
     `/v1/dashboard/alerts`
   - per-service health check results

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
the only reliability signal that the effort-routing `/metrics` surface can
measure honestly end to end.

### HTTP Availability (P3.3)

Definition:

- SLI: `1 - (rate(http_requests_total{status_code=~"5.."}[window]) / rate(http_requests_total[window]))`
- Recording rule: `agent33:http_requests:error_rate_5m`
- Window: `5m` rolling (for burn-rate alerting)
- Objective: 99.9% of requests return a non-5xx status code
- Error budget: 0.1% of total requests over the measurement window
- Config field: `slo_availability_target` (default `0.999`)

The `HTTPMetricsMiddleware` emits `http_requests_total` with `method`, `path`,
and `status_code` labels on every request.  Path segments containing UUIDs or
pure numeric IDs are normalized to `{id}` to keep label cardinality bounded.

Alert: `Agent33HighErrorRate` fires when the 5-minute error rate exceeds 1%
(the burn-rate threshold for the 99.9% target) for 5 consecutive minutes.

### HTTP Latency (P3.3)

Definition:

- SLI: p99 of `http_request_duration_seconds` per path
- Recording rule: `agent33:http_request_duration_seconds:p99_5m`
- Window: `5m` rolling
- Objective (API): p99 < 500 ms for standard API endpoints
- Objective (Agent): p99 < 10 s for agent invocation paths
- Config fields: `slo_latency_p99_ms` (default `500`), `slo_latency_agent_p99_ms` (default `10000`)

Note: The in-memory metrics collector records raw observation values, not
histogram buckets.  The Prometheus recording rule assumes a future histogram
export.  Until histogram buckets are exported, the in-app `/v1/dashboard/metrics`
JSON summary provides count, sum, avg, min, and max breakdowns per path which
can be used for operational spot-checks.

Alert: `Agent33HighLatency` fires when the 5-minute p99 latency exceeds 500 ms
for 5 consecutive minutes.

### Health Check Results (P3.3)

The `/health` endpoint emits a `health_check_result` observation (1.0 for OK,
0.0 for degraded/unavailable) per service on every call.  This is exported
through `/metrics` for Prometheus scraping and can be used to build
dependency-readiness dashboards.

### Webhook Delivery Reliability (P3.10)

Definition:

- SLI: `1 - (rate(webhook_delivery_failures_total[window]) / rate(webhook_delivery_total[window]))`
- Recording rule: `agent33:webhook_delivery:failure_rate_5m`
- Window: `5m` rolling (for burn-rate alerting), `1h` for formal objective
- Objective: 95% of webhook deliveries succeed over a 1-hour window
- Error budget: 5% of total deliveries over the measurement window
- Metrics:
  - `webhook_delivery_total` -- counter with `webhook_id` and `status` labels
  - `webhook_delivery_failures_total` -- counter with `webhook_id` label
  - `webhook_delivery_duration_seconds` -- observation with `webhook_id` label
  - `dead_letter_queue_captures_total` -- counter (no labels)
  - `dead_letter_queue_depth` -- observation (no labels)

The `WebhookDeliveryManager.process_result()` method emits delivery metrics
after each attempt.  `DeadLetterQueue.capture()` emits capture count and
current queue depth.

Alert: `Agent33WebhookDeliveryFailures` fires when the 5-minute failure rate
exceeds 5% for 5 consecutive minutes.

Alert: `Agent33DeadLetterQueueGrowing` fires when the dead-letter queue depth
exceeds 100 items for 10 consecutive minutes.

## Error Budget Policy

### Effort Telemetry

| Budget State | Policy |
| --- | --- |
| `0` failures in `28d` | normal deployment velocity |
| `> 0` failures in `28d` | investigate exporter health before risky monitoring changes |
| repeated `15m` failures | treat as active observability degradation and respond immediately |

### HTTP Availability

| Budget State | Policy |
| --- | --- |
| error rate < 0.1% over `28d` | normal deployment velocity |
| error rate 0.1% - 1% over `28d` | slow rollout cadence; investigate top error paths |
| error rate > 1% sustained `5m` | `Agent33HighErrorRate` fires; halt deploys and triage |

### HTTP Latency

| Budget State | Policy |
| --- | --- |
| p99 < 500 ms sustained | normal deployment velocity |
| p99 500 ms - 1 s sustained `5m` | `Agent33HighLatency` fires as warning; investigate slow paths |
| p99 > 1 s sustained `5m` | halt deploys and investigate; check DB pool, downstream timeouts |

### Webhook Delivery

| Budget State | Policy |
| --- | --- |
| failure rate < 5% over `1h` | normal deployment velocity |
| failure rate 5% - 15% sustained `5m` | `Agent33WebhookDeliveryFailures` fires; investigate failing endpoints |
| dead-letter depth > 100 sustained `10m` | `Agent33DeadLetterQueueGrowing` fires; drain or investigate root cause |

## Operational Guardrails

These stay alert-backed, but they are not promoted to full error-budgeted SLOs:

| Guardrail | Source | Threshold Surface |
| --- | --- | --- |
| high-effort routing ratio | `effort_routing_high_effort_total` and `effort_routing_decisions_total` | `agent33:sli:high_effort_routing_ratio:ratio_15m` |
| estimated cost rolling-window average | `effort_routing_estimated_cost_usd_window_avg` | `agent33:sli:estimated_cost_usd_window_avg:max` |
| estimated cost lifetime average | `effort_routing_estimated_cost_usd_avg` | `agent33:sli:estimated_cost_usd_avg:max` |
| token-budget rolling-window average | `effort_routing_estimated_token_budget_window_avg` | `agent33:sli:estimated_token_budget_window_avg:max` |
| token-budget lifetime average | `effort_routing_estimated_token_budget_avg` | `agent33:sli:estimated_token_budget_avg:max` and `/v1/dashboard/alerts` |
| in-app high-effort count | in-memory routing summary | `AlertManager` threshold in `engine/src/agent33/main.py` |

The Prometheus guardrails and the in-app dashboard alerts are related, but they
are not identical. Prometheus is the production-facing alerting contract; the
dashboard route remains a local operator spot-check surface.

As of P3.6, the metrics collector exports both process-lifetime averages
(`*_avg`) and rolling-window averages (`*_window_avg`). The lifetime averages
remain useful for persistent-elevation checks. The rolling-window averages
(default 5-minute window, configurable via `METRICS_ROLLING_WINDOW_SECONDS`)
enable short-window drift and spike detection. The `Agent33EstimatedCostDrift`
alert now fires on the rolling-window average rather than the lifetime average.

## Deferred Objectives

The following objectives remain explicitly deferred:

| Objective | Deferred Reason |
| --- | --- |
| evaluation regression rate | evaluation results live behind API routes, not `/metrics` |
| connector fleet reliability | connector monitoring is not exported through the public Prometheus surface |

Previously deferred objectives that are now formal SLOs:

| Objective | Resolved In |
| --- | --- |
| API availability success rate | P3.3 -- `http_requests_total` counter with status_code labels |
| request latency | P3.3 -- `http_request_duration_seconds` observation |
| dependency readiness (partial) | P3.3 -- `health_check_result` observation per service |
| webhook backlog / dead-letter rate | P3.10 -- `webhook_delivery_total`, `webhook_delivery_failures_total`, `dead_letter_queue_captures_total` counters |

The remaining deferred items are operationally important, but they require
additional instrumentation before they can become formal SLOs.

## Threshold Map

| Surface | Rule Family | Intent |
| --- | --- | --- |
| `deploy/monitoring/prometheus/agent33-alerts.rules.yaml` | recording rules + production alerts | formal telemetry objective and effort-routing guardrails |
| `/v1/dashboard/alerts` | in-app alert manager | local spot checks against the in-memory dashboard summary |
| `incident-response-playbooks.md` | operator procedures | manual handling for deferred evaluation and webhook incidents |

Current Prometheus-backed alert rule names:

- `Agent33EffortTelemetryExportFailures`
- `Agent33HighEffortRoutingRatio`
- `Agent33EstimatedCostDrift`
- `Agent33HighErrorRate` (P3.3)
- `Agent33HighLatency` (P3.3)
- `Agent33WebhookDeliveryFailures` (P3.10)
- `Agent33DeadLetterQueueGrowing` (P3.10)

`Agent33EstimatedCostDrift` keeps its historical rule name for continuity. As
of P3.6 it now alerts on the rolling-window average
(`agent33:sli:estimated_cost_usd_window_avg:max`) rather than the lifetime
average, enabling true short-window spike detection.

Current recording rules:

- `agent33:sli:effort_telemetry_export_failures:count_15m`
- `agent33:sli:effort_telemetry_export_failures:count_28d`
- `agent33:sli:high_effort_routing_ratio:ratio_15m`
- `agent33:sli:estimated_cost_usd_avg:max` (lifetime)
- `agent33:sli:estimated_cost_usd_window_avg:max` (rolling window, P3.6)
- `agent33:sli:estimated_token_budget_avg:max` (lifetime)
- `agent33:sli:estimated_token_budget_window_avg:max` (rolling window, P3.6)
- `agent33:http_requests:error_rate_5m` (P3.3)
- `agent33:http_request_duration_seconds:p99_5m` (P3.3)
- `agent33:webhook_delivery:failure_rate_5m` (P3.10)

## Validation Sequence

1. Confirm the API service is scraped through `/metrics`.
2. Load `deploy/monitoring/prometheus/agent33-alerts.rules.yaml`.
3. Verify the recording rules and alert names above are present in Prometheus.
4. Confirm `/v1/dashboard/alerts` remains available for local operator checks.
5. Confirm evaluation and webhook incidents still route through the manual
   procedures in `incident-response-playbooks.md`.

## Notes

- This document does not create a customer SLA.
- P3.3 adds HTTP availability (99.9%) and latency (p99 < 500 ms) SLOs backed
  by `HTTPMetricsMiddleware` and exported through `GET /metrics`.
- P3.10 adds webhook delivery reliability (95% success rate) SLO backed by
  `WebhookDeliveryManager` and `DeadLetterQueue` metrics, exported through
  `GET /metrics`.
- Evaluation and connector objectives remain deferred until the repo exports
  the required Prometheus metrics.
- SLO threshold config fields (`slo_availability_target`, `slo_latency_p99_ms`,
  `slo_latency_agent_p99_ms`) are defined in `engine/src/agent33/config.py`
  and can be overridden via environment variables.
