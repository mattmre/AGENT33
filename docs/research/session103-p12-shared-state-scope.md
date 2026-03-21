# Session 103 P1.2 Shared-State Runtime Implementation Scope

Date: 2026-03-21
Slice: `P1.2` shared-state instance registry and distributed locks
Baseline: `origin/main` at `9e4afa7` after `P1.1`
Predecessor: `docs/research/session102-p11-scaling-scope.md`

## Goal

Implement the minimum runtime changes to make AGENT-33 aware of instance
identity and add distributed locking primitives that prevent state corruption
if a second instance were accidentally started. The single-instance guardrail
from `docs/operators/horizontal-scaling-architecture.md` is NOT removed.

## What State Was Identified as Unsafe

The P1.1 audit (`docs/operators/horizontal-scaling-architecture.md`) identified
four categories of state. The multi-replica blocking surfaces (group 4) are the
primary targets for P1.2 mitigation:

### Scheduler / Cron Dual-Execution Risk (mitigated in P1.2)

| Surface | Module | Risk |
| --- | --- | --- |
| Workflow scheduler (APScheduler) | `automation/scheduler.py` | Two instances run independent APScheduler loops, triggering duplicate job executions |
| Scheduled evaluation gates | `evaluation/scheduled_gates.py` | Independent APScheduler instances fire the same gate evaluations concurrently |
| Tuning loop scheduler | `improvement/tuning.py` | Duplicate tuning cycles can corrupt improvement state |

These are the highest-risk surfaces because duplicate scheduled execution can
cause observable side effects (double workflow runs, double evaluations, double
tuning cycles) even without shared mutable state.

**Mitigation:** Distributed lock guard around scheduler job execution. Each
scheduled job acquires a lock keyed by job identity before execution. If the
lock is already held, the duplicate fires a warning and skips.

### Module-Level Mutable Globals (identified, deferred to P1.3+)

| Surface | Module | Risk |
| --- | --- | --- |
| Bootstrap auth users | `api/routes/auth.py` | `_users` dict diverges per replica |
| API keys | `security/auth.py` | `_api_keys` dict diverges per replica |
| Workflow registry / history | `api/routes/workflows.py` | definitions and run history split |
| Cron job store | `main.py` / `api/routes/cron.py` | `cron_job_store` is process-local dict |
| Webhook registrations | `automation/webhooks.py` | `_hooks` dict is process-local |
| Webhook delivery state | `automation/webhook_delivery.py` | queue and receipts are bounded in-memory |
| Evaluation runs / baselines | `evaluation/service.py` | replica-local run state |
| Review lifecycle records | `review/service.py` | process-local approval state |

**Decision:** Migrating these to Redis or PostgreSQL is P1.3+ work. P1.2
establishes the instance identity and locking primitives that P1.3 will use.

### File-Backed Single-Replica Durable State (identified, deferred to P1.3+)

| Surface | Module | Risk |
| --- | --- | --- |
| Orchestration snapshots | `services/orchestration_state.py` | JSON file with last-writer-wins |
| Operator session storage | `sessions/storage.py` | filesystem-based with PID locks |
| Benchmark artifacts | SkillsBench artifact store | local disk |
| Learning signal persistence | SQLite / file backend | per-node durable only |

**Decision:** Deferred. These require shared volume or backend migration.

### Replica-Local Affinity Surfaces (identified, deferred to P1.3+)

| Surface | Module | Risk |
| --- | --- | --- |
| WS/SSE subscriptions | `workflows/ws_manager.py` | process-local connection tables |
| Browser sessions | `tools/builtin/browser.py` | Playwright handles are process-local |
| Voice sessions | `multimodal/service.py` | process-local voice runtime |
| Jupyter kernels | `execution/adapters/jupyter.py` | process-local kernel handles |
| Operator session hot cache | `sessions/service.py` | `_active` dict is process-local |

**Decision:** These require sticky routing or session affinity, not locks.

## What P1.2 Delivers

1. **Instance registry** (`scaling/instance_registry.py`): UUID-based instance
   identity, registered in Redis on startup (with in-process fallback). Other
   instances can detect a live instance before attempting to claim ownership.

2. **Distributed lock** (`scaling/distributed_lock.py`): Redis SETNX-based
   distributed lock with TTL expiry and in-process asyncio.Lock fallback.
   Real acquire/release semantics, not stubs.

3. **State guards** (`scaling/state_guards.py`): Enforcement layer that checks
   instance registry before allowing scheduler ownership. Raises
   `InstanceConflictError` if a second instance tries to own single-replica
   state without proper distributed lock coordination.

4. **Main.py wiring**: Instance registry initializes after Redis, before other
   subsystems. State guard wraps scheduler job execution.

5. **Tests**: Full coverage of instance registry, distributed lock, state
   guards, and scheduler lock integration.

## What Remains for P1.3+

- Migrate auth users, API keys, workflow registry, cron job store, webhook
  registrations, evaluation state, and review state to shared backends
- Migrate file-backed orchestration snapshots and session storage to PostgreSQL
  or Redis
- Define sticky routing for WS/SSE, browser, voice, and kernel sessions
- Remove the single-instance guardrail from the deployment overlay
