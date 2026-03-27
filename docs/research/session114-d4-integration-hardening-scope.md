# Session 114 -- D4 Cross-Feature Integration Hardening Scope

## Goal

Add one high-signal regression test that proves the post-Session-113 composition
stack works together on the current `main` baseline:

- slash-command skill activation
- capability-pack sourced skill loading
- delegated child tool filtering
- Mixture-of-Agents execution

## Live Baseline

- D1 merged: delegated children now honor the filtered child tool registry
- D2 merged: MoA resolves exact workflow agent handlers safely before DAG build
- D3 merged: direct `invoke()` trajectory persistence is wired, but this slice
  does not widen into trajectory assertions
- No open AGENT33 PRs exist, so D4 is a new test-focused PR

## Narrowest Credible Test Path

The narrowest regression path is a direct runtime/tool integration test, not a
full API or frontend roundtrip.

### Proposed scenario

1. Create a temporary capability pack containing a skill with:
   - a slash-command-friendly name
   - `allowed_tools` limited to `mixture_of_agents`
2. Discover that pack through `PackRegistry` so the skill is loaded through the
   real pack path instead of manual registry registration.
3. Build slash-command mappings with `scan_skill_commands()` and parse an input
   like `/ensemble-review compare these answers`.
4. Use the parsed skill name to derive the delegated child tool allowlist from
   the real `SkillDefinition` through `SkillInjector.resolve_tool_context(...)`.
5. Execute `delegate_subtask` against a real `ToolRegistry` containing:
   - `delegate_subtask`
   - `mixture_of_agents`
   - one unrelated probe tool that must stay hidden from the child
6. Drive the parent and child LLM calls with a mocked router so the child
   attempts to call `mixture_of_agents`.
7. Patch the registered `MoATool` instance so the test asserts the child loop
   actually executed the MoA tool and fed its synthesized result back into the
   next LLM turn.
8. Assert:
   - the capability-pack skill was discovered and slash-parsed correctly
   - the delegated child receives only `mixture_of_agents`
   - the unrelated tool is not visible/executable in the child loop
   - the MoA result propagates back through delegation successfully

## Why This Is The Right Scope

- It exercises the exact residual risk from D1 and D2 together instead of
  re-testing those slices independently.
- It proves capability-pack skill metadata can drive a delegated-tool boundary.
- It keeps D4 as a test-only hardening slice, matching the active queue.
- It avoids shallow route-existence testing and instead asserts on real
  cross-feature behavior.

## Files In Scope

- `engine/tests/test_delegate_subtask.py`
- `docs/research/session114-d4-integration-hardening-scope.md`

## Existing Helpers Reused

- `engine/tests/test_delegate_subtask.py` fixtures for:
  - `DelegateSubtaskTool`
  - `ToolContext`
  - mocked router / registry plumbing
- `engine/tests/test_pack_integration.py` discovery and enablement patterns
- `engine/tests/test_slash_commands.py` parser mechanics
- `engine/tests/test_moa_workflow.py` deterministic MoA success/failure patterns

## Non-Goals

- No production runtime changes unless the new regression test exposes a real
  integration defect
- No API route wiring
- No CLI chat-path expansion
- No trajectory assertions
- No voice-sidecar work in this slice

## Validation Plan

- `python -m pytest engine/tests/test_delegate_subtask.py -q --no-cov`
- `python -m ruff check engine/tests/test_delegate_subtask.py`
- `python -m ruff format --check engine/tests/test_delegate_subtask.py`
