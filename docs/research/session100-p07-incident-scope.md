# Session 100 P0.7 Incident Playbooks Scope

Date: 2026-03-20
Slice: `P0.7` incident response playbooks
Baseline: `origin/main` at `4f6bea5` after `P0.6`

## Goal

Add the first incident-response playbooks for the currently shipped production
topology without reopening deployment packaging, metrics design, or SLI policy.

## Why This Slice Exists Now

`P0.6` established the rollout, verification, and rollback baseline for the
single-instance Kubernetes deployment. The repo now needs operator-facing
incident workflows tied to the assets that actually exist on `main`:

- Kubernetes base + production overlay under `deploy/k8s/`
- monitoring assets under `deploy/monitoring/`
- public health and metrics routes
- authenticated operator and evaluation surfaces

## Locked Inclusions

1. Add one incident playbook document under `docs/operators/`.
2. Keep the playbooks bounded to four concrete scenarios already implied by the
   queue and current repo surfaces:
   - service/API outage
   - degraded dependencies / readiness failure
   - evaluation regression or scheduled-gate failure
   - webhook delivery backlog growth / dead-letter accumulation
3. Cross-link the new playbook from the current operator and monitoring docs.
4. Tighten `docs/api-surface.md` where the playbooks depend on routes that are
   present in code but not documented clearly enough yet.
5. Add a focused docs-validation test so the playbook keeps referencing real
   repo paths, commands, and endpoint contracts.

## Locked Non-Goals

- new deployment manifests, Helm charts, or service packaging
- new Prometheus metrics, Grafana dashboards, or alert rules
- SLI / SLA targets, error budgets, or threshold policy work reserved for `P0.8`
- broad release-management, scaling, or incident-automation changes
- generic incident templates detached from the repo's real runtime surfaces

## Current Concrete Surfaces To Anchor

### Core rollout and monitoring baseline

- `docs/operators/production-deployment-runbook.md`
- `deploy/monitoring/README.md`
- `deploy/monitoring/prometheus/agent33-alerts.rules.yaml`
- `deploy/k8s/overlays/production/README.md`

### Public health and monitoring endpoints

- `GET /healthz`
- `GET /readyz`
- `GET /health`
- `GET /metrics`
- `GET /v1/dashboard/alerts`

### Authenticated operator and diagnostic endpoints

- `GET /v1/operator/status`
- `GET /v1/operator/doctor`
- `POST /v1/operator/reset`

### Evaluation and regression surfaces

- `GET /v1/evaluations/regressions`
- `PATCH /v1/evaluations/regressions/{regression_id}/triage`
- `POST /v1/evaluations/regressions/{regression_id}/resolve`
- `GET /v1/evaluations/schedules`
- `POST /v1/evaluations/schedules/{schedule_id}/trigger`
- `GET /v1/evaluations/schedules/{schedule_id}/history`

### Backlog / dead-letter surfaces already in code

- `GET /v1/webhooks/deliveries/stats`
- `GET /v1/webhooks/deliveries/dead-letters`
- `POST /v1/webhooks/deliveries/{delivery_id}/retry`

## Key Scope Trap

The checked-in Prometheus rules only cover effort-routing telemetry and cost
drift today. They do not define production thresholds for evaluation failures
or webhook backlog depth. The `P0.7` playbooks must acknowledge that reality
and route operators through the current admin/operator endpoints instead of
pretending those scenarios already have Prometheus-backed alerting.

## Intended Deliverable Shape

- one operator document with:
  - incident severity model
  - incident matrix
  - four step-by-step playbooks
  - dependency map from symptom to route / command / repo asset
- small doc cross-links
- focused validation test
