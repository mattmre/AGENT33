# Runtime Compatibility

This repo pins the upstream protocol sources that AGENT-33 currently depends on
for chat-runtime interoperability:

- OpenAI-compatible `POST /chat/completions`
- Ollama native `POST /api/chat`

The lock file lives at `engine/runtime_compatibility.lock.json`.

## Supported sources

- OpenAI-compatible chat completions:
  - official source: `openai/openai-openapi`
- Ollama chat API:
  - official source: `ollama/ollama` `docs/api.md`

## Check command

Run this to verify that the pinned upstream sources have not drifted:

```powershell
python scripts/check_runtime_compatibility.py
```

The command fetches the official sources, verifies a few required markers are
still present, computes their content hashes, and fails if they differ from the
checked-in lock file.

## Refresh command

Run this only when intentionally accepting upstream protocol drift after review:

```powershell
python scripts/check_runtime_compatibility.py --write-lock
```

Use the refresh flow together with the focused provider tests:

- `tests/test_runtime_compatibility.py`
- `tests/test_streaming.py`
- `tests/test_provider_catalog.py`

## CI coverage

- PR CI runs the compatibility check from `.github/workflows/ci.yml`
- scheduled drift detection runs from `.github/workflows/runtime-compatibility.yml`

## Review rule

Do not update the lock file blindly. When drift is detected, confirm:

1. the upstream change actually affects AGENT-33's assumptions
2. the provider request/response tests still match the intended runtime contract
3. any required adapter changes land in the same PR as the lock refresh
