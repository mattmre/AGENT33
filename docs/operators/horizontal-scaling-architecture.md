# Horizontal-Scaling Architecture

## Purpose

Define the current state-boundary contract for AGENT-33 before any
multi-replica Kubernetes rollout.

Use this document with:

- [`production-deployment-runbook.md`](production-deployment-runbook.md)
- [`incident-response-playbooks.md`](incident-response-playbooks.md)
- [`service-level-objectives.md`](service-level-objectives.md)
- [`../research/session102-p11-scaling-scope.md`](../research/session102-p11-scaling-scope.md)

## Current Deployment Guardrail

The repo-owned production overlay remains single-instance today.

Do not increase the API deployment above `replicas: 1` until the blocking
surfaces in this document are migrated or fenced by an explicit ownership
model. `P1.1` is architecture only. The implementation work starts in `P1.2`.

## State Boundary Model

Classify runtime state into four groups before changing deployment topology:

1. Shared backing services or durable data stores that multiple replicas can
   connect to today.
2. Durable state that survives restart on one replica but is not actually
   shared across replicas yet.
3. Replica-local state that is acceptable only when a client, worker, or
   long-lived task stays attached to its owning replica.
4. Global mutable state that is currently stored only in one process and would
   diverge immediately if multiple replicas served the same traffic.

Horizontal scaling is blocked by groups 2 and 4, and partially constrained by
group 3.

## Shared Backing Services Available Today

The following backends already exist on `main` and are the foundation for
multi-replica work:

| Surface | Current backing | Notes |
| --- | --- | --- |
| Long-term memory | PostgreSQL via `LongTermMemory` | Durable and already shared |
| Cache / transient coordination | Redis | Shared runtime service, but the checked-in overlay does not make it a durable state store |
| Event bus | NATS | Shared messaging plane, but not a persisted state backend for control-plane ownership |

Redis and NATS are present today, but `P1.1` does not claim that the repo is
already using them as the source of truth for schedulers, sessions, or control
plane state ownership, nor that the checked-in deployment treats them as
durable state stores.

## Single-Replica Durable But Not Shared Yet

The following surfaces survive some restart paths, but they are still not safe
to treat as shared state:

| Surface | Current module | Why it is not shared yet |
| --- | --- | --- |
| Orchestration control-plane snapshots | `engine/src/agent33/services/orchestration_state.py` | JSON file is loaded once per process and rewritten from in-memory state without distributed locking or reload |
| Operator sessions | `engine/src/agent33/sessions/storage.py` | session files and PID locks assume one host or one shared filesystem |
| Benchmark artifacts | `SkillsBenchArtifactStore` | persisted on local disk unless deployment provides shared storage |
| Improvement learning-signal persistence | `SQLiteLearningSignalStore` or file backend | durable per node, but still file-backed and separate from other improvement state |

Services wired through `state_store=orchestration_state_store` in
[`engine/src/agent33/main.py`](../../engine/src/agent33/main.py) therefore
have restart durability on one worker, not true replica-safe coordination.
That includes autonomy budgets, release state, traces, approval-token state,
tool approval state, mutation audit state, process-manager state, pack trust
state, and related operator control-plane snapshots.

## Replica-Local Surfaces That Need Ownership or Affinity

These surfaces can exist per replica, but they require an explicit routing or
ownership model before multi-replica rollout:

| Surface | Current module | Why affinity matters |
| --- | --- | --- |
| Workflow WS / SSE subscriptions | `engine/src/agent33/workflows/ws_manager.py` | connection tables, replay buffers, and snapshots are process-local |
| Browser tool sessions | `engine/src/agent33/tools/builtin/browser.py` | Playwright browser/page objects live only in one process |
| Voice sessions / daemons | `engine/src/agent33/multimodal/service.py` | active voice runtime ownership is process-local |
| Jupyter kernel sessions | `engine/src/agent33/execution/adapters/jupyter.py` | kernel handles are owned by one process |
| Operator session hot cache | `engine/src/agent33/sessions/service.py` | `_active` is local even though disk state can be reloaded |

Required rule: once a client or task is attached to one of these surfaces, the
next request must either return to the owning replica or reconnect through a
shared coordination layer.

## Multi-Replica Blocking Surfaces

The following modules currently make `replicas > 1` unsafe:

| Surface | Current module | Blocking issue |
| --- | --- | --- |
| Bootstrap auth users | `engine/src/agent33/api/routes/auth.py` | `_users` is in-memory per process |
| API keys | `engine/src/agent33/security/auth.py` | `_api_keys` is in-memory per process |
| Workflow registry / history / scheduler | `engine/src/agent33/api/routes/workflows.py` | definitions, run history, and scheduled jobs diverge by replica |
| Orchestration-state-backed control plane | `engine/src/agent33/services/orchestration_state.py` | last-writer-wins JSON snapshots are not a distributed state backend |
| Webhook registrations | `engine/src/agent33/automation/webhooks.py` | registered paths live only in one process |
| Webhook delivery receipts and retries | `engine/src/agent33/automation/webhook_delivery.py` | queue, receipts, and dead letters are bounded in-memory only |
| Evaluation runs / baselines / experiments | `engine/src/agent33/evaluation/service.py` | run state and baselines are replica-local |
| Scheduled gates | `engine/src/agent33/evaluation/scheduled_gates.py` | each replica would own an independent APScheduler instance |
| Review lifecycle records | `engine/src/agent33/review/service.py` | approvals and assignments are process-local |
| Operator session storage root | `engine/src/agent33/sessions/storage.py` | durable only if every replica sees the same filesystem path |
| Cron and workflow scheduler ownership | `engine/src/agent33/api/routes/cron.py` | scheduler boundary is fragmented and not backed by shared ownership |

Two implications follow from this table:

1. Stateless HTTP load balancing is not enough.
2. A second replica would create split-brain state for auth bootstrap,
   workflow scheduling, evaluations, reviews, and webhook operations.

## Storage and Ownership Constraints

`OrchestrationStateStore` and `FileSessionStorage` both persist to local files.
`OrchestrationStateStore` in particular is not a distributed key/value store:
each worker loads the JSON file into memory once and later rewrites namespaces
from that local copy. That is sufficient for restart recovery on one pod, but
not enough for true horizontal scaling unless one of these becomes true:

- all replicas mount the same read-write-many volume and tolerate file-level
  coordination constraints
- the stores are migrated to a shared service such as PostgreSQL or Redis
- only one elected leader writes those surfaces while followers stay read-only

Until one of those models exists, treat file-backed persistence as
single-replica durability, not shared state.

## Ingress and Transport Contract

Use the following contract for future multi-replica rollout:

| Traffic type | Current contract |
| --- | --- |
| simple request/response routes backed only by shared stores | may load balance freely once blocking globals are removed |
| workflow WS / SSE follow-up requests | require sticky routing or shared replay / pubsub state |
| browser, voice, and kernel session follow-ups | must return to the owning replica or reconnect through a broker |
| scheduler-triggered or queue-owned background work | must run under leader election or durable queue ownership |

For the current repo baseline, assume workflow streaming, voice sessions,
browser sessions, and local execution sessions are owner-affine.

## Secondary Divergence Risks

The first blocking set above is the minimum gate for `P1.2`, but additional
replica-local behavior still needs follow-up:

- live observation buffers in `engine/src/agent33/memory/observation.py`
- BM25 freshness after new writes in `engine/src/agent33/memory/bm25.py`
- dynamic tool activation in `engine/src/agent33/tools/discovery_runtime.py`
- rate-limiter counters in `engine/src/agent33/security/rate_limiter.py`

These are not the first migration wave, but they should not be ignored once
the core control-plane split-brain risks are addressed.

## P1.2 Migration Sequence

Implement the next slice in this order to minimize drift:

1. Move auth bootstrap users and API-key state out of process memory.
2. Replace workflow registry, execution history, and scheduler ownership with a
   shared or leader-elected model.
3. Persist cron job definitions and job history so the `/v1/cron` surface does
   not fragment by replica.
4. Persist webhook registrations, delivery receipts, retry scheduling, and
   dead-letter state.
5. Persist evaluation runs, baselines, and scheduled-gate schedules/history.
6. Migrate review lifecycle state to a shared durable store.
7. Decide whether operator sessions and orchestration snapshots will use a
   shared filesystem, PostgreSQL, or Redis-backed coordination.
8. Define the routing strategy for workflow streaming, browser sessions, voice
   sessions, and kernel-backed execution.

## Readiness Gate Before `replicas > 1`

Treat the API deployment as ready for multi-replica rollout only when all of
the following are true:

- no user-visible global mutable state depends on module-level dictionaries
- no scheduler can run independently on multiple replicas without coordination
- webhook, evaluation, and review state survive replica replacement
- operator sessions and orchestration snapshots use shared storage or a durable
  coordination service
- workflow WS / SSE and other long-lived sessions have a documented ownership
  model
- the production overlay and runbook are updated together to reflect the new
  topology

Until then, the safe production posture is the single-instance baseline defined
in [`production-deployment-runbook.md`](production-deployment-runbook.md).
