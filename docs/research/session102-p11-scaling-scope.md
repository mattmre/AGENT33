# Session 102 P1.1 Horizontal-Scaling Architecture and State-Boundary Scope

Date: 2026-03-20
Slice: `P1.1` horizontal-scaling architecture and state-boundary design
Baseline: `origin/main` at `2ebf5ef` after `P0.8`

## Goal

Document the current runtime state boundaries honestly, define which surfaces
are already replica-safe versus replica-local, and lock the minimum design
needed before any multi-replica Kubernetes rollout work starts.

## Why This Slice Exists Now

The repo now has:

- a production Kubernetes baseline under `deploy/k8s/`
- scrape-ready `/metrics` plus Grafana and Prometheus assets
- a deployment runbook, incident playbooks, and a bounded SLO baseline

What it does not yet have is a single architectural contract answering:

- which runtime state is already shared across replicas
- which transport and session surfaces require routing affinity
- which mutable globals still block `replicas > 1`
- what `P1.2` must migrate before the deployment overlay can claim
  horizontal-scaling support

## Locked Inclusions

1. Add one canonical operator-facing architecture doc under `docs/operators/`.
2. Add one session research memo capturing the audit and the bounded
   implementation scope for this slice.
3. Cross-link the new architecture doc from the production deployment docs.
4. Add focused validation for the new doc and its required references.
5. Keep the deliverable design-only: no runtime code changes, no deployment
   manifest changes, and no speculative infra additions.

## Locked Non-Goals

- changing Kubernetes replica counts or adding HPA/PDB resources
- implementing leader election, sharding, or Redis/Postgres migrations
- replacing the local workflow/event/session managers
- refactoring auth, webhook delivery, evaluation, review, or browser session
  storage in this slice
- claiming that current single-node filesystem-backed stores are multi-replica
  safe

## Current Boundary Findings

### Already shared enough to build on

- PostgreSQL-backed long-term memory
- Redis
- NATS

### Durable for restart on one replica, but not truly shared

- `OrchestrationStateStore` snapshots written from
  `engine/src/agent33/services/orchestration_state.py`
- operator session files from `engine/src/agent33/sessions/storage.py`
- persisted benchmark artifacts via `SkillsBenchArtifactStore`
- improvement learning-signal persistence when the configured backend is
  `sqlite` or `file`

These surfaces survive some restart paths, but they still depend on local
files or local process ownership. They should not be treated as horizontally
shared state without a shared volume or a different backend.

### Process-local but tolerable only with ownership or routing affinity

- workflow WebSocket / SSE subscription state in
  `engine/src/agent33/workflows/ws_manager.py`
- browser automation sessions in
  `engine/src/agent33/tools/builtin/browser.py`
- multimodal voice sessions and daemons in
  `engine/src/agent33/multimodal/service.py`
- Jupyter kernel sessions in `engine/src/agent33/execution/adapters/jupyter.py`

These can exist per replica, but follow-up work must define how clients or
workers reconnect to the owning replica.

### Global mutable state that still blocks `replicas > 1`

- bootstrap auth users and API keys in `engine/src/agent33/api/routes/auth.py`
  and `engine/src/agent33/security/auth.py`
- workflow registry, execution history, and scheduler state in
  `engine/src/agent33/api/routes/workflows.py`
- orchestration-state-backed control-plane namespaces because
  `engine/src/agent33/services/orchestration_state.py` keeps an in-memory copy
  and rewrites the JSON snapshot without distributed locking or reload
- webhook registrations and delivery receipts in
  `engine/src/agent33/automation/webhooks.py` and
  `engine/src/agent33/automation/webhook_delivery.py`
- evaluation runs, baselines, multi-trial runs, and scheduled-gate state in
  `engine/src/agent33/evaluation/service.py` and
  `engine/src/agent33/evaluation/scheduled_gates.py`
- review records in `engine/src/agent33/review/service.py`
- operator session storage in `engine/src/agent33/sessions/storage.py` because
  it writes to a pod-local filesystem path unless a shared volume is provided
- live observation buffers, local BM25 freshness, dynamic tool activation, and
  rate-limiter counters remain replica-local follow-up risks even after the
  first blocking set is addressed

## Intended Deliverable Shape

- one operator doc with:
  - the current single-replica guardrail
  - a state-boundary matrix
  - an ingress / transport affinity contract
  - the blocking surfaces for multi-replica rollout
  - an ordered `P1.2` migration sequence
- one focused test validating:
  - section presence
  - required path references
  - the explicit `do not scale yet` guardrail
