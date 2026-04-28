# Wave 2 Round 1 - Help Assistant MVP

## Objective

Give first-time and layperson users an in-app "Ask AGENT33" surface that answers setup and orientation questions without requiring them to understand raw configuration, model IDs, MCP, or workflow internals.

## Panel critique summary

### Pass A - Layperson comprehension

Users need immediate answers to "How do I connect a model?", "How do I start Docker?", and "What should I click first?" before they can benefit from the rest of the platform. The first MVP should be visible everywhere and should answer with steps, not generic documentation links.

### Pass B - Functional workflow depth

The assistant must route users to working UI surfaces: Models, Workflow Catalog, Workflow Starter, Operations Hub, Safety Center, MCP Health, and Advanced only when needed. It should cite where answers came from so users trust it and so future docs drift is easy to detect.

### Pass C - Feasibility and safety

Start with deterministic static search instead of a browser LLM. This avoids model downloads, WebGPU incompatibility, hallucinated setup instructions, and accidental secret handling. The static helper becomes the corpus and UX shell for a later browser/local RAG assistant.

## MVP scope

- Static help corpus in the frontend.
- Deterministic lexical search.
- Cited answers with source files.
- Step-by-step OpenRouter setup answer.
- Docker refresh/start answer.
- First workflow, Beginner/Pro, and MCP/tool/skill glossary answers.
- Floating drawer available across the app.
- Navigation actions into existing beginner surfaces.
- Tests for search ranking and drawer behavior.

## Out of scope for this round

- External model calls.
- Browser model downloads.
- Embedding index generation.
- Backend `/v1/help/ask`.
- Secret validation beyond linking to existing Model Connection Wizard and health surfaces.

## Acceptance criteria

- "How do I connect OpenRouter?" resolves to a cited answer that mentions `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`, and `DEFAULT_MODEL=openrouter/auto`.
- The helper states that the MVP does not call an external model.
- The helper never displays or stores raw secret values.
- The drawer can navigate to Models and Workflow Catalog.
- The feature builds and focused tests pass.
