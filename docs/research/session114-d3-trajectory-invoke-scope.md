# Session 114 D3: Direct `invoke()` Trajectory Wiring

## Scope Lock

### Include

1. Wire trajectory persistence into `AgentRuntime.invoke()` only.
2. Persist successful direct invocations to the configured trajectory output directory.
3. Persist failed direct invocations to the failed-trajectory file when execution reaches the LLM phase and then raises.
4. Keep trajectory persistence fail-open so a save failure never changes the original invoke result.
5. Add focused regression coverage for success, failure, and fail-open behavior.

### Exclude

1. `invoke_iterative()` wiring.
2. `invoke_iterative_stream()` wiring.
3. Session-trajectory tracker changes in `agent33.memory.trajectory`.
4. Training-store / database trajectory ingestion.
5. File rotation or retention-policy changes.

## Current Baseline

- `engine/src/agent33/agents/trajectory.py` already provides `save_trajectory()`.
- `engine/src/agent33/config.py` already exposes:
  - `trajectory_capture_enabled`
  - `trajectory_output_dir`
- `engine/src/agent33/agents/runtime.py` currently never calls `save_trajectory()`.
- Existing tests cover the saver itself in `engine/tests/test_trajectory.py`, but not runtime integration.

## Design Decision

- Keep the integration local to `AgentRuntime.invoke()` so the slice closes the main Phase 59 gap without widening into iterative or streaming behavior.
- Capture the direct-invoke conversation in ShareGPT-compatible order:
  1. `system`
  2. `user`
  3. `assistant`
- On success, persist the real assistant response.
- On failure after the invoke reaches the LLM execution phase, persist the base prompt plus a synthetic assistant error turn into the failed-trajectory file.
- Use the global settings object inside `AgentRuntime` for this slice because runtime already lazily reads config there for other direct behaviors.

## Risks

1. Saving trajectories must not mask the original invoke outcome.
2. Failed invocations should not write empty records before user content is constructed.
3. Secret-bearing error strings must still pass through the existing redaction path.

## Planned Validation

```powershell
cd D:\GITHUB\AGENT33\worktrees\session114-p3-trajectory-invoke\engine
$env:PYTHONPATH='D:\GITHUB\AGENT33\worktrees\session114-p3-trajectory-invoke\engine\src'
python -m pytest tests/test_trajectory.py -q --no-cov
python -m ruff check src/agent33/agents/runtime.py src/agent33/agents/trajectory.py tests/test_trajectory.py
python -m ruff format --check src/agent33/agents/runtime.py src/agent33/agents/trajectory.py tests/test_trajectory.py
python -m mypy src/agent33/agents/runtime.py src/agent33/agents/trajectory.py --config-file pyproject.toml
```
