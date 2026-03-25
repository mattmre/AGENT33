# Session 109: Phase 59 -- Session Title Generation & Trajectory Saving

## Included Work

1. **Title Generator** (`engine/src/agent33/agents/title_generator.py`)
   - `generate_title()` -- async function that uses cheapest model via router
   - Truncates inputs to 500 chars, returns 3-7 word title or None on failure
   - Strips surrounding quotes from LLM output

2. **Trajectory Saver** (`engine/src/agent33/agents/trajectory.py`)
   - `save_trajectory()` -- async function that writes ShareGPT-format JSONL
   - Applies `redact_secrets()` before persisting
   - Uses `asyncio.to_thread()` for file I/O
   - Separates successful vs failed trajectories into different files
   - `convert_scratchpad_to_think()` -- normalizes reasoning tags

3. **Config** (`engine/src/agent33/config.py`)
   - `trajectory_capture_enabled: bool = False` -- opt-in
   - `trajectory_output_dir: str = "trajectories"` -- output directory

4. **Tests**
   - `engine/tests/test_title_generator.py` -- title generation with mock router
   - `engine/tests/test_trajectory.py` -- trajectory saving, format, redaction

## Explicit Non-Goals

- No wiring into AgentRuntime post-invoke hooks (spec says "via hooks", but that
  is a follow-up integration slice once the core modules exist and are tested)
- No TrainingStore (PostgreSQL) integration -- local JSONL is the primary storage
  for this slice; TrainingStore integration is a future follow-up
- No file rotation (max 100MB) -- future hardening
- No `auto_title_session()` fire-and-forget wrapper (trivial to add once session
  service integration is done)

## Implementation Notes

- `redact_secrets` from `agent33.security.redaction` is imported and applied to
  every conversation turn before writing
- `ModelRouter.complete()` accepts `messages: list[ChatMessage]`, returns
  `LLMResponse` with `.content`
- Config follows existing `pydantic_settings.BaseSettings` pattern with env vars

## Validation Plan

```bash
cd engine
.venv/Scripts/python.exe -m ruff check src/ tests/
.venv/Scripts/python.exe -m ruff format --check src/ tests/
.venv/Scripts/python.exe -m mypy src --config-file pyproject.toml
.venv/Scripts/python.exe -m pytest tests/test_title_generator.py tests/test_trajectory.py -x -q
```
