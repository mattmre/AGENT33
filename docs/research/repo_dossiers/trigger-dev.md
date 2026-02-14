# Repo Dossier: triggerdotdev/trigger.dev

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

Trigger.dev is an open-source TypeScript platform (Apache 2.0, ~13.6k stars) for building and deploying background jobs and long-running workflows with no timeout limits. It uses a **checkpoint-resume durable execution model** where tasks are written as exported functions in the codebase, deployed to a managed cloud service or self-hosted infrastructure (Docker Compose/Kubernetes), and orchestrated through queues with configurable concurrency, retry policies, and human-in-the-loop waitpoints. Unlike serverless platforms (Lambda, Vercel) or traditional job queues (Celery, APScheduler), Trigger.dev offers fully-managed infrastructure with real-time OpenTelemetry tracing, automatic payload offloading to object storage, and elastic machine scaling (7 CPU/RAM presets from 0.25 vCPU to 8 vCPU). The platform supports declarative cron schedules, batch operations, task coordination primitives (`triggerAndWait`, `batchTriggerAndWait`), and extensibility through build hooks, middleware, and custom container layers.

## 2) Core orchestration model

**Checkpoint-resume durable execution**: Tasks pause at **waitpoints** (explicit `wait.for()` calls, `triggerAndWait()`, or wait tokens for human approval) and release concurrency slots, allowing other runs to execute. State is checkpointed and resumed from the same point after dependencies complete or timeouts expire. This is fundamentally different from APScheduler (single-threaded in-memory scheduler) or Celery (distributed task queue requiring RabbitMQ/Redis message brokers).

**Task lifecycle**: `onStartAttempt` → middleware wrapping → `run()` function → completion hooks (`onSuccess`/`onFailure`/`onComplete`/`onCancel`). The `catchError` callback provides granular error inspection for conditional retry logic (e.g., dynamic `retryAt` scheduling for rate limits).

**Coordination primitives**:
- `task.trigger()` — fire-and-forget
- `task.triggerAndWait()` — synchronous child task execution with typed results
- `batch.triggerAndWait()` — parallel multi-task coordination
- `wait.createToken()` — human-in-the-loop waitpoints with webhook callbacks or SDK completion
- `runs.reschedule()` — dynamic delay adjustment for queued runs

**Queue management**: Queues defined as reusable objects with `concurrencyLimit` (default: unbounded). `concurrencyKey` creates per-tenant queue instances. Runtime queue selection via trigger-time overrides enables priority routing (e.g., high-priority users → higher-concurrency queues).

**Environments**: Dev (no charge, 500 queue limit), Staging, Preview (branch-isolated, 5-20 depending on tier), Production (10M queue limit). Preview branches auto-archive on PR close.

## 3) Tooling and execution

**CLI**: `npx trigger.dev@latest deploy` (builds locally, pushes to registry, deploys), `--env preview` for branch environments, `--dry-run` for container inspection, `--log-level debug` for troubleshooting. CI/CD via `TRIGGER_API_URL` and `TRIGGER_ACCESS_TOKEN` environment variables in GitHub Actions.

**Machine presets**: 7 tiers (micro to large-2x) configurable per-task or globally in `trigger.config.ts`. Runtime overrides available during triggering for dynamic resource allocation. OOM handling pattern: retry with escalation to larger machines.

**Build system**: esbuild-based with lifecycle hooks (`onBuildStart`, `onBuildComplete`, `externalsForTarget`). Custom plugins via `context.registerPlugin()`, container customization via `addLayer()` API (dependencies, system packages, Dockerfile instructions, build/deploy env vars).

**Middleware**: Wraps all lifecycle hooks, shares state via `locals` API. Auto-loaded from `init.ts` in trigger directory (e.g., database connections that disconnect during waits).

**SDK**: TypeScript-first with React hooks for frontend integration, REST API for external systems. Management SDK provides `runs.list()`, `runs.retrieve()`, `runs.cancel()`, `runs.replay()`, `schedules.create()`/`.update()`/`.deactivate()`.

## 4) Observability and evaluation

**OpenTelemetry integration**: Automatic instrumentation for task triggers, attempts, and HTTP requests. Optional instrumentation for database operations (e.g., Prisma). Custom tracing via `logger.trace(name, async (span) => {...})` with manual attribute assignment.

**Structured logging**: `logger.[debug|log|info|warn|error](message, keyValueObject)`. Standard `console.log()` also captured. Log retention: Free (1 day), Hobby (7 days), Pro (30 days). 128 KB I/O packet limit, 256 attributes per span/log.

**Real-time trace view**: Live run page shows step-by-step execution as it happens. Powered by OpenTelemetry, includes complete execution traces and all logs for debugging failures.

**Metadata & tagging**: Up to 10 tags per run for filtering (dashboard, realtime API, SDK). Metadata updates progressively during execution. Tag-based subscriptions enable real-time monitoring of all runs matching criteria (e.g., `user:123`).

**Alerts**: Email, Slack, webhooks for task failures and deployments. Free (1 destination), Hobby (3), Pro (100+).

**Realtime API**: Subscribe to individual runs, tag-filtered runs, batches, or combined trigger-subscribe. Supports streaming data for AI/LLM outputs and progress updates. React hooks for frontend dashboards, backend SDK for workflow orchestration.

**ResourceMonitor utility**: Tracks heap usage, process memory, disk space, GC activity, and child processes (e.g., ffmpeg) for proactive resource management.

## 5) Extensibility

**Build extensions**: Add to `trigger.config.ts` with `name` and hook functions. `onBuildStart` registers esbuild plugins (with `placement: "first"|"last"`), `onBuildComplete` adds build layers (dependencies, container packages, Dockerfile instructions, env vars). `externalsForTarget` excludes packages from bundling.

**Custom runtime environment**: System packages via `image.pkgs` in build layers (e.g., browsers, Python, FFmpeg). Runtime env vars via `deploy.env` (synced securely to Trigger.dev), build-time vars via `build.env`.

**Middleware system**: Wraps all lifecycle hooks, uses `locals` for shared state. `init.ts` auto-loads during task execution for global initialization (DB connections, etc.).

**Integrations**: Use any Node.js SDK or HTTP client. OAuth-aware integrations simplify external API usage. Webhooks, custom events, and cron schedules as triggers.

**Self-hosting**: Docker Compose (webapp + supervisor + registry + MinIO object storage + PostgreSQL + Redis) or Kubernetes (Helm charts). Network isolation via Docker Socket Proxy. Built-in registry and object storage eliminate S3/GCS dependency. Webapp machine (3+ vCPU, 6+ GB RAM), worker machines (4+ vCPU, 8+ GB RAM, horizontally scalable).

## 6) Notable practices worth adopting in AGENT-33

1. **Checkpoint-at-wait pattern**: AGENT-33's APScheduler jobs run to completion or fail. Trigger.dev's waitpoints release concurrency during pauses (subtask execution, time delays, human approval). Adopt this for AGENT-33's `workflow_executor.py` to free resources during `wait` action or agent invocations.

2. **Progressive metadata updates**: Trigger.dev's run metadata updates as tasks execute, enabling real-time progress UIs. AGENT-33's workflow state is checkpoint-only. Add a `metadata: Dict[str, Any]` field to `WorkflowRun` that updates via `workflow.update_metadata(key, value)` and streams to observability layer.

3. **Concurrency keys for multi-tenancy**: `concurrencyKey` creates per-entity queue instances (per-user, per-account). AGENT-33 has tenant isolation but no per-tenant queuing. Add `concurrency_key` to workflow/agent invocation to prevent one tenant's burst from starving others.

4. **Batch trigger primitives**: `batchTrigger()` and `batchTriggerAndWait()` process 1,000+ items with automatic rate limiting and error handling. AGENT-33's `parallel_group` action runs subtasks but lacks built-in batching. Add `batch_invoke_agent()` and `batch_execute_workflow()` with chunking and error aggregation.

5. **Token bucket rate limiting**: Trigger.dev's batch system uses token buckets (5,000 burst, 500 runs/5s). AGENT-33's rate limiting is per-tool-call only. Apply token bucket to `ToolRegistry.execute()` and `WorkflowEngine.execute_action()` for system-wide burst control.

6. **Idempotency keys at invocation**: Trigger.dev accepts `idempotencyKey` per trigger, not just per task. AGENT-33's `AgentRuntime` has no invocation-level deduplication. Add `idempotency_key` to `invoke_agent` workflow action and `POST /v1/agents/{id}/invoke` to prevent duplicate runs during retries.

7. **Run replay**: `runs.replay(runId)` re-executes with identical payload for debugging. AGENT-33's observability has lineage tracking but no replay. Add `POST /v1/workflows/{run_id}/replay` that clones the run's input and resubmits.

8. **Declarative + imperative scheduling**: Cron schedules defined in code (declarative, version-controlled) or created dynamically via API (imperative, per-user). AGENT-33's automation layer is imperative-only (APScheduler jobs created via API). Add a `schedules/` directory with YAML definitions that auto-sync on startup.

9. **Build hooks for deployment customization**: `onBuildStart`/`onBuildComplete` customize bundling and containers. AGENT-33 deploys via Docker but has no pre-deploy customization. Add `pre_deploy_hooks` to `config.py` that run before image build (e.g., schema validation, dependency audits).

10. **Machine presets for resource control**: 7 standardized CPU/RAM tiers, configurable per-task with runtime override. AGENT-33 runs everything on the same container resources. Add `machine_preset` to agent definitions and workflow run options, map to Docker `--cpus` and `--memory` limits via Docker SDK.

11. **Wait tokens for human-in-the-loop**: `wait.createToken()` pauses execution until external completion (webhook or SDK). AGENT-33's workflows have no blocking external input. Add a `wait_for_approval` workflow action that creates a token, stores URL in run metadata, and polls for completion. Expose `POST /v1/workflows/{run_id}/approve` endpoint.

12. **Log retention tiers**: Free (1 day), Hobby (7 days), Pro (30 days). AGENT-33 logs everything to stdout with no retention policy. Add `LOG_RETENTION_DAYS` config, implement a nightly Alembic-driven cleanup job that deletes old `WorkflowCheckpoint` and `ObservationCapture` rows.

## 7) Risks / limitations to account for

1. **Cold start latency**: Traditional containers take seconds to boot. Trigger.dev is migrating to MicroVMs (<500ms), but this is not yet GA. AGENT-33's APScheduler jobs start immediately since the worker process is always running. If adopting durable execution, pre-warm containers or use agent pooling.

2. **API rate limits**: 1,500 req/min across the platform. Trigger.dev mitigates via `batchTrigger()`, but AGENT-33's current architecture has no global rate limiter. Enforce this at the FastAPI middleware layer (token bucket per tenant) before adopting batch patterns.

3. **Concurrency constraints**: Free (10), Hobby (25), Pro (100+). AGENT-33 has no concurrency limit. If migrating to a Trigger.dev-like queue model, set per-tenant limits in `GovernanceConstraints` and enforce in `workflow_executor.py` before dequeuing.

4. **3MB payload limit**: Single triggers max at 3MB, offloaded to object storage if >512KB. AGENT-33's workflow payloads are JSON in PostgreSQL with no size enforcement. Add a pre-check in `POST /v1/workflows/execute` that rejects >3MB payloads or auto-offloads to S3/MinIO.

5. **10MB output limit**: Task results capped at 10MB. AGENT-33's workflow results are unbounded. Add output validation in `workflow_executor.py` that truncates or errors on oversized outputs.

6. **No automatic checkpointing**: Checkpoints only occur at explicit waitpoints. Trigger.dev docs warn that long-running compute (e.g., hours of ML inference) without waits can OOM on retries. AGENT-33's `execute_code` action could run arbitrarily long. Add periodic `yield` points or enforce `max_execution_time` in `CodeExecutor`.

7. **Middleware wraps entire run**: Trigger.dev's middleware runs once per attempt, not per step. AGENT-33's workflow actions are independently retryable. If adopting middleware, ensure it's idempotent (e.g., DB connection pooling, not one-time setup).

8. **Preview branch limits**: Hobby (5), Pro (20). AGENT-33 has no branch-based environments. If implementing this, auto-archive inactive branches to avoid hitting limits (detect via `gh pr list --state closed`).

9. **Batch size cap**: 1,000 items per batch. AGENT-33's `parallel_group` action has no limit. If adding batch primitives, chunk >1,000 items into multiple batches and use `asyncio.gather()` to parallelize.

10. **Self-hosting complexity**: Requires webapp + supervisor + registry + MinIO + PostgreSQL + Redis. AGENT-33's current stack is PostgreSQL + Redis + NATS. Adding Trigger.dev-style durable execution would require a container registry (Docker Registry or Harbor) and object storage (MinIO or S3). Evaluate operational overhead before adopting.

11. **TypeScript-first SDK**: Trigger.dev's Python support is unclear. AGENT-33 is Python-based. A durable execution rewrite would need a custom implementation, not direct adoption of Trigger.dev. Consider `temporal.io` (Python SDK exists) or Prefect (Python-native) as alternatives.

12. **No automatic compensation**: Trigger.dev has retries but no rollback primitives (sagas, compensating transactions). AGENT-33's workflow engine also lacks this. If adopting durable execution, add a `compensate` field to workflow actions that defines rollback logic (e.g., delete created resources on failure).

## 8) Feature extraction (for master matrix)

| Feature | AGENT-33 Status | Trigger.dev Implementation | Gap/Opportunity |
|---------|----------------|---------------------------|-----------------|
| **Orchestration** |
| Durable execution | ❌ APScheduler jobs run to completion | ✅ Checkpoint-resume at waitpoints | Add checkpoint-at-wait to workflow executor |
| Queue-based scheduling | ⚠️ APScheduler (in-memory, single-threaded) | ✅ PostgreSQL-backed queues, 10M limit | Migrate to NATS JetStream + PostgreSQL queue table |
| Concurrency limiting | ❌ No system-wide limits | ✅ Per-queue, per-task, per-tenant via `concurrencyKey` | Add to `GovernanceConstraints`, enforce in workflow executor |
| Multi-environment | ⚠️ Single environment | ✅ Dev/Staging/Preview/Prod with isolated queues | Add `environment` to `WorkflowRun`, separate queues |
| Preview branches | ❌ No branch-based isolation | ✅ PR-scoped environments with auto-archival | GitHub Actions workflow for `feat/*` → isolated tenant |
| **Retry & Error Handling** |
| Exponential backoff | ✅ Configurable in workflow actions | ✅ `factor`, `minTimeoutInMs`, `maxTimeoutInMs`, `randomize` | AGENT-33's implementation is similar, already robust |
| Conditional retry | ❌ No error inspection | ✅ `catchError` callback with dynamic `retryAt` | Add `retry_condition` to workflow actions (Python expression) |
| Inline retry primitives | ❌ Whole-action retry only | ✅ `retry.onThrow()`, `retry.fetch()` for sub-blocks | Add `retry_block` context manager to Python executor |
| Abort without retry | ⚠️ `max_attempts: 1` workaround | ✅ `AbortTaskRunError` explicit failure | Add `AbortWorkflowError` exception class |
| **Coordination** |
| Trigger-and-wait | ⚠️ `invoke_agent` action blocks, but no subtask coordination | ✅ `triggerAndWait()` with typed results | Add `invoke_and_wait` that returns agent output |
| Batch coordination | ⚠️ `parallel_group` action, no batching | ✅ `batchTriggerAndWait()` with 1,000-item limit | Add `batch_invoke` with chunking and aggregation |
| Human-in-the-loop | ❌ No approval primitives | ✅ Wait tokens with webhook/SDK completion | Add `wait_for_approval` action with token generation |
| Time-based waits | ⚠️ `wait` action via `time.sleep()` (blocks thread) | ✅ `wait.for()` releases concurrency | Make `wait` action checkpoint instead of sleep |
| External event wait | ❌ No webhook resume | ✅ Wait tokens with `token.url` callback | Add `wait_for_webhook` action with NATS pub/sub |
| **Scheduling** |
| Declarative cron | ❌ No code-based schedules | ✅ `cron` property in task definitions, synced on deploy | Add `schedules/` directory with YAML, auto-sync on startup |
| Imperative cron | ✅ APScheduler jobs via API | ✅ SDK's `schedules.create()` | AGENT-33's implementation is API-only, works |
| Timezone support | ⚠️ APScheduler supports, unclear in AGENT-33 config | ✅ IANA format, auto DST adjustment | Expose `timezone` in automation API |
| Deduplication keys | ❌ No schedule deduplication | ✅ `deduplicationKey` prevents duplicate creation | Add to `POST /v1/automation/schedules` |
| Delayed runs | ❌ No built-in delay | ✅ `delay: "1h"` or timestamp, `runs.reschedule()` | Add `delay` to workflow/agent invocation |
| Run TTL | ❌ No expiration | ✅ 10m default (dev), configurable per-run | Add `ttl` to `WorkflowRun`, expire in queue consumer |
| **Observability** |
| OpenTelemetry | ❌ Custom tracing in observability layer | ✅ Auto-instrumentation for tasks, HTTP, DB | Migrate to OpenTelemetry SDK, deprecate custom spans |
| Structured logging | ✅ `structlog` with key-value pairs | ✅ `logger.[level](msg, kvObject)` | AGENT-33's implementation is equivalent |
| Real-time trace view | ❌ Post-execution lineage only | ✅ Live step-by-step execution | Add WebSocket endpoint that streams checkpoint events |
| Metadata updates | ❌ Static checkpoint data | ✅ Progressive metadata mutation | Add `metadata` to `WorkflowRun`, update via action |
| Tagging | ❌ No run tags | ✅ Up to 10 tags, filterable in dashboard/API | Add `tags: List[str]` to `WorkflowRun`, index for filtering |
| Log retention | ❌ Unbounded logs | ✅ Tiered (1/7/30 days), 128KB I/O limit | Add `LOG_RETENTION_DAYS`, nightly cleanup job |
| Alerts | ⚠️ No built-in alerts | ✅ Email, Slack, webhooks for failures/deploys | Add `AlertConfig` model, send via NATS on failure |
| **Batching** |
| Batch trigger | ❌ No batch primitives | ✅ `batchTrigger()` with 1,000 items, rate limiting | Add `batch_invoke_agent()` with token bucket |
| Batch wait | ⚠️ `parallel_group` waits, no batching | ✅ `batchTriggerAndWait()` with result aggregation | Extend `parallel_group` to auto-chunk >1,000 tasks |
| Streaming batches | ❌ No async iteration | ✅ `AsyncIterable` for memory efficiency | Add generator support to `parallel_group` action |
| Batch error handling | ⚠️ `parallel_group` fails-fast or collects errors | ✅ `BatchTriggerError` with partial success | Improve `parallel_group` to return success/failure splits |
| **Idempotency** |
| Invocation-level keys | ❌ No deduplication at invoke | ✅ `idempotencyKey` per trigger | Add to `POST /v1/agents/{id}/invoke`, `/v1/workflows/execute` |
| Wait token idempotency | ❌ No wait primitives | ✅ Reusing key skips wait on retry (1h TTL) | Implement with wait action's idempotency |
| **Resource Management** |
| Machine presets | ❌ Single container resources | ✅ 7 CPU/RAM tiers, per-task or runtime override | Add `machine_preset` to agent defs, map to Docker limits |
| Resource monitoring | ❌ No built-in monitoring | ✅ `ResourceMonitor` for heap, memory, disk, GC, child processes | Add metrics collection to `CodeExecutor` |
| OOM retry escalation | ❌ No automatic retry-with-more-memory | ✅ Pattern: catch OOM → retry with larger machine | Implement in workflow executor's retry logic |
| **Extensibility** |
| Build hooks | ❌ No pre-deploy customization | ✅ `onBuildStart`, `onBuildComplete` | Add `pre_deploy_hooks` to config |
| Middleware | ❌ No lifecycle wrapping | ✅ Wraps all hooks, shares state via `locals` | Add middleware support to `WorkflowEngine` |
| Custom container layers | ❌ Dockerfile only | ✅ `addLayer()` API for deps, packages, env vars | Add to `engine/Dockerfile` build args |
| **Rate Limiting** |
| API rate limits | ❌ No global rate limiter | ✅ 1,500 req/min, mitigated by batch primitives | Add FastAPI middleware with token bucket |
| Batch rate limits | ❌ No batch system | ✅ Token bucket: 5,000 burst, 500/5s | Apply to batch primitives when added |
| **Payload Management** |
| Size limits | ❌ No enforcement | ✅ 3MB (single), 3MB per item (batch), auto-offload >512KB | Add validation + S3 offload to workflow executor |
| Output limits | ❌ No enforcement | ✅ 10MB max | Add to workflow executor, truncate or error |
| Object storage | ⚠️ Planned (S3/MinIO) | ✅ MinIO built-in for self-hosting | Integrate MinIO for offloaded payloads |
| **Deployment** |
| CI/CD integration | ⚠️ Manual Docker build/push | ✅ GitHub Actions with env vars, preview branches | Add `.github/workflows/deploy.yml` with trigger.dev pattern |
| Versioning | ❌ No version tracking | ✅ Auto-versioned deploys, pinning support | Add `version` to `WorkflowDefinition`, track in DB |
| Run replay | ❌ No replay | ✅ `runs.replay(runId)` | Add `POST /v1/workflows/{run_id}/replay` |

**Priority gaps to close**:
1. Checkpoint-at-wait (Phase 14: replace sleep-based `wait` action with NATS pub/sub resume)
2. Concurrency limiting (Phase 14: add to `GovernanceConstraints`, enforce in workflow executor)
3. Idempotency keys (Phase 14: add to invocation endpoints, store in Redis with TTL)
4. Batch primitives (Phase 15: `batch_invoke_agent`, `batch_execute_workflow`)
5. Wait tokens for human-in-the-loop (Phase 15: `wait_for_approval` action)
6. Real-time trace view (Phase 16: WebSocket endpoint streaming checkpoint events)
7. OpenTelemetry migration (Phase 16: replace custom tracing)

## 9) Evidence links

**Core documentation**:
- [Trigger.dev main site](https://trigger.dev/)
- [Tasks overview](https://trigger.dev/docs/tasks/overview) (execution model, checkpointing, lifecycle)
- [Errors & retrying](https://trigger.dev/docs/errors-retrying) (retry config, backoff, `catchError`, `AbortTaskRunError`)
- [Queue concurrency](https://trigger.dev/docs/queue-concurrency) (concurrency limits, `concurrencyKey`, deadlock prevention)
- [Runs](https://trigger.dev/docs/runs) (run lifecycle, statuses, programmatic management, idempotency)
- [Triggering tasks](https://trigger.dev/docs/triggering) (all trigger methods, batch operations, coordination primitives)
- [Wait for token](https://trigger.dev/docs/wait-for-token) (human-in-the-loop waitpoints, webhook callbacks)
- [Scheduled tasks (cron)](https://trigger.dev/docs/tasks/scheduled) (declarative/imperative, timezone handling)
- [Logging and tracing](https://trigger.dev/docs/logging) (structured logging, OpenTelemetry, custom spans)
- [Limits](https://trigger.dev/docs/limits) (concurrency, payloads, batches, queues, retention)
- [Machines](https://trigger.dev/docs/machines) (CPU/RAM presets, ResourceMonitor)
- [Custom build extensions](https://trigger.dev/docs/config/extensions/custom) (lifecycle hooks, esbuild customization, container layers)
- [Self-hosting (Docker)](https://trigger.dev/docs/self-hosting/docker) (infrastructure components, configuration, deployment)
- [GitHub Actions CI/CD](https://trigger.dev/docs/github-actions) (preview branches, versioning, deployment workflows)

**Blog & changelog**:
- [Observability & monitoring](https://trigger.dev/product/observability-and-monitoring) (real-time trace view, alerts)
- [Realtime API](https://trigger.dev/docs/realtime) (subscriptions, streaming, live updates)
- [Self-hosting v4 with Docker](https://trigger.dev/blog/self-hosting-trigger-dev-v4-docker) (setup guide)
- [Concurrency plan increases](https://trigger.dev/changelog/concurrency-plan-increases) (limits, pricing)
- [Declarative cron](https://trigger.dev/changelog/declarative-cron) (schedule sync on deploy)
- [Task delays and TTLs](https://trigger.dev/changelog/task-delays-and-timeouts) (delayed runs, run expiration)
- [v4 GA](https://trigger.dev/launchweek/2/trigger-v4-ga) (waitpoints, durable execution)

**Community & comparisons**:
- [GitHub repo](https://github.com/triggerdotdev/trigger.dev) (~13.6k stars, Apache 2.0)
- [APScheduler vs Celery](https://stackshare.io/stackups/apscheduler-vs-celery) (comparison: message broker, concurrency, complexity)
- [Creating modern workflow automation with Python](https://community.latenode.com/t/creating-a-modern-workflow-automation-platform-with-python-alternatives-to-make-celery-feel-more-like-trigger-dev/30107) (user comparison: Trigger.dev vs Celery)
- [Trigger.dev review 2026](https://aichief.com/ai-business-tools/trigger-dev/) (limitations: cold start, pricing)

**Referenced in search results**:
- [Scheduled tasks for v3](https://trigger.dev/changelog/scheduled-tasks) (cron evolution)
- [Trigger.dev product page](https://trigger.dev/product) (overview of features)
- [Self-hosting v4 with Kubernetes](https://trigger.dev/blog/self-hosting-trigger-dev-v4-kubernetes) (alternative deployment)
- [Docker templates repo](https://github.com/triggerdotdev/docker) (self-hosting templates)
- [Pricing](https://trigger.dev/pricing) (concurrency tiers, invocation costs)
