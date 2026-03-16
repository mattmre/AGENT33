# S46: E2E Integration Test Suite - Scope and Design

**Session**: 91
**Date**: 2026-03-15
**Status**: Implemented

## Problem Statement

AGENT-33 has 165+ test files and ~3,572 test functions, but only 3 files
qualify as true cross-subsystem integration tests. The existing tests are
either unit tests (testing a single module) or wiring tests (verifying app
startup/middleware). No HTTP-level E2E tests exercise the full request
lifecycle across subsystem boundaries.

## Scope

Add comprehensive E2E integration tests that exercise cross-subsystem flows
through the HTTP API layer, using mocked external dependencies (PostgreSQL,
Redis, NATS, LLM providers) but real internal wiring.

## Test Categories

### 1. Agent Invocation Flow (`test_agent_tool_memory_flow.py`)
- Agent registration via API
- Agent invoke -> runtime construction -> LLM response -> structured output
- Subsystem passthrough (skill_injector, progressive_recall, hook_registry)
- Prompt injection detection at the HTTP layer
- 404 for non-existent agents

### 2. Workflow Execution (`test_workflow_agent_bridge.py`)
- Workflow creation -> DAG validation -> storage
- Sequential workflow execution with state passing between steps
- Execution history recording
- DAG visualization endpoint
- Run ID passthrough
- Duplicate prevention (409 on re-create)

### 3. Multi-Tenant Isolation (`test_multi_tenant_isolation.py`)
- Authentication enforcement (401 on unauthenticated requests)
- Public endpoint allowlist (health, dashboard)
- Session data isolation between tenants
- Direct access prevention (403 on cross-tenant by-id access)
- Admin sees all tenants
- Workflow history tenant scoping

### 4. Session Lifecycle (`test_session_lifecycle.py`)
- Full lifecycle: create -> checkpoint -> end
- Task tracking (add, update status, list, count)
- Replay log accumulation and summary
- Suspend and resume
- State machine enforcement (409 on invalid transitions)

### 5. Hook Chain Integration (`test_hook_chain.py`)
- Pre-hook input mutation before LLM call
- Post-hook result capture
- Hook abort prevents execution (403)
- Hook chain priority ordering

## Mock Strategy

| Dependency      | Mock Approach                          |
|----------------|----------------------------------------|
| PostgreSQL     | `patch("agent33.main.LongTermMemory")` |
| Redis          | `patch.dict(sys.modules, ...)` with mock |
| NATS           | `patch("agent33.main.NATSMessageBus")` |
| LLM providers  | `patch.object(model_router, "complete")` or `patch("...AgentRuntime")` |

Internal subsystems (AgentRegistry, HookRegistry, SkillInjector, etc.) use
their real implementations initialized through the app lifespan.

## Directory Layout

```
engine/tests/e2e/
  __init__.py
  conftest.py                      # Shared fixtures
  test_agent_tool_memory_flow.py   # 5 tests
  test_workflow_agent_bridge.py    # 5 tests
  test_multi_tenant_isolation.py   # 7 tests
  test_session_lifecycle.py        # 5 tests
  test_hook_chain.py               # 3 tests
```

## Key Design Decisions

1. **Shared `e2e_app` fixture** creates the app once per test with lifespan
   intact. Each test gets its own `TestClient`.

2. **Tenant fixtures** create separate `TestClient` instances with different
   JWT tokens bound to different tenant IDs, enabling real tenant isolation
   testing.

3. **Hook tests register real hook instances** on the app.state.hook_registry,
   testing the actual hook chain execution path rather than mocking.

4. **Session tests may skip** when the operator session service is not
   initialized in the test environment (it requires filesystem storage).

5. **All tests marked with `pytest.mark.e2e`** for selective execution.
