# Session 109 -- Phase 53: Ad-Hoc Subagent Delegation Tool

## Included Work

1. **`delegate_subtask` tool** (`engine/src/agent33/tools/builtin/delegate_subtask.py`)
   - `DelegateSubtaskTool` implementing `SchemaAwareTool` protocol
   - Parameters: `goal`, `context`, `toolsets`, `max_iterations`, `model_override`
   - Child agent gets fresh conversation with restricted toolset
   - Blocked tools: `delegate_subtask` (no recursion), `clarify`
   - `MAX_DEPTH = 2` enforced via `ToolContext.tool_policies["delegation_depth"]`
   - Concurrent children via `asyncio.Semaphore(3)`
   - Batch delegation via `tasks` parameter

2. **Delegation prompt helpers** (`engine/src/agent33/tools/builtin/delegate_prompts.py`)
   - `build_child_system_prompt(goal, context)` -- focused system prompt
   - `BLOCKED_TOOLS` frozenset
   - `strip_blocked_tools(tool_names)` -- filter blocked tool names

3. **Tests** (`engine/tests/test_delegate_subtask.py`)
   - Child receives isolated context (no parent messages)
   - Blocked tools stripped from child toolset
   - `MAX_DEPTH` enforcement (depth >= 2 raises error)
   - Parent receives summary only, not intermediate tool calls
   - Batch mode runs concurrently and aggregates results

4. **Tool registration** in `main.py` lifespan

## Explicit Non-Goals

- Progress relay / event bus integration (Phase 53 deliverable #4 -- separate slice)
- `run_stream()` integration for delegation events
- Integration tests requiring live LLM calls
- `AgentRuntimeFactory` type alias in runtime.py (not needed; factory is a plain callable)

## Implementation Notes

- Delegation depth is tracked via `ToolContext.tool_policies["delegation_depth"]`.
  `ToolContext` is frozen dataclass so child gets a new instance via `dataclasses.replace()`.
- Child agent uses a minimal `AgentDefinition` with role=IMPLEMENTER, name="delegate-child".
- The tool requires `ModelRouter` and `ToolRegistry` injected at construction time,
  matching the `ApplyPatchTool` pattern of constructor-injected dependencies.
- Child timeout defaults to 300s, configurable via `timeout` parameter.

## Validation Plan

1. `ruff check src/ tests/` -- 0 errors
2. `ruff format --check src/ tests/` -- 0 drift
3. `mypy src --config-file pyproject.toml` -- 0 errors
4. `pytest tests/test_delegate_subtask.py -v` -- all pass
5. `pytest tests/ -q` -- full suite green
