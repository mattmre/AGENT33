# Wave 2 Round 5 - Provider setup v2

## Goal

Round 5 deepens the model setup experience so a beginner can pick a provider path before seeing raw endpoint fields. The target is a PR-sized frontend upgrade to the existing Model Connection Wizard: one-click OpenRouter, Ollama, LM Studio, and custom OpenAI-compatible presets; clear local-vs-cloud copy; capability labels; and a workflow catalog handoff after testing.

## Panel critique synthesis

- Layperson users do not know whether they need a cloud key, a local server, or a custom endpoint. Provider choice must be the first visible decision, not a buried base URL field.
- A model list without labels does not answer the beginner question: "Which one should I choose?" Cards need compact labels such as "Best for coding", "Free option", "Long context", and "Runs locally".
- Local paths must be explicit that AGENT-33 is not downloading a model by itself. Ollama and LM Studio require their local server to be running before the test button can succeed.
- The safest implementation is frontend-first. The existing save/probe payloads already accept base URL and model fields, so this slice should avoid new backend endpoints and stay compatible with current config keys.
- The next user action should be obvious: test the connection, then open the workflow catalog.

## Competitive patterns reviewed

- Open WebUI and AnythingLLM make local model setup approachable by placing Ollama and custom OpenAI-compatible endpoints near the top of setup.
- Dify, Flowise, Langflow, and n8n use provider cards before advanced settings, reducing intimidation from raw fields.
- OpenHands and agent workbench tools emphasize a "test connection" step before letting users run tasks.
- AutoGen Studio and LangGraph-style tools still assume too much provider knowledge; AGENT-33 can win by combining provider presets with outcome workflow handoff.

## Implementation decision

Implement provider presets as typed frontend constants and small presentational components:

1. `presets.ts` owns provider setup paths and recommended models.
2. `capabilityLabels.ts` computes compact labels from model metadata or preset recommendations.
3. `ProviderPresetSelector` renders "Step 0" provider cards.
4. `ModelCapabilityBadges` renders labels on recommended and catalog models.
5. `ModelConnectionWizardPanel` reuses existing save/probe helpers and changes only form defaults when a preset is selected.

## Out of scope for this PR

- Live Ollama or LM Studio discovery.
- New backend health endpoints.
- Secret storage changes.
- Automatic model download.

Those should follow after the frontend path proves understandable.
