# OpenClaw Track Phase 1: Operator Shell Reset & Route-Based Control Plane

Date: 2026-03-10
Session: 59
Status: Architecture Document (research only, no code)

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Operator Shell Reset](#1-operator-shell-reset)
3. [Route-Based Control Plane](#2-route-based-control-plane)
4. [Frontend Integration](#3-frontend-integration)
5. [API Endpoints (Detailed)](#4-api-endpoints-detailed)
6. [Test Strategy](#5-test-strategy)
7. [File Layout](#6-file-layout)
8. [Implementation Sequencing](#7-implementation-sequencing)

---

## Executive Summary

Track Phase 1 replaces AGENT-33's monolithic tab shell with a route-based operator UI and introduces a dedicated operator control plane API namespace. The current frontend (`App.tsx`) uses a flat `AppTab` state variable to switch between six hardcoded panels (Chat, Voice, Integrations, Operations, Outcomes, Advanced Settings). Operator-relevant surfaces like tools, plugins, packs, sessions, and backups are buried under the "Advanced Settings" tab inside a domain-panel sidebar with 24 entries. This makes it impossible for operators to reach critical surfaces without navigating through a taxonomy-first tree.

The fix has two layers:

- **Backend**: A new `/api/v1/operator/` route namespace that aggregates system status, subsystem inventories, and operator actions into a purpose-built control plane API.
- **Frontend**: Replace the tab-based shell with a React Router application that gives each operator concern its own URL, enabling direct navigation, bookmarks, and link sharing.

### What This Phase Does NOT Include

- Runtime tool catalog endpoint (Track Phase 2)
- Plugin install/update/doctor flows (Track Phase 3)
- Pack marketplace (Track Phase 4)
- Backup create/verify (Track Phase 6)

Those phases build on top of the shell and route infrastructure delivered here.

---

## 1. Operator Shell Reset

### What "Operator Shell" Means in AGENT-33 Context

The operator shell is the outermost navigation and layout frame of the AGENT-33 frontend. It controls:

- What top-level destinations exist
- How users switch between them
- What persistent affordances (status, notifications, search) are always visible
- Whether the interface is organized around operator tasks or technical taxonomy

Today, the shell is `App.tsx`: a single component with a `useState<AppTab>` that conditionally renders one of six panels. This is a monolithic shell. Adding a new top-level destination requires editing `App.tsx`, adding a new tab entry, and adding a new conditional render block. There is no URL routing, no deep linking, and no way for an operator to bookmark "the plugins page."

### Operator Shell Reset Goals

1. Replace tab-based navigation with URL-based routing.
2. Separate operator control plane from end-user interaction (chat, voice).
3. Create dedicated top-level pages for: tools, plugins, packs, sessions, backups, and operations.
4. Add persistent status, search, and notification affordances to the shell frame.
5. Make navigation testable and keyboard-accessible.

### CLI Commands for Operator Control

The existing CLI (`engine/src/agent33/cli/main.py`) has four commands: `init`, `run`, `test`, `status`. Track Phase 1 extends this with operator-oriented commands that call the new operator API:

| Command | Description | Backend Route |
| --- | --- | --- |
| `agent33 status` | System health (already exists) | `GET /health` |
| `agent33 operator status` | Operator control plane summary | `GET /v1/operator/status` |
| `agent33 operator config` | Show effective runtime config (redacted) | `GET /v1/operator/config` |
| `agent33 operator doctor` | Run diagnostics and report issues | `GET /v1/operator/doctor` |
| `agent33 operator reset` | Reset operator state (clear caches, reload registries) | `POST /v1/operator/reset` |

The `status` command already calls `/health`. The new `operator` subgroup calls the new operator namespace. These CLI commands are thin HTTP clients (like the existing `status` and `run` commands) that format the JSON response for terminal output.

### Mapping to Existing `agent33 status`

The existing `agent33 status` command calls `GET /health` and prints the result. It stays unchanged. The new `agent33 operator status` is a superset: it includes health data plus subsystem inventories (agent count, tool count, plugin count, pack count, active workflow count, pending approvals). The operator status endpoint internally calls the health check and enriches it.

---

## 2. Route-Based Control Plane

### New API Namespace: `/api/v1/operator/`

All operator-specific endpoints live under `/v1/operator/`. This namespace is for system-level introspection and control, not for per-entity CRUD (which stays in existing routes like `/v1/plugins/`, `/v1/packs/`, etc.).

The operator namespace provides:

1. **Aggregated status** — one call to understand system state
2. **Subsystem inventories** — counts and summaries without needing to call each subsystem
3. **Operator actions** — reset, doctor, config inspection
4. **Navigation metadata** — what pages/features are available and their health status

### Route-Level Access Control

Three roles interact with the operator control plane:

| Role | Scopes | Access Level |
| --- | --- | --- |
| **User** | `agents:read`, `workflows:read`, etc. | Can view chat, voice, their own sessions. No operator routes. |
| **Operator** | `operator:read`, `operator:write` | Can view all operator pages, run doctor, view config. Cannot reset or change system state without `operator:write`. |
| **Admin** | `admin` | Full access. Can reset, modify config, reload registries. |

New scopes to add to `engine/src/agent33/security/permissions.py`:

```python
"operator:read",   # view operator status, config, inventories
"operator:write",  # reset, reload, apply config changes
```

The `admin` scope already grants all permissions via the existing wildcard logic in `check_permission_decision()`.

### Dedicated Pages

Track Phase 1 establishes the route structure. Some pages will be skeletal until later phases deliver their backend contracts.

| Page Route | Title | Backend Source | Phase |
| --- | --- | --- | --- |
| `/` | Chat Central | Existing chat routes | Existing |
| `/voice` | Voice Call | Existing multimodal routes | Existing |
| `/operator` | Operator Home | `GET /v1/operator/status` | Phase 1 |
| `/operator/tools` | Tools | `GET /v1/tools/catalog` (Phase 2) | Skeleton in 1, filled in 2 |
| `/operator/plugins` | Plugins | `GET /v1/plugins` | Phase 1 (existing API) |
| `/operator/packs` | Packs | `GET /v1/packs` | Phase 1 (existing API) |
| `/operator/sessions` | Sessions | `GET /v1/operator/sessions` | Phase 1 (new API) |
| `/operator/backups` | Backups | `GET /v1/operator/backups` (Phase 6) | Skeleton in 1, filled in 6 |
| `/operator/operations` | Operations Hub | `GET /v1/operations/hub` | Phase 1 (existing API) |
| `/operator/config` | Configuration | `GET /v1/operator/config` | Phase 1 |
| `/operator/doctor` | Diagnostics | `GET /v1/operator/doctor` | Phase 1 |
| `/settings` | User Settings | Auth panel, integrations | Existing (relocated) |

### Health Check and System Status Endpoints

The existing `GET /health` endpoint checks Ollama, Redis, PostgreSQL, OpenAI, ElevenLabs, Jina, NATS, and messaging channels. It returns `{ status: "healthy"|"degraded", services: {...} }`.

The new operator status endpoint builds on this:

```
GET /v1/operator/status
```

Response shape:

```json
{
  "health": { "status": "healthy", "services": { ... } },
  "inventories": {
    "agents": { "count": 6, "loaded": true },
    "tools": { "count": 12, "loaded": true },
    "plugins": { "count": 3, "active": 2, "loaded": true },
    "packs": { "count": 5, "enabled": 4, "loaded": true },
    "skills": { "count": 18, "loaded": true },
    "hooks": { "count": 7, "enabled": true },
    "workflows": { "active": 2, "total": 15 }
  },
  "runtime": {
    "version": "0.1.0",
    "python_version": "3.11.x",
    "uptime_seconds": 3600,
    "start_time": "2026-03-10T08:00:00Z"
  },
  "pending": {
    "approvals": 0,
    "reviews": 1,
    "improvements": 3
  }
}
```

---

## 3. Frontend Integration

### Current State

The frontend is a single-page application in `frontend/src/`. Key facts:

- Entry point: `main.tsx` renders `App.tsx`
- No React Router — navigation is `useState<AppTab>`
- 24 domain panels under Advanced Settings, each a config-driven API caller
- Operations Hub and Outcomes Dashboard are dedicated feature panels
- Global search exists but only searches the current domain list
- No URL routing, no deep linking, no browser back/forward support

### Required Changes

#### 3.1 Install React Router

Add `react-router-dom` to the frontend dependencies. The application will use `BrowserRouter` with `Routes` and `Route` components.

#### 3.2 New Layout Components

**AppShell** (`frontend/src/layout/AppShell.tsx`)

The persistent outer frame. Contains:

- Top bar with logo, global search, notification badge, user menu
- Primary navigation (sidebar or top nav, depending on viewport)
- Outlet for routed content
- Persistent status bar at the bottom showing system health summary

**OperatorLayout** (`frontend/src/layout/OperatorLayout.tsx`)

A sub-layout for `/operator/*` routes. Contains:

- Operator-specific sidebar navigation (Tools, Plugins, Packs, Sessions, Backups, Operations, Config, Doctor)
- Breadcrumb trail
- Outlet for operator page content

**UserLayout** (`frontend/src/layout/UserLayout.tsx`)

A sub-layout for user-facing routes (`/`, `/voice`, `/settings`). Contains:

- Minimal chrome around chat and voice
- Outlet for user page content

#### 3.3 New Pages

| File | Route | Content |
| --- | --- | --- |
| `frontend/src/pages/ChatPage.tsx` | `/` | Wraps existing `ChatInterface` |
| `frontend/src/pages/VoicePage.tsx` | `/voice` | Wraps existing `LiveVoicePanel` |
| `frontend/src/pages/SettingsPage.tsx` | `/settings` | Auth panel, integrations setup |
| `frontend/src/pages/operator/HomePage.tsx` | `/operator` | System status dashboard, inventories, pending items |
| `frontend/src/pages/operator/ToolsPage.tsx` | `/operator/tools` | Placeholder until Phase 2 delivers catalog API |
| `frontend/src/pages/operator/PluginsPage.tsx` | `/operator/plugins` | List/search/enable/disable plugins (wired to existing API) |
| `frontend/src/pages/operator/PacksPage.tsx` | `/operator/packs` | List/search/enable/disable packs (wired to existing API) |
| `frontend/src/pages/operator/SessionsPage.tsx` | `/operator/sessions` | Session catalog (new API) |
| `frontend/src/pages/operator/BackupsPage.tsx` | `/operator/backups` | Placeholder until Phase 6 |
| `frontend/src/pages/operator/OperationsPage.tsx` | `/operator/operations` | Wraps existing `OperationsHubPanel` |
| `frontend/src/pages/operator/ConfigPage.tsx` | `/operator/config` | Runtime config viewer (redacted secrets) |
| `frontend/src/pages/operator/DoctorPage.tsx` | `/operator/doctor` | Diagnostics results |
| `frontend/src/pages/operator/OutcomesPage.tsx` | `/operator/outcomes` | Wraps existing `OutcomesDashboardPanel` |

#### 3.4 Navigation Structure

Primary nav (always visible in top bar):

```
Chat  |  Voice  |  Operator  |  Settings
```

Operator sidebar (visible when on `/operator/*` routes):

```
Home
---
Tools
Plugins
Packs
---
Sessions
Operations
Outcomes
---
Backups
Config
Doctor
```

#### 3.5 Preserving the Advanced Settings Panel

The current "Advanced Settings" tab with its 24 domain panels is retained as a legacy compatibility route at `/operator/advanced`. This prevents any loss of functionality during migration. Individual domain panels will be promoted to first-class pages in later phases as their APIs mature. The `domains.ts` registry and `DomainPanel` component remain unchanged.

#### 3.6 Responsive Behavior

- On desktop (>1024px): sidebar navigation is always visible
- On tablet (768-1024px): sidebar collapses to icons, expands on hover
- On mobile (<768px): sidebar becomes a hamburger menu overlay

---

## 4. API Endpoints (Detailed)

### 4.1 Operator Status and System Info

```
GET /v1/operator/status
Scope: operator:read
```

Returns aggregated system health, subsystem inventories, runtime info, and pending items. Implementation reads from `app.state` to count registries without making external calls (health check data is fetched from the existing health endpoint internally).

```
GET /v1/operator/info
Scope: operator:read
```

Returns static runtime info: version, Python version, platform, start time, configuration summary (feature flags, enabled subsystems).

### 4.2 Operator Config

```
GET /v1/operator/config
Scope: operator:read
```

Returns the effective runtime configuration with all `SecretStr` fields redacted to `"***"`. Groups settings by subsystem (database, redis, nats, ollama, security, plugins, packs, skills, etc.). Does not expose raw secret values.

Response shape:

```json
{
  "groups": {
    "database": {
      "database_url": "***@db-host:5432/agent33",
      "pool_size": 5
    },
    "redis": {
      "redis_url": "redis://redis-host:6379/0"
    },
    "agents": {
      "agent_definitions_dir": "agent-definitions",
      "definitions_count": 6
    }
  },
  "feature_flags": {
    "hooks_enabled": true,
    "training_enabled": false,
    "airllm_enabled": false,
    "bm25_warmup_enabled": true,
    "rag_hybrid_enabled": true,
    "embedding_cache_enabled": true,
    "plugin_auto_enable": true
  }
}
```

### 4.3 Operator Doctor

```
GET /v1/operator/doctor
Scope: operator:read
```

Runs a series of diagnostic checks and returns results with severity and remediation guidance.

Check categories:

| Check ID | Category | What It Checks |
| --- | --- | --- |
| `DOC-01` | Database | PostgreSQL connectivity and pgvector extension |
| `DOC-02` | Redis | Redis connectivity and ping |
| `DOC-03` | NATS | NATS connectivity |
| `DOC-04` | LLM | Ollama/OpenAI provider reachability |
| `DOC-05` | Agents | Agent definitions directory exists and has valid JSON |
| `DOC-06` | Skills | Skills directory exists and has valid SKILL.md files |
| `DOC-07` | Plugins | Plugin directory exists, all plugins in valid state |
| `DOC-08` | Packs | Pack directory exists, all packs loadable |
| `DOC-09` | Security | JWT secret is not default, DB credentials are not default |
| `DOC-10` | Config | No deprecated or conflicting config values |

Response shape:

```json
{
  "overall": "warning",
  "checks": [
    {
      "id": "DOC-01",
      "category": "database",
      "status": "ok",
      "message": "PostgreSQL connected",
      "remediation": null
    },
    {
      "id": "DOC-09",
      "category": "security",
      "status": "warning",
      "message": "JWT secret is using default value",
      "remediation": "Set JWT_SECRET environment variable to a cryptographically random value"
    }
  ],
  "timestamp": "2026-03-10T12:00:00Z"
}
```

### 4.4 Operator Reset

```
POST /v1/operator/reset
Scope: operator:write
Body: { "targets": ["caches", "registries", "all"] }
```

Resets specified operator state:

- `caches`: Clears embedding cache, BM25 index, any in-memory caches
- `registries`: Re-discovers agents, skills, plugins, packs from disk
- `all`: Both of the above

Returns a report of what was reset and any errors encountered.

### 4.5 Tools Listing (Existing + Bridge)

Tools already exist in the `ToolRegistry` on `app.state.tool_registry`. Track Phase 1 adds a lightweight bridge endpoint so the operator tools page has something to render before Phase 2 delivers the full catalog.

```
GET /v1/operator/tools/summary
Scope: operator:read
```

Response:

```json
{
  "tools": [
    {
      "name": "shell",
      "source": "builtin",
      "status": "active",
      "has_schema": true
    }
  ],
  "count": 12,
  "note": "Full catalog with grouping, provenance, and availability coming in Track Phase 2"
}
```

### 4.6 Plugin Listing and Management

Existing endpoints under `/v1/plugins/` already provide list, search, detail, enable, disable, reload, config, health, and discover. The operator plugins page calls these directly. No new backend endpoints needed for Phase 1.

Existing endpoints used:

- `GET /v1/plugins` — list all plugins
- `GET /v1/plugins/search?q=...` — search
- `GET /v1/plugins/{name}` — detail
- `POST /v1/plugins/{name}/enable` — enable
- `POST /v1/plugins/{name}/disable` — disable
- `POST /v1/plugins/{name}/reload` — hot reload (admin)
- `GET /v1/plugins/{name}/health` — health check
- `GET /v1/plugins/{name}/config` — get config
- `PUT /v1/plugins/{name}/config` — update config
- `POST /v1/plugins/discover` — re-scan (admin)

### 4.7 Pack Listing and Management

Existing endpoints under `/v1/packs/` already provide list, list enabled, search, detail, install, uninstall, enable, disable, and sync. The operator packs page calls these directly. No new backend endpoints needed for Phase 1.

Existing endpoints used:

- `GET /v1/packs` — list all packs
- `GET /v1/packs/enabled` — list tenant-enabled packs
- `GET /v1/packs/search?q=...` — search
- `GET /v1/packs/{name}` — detail
- `POST /v1/packs/install` — install
- `DELETE /v1/packs/{name}` — uninstall
- `POST /v1/packs/{name}/enable` — enable
- `POST /v1/packs/{name}/disable` — disable
- `POST /v1/packs/{name}/sync` — re-scan

### 4.8 Session Management

Sessions do not currently have a dedicated API surface. Track Phase 1 adds a lightweight session catalog endpoint. Full session management (Track Phase 8) builds on this.

```
GET /v1/operator/sessions
Scope: operator:read
Query params: status, limit, offset, since
```

Response:

```json
{
  "sessions": [
    {
      "session_id": "...",
      "type": "chat",
      "status": "active",
      "agent": "orchestrator",
      "started_at": "2026-03-10T08:30:00Z",
      "last_activity": "2026-03-10T09:15:00Z",
      "message_count": 12,
      "tenant_id": "default"
    }
  ],
  "count": 5,
  "total": 42
}
```

Implementation: The session catalog reads from the memory/session state layer. If `LongTermMemory` or Redis session tracking is available, it enumerates active and recent sessions. If neither is available, it returns an empty list with a `degraded: true` flag.

```
GET /v1/operator/sessions/{session_id}
Scope: operator:read
```

Returns session detail: transcript summary, agent, model, duration, token usage.

### 4.9 Backup Management (Skeleton)

Track Phase 1 registers the backup routes with placeholder responses. Phase 6 fills them in.

```
GET /v1/operator/backups
Scope: operator:read
```

Response (Phase 1):

```json
{
  "backups": [],
  "count": 0,
  "note": "Archive-grade backup management coming in Track Phase 6"
}
```

---

## 5. Test Strategy

### 5.1 Backend Route Tests

Each new operator endpoint gets a dedicated test file. Tests use `TestClient` with mocked `app.state` dependencies.

| Test File | Coverage |
| --- | --- |
| `tests/test_api_operator_status.py` | `GET /v1/operator/status` — verify response shape, inventory counts from mocked registries, health aggregation |
| `tests/test_api_operator_config.py` | `GET /v1/operator/config` — verify SecretStr redaction, group structure, feature flags |
| `tests/test_api_operator_doctor.py` | `GET /v1/operator/doctor` — verify check execution, status rollup, remediation messages |
| `tests/test_api_operator_reset.py` | `POST /v1/operator/reset` — verify cache clearing, registry rediscovery, error handling |
| `tests/test_api_operator_tools_summary.py` | `GET /v1/operator/tools/summary` — verify tool listing from mocked registry |
| `tests/test_api_operator_sessions.py` | `GET /v1/operator/sessions` — verify session catalog, filtering, pagination |
| `tests/test_api_operator_backups.py` | `GET /v1/operator/backups` — verify skeleton response |
| `tests/test_api_operator_auth.py` | Verify all operator endpoints require `operator:read` or `operator:write` scope, return 401/403 without proper auth |

**Test quality requirements** (per CLAUDE.md anti-corner-cutting rules):

- Every test asserts on response body shape, not just status codes
- Auth tests verify both 401 (no token) and 403 (insufficient scope)
- Doctor tests mock individual check failures and verify the correct check ID, status, and remediation appear in the response
- Reset tests verify that the mocked registry's `discover()` method was actually called
- Config tests verify that known SecretStr fields appear as `"***"` in the response

### 5.2 CLI Tests

| Test File | Coverage |
| --- | --- |
| `tests/test_cli_operator.py` | `agent33 operator status`, `config`, `doctor`, `reset` — verify HTTP calls and output formatting |

### 5.3 Frontend Component Tests

Using Vitest + Testing Library (already configured in the frontend).

| Test File | Coverage |
| --- | --- |
| `frontend/src/layout/AppShell.test.tsx` | Renders nav items, highlights active route, shows health badge |
| `frontend/src/layout/OperatorLayout.test.tsx` | Renders sidebar, highlights active operator route |
| `frontend/src/pages/operator/HomePage.test.tsx` | Fetches and displays status data, handles loading/error states |
| `frontend/src/pages/operator/PluginsPage.test.tsx` | Lists plugins, enable/disable interactions |
| `frontend/src/pages/operator/PacksPage.test.tsx` | Lists packs, search interaction |
| `frontend/src/pages/operator/ConfigPage.test.tsx` | Displays grouped config, verifies secrets are redacted |
| `frontend/src/pages/operator/DoctorPage.test.tsx` | Displays check results with severity colors and remediation |

### 5.4 Integration Tests

| Test File | Coverage |
| --- | --- |
| `tests/test_operator_integration.py` | Full lifespan startup, verify operator status returns real inventory counts from initialized registries |

### 5.5 Navigation Tests

| Test File | Coverage |
| --- | --- |
| `frontend/src/navigation.test.tsx` | Route matching, keyboard navigation (Tab/Enter), browser back/forward with mocked router |

---

## 6. File Layout

### New Files to Create

#### Backend

```
engine/src/agent33/api/routes/operator.py          # Operator control plane router
engine/src/agent33/services/operator.py             # Operator service (status, config, doctor, reset)
engine/src/agent33/services/doctor.py               # Doctor check runner
engine/src/agent33/cli/operator.py                  # CLI operator subcommand group

tests/test_api_operator_status.py
tests/test_api_operator_config.py
tests/test_api_operator_doctor.py
tests/test_api_operator_reset.py
tests/test_api_operator_tools_summary.py
tests/test_api_operator_sessions.py
tests/test_api_operator_backups.py
tests/test_api_operator_auth.py
tests/test_cli_operator.py
tests/test_operator_integration.py
```

#### Frontend

```
frontend/src/layout/AppShell.tsx                    # Root layout with nav and outlet
frontend/src/layout/OperatorLayout.tsx              # Operator sub-layout with sidebar
frontend/src/layout/UserLayout.tsx                  # User-facing sub-layout
frontend/src/layout/AppShell.test.tsx
frontend/src/layout/OperatorLayout.test.tsx

frontend/src/pages/ChatPage.tsx                     # Wraps ChatInterface
frontend/src/pages/VoicePage.tsx                    # Wraps LiveVoicePanel
frontend/src/pages/SettingsPage.tsx                 # Auth + integrations

frontend/src/pages/operator/HomePage.tsx            # Operator dashboard
frontend/src/pages/operator/ToolsPage.tsx           # Tools (skeleton for Phase 2)
frontend/src/pages/operator/PluginsPage.tsx         # Plugins management
frontend/src/pages/operator/PacksPage.tsx           # Packs management
frontend/src/pages/operator/SessionsPage.tsx        # Session catalog
frontend/src/pages/operator/BackupsPage.tsx         # Backups (skeleton for Phase 6)
frontend/src/pages/operator/OperationsPage.tsx      # Wraps OperationsHubPanel
frontend/src/pages/operator/OutcomesPage.tsx        # Wraps OutcomesDashboardPanel
frontend/src/pages/operator/ConfigPage.tsx          # Runtime config viewer
frontend/src/pages/operator/DoctorPage.tsx          # Diagnostics
frontend/src/pages/operator/AdvancedPage.tsx        # Legacy domain panel grid

frontend/src/pages/operator/HomePage.test.tsx
frontend/src/pages/operator/PluginsPage.test.tsx
frontend/src/pages/operator/PacksPage.test.tsx
frontend/src/pages/operator/ConfigPage.test.tsx
frontend/src/pages/operator/DoctorPage.test.tsx

frontend/src/navigation.test.tsx
frontend/src/router.tsx                             # Route definitions
```

### Existing Files to Modify

#### Backend

| File | Change |
| --- | --- |
| `engine/src/agent33/main.py` | Import and include `operator.router`; store `start_time` on `app.state` for uptime calculation |
| `engine/src/agent33/security/permissions.py` | Add `"operator:read"` and `"operator:write"` to `SCOPES` set |
| `engine/src/agent33/cli/main.py` | Add `operator` subcommand group via `app.add_typer()` |
| `engine/src/agent33/config.py` | No changes needed (config is already readable via `settings`) |

#### Frontend

| File | Change |
| --- | --- |
| `frontend/src/App.tsx` | Replace with router setup, delegate to `AppShell` layout |
| `frontend/src/main.tsx` | Wrap app in `BrowserRouter` |
| `frontend/package.json` | Add `react-router-dom` dependency |

---

## 7. Implementation Sequencing

Track Phase 1 should be delivered as 2-3 PRs, not one mega-branch.

### PR 1: Backend Operator API

**Scope**: New route file, service, doctor checks, permissions update, CLI extension.

Files:
- `engine/src/agent33/api/routes/operator.py`
- `engine/src/agent33/services/operator.py`
- `engine/src/agent33/services/doctor.py`
- `engine/src/agent33/cli/operator.py`
- `engine/src/agent33/security/permissions.py` (add scopes)
- `engine/src/agent33/main.py` (include router, store start_time)
- `engine/src/agent33/cli/main.py` (add operator subcommand)
- All `tests/test_api_operator_*.py` and `tests/test_cli_operator.py`

**Exit criteria**:
- All operator endpoints return correct response shapes
- Auth enforcement verified (401/403 tests pass)
- Doctor checks run against mocked subsystems
- Config redaction verified
- CLI operator commands work against a running server
- Ruff + mypy clean

### PR 2: Frontend Route Shell

**Scope**: React Router setup, layout components, page wrappers, navigation.

Files:
- `frontend/src/router.tsx`
- `frontend/src/layout/*.tsx`
- `frontend/src/pages/*.tsx`
- `frontend/src/pages/operator/*.tsx`
- `frontend/src/App.tsx` (rewrite)
- `frontend/src/main.tsx` (add BrowserRouter)
- `frontend/package.json` (add react-router-dom)
- All frontend test files

**Exit criteria**:
- Every operator page is reachable by URL
- Browser back/forward works
- Operator sidebar navigation highlights active route
- Existing chat, voice, and operations hub panels render correctly in their new locations
- Advanced Settings legacy panel accessible at `/operator/advanced`
- All frontend tests pass

### PR 3 (optional): Polish and Integration

**Scope**: Integration test, keyboard navigation, responsive behavior, empty states.

Files:
- `tests/test_operator_integration.py`
- `frontend/src/navigation.test.tsx`
- CSS updates for responsive sidebar

**Exit criteria**:
- Integration test verifies real inventory counts after lifespan startup
- Keyboard navigation (Tab, Enter, Escape) works across all nav elements
- Empty states show helpful messages with action links
- Mobile viewport renders correctly

---

## Appendix A: Backlog Item Coverage

This architecture covers the following items from the OpenClaw parity backlog:

| ID | Title | Coverage |
| --- | --- | --- |
| `OC-UI-001` | Route-based navigation | Full — core deliverable |
| `OC-UI-002` | Operator home page | Full — `/operator` home |
| `OC-UI-003` | Task-oriented navigation labels | Full — operator sidebar |
| `OC-UI-004` | "What can I do next" panel | Partial — operator home shows pending items |
| `OC-UI-005` | Workspace-aware landing | Deferred — needs tenant UX work |
| `OC-UI-006` | Dedicated pages | Full — tools, plugins, packs, backups, sessions, operations |
| `OC-UI-007` | Runtime availability badges | Partial — operator home shows health |
| `OC-UI-008` | Command palette | Deferred — Phase 9 or later |
| `OC-UI-009` | Notifications center | Deferred — needs notification service |
| `OC-UI-010` | Contextual docs links | Partial — doctor remediation includes guidance |
| `OC-FE-001` | Route-based refactor | Full — core deliverable |
| `OC-FE-002` | Dedicated pages | Full — all listed pages created |
| `OC-FE-003` | Responsive and mobile-safe | Full — responsive sidebar |
| `OC-FE-004` | Standardized states | Partial — empty/loading/error for operator pages |
| `OC-FE-005` | Keyboard navigation | Full — tested |
| `OC-FE-006` | Landmarks and labels | Partial — basic ARIA, full a11y in Phase 10 |

## Appendix B: Dependency on Later Phases

| This Phase Creates | Later Phase Fills |
| --- | --- |
| `/operator/tools` skeleton page | Phase 2: Runtime tool catalog API + full tools page |
| `/operator/backups` skeleton page | Phase 6: Backup create/verify API + full backups page |
| Session catalog endpoint (lightweight) | Phase 8: Full session management, subagent UX |
| Operator config viewer (read-only) | Phase 9: Config apply flows, schema-driven forms |
| Doctor check framework | Phase 9: Plugin doctor, update doctor, onboarding |
