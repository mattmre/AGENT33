# Hook Framework Architecture (H01 -- Phase 32.1)

**Date**: 2026-02-27
**Author**: Session 50 Research Agent
**Status**: Architecture Plan (Ready for Implementation)
**Scope**: 3-tier middleware hook chain, event taxonomy, data model, integration points, file plan

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Codebase Analysis: Existing Patterns](#2-codebase-analysis-existing-patterns)
3. [Hook Types & Event Taxonomy](#3-hook-types--event-taxonomy)
4. [3-Tier Middleware Chain Design](#4-3-tier-middleware-chain-design)
5. [Async Execution Model](#5-async-execution-model)
6. [Multi-Tenancy](#6-multi-tenancy)
7. [Data Model](#7-data-model)
8. [API Endpoints](#8-api-endpoints)
9. [Integration Points](#9-integration-points)
10. [File Plan](#10-file-plan)
11. [Migration Strategy](#11-migration-strategy)
12. [Design Decisions & Rationale](#12-design-decisions--rationale)

---

## 1. Executive Summary

This document specifies the architecture for AGENT-33's Hook Framework (H01, Phase 32.1). The hook framework provides a 3-tier middleware chain system that intercepts and extends agent invocations, tool executions, and workflow step processing without modifying the core execution paths.

**Design philosophy**: The hook framework is modeled after the Microsoft Agent Framework's 3-tier middleware pattern (identified as best-in-class in `docs/research/hooks-mcp-plugin-architecture-research.md`), adapted to AGENT-33's existing architecture. Critically, AGENT-33 already has a working middleware chain in `engine/src/agent33/connectors/` (the connector boundary system). The hook framework generalizes this proven pattern into a first-class extensibility mechanism for the agent/tool/workflow tiers.

**Key design constraints**:
- Less than 500ms total budget per hook chain execution
- Failure isolation: one hook failure must not crash the chain
- Backward compatibility: all existing functionality works unchanged without hooks
- Multi-tenancy: hook configurations are tenant-isolated
- The hook framework does NOT replace the existing connector boundary middleware -- it operates at a higher abstraction level

**Estimated scope**: 9 new files, ~90-110 tests, 6-8 API endpoints, 2-3 sessions to implement.

---

## 2. Codebase Analysis: Existing Patterns

### 2.1 Connector Boundary Middleware Chain (Existing -- Reusable Pattern)

The codebase already implements a full middleware chain pattern in `engine/src/agent33/connectors/`. This is the primary architectural precedent.

**`connectors/middleware.py`** -- defines the `ConnectorMiddleware` protocol:
```python
class ConnectorMiddleware(Protocol):
    async def __call__(
        self,
        request: ConnectorRequest,
        call_next: ConnectorHandler,
    ) -> Any: ...
```

**`connectors/executor.py`** -- chains middleware via reversed iteration:
```python
class ConnectorExecutor:
    async def execute(self, request: ConnectorRequest, handler: ConnectorHandler) -> Any:
        next_handler = handler
        for middleware in reversed(self._middlewares):
            current = middleware
            downstream = next_handler
            async def wrapped(req, m=current, n=downstream):
                return await m(req, n)
            next_handler = wrapped
        return await next_handler(request)
```

**Built-in middleware**: `GovernanceMiddleware`, `CircuitBreakerMiddleware`, `TimeoutMiddleware`, `RetryMiddleware`, `MetricsMiddleware`.

**`connectors/boundary.py`** -- factory function `build_connector_boundary_executor()` composes the chain from settings.

**Key takeaway**: The `ConnectorMiddleware` protocol + `ConnectorExecutor` chaining pattern is battle-tested and should be generalized into the hook framework's chain runner.

### 2.2 AuthMiddleware (FastAPI-level)

**File**: `engine/src/agent33/security/middleware.py`

The `AuthMiddleware` extends Starlette's `BaseHTTPMiddleware` and intercepts HTTP requests. It resolves tenant identity from JWT or API key and attaches `request.state.user` (a `TokenPayload` with `tenant_id`).

**Hook point**: The request lifecycle hook tier would operate at this same layer but with a different concern (extensible user-defined pre/post processing vs. fixed authentication logic).

### 2.3 AgentRuntime (Agent Invocation Flow)

**File**: `engine/src/agent33/agents/runtime.py`

The `AgentRuntime.invoke()` method follows this flow:
1. Build system prompt (line 323)
2. Inject skill context (lines 326-336)
3. Inject memory context (lines 339-351)
4. Validate required inputs (lines 354-356)
5. Resolve execution parameters / effort routing (line 365)
6. Call LLM with retries (lines 371-393)
7. Parse output (line 395)
8. Build result (lines 397-403)
9. Emit routing metrics (line 404)
10. Record observation (lines 407-423)
11. Emit trace spans (lines 426-434)

**Hook injection points**:
- **Pre-agent**: After input validation (step 4), before LLM call (step 6). Context: agent definition, inputs, system prompt.
- **Post-agent**: After result is built (step 8), before observation recording (step 10). Context: agent definition, inputs, result, duration.

The `invoke_iterative()` method has the same structure but routes through `ToolLoop`. Same pre/post injection points apply.

### 2.4 ToolLoop (Tool Execution Flow)

**File**: `engine/src/agent33/agents/tool_loop.py`

The `ToolLoop._execute_tool_calls()` method (line 425) processes each tool call:
1. Parse arguments (lines 441-462)
2. Governance check (lines 465-484)
3. Autonomy enforcement check (lines 487-514)
4. Execute tool via registry (lines 517-530)
5. Governance audit (lines 533-534)
6. Leakage detection (lines 537-549)
7. Record observation (lines 552-563)
8. Track stats (lines 566-568)

**Hook injection points**:
- **Pre-tool**: After governance check (step 2), before execution (step 4). Context: tool name, parsed args, tool context.
- **Post-tool**: After execution (step 4), before audit/observation (step 5). Context: tool name, args, result, duration.

### 2.5 WorkflowExecutor (Workflow Step Flow)

**File**: `engine/src/agent33/workflows/executor.py`

The `WorkflowExecutor._execute_step()` method (line 193):
1. Evaluate condition (lines 203-217)
2. Resolve inputs (line 220)
3. Retry loop (lines 226-258):
   a. Dispatch action (line 228)
   b. Apply timeout (lines 231-233)
   c. Return StepResult

**Hook injection points**:
- **Pre-step**: After condition evaluation and input resolution (step 2), before dispatch (step 3a). Context: step definition, resolved inputs, workflow state.
- **Post-step**: After StepResult is built, before return. Context: step definition, inputs, result, duration.

### 2.6 Tool Registry Execution

**File**: `engine/src/agent33/tools/registry.py`

The `ToolRegistry.validated_execute()` method (line 187):
1. Look up tool (line 200)
2. Get schema (line 205)
3. Validate params (lines 207-210)
4. Execute tool (line 212)

This is the lower-level entry point. The ToolLoop already wraps this with governance and autonomy, so hooks at the ToolLoop level are sufficient. However, direct `validated_execute()` callers (e.g., future non-agent consumers) would also benefit from hooks here.

### 2.7 ToolGovernance (Existing Pre/Post Pattern)

**File**: `engine/src/agent33/tools/governance.py`

Already implements a pre-execute check (`pre_execute_check()`) and post-execute audit (`log_execution()`). The hook framework should call governance first, then run hooks, maintaining the existing security boundary.

---

## 3. Hook Types & Event Taxonomy

### 3.1 Event Types

```
HookEventType (StrEnum):
    # Agent lifecycle
    AGENT_INVOKE_PRE      = "agent.invoke.pre"
    AGENT_INVOKE_POST     = "agent.invoke.post"

    # Tool execution
    TOOL_EXECUTE_PRE      = "tool.execute.pre"
    TOOL_EXECUTE_POST     = "tool.execute.post"

    # Workflow step execution
    WORKFLOW_STEP_PRE     = "workflow.step.pre"
    WORKFLOW_STEP_POST    = "workflow.step.post"

    # Request lifecycle (HTTP layer)
    REQUEST_PRE           = "request.pre"
    REQUEST_POST          = "request.post"

    # Memory operations (discovered from codebase -- progressive recall, observation)
    MEMORY_STORE_PRE      = "memory.store.pre"
    MEMORY_STORE_POST     = "memory.store.post"

    # LLM call (discovered from runtime.py -- wraps router.complete)
    LLM_CALL_PRE          = "llm.call.pre"
    LLM_CALL_POST         = "llm.call.post"
```

### 3.2 Event Type Justification

| Event Type | Source Code Location | Use Cases |
|---|---|---|
| `agent.invoke.pre/post` | `runtime.py` lines 321-436 | Logging, input sanitization, cost estimation, tenant-specific prompt injection, A/B testing |
| `tool.execute.pre/post` | `tool_loop.py` lines 425-572 | Tool result caching, usage metering, output transformation, sensitive data redaction |
| `workflow.step.pre/post` | `executor.py` lines 193-259 | Step-level audit trail, progress notifications, conditional override, dynamic input augmentation |
| `request.pre/post` | `middleware.py` (security) | Rate limiting, request logging, response transformation, custom headers |
| `memory.store.pre/post` | `memory/observation.py`, `memory/long_term.py` | PII scrubbing, content enrichment, deduplication |
| `llm.call.pre/post` | `runtime.py` line 373, `tool_loop.py` line 168 | Prompt caching, response logging, model fallback, cost tracking |

### 3.3 Phase 1 vs Phase 2 Scope

**Phase 1 (H01 -- this implementation)**:
- `agent.invoke.pre/post`
- `tool.execute.pre/post`
- `workflow.step.pre/post`
- `request.pre/post`

**Phase 2 (future)**:
- `memory.store.pre/post`
- `llm.call.pre/post`
- Custom/user-defined event types

---

## 4. 3-Tier Middleware Chain Design

### 4.1 Chain Architecture

```
                    +-----------------------+
                    |   Hook Chain Runner    |
                    +-----------------------+
                    |                       |
          +---------+---------+   +---------+---------+
          |  Pre-Hook Chain   |   |  Post-Hook Chain  |
          +---+---+---+---+--+   +---+---+---+---+--+
              |   |   |   |          |   |   |   |
            H1  H2  H3  ...       H1  H2  H3  ...
         (priority order)        (priority order)
```

The 3 tiers map to:
1. **Agent Tier** -- intercepts `AgentRuntime.invoke()` and `invoke_iterative()`
2. **Tool Tier** -- intercepts `ToolLoop._execute_tool_calls()` individual tool calls
3. **Workflow Tier** -- intercepts `WorkflowExecutor._execute_step()`

Each tier runs independently. There is no cross-tier dependency within a single request (though an agent invocation triggered by a workflow step will run both the workflow tier hooks and the agent tier hooks).

### 4.2 Hook Protocol

```python
from __future__ import annotations
from typing import Any, Protocol
from collections.abc import Awaitable, Callable

class Hook(Protocol):
    """Base hook protocol. All hooks implement this interface."""

    @property
    def name(self) -> str: ...

    @property
    def event_type(self) -> str: ...

    @property
    def priority(self) -> int: ...

    @property
    def enabled(self) -> bool: ...

    async def execute(
        self,
        context: HookContext,
        call_next: Callable[[HookContext], Awaitable[HookContext]],
    ) -> HookContext: ...
```

### 4.3 Context Objects

Each tier gets a strongly-typed context:

```python
@dataclasses.dataclass(slots=True)
class HookContext:
    """Base context passed through hook chains."""
    event_type: str
    tenant_id: str
    metadata: dict[str, Any]  # cross-hook state sharing
    abort: bool = False  # set to True to short-circuit
    abort_reason: str = ""
    results: list[HookResult] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(slots=True)
class AgentHookContext(HookContext):
    """Context for agent.invoke.pre and agent.invoke.post hooks."""
    agent_name: str = ""
    agent_definition: AgentDefinition | None = None
    inputs: dict[str, Any] = dataclasses.field(default_factory=dict)
    system_prompt: str = ""
    model: str = ""
    result: AgentResult | None = None  # populated in post hooks
    duration_ms: float = 0.0  # populated in post hooks


@dataclasses.dataclass(slots=True)
class ToolHookContext(HookContext):
    """Context for tool.execute.pre and tool.execute.post hooks."""
    tool_name: str = ""
    arguments: dict[str, Any] = dataclasses.field(default_factory=dict)
    tool_context: ToolContext | None = None
    result: ToolResult | None = None  # populated in post hooks
    duration_ms: float = 0.0  # populated in post hooks


@dataclasses.dataclass(slots=True)
class WorkflowHookContext(HookContext):
    """Context for workflow.step.pre and workflow.step.post hooks."""
    workflow_name: str = ""
    step_id: str = ""
    step_action: str = ""
    inputs: dict[str, Any] = dataclasses.field(default_factory=dict)
    state: dict[str, Any] = dataclasses.field(default_factory=dict)
    result: StepResult | None = None  # populated in post hooks
    duration_ms: float = 0.0  # populated in post hooks


@dataclasses.dataclass(slots=True)
class RequestHookContext(HookContext):
    """Context for request.pre and request.post hooks."""
    method: str = ""
    path: str = ""
    headers: dict[str, str] = dataclasses.field(default_factory=dict)
    body: bytes = b""
    status_code: int = 0  # populated in post hooks
    response_headers: dict[str, str] = dataclasses.field(default_factory=dict)  # post
    duration_ms: float = 0.0  # populated in post hooks
```

### 4.4 Chain Runner

The chain runner generalizes `ConnectorExecutor`'s chaining pattern:

```python
class HookChainRunner:
    """Executes a chain of hooks with priority ordering and failure isolation."""

    def __init__(
        self,
        hooks: list[Hook],
        timeout_ms: float = 500.0,
        fail_open: bool = True,
    ) -> None:
        self._hooks = sorted(hooks, key=lambda h: h.priority)
        self._timeout_ms = timeout_ms
        self._fail_open = fail_open

    async def run(self, context: HookContext) -> HookContext:
        """Execute all hooks in priority order via middleware chain delegation."""
        # Build the chain from innermost to outermost
        async def terminal(ctx: HookContext) -> HookContext:
            return ctx

        chain = terminal
        for hook in reversed(self._hooks):
            if not hook.enabled:
                continue
            downstream = chain
            current_hook = hook

            async def link(
                ctx: HookContext,
                h: Hook = current_hook,
                next_fn: Callable = downstream,
            ) -> HookContext:
                if ctx.abort:
                    return ctx
                start = time.monotonic()
                try:
                    result_ctx = await asyncio.wait_for(
                        h.execute(ctx, next_fn),
                        timeout=self._timeout_ms / 1000.0,
                    )
                    duration = (time.monotonic() - start) * 1000
                    result_ctx.results.append(HookResult(
                        hook_name=h.name,
                        success=True,
                        duration_ms=duration,
                    ))
                    return result_ctx
                except Exception as exc:
                    duration = (time.monotonic() - start) * 1000
                    ctx.results.append(HookResult(
                        hook_name=h.name,
                        success=False,
                        error=str(exc),
                        duration_ms=duration,
                    ))
                    if self._fail_open:
                        # Skip this hook, continue chain
                        return await next_fn(ctx)
                    else:
                        ctx.abort = True
                        ctx.abort_reason = f"Hook '{h.name}' failed: {exc}"
                        return ctx

            chain = link

        return await chain(context)
```

### 4.5 Short-Circuit / Abort Capability

Any hook can abort the chain by setting `context.abort = True` and providing `context.abort_reason`. Once abort is set:
- Remaining hooks in the chain are skipped
- The caller receives the context with abort=True and checks it before proceeding
- For pre-hooks, aborting prevents the main handler from executing
- For post-hooks, aborting prevents subsequent hooks but the main handler has already run

**Example -- input validation hook that blocks agent invocation:**
```python
class InputSanitizationHook:
    name = "input_sanitization"
    event_type = "agent.invoke.pre"
    priority = 10  # run early
    enabled = True

    async def execute(self, context, call_next):
        if detect_injection(context.inputs):
            context.abort = True
            context.abort_reason = "Prompt injection detected"
            return context
        return await call_next(context)
```

### 4.6 Error Handling

Two modes, configurable per chain:

1. **Fail-open (default)**: A hook failure is logged and the chain continues. The failed hook's `HookResult` records `success=False` with the error. This is appropriate for observability, logging, and non-critical hooks.

2. **Fail-closed**: A hook failure aborts the chain. The context is returned with `abort=True`. This is appropriate for security-critical hooks (input validation, PII detection).

The mode is set per `HookChainRunner` instance, which is configured per event type in the `HookRegistry`.

---

## 5. Async Execution Model

### 5.1 Timeout Budget

- **Per-hook timeout**: 200ms default (configurable per hook definition)
- **Per-chain timeout**: 500ms total budget
- **Implementation**: `asyncio.wait_for()` wrapping each hook's `execute()` call
- **Timeout handling**: Treated as a hook failure; follows fail-open/fail-closed policy

### 5.2 Sequential vs Concurrent Execution

**Default: Sequential execution** within each chain. Hooks run in priority order (lowest number first). This ensures:
- Deterministic execution order
- A hook can depend on metadata set by a prior hook
- Abort propagation is well-defined

**Opt-in concurrent execution**: For independent post-hooks that don't need ordering (e.g., multiple notification hooks), a `ConcurrentHookChainRunner` variant runs all hooks in parallel via `asyncio.gather()`:

```python
class ConcurrentHookChainRunner:
    """Runs all hooks concurrently. Use for independent post-processing hooks."""

    async def run(self, context: HookContext) -> HookContext:
        tasks = [
            asyncio.wait_for(
                hook.execute(context, _noop_next),
                timeout=self._timeout_ms / 1000.0,
            )
            for hook in self._hooks if hook.enabled
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Aggregate results...
        return context
```

### 5.3 Failure Isolation

- Each hook runs in its own `try/except` block
- `asyncio.CancelledError` is re-raised (never swallowed)
- `TimeoutError` is caught and recorded as a hook failure
- All other exceptions are caught, logged with structlog, and recorded in `HookResult`
- The main execution path (agent invoke, tool execute, workflow step) is never affected by hook failures in fail-open mode

---

## 6. Multi-Tenancy

### 6.1 Tenant-Isolated Hook Configuration

Each hook definition includes a `tenant_id` field. The `HookRegistry` enforces tenant isolation:

```python
class HookRegistry:
    def get_hooks(
        self,
        event_type: str,
        tenant_id: str,
    ) -> list[Hook]:
        """Return hooks for the given event type, filtered by tenant.

        Returns:
        - System hooks (tenant_id="") -- always included
        - Tenant-specific hooks matching the provided tenant_id
        """
        return [
            h for h in self._hooks[event_type]
            if h.tenant_id == "" or h.tenant_id == tenant_id
        ]
```

### 6.2 Integration with AuthMiddleware

The existing `AuthMiddleware` in `engine/src/agent33/security/middleware.py` resolves tenant identity from JWT/API-key and stores it in `request.state.user.tenant_id`. The hook framework reads this tenant_id and passes it through:

1. **Request hooks**: Read `request.state.user.tenant_id` directly
2. **Agent hooks**: Receive `tenant_id` from `AgentRuntime._tenant_id` (already plumbed at line 238)
3. **Tool hooks**: Receive `tenant_id` via the `HookContext` populated by the ToolLoop
4. **Workflow hooks**: Receive `tenant_id` from the workflow execution context

### 6.3 System vs Tenant Hooks

- **System hooks** (`tenant_id=""`) run for all tenants. Examples: metrics collection, audit logging, security checks.
- **Tenant hooks** (`tenant_id="acme-corp"`) run only for that tenant. Examples: custom input enrichment, tenant-specific output formatting.
- System hooks always run before tenant hooks at the same priority level.

---

## 7. Data Model

### 7.1 HookDefinition

```python
class HookDefinition(BaseModel):
    """Persistent hook configuration stored in DB or loaded from YAML."""

    hook_id: str = Field(default_factory=lambda: f"hook_{uuid4().hex[:12]}")
    name: str
    description: str = ""
    event_type: HookEventType
    priority: int = Field(default=100, ge=0, le=1000)
    handler_ref: str  # dotted Python path or plugin identifier
    timeout_ms: float = Field(default=200.0, gt=0, le=5000)
    enabled: bool = True
    tenant_id: str = ""  # "" = system hook
    config: dict[str, Any] = Field(default_factory=dict)  # hook-specific config
    fail_mode: Literal["open", "closed"] = "open"
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

### 7.2 HookResult

```python
@dataclasses.dataclass(frozen=True, slots=True)
class HookResult:
    """Result of a single hook execution within a chain."""

    hook_name: str
    success: bool
    data: dict[str, Any] = dataclasses.field(default_factory=dict)
    error: str = ""
    duration_ms: float = 0.0
```

### 7.3 HookChainResult

```python
@dataclasses.dataclass(frozen=True, slots=True)
class HookChainResult:
    """Aggregated result of running a full hook chain."""

    event_type: str
    hook_results: list[HookResult]
    aborted: bool = False
    abort_reason: str = ""
    total_duration_ms: float = 0.0

    @property
    def all_succeeded(self) -> bool:
        return all(r.success for r in self.hook_results)

    @property
    def hook_count(self) -> int:
        return len(self.hook_results)
```

### 7.4 HookExecutionLog

For diagnostics and audit:

```python
class HookExecutionLog(BaseModel):
    """Persisted record of a hook chain execution."""

    log_id: str = Field(default_factory=lambda: uuid4().hex)
    event_type: str
    tenant_id: str
    hook_results: list[dict[str, Any]]
    aborted: bool = False
    abort_reason: str = ""
    total_duration_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: str = ""  # correlation ID
```

---

## 8. API Endpoints

### 8.1 Hook Management (CRUD)

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/hooks` | Create a new hook definition |
| `GET` | `/v1/hooks` | List all hooks (filterable by event_type, tenant_id, enabled) |
| `GET` | `/v1/hooks/{hook_id}` | Get a specific hook definition |
| `PUT` | `/v1/hooks/{hook_id}` | Update a hook definition |
| `DELETE` | `/v1/hooks/{hook_id}` | Delete a hook definition |
| `PUT` | `/v1/hooks/{hook_id}/toggle` | Enable/disable a hook |

### 8.2 Hook Diagnostics

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/hooks/logs` | List recent hook execution logs |
| `GET` | `/v1/hooks/logs/{log_id}` | Get detailed execution log |
| `GET` | `/v1/hooks/stats` | Aggregate hook execution statistics |
| `POST` | `/v1/hooks/{hook_id}/test` | Dry-run a hook with sample context |

### 8.3 Request/Response Schemas

```python
class HookCreateRequest(BaseModel):
    name: str
    description: str = ""
    event_type: HookEventType
    priority: int = 100
    handler_ref: str
    timeout_ms: float = 200.0
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    fail_mode: Literal["open", "closed"] = "open"
    tags: list[str] = Field(default_factory=list)

class HookResponse(BaseModel):
    hook_id: str
    name: str
    description: str
    event_type: str
    priority: int
    handler_ref: str
    timeout_ms: float
    enabled: bool
    tenant_id: str
    config: dict[str, Any]
    fail_mode: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

class HookTestRequest(BaseModel):
    sample_context: dict[str, Any]

class HookTestResponse(BaseModel):
    result: HookResult
    context_after: dict[str, Any]
```

### 8.4 Auth Requirements

All hook endpoints require the `hooks:manage` scope. Hook execution logs require `hooks:read`. System hooks (tenant_id="") require the `hooks:admin` scope.

---

## 9. Integration Points

### 9.1 Agent Invocation Hooks

**File**: `engine/src/agent33/agents/runtime.py`

**Pre-hook injection** -- in `invoke()` method, after input validation, before LLM call:

```python
# Line 356 (after input validation) -> INSERT HERE
# --- Hook: agent.invoke.pre ---
if hook_registry is not None:
    hook_ctx = AgentHookContext(
        event_type="agent.invoke.pre",
        tenant_id=self._tenant_id,
        metadata={},
        agent_name=self._definition.name,
        agent_definition=self._definition,
        inputs=inputs,
        system_prompt=system_prompt,
        model=routed_model,
    )
    hook_ctx = await hook_chain_runner.run(hook_ctx)
    if hook_ctx.abort:
        raise HookAbortError(hook_ctx.abort_reason)
    # Allow hooks to modify inputs and system prompt
    inputs = hook_ctx.inputs
    system_prompt = hook_ctx.system_prompt

# Line 365 (existing: resolve execution parameters)
```

**Post-hook injection** -- after result is built, before observation:

```python
# Line 404 (after emit_routing_metrics) -> INSERT HERE
# --- Hook: agent.invoke.post ---
if hook_registry is not None:
    hook_ctx = AgentHookContext(
        event_type="agent.invoke.post",
        tenant_id=self._tenant_id,
        metadata={},
        agent_name=self._definition.name,
        agent_definition=self._definition,
        inputs=inputs,
        result=result,
        duration_ms=(time.monotonic() - start) * 1000,
    )
    await hook_chain_runner.run(hook_ctx)
    # Post hooks cannot modify the result (immutable AgentResult)

# Line 407 (existing: record observation)
```

**Same pattern applies to `invoke_iterative()`** at analogous positions.

**Constructor change**: Add `hook_registry: HookRegistry | None = None` parameter to `AgentRuntime.__init__()`.

### 9.2 Tool Execution Hooks

**File**: `engine/src/agent33/agents/tool_loop.py`

**Pre-hook injection** -- in `_execute_tool_calls()`, after governance/autonomy checks, before tool execution:

```python
# Line 514 (after autonomy enforcement) -> INSERT HERE
# --- Hook: tool.execute.pre ---
if self._hook_registry is not None:
    tool_hook_ctx = ToolHookContext(
        event_type="tool.execute.pre",
        tenant_id=self._tenant_id,
        metadata={},
        tool_name=tool_name,
        arguments=parsed_args,
        tool_context=context,
    )
    tool_hook_ctx = await self._tool_hook_runner.run(tool_hook_ctx)
    if tool_hook_ctx.abort:
        result = ToolResult.fail(f"Hook aborted: {tool_hook_ctx.abort_reason}")
        results.append(result)
        continue
    # Allow hooks to modify arguments
    parsed_args = tool_hook_ctx.arguments

# Line 517 (existing: execute tool)
```

**Post-hook injection** -- after tool execution, before governance audit:

```python
# Line 530 (after tool execution try/except) -> INSERT HERE
# --- Hook: tool.execute.post ---
if self._hook_registry is not None:
    tool_hook_ctx = ToolHookContext(
        event_type="tool.execute.post",
        tenant_id=self._tenant_id,
        metadata={},
        tool_name=tool_name,
        arguments=parsed_args,
        tool_context=context,
        result=result,
        duration_ms=tool_duration_ms,
    )
    tool_hook_ctx = await self._tool_hook_runner.run(tool_hook_ctx)
    # Post hooks can replace the result (e.g., output transformation)
    if tool_hook_ctx.result is not None:
        result = tool_hook_ctx.result

# Line 533 (existing: governance audit)
```

**Constructor change**: Add `hook_registry: HookRegistry | None = None` and `tenant_id: str = ""` parameters to `ToolLoop.__init__()`.

### 9.3 Workflow Step Hooks

**File**: `engine/src/agent33/workflows/executor.py`

**Pre-hook injection** -- in `_execute_step()`, after input resolution, before dispatch:

```python
# Line 220 (after resolve_inputs) -> INSERT HERE
# --- Hook: workflow.step.pre ---
if self._hook_registry is not None:
    wf_hook_ctx = WorkflowHookContext(
        event_type="workflow.step.pre",
        tenant_id=self._tenant_id,
        metadata={},
        workflow_name=self._definition.name,
        step_id=step.id,
        step_action=step.action.value,
        inputs=resolved_inputs,
        state=dict(state),  # snapshot
    )
    wf_hook_ctx = await self._step_hook_runner.run(wf_hook_ctx)
    if wf_hook_ctx.abort:
        return StepResult(
            step_id=step.id,
            status="failed",
            error=f"Hook aborted: {wf_hook_ctx.abort_reason}",
        )
    resolved_inputs = wf_hook_ctx.inputs

# Line 226 (existing: retry loop)
```

**Post-hook injection** -- after StepResult is built:

```python
# Line 239 (after successful StepResult return) -> INSERT HERE (refactor return)
# --- Hook: workflow.step.post ---
step_result = StepResult(...)  # existing construction
if self._hook_registry is not None:
    wf_hook_ctx = WorkflowHookContext(
        event_type="workflow.step.post",
        tenant_id=self._tenant_id,
        metadata={},
        workflow_name=self._definition.name,
        step_id=step.id,
        step_action=step.action.value,
        inputs=resolved_inputs,
        state=dict(state),
        result=step_result,
        duration_ms=step_result.duration_ms,
    )
    await self._step_hook_runner.run(wf_hook_ctx)
return step_result
```

**Constructor change**: Add `hook_registry: HookRegistry | None = None` and `tenant_id: str = ""` parameters to `WorkflowExecutor.__init__()`.

### 9.4 Request Lifecycle Hooks

**File**: `engine/src/agent33/main.py`

A new `HookMiddleware` added to the FastAPI middleware stack:

```python
# Line 503 (after RequestSizeLimitMiddleware) -> INSERT HERE
app.add_middleware(HookMiddleware)  # before AuthMiddleware
```

**Middleware order** (last added = first executed in Starlette):
1. `CORSMiddleware` (outermost)
2. `AuthMiddleware`
3. `HookMiddleware` (request pre/post hooks, runs AFTER auth resolves tenant)
4. `RequestSizeLimitMiddleware` (innermost)

Wait -- this ordering is wrong. In Starlette, last added = first executed. So the actual execution order is:

```
Request → RequestSizeLimit → HookMiddleware → AuthMiddleware → CORS → Router
```

But we need tenant_id from AuthMiddleware. So HookMiddleware must run AFTER AuthMiddleware. The correct addition:

```python
# In main.py, line 501 area:
# Middleware order (last added = first executed):
# 1. HookMiddleware (first executed - has tenant from auth)  <-- add AFTER auth
# 2. RequestSizeLimitMiddleware
# 3. AuthMiddleware
# 4. CORSMiddleware (last executed)

app.add_middleware(HookMiddleware)  # ADD THIS LINE FIRST (so it runs last)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(AuthMiddleware)
# CORS added below
```

Actually, to run AFTER auth resolves tenant, HookMiddleware should be added BEFORE AuthMiddleware in the `add_middleware` calls (because Starlette processes them in reverse order of addition):

```python
app.add_middleware(HookMiddleware)     # executed AFTER auth (added first = runs last)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(AuthMiddleware)
```

This way: Request -> CORS -> Auth (sets user) -> SizeLimit -> HookMiddleware (has user).

**Correction**: The current order in `main.py` lines 501-513 is:
1. `RequestSizeLimitMiddleware` (added at line 503)
2. `AuthMiddleware` (added at line 504)
3. `CORSMiddleware` (added at line 507)

Execution order: CORS -> Auth -> SizeLimit -> Router

To insert HookMiddleware after auth resolves tenant, add it BEFORE `RequestSizeLimitMiddleware`:

```python
app.add_middleware(HookMiddleware)     # added first, runs LAST (after auth)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(AuthMiddleware)
# CORS added below
```

Execution order: CORS -> Auth -> SizeLimit -> HookMiddleware -> Router

This ensures `request.state.user` is populated before HookMiddleware reads tenant_id.

### 9.5 Lifespan Integration

**File**: `engine/src/agent33/main.py`

The `HookRegistry` must be initialized during lifespan and stored on `app.state`:

```python
# After skill_injector initialization (line 309), add:
from agent33.hooks.registry import HookRegistry
from agent33.hooks.chain import HookChainRunner

hook_registry = HookRegistry()
# Load built-in hooks
hook_registry.discover_builtins()
# Load hook definitions from DB or YAML
# hook_registry.load_from_db(long_term_memory) -- Phase 2
app.state.hook_registry = hook_registry
logger.info("hook_registry_initialized", hook_count=hook_registry.count())
```

---

## 10. File Plan

### 10.1 New Files

| # | File Path | Responsibility | Est. Lines | Est. Tests |
|---|---|---|---|---|
| 1 | `engine/src/agent33/hooks/__init__.py` | Package init, public exports | 20 | 0 |
| 2 | `engine/src/agent33/hooks/models.py` | `HookEventType`, `HookDefinition`, `HookResult`, `HookChainResult`, `HookExecutionLog`, context dataclasses (`HookContext`, `AgentHookContext`, `ToolHookContext`, `WorkflowHookContext`, `RequestHookContext`) | 200 | 15 |
| 3 | `engine/src/agent33/hooks/protocol.py` | `Hook` protocol, `HookAbortError` exception, base hook class | 60 | 5 |
| 4 | `engine/src/agent33/hooks/chain.py` | `HookChainRunner` (sequential), `ConcurrentHookChainRunner` -- chain execution with timeout, failure isolation, abort propagation | 180 | 25 |
| 5 | `engine/src/agent33/hooks/registry.py` | `HookRegistry` -- register/deregister hooks, tenant filtering, event type indexing, handler resolution from `handler_ref`, built-in hook discovery | 200 | 20 |
| 6 | `engine/src/agent33/hooks/middleware.py` | `HookMiddleware` (Starlette `BaseHTTPMiddleware`) -- request lifecycle hooks | 80 | 10 |
| 7 | `engine/src/agent33/hooks/builtins.py` | Built-in hooks: `MetricsHook`, `AuditLogHook`, `PromptInjectionScanHook` | 120 | 10 |
| 8 | `engine/src/agent33/api/routes/hooks.py` | API endpoints for hook CRUD, diagnostics, testing | 250 | 15 |
| 9 | `engine/tests/test_hooks_*.py` | Test files (split across multiple files for clarity) | -- | -- |

**Total new production code**: ~1,110 lines across 8 files
**Total new tests**: ~100 tests across 4-5 test files

### 10.2 Test File Breakdown

| Test File | Tests | Coverage Target |
|---|---|---|
| `tests/test_hooks_models.py` | 15 | Context creation, serialization, event type enum, field defaults |
| `tests/test_hooks_chain.py` | 25 | Sequential execution, priority ordering, timeout, abort, fail-open, fail-closed, concurrent runner |
| `tests/test_hooks_registry.py` | 20 | Register, deregister, tenant filtering, event indexing, handler resolution, discover_builtins |
| `tests/test_hooks_middleware.py` | 10 | Request pre/post hooks via TestClient, tenant propagation, abort handling |
| `tests/test_hooks_builtins.py` | 10 | MetricsHook, AuditLogHook, PromptInjectionScanHook behavior |
| `tests/test_hooks_api.py` | 15 | CRUD endpoints, auth, validation, toggle, test dry-run |
| `tests/test_hooks_integration.py` | 10 | End-to-end: agent invoke with hooks, tool execute with hooks, workflow step with hooks |

### 10.3 Modified Files

| File | Change Description |
|---|---|
| `engine/src/agent33/agents/runtime.py` | Add `hook_registry` parameter, inject pre/post agent hooks in `invoke()` and `invoke_iterative()` |
| `engine/src/agent33/agents/tool_loop.py` | Add `hook_registry` and `tenant_id` parameters, inject pre/post tool hooks in `_execute_tool_calls()` |
| `engine/src/agent33/workflows/executor.py` | Add `hook_registry` and `tenant_id` parameters, inject pre/post workflow step hooks in `_execute_step()` |
| `engine/src/agent33/main.py` | Initialize `HookRegistry` in lifespan, add `HookMiddleware`, wire `hook_registry` to agent/tool/workflow subsystems |
| `engine/src/agent33/api/routes/agents.py` | Pass `hook_registry` from `app.state` to `AgentRuntime` |
| `engine/src/agent33/workflows/actions/invoke_agent.py` | Plumb `hook_registry` through the workflow-agent bridge |

---

## 11. Migration Strategy

### 11.1 Backward Compatibility

All hook injection points are guarded by `if hook_registry is not None:`. When no hook registry is configured (the default), the code paths are unchanged. This ensures:
- Zero runtime cost when hooks are not used
- All existing tests pass without modification
- Gradual adoption: teams can enable hooks per-tenant without affecting others

### 11.2 Relationship to Existing Connector Boundary

The `connectors/middleware.py` system continues to operate independently. It handles connector-level concerns (circuit breakers, governance, retry, timeout, metrics) for external service calls. The hook framework operates at a higher level (agent, tool, workflow, request).

In the future, the connector boundary middleware could be refactored to use the hook framework as its underlying engine, but this is NOT part of H01 scope. The two systems coexist cleanly.

### 11.3 Implementation Order

1. **Wave 1**: `hooks/models.py`, `hooks/protocol.py` -- data model and protocol (no dependencies)
2. **Wave 2**: `hooks/chain.py`, `hooks/registry.py` -- chain runner and registry (depends on Wave 1)
3. **Wave 3**: `hooks/builtins.py`, `hooks/middleware.py` -- built-in hooks and HTTP middleware (depends on Wave 2)
4. **Wave 4**: `api/routes/hooks.py` -- API endpoints (depends on Wave 2)
5. **Wave 5**: Integration into `runtime.py`, `tool_loop.py`, `executor.py`, `main.py` (depends on Wave 2-3)

Each wave can be a separate PR with full test coverage.

---

## 12. Design Decisions & Rationale

### 12.1 Why Middleware Chain over Observer/Callback?

The OpenAI Agents SDK uses an observer/callback model where hooks are fire-and-forget notifications. The Microsoft Agent Framework uses middleware chains with `call_next()` delegation. We chose middleware chains because:

1. **Pre/post interception**: Hooks can modify context before and after the handler runs
2. **Short-circuit capability**: A hook can abort the chain (essential for security hooks)
3. **Result modification**: Post-hooks can transform outputs
4. **Cross-hook state**: The `metadata` dict enables communication between hooks
5. **AGENT-33 precedent**: The connector boundary already uses this pattern successfully

### 12.2 Why Priority Ordering over Registration Order?

Registration order is fragile -- it depends on initialization timing. Priority ordering (0-1000 integer) provides:

1. **Explicit control**: Developers declare intent via priority numbers
2. **Determinism**: Same hooks always run in the same order regardless of registration timing
3. **Insertion flexibility**: A new hook can be slotted between existing hooks
4. **Convention**: Priority 0-99 = system/security, 100-499 = application logic, 500-999 = observability/logging

### 12.3 Why Fail-Open by Default?

Most hooks are non-critical extensions (logging, metrics, enrichment). A logging hook failing should not prevent an agent from executing. Critical hooks (security validation) explicitly set `fail_mode="closed"`.

### 12.4 Why Not Reuse ConnectorMiddleware Directly?

The `ConnectorMiddleware` protocol operates on `ConnectorRequest` objects, which are connector-boundary-specific (connector name, operation, payload). Hook contexts are richer and tier-specific (`AgentHookContext` has agent definition, system prompt; `ToolHookContext` has tool context, etc.). However, the *chaining pattern* from `ConnectorExecutor` is reused in `HookChainRunner`.

### 12.5 Why Separate HookRegistry from ToolRegistry/SkillRegistry?

Hooks are cross-cutting concerns that span all subsystems. Putting them in the tool or skill registry would create circular dependencies. A dedicated `hooks/` package keeps the dependency graph clean:
- `hooks/` depends on: `agents/definition`, `tools/base`, `workflows/executor` (for type hints only)
- `agents/runtime`, `tools/tool_loop`, `workflows/executor` depend on: `hooks/` (for invocation)
- No circular dependencies

### 12.6 Multi-Tenancy Decision: System + Tenant Hooks

System hooks (`tenant_id=""`) always run to ensure baseline security and observability. Tenant hooks run only for their tenant. This dual model matches the existing multi-tenancy pattern where all DB models have `tenant_id` and the `AuthMiddleware` resolves tenant per-request.

---

## Appendix A: Reference Implementations

### A.1 Microsoft Agent Framework 3-Tier Middleware

From `docs/research/hooks-mcp-plugin-architecture-research.md` section 3.2:
- Agent Middleware: intercepts agent run with `AgentContext` (agent, messages, metadata, result, terminate)
- Function Middleware: intercepts tool calls with `FunctionInvocationContext` (function, arguments, metadata, result, terminate)
- Chat Middleware: intercepts LLM calls with `ChatContext` (chat_client, messages, options, metadata, result, terminate)

AGENT-33 adapts this to 4 tiers (agent, tool, workflow, request) since AGENT-33 has a workflow engine that MS Agent Framework lacks.

### A.2 AGENT-33 Connector Boundary (Existing)

From `engine/src/agent33/connectors/`:
- `ConnectorMiddleware` protocol: `async __call__(request, call_next) -> Any`
- `ConnectorExecutor`: chains middleware via reversed iteration with closure binding
- Built-in middleware: governance, circuit breaker, timeout, retry, metrics
- `boundary.py`: factory function for composing the chain from settings

### A.3 OpenAI Agents SDK Lifecycle Hooks

From `docs/research/hooks-mcp-plugin-architecture-research.md` section 3.1:
- `RunHooksBase`: on_agent_start, on_agent_end, on_llm_start, on_llm_end, on_tool_start, on_tool_end, on_handoff
- `AgentHooksBase`: per-agent instance hooks
- Limitation: fire-and-forget, no result modification, no abort capability

---

## Appendix B: Hook Priority Conventions

| Range | Category | Examples |
|---|---|---|
| 0-49 | Security (fail-closed) | Input sanitization, prompt injection scan, PII detection |
| 50-99 | Governance (fail-closed) | Tenant policy enforcement, rate limiting, cost caps |
| 100-199 | Input transformation (fail-open) | Input enrichment, context augmentation, skill injection |
| 200-299 | Execution modification (fail-open) | Model override, parameter defaults, caching |
| 300-399 | Output transformation (fail-open) | Response formatting, output filtering, redaction |
| 400-499 | Application logic (fail-open) | Custom business rules, conditional routing |
| 500-699 | Observability (fail-open) | Metrics collection, trace emission, audit logging |
| 700-899 | Notification (fail-open) | Webhooks, Slack notifications, email alerts |
| 900-999 | Debug/development (fail-open) | Debug logging, request capture, replay recording |

---

## Appendix C: Configuration Settings

New settings to add to `engine/src/agent33/config.py`:

```python
# Hook framework
hooks_enabled: bool = True
hooks_definitions_dir: str = "hook-definitions"
hooks_default_timeout_ms: float = 200.0
hooks_chain_timeout_ms: float = 500.0
hooks_fail_open_default: bool = True
hooks_max_per_event: int = 20  # max hooks per event type
hooks_execution_log_enabled: bool = True
hooks_execution_log_retention_hours: int = 24
```
