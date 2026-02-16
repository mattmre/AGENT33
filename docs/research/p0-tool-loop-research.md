# P0: Iterative Tool-Use Loop -- Research & Architecture

**Date**: 2026-02-15
**Status**: Research complete, ready for implementation
**Priority**: P0 (the single largest capability gap)
**Estimated effort**: 3-4 days
**Depends on**: No blocking dependencies (context window management is complementary, not prerequisite)
**Related**: `docs/research/skillsbench-analysis.md` (sections 4.1, 4.4, 7.4, 10.3)

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Required Changes (Ordered by Dependency)](#2-required-changes-ordered-by-dependency)
3. [Design Decisions](#3-design-decisions)
4. [SkillsBench Alignment](#4-skillsbench-alignment)
5. [Files to Create/Modify](#5-files-to-createmodify)
6. [Test Strategy](#6-test-strategy)
7. [Risk Assessment](#7-risk-assessment)
8. [Open Questions](#8-open-questions)

---

## 1. Current State Analysis

### 1.1 AgentRuntime (`engine/src/agent33/agents/runtime.py`)

The current `AgentRuntime` is strictly single-shot. The `invoke()` method makes exactly ONE LLM call
and returns the parsed result.

**Key observations**:

- `_build_system_prompt()` constructs a multi-section system prompt from `AgentDefinition` fields:
  identity, capabilities, spec capabilities, governance constraints, autonomy level, ownership,
  dependencies, inputs/outputs, execution constraints, safety guardrails, and output format.
- **Skill injection**: If a `SkillInjector` is provided, the system prompt is extended with an L0
  metadata block (compact list of all preloaded skills) and L1 full instructions for each active
  skill.
- **Memory injection**: If `ProgressiveRecall` is provided, the system prompt is extended with up to
  5 prior context items retrieved via `search(query, level="index", top_k=5)`.
- **Messages are always exactly 2**: `[system_message, user_message]`. The user message is the
  JSON-serialized inputs dict.
- **Output parsing**: `_parse_output()` strips markdown code fences, tries `json.loads()`, falls
  back to wrapping raw text in a dict keyed by the first output field name (or `"result"`).
- `AgentResult` is a frozen dataclass with fields: `output` (dict), `raw_response` (str),
  `tokens_used` (int), `model` (str). No iteration metadata.
- **Retry logic**: The existing retry loop (controlled by `AgentConstraints.max_retries`) retries
  failed LLM API calls (network errors, timeouts). It does NOT retry the task itself.
- **Observation**: After a successful LLM call, an `Observation` with `event_type="llm_response"` is
  recorded via `ObservationCapture` if available.
- **Tracing**: If `trace_emitter` is provided, prompt and result spans are emitted.

**What is missing**:

- No tool call parsing from LLM responses.
- No tool execution capability.
- No message accumulation (conversation history).
- No iteration loop.
- No completion detection beyond "parse the first response."

### 1.2 ToolRegistry (`engine/src/agent33/tools/registry.py`)

The tool infrastructure is mature and ready for integration.

- **`validated_execute(name, params, context) -> ToolResult`**: The primary execution method.
  Validates params against JSON Schema (if declared) before calling `tool.execute()`. Returns
  `ToolResult.fail()` if the tool is not found or validation fails.
- **`generate_tool_description(tool, entry)`** (in `tools/schema.py`): Already produces OpenAI-style
  function schemas with `name`, `description`, and `parameters` (JSON Schema). This is exactly the
  format needed for the `tools` parameter in LLM API calls.
- **Tool protocol** (`tools/base.py`): `Tool` requires `name` (str), `description` (str),
  `execute(params, context) -> ToolResult`. `SchemaAwareTool` extends `Tool` with
  `parameters_schema` (dict).
- **`ToolResult`** (`tools/base.py`): Frozen dataclass with `success` (bool), `output` (str),
  `error` (str). Factory methods: `ToolResult.ok(output)`, `ToolResult.fail(error)`.
- **`ToolContext`** (`tools/base.py`): Frozen dataclass with `user_scopes` (list[str]),
  `command_allowlist` (list[str]), `path_allowlist` (list[str]), `domain_allowlist` (list[str]),
  `working_dir` (Path).
- **Schema resolution priority** (`tools/schema.py`): (1) `ToolRegistryEntry.parameters_schema`,
  (2) `SchemaAwareTool.parameters_schema`, (3) `None`.
- **Built-in tools**: shell, file_ops, web_fetch, browser (in `tools/builtins/`).
- **Entry point discovery**: `discover_from_entrypoints(group)` loads tools from setuptools entry
  points.
- **YAML definitions**: `load_definitions(dir)` loads metadata entries from YAML files.

### 1.3 ToolGovernance (`engine/src/agent33/tools/governance.py`)

Governance is implemented but NOT currently wired into `AgentRuntime` or the invoke route.

- **`pre_execute_check(tool_name, params, context, autonomy_level) -> bool`**: The gate that must
  pass before any tool executes. Checks performed in order:
  1. Rate limiting (per-subject sliding window, configurable per_minute and burst).
  2. Autonomy level enforcement (read-only blocks write tools, supervised logs destructive ops).
  3. Scope check (user must have `tools:execute` or a tool-specific scope).
  4. Shell command validation (multi-segment: subshell patterns blocked, each segment's executable
     checked against allowlist).
  5. Path allowlist enforcement for file_ops.
  6. Domain allowlist enforcement for web_fetch.
- **`log_execution(tool_name, params, result)`**: Structured audit log entry with tool, params,
  success, error, timestamp.
- **`_RateLimiter`**: Sliding-window rate limiter with burst detection (per-second and per-minute).
- **Integration point**: The tool loop must call `pre_execute_check()` before every tool execution
  and `log_execution()` after every tool execution.

### 1.4 LLM Provider Interface (`engine/src/agent33/llm/base.py`)

The LLM layer currently has no awareness of tool calling. This is the most critical gap to address.

- **`LLMProvider` protocol**:
  ```python
  async def complete(
      self,
      messages: list[ChatMessage],
      *,
      model: str,
      temperature: float = 0.7,
      max_tokens: int | None = None,
  ) -> LLMResponse
  ```
  **CRITICAL GAP**: No `tools` parameter. No way to pass function definitions to the LLM.

- **`ChatMessage`** (frozen dataclass):
  - Fields: `role` (str), `content` (str).
  - **Missing**: `tool_calls` (list of tool call objects for assistant messages), `tool_call_id`
    (str for tool response messages), `name` (str for tool identification).

- **`LLMResponse`** (frozen dataclass):
  - Fields: `content` (str), `model` (str), `prompt_tokens` (int), `completion_tokens` (int).
  - Computed: `total_tokens` (property).
  - **Missing**: `tool_calls` (list of tool calls requested by the LLM), `finish_reason` (str to
    distinguish "stop" vs "tool_calls").

- **Concrete providers**:
  - `OllamaProvider` (`llm/ollama.py`): Serializes messages as `[{"role": ..., "content": ...}]`.
    Ollama's `/api/chat` endpoint supports a `tools` parameter (since Ollama 0.2+), but the
    provider does not pass it. Response parsing extracts only `message.content`, ignoring any
    `message.tool_calls`.
  - `OpenAIProvider` (`llm/openai.py`): Serializes messages as `[{"role": ..., "content": ...}]`.
    The OpenAI API natively supports `tools` and `tool_choice` parameters, but the provider does
    not pass them. Response parsing extracts only `choices[0].message.content`, ignoring
    `choices[0].message.tool_calls` and `choices[0].finish_reason`.

- **`ModelRouter`** (`llm/router.py`): Pure pass-through to the resolved provider's `complete()`.
  Must be updated to forward the `tools` parameter.

### 1.5 SkillInjector (`engine/src/agent33/skills/injection.py`)

The skill system is already integrated with `AgentRuntime` and provides the foundation for
tool-context narrowing during tool execution.

- **`build_skill_metadata_block(skill_names) -> str`**: L0 disclosure. Produces a compact
  `# Available Skills` section listing name and description for each skill.
- **`build_skill_instructions_block(skill_name) -> str`**: L1 disclosure. Produces a full section
  with governance info (allowed/blocked tools, autonomy level, approval requirements) and complete
  skill instructions.
- **`resolve_tool_context(active_skills, base_context) -> ToolContext`**: Narrows tool access by
  intersecting the agent's base allowlist with each skill's `allowed_tools` and removing
  `disallowed_tools`. Returns a new `ToolContext` with the merged restrictions.
- **Integration point for tool loop**: Before executing a tool, call `resolve_tool_context()` to
  get the narrowed `ToolContext` that reflects the active skills' governance constraints. This
  ensures skill-level tool restrictions are enforced even within the iterative loop.

### 1.6 Autonomy Enforcement (`engine/src/agent33/autonomy/enforcement.py`)

The autonomy system provides budget-based enforcement that the tool loop should integrate with.

- **`RuntimeEnforcer`**: Initialized with an `AutonomyBudget`. Tracks consumption via
  `EnforcementContext`.
- **Enforcement points relevant to tool loop**:
  - `EF-01 check_file_read(path)`: Before file read tools.
  - `EF-02 check_file_write(path, lines)`: Before file write tools.
  - `EF-03 check_command(command)`: Before shell tool.
  - `EF-04 check_network(domain)`: Before web_fetch/browser tools.
  - `EF-05 record_iteration()`: Once per loop iteration.
  - `EF-06 check_duration()`: Elapsed time check.
  - `EF-07/EF-08`: Files modified and lines changed limits (checked within EF-02).
- **`EnforcementResult` enum**: `ALLOWED`, `BLOCKED`, `WARNED`, `ESCALATED`.
- **Resource limits** (from `AutonomyBudget.limits`): `max_iterations=100`,
  `max_duration_minutes=60`, `max_tool_calls=200`, `max_files_modified=50`,
  `max_lines_changed=5000`.
- **Stop conditions**: `evaluate_stop_conditions()` checks all configured stop conditions.
- **NOT currently wired into AgentRuntime**: Must be passed as an optional dependency and checked at
  each iteration and before each tool execution.

### 1.7 Agent Invoke Route (`engine/src/agent33/api/routes/agents.py`)

The HTTP endpoint for agent invocation.

- **`POST /v1/agents/{name}/invoke`**: Requires `agents:invoke` scope. Scans inputs for prompt
  injection. Pulls `skill_injector` and `progressive_recall` from `app.state`. Creates
  `AgentRuntime` and calls `invoke()`.
- **NOT wired**: `ToolRegistry`, `ToolGovernance`, `AutonomyService`, `TraceCollector`,
  `ObservationCapture`.
- **Module-level `_model_router` singleton**: Inconsistency with the `app.state.model_router`
  created during lifespan. The route creates its own `ModelRouter` at import time rather than using
  the one from lifespan. This should be fixed as part of the tool loop wiring.
- **`InvokeRequest`**: `inputs` (dict), `model` (str|None), `temperature` (float).
- **`InvokeResponse`**: `agent` (str), `output` (dict), `tokens_used` (int), `model` (str). No
  iteration metadata.

### 1.8 Observation & Tracing

Both subsystems are ready for tool loop integration.

- **`ObservationCapture`** (`memory/observation.py`):
  - `record(obs: Observation) -> str`: Records an observation, storing with embedding if long-term
    memory and embedding provider are available. Private-tagged observations are buffered but not
    persisted.
  - `Observation` dataclass: `id`, `session_id`, `agent_name`, `event_type`, `content`, `metadata`,
    `tags`, `timestamp`.
  - Relevant `event_type` values: `"tool_call"`, `"llm_response"`, `"decision"`, `"error"`.
  - **Tool loop integration**: Record an observation for each tool call (event_type=tool_call) and
    each LLM response (event_type=llm_response).

- **`TraceCollector`** (`observability/trace_collector.py`):
  - `start_trace(task_id, session_id, ...) -> TraceRecord`: Creates a trace in RUNNING state.
  - `add_step(trace_id, step_id) -> TraceStep`: Adds a step (maps to one loop iteration).
  - `add_action(trace_id, step_id, action_id, tool, ...) -> TraceAction`: Adds a tool action.
  - `complete_trace(trace_id, status, ...) -> TraceRecord`: Marks trace as complete.
  - `record_failure(trace_id, message, category, severity, ...) -> FailureRecord`: Records a
    failure with taxonomy classification.
  - **Tool loop integration**: Start a trace when the loop begins. Add a step per iteration. Add an
    action per tool call. Complete the trace when the loop ends (with success or failure status).

### 1.9 Workflow Bridge (`engine/src/agent33/workflows/actions/invoke_agent.py`)

The bridge between the workflow engine and `AgentRuntime`.

- **`_register_agent_runtime_bridge()`** in `main.py`: Creates a `__default__` agent handler that
  looks up the agent definition from the registry, creates an `AgentRuntime` with `skill_injector`
  and `progressive_recall`, and calls `invoke()`.
- **Missing from bridge**: `ToolRegistry`, `ToolGovernance`. When the tool loop is implemented, the
  bridge should pass these dependencies and call `invoke_iterative()` instead of `invoke()`.
- **`set_definition_registry(registry)`**: Called during lifespan to wire the AgentRegistry.
- **`execute(agent, inputs, dry_run) -> dict`**: Called by the workflow step executor. Looks up the
  agent handler and calls it with inputs.

---

## 2. Required Changes (Ordered by Dependency)

### Layer 1: LLM Protocol Extensions

These changes extend the base LLM types to support tool calling. All downstream layers depend on
these types.

**Change 1: Add `ToolCall` model to `llm/base.py`**

```python
@dataclasses.dataclass(frozen=True, slots=True)
class ToolCallFunction:
    """Function details within a tool call."""
    name: str
    arguments: str  # JSON string of arguments

@dataclasses.dataclass(frozen=True, slots=True)
class ToolCall:
    """A tool call requested by the LLM."""
    id: str
    function: ToolCallFunction
```

**Change 2: Extend `ChatMessage` with optional tool-calling fields**

```python
@dataclasses.dataclass(frozen=True, slots=True)
class ChatMessage:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_calls: list[ToolCall] | None = None      # For assistant messages with tool calls
    tool_call_id: str | None = None                # For tool response messages
    name: str | None = None                        # Tool name for tool response messages
```

**Change 3: Extend `LLMResponse` with tool-calling fields**

```python
@dataclasses.dataclass(frozen=True, slots=True)
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    tool_calls: list[ToolCall] | None = None       # Tool calls from the LLM
    finish_reason: str = "stop"                     # "stop" | "tool_calls" | "length"

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)
```

**Change 4: Add `tools` parameter to `LLMProvider.complete()` and `ModelRouter.complete()`**

```python
# In LLMProvider protocol:
async def complete(
    self,
    messages: list[ChatMessage],
    *,
    model: str,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    tools: list[dict[str, Any]] | None = None,     # NEW: OpenAI-style tool definitions
) -> LLMResponse: ...

# In ModelRouter.complete():
async def complete(
    self,
    messages: list[ChatMessage],
    *,
    model: str,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    tools: list[dict[str, Any]] | None = None,     # NEW: pass through to provider
) -> LLMResponse: ...
```

**Change 5: Update `OllamaProvider.complete()` to pass `tools` and parse `tool_calls`**

- Add `tools` to the payload if provided (Ollama `/api/chat` supports tools since v0.2).
- Parse `data["message"]["tool_calls"]` if present.
- Set `finish_reason` based on whether tool_calls are present.

**Change 6: Update `OpenAIProvider.complete()` to pass `tools` and parse `tool_calls`**

- Add `tools` to the payload if provided (wrap each in `{"type": "function", "function": ...}`).
- Parse `choices[0]["message"]["tool_calls"]` if present.
- Parse `choices[0]["finish_reason"]`.
- Serialize tool messages with `tool_call_id` in the messages payload.

### Layer 2: Tool Loop Core (NEW: `agents/tool_loop.py`)

This is the heart of the implementation -- a new module containing the iterative loop logic.

**Change 7: `ToolLoopConfig` dataclass**

```python
@dataclasses.dataclass(frozen=True, slots=True)
class ToolLoopConfig:
    """Configuration for the iterative tool-use loop."""
    max_iterations: int = 20                          # Hard cap on loop iterations
    max_tool_calls_per_iteration: int = 5             # Max parallel tool calls per LLM response
    enable_double_confirmation: bool = True            # Ask "are you sure?" on completion
    error_threshold: int = 3                           # Consecutive errors before stopping
    tool_call_timeout_seconds: float = 60.0            # Per-tool execution timeout
```

**Change 8: `ToolLoopState` mutable tracking class**

```python
class ToolLoopState:
    """Mutable state tracking for a single tool loop execution."""
    iterations: int = 0
    total_tokens: int = 0
    tool_calls_made: int = 0
    tools_used: set[str]                               # Unique tool names used
    messages: list[ChatMessage]                        # Full conversation history
    consecutive_errors: int = 0
    termination_reason: str = ""
```

**Change 9: `ToolLoop` class with `run()` method**

The core loop algorithm:

```
1. Initialize messages with [system, user]
2. Generate tool definitions from ToolRegistry via generate_tool_description()
3. LOOP:
   a. Call LLM with messages + tool definitions
   b. Record LLM response observation
   c. Append assistant message to history
   d. IF response has tool_calls:
      - For each tool_call:
        i.   Check ToolGovernance.pre_execute_check()
        ii.  Check RuntimeEnforcer (if budget exists)
        iii. Parse arguments from JSON string
        iv.  Execute via ToolRegistry.validated_execute()
        v.   Log via ToolGovernance.log_execution()
        vi.  Record tool_call observation
        vii. Record TraceCollector action
        viii. Append tool result message to history
      - Increment iteration, continue loop
   e. ELSE (text-only response, no tool calls):
      - IF double_confirmation enabled AND this is the first text-only response:
        - Append confirmation prompt: "Please confirm: is the task fully complete?"
        - Continue loop (LLM will respond with either more tool calls or confirmation)
      - ELSE:
        - Parse final output
        - Return result
   f. Check termination conditions:
      - max_iterations reached
      - consecutive_errors >= error_threshold
      - autonomy budget stop condition triggered
      - duration exceeded
4. Return ToolLoopResult with final output, iteration count, tools used, token totals
```

**Change 10: `ToolLoopResult` dataclass**

```python
@dataclasses.dataclass(frozen=True, slots=True)
class ToolLoopResult:
    """Result of an iterative tool loop execution."""
    output: dict[str, Any]
    raw_response: str
    tokens_used: int
    model: str
    iterations: int
    tool_calls_made: int
    tools_used: list[str]
    termination_reason: str                            # "completed", "max_iterations", "error",
                                                       # "budget_exceeded", "duration_exceeded"
```

### Layer 3: Runtime Integration

**Change 11: New `AgentRuntime.invoke_iterative()` method**

Wraps `ToolLoop` with the existing prompt construction, skill injection, and memory logic:

```python
async def invoke_iterative(
    self,
    inputs: dict[str, Any],
    tool_loop_config: ToolLoopConfig | None = None,
) -> ToolLoopResult:
    """Run the agent in an iterative tool-use loop."""
    # 1. Build system prompt (existing _build_system_prompt + skill + memory injection)
    # 2. Validate required inputs (existing logic)
    # 3. Create ToolLoop with all dependencies
    # 4. Run the loop
    # 5. Record final observation
    # 6. Emit trace spans
    # 7. Return ToolLoopResult
```

**Change 12: Extended `AgentRuntime.__init__` to accept new dependencies**

```python
def __init__(
    self,
    definition: AgentDefinition,
    router: ModelRouter,
    model: str | None = None,
    temperature: float = 0.7,
    observation_capture: Any | None = None,
    trace_emitter: Any | None = None,
    session_id: str = "",
    progressive_recall: Any | None = None,
    skill_injector: Any | None = None,
    active_skills: list[str] | None = None,
    # NEW dependencies for tool loop:
    tool_registry: ToolRegistry | None = None,
    tool_governance: ToolGovernance | None = None,
    runtime_enforcer: RuntimeEnforcer | None = None,
    trace_collector: TraceCollector | None = None,
) -> None:
```

**Change 13: Preserve existing `invoke()` as-is**

The existing `invoke()` method remains untouched for backward compatibility. Callers that do not need
tool use continue to work without changes. `invoke_iterative()` is an additive method.

### Layer 4: Wiring

**Change 14: Initialize ToolRegistry + builtins in `main.py` lifespan**

```python
# -- Tool registry + governance ------------------------------------------
from agent33.tools.registry import ToolRegistry
from agent33.tools.governance import ToolGovernance

tool_registry = ToolRegistry()
# Register built-in tools
from agent33.tools.builtins.shell import ShellTool
from agent33.tools.builtins.file_ops import FileOpsTool
from agent33.tools.builtins.web_fetch import WebFetchTool
tool_registry.register(ShellTool())
tool_registry.register(FileOpsTool())
tool_registry.register(WebFetchTool())
# Discover additional tools from entry points
tool_registry.discover_from_entrypoints()
app.state.tool_registry = tool_registry

tool_governance = ToolGovernance()
app.state.tool_governance = tool_governance
```

**Change 15: Update agent invoke route to pull new dependencies**

```python
# In invoke_agent():
tool_registry = getattr(request.app.state, "tool_registry", None)
tool_governance = getattr(request.app.state, "tool_governance", None)
observation_capture = getattr(request.app.state, "observation_capture", None)
trace_collector = getattr(request.app.state, "trace_collector", None)

runtime = AgentRuntime(
    definition=definition,
    router=_model_router,  # TODO: use app.state.model_router instead
    model=body.model,
    temperature=body.temperature,
    skill_injector=skill_injector,
    progressive_recall=progressive_recall,
    tool_registry=tool_registry,
    tool_governance=tool_governance,
    observation_capture=observation_capture,
    trace_collector=trace_collector,
)
```

**Change 16: Add iterative invoke endpoint**

```python
@router.post("/{name}/invoke-iterative", dependencies=[require_scope("agents:invoke")])
async def invoke_agent_iterative(
    name: str,
    body: InvokeIterativeRequest,  # extends InvokeRequest with max_iterations, etc.
    request: Request,
    registry: AgentRegistry = Depends(get_registry),
) -> InvokeIterativeResponse:
    """Invoke a registered agent with iterative tool-use loop."""
    ...
```

**Change 17: Update workflow bridge to pass tool dependencies**

```python
def _register_agent_runtime_bridge(
    model_router: ModelRouter,
    register_fn: Callable[..., object],
    registry: Any = None,
    skill_injector: Any = None,
    progressive_recall: Any = None,
    tool_registry: Any = None,          # NEW
    tool_governance: Any = None,        # NEW
) -> None:
    ...
    runtime = AgentRuntime(
        definition=definition,
        router=model_router,
        model=model,
        skill_injector=skill_injector,
        progressive_recall=progressive_recall,
        tool_registry=tool_registry,        # NEW
        tool_governance=tool_governance,    # NEW
    )
    result = await runtime.invoke_iterative(inputs)  # Use iterative by default
    ...
```

### Layer 5: Double-Confirmation

**Change 18: Confirmation logic within `ToolLoop.run()`**

When the LLM returns a text-only response (no tool_calls), the loop does not immediately accept it
as the final answer. Instead:

1. On the first text-only response: append a follow-up message asking the LLM to confirm completion.
   The prompt should be specific:
   ```
   Before I accept your answer, please verify:
   1. Have you completed all parts of the task?
   2. Have you verified your results (e.g., by reading output files)?
   If the task is not fully complete, continue working. If it is complete, restate your final answer.
   ```
2. If the LLM responds with more tool calls, the loop continues normally.
3. If the LLM responds with another text-only message (confirming completion), the loop terminates
   and returns the confirmed result.

This prevents premature exit when the LLM generates a plan or partial response without actually
executing it via tools.

**Configurable**: `ToolLoopConfig.enable_double_confirmation` (default `True`). Can be disabled for
simple tasks where single-shot completion is acceptable.

---

## 3. Design Decisions

| Decision | Chosen Approach | Rationale |
|----------|----------------|-----------|
| Preserve `invoke()`, add `invoke_iterative()` | Additive, not replacement | Backward compatibility. Existing callers (tests, routes, workflow bridge) continue to work unchanged. Migration can be gradual. |
| Hard cap at 20 iterations (default) | `ToolLoopConfig.max_iterations = 20` | Prevents runaway loops even without an autonomy budget. SkillsBench tasks rarely need more than 15 iterations. The autonomy system's `max_iterations=100` serves as an absolute backstop. |
| Tool definitions from ToolRegistry | `generate_tool_description()` per registered tool | Leverages existing infrastructure. Tool descriptions are generated in OpenAI function-calling format. No duplication of tool metadata. |
| Governance check before every tool execution | `ToolGovernance.pre_execute_check()` | Reuses existing security infrastructure. Rate limiting, autonomy levels, scope checks, command validation, path/domain allowlists are all enforced consistently. |
| Observation per tool call AND per LLM response | `ObservationCapture.record()` with distinct event types | Full audit trail via existing system. Tool calls use `event_type="tool_call"`, LLM responses use `event_type="llm_response"`. Enables post-hoc analysis and session replay. |
| Trace per loop execution, step per iteration | `TraceCollector.start_trace()` / `add_step()` / `add_action()` | Maps naturally to the trace model. One trace per `invoke_iterative()` call. Steps correspond to loop iterations. Actions correspond to individual tool calls. |
| Graceful fallback if no tools available | Return single-shot result from `invoke()` | Provider compatibility. If `ToolRegistry` has no tools, or the provider does not support function calling, the system degrades gracefully to single-shot behavior. |
| `ToolLoopResult` as separate type from `AgentResult` | New dataclass with iteration metadata | `AgentResult` is frozen and used extensively. Adding optional fields would break its contract. `ToolLoopResult` extends the concept with `iterations`, `tool_calls_made`, `tools_used`, `termination_reason`. |
| Double-confirmation on by default | `ToolLoopConfig.enable_double_confirmation = True` | SkillsBench analysis shows this reduces false-positive completions significantly. Can be disabled for known-simple tasks. |
| JSON tool call format (not XML) | Parse `tool_calls` from structured LLM response | Both Ollama and OpenAI use JSON tool_calls natively. XML parsing adds complexity without provider support. If needed later, a fallback XML parser can be added as P2 work. |
| ToolLoop as a separate module from AgentRuntime | `agents/tool_loop.py` | Follows the SkillsBench analysis recommendation (section 6.1): avoid "God Runtime" by decomposing into composable modules. ToolLoop can be tested independently. |
| Autonomy enforcement is optional | `RuntimeEnforcer` passed as `None` when no budget exists | Most agent invocations (direct API calls, simple workflow steps) will not have an autonomy budget. The tool loop should work without one. When a budget is provided, it adds resource tracking and stop conditions. |

---

## 4. SkillsBench Alignment

### 4.1 Terminus-2 Tool Loop Pattern

From the SkillsBench analysis (`docs/research/skillsbench-analysis.md`, section 4.1), the Terminus-2
agent implements its tool loop in `agents/terminus2/tool_loop.py`. The core pattern is:

```
while not done:
    response = llm.complete(messages, tools=tool_definitions)
    if response.has_tool_calls:
        for call in response.tool_calls:
            result = execute_tool(call)
            messages.append(tool_result(result))
    elif is_task_complete(response):
        if double_confirm(response):
            done = True
    else:
        messages.append(assistant_message(response))
```

AGENT-33's implementation follows this pattern exactly, with additional features:

- **Governance enforcement** at every tool call (Terminus-2 relies on Docker container isolation).
- **Autonomy budget tracking** (Terminus-2 has no resource accounting).
- **Structured observation capture** (Terminus-2 has no observation system).
- **Trace pipeline integration** (Terminus-2 has no tracing).
- **Multi-tenant context** (Terminus-2 is single-tenant).

### 4.2 Expected Performance Impact

From the SkillsBench analysis (section 10.3):

| Enhancement | Baseline (current) | After Enhancement | Expected Lift |
|------------|-------------------|-------------------|---------------|
| Iterative tool-use loop | 5-10% (single LLM call) | 40-60% (agents can interact with environment) | +35-50% |
| Double-confirmation | 40-60% (after tool loop) | 43-63% (fewer false completions) | +3% |

The tool loop is the single highest-impact change. Without it, AGENT-33 agents cannot complete any
multi-step SkillsBench task because they make a single LLM call and return. With it, agents can
execute commands, read/write files, observe results, and iterate.

### 4.3 Complementary Features (Separate PRs)

The tool loop is designed to work with future enhancements that are NOT part of this PR:

- **Context window management** (P2): When the message history grows too large, a
  `ContextWindowManager` will truncate or summarize older messages. The tool loop's `messages` list
  is the input to this system. Until implemented, the loop will hit the LLM's context limit on very
  long tasks, which is acceptable for the initial release.
- **4-stage skill matching** (P1): Better skill selection produces better tool context. The tool loop
  consumes whatever skills are injected; it does not depend on the matching strategy.
- **CTRF reporting** (P5): Test result reporting format. Orthogonal to the loop itself.

---

## 5. Files to Create/Modify

### New Files

| File | Description |
|------|-------------|
| `engine/src/agent33/agents/tool_loop.py` | Core loop logic: `ToolLoopConfig`, `ToolLoopState`, `ToolLoop`, `ToolLoopResult` |
| `engine/tests/test_tool_loop.py` | Tests for tool loop: termination conditions, tool execution, error handling, double-confirmation, budget enforcement |

### Modified Files

| File | Changes |
|------|---------|
| `engine/src/agent33/llm/base.py` | Add `ToolCallFunction`, `ToolCall` dataclasses. Add `tool_calls`, `tool_call_id`, `name` to `ChatMessage`. Add `tool_calls`, `finish_reason`, `has_tool_calls` to `LLMResponse`. Add `tools` parameter to `LLMProvider.complete()`. |
| `engine/src/agent33/llm/router.py` | Add `tools` parameter to `ModelRouter.complete()`, pass through to provider. |
| `engine/src/agent33/llm/ollama.py` | Add `tools` parameter to `OllamaProvider.complete()`. Include `tools` in payload if provided. Parse `message.tool_calls` from response. Set `finish_reason`. |
| `engine/src/agent33/llm/openai.py` | Add `tools` parameter to `OpenAIProvider.complete()`. Include `tools` in payload (wrapped in `{"type": "function", "function": ...}`). Parse `choices[0].message.tool_calls`. Parse `finish_reason`. Serialize tool messages with `tool_call_id`. |
| `engine/src/agent33/agents/runtime.py` | Add `tool_registry`, `tool_governance`, `runtime_enforcer`, `trace_collector` to `__init__`. Add `invoke_iterative()` method. Keep existing `invoke()` unchanged. |
| `engine/src/agent33/api/routes/agents.py` | Pull `tool_registry`, `tool_governance`, `observation_capture` from `app.state`. Pass to `AgentRuntime`. Add `POST /{name}/invoke-iterative` endpoint. Add `InvokeIterativeRequest` and `InvokeIterativeResponse` models. |
| `engine/src/agent33/main.py` | Initialize `ToolRegistry` with built-in tools. Initialize `ToolGovernance`. Store on `app.state`. Pass to `_register_agent_runtime_bridge()`. |
| `engine/src/agent33/workflows/actions/invoke_agent.py` | Accept `tool_registry` and `tool_governance` parameters. Use `invoke_iterative()` when tools are available. |

### Files NOT Modified (Confirmed Unchanged)

| File | Reason |
|------|--------|
| `engine/src/agent33/tools/registry.py` | Already has `validated_execute()` and all needed APIs. |
| `engine/src/agent33/tools/governance.py` | Already has `pre_execute_check()` and `log_execution()`. |
| `engine/src/agent33/tools/base.py` | `Tool`, `SchemaAwareTool`, `ToolContext`, `ToolResult` are complete. |
| `engine/src/agent33/tools/schema.py` | `generate_tool_description()` already produces the right format. |
| `engine/src/agent33/skills/injection.py` | Already has `resolve_tool_context()`. |
| `engine/src/agent33/autonomy/enforcement.py` | Already has all EF-01..EF-08 checks. |
| `engine/src/agent33/memory/observation.py` | Already has `record()` with event_type support. |
| `engine/src/agent33/observability/trace_collector.py` | Already has full trace lifecycle API. |

---

## 6. Test Strategy

### 6.1 Unit Tests for `ToolLoop` (`test_tool_loop.py`)

These tests mock the `ModelRouter`, `ToolRegistry`, and `ToolGovernance` to test loop behavior in
isolation.

**Termination conditions**:

1. LLM returns text-only (no tool_calls) on first response -> single iteration, result returned.
2. LLM returns tool_calls, then text-only -> two iterations, result returned after second.
3. LLM returns tool_calls repeatedly until `max_iterations` -> terminates with
   `termination_reason="max_iterations"`.
4. Tool execution fails `error_threshold` consecutive times -> terminates with
   `termination_reason="error"`.
5. Autonomy budget `record_iteration()` returns BLOCKED -> terminates with
   `termination_reason="budget_exceeded"`.

**Tool execution**:

6. Tool call with valid params -> `validated_execute()` called, result appended as tool message.
7. Tool call with invalid params -> `validated_execute()` returns fail, error appended as tool
   message, loop continues.
8. `ToolGovernance.pre_execute_check()` returns False -> tool skipped, message appended explaining
   denial, loop continues.
9. Multiple tool_calls in one response -> all executed in sequence, all results appended.
10. Tool not found in registry -> fail result returned, loop continues.

**Double-confirmation**:

11. First text-only response triggers confirmation prompt -> confirmation message appended to
    history.
12. LLM responds to confirmation with tool_calls -> loop continues normally.
13. LLM responds to confirmation with text -> loop terminates, result returned.
14. `enable_double_confirmation=False` -> first text-only response is immediately accepted.

**Message history**:

15. Messages accumulate correctly: system, user, assistant (with tool_calls), tool results,
    assistant, ...
16. Tool result messages have `role="tool"`, `tool_call_id` set, and `name` set to tool name.

**Integration with subsystems**:

17. `ObservationCapture.record()` called for each LLM response and each tool call.
18. `TraceCollector.add_step()` called for each iteration, `add_action()` for each tool call.
19. `RuntimeEnforcer.check_command()` / `check_file_read()` / etc. called for relevant tool types.

**Edge cases**:

20. Empty tool_calls list in response -> treated as text-only response.
21. Tool call with malformed JSON arguments -> parse error handled gracefully, error message appended
    as tool result.
22. LLM response with both content and tool_calls -> tool_calls take priority, content preserved in
    message.

### 6.2 Unit Tests for LLM Protocol Extensions

23. `ChatMessage` with tool_calls serializes correctly for Ollama format.
24. `ChatMessage` with tool_calls serializes correctly for OpenAI format.
25. `ChatMessage` with `role="tool"` includes `tool_call_id` and `name`.
26. `LLMResponse.has_tool_calls` returns True when tool_calls is non-empty.
27. `LLMResponse.has_tool_calls` returns False when tool_calls is None or empty.
28. `OllamaProvider` passes tools in payload when provided.
29. `OpenAIProvider` wraps tools in `{"type": "function", "function": ...}` format.

### 6.3 Integration Tests

30. `AgentRuntime.invoke_iterative()` with mock router and real ToolRegistry (shell tool) executes a
    multi-step task.
31. `AgentRuntime.invoke()` continues to work unchanged (regression test).
32. Agent invoke route returns correct response shape for iterative invocation.
33. Workflow bridge uses iterative invocation when tools are available.

### 6.4 Estimated Test Count

Target: 35-45 tests across `test_tool_loop.py` and extensions to existing test files.

---

## 7. Risk Assessment

### 7.1 Breaking Changes

**Risk: LLM protocol changes break existing providers or tests.**

The `ChatMessage` and `LLMResponse` changes add optional fields with defaults. Existing code that
creates these objects with positional or keyword arguments for `role` and `content` will continue to
work. The `tools` parameter in `complete()` defaults to `None`. All existing tests should pass
without modification.

**Mitigation**: Run the full test suite (`python -m pytest tests/ -q`) after each Layer 1 change to
verify no regressions.

### 7.2 Provider Compatibility

**Risk: Some LLM providers do not support function calling.**

Not all models support the `tools` parameter. Older Ollama models, some open-source models via
OpenAI-compatible APIs, and certain providers may ignore or reject the `tools` field.

**Mitigation**: The tool loop gracefully degrades. If the LLM never returns `tool_calls`, the loop
behaves as single-shot (text-only response on first iteration). The `tools` parameter is only
included in the payload if it is not `None`, so providers that reject it will not receive it when
tools are unavailable.

### 7.3 Runaway Loops

**Risk: A misconfigured or adversarial prompt causes infinite looping.**

**Mitigation**: Three independent safeguards:
1. `ToolLoopConfig.max_iterations` (default 20) -- hard cap on the tool loop itself.
2. `AutonomyBudget.limits.max_iterations` (default 100) -- autonomy system backstop.
3. `ToolLoopConfig.error_threshold` (default 3) -- stops on consecutive failures.

### 7.4 Context Window Overflow

**Risk: Long-running tasks accumulate messages that exceed the model's context window.**

**Mitigation for initial release**: The `max_iterations` cap limits message accumulation. For
typical tool calls (shell commands, file reads), 20 iterations produce approximately 30-50 messages,
which fits within most model context windows (8K-128K tokens). For longer tasks, context window
management (P2) will add message truncation and summarization.

### 7.5 Security

**Risk: Tool execution bypasses governance checks.**

**Mitigation**: The tool loop explicitly calls `ToolGovernance.pre_execute_check()` before every
tool execution. The `SkillInjector.resolve_tool_context()` narrows the `ToolContext` based on
active skills. The `RuntimeEnforcer` checks file paths, commands, and network domains against the
autonomy budget. All three layers are independent and composable.

---

## 8. Open Questions

### 8.1 Should the workflow bridge default to `invoke_iterative()` or `invoke()`?

**Option A**: Default to `invoke_iterative()` when `tool_registry` is available on `app.state`.
This means all workflow-invoked agents automatically get tool-use capability.

**Option B**: Default to `invoke()` and require explicit opt-in per workflow step (e.g., a
`use_tools: true` flag in the workflow definition).

**Recommendation**: Option A, since the iterative loop degrades to single-shot when the LLM returns
no tool calls. There is no downside to having tools available.

### 8.2 Should the module-level `_model_router` in `agents.py` be replaced?

The agent routes file creates its own `ModelRouter` at import time (`_model_router = ModelRouter()`),
which is separate from the `app.state.model_router` created during lifespan. This means the route
uses a different router instance than the rest of the system.

**Recommendation**: Fix this inconsistency as part of the tool loop wiring. The route should pull
the router from `app.state` via dependency injection, matching the pattern used for
`agent_registry`, `skill_injector`, and `progressive_recall`.

### 8.3 Parallel tool execution?

Some LLM responses contain multiple tool_calls. Should they be executed in parallel or sequentially?

**Recommendation**: Sequential for the initial implementation. Parallel execution introduces
ordering dependencies (one tool's output may affect another's input) and complicates error handling.
The `max_tool_calls_per_iteration` config provides a soft limit. Parallel execution can be added
later as an optimization.

### 8.4 Tool call format: native function calling vs. text-based parsing?

Should the loop rely exclusively on the LLM's native function calling (via the `tools` API
parameter), or also parse tool calls from text output (e.g., JSON blocks or XML tags)?

**Recommendation**: Native function calling only for the initial implementation. Both Ollama and
OpenAI support it natively. Text-based parsing adds complexity and is error-prone. If a model does
not support function calling, the loop degrades to single-shot. Text-based fallback can be added as
P2 work.

### 8.5 How should `ToolLoopResult` relate to `AgentResult`?

`AgentResult` is a frozen dataclass used throughout the codebase. `ToolLoopResult` has additional
fields. Should `ToolLoopResult` extend `AgentResult`?

**Recommendation**: `ToolLoopResult` is a separate type. It can be converted to `AgentResult` via a
helper method for callers that need the simpler type. Inheritance of frozen dataclasses is fragile
in Python and not recommended.

---

## Appendix A: Message Format Examples

### A.1 OpenAI Function Calling Format (used by both Ollama and OpenAI)

**Tool definition (sent in API request)**:

```json
{
  "type": "function",
  "function": {
    "name": "shell",
    "description": "Run a shell command and return its output",
    "parameters": {
      "type": "object",
      "properties": {
        "command": {"type": "string", "description": "Command to execute"}
      },
      "required": ["command"]
    }
  }
}
```

**Assistant message with tool call (from LLM response)**:

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "shell",
        "arguments": "{\"command\": \"ls -la /workspace\"}"
      }
    }
  ]
}
```

**Tool result message (sent back to LLM)**:

```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "name": "shell",
  "content": "total 24\ndrwxr-xr-x 3 user user 4096 Feb 15 10:00 .\n..."
}
```

### A.2 Full Conversation Example (3-iteration loop)

```
Iteration 1:
  -> LLM receives: [system, user] with tools=[shell, file_ops, web_fetch]
  <- LLM responds: tool_calls=[shell("ls /workspace")]
  -> Execute shell("ls /workspace") -> "file1.py file2.py"
  -> Append assistant message + tool result

Iteration 2:
  -> LLM receives: [system, user, assistant+tool_calls, tool_result] with tools=...
  <- LLM responds: tool_calls=[file_ops("read", "file1.py")]
  -> Execute file_ops("read", "file1.py") -> "def main(): ..."
  -> Append assistant message + tool result

Iteration 3:
  -> LLM receives: [system, user, asst, tool, asst, tool] with tools=...
  <- LLM responds: "The file contains a main function that..." (no tool_calls)
  -> Double-confirmation: "Please confirm: is the task fully complete?"

Iteration 4:
  -> LLM receives: [..., assistant, user(confirmation)] with tools=...
  <- LLM responds: "Yes, the task is complete. The answer is..."
  -> Parse final output, return ToolLoopResult
```

---

## Appendix B: Dependency Graph

```
Layer 1: LLM Protocol Extensions
  llm/base.py (ToolCall, ToolCallFunction, ChatMessage ext, LLMResponse ext)
    |
    +-> llm/router.py (tools param passthrough)
    +-> llm/ollama.py (tools payload, tool_calls parsing)
    +-> llm/openai.py (tools payload, tool_calls parsing)

Layer 2: Tool Loop Core
  agents/tool_loop.py (ToolLoopConfig, ToolLoopState, ToolLoop, ToolLoopResult)
    |
    +-- depends on --> llm/base.py (Layer 1)
    +-- depends on --> tools/registry.py (existing, unchanged)
    +-- depends on --> tools/governance.py (existing, unchanged)
    +-- depends on --> tools/schema.py (existing, unchanged)
    +-- depends on --> skills/injection.py (existing, unchanged)
    +-- depends on --> autonomy/enforcement.py (existing, unchanged)
    +-- depends on --> memory/observation.py (existing, unchanged)
    +-- depends on --> observability/trace_collector.py (existing, unchanged)

Layer 3: Runtime Integration
  agents/runtime.py (invoke_iterative, new deps in __init__)
    |
    +-- depends on --> agents/tool_loop.py (Layer 2)

Layer 4: Wiring
  main.py (ToolRegistry init, ToolGovernance init, bridge update)
  api/routes/agents.py (new endpoint, dependency injection)
  workflows/actions/invoke_agent.py (tool deps, invoke_iterative)
    |
    +-- depends on --> agents/runtime.py (Layer 3)

Layer 5: Double-Confirmation
  (Implemented within agents/tool_loop.py, Layer 2)
  No additional file dependencies.
```

---

## Appendix C: Implementation Schedule

### Day 1: LLM Protocol Extensions (Layer 1)

- Extend `llm/base.py` with `ToolCall`, `ToolCallFunction`, extended `ChatMessage`, extended
  `LLMResponse`.
- Update `llm/router.py` to pass `tools` parameter.
- Update `llm/ollama.py` to include tools in payload and parse tool_calls.
- Update `llm/openai.py` to include tools in payload and parse tool_calls.
- Run full test suite to verify no regressions.
- Write tests for new LLM types (5-8 tests).

### Day 2: Tool Loop Core (Layer 2)

- Create `agents/tool_loop.py` with `ToolLoopConfig`, `ToolLoopState`, `ToolLoop`, `ToolLoopResult`.
- Implement the core loop algorithm with all termination conditions.
- Implement governance checks, observation recording, trace integration.
- Write tests for termination conditions, tool execution, error handling (15-20 tests).

### Day 3: Runtime Integration + Wiring (Layers 3 & 4)

- Add `invoke_iterative()` to `agents/runtime.py`.
- Update `main.py` lifespan to initialize `ToolRegistry` and `ToolGovernance`.
- Update agent invoke route with new endpoint and dependency injection.
- Update workflow bridge.
- Write integration tests (5-8 tests).

### Day 4: Double-Confirmation + Polish (Layer 5)

- Implement double-confirmation logic in `ToolLoop.run()`.
- Write double-confirmation tests (4-5 tests).
- Fix the `_model_router` singleton inconsistency in `agents.py`.
- Run full test suite, lint, type check.
- Update CLAUDE.md if architecture description needs changes.

**Total estimated new tests**: 35-45
**Total estimated new/modified files**: 10
