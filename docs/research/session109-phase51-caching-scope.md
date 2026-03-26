# Session 109 -- Phase 51: Anthropic Prompt Caching Scope

## Included Work

1. **Prompt cache module** (`engine/src/agent33/llm/prompt_caching.py`)
   - `apply_anthropic_cache_control()` -- injects up to 4 `cache_control`
     breakpoints using the *system_and_3* strategy.
   - `is_anthropic_model()` -- detects `claude-*` model name prefix.
   - Deep-copies messages to avoid caller mutation.
   - Handles string content, content-block lists, and tool-role messages.

2. **Provider integration** (`engine/src/agent33/llm/openai.py`)
   - `complete()`: inject cache breakpoints for Claude models when
     `prompt_cache_enabled` is `True`.
   - `stream_complete()`: same injection.
   - Log `cache_read_input_tokens` and `cache_creation_input_tokens` from
     response usage metadata when available.

3. **Config** (`engine/src/agent33/config.py`)
   - `prompt_cache_enabled: bool = True` -- on by default; operators can
     disable via `PROMPT_CACHE_ENABLED=false`.

4. **Tests** (`engine/tests/test_prompt_caching.py`)
   - system_and_3 strategy places exactly 4 breakpoints.
   - String content converted to content-block list with cache marker.
   - Tool-role messages get top-level `cache_control`.
   - Deep copy: original messages unmodified.
   - Mixed content blocks (text + image_url).
   - Fewer-than-4 messages edge case.
   - No system message edge case.
   - Settings gate: disabled setting skips injection.
   - Wire format assertions match Anthropic API expectations.
   - `cache_ttl` parameter accepted for forward compatibility.

## Explicit Non-Goals

- **Phase 49 pricing catalog changes** -- already merged; no modifications here.
- **Cost tracking/billing integration** -- cache savings are logged but not
  fed into the effort-routing cost model in this slice.
- **Dynamic cache_ttl mapping** -- Anthropic currently only supports
  `{"type": "ephemeral"}`; the `cache_ttl` parameter is accepted but not
  translated to different marker types.
- **Streaming cache usage logging** -- Anthropic's streaming format may not
  return cache_read/cache_creation tokens in every chunk; logging is only
  implemented for non-streaming `complete()`.

## Implementation Notes

- The provider integration patches the serialized message list *after*
  `_serialize_message()` has run, so it operates on plain dicts (wire format),
  not `ChatMessage` dataclasses.
- The module import of `settings` in `openai.py` uses the module-level
  singleton; tests patch `agent33.llm.openai.settings` to override.
- Breakpoint count: 1 system + up to 3 tail non-system = 4 max. If no system
  message exists, all 4 breakpoints go to the last 4 non-system messages.

## Validation Plan

1. `ruff check src/ tests/` -- 0 errors
2. `ruff format --check src/ tests/` -- no diffs
3. `mypy src --config-file pyproject.toml` -- 0 errors
4. `pytest tests/test_prompt_caching.py -q` -- all tests pass
5. Full test suite: `pytest tests/ -q` -- no regressions
