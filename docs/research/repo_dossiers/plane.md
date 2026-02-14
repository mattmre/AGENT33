# Repo Dossier: makeplane/plane

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

Plane is an open-source project management and issue tracking platform (40k+ GitHub stars) designed as a self-hostable alternative to Jira, Linear, and Asana. It targets engineering teams and organizations that want full data sovereignty over their project management tooling. The primary interface is a web application (Next.js frontend, Django/DRF backend) with a comprehensive REST API. Its core organizational primitive is the **Workspace** -- a tenant boundary that contains Projects, which in turn contain Issues organized via Cycles (time-boxed sprints), Modules (feature groupings), and Views (saved filters). Plane is not an agent orchestration framework, but its mature multi-tenancy model, issue state machine, webhook automation, and API design patterns are directly relevant to AGENT-33's architecture gaps.

## 2) Core orchestration model

Plane is not an orchestration framework -- it is an issue-tracking and project management tool. However, it implements several workflow and state management patterns relevant to AGENT-33:

- **Primary primitive:** Issue lifecycle management with configurable state machines. Each Project defines its own set of States grouped into five categories (Backlog, Unstarted, Started, Completed, Cancelled). Transitions between states are unconstrained by default but can be governed by automations.
- **State model:** Explicit database-backed state. Every Issue has a `state_id` FK referencing a project-scoped `State` model. State changes are tracked via `IssueActivity` audit records. Workflow state is always persisted in PostgreSQL, never held in memory only.
- **Concurrency:** Web requests are handled by Gunicorn/Uvicorn workers. Background tasks (email, notifications, webhooks, analytics aggregation) run via Celery with Redis as broker. Real-time updates use Django Channels with WebSocket transport backed by Redis channel layers.
- **Human-in-the-loop:** All issue transitions are human-initiated through the UI or API. Automations (auto-close stale issues, auto-assign, auto-archive completed) run on configurable rules but do not require approval -- they execute automatically once configured by a project admin.

## 3) Tooling and execution

- **Tool interface:** REST API (Django REST Framework). All endpoints versioned under `/api/v1/`. OpenAPI schema available. Third-party integrations connect via OAuth2 apps and webhooks. GitHub integration syncs issues bidirectionally. Slack integration posts notifications. No function-calling, MCP, or JSON-RPC -- integrations are webhook/API-based.
- **Runtime environment:** Self-hosted via Docker Compose (recommended) or Kubernetes (Helm charts available). The stack includes: Django API server, Next.js web app, PostgreSQL, Redis, Celery workers, Minio (object storage), and an optional SMTP relay. Plane Cloud is the hosted SaaS option.
- **Sandboxing / safety controls:** No code execution sandbox -- Plane does not execute user-provided code. Security controls include: CORS configuration, CSRF protection, rate limiting middleware, CSP headers, input sanitization via Django's ORM (parameterized queries), file upload validation (type, size limits), and API key scoping.

## 4) Observability and evaluation

- **Tracing/logging:** Django's built-in logging framework with configurable levels per module. Sentry integration for error tracking in production. No distributed tracing (no OpenTelemetry/Jaeger integration). Celery task execution is logged with task IDs for correlation.
- **Evaluation harness:** Standard Django test suite using pytest-django. No SWE-bench or automated evaluation. Analytics module tracks issue velocity, cycle burndown, and project-level metrics (created vs. completed over time). These are product analytics, not system evaluation.
- **Audit trail:** `IssueActivity` model records every field change on an issue with actor, timestamp, old value, and new value. This is the primary accountability mechanism. Workspace-level audit logs track membership changes and settings modifications.

## 5) Extensibility

- **Where extensions live:** Integrations are implemented as Django apps within `apiserver/plane/app/`. The GitHub integration lives alongside core code. Webhooks enable external extension without modifying the codebase. The `space/` app provides embeddable public project views.
- **How to add tools/skills:** Register a new Webhook endpoint via the API (`POST /api/v1/workspaces/{slug}/webhooks/`) to receive events (issue.created, issue.updated, cycle.completed, etc.). For deeper integration, implement a new Django app in `apiserver/plane/app/` with DRF viewsets, register URLs in the router, and add models via Django migrations. There is no plugin marketplace or dynamic plugin loading.
- **Config surface:** Environment variables for all infrastructure (DATABASE_URL, REDIS_URL, SECRET_KEY, etc.) loaded via `django-environ`. Instance-level settings stored in the `Instance` model (configurable via admin panel): email provider, AI features toggle, telemetry opt-out, file storage backend, authentication methods (Google OAuth, GitHub OAuth, magic link, password).

## 6) Notable practices worth adopting in AGENT-33

- **Workspace-scoped URL namespacing.** Every Plane API endpoint is scoped: `/api/v1/workspaces/{workspace_slug}/projects/{project_id}/issues/`. The workspace slug is resolved in middleware and attached to the request context. This prevents IDOR by construction -- queries are always filtered by the workspace from the URL path, not just from the JWT. AGENT-33's routes (`/v1/workflows/{name}`) lack tenant scoping in the URL structure. Adding `/v1/tenants/{tenant_id}/workflows/{name}` would make tenant isolation structural rather than relying solely on middleware filtering.

- **Base model mixin with audit fields.** Every Plane model inherits from `BaseModel` which provides `id` (UUID4 PK), `created_at`, `updated_at`, `created_by` (FK to User), `updated_by` (FK to User), and uses a soft-delete pattern. This makes every database record attributable and recoverable. AGENT-33's workflow and agent models lack audit fields -- adding `created_by`, `updated_by`, `created_at`, `updated_at` to all persistent models would support governance requirements.

- **Per-project configurable state machines.** Plane does not hardcode issue states. Each project defines its own states within five fixed groups (Backlog, Unstarted, Started, Completed, Cancelled). This gives teams flexibility while maintaining queryable state groups for cross-project analytics. AGENT-33's `WorkflowStep` has a fixed `StepAction` enum. Allowing user-defined step types within fixed action groups (invoke, transform, validate, execute) would enable customization without breaking the execution engine.

- **Hierarchical role-based access with workspace and project scopes.** Plane implements three-level RBAC: Instance Admin (super-admin), Workspace roles (Owner, Admin, Member, Guest), and Project roles (Admin, Member, Viewer, Guest). Each level inherits permissions and can restrict further. A Workspace Member who is a Project Viewer cannot edit issues in that project. AGENT-33's scope-based auth (`["admin"]`) is flat. Adopting hierarchical scopes like `workspace:admin`, `project:{id}:member` would enable finer-grained access control.

- **Webhook event system with retry and failure tracking.** Plane's webhook system sends HTTP POST requests on configurable events (issue CRUD, cycle changes, module updates). Failed deliveries are retried with exponential backoff. Webhook logs show delivery status, response codes, and payloads for debugging. AGENT-33's `automation/webhooks.py` could adopt this pattern -- storing delivery attempts with status codes enables operators to diagnose integration failures.

- **Activity stream as append-only audit log.** Every mutation to an Issue generates an `IssueActivity` record capturing the actor, field changed, old value, new value, and timestamp. This is never deleted and serves as both an audit trail and a user-facing activity feed. AGENT-33's observability module (`observability/lineage.py`) could adopt this pattern for workflow step executions -- recording every state transition as an immutable activity record.

## 7) Risks / limitations to account for

- **No agent or automation orchestration.** Plane is a project management UI, not a workflow engine. Its "automations" are simple rule-based triggers (if state=X for N days, then transition to Y). There is no DAG execution, no conditional branching, no parallel step execution. AGENT-33 should not look to Plane for orchestration patterns -- those come from n8n, Trigger.dev, and similar tools. Plane's value to AGENT-33 is in its data model and API design, not its execution model.

- **Monolithic Django architecture limits scalability patterns.** Plane runs as a single Django application with Celery for background tasks. There is no microservice decomposition, no event sourcing, no CQRS. For AGENT-33's FastAPI-based architecture, adopting Plane's data model patterns is straightforward, but its deployment architecture (Gunicorn + Celery + Redis) is not a model to follow for a system that needs real-time agent orchestration with sub-second latency.

- **Multi-tenancy is application-level, not database-level.** Plane uses shared-database multi-tenancy with workspace_id filtering in querysets. There is no row-level security (PostgreSQL RLS), no schema-per-tenant, no database-per-tenant. Every query must correctly filter by workspace. A missed filter is a data leak. AGENT-33 faces the same risk -- the next-session.md notes "tenant_id missing from TokenPayload" as a HIGH severity gap. Plane's approach works but requires discipline; PostgreSQL RLS would be more defensive.

- **WebSocket scaling requires sticky sessions.** Plane's real-time updates use Django Channels with Redis channel layers. In multi-instance deployments, WebSocket connections must be routed to the same instance (sticky sessions) or use Redis pub/sub for cross-instance communication. AGENT-33 uses NATS for messaging, which is architecturally superior for this use case (no sticky sessions needed).

- **No API versioning strategy beyond /v1/.** Plane has a single API version (`/api/v1/`). There is no deprecation policy, no version negotiation, no API changelog. As the API evolves, breaking changes are introduced without a migration path. AGENT-33 should plan for API versioning from the start -- adding `/v2/` support with a deprecation timeline before the API surface grows too large.

## 8) Feature extraction (for master matrix)

- **Interfaces:** Web UI (Next.js), REST API (Django REST Framework), WebSocket (Django Channels), CLI (limited -- mostly for admin tasks), embeddable public pages (`space/` app)
- **Orchestration primitives:** Issue state machine with configurable states per project, Cycles (time-boxed sprints), Modules (feature groupings), rule-based automations (auto-close, auto-assign, auto-archive)
- **State/persistence:** PostgreSQL with UUID PKs, all models have audit fields (created_at, updated_at, created_by, updated_by), soft-delete pattern, Redis for caching and Celery broker, Minio for file storage
- **HITL controls:** All issue transitions are human-initiated. Automations are admin-configured rules that execute without approval. No approval workflows or confirmation gates for state changes.
- **Sandboxing:** Not applicable -- no code execution. Input sanitization via Django ORM parameterized queries. File upload validation. CSP headers.
- **Observability:** Django logging, Sentry error tracking, IssueActivity audit trail (every field change), analytics module (velocity, burndown), webhook delivery logs. No distributed tracing.
- **Evaluation:** pytest-django test suite. Product analytics (issue velocity, cycle burndown). No automated system evaluation, no benchmarks.
- **Extensibility:** Webhooks (configurable per workspace, event-driven), OAuth2 app integrations (GitHub, Slack), public API, embeddable views. No plugin marketplace or dynamic extension loading.

## 9) Evidence links

The following sources informed this dossier:

1. **GitHub Repository**: https://github.com/makeplane/plane -- Main codebase, monorepo structure (apiserver/, web/, space/, admin/, deploy/)
2. **Plane Documentation**: https://docs.plane.so/ -- Official documentation covering setup, API reference, and feature guides
3. **API Server Structure**: https://github.com/makeplane/plane/tree/master/apiserver/plane -- Django backend with db/models/, app/views/, app/serializers/, middleware/
4. **Database Models**: https://github.com/makeplane/plane/tree/master/apiserver/plane/db/models -- BaseModel mixin, Issue, State, Cycle, Module, Workspace, Project models
5. **Docker Compose Deployment**: https://github.com/makeplane/plane/tree/master/deploy/selfhost -- Self-hosted deployment configuration with all service definitions
6. **Webhook Implementation**: https://github.com/makeplane/plane/blob/master/apiserver/plane/app/views/webhook/ -- Webhook CRUD and event dispatch
7. **Authentication and Permissions**: https://github.com/makeplane/plane/tree/master/apiserver/plane/app/permissions.py -- Role-based permission classes (WorkspacePermission, ProjectPermission)
8. **Issue Activity Tracking**: https://github.com/makeplane/plane/blob/master/apiserver/plane/db/models/issue.py -- IssueActivity model and change tracking
9. **State Management**: https://github.com/makeplane/plane/blob/master/apiserver/plane/db/models/state.py -- Per-project configurable states with state groups
10. **Workspace Multi-Tenancy**: https://github.com/makeplane/plane/blob/master/apiserver/plane/db/models/workspace.py -- Workspace model as tenant boundary with membership roles
11. **Plane Blog - Architecture**: https://plane.so/blog -- Technical blog posts about architecture decisions
12. **GitHub Integration**: https://github.com/makeplane/plane/tree/master/apiserver/plane/app/views/integration/ -- GitHub bidirectional sync implementation
