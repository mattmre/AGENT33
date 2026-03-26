# Session 109 - Phase 56: Programmatic Tool Calling (PTC) Execution

## Included Work

1. **PTCExecutor** (`engine/src/agent33/execution/programmatic_tool_chain.py`)
   - TCP localhost socket RPC server (Windows-compatible, no UDS dependency)
   - Shared-secret authentication per request
   - AST-level validation (custom walker, no RestrictedPython dependency)
   - Stub module generation for allowed tools
   - Subprocess isolation with `asyncio.wait_for()` + `finally:` cleanup
   - Resource limits: `timeout=300s`, `max_tool_calls=50`, `max_stdout=50KB`

2. **PTC Tool** (`engine/src/agent33/tools/builtin/ptc_execute.py`)
   - `PTCExecuteTool` implementing `SchemaAwareTool` protocol
   - Tool name: `ptc_execute` (avoids collision with Phase 13 `execute_code`)
   - AST validation before execution
   - Dispatches to PTCExecutor

3. **Tests** (`engine/tests/test_ptc_execution.py`)
   - Stub generation produces valid Python module
   - RPC socket round-trip (tool call -> parent dispatch -> result)
   - Resource limits enforced (timeout kills process, stdout capped)
   - Blocked imports rejected by AST validation
   - Multi-tool script dispatches correctly

## Explicit Non-Goals

- No lifespan registration in `main.py` (deferred to integration slice)
- No named-pipe Windows fallback (TCP localhost is sufficient and simpler)
- No RestrictedPython dependency (custom AST walker covers the security needs)
- No route/API endpoint for PTC (tool is invoked via tool registry)
- No Docker/container isolation (existing subprocess sandbox is sufficient for Phase 56)

## Implementation Notes

- TCP localhost socket chosen over UDS for cross-platform compatibility (spec says
  "TCP localhost socket instead of Unix domain socket" for Windows support)
- Tool calls travel as JSON over the TCP socket: `{"secret": "...", "tool": "...", "params": {...}}`
- Response format: `{"success": true/false, "output": "...", "error": "..."}`
- The stub module (`agent33_tools.py`) is generated at runtime with typed functions
  that connect to the parent's RPC server
- AST validation rejects: `import` statements for non-allowed modules, `exec/eval/compile`,
  `__import__`, attribute access on `__builtins__`, `open()` calls, `os.system` etc.

## Validation Plan

1. `ruff check src/ tests/` -- 0 errors
2. `ruff format --check src/ tests/` -- 0 diffs
3. `mypy src --config-file pyproject.toml` -- 0 errors
4. `pytest tests/test_ptc_execution.py -v` -- all pass
