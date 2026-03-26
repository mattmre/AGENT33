# Session 111 B2A Stream Parity Scope

Date: 2026-03-26

## Goal

Close the lowest-risk subset of the documented `run_stream()` parity gaps by aligning streaming behavior with `run()` for:

- LLM retry on transient errors
- end-of-iteration budget enforcement
- consecutive-error reset after a successful tool-call iteration

## Included Gaps

1. **LLM retry on error**
   - `run()` already retries until `error_threshold`
   - `run_stream()` previously terminated on the first LLM error

2. **End-of-iteration budget enforcement**
   - `run()` checks `record_iteration()` and `check_duration()` after context updates
   - `run_stream()` previously skipped those checks between iterations

3. **`consecutive_errors` reset**
   - `run()` resets the counter when a response contains tool calls
   - `run_stream()` previously never reset it

## Explicit Non-Goals

- Handoff interceptor parity
- Double-confirmation parity
- LLM response observation parity
- Any changes to non-streaming `run()`
- Any event-schema redesign beyond what is needed to express retry/budget state

## Implementation Notes

- Touch only `engine/src/agent33/agents/tool_loop.py` plus targeted streaming tests.
- Preserve the existing streaming event model.
- Use a dedicated follow-up slice (`B2B`) for the remaining stateful parity features.

## Validation Plan

- `python -m pytest engine/tests/test_streaming_tool_loop.py engine/tests/test_tool_loop.py -q --no-cov`
- `python -m ruff check engine/src/agent33/agents/tool_loop.py engine/tests/test_streaming_tool_loop.py`
- `python -m ruff format --check engine/src/agent33/agents/tool_loop.py engine/tests/test_streaming_tool_loop.py`
- `python -m mypy engine/src/agent33/agents/tool_loop.py --config-file engine/pyproject.toml`
