# Session 116 P3 Scope Lock: Runtime Compatibility Drift CI

Date: 2026-03-28
Slice: `0.3 agent/runtime compatibility drift CI`

## Why this slice exists

AGENT-33 depends on two concrete runtime protocol families today:

1. OpenAI-compatible `POST /chat/completions`
2. Native Ollama `POST /api/chat`

Those contracts are external to the repo. When they drift silently, the breakage
first appears in provider integration paths instead of in CI.

## Minimum credible scope

- add a pinned compatibility lock for the official upstream protocol sources we
  rely on
- add one repo-local check command that fetches those sources and fails when
  the upstream content hash drifts
- add one scheduled GitHub Actions workflow for the same check
- add focused provider-contract tests for the request/response shapes AGENT-33
  expects from:
  - `agent33.llm.openai.OpenAIProvider`
  - `agent33.llm.ollama.OllamaProvider`
- document the refresh/check workflow

## Supported runtimes in this slice

- OpenAI-compatible chat completions
  - canonical source: official `openai/openai-openapi` spec
- Ollama native chat API
  - canonical source: official `ollama/ollama` API docs

## Non-goals

- full provider expansion or direct support for every catalog entry
- live end-to-end calls against remote providers
- replacing the existing provider unit and streaming tests
- broad router or prompt-caching refactors

## Exit criteria

- `python scripts/check_runtime_compatibility.py` works as the canonical drift check
- one documented refresh command exists
- PR CI runs the compatibility check
- a scheduled workflow runs the same check
- focused tests cover the provider request/response contract assumptions
