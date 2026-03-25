# Session 109: Phase 50 -- Context Compression Engine

## Included Work

1. **ContextCompressor** (`engine/src/agent33/memory/context_compressor.py`)
   - Three-zone splitting: head (protected), middle (compressed), tail (recent)
   - `needs_compression()` threshold check against model context window
   - `compress()` with structured 5-section summary (Goal / Progress / Key Decisions / Files Modified / Next Steps)
   - Iterative update support: detects existing summary and merges new data
   - Tool output pruning in the middle zone
   - Fallback summary when LLM is unavailable
   - Non-tool-capable LLM call path (`tools=None`) to prevent recursion
   - Operates on a copy of messages; atomic swap

2. **ShortTermMemory integration** (`engine/src/agent33/memory/short_term.py`)
   - Added `compressor: ContextCompressor | None` field
   - Added `compression_count: int` tracking field

3. **ToolLoop integration** (`engine/src/agent33/agents/tool_loop.py`)
   - New `context_compressor` and `model_context_window` parameters on `ToolLoop.__init__`
   - Compression check in `run()` after context management, before next LLM call
   - Compression check in `run_stream()` with `context_compressed` event emission
   - Graceful failure: compression errors are logged but do not break the loop

4. **Config** (`engine/src/agent33/config.py`)
   - `context_compression_enabled: bool = False` (opt-in)
   - `context_compression_threshold_percent: float = 0.50`

5. **Tests** (`engine/tests/test_context_compressor.py`)
   - 22 test cases covering all specified scenarios

## Explicit Non-Goals

- **Lifespan wiring**: The compressor is not auto-created in `main.py` lifespan yet.
  This requires further work to wire `ContextCompressor` into `AgentRuntime` creation
  based on the `context_compression_enabled` config flag.
- **Metrics/observability**: No Prometheus counters for compression events (follow-up).
- **Per-model summarization model selection**: Uses a single `summarize_model` parameter.
- **Token-accurate counting**: Uses the existing `estimate_message_tokens` heuristic.

## Implementation Notes

- Compression is positioned after the existing `ContextManager.manage()` call in the tool
  loop, so both mechanisms can coexist. The existing context manager handles unwinding and
  basic summarization; the new compressor provides structured compression with iterative
  updates.
- The `_CONTEXT_SUMMARY_PREFIX` (`[Compressed Context Summary]`) distinguishes Phase 50
  summaries from the existing `[Context Summary]` prefix used by `ContextManager`.
- `protect_first_n` counts logical message groups, not individual messages. An assistant
  message with `tool_calls` followed by tool-result messages counts as a single group.
- The compressor uses `estimate_message_tokens()` from `context_manager.py` for consistency
  with the rest of the context management subsystem.

## Validation Plan

```bash
cd engine
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
python -m mypy src --config-file pyproject.toml
python -m pytest tests/test_context_compressor.py -x -q
```
