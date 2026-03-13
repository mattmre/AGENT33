# Session 59 Wave 5 Refinements Architecture

**Date:** 2026-03-10
**Scope:** Phase 25 SSE fallback hardening, Phase 38 Stage 3 Docker container kernels, frontend component test expansion
**Status:** Research / architecture document (no code changes)

---

## 1. Phase 25 SSE Fallback — Hardening and Reconnection

### 1.1 Current State

The SSE fallback is **already implemented** and functional:

- **Backend:** `engine/src/agent33/api/routes/workflow_sse.py` exposes `GET /v1/workflows/{run_id}/events` with `text/event-stream` responses, authenticated via `require_scope("workflows:read")`. The endpoint delegates to `WorkflowWSManager.subscribe_sse_if_allowed()` for authorization and queue registration, emits an initial `sync` event, then streams live events with periodic heartbeats.
- **Frontend:** `frontend/src/lib/workflowLiveTransport.ts` uses `fetch()` with `ReadableStream` parsing (not native `EventSource`) to consume the SSE endpoint. It attaches `Authorization: Bearer <token>` or `X-API-Key` headers.
- **Manager:** `engine/src/agent33/workflows/ws_manager.py` (`WorkflowWSManager`) maintains both WebSocket and SSE subscription sets, with backpressure handling on SSE queues (drop-oldest policy).
- **Tests:** `engine/tests/test_workflow_sse.py` covers auth, scope, tenant isolation, sync events, live event streaming, cleanup on disconnect, and heartbeat generation. Frontend tests in `frontend/src/lib/workflowLiveTransport.test.ts` cover SSE-with-JWT and SSE-with-API-key paths.

### 1.2 Gap Analysis

The following refinements remain:

| Gap | Severity | Description |
|-----|----------|-------------|
| G1: No client-side reconnection | Medium | If the SSE stream drops (network blip, proxy timeout), the client silently stops receiving events. There is no retry loop or exponential backoff. |
| G2: No `Last-Event-ID` support | Low | The SSE endpoint does not emit `id:` fields. On reconnect, the client cannot request missed events. |
| G3: No WS-to-SSE automatic fallback | Low | The `connectWorkflowLiveTransport` function currently always uses SSE. The prior design document (session57) intended a "try WS first, fall back to SSE" pattern, but the implementation went directly to SSE-only. This is fine for API-key clients but leaves JWT browser sessions without the lower-latency WebSocket path. |
| G4: No terminal event auto-close | Low | The SSE generator does not explicitly break on terminal events (`workflow_completed`/`workflow_failed`). The stream continues until the client disconnects. The frontend handles this by calling `close()` on the transport, but a server-side close would reduce resource consumption. |

### 1.3 Reconnection Design

#### 1.3.1 Server-side: Event IDs

Add an `id:` field to each SSE frame using a monotonically increasing sequence number per `run_id`. The format becomes:

```
id: 7
data: {"type":"step_completed","run_id":"abc",...}

```

The `_format_sse` function in `workflow_sse.py` changes to accept a sequence counter:

```python
def _format_sse(event: WorkflowEvent, seq: int) -> str:
    return f"id: {seq}\ndata: {event.to_json()}\n\n"
```

On `subscribe_sse_if_allowed`, the manager should accept an optional `last_event_id: int | None` parameter. When provided, the manager replays any events from the run snapshot that occurred after that sequence (or re-sends the full `sync` event if the sequence is too old). This requires the manager to maintain a bounded event ring buffer per run (recommended: 200 events max, matching the SSE queue maxsize).

#### 1.3.2 Client-side: Retry with Backoff

Wrap the `streamWorkflowEventsOverSse` function in a retry loop:

```typescript
async function streamWithReconnect(
  baseUrl: string,
  options: WorkflowLiveTransportOptions,
  signal: AbortSignal
): Promise<void> {
  let lastEventId: string | undefined;
  let attempt = 0;
  const maxAttempts = 10;
  const baseDelayMs = 1000;
  const maxDelayMs = 30000;

  while (!signal.aborted && attempt < maxAttempts) {
    try {
      await streamWorkflowEventsOverSse(baseUrl, options, signal, lastEventId);
      break; // Clean close (terminal event or server closed)
    } catch (error) {
      if (signal.aborted) break;
      attempt++;
      const delay = Math.min(baseDelayMs * 2 ** (attempt - 1), maxDelayMs);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

The `Last-Event-Id` header is passed on reconnect requests per the SSE specification. On each received event, the client updates `lastEventId` from the `id:` field.

#### 1.3.3 State Sync on Reconnect

On reconnect, the server always sends a fresh `sync` event first (this is already the behavior). The client should:

1. Accept the `sync` event and trigger a full graph refetch (already happens via `shouldRefreshWorkflowGraph`).
2. Resume processing subsequent events normally.
3. Reset the retry attempt counter on successful reconnection.

This approach avoids complex client-side event deduplication. The `sync` event replaces any stale local state.

#### 1.3.4 Optional WS-to-SSE Fallback

For JWT browser sessions that want lower latency, the transport can attempt a WebSocket connection first:

```typescript
export function connectWorkflowLiveTransport(options): WorkflowLiveTransportConnection {
  const { API_BASE_URL } = getRuntimeConfig();
  const abortController = new AbortController();

  if (options.token && !options.apiKey) {
    // Try WS first for JWT sessions
    tryWebSocketFirst(API_BASE_URL, options, abortController);
  } else {
    // SSE directly for API-key-only clients
    void streamWithReconnect(API_BASE_URL, options, abortController.signal);
  }

  return { close: () => abortController.abort() };
}
```

The `tryWebSocketFirst` function opens a WebSocket to `/v1/workflows/{run_id}/ws`, and if the connection fails within 3 seconds or receives a close code >= 4000, falls back to the SSE path. The `buildWorkflowWebSocketUrl` helper already exists in the transport module.

**Recommendation:** Defer WS-to-SSE fallback to a future PR. The current SSE-only approach works for all auth methods and the reconnection hardening provides the most immediate value.

### 1.4 Files to Change

| File | Change |
|------|--------|
| `engine/src/agent33/api/routes/workflow_sse.py` | Add sequence counter to `_format_sse`, accept `Last-Event-Id` header |
| `engine/src/agent33/workflows/ws_manager.py` | Add bounded event ring buffer per run, `replay_from_seq` method |
| `frontend/src/lib/workflowLiveTransport.ts` | Add retry loop with backoff, `Last-Event-Id` header on reconnect |
| `engine/tests/test_workflow_sse.py` | Test reconnection with `Last-Event-Id`, test event ID emission |
| `frontend/src/lib/workflowLiveTransport.test.ts` | Test retry on fetch failure, test `Last-Event-Id` header sent |

---

## 2. Phase 38 Stage 3: Docker Container Kernels

### 2.1 Current State

The Docker kernel infrastructure is **already implemented** in `engine/src/agent33/execution/adapters/jupyter.py`:

- **`DockerKernelSession`** (lines 270-426): Manages a full Docker container lifecycle — creates temp runtime directories, writes connection files, builds `docker run` commands with port mapping, volume mounts, and network policies, starts ipykernel inside the container, connects via `jupyter_client.AsyncKernelClient`, and cleans up with `docker rm -f` on stop.
- **`KernelContainerPolicy`** (in `models.py`, lines 152-162): Pydantic model for container runtime controls — image, allowed images whitelist, network toggle, working directory mount, container workdir, extra run args.
- **`KernelInterface`** (lines 164-172): Session limits (max sessions, idle timeout, startup timeout, execution timeout) with nested `container` policy.
- **`KernelSessionManager`** (lines 428-501): Manages session lifecycle with `get_or_create`/`remove`/`shutdown_all`, idle reaping, and max session enforcement.
- **`JupyterAdapter`** (lines 503-616): `BaseAdapter` implementation that routes to either `KernelSession` (local) or `DockerKernelSession` (container) based on `kernel.container.enabled`.
- **`build_default_jupyter_definition`** helper for runtime registration with all Docker options.

### 2.2 Gap Analysis

| Gap | Severity | Description |
|-----|----------|-------------|
| G1: No tests for DockerKernelSession | High | `engine/tests/test_execution_jupyter_adapter.py` exists with `_FakeSession` mocks for the adapter and session manager, but there are no tests that exercise `DockerKernelSession` directly (Docker command building, connection file creation, startup failure paths, cleanup). |
| G2: No CPU/memory resource limits | Medium | The `_build_docker_command` method does not apply `--memory` or `--cpus` flags from `SandboxConfig`. The contract's `sandbox.memory_mb` and `sandbox.cpu_cores` are ignored at the container level. |
| G3: No container health check | Medium | After `docker run -d`, the code immediately tries to connect. There is no health probe to verify the container is running before attempting the Jupyter client connection. A failed container startup (e.g., image pull failure) relies solely on the `startup_timeout`. |
| G4: No image pull policy | Low | If the specified image is not locally available, `docker run` will implicitly pull it, which can exceed the startup timeout. There is no explicit pull-before-run or pull policy configuration. |
| G5: No container label/metadata | Low | Containers are named `agent33-kernel-<session_id>` but have no Docker labels for filtering/cleanup by external tools. |
| G6: No tmpfs for `/tmp` | Low | Container `/tmp` uses the overlay filesystem. A `tmpfs` mount would improve security and prevent disk exhaustion from runaway output. |
| G7: No read-only root filesystem | Low | The container root is writable. Setting `--read-only` with explicit writable mounts (`/workspace`, `/agent33-runtime`, `/tmp`) would reduce attack surface. |
| G8: No user namespace remapping | Low | The kernel runs as the container's default user (often root in Jupyter images). No `--user` flag is applied. |

### 2.3 Refinement Design

#### 2.3.1 Resource Limits from SandboxConfig

The `_build_docker_command` method should merge contract sandbox limits:

```python
def _build_docker_command(self, runtime_dir, connection_info, sandbox=None):
    command = ["docker", "run", "-d", "--rm", "--name", self._container_name]

    # Resource limits
    if sandbox:
        command.extend(["--memory", f"{sandbox.memory_mb}m"])
        command.extend(["--cpus", str(sandbox.cpu_cores)])
    else:
        command.extend(["--memory", "512m", "--cpus", "1"])

    # Security hardening
    command.extend([
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=100m",
        "--security-opt", "no-new-privileges",
        "--pids-limit", "100",
    ])

    # Labels for external management
    command.extend([
        "--label", "agent33.component=kernel",
        "--label", f"agent33.session={self.session_id}",
    ])

    # ... existing network, port, volume, image, and entrypoint logic ...
```

The `DockerKernelSession.__init__` should accept an optional `SandboxConfig` parameter, and the `JupyterAdapter.execute` method should pass the contract's merged sandbox through.

#### 2.3.2 Container Health Verification

After `docker run`, add a brief health check before connecting the Jupyter client:

```python
async def _wait_for_container(self, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        proc = await asyncio.create_subprocess_exec(
            "docker", "inspect", "--format", "{{.State.Running}}",
            self._container_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        if stdout.strip() == b"true":
            return
        await asyncio.sleep(0.5)
    raise RuntimeError(f"Container {self._container_name} failed to start")
```

#### 2.3.3 User Namespace and Non-root Execution

For Jupyter images that support it (e.g., `quay.io/jupyter/minimal-notebook`), add `--user 1000:1000` to run as the `jovyan` user instead of root. This should be configurable via a new field on `KernelContainerPolicy`:

```python
class KernelContainerPolicy(BaseModel):
    # ... existing fields ...
    run_as_user: str | None = None  # e.g., "1000:1000"
    read_only_root: bool = False
    tmpfs_tmp: bool = True
    pids_limit: int = Field(default=100, ge=10, le=10000)
```

### 2.4 Test Strategy for Docker Kernels

Since Docker is not available in CI (and should not be required for unit tests), all Docker kernel tests should use subprocess mocking:

```python
class TestDockerKernelSession:
    @pytest.mark.asyncio
    async def test_build_docker_command_includes_resource_limits(self):
        session = DockerKernelSession(
            "test-session", "python3",
            policy=KernelContainerPolicy(enabled=True, image="jupyter:test"),
            sandbox=SandboxConfig(memory_mb=256, cpu_cores=2),
        )
        # Inspect the command without actually running Docker
        cmd = session._build_docker_command(runtime_dir, connection_info)
        assert "--memory" in cmd
        assert "256m" in cmd
        assert "--cpus" in cmd
        assert "2" in cmd

    @pytest.mark.asyncio
    async def test_build_docker_command_network_isolation(self):
        session = DockerKernelSession(
            "test-net", "python3",
            policy=KernelContainerPolicy(enabled=True, network_enabled=False),
        )
        cmd = session._build_docker_command(runtime_dir, connection_info)
        assert "--network" in cmd
        idx = cmd.index("--network")
        assert cmd[idx + 1] == "none"

    @pytest.mark.asyncio
    async def test_build_docker_command_with_allowed_images_whitelist(self):
        policy = KernelContainerPolicy(
            enabled=True,
            image="disallowed:latest",
            allowed_images=["allowed:latest"],
        )
        session = DockerKernelSession("test-img", "python3", policy=policy)
        with pytest.raises(RuntimeError, match="not permitted"):
            await session.start()

    @pytest.mark.asyncio
    async def test_stop_calls_docker_rm_force(self):
        # Mock create_subprocess_exec to verify cleanup command
        ...

    @pytest.mark.asyncio
    async def test_connection_file_contents(self):
        # Verify the connection file JSON has correct ports and key
        ...

    @pytest.mark.asyncio
    async def test_working_directory_mount(self):
        policy = KernelContainerPolicy(
            enabled=True, mount_working_directory=True, container_workdir="/work",
        )
        session = DockerKernelSession(
            "test-wd", "python3", policy=policy, working_directory="/host/path",
        )
        cmd = session._build_docker_command(runtime_dir, connection_info)
        assert "-v" in cmd
        assert "/host/path:/work" in cmd
```

### 2.5 Files to Change

| File | Change |
|------|--------|
| `engine/src/agent33/execution/adapters/jupyter.py` | Add `SandboxConfig` passthrough to `DockerKernelSession`, resource limit flags, security hardening flags, container health check |
| `engine/src/agent33/execution/models.py` | Add `run_as_user`, `read_only_root`, `tmpfs_tmp`, `pids_limit` to `KernelContainerPolicy` |
| `engine/tests/test_execution_jupyter_adapter.py` | Add `TestDockerKernelSession` class with command-building tests, cleanup tests, image whitelist tests |

---

## 3. Frontend Component Tests

### 3.1 Current Test Infrastructure

The frontend test stack is already well-configured:

- **Test runner:** Vitest 2.1.3 (`vitest run`)
- **DOM environment:** jsdom 26.1.0
- **Testing Library:** `@testing-library/react` 16.3.2, `@testing-library/jest-dom` 6.9.1, `@testing-library/user-event` 14.6.1
- **TypeScript:** 5.6.3

### 3.2 Existing Test Coverage

| File | Type | What it Tests |
|------|------|---------------|
| `frontend/src/lib/api.test.ts` | Unit | API client utilities |
| `frontend/src/lib/workflowLiveTransport.test.ts` | Unit | SSE transport with JWT/API-key auth |
| `frontend/src/components/WorkflowGraph.test.ts` | Component | Node/edge mapping, status colors, edge animation, polling detection, React component rerender |
| `frontend/src/components/OperationCard.test.tsx` | Component | Full workflow execution flow with live transport, graph fetch, event handling, presets |
| `frontend/src/components/ExplanationView.test.ts` | Unit | Explanation rendering |
| `frontend/src/data/domains/componentSecurity.test.ts` | Unit | Domain data structures |
| `frontend/src/data/domains/operationsHub.test.ts` | Unit | Domain data structures |
| `frontend/src/data/domains/improvements.test.ts` | Unit | Domain data structures |
| `frontend/src/data/domains/workflows.test.ts` | Unit | Domain data structures |
| `frontend/src/features/operations-hub/helpers.test.ts` | Unit | Helper functions |
| `frontend/src/features/outcomes-dashboard/helpers.test.ts` | Unit | Helper functions |
| `frontend/src/features/security-dashboard/SecurityDashboard.test.tsx` | Component | Security dashboard rendering |
| `frontend/src/features/improvement-cycle/ImprovementCycleWizard.test.tsx` | Component | Improvement cycle wizard UI |
| `frontend/src/features/improvement-cycle/presets.test.ts` | Unit | Preset data |
| `frontend/src/features/voice/LiveVoicePanel.test.tsx` | Component | Voice panel rendering |

### 3.3 Existing Patterns and Conventions

The codebase uses consistent patterns that new tests should follow:

1. **ReactFlow mocking:** `WorkflowGraph.test.ts` provides a complete mock of `reactflow` that replaces `ReactFlow`, `Background`, `Controls`, `Panel`, `ReactFlowProvider`, `useNodesState`, and `useEdgesState` with minimal implementations. This pattern should be reused wherever components depend on ReactFlow.

2. **API mocking:** `OperationCard.test.tsx` uses `vi.hoisted()` + `vi.mock()` to create stable mock references that survive module reloading. The `apiRequestMock` pattern returns structured response objects matching the `apiRequest` return type.

3. **Live transport mocking:** The `connectWorkflowLiveTransportMock` pattern captures the `onEvent` callback, allowing tests to simulate server-sent events by calling `liveEventHandler?.({ type: "step_completed" })`.

4. **User interactions:** Tests use `@testing-library/user-event` for realistic interactions (`userEvent.click`, `userEvent.selectOptions`).

5. **Assertions:** Tests use `@testing-library/jest-dom` matchers (`toBeInTheDocument`, `toHaveTextContent`) and `waitFor` for async assertions.

### 3.4 Priority Components to Test

Ranked by user-facing impact and current lack of coverage:

| Priority | Component | File | Why |
|----------|-----------|------|-----|
| P1 | `ObservationStream` | `components/ObservationStream.tsx` | Live SSE consumer with no tests. Critical real-time feature. |
| P2 | `HealthPanel` | `components/HealthPanel.tsx` | Status indicator shown on every page load. |
| P3 | `AuthPanel` | `components/AuthPanel.tsx` | Token/API-key entry — affects all authenticated operations. |
| P4 | `DomainPanel` | `components/DomainPanel.tsx` | Container for domain-specific operation cards. |
| P5 | `GlobalSearch` | `components/GlobalSearch.tsx` | Cross-domain search with keyboard shortcuts. |
| P6 | `OperationsHubPanel` | `features/operations-hub/OperationsHubPanel.tsx` | Main operations panel wrapper. |
| P7 | `OutcomesDashboardPanel` | `features/outcomes-dashboard/OutcomesDashboardPanel.tsx` | Outcomes visualization. |
| P8 | `ChatInterface` | `features/chat/ChatInterface.tsx` | Agent chat with streaming responses. |

### 3.5 Test Plans for Priority Components

#### 3.5.1 ObservationStream

The component uses `fetch()` with `ReadableStream` parsing (same pattern as workflowLiveTransport). Tests should:

- Verify SSE connection setup with correct auth header
- Simulate incoming events and verify they appear in the DOM
- Verify event filtering (only `handoff_context_wipe`, specific `tool_call` events)
- Verify max event buffer (10 events, newest first)
- Verify cleanup on unmount (reader cancel)
- Verify empty state renders nothing

Mock strategy: `vi.stubGlobal("fetch", ...)` with a `ReadableStream` that emits encoded SSE chunks (same pattern as `workflowLiveTransport.test.ts`).

#### 3.5.2 HealthPanel

Tests should:

- Render loading state during initial fetch
- Render healthy status with service details
- Render degraded/unhealthy states with error information
- Handle fetch errors gracefully
- Verify periodic refresh if applicable

Mock strategy: `vi.mock("../lib/api")` with `apiRequest` returning health check responses.

#### 3.5.3 AuthPanel

Tests should:

- Render token and API key input fields
- Handle token submission and storage
- Verify token format validation (if any)
- Handle clear/logout action
- Verify callback invocations on auth state changes

Mock strategy: Direct render with callback props.

### 3.6 Mock Strategy for API Calls

All frontend tests should follow the established `vi.hoisted()` + `vi.mock()` pattern:

```typescript
const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn()
}));

vi.mock("../lib/api", () => ({
  apiRequest: apiRequestMock,
  getRuntimeConfig: () => ({ API_BASE_URL: "http://localhost:8000" }),
  buildUrl: (base: string, path: string, params: Record<string, string>) => {
    let url = `${base}${path}`;
    for (const [key, value] of Object.entries(params)) {
      url = url.replace(`{${key}}`, value);
    }
    return url;
  }
}));
```

For SSE/streaming endpoints, use the `buildSseResponse` helper pattern from `workflowLiveTransport.test.ts`.

For WebSocket connections, use `vi.stubGlobal("WebSocket", ...)` with a mock class.

### 3.7 Files to Create/Change

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/components/ObservationStream.test.tsx` | Create | SSE connection, event rendering, filtering, cleanup |
| `frontend/src/components/HealthPanel.test.tsx` | Create | Health status rendering, error handling |
| `frontend/src/components/AuthPanel.test.tsx` | Create | Auth input, submission, state callbacks |
| `frontend/src/components/DomainPanel.test.tsx` | Create | Domain rendering, operation card delegation |
| `frontend/src/components/GlobalSearch.test.tsx` | Create | Search input, results, keyboard shortcuts |

---

## 4. Consolidated Test Strategy and File Layout

### 4.1 Backend Tests (engine/tests/)

```
engine/tests/
  test_workflow_sse.py               # Existing — add reconnection/Last-Event-Id tests
  test_workflow_ws.py                # Existing — no changes needed
  test_execution_jupyter_adapter.py  # Existing — add TestDockerKernelSession class
```

New test classes to add:

**`test_workflow_sse.py`:**
- `TestWorkflowSSEReconnection`
  - `test_sse_event_frames_include_id_field` — verify `id: N` appears in SSE output
  - `test_sse_sync_event_has_id_zero` — initial sync event has sequence 0
  - `test_sse_events_have_monotonically_increasing_ids` — publish multiple events, verify sequence
  - `test_last_event_id_header_triggers_replay` — send `Last-Event-Id` header, verify missed events replayed
  - `test_last_event_id_too_old_sends_full_sync` — stale ID falls back to fresh sync

**`test_execution_jupyter_adapter.py`:**
- `TestDockerKernelSession`
  - `test_build_docker_command_basic_structure` — verify command starts with `docker run -d --rm --name`
  - `test_build_docker_command_resource_limits` — verify `--memory` and `--cpus` from sandbox config
  - `test_build_docker_command_network_none` — verify `--network none` when disabled
  - `test_build_docker_command_network_bridge` — verify `--network bridge` when enabled
  - `test_build_docker_command_port_mapping` — verify all 5 ZMQ ports are mapped
  - `test_build_docker_command_volume_mounts` — verify runtime dir and working directory mounts
  - `test_build_docker_command_extra_run_args` — verify policy extra args are appended
  - `test_start_rejects_disallowed_image` — verify RuntimeError on image not in whitelist
  - `test_start_rejects_missing_docker` — verify RuntimeError when docker not on PATH
  - `test_stop_invokes_docker_rm_force` — mock subprocess, verify cleanup
  - `test_connection_file_structure` — verify written JSON has correct fields
  - `test_sanitize_container_name` — verify special characters are replaced

### 4.2 Frontend Tests (frontend/src/)

```
frontend/src/
  components/
    AuthPanel.test.tsx                # New
    DomainPanel.test.tsx              # New
    ExplanationView.test.ts           # Existing
    GlobalSearch.test.tsx             # New
    HealthPanel.test.tsx              # New
    ObservationStream.test.tsx        # New
    OperationCard.test.tsx            # Existing
    WorkflowGraph.test.ts            # Existing
  features/
    improvement-cycle/
      ImprovementCycleWizard.test.tsx # Existing
      presets.test.ts                 # Existing
    security-dashboard/
      SecurityDashboard.test.tsx      # Existing
    voice/
      LiveVoicePanel.test.tsx         # Existing
  data/domains/
    componentSecurity.test.ts         # Existing
    improvements.test.ts              # Existing
    operationsHub.test.ts             # Existing
    workflows.test.ts                 # Existing
  lib/
    api.test.ts                       # Existing
    workflowLiveTransport.test.ts     # Existing — add reconnection tests
```

### 4.3 Estimated Test Count

| Area | New Tests | Existing Tests | Total |
|------|-----------|----------------|-------|
| SSE reconnection (backend) | ~5 | 8 | ~13 |
| Docker kernel session (backend) | ~12 | ~25 | ~37 |
| ObservationStream (frontend) | ~6 | 0 | ~6 |
| HealthPanel (frontend) | ~4 | 0 | ~4 |
| AuthPanel (frontend) | ~4 | 0 | ~4 |
| DomainPanel (frontend) | ~3 | 0 | ~3 |
| GlobalSearch (frontend) | ~4 | 0 | ~4 |
| SSE reconnection (frontend) | ~3 | 2 | ~5 |
| **Total** | **~41** | **~35** | **~76** |

### 4.4 Implementation Order

1. **Phase 38 Docker kernel tests** — Highest gap severity (no existing tests for DockerKernelSession). Pure unit tests with subprocess mocking. No infrastructure dependencies.
2. **Phase 25 SSE reconnection (backend)** — Builds on existing well-tested SSE infrastructure. Event ID emission is a small change to `_format_sse`. Ring buffer is a contained addition to the manager.
3. **Frontend component tests** — Start with ObservationStream (most similar to existing transport test patterns), then HealthPanel and AuthPanel.
4. **Phase 25 SSE reconnection (frontend)** — Retry loop in `workflowLiveTransport.ts`. Depends on backend event ID support.

### 4.5 Risk Notes

- **Docker kernel tests require careful mocking:** `asyncio.create_subprocess_exec` must be patched to avoid actual Docker invocations. The `_build_docker_command` method is testable as a pure function (returns `list[str]`), which is the easiest entry point.
- **SSE event ring buffer adds memory per run:** Bound to 200 events max. At ~500 bytes per event, this is ~100KB per active run. Acceptable for the expected concurrent run count.
- **Frontend test mocking depth:** Components like `ObservationStream` depend on `fetch` + `ReadableStream` + `TextDecoder`. The existing `buildSseResponse` helper in `workflowLiveTransport.test.ts` demonstrates this pattern already works in the jsdom environment.
- **ReactFlow mock maintenance:** The comprehensive ReactFlow mock in `WorkflowGraph.test.ts` covers the v11 API. Any components that import from `reactflow` will need this mock. Consider extracting it to a shared `__mocks__/reactflow.ts` or `test-utils/` file if more than two test files need it.
