# S27: Context Window Management Improvements

**Session**: 89
**Slice**: S27
**Status**: Implemented
**Date**: 2026-03-15

## Problem Statement

Agent invocations assemble prompts from multiple components (system prompt,
skill instructions, tool definitions, conversation history) but had no
proactive mechanism to check whether the assembled context fits within the
target model's context window *before* sending the request to the LLM.

The existing `ContextManager` (in `agents/context_manager.py`) handles
*reactive* management during iterative tool loops -- unwinding and
summarizing messages when they exceed limits. However, there was no
*proactive* per-component budgeting layer for single-shot invocations.

## Solution

### New module: `agents/context_window.py`

Three core constructs:

1. **`ContextBudget`** (Pydantic model) -- per-component token breakdown
   with computed fields for `used_tokens`, `available_tokens`, and
   `utilization` percentage.

2. **`ContextWindowPolicy`** (Pydantic model) -- configurable ratio limits
   for history, skills, and tools, plus truncation strategy and warning
   threshold.

3. **`ContextWindowManager`** (class) -- proactive budgeting engine:
   - `estimate_tokens(text)` -- fast token estimation via pluggable counter
   - `create_budget(...)` -- compute per-component allocation
   - `truncate_history(messages, max_tokens)` -- smart history truncation
   - `truncate_context(text, max_tokens, strategy)` -- head/tail/smart text truncation
   - `fits_budget(text, budget)` -- check if text fits available tokens
   - `enforce_policy(budget)` -- cap components to policy ratios
   - `get_utilization_report(budget)` -- detailed breakdown dict
   - `check_and_warn(budget)` -- log warning if above threshold

### Runtime integration

`AgentRuntime.__init__` accepts an optional `context_window_manager`
parameter. In `invoke()`, after hooks and input validation, the manager
creates a budget from the assembled system prompt and user content, then
logs warnings if utilization exceeds the configured threshold.

### API endpoint

`GET /v1/agents/{name}/context-budget` (scope: `agents:read`) returns
the utilization report for an agent's current configuration, including
skill instructions if a skill injector is available.

### Config additions

- `agent_default_context_window: int = 128000`
- `agent_context_warn_threshold: float = 0.8`

## Relationship to existing ContextManager

This module is **complementary**, not a replacement:

| Aspect | `context_manager.py` | `context_window.py` |
|--------|---------------------|---------------------|
| Scope | Iterative tool loops | Any invocation |
| Strategy | Reactive (unwind/summarize) | Proactive (budget/truncate) |
| Granularity | Total message tokens | Per-component breakdown |
| When it acts | During loop iterations | Before first LLM call |

## Test Coverage

`tests/test_context_window.py` -- 37 tests covering all public API
surfaces, policy enforcement, API route behavior, and runtime integration.
