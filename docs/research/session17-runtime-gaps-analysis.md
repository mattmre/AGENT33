---
title: "Session 17: Runtime Integration Gaps Analysis"
date: 2026-02-15
session: 17
type: research
status: complete
---

# Session 17: Runtime Integration Gaps Analysis

## Overview

This document identifies and analyzes four runtime integration gaps in AGENT-33's engine where subsystems that are individually complete and tested fail to work together due to missing wiring. These are not feature gaps (the capabilities exist) but integration gaps (the connections between capabilities are absent).

## Gap 1: Answer Leakage Prevention -> Tool Loop

### Description

The `SkillMatcher` class implements answer leakage detection in its stage 4 strict filter. When the LLM's skill matching response contains content that looks like a direct task answer (rather than a skill recommendation), the leakage detector flags it and the response is discarded.

However, this leakage detection is only active during the skill matching phase. During the iterative tool loop, tool outputs are fed back to the LLM without any leakage check. If a tool returns content that inadvertently contains an answer to the overall task, the LLM may simply parrot it rather than reasoning about it.

### Current State

- `skills/matching.py`: `_detect_leakage()` method on `SkillMatcher`, checks for answer patterns in LLM responses during stage 4
- `agents/tool_loop.py`: `_execute_tool_calls()` method feeds tool results directly back to the conversation without any content filtering
- No connection between the two systems

### Impact

- **Medium-High**: In evaluation scenarios, if a tool returns the expected answer verbatim, the agent may pass the evaluation without demonstrating reasoning ability
- This is particularly relevant for SkillsBench-style evaluation where skills_impact measurement requires distinguishing between skill-assisted reasoning and answer parroting

### Proposed Integration

```python
# In agents/tool_loop.py, ToolLoop class

class ToolLoop:
    def __init__(
        self,
        ...,
        leakage_detector: Callable[[str], bool] | None = None,
    ):
        self._leakage_detector = leakage_detector

    async def _execute_tool_calls(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        results = []
        for call in tool_calls:
            result = await self._execute_single_call(call)

            # Check for answer leakage in tool output
            if self._leakage_detector and isinstance(result.output, str):
                if self._leakage_detector(result.output):
                    result = ToolResult(
                        tool_name=call.name,
                        output="[Tool output filtered: potential answer leakage detected]",
                        success=True,
                        metadata={"leakage_filtered": True},
                    )

            results.append(result)
        return results
```

### Effort

Small -- 15-20 lines of production code, 5-8 tests.

## Gap 2: Context Manager <-> Tool Loop Auto-Management

### Description

The `ContextManager` (`agents/context_manager.py`) provides token-aware conversation management: estimating token counts, detecting budget overruns, unwinding old messages, and generating handoff summaries. It is fully implemented and tested with 38 tests.

The `ToolLoop` (`agents/tool_loop.py`) runs iterative tool-use cycles where the conversation grows with each iteration (user message -> LLM response -> tool call -> tool result -> LLM response -> ...). It is fully implemented and tested with 64 tests.

These two systems are not connected. A tool loop running 10 iterations on a 128k context window model will silently accumulate tokens until the context is exhausted, at which point the LLM call will fail with a context length error.

### Current State

- `agents/context_manager.py`: `ContextManager.manage()` accepts a message list and budget, returns a managed (possibly truncated) message list
- `agents/tool_loop.py`: `ToolLoop.run()` maintains `self._state.messages` list, appends to it each iteration, never checks size
- No integration point between the two

### Impact

- **High**: Long-running tool loops will fail unpredictably when context is exhausted
- The failure mode is particularly bad: the LLM receives a truncated context (API-side) without any intelligent summarization, losing important early-conversation context
- This gap was identified during integration testing analysis as both a test gap AND an implementation gap

### Proposed Integration

```python
# In agents/tool_loop.py, ToolLoop class

class ToolLoopConfig(BaseModel):
    # ... existing fields ...
    context_manager: ContextManager | None = None
    context_check_interval: int = 1  # Check every N iterations

class ToolLoop:
    def __init__(self, config: ToolLoopConfig, ...):
        ...
        self._context_manager = config.context_manager
        self._context_check_interval = config.context_check_interval

    async def run(self, initial_message: str) -> ToolLoopResult:
        ...
        for iteration in range(self._config.max_iterations):
            # Context management between iterations
            if (
                self._context_manager
                and iteration > 0
                and iteration % self._context_check_interval == 0
            ):
                managed = self._context_manager.manage(
                    self._state.messages,
                    model=self._config.model,
                )
                if managed.was_truncated:
                    self._state.messages = managed.messages
                    # Log the truncation for observability
                    self._state.metadata["context_truncations"] = (
                        self._state.metadata.get("context_truncations", 0) + 1
                    )

            # ... existing iteration logic ...
```

### Effort

Medium -- 30-40 lines of production code, 8-12 tests.

## Gap 3: Failure Mode Taxonomy Alignment

### Description

AGENT-33 has a failure taxonomy in the observability subsystem (`observability/`) that categorizes trace outcomes into 10 failure categories. The `TraceOutcome` model includes `failure_code`, `failure_message`, and `failure_category` fields.

SkillsBench categorizes task failures differently, using categories aligned with tool-use patterns (tool selection failure, argument formatting error, partial completion, timeout, etc.).

Currently, when the iterative tool loop fails, the failure is reported as a generic error without mapping to the observability taxonomy. This means:
- Tool loop failures don't appear in the trace pipeline with meaningful categorization
- SkillsBench-style failure analysis cannot be performed on AGENT-33 results
- Regression detection (RI-01..RI-05) cannot distinguish between failure types in tool-use scenarios

### Current State

- `observability/models.py`: `TraceOutcome` with `failure_category` field, 10 existing categories
- `agents/tool_loop.py`: `ToolLoopResult` with `error` field (free-form string), no category mapping
- No mapping between tool loop failure modes and trace failure categories

### Impact

- **Medium**: Without categorized failures, it is impossible to detect patterns like "this model consistently fails at tool argument formatting" or "this agent times out on multi-step tasks"
- Blocks meaningful regression analysis on multi-trial evaluation results

### Proposed Integration

Add tool-loop-specific failure categories to the existing taxonomy:

```python
# New failure categories for tool loop
TOOL_LOOP_FAILURE_CATEGORIES = {
    "tool_selection_invalid": "LLM selected a tool that doesn't exist",
    "tool_argument_error": "LLM provided invalid arguments to a tool",
    "tool_execution_error": "Tool execution raised an exception",
    "tool_governance_denied": "Tool call blocked by governance/allowlist",
    "max_iterations_exceeded": "Tool loop hit max iterations without final answer",
    "context_exhausted": "Context window exhausted during tool loop",
    "double_confirm_rejected": "LLM could not confirm task completion",
    "leakage_detected": "Answer leakage detected in tool output",
}
```

Map `ToolLoopResult` failures to `TraceOutcome`:

```python
def tool_loop_result_to_trace_outcome(result: ToolLoopResult) -> TraceOutcome:
    """Map a tool loop result to a trace outcome with proper failure categorization."""
    if result.success:
        return TraceOutcome(status="success")

    category = _classify_tool_loop_failure(result)
    return TraceOutcome(
        status="failure",
        failure_code=f"TOOL_LOOP_{category.upper()}",
        failure_message=result.error,
        failure_category=category,
    )
```

### Effort

Small-Medium -- 40-50 lines of production code, 10-15 tests.

## Gap 4: Task Completion Double-Confirmation

### Description

The `ToolLoop` implements a double-confirmation mechanism for task completion. When `enable_double_confirmation` is True and the LLM returns a text response (not a tool call), the loop re-prompts the LLM with a confirmation request before accepting the response as the final answer.

This mechanism is implemented and functional, but could be strengthened in two ways:

1. **Structured completion detection**: Currently, `_looks_like_final_answer()` uses heuristics (checking for tool call markers in the text). It could use structured output (JSON with a `completed` field) for more reliable detection.

2. **Verification integration**: The double-confirmation only asks the LLM "are you done?" -- it does not verify that the task was actually completed correctly. Integration with A2's `DatabaseVerifier` or A3's `ToolCallExpectation` would allow verification-backed confirmation.

### Current State

- `agents/tool_loop.py`: `_looks_like_final_answer()` method, `enable_double_confirmation` flag
- Double confirmation re-prompts the LLM with: "You appear to have completed the task. Please confirm your final answer or continue working."
- No integration with verification systems

### Impact

- **Low-Medium**: The current implementation works for most cases. The primary risk is false positives (LLM says "done" when it isn't) in complex multi-step scenarios.
- This gap becomes more important when multi-turn evaluation (A3) is implemented, as accurate completion detection directly affects M-07 (multi-turn success rate)

### Proposed Enhancement (Staged)

**Stage 1** (minimal, can ship now): Add structured completion format:

```python
COMPLETION_CHECK_PROMPT = """
You indicated you have completed the task. Please respond with exactly one of:
- COMPLETED: [your final answer]
- CONTINUE: [what you still need to do]
"""
```

**Stage 2** (after A2/A3): Add verification-backed confirmation:

```python
async def _verify_completion(
    self,
    result: str,
    verification_specs: list[VerificationSpec] | None = None,
) -> bool:
    """Verify task completion using database verification if available."""
    if not verification_specs:
        return True  # No specs, trust the LLM's self-report

    verifier = self._db_verifier
    results = await verifier.verify_all(verification_specs)
    return all(r.passed for r in results)
```

### Effort

Stage 1: Small -- 10-15 lines of production code, 3-5 tests.
Stage 2: Medium -- depends on A2 implementation.

## Summary

| Gap | Severity | Effort | Dependencies |
|-----|----------|--------|--------------|
| Gap 1: Leakage -> Tool Loop | Medium-High | Small | None |
| Gap 2: Context Manager <-> Tool Loop | High | Medium | None |
| Gap 3: Failure Taxonomy Alignment | Medium | Small-Medium | None |
| Gap 4: Double-Confirmation Enhancement | Low-Medium | Small (Stage 1) | A2/A3 (Stage 2) |

### Recommended Priority

1. **Gap 2** (Context Manager <-> Tool Loop) -- Highest severity, prevents context exhaustion failures
2. **Gap 1** (Leakage -> Tool Loop) -- Important for evaluation integrity
3. **Gap 3** (Failure Taxonomy) -- Enables meaningful failure analysis
4. **Gap 4** (Double-Confirmation) -- Enhancement, not blocking

Total estimated effort: 95-120 lines of production code, 26-40 tests.
