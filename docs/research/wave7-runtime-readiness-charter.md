# Wave 7 runtime/provider readiness charter

Wave 7 is the odd-wave research gate for making AGENT33 feel like a usable local-and-cloud agent runtime instead of a form that asks beginners to know provider URLs, model names, and failure modes. The Wave 8 implementation should make local providers visible, testable, and explainable before a user saves a model connection.

## Ground truths to preserve

1. Provider setup stays frontend-first: beginner presets remain the first interaction, and raw endpoint fields stay secondary.
2. Local helper modes stay opt-in: no hidden model downloads, no silent browser/WebGPU startup, and static cited help remains the fallback.
3. Automation uses provider API keys only; do not introduce OAuth tokens or exported CLI credentials into CI or runtime probes.
4. Docker/Agent OS isolation remains the default for code execution; local execution remains explicit opt-in.
5. MCP stays operator-visible infrastructure with health, sync, and tool inventory surfaces.
6. Destructive actions and credential-affecting actions stay gated by risk-prioritized approvals.
7. Named Agent OS sessions remain first-class workspaces, not disposable temp directories.

## Current implementation surface

| Surface | Current state | Wave 7 finding |
| --- | --- | --- |
| Provider catalog | `engine/src/agent33/llm/providers.py` registers static provider metadata for Ollama, LM Studio, OpenRouter, OpenAI-compatible providers, and others. | Catalog is useful, but it is not live discovery. |
| Runtime router | `engine/src/agent33/llm/runtime_config.py` builds configured provider routes from settings/env vars. | Router can register providers that are not actually reachable. |
| Health routes | `engine/src/agent33/api/routes/health.py` probes core services and some providers. | Ollama has a basic service ping, but model availability and LM Studio model state are missing. |
| Ollama provider | `engine/src/agent33/llm/ollama.py` supports chat/streaming and internal `list_models()` via `/api/tags`. | Model list is not exposed to frontend setup, and model metadata/load state are thin. |
| Model Connection Wizard | `frontend/src/features/model-connection/ModelConnectionWizardPanel.tsx` supports presets and OpenRouter probe. | OpenRouter is testable; Ollama and LM Studio remain blind setup paths. |
| Provider presets | `frontend/src/features/model-connection/presets.ts` includes Ollama and LM Studio defaults. | Defaults are helpful but hardcoded; users cannot see what is actually running. Ollama also needs base URL normalization because the preset currently uses an OpenAI-compatible `/v1` URL while native Ollama probes use the root URL. |
| Connect Center | `frontend/src/features/connect-center` summarizes engine/model/runtime health from onboarding status. | It lacks explicit local runtime readiness and model availability. |
| Help Assistant | `frontend/src/features/help-assistant` has setup/model targets. | It lacks local runtime recipes for “is Ollama running?”, “what models are available?”, and “why is LM Studio not detected?”. |

## External runtime facts

| Runtime | Relevant current API behavior | Design consequence |
| --- | --- | --- |
| Ollama | Official API docs list `/api/tags` for local models, `/api/ps` for running models, `/api/version` for version checks, `/api/chat`, `/api/generate`, and `/api/embed` style operations. See [Ollama API docs](https://github.com/ollama/ollama/blob/main/docs/api.md). | Wave 8 should probe `/api/version` for identity and `/api/tags` for model availability; optional running-model state can follow via `/api/ps`. |
| Ollama browser CORS | Browser calls from a separate localhost frontend can fail unless `OLLAMA_ORIGINS` permits that origin. | Treat CORS as a user-facing readiness state. Do not silently label it as “not installed.” Prefer backend/server-side probes where available. |
| LM Studio | Current LM Studio docs list OpenAI-compatible endpoints including `GET /v1/models`, `POST /v1/responses`, `POST /v1/chat/completions`, `POST /v1/embeddings`, and `POST /v1/completions`. See [LM Studio OpenAI-compatible endpoints](https://lmstudio.ai/docs/app/api/endpoints/openai). | Wave 8 only needs to probe `/v1/models` and reuse OpenAI-compatible request shapes; it does not need to implement Responses API support to complete readiness detection. |
| LM Studio headless | Current LM Studio docs describe `llmster` as the recommended GUI-less daemon and use `lms daemon up` / `lms server start` commands for daemon/server startup; JIT loading affects whether `/v1/models` lists all downloaded models or only loaded models. See [LM Studio headless docs](https://lmstudio.ai/docs/app/api/headless). | UI copy must distinguish “server not running,” “server running with no model loaded,” and “model can be JIT loaded.” |

## Wave 8 implementation sequence

| Slice | Priority | Scope | Acceptance |
| --- | --- | --- | --- |
| W8-1 Ollama model list and status | P0 | Add backend route(s) that expose Ollama reachability and available local models using the existing provider/client. Wire the wizard to populate Ollama model choices and show a clear not-running/CORS/setup state. | Selecting the Ollama preset shows a live model list or a specific “Ollama is not reachable at this URL” explanation. |
| W8-2 LM Studio detection | P0 | Add a small LM Studio/OpenAI-compatible detector around `GET /v1/models`, then wire the wizard to show detected models and loaded/JIT state guidance. | Selecting the LM Studio preset shows detected model IDs or “start LM Studio server / load a model” guidance. |
| W8-3 Unified model health | P0 | Extend health/readiness output with model availability for required/default local providers without over-failing optional providers. | `/health` reports local provider service and model availability separately; `/readyz` only fails when a required default model is unavailable. |
| W8-4 Probe fallback chain | P1 | Add a deliberate “test fallback chain” flow that tries selected local providers before OpenRouter and explains each result. | User sees the chain result, including the first usable runtime and skipped/failed alternatives. |
| W8-5 Help Assistant setup recipes | P1 | Add local runtime recipes for Ollama running checks, model pulls, LM Studio server startup, CORS, and common failure messages. | Searching “how do I connect Ollama?” or “LM Studio not showing model” returns actionable setup guidance. |
| W8-6 Runtime discovery service | P2 | Add conservative discovery from configured URLs and known defaults only after user intent; avoid broad localhost port scanning. | The wizard can show “detected” badges for configured/default local runtimes without probing arbitrary ports. |

## Implementation constraints

1. Probe only explicit or known default URLs (`localhost:11434`, `localhost:1234`, configured env/base URLs); do not scan arbitrary local ports.
2. Use short timeouts and cache probe results briefly so typing in the wizard does not create repeated local requests.
3. Never send API keys, project content, prompts, or secrets to a local runtime during readiness checks; model-list/version probes only.
4. Display CORS and browser-reachability failures as separate setup issues when the frontend probe cannot access a server the backend may be able to reach.
5. Do not automatically pull or download models in Wave 8; provide copyable commands and explicit next actions instead.
6. Keep OpenRouter probe behavior intact and avoid making cloud provider setup depend on local runtime availability.
7. Normalize local runtime base URLs only where that matches current provider client behavior. Ollama native checks should use the root URL, such as `http://localhost:11434`, while LM Studio should stay on the current OpenAI-compatible base URL, such as `http://localhost:1234/v1`, unless Wave 8 also changes the OpenAI-compatible client to append `/v1` internally and migrates existing saved URLs safely. Avoid duplicate suffixes such as `.../v1/v1` when a user starts from an existing preset.
8. Add focused tests for success, timeout, malformed response, missing model, “server up but no model loaded,” and local base URL normalization states.

## Stop and continue gates

Continue when a slice keeps the beginner path simple: select provider, see detected status, choose a model, test safely, save with confidence.

Pause if a change pushes raw URLs or provider internals into the primary UI, hides setup failures behind generic “unavailable” copy, broadens localhost probing, stores secrets in logs/state, or makes model downloads automatic.

## Canonical references

- `docs/research/wave2-r5-provider-setup-v2.md`
- `docs/research/wave2-r10-helper-llm-pilot.md`
- `docs/research/session116-p3-runtime-compatibility-scope.md`
- `docs/research/provider-auth-policy-migration-2026-02-25.md`
- `docs/research/hooks-mcp-plugin-architecture-research.md`
- `engine/src/agent33/llm/ollama.py`
- `engine/src/agent33/api/routes/health.py`
- `frontend/src/features/model-connection/ModelConnectionWizardPanel.tsx`
- `frontend/src/features/model-connection/presets.ts`
