# Phase 44 Architecture: Session Safety, Hook Operating Layer, and Continuity

**Date:** 2026-03-10
**Session:** 59
**Phase:** 44 (EVOKORE Convergence Wave 1)
**Status:** Architecture specification (pre-implementation)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Hook Operating Layer Design](#2-hook-operating-layer-design)
3. [Session Safety and Continuity](#3-session-safety-and-continuity)
4. [`.claude/settings.json` Wiring](#4-claudesettingsjson-wiring)
5. [API Endpoints](#5-api-endpoints)
6. [Test Strategy](#6-test-strategy)
7. [File Layout](#7-file-layout)
8. [Migration and Compatibility](#8-migration-and-compatibility)
9. [Risks and Open Questions](#9-risks-and-open-questions)

---

## 1. Executive Summary

Phase 44 turns AGENT-33's existing hook framework (Phase 32.1 H01) into a durable operator operating layer for CLI sessions. The existing hook system already provides:

- 8 event types across 4 tiers (agent, tool, workflow, request)
- Sequential and concurrent chain runners with abort propagation and per-hook timeouts
- HookMiddleware integrated into the Starlette middleware stack
- CRUD API at `/v1/hooks/` with tenant isolation
- Built-in MetricsHook and AuditLogHook

Phase 44 adds three capabilities the existing system lacks:

1. **Operator hook scripts** -- file-based hooks that live in `.claude/hooks/` or `scripts/hooks/` and execute as subprocesses, bridging Claude Code's local hook convention into AGENT-33's governed hook chain.
2. **Durable session state** -- a filesystem-backed + optional Redis/DB session layer that persists purpose, task state, replay logs, and cache entries across CLI invocations without breaking the existing encrypted in-memory `SessionManager`.
3. **Session replay and crash recovery** -- structured event logging that enables session reconstruction, incomplete-session detection, and resume offers.

### Downstream Dependencies

Phase 45 (Secure MCP Fabric) depends on durable session state for token scoping.
Phase 46 (Dynamic Tool Catalog) depends on session-scoped activation sets stored in the continuity layer.
Phase 48 (Status Line) depends on the continuity cache populated here.

---

## 2. Hook Operating Layer Design

### 2.1 Current State

The existing hook framework (`engine/src/agent33/hooks/`) provides:

| Component | File | Purpose |
|---|---|---|
| `HookEventType` | `models.py` | 8 event types: `agent.invoke.{pre,post}`, `tool.execute.{pre,post}`, `workflow.step.{pre,post}`, `request.{pre,post}` |
| `Hook` protocol | `protocol.py` | `name`, `event_type`, `priority`, `enabled`, `tenant_id`, `execute(ctx, call_next)` |
| `BaseHook` | `protocol.py` | Concrete base with `_name`, `_event_type`, `_priority`, `_enabled`, `_tenant_id` |
| `HookChainRunner` | `chain.py` | Sequential priority-ordered execution with middleware delegation, per-hook timeout via `asyncio.wait_for`, abort propagation, fail-open/fail-closed |
| `ConcurrentHookChainRunner` | `chain.py` | Parallel execution via `asyncio.gather` for independent post-processing |
| `HookRegistry` | `registry.py` | Registration, tenant-filtered retrieval, definition CRUD, builtin discovery, handler resolution via `importlib` |
| `HookMiddleware` | `middleware.py` | Starlette middleware firing `request.pre` and `request.post` hooks |
| Builtins | `builtins.py` | `MetricsHook` (priority 500) and `AuditLogHook` (priority 550), registered per event type |
| API | `api/routes/hooks.py` | Full CRUD + toggle + dry-run test at `/v1/hooks/` |

### 2.2 New Event Types for CLI Lifecycle

Phase 44 extends `HookEventType` with four new events that map to Claude Code's hook surfaces:

```python
class HookEventType(StrEnum):
    # ... existing 8 events ...

    # CLI session lifecycle (Phase 44)
    SESSION_START = "session.start"        # CLI session begins
    SESSION_END = "session.end"            # CLI session ends (normal or crash)
    SESSION_CHECKPOINT = "session.checkpoint"  # periodic state flush
    SESSION_RESUME = "session.resume"      # resuming an incomplete session
```

These events do not pass through the HTTP middleware. They are fired explicitly by the operator session service (Section 3) when a CLI session starts, checkpoints, ends, or resumes.

### 2.3 Operator Hook Scripts (File-Based Hooks)

EVOKORE and Claude Code use file-based hooks stored in `.claude/hooks/` that run as subprocesses. AGENT-33 needs to bridge this convention into its governed hook chain without losing tenant isolation or timeout enforcement.

#### 2.3.1 Discovery Paths

Hook scripts are discovered from two locations, in priority order:

1. **Project-level**: `<repo_root>/.claude/hooks/` -- checked in, shared by team
2. **User-level**: `~/.agent33/hooks/` -- personal, not version-controlled

Each hook script is a file (any executable: `.py`, `.sh`, `.ps1`, `.js`) whose filename encodes the event binding:

```
<event-type>--<hook-name>[.ext]
```

Examples:
- `session.start--purpose-gate.py`
- `tool.execute.pre--damage-control.sh`
- `session.end--session-replay.py`
- `session.checkpoint--tilldone.py`

#### 2.3.2 ScriptHook Adapter

A new `ScriptHook` class wraps file-based hooks into the existing `Hook` protocol:

```python
class ScriptHook(BaseHook):
    """Adapts a file-based hook script into the Hook protocol.

    Executes the script as a subprocess, passing context as JSON on stdin
    and reading modified context from stdout. Enforces per-hook timeout.
    Fail-open by default: if the script crashes, returns exit code != 0,
    or times out, the chain continues.
    """

    def __init__(
        self,
        *,
        name: str,
        event_type: str,
        script_path: Path,
        timeout_ms: float = 5000.0,
        fail_mode: Literal["open", "closed"] = "open",
        priority: int = 200,  # after builtins (100), before observability (500)
        tenant_id: str = "",
    ) -> None: ...

    async def execute(
        self,
        context: HookContext,
        call_next: Callable[[HookContext], Awaitable[HookContext]],
    ) -> HookContext:
        """Run script subprocess, enforce timeout, parse output."""
        ...
```

**Subprocess contract:**
- **stdin**: JSON-serialized `HookContext` (event_type, tenant_id, metadata, plus context-specific fields)
- **stdout**: JSON object with optional overrides: `{"abort": true, "abort_reason": "..."}` or `{"metadata": {...}}`
- **stderr**: captured for logging, not parsed
- **exit code 0**: success; **non-zero**: treated as failure, fail-open/closed per config
- **timeout**: enforced via `asyncio.wait_for` on `create_subprocess_exec`, matching existing chain timeout pattern
- **environment**: script receives `AGENT33_SESSION_ID`, `AGENT33_TENANT_ID`, `AGENT33_EVENT_TYPE` as env vars
- **Windows**: uses `subprocess.list2cmdline()` for proper quoting; merges `os.environ` to preserve PATH

#### 2.3.3 Script Discovery Service

```python
class ScriptHookDiscovery:
    """Discovers and registers file-based hooks from filesystem paths."""

    def __init__(
        self,
        hook_registry: HookRegistry,
        project_hooks_dir: Path | None = None,
        user_hooks_dir: Path | None = None,
        default_timeout_ms: float = 5000.0,
    ) -> None: ...

    def discover(self) -> int:
        """Scan directories, parse filenames, register ScriptHook instances.

        Returns the number of hooks discovered and registered.
        Project-level hooks take priority over user-level hooks with the
        same name (project overrides user).
        """
        ...

    def _parse_hook_filename(self, path: Path) -> tuple[str, str] | None:
        """Parse '<event-type>--<hook-name>[.ext]' -> (event_type, name).

        Returns None for unparseable filenames.
        """
        ...
```

#### 2.3.4 Fail-Safe Conventions

Per the EVOKORE brief and Phase 44 roadmap, operator hooks must be fail-safe:

1. **Exit 0 on unexpected errors**: `ScriptHook` catches all exceptions from the subprocess and, in fail-open mode (the default), logs a warning and continues the chain. This matches the existing `HookChainRunner` behavior.
2. **Quiet config loading**: scripts that read config files must not crash if the file is missing. The subprocess adapter does not enforce this -- it is a convention documented for hook script authors.
3. **Log rotation for replay/audit files**: handled by the session replay service (Section 3.3), not by individual hooks.
4. **Sanitized session IDs**: session IDs are UUID hex (32 chars, `[a-f0-9]+`). The session service validates this format before passing to hooks.

#### 2.3.5 Integration with Existing Middleware Chain

The middleware stack order remains unchanged:

```
CORS -> AuthMiddleware -> RequestSizeLimitMiddleware -> HookMiddleware -> Router
```

`HookMiddleware` already fires `request.pre` and `request.post` via the `HookRegistry`. The new `ScriptHook` instances register into the same registry and participate in the same chain. No middleware changes are needed for request-tier hooks.

For session-tier events (`session.start`, `session.end`, `session.checkpoint`, `session.resume`), the operator session service fires hooks directly via `HookRegistry.get_chain_runner()` -- these do not pass through HTTP middleware because they are not HTTP requests.

### 2.4 Seed Hook Scripts

Phase 44 delivers four concrete hook scripts under `scripts/hooks/`:

| Script | Event Binding | Purpose |
|---|---|---|
| `damage-control` | `session.end`, `tool.execute.post` | Detects potentially destructive outcomes (file deletions, failed commands, unexpected state changes) and logs a damage report. Fail-open. |
| `purpose-gate` | `session.start` | Prompts for or validates a session purpose string. If purpose is empty after the gate, logs a warning but does not abort (fail-open). Stores purpose in session state. |
| `session-replay` | `session.end` | Writes a replay log summary to `~/.agent33/sessions/<session_id>/replay.jsonl`. |
| `tilldone` | `session.checkpoint` | Checks task completion criteria from session state. If all tasks are marked done, sets a `session_complete` flag. Used by downstream completion gates. |

These scripts are also registered in `.claude/settings.json` (Section 4) so Claude Code discovers them.

---

## 3. Session Safety and Continuity

### 3.1 Current State

The existing `SessionManager` (`engine/src/agent33/memory/session.py`) provides:

- In-memory encrypted session store (Fernet)
- `SessionData` dataclass: `session_id`, `user_id`, `agent_name`, `data` dict, `created_at`, `updated_at`
- CRUD operations: `create`, `get`, `update`, `delete`, `exists`
- No persistence beyond process lifetime
- No session purpose, task state, or replay logging

This is the **runtime session** used for agent conversations. Phase 44 does not replace it. Instead, it adds a parallel **operator session** layer for CLI-level continuity.

### 3.2 Operator Session Model

```python
class OperatorSessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CRASHED = "crashed"      # process died without clean shutdown
    SUSPENDED = "suspended"  # user paused, intends to resume

@dataclass
class OperatorSession:
    session_id: str                    # UUID hex, sanitized
    purpose: str                       # human-readable session goal
    status: OperatorSessionStatus
    started_at: datetime
    updated_at: datetime
    ended_at: datetime | None

    # Task tracking
    tasks: list[TaskEntry]             # ordered task list with completion flags
    task_summary: str                  # auto-generated summary of progress

    # Context carry-forward
    context: dict[str, Any]            # arbitrary key-value pairs
    parent_session_id: str | None      # if resumed from a previous session

    # Cache for status surfaces (Phase 48 status line)
    cache: dict[str, Any]              # tool counts, skill counts, git metadata, etc.

    # Replay
    event_count: int                   # total events logged
    last_checkpoint_at: datetime | None

@dataclass
class TaskEntry:
    task_id: str
    description: str
    status: Literal["pending", "in_progress", "done", "blocked"]
    created_at: datetime
    completed_at: datetime | None
    metadata: dict[str, Any]
```

### 3.3 Storage Architecture

Operator session state uses a **tiered storage** model:

| Tier | Backend | Purpose | Latency | Durability |
|---|---|---|---|---|
| Hot | Filesystem (`~/.agent33/sessions/<session_id>/`) | Active session state, replay log, checkpoint files | <1ms | Durable across process restarts |
| Warm | Redis (optional) | Cross-machine session lookup, status cache for MCP/API queries | <5ms | Ephemeral with TTL (configurable, default 24h) |
| Cold | PostgreSQL (optional) | Long-term session history for auditing and analytics | ~10ms | Permanent with retention policy |

**Filesystem layout under `~/.agent33/sessions/<session_id>/`:**

```
session.json            # OperatorSession serialized
replay.jsonl            # Append-only event log (one JSON line per event)
checkpoint.json         # Latest checkpoint snapshot
tasks.json              # Task list with completion state
cache.json              # Status surface cache
```

**Why filesystem-first:**
- CLI sessions run locally; filesystem is always available
- No dependency on Redis/Postgres for basic operator continuity
- Redis and DB tiers are populated asynchronously for API/MCP access
- Matches the EVOKORE `~/.agent33/` convention

### 3.4 Operator Session Service

```python
class OperatorSessionService:
    """Manages operator session lifecycle, persistence, and replay logging.

    This service owns the durable session state. It is separate from the
    existing SessionManager (which handles encrypted runtime sessions for
    agent conversations).
    """

    def __init__(
        self,
        base_dir: Path,                    # ~/.agent33/sessions/
        hook_registry: HookRegistry | None,
        redis: Any | None = None,          # optional Redis for warm tier
        db: Any | None = None,             # optional DB for cold tier
        checkpoint_interval_seconds: float = 60.0,
        max_replay_file_bytes: int = 50 * 1024 * 1024,  # 50 MB rotation
        max_sessions_retained: int = 100,
    ) -> None: ...

    # -- Lifecycle --

    async def start_session(
        self, purpose: str = "", context: dict[str, Any] | None = None
    ) -> OperatorSession:
        """Create a new operator session.

        1. Generate sanitized session_id (UUID hex)
        2. Create filesystem directory structure
        3. Write initial session.json
        4. Fire session.start hooks
        5. Optionally write to Redis/DB warm/cold tiers
        """
        ...

    async def end_session(
        self, session_id: str, status: OperatorSessionStatus = OperatorSessionStatus.COMPLETED
    ) -> OperatorSession:
        """End an operator session.

        1. Update status and ended_at
        2. Fire session.end hooks
        3. Flush final checkpoint
        4. Update warm/cold tiers
        """
        ...

    async def resume_session(self, session_id: str) -> OperatorSession:
        """Resume a previously incomplete session.

        1. Load session from filesystem
        2. Validate status is CRASHED or SUSPENDED
        3. Set parent_session_id on new session or update status to ACTIVE
        4. Fire session.resume hooks
        """
        ...

    async def checkpoint(self, session_id: str) -> None:
        """Periodic state flush.

        1. Write checkpoint.json with current state
        2. Fire session.checkpoint hooks
        3. Update warm tier (Redis) if available
        """
        ...

    # -- Task tracking --

    async def add_task(self, session_id: str, description: str) -> TaskEntry: ...
    async def update_task(self, session_id: str, task_id: str, status: str) -> TaskEntry: ...
    async def list_tasks(self, session_id: str) -> list[TaskEntry]: ...

    # -- Replay --

    async def append_event(self, session_id: str, event: SessionEvent) -> None:
        """Append an event to the replay log (replay.jsonl)."""
        ...

    async def get_replay(
        self, session_id: str, offset: int = 0, limit: int = 100
    ) -> list[SessionEvent]:
        """Read events from replay log."""
        ...

    # -- Query --

    async def get_session(self, session_id: str) -> OperatorSession | None: ...
    async def list_sessions(
        self, status: OperatorSessionStatus | None = None, limit: int = 50
    ) -> list[OperatorSession]: ...

    # -- Crash detection --

    async def detect_incomplete_sessions(self) -> list[OperatorSession]:
        """Scan filesystem for sessions with status=ACTIVE that have stale checkpoints.

        A session is considered crashed if:
        - status is ACTIVE
        - last_checkpoint_at is older than 2x checkpoint_interval_seconds
        - No process lock file is held

        Returns sessions eligible for resume.
        """
        ...

    # -- Maintenance --

    async def rotate_replay_log(self, session_id: str) -> None:
        """Rotate replay.jsonl when it exceeds max_replay_file_bytes."""
        ...

    async def cleanup_old_sessions(self) -> int:
        """Remove sessions beyond max_sessions_retained (oldest first)."""
        ...
```

### 3.5 Session Event Model (Replay Log)

```python
class SessionEventType(StrEnum):
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"
    SESSION_RESUMED = "session.resumed"
    TASK_ADDED = "task.added"
    TASK_UPDATED = "task.updated"
    AGENT_INVOKED = "agent.invoked"
    TOOL_EXECUTED = "tool.executed"
    HOOK_FIRED = "hook.fired"
    CHECKPOINT = "checkpoint"
    ERROR = "error"
    USER_INPUT = "user.input"

@dataclass
class SessionEvent:
    event_id: str                  # UUID hex
    event_type: SessionEventType
    timestamp: datetime
    session_id: str
    data: dict[str, Any]           # event-specific payload
    correlation_id: str = ""       # links related events
```

Each event is written as a single JSON line to `replay.jsonl`. The file is append-only during a session. Rotation happens when the file exceeds the configured size limit (default 50 MB).

### 3.6 Crash Recovery Flow

```
1. CLI starts
2. OperatorSessionService.detect_incomplete_sessions()
3. If incomplete sessions found:
   a. Log: "Found N incomplete sessions from previous runs"
   b. For each:
      - Mark status as CRASHED
      - Display: session_id, purpose, last_checkpoint_at, task_summary
   c. Offer resume: "Resume session <id>? [y/N]"
      - If yes: resume_session(id) -> fires session.resume hooks
      - If no: leave as CRASHED for audit trail
4. Proceed to start_session() for the new session
```

### 3.7 Cross-Invocation Context Carry-Forward

When a session is resumed, its `context` dict carries forward into the new session. This includes:

- **Purpose**: the original session goal
- **Task state**: which tasks were pending/done
- **Agent memory references**: IDs of agent conversations that were active
- **Tool activation state**: which tools were activated (consumed by Phase 46)
- **Cache entries**: last-known tool/skill/git counts for status surfaces (Phase 48)

The context dict is extensible -- any subsystem can read/write keys. Phase 44 reserves the following key prefixes:

| Prefix | Owner | Purpose |
|---|---|---|
| `purpose.*` | Session service | Session goal and sub-goals |
| `tasks.*` | Session service | Task completion state |
| `hooks.*` | Hook operating layer | Hook execution summaries |
| `cache.*` | Status cache | Counts, metadata for status line |
| `agent.*` | Agent runtime | Active agent conversation refs |
| `tool.*` | Tool registry (Phase 46) | Activation sets |

### 3.8 Process Locking

To distinguish "active session on this machine" from "crashed session", the service writes a PID-based lock file:

```
~/.agent33/sessions/<session_id>/process.lock
```

Contents: `{"pid": 12345, "started_at": "2026-03-10T...", "hostname": "..."}`.

On startup, `detect_incomplete_sessions()` checks whether the PID in the lock file is still running (via `os.kill(pid, 0)` on Unix, `psutil` or `ctypes.windll.kernel32.OpenProcess` on Windows). If the process is dead, the session is considered crashed.

---

## 4. `.claude/settings.json` Wiring

### 4.1 Settings Schema

AGENT-33 produces a `.claude/settings.json` at the repo root that Claude Code reads to discover hooks and project settings:

```json
{
  "$schema": "https://agent33.dev/schemas/claude-settings-v1.json",
  "version": 1,
  "hooks": {
    "session.start": [
      {
        "name": "purpose-gate",
        "command": "python scripts/hooks/session.start--purpose-gate.py",
        "timeout_ms": 5000,
        "fail_mode": "open"
      }
    ],
    "session.end": [
      {
        "name": "damage-control",
        "command": "python scripts/hooks/session.end--damage-control.py",
        "timeout_ms": 5000,
        "fail_mode": "open"
      },
      {
        "name": "session-replay",
        "command": "python scripts/hooks/session.end--session-replay.py",
        "timeout_ms": 10000,
        "fail_mode": "open"
      }
    ],
    "session.checkpoint": [
      {
        "name": "tilldone",
        "command": "python scripts/hooks/session.checkpoint--tilldone.py",
        "timeout_ms": 3000,
        "fail_mode": "open"
      }
    ],
    "tool.execute.post": [
      {
        "name": "damage-control",
        "command": "python scripts/hooks/tool.execute.post--damage-control.py",
        "timeout_ms": 5000,
        "fail_mode": "open"
      }
    ]
  },
  "session": {
    "auto_purpose_prompt": true,
    "checkpoint_interval_seconds": 60,
    "crash_recovery_enabled": true,
    "replay_enabled": true,
    "max_replay_file_mb": 50,
    "max_sessions_retained": 100
  },
  "safety": {
    "hooks_fail_open_default": true,
    "hooks_max_script_timeout_ms": 30000,
    "hooks_max_per_event": 20,
    "session_id_format": "uuid_hex"
  }
}
```

### 4.2 Auto-Discovery

Settings are loaded from two levels:

1. **Project-level**: `<repo_root>/.claude/settings.json` -- shared team settings
2. **User-level**: `~/.agent33/settings.json` -- personal overrides

Merge strategy: user-level settings override project-level settings at the top-level key level. Hook lists are merged (user hooks appended after project hooks). Safety thresholds use the more restrictive value (lower timeout, lower max-per-event).

### 4.3 Settings Loader

```python
class ClaudeSettingsLoader:
    """Load and merge .claude/settings.json from project and user levels."""

    def __init__(
        self,
        project_dir: Path | None = None,
        user_dir: Path | None = None,
    ) -> None: ...

    def load(self) -> ClaudeSettings:
        """Load, validate, and merge settings from both levels."""
        ...

    def validate(self, raw: dict[str, Any]) -> ClaudeSettings:
        """Validate settings against the schema. Returns validated model."""
        ...

    def migrate(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Migrate settings from older schema versions to current."""
        ...
```

### 4.4 Engine Config Additions

New settings in `engine/src/agent33/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Phase 44: Operator session
    operator_session_enabled: bool = True
    operator_session_base_dir: str = ""  # default: ~/.agent33/sessions/
    operator_session_checkpoint_interval_seconds: float = 60.0
    operator_session_max_replay_file_mb: int = 50
    operator_session_max_retained: int = 100
    operator_session_crash_recovery_enabled: bool = True
    operator_session_redis_ttl_hours: int = 24

    # Phase 44: Script hooks
    script_hooks_enabled: bool = True
    script_hooks_project_dir: str = ""    # default: <cwd>/.claude/hooks/
    script_hooks_user_dir: str = ""       # default: ~/.agent33/hooks/
    script_hooks_default_timeout_ms: float = 5000.0
    script_hooks_max_timeout_ms: float = 30000.0
```

---

## 5. API Endpoints

### 5.1 Session CRUD (`/v1/sessions/`)

| Method | Path | Description | Auth Scope |
|---|---|---|---|
| `POST` | `/v1/sessions/` | Create a new operator session | `sessions:write` |
| `GET` | `/v1/sessions/` | List sessions (filterable by status) | `sessions:read` |
| `GET` | `/v1/sessions/{session_id}` | Get session details | `sessions:read` |
| `POST` | `/v1/sessions/{session_id}/resume` | Resume an incomplete session | `sessions:write` |
| `POST` | `/v1/sessions/{session_id}/end` | End a session | `sessions:write` |
| `POST` | `/v1/sessions/{session_id}/checkpoint` | Force a checkpoint | `sessions:write` |
| `GET` | `/v1/sessions/incomplete` | List sessions eligible for resume | `sessions:read` |

#### Request/Response Models

```python
class SessionCreateRequest(BaseModel):
    purpose: str = ""
    context: dict[str, Any] = Field(default_factory=dict)

class SessionEndRequest(BaseModel):
    status: Literal["completed", "suspended"] = "completed"

class SessionResponse(BaseModel):
    session_id: str
    purpose: str
    status: str
    started_at: datetime
    updated_at: datetime
    ended_at: datetime | None
    task_count: int
    tasks_completed: int
    event_count: int
    parent_session_id: str | None
```

### 5.2 Session Tasks (`/v1/sessions/{session_id}/tasks/`)

| Method | Path | Description | Auth Scope |
|---|---|---|---|
| `POST` | `/v1/sessions/{session_id}/tasks/` | Add a task | `sessions:write` |
| `GET` | `/v1/sessions/{session_id}/tasks/` | List tasks | `sessions:read` |
| `PUT` | `/v1/sessions/{session_id}/tasks/{task_id}` | Update task status | `sessions:write` |

### 5.3 Session Replay (`/v1/sessions/{session_id}/replay/`)

| Method | Path | Description | Auth Scope |
|---|---|---|---|
| `GET` | `/v1/sessions/{session_id}/replay/` | Get replay events (paginated) | `sessions:read` |
| `GET` | `/v1/sessions/{session_id}/replay/stream` | SSE stream of replay events | `sessions:read` |
| `GET` | `/v1/sessions/{session_id}/replay/summary` | Get replay summary (event counts by type, duration, key moments) | `sessions:read` |

The SSE stream endpoint reuses the existing SSE infrastructure from `api/routes/workflow_sse.py`.

### 5.4 Hook Management Extensions

The existing `/v1/hooks/` endpoints already cover CRUD, toggle, and test. Phase 44 adds:

| Method | Path | Description | Auth Scope |
|---|---|---|---|
| `GET` | `/v1/hooks/scripts` | List discovered script hooks | `hooks:read` |
| `POST` | `/v1/hooks/scripts/rediscover` | Re-scan filesystem for script hooks | `hooks:manage` |
| `GET` | `/v1/hooks/scripts/{name}/logs` | Get recent execution logs for a script hook | `hooks:read` |

---

## 6. Test Strategy

### 6.1 Hook Operating Layer Tests

#### Unit Tests (~80 tests estimated)

| Category | Tests | Focus |
|---|---|---|
| `ScriptHook` execution | 15 | Subprocess launch, stdin/stdout contract, timeout enforcement, exit code handling, fail-open/closed behavior, Windows path quoting |
| `ScriptHookDiscovery` | 12 | Filename parsing (valid and invalid patterns), directory scanning, project-overrides-user priority, permission checks |
| Hook event type extensions | 8 | New `SESSION_*` events register correctly, coexist with existing events, tenant filtering works |
| `ScriptHook` edge cases | 10 | Script not found, script not executable, empty stdout, malformed JSON stdout, stderr-only output, very large stdout |
| Integration with `HookChainRunner` | 10 | ScriptHook participates in chains alongside Python hooks, abort propagation works across script/Python boundary, priority ordering |
| Integration with `HookRegistry` | 8 | Script hooks register/deregister, coexist with builtin hooks, definition CRUD works |
| `ClaudeSettingsLoader` | 10 | Project-only, user-only, merged, missing files, invalid JSON, version migration, safety threshold clamping |
| Hook API extensions | 7 | `/v1/hooks/scripts` list, rediscover, logs endpoints |

#### Key Test Scenarios

1. **Script timeout enforcement**: Register a script hook that sleeps for 10 seconds. Verify the chain runner cancels it after the configured timeout and continues (fail-open) or aborts (fail-closed).

2. **Script crash fail-open**: Register a script hook that exits with code 1. Verify the chain continues and the failure is logged in `HookResult`.

3. **Abort propagation across boundary**: A Python hook runs before a ScriptHook. The Python hook sets `abort=True`. Verify the ScriptHook is never invoked.

4. **Windows subprocess**: On Windows, verify `create_subprocess_exec` uses proper quoting and environment merging. Detect missing commands via stderr pattern.

5. **Concurrent discovery**: Two discovery runs overlap. Verify no duplicate registrations.

### 6.2 Session Continuity Tests

#### Unit Tests (~70 tests estimated)

| Category | Tests | Focus |
|---|---|---|
| `OperatorSessionService` lifecycle | 15 | Create, checkpoint, end, resume. Verify filesystem artifacts at each stage. |
| Session persistence | 10 | Write session.json, reload from filesystem, verify round-trip fidelity. Edge cases: corrupt JSON, missing fields, extra fields (forward compat). |
| Crash detection | 12 | Active session with dead PID -> detected as crashed. Active session with live PID -> not crashed. No lock file -> crashed. Lock file with stale hostname -> crashed. |
| Replay logging | 10 | Append events, read back with pagination, rotation at size limit, empty log, concurrent appends. |
| Task tracking | 8 | Add tasks, update status, completion percentage, all-done detection for tilldone. |
| Context carry-forward | 8 | Resume session preserves context. Reserved key prefixes respected. Nested context merge. |
| Cleanup and retention | 7 | Old sessions removed when limit exceeded. Oldest-first ordering. Filesystem artifacts fully removed. |

#### Key Test Scenarios

1. **Crash and resume**: Start a session, write a checkpoint, simulate crash (kill without end_session). On next startup, detect the incomplete session. Resume it. Verify purpose, tasks, and context carry forward. Verify `session.resume` hooks fire.

2. **Replay accuracy**: Start a session, perform 50 operations (agent invocations, tool executions). End the session. Read replay log. Verify all 50 events are present with correct ordering and timestamps.

3. **Replay rotation**: Generate a replay log that exceeds the size limit. Verify rotation creates an archived file and a fresh current file. Verify reading spans both files.

4. **Redis warm tier**: Start a session with Redis available. Verify session appears in Redis with correct TTL. Kill Redis. Verify session service degrades gracefully to filesystem-only.

5. **Concurrent sessions**: Start two sessions (different session_ids). Verify they do not interfere. End one. Verify the other continues.

### 6.3 Integration Tests (~30 tests estimated)

| Category | Tests | Focus |
|---|---|---|
| End-to-end session lifecycle | 8 | API call to create session -> invoke agent -> execute tool -> checkpoint -> end session. Verify replay log contains all events. Verify hooks fired at each stage. |
| Existing subsystem non-regression | 10 | Existing `SessionManager` (encrypted runtime sessions) works unchanged. Existing hook builtins (MetricsHook, AuditLogHook) continue to function. Existing middleware chain order preserved. |
| Lifespan integration | 5 | `OperatorSessionService` initializes in lifespan after hook registry. Shuts down cleanly. Crash detection runs on startup. |
| Multi-tenant isolation | 7 | Operator sessions respect tenant_id. Script hooks from one tenant cannot read another tenant's session state. |

### 6.4 Total Estimated Tests

| Category | Count |
|---|---|
| Hook operating layer unit tests | ~80 |
| Session continuity unit tests | ~70 |
| Integration tests | ~30 |
| **Total** | **~180** |

---

## 7. File Layout

### 7.1 New Files

| File | Purpose | Est. LOC |
|---|---|---|
| `engine/src/agent33/hooks/script_hook.py` | `ScriptHook` adapter and subprocess execution | ~250 |
| `engine/src/agent33/hooks/script_discovery.py` | `ScriptHookDiscovery` filesystem scanner | ~180 |
| `engine/src/agent33/sessions/__init__.py` | Package init for operator sessions | ~30 |
| `engine/src/agent33/sessions/models.py` | `OperatorSession`, `TaskEntry`, `SessionEvent`, `OperatorSessionStatus`, `SessionEventType` | ~120 |
| `engine/src/agent33/sessions/service.py` | `OperatorSessionService` (lifecycle, persistence, replay, crash detection) | ~550 |
| `engine/src/agent33/sessions/storage.py` | Filesystem, Redis, and DB storage backends | ~350 |
| `engine/src/agent33/sessions/settings_loader.py` | `ClaudeSettingsLoader` for `.claude/settings.json` | ~200 |
| `engine/src/agent33/api/routes/sessions.py` | Session CRUD + replay + task API endpoints | ~350 |
| `scripts/hooks/session.start--purpose-gate.py` | Purpose gate hook script | ~80 |
| `scripts/hooks/session.end--damage-control.py` | Damage control hook script | ~120 |
| `scripts/hooks/session.end--session-replay.py` | Session replay hook script | ~90 |
| `scripts/hooks/session.checkpoint--tilldone.py` | Tilldone completion gate hook script | ~70 |
| `engine/tests/test_script_hook.py` | ScriptHook unit tests | ~400 |
| `engine/tests/test_script_discovery.py` | ScriptHookDiscovery tests | ~250 |
| `engine/tests/test_operator_session_service.py` | OperatorSessionService tests | ~500 |
| `engine/tests/test_session_storage.py` | Storage backend tests | ~300 |
| `engine/tests/test_settings_loader.py` | ClaudeSettingsLoader tests | ~200 |
| `engine/tests/test_session_api.py` | Session API endpoint tests | ~350 |
| `engine/tests/test_session_integration.py` | Cross-subsystem integration tests | ~300 |

**Subtotals:**

| Category | LOC |
|---|---|
| Production code (new files) | ~2,390 |
| Test code (new files) | ~2,300 |
| Hook scripts | ~360 |
| **Total new LOC** | **~5,050** |

### 7.2 Existing Files to Modify

| File | Change | Est. Delta |
|---|---|---|
| `engine/src/agent33/hooks/models.py` | Add 4 new `HookEventType` values (`SESSION_*`), add `SessionHookContext` dataclass | +30 LOC |
| `engine/src/agent33/hooks/__init__.py` | Export new models and ScriptHook | +10 LOC |
| `engine/src/agent33/hooks/builtins.py` | Add session event types to `_PHASE1_EVENT_TYPES` for builtin hook registration | +5 LOC |
| `engine/src/agent33/config.py` | Add operator session and script hook settings (Section 4.4) | +20 LOC |
| `engine/src/agent33/main.py` | Initialize `OperatorSessionService` and `ScriptHookDiscovery` in lifespan, register session routes | +60 LOC |
| `engine/src/agent33/api/routes/__init__.py` | Import sessions route module | +2 LOC |
| `engine/src/agent33/agents/runtime.py` | Emit `SessionEvent` for agent invocations (if operator session active) | +15 LOC |
| `.claude/settings.json` | New file with hook and session configuration | ~50 LOC |
| `CLAUDE.md` | Document continuity, replay, and memory operating rules | +30 LOC |

**Total modification delta: ~220 LOC**

### 7.3 Initialization Order Update

The lifespan in `main.py` adds two new initialization steps after the hook registry:

```
... existing initialization ...
Hook Registry                   # existing
  -> Script Hook Discovery      # NEW (Phase 44) - discovers file-based hooks
  -> Operator Session Service   # NEW (Phase 44) - crash detection, session lifecycle
... rest of existing initialization ...
```

Shutdown adds:

```
... existing shutdown ...
Operator Session Service shutdown  # NEW - flush final checkpoint, mark sessions
... rest of existing shutdown ...
```

---

## 8. Migration and Compatibility

### 8.1 Backward Compatibility

| Concern | Mitigation |
|---|---|
| Existing `SessionManager` | Unchanged. The new `OperatorSessionService` is a separate module in `engine/src/agent33/sessions/`, not a modification of `engine/src/agent33/memory/session.py`. Both can coexist. |
| Existing hook registry | ScriptHooks register into the same `HookRegistry` via the same `register()` method. No registry API changes. |
| Existing hook middleware | `HookMiddleware` continues to fire `request.pre/post` hooks unchanged. New session events bypass HTTP middleware entirely. |
| Existing hook API | `/v1/hooks/` CRUD endpoints work unchanged. New `/v1/hooks/scripts` endpoints are additive. |
| Existing tests | No existing test should break. New session event types are additive to the `HookEventType` enum. |

### 8.2 Feature Flags

All Phase 44 features are gated behind settings:

- `operator_session_enabled` (default `True`) -- disable to skip session service initialization
- `script_hooks_enabled` (default `True`) -- disable to skip filesystem hook discovery
- `operator_session_crash_recovery_enabled` (default `True`) -- disable crash detection on startup

### 8.3 Settings Version Migration

`.claude/settings.json` includes a `version` field. The `ClaudeSettingsLoader.migrate()` method handles version upgrades:

- **v0 -> v1**: No existing v0 exists, so initial creation is always v1
- Future versions: add migration functions keyed by version number

---

## 9. Risks and Open Questions

### 9.1 Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Script hook subprocess overhead on hot paths | Medium | Script hooks default to priority 200 (after critical hooks). Timeout enforcement prevents runaway processes. Monitor latency in MetricsHook. Consider caching subprocess results for idempotent hooks. |
| Filesystem lock reliability on Windows | Medium | PID-based lock detection is less reliable on Windows (PID reuse). Use a combination of PID + start time. Fall back to file mtime heuristic if `OpenProcess` fails. |
| Replay log disk usage | Low | Configurable size limit with rotation. Default 50 MB per session, 100 sessions retained = 5 GB worst case. Cleanup runs on startup. |
| Cross-platform path handling | Medium | Use `pathlib.Path` throughout. Test on Windows explicitly. Sanitize session IDs to prevent path traversal (UUID hex only). |
| Redis unavailability | Low | Warm tier is optional. Service degrades to filesystem-only with a warning log. No functional loss. |

### 9.2 Open Questions

1. **Should the replay SSE endpoint support real-time streaming of the active session's events?** Currently specced as read-back only. Real-time streaming would require a pub/sub mechanism (NATS or Redis pubsub). Recommendation: defer to Phase 48 (status line) which already needs a live event feed.

2. **Should script hooks support Windows `.cmd` and `.bat` files?** The current spec supports `.py`, `.sh`, `.ps1`, `.js`. Adding `.cmd`/`.bat` is trivial but increases the attack surface for path injection. Recommendation: support `.cmd`/`.bat` with explicit opt-in via settings.

3. **Should the operator session service integrate with the existing `ObservationCapture` NATS bus?** The existing memory subsystem has `ObservationCapture` wired to NATS. Session events could be published to NATS for other consumers. Recommendation: yes, publish session events to a `session.events` NATS subject. Consumers are optional.

4. **How should multi-machine sessions work?** If a developer starts a session on machine A and wants to resume on machine B, the filesystem tier is insufficient. The Redis/DB tiers would need to be the primary store. Recommendation: document this as a Phase 45+ concern (cross-CLI sync). For Phase 44, sessions are single-machine.

---

## Appendix A: Recommended PR Slicing

| PR | Scope | Estimated LOC |
|---|---|---|
| PR 1 | Models + storage backends (`sessions/models.py`, `sessions/storage.py`) + tests | ~1,100 |
| PR 2 | `OperatorSessionService` + crash detection + tests | ~1,200 |
| PR 3 | `ScriptHook` + `ScriptHookDiscovery` + hook model extensions + tests | ~1,100 |
| PR 4 | Session API endpoints + replay + tests | ~900 |
| PR 5 | `.claude/settings.json` wiring + `ClaudeSettingsLoader` + seed hook scripts + integration tests + docs | ~750 |

## Appendix B: Configuration Reference

| Setting | Type | Default | Description |
|---|---|---|---|
| `operator_session_enabled` | `bool` | `True` | Enable the operator session service |
| `operator_session_base_dir` | `str` | `""` (resolves to `~/.agent33/sessions/`) | Base directory for session state |
| `operator_session_checkpoint_interval_seconds` | `float` | `60.0` | Seconds between automatic checkpoints |
| `operator_session_max_replay_file_mb` | `int` | `50` | Max replay file size before rotation |
| `operator_session_max_retained` | `int` | `100` | Max sessions to keep on disk |
| `operator_session_crash_recovery_enabled` | `bool` | `True` | Enable crash detection on startup |
| `operator_session_redis_ttl_hours` | `int` | `24` | TTL for session data in Redis warm tier |
| `script_hooks_enabled` | `bool` | `True` | Enable filesystem-based hook discovery |
| `script_hooks_project_dir` | `str` | `""` (resolves to `<cwd>/.claude/hooks/`) | Project-level hook scripts directory |
| `script_hooks_user_dir` | `str` | `""` (resolves to `~/.agent33/hooks/`) | User-level hook scripts directory |
| `script_hooks_default_timeout_ms` | `float` | `5000.0` | Default timeout for script hooks |
| `script_hooks_max_timeout_ms` | `float` | `30000.0` | Maximum allowed timeout for script hooks |
