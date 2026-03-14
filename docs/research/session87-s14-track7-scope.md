# Session 87 S14 Track 7 Scope Lock

Date: 2026-03-14
Branch: `codex/session87-s14-track7`
Worktree: `worktrees/session87-s14-track7`

## Goal

Land the backend-first slice of OpenClaw Track 7 by upgrading AGENT-33's web-grounding layer from a single-provider string tool into a provider-aware research surface with structured results and operator-visible trust metadata.

## Current Baseline

- `engine/src/agent33/tools/builtin/search.py` is still a SearXNG-only tool that returns a formatted text blob instead of structured result objects.
- `engine/src/agent33/tools/builtin/web_fetch.py` exists and already enforces connector-boundary execution plus domain allowlists, but it is not integrated into a richer research result model.
- There is no dedicated provider abstraction for web research providers, no diagnostics surface for provider health/auth state, and no trust/citation model shared between backend and frontend.
- The current `frontend/src/features/research/Dashboard.tsx` is a semantic memory search panel, not a grounded web research UI.

## Included Work

1. Add backend provider abstraction for search/fetch research providers.
2. Define structured web research result models with citation/trust metadata.
3. Extend runtime/operator APIs to expose provider diagnostics and effective capability/auth state.
4. Add the minimum frontend/runtime plumbing needed to render trust labels and citation cards from structured results.
5. Cover the new contracts with focused backend tests and, if UI work lands in this slice, targeted frontend tests.

## Explicit Non-Goals

- Do not fold in Track 8 session catalog or context-engine work.
- Do not rework the existing memory-search / RAG experience beyond what is needed to avoid naming or UX collisions.
- Do not add broad browser automation changes; `browser` remains a separate tool surface.
- Do not expand into generic repo-ingestion or improvement-intake work already tracked elsewhere.

## Recommended Implementation Shape

1. Introduce a shared web-research service layer under `engine/src/agent33/` rather than growing tool logic directly inside the builtin tool modules.
2. Keep the first provider set small:
   - preserve SearXNG as the default search provider
   - wrap `web_fetch`/HTTP retrieval behind the same structured result pipeline
3. Reuse existing trust/provenance patterns from packs where practical, but avoid coupling Track 7 directly to pack-specific models.
4. Land backend contracts first, then only the frontend needed to prove the data model and trust affordances end to end.

## Files Likely In Scope

- `engine/src/agent33/tools/builtin/search.py`
- `engine/src/agent33/tools/builtin/web_fetch.py`
- new `engine/src/agent33/web_research/` package
- new or expanded API routes/models for research results and provider diagnostics
- `frontend/src/features/research/`
- targeted tests under `engine/tests/` and possibly `frontend/src/features/research/`

## Exit Criteria

- Web search/fetch results have a structured model instead of only formatted text.
- Provider identity, auth/config status, and trust semantics are inspectable by operators.
- Citation/trust metadata is available to the UI without ad hoc parsing.
- The slice remains isolated to Track 7 and is ready for a separate PR after implementation and validation.
