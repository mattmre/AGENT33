# Wave 2 Round 10 - Browser/local helper LLM pilot

## Goal

Round 10 turns the static Help Assistant into a runtime-aware helper pilot without adding model downloads, external calls, or secret handling. The default remains deterministic cited search. Browser semantic search and Ollama sidecar modes are exposed as opt-in readiness paths with privacy and setup guidance.

## Panel critique synthesis

- Beginners need a helper that answers setup questions immediately, but a hidden model download would create trust and performance problems.
- The safe first step is runtime selection and privacy education, not generation.
- Static cited search should remain the fallback for every mode.
- Local helper modes must be explicit about who controls the model, where it runs, and whether secrets are included.

## Competitive patterns reviewed

- Open WebUI and AnythingLLM make local model use accessible but still require clear setup and runtime status.
- Browser LLM demos often fail silently when WebGPU or memory is unavailable; AGENT-33 should show readiness before attempting downloads.
- Agent platforms that answer setup questions in-product reduce onboarding friction, but hallucination risk is unacceptable for credentials and configuration.

## Implementation decision

This PR-sized slice adds:

1. `helperModes.ts` with typed runtime modes and beginner status labels.
2. A Help Assistant runtime selector for static search, browser semantic search, and Ollama sidecar.
3. A help article explaining when to use each runtime.
4. Tests for runtime mode behavior and drawer rendering.

## Deferred follow-up

- Generated docs index.
- Browser embeddings with bundle-size and CPU checks.
- Optional Ollama/OpenAI-compatible local RAG calls.
- WebLLM/WebGPU generation only after explicit user opt-in.
