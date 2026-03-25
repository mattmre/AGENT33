# Session 109 -- Phase 49: Per-Model Pricing Catalog & Effort Router Enhancement

**Date**: 2026-03-25
**Branch**: `feat/phase49-pricing-effort-router`
**Base**: `origin/main` (`9929c0d`)

## Included Work

### 1. Per-Model Pricing Catalog (`engine/src/agent33/llm/pricing.py`)
- `PricingEntry` dataclass with Decimal-based per-million-token costs
- `CostResult` dataclass with amount, status, model, provider, token counts
- `CostSource` and `CostStatus` enums for provenance tracking
- `PricingCatalog` class with multi-tier fallback lookup:
  1. User overrides (exact provider+model)
  2. Builtin table (exact provider+model)
  3. Model-only match (any provider)
  4. Wildcard provider patterns (ollama/*, local/*, airllm/*)
  5. Unknown ($0, status=unknown)
- `estimate_cost()` function for end-to-end cost estimation
- 20 builtin models: Claude Sonnet 4, Claude Opus 4, GPT-4.1 family, GPT-4o
  family, O3/O4-mini, Gemini 2.5/2.0, Mistral Large/Small/Codestral,
  Ollama llama3.2 + nomic-embed-text
- All money values use `Decimal` to avoid floating-point rounding

### 2. Effort Router Fast-Path Pre-Filter
- New `_is_simple_message()` method checks:
  - Char length <= `heuristic_simple_max_chars` (default 160)
  - Char length < `heuristic_medium_payload_chars` (prevents bypassing
    payload-size scoring when thresholds are customized)
  - Word count <= `heuristic_simple_max_words` (default 28)
  - No code fences, no URLs, no complex-task keywords
- Returns LOW with confidence 0.85 and reason `simple_message_fast_path`
- Skipped for iterative mode requests

### 3. Expanded Keyword Categories
- Replaced 6 flat keywords with 9 organized categories (45+ keywords):
  - Debugging, Implementation, Analysis, Architecture, Testing,
    Operations, Security, Incident, Optimization
- Each category contributes +1 to score (multiple keywords in same
  category count only once)
- This is a **behavioral change**: inputs that match multiple categories
  now score higher than before. Two existing test expectations were
  updated to reflect the new scores.

### 4. Pricing Integration in `resolve()`
- New optional `provider` parameter on `resolve()`
- New `_estimate_cost_for_tokens()` helper that:
  1. Tries the pricing catalog when provider is given
  2. Falls back to legacy `cost_per_1k_tokens` flat rate
  3. Returns None if no pricing info available
- Backward compatible: callers that don't pass `provider` get identical
  behavior to before

### 5. Config Fields
- `heuristic_simple_max_chars: int = 160`
- `heuristic_simple_max_words: int = 28`

## Explicit Non-Goals
- No runtime auto-refresh of pricing data from provider APIs
- No changes to API routes or response schemas
- No changes to the lifespan initialization order
- No changes to the ModelRouter class
- No new dependencies added

## Test Coverage
- `tests/test_pricing.py`: 29 tests covering catalog lookup chain,
  cost arithmetic, all 20 builtin models, user overrides, wildcards
- `tests/test_phase30_effort_routing.py`: 26 new tests for fast-path,
  expanded keywords, and pricing integration
- 2 existing tests updated for expanded keyword score changes

## Validation Plan
- `ruff check src/ tests/` -- 0 errors
- `ruff format --check src/ tests/` -- no reformats needed
- `mypy src --config-file pyproject.toml` -- 0 issues
- `pytest tests/test_pricing.py tests/test_phase30_effort_routing.py -x -q`
  -- 109 passed

## Files Modified
- `engine/src/agent33/llm/pricing.py` (new)
- `engine/src/agent33/agents/effort.py` (modified)
- `engine/src/agent33/config.py` (modified)
- `engine/tests/test_pricing.py` (new)
- `engine/tests/test_phase30_effort_routing.py` (modified)
- `docs/research/session109-phase49-pricing-scope.md` (this file)
