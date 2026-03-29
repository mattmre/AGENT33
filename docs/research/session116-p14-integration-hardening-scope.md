# Session 116 -- P14 Integration Hardening Scope

## Goal

Add a narrow regression test that proves the real FastAPI lifespan wires the
live builtin tool registry correctly on the current `origin/main` baseline.

## Why This Slice Exists

The earlier integration-hardening candidate from Session 114 is already covered
on `main`:

- capability-pack skill discovery
- slash-command parsing
- delegated child tool filtering
- Mixture-of-Agents execution

That path is exercised by
`engine/tests/test_delegate_subtask.py::test_pack_discovery_slash_command_and_moa_chain`,
so repeating it would be duplicate coverage instead of honest hardening.

## Remaining Honest Gap

The app lifespan builds a shared `ToolRegistry` and registers several constructor
injected builtin tools into the live runtime:

- `apply_patch`
- `delegate_subtask`
- `browser`
- `web_search`
- `ptc_execute` when PTC is enabled

Existing tests cover those tools individually, but there is not a direct
lifespan-level regression test proving:

1. `app.state.tool_registry` exists after startup
2. the builtin tools are present in the live registry
3. constructor-injected dependencies point at the runtime objects created by
   startup, especially:
   - `delegate_subtask` using the live `model_router` and `tool_registry`
   - `browser` using the live `model_router`
   - `ptc_execute` using the live `tool_registry`

## Scope

- Add assertions in `engine/tests/test_integration_wiring.py`
- Keep the slice test/docs only unless a real startup wiring defect is exposed

## Non-Goals

- No new production behavior
- No API route expansion
- No new delegation or MoA scenarios
- No frontend or CLI work

## Validation Plan

- `python -m pytest engine/tests/test_integration_wiring.py -q --no-cov`
- `python -m ruff check engine/tests/test_integration_wiring.py docs/research/session116-p14-integration-hardening-scope.md`
