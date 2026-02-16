# Phase 22 PR-06: Phase A Safety Guardrails

## Scope
- Add wildcard permission decisions with explicit `allow` / `ask` / `deny`.
- Add tool-level governance policy matching (`tool`, `tool:operation`, wildcard patterns).
- Add iterative doom-loop detection for repeated identical tool calls.
- Wire iterative invoke runtime context to authenticated scopes + governance tool policies.

## Key Changes
- Updated `engine/src/agent33/security/permissions.py`:
  - Added `PermissionDecision` enum and `check_permission_decision(...)`.
  - Added wildcard scope matching with deny-first semantics.
  - Preserved `check_permission(...)` backward-compatible bool behavior.
- Updated `engine/src/agent33/tools/base.py`:
  - Added `tool_policies` to `ToolContext`.
- Updated `engine/src/agent33/tools/governance.py`:
  - Added policy evaluation before standard scope checks.
  - Added precedence-aware policy matching:
    - exact operation (`tool:op`)
    - exact tool (`tool`)
    - wildcard operation (`pattern:op`)
    - wildcard tool (`pattern`)
    - global (`*`)
  - `deny` and `ask` block execution (ask is staged for future approval flow).
- Updated `engine/src/agent33/agents/definition.py`:
  - Added `governance.tool_policies`.
- Updated `engine/src/agent33/agents/runtime.py`:
  - Included tool policies in governance system prompt.
- Updated `engine/src/agent33/agents/tool_loop.py`:
  - Added loop detection config and identical-call detection.
  - Added `loop_detected` termination reason.
  - Default loop detection disabled in base config for backward compatibility.
- Updated `engine/src/agent33/api/routes/agents.py`:
  - Added iterative request `loop_detection_threshold`.
  - Constructed iterative `ToolContext` from authenticated user scopes and definition governance tool policies.

## Tests
- Updated `engine/tests/test_phase14_security.py`:
  - wildcard deny/allow coverage
  - ask decision coverage
  - tool policy allow/ask/deny/wildcard/operation coverage
- Updated `engine/tests/test_tool_loop.py`:
  - loop detection trigger and reset behavior
  - disabled-threshold behavior
  - config default assertions
- Updated `engine/tests/test_governance_prompt.py`:
  - governance prompt rendering for tool policies

## Validation
- `cd engine && python -m ruff check src/agent33/security/permissions.py src/agent33/tools/base.py src/agent33/tools/governance.py src/agent33/agents/definition.py src/agent33/agents/runtime.py src/agent33/agents/tool_loop.py src/agent33/api/routes/agents.py tests/test_phase14_security.py tests/test_tool_loop.py tests/test_governance_prompt.py`
- `cd engine && python -m mypy src/agent33/security/permissions.py src/agent33/tools/base.py src/agent33/tools/governance.py src/agent33/agents/definition.py src/agent33/agents/runtime.py src/agent33/agents/tool_loop.py src/agent33/api/routes/agents.py`
- `cd engine && python -m pytest tests/test_phase14_security.py tests/test_tool_loop.py tests/test_invoke_iterative.py tests/test_governance_prompt.py tests/test_agent_registry.py -q`
