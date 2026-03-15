# S35: Citation Card Rendering for Web Research

**Session:** 89
**Slice:** S35
**Branch:** `codex/session89-s35-citations`
**Status:** Complete

## Summary

Adds frontend citation card components for rendering web research results
returned by the `/v1/research/search` API. The components provide visual trust
indicators, provider badges, sort controls, and grouped views for web research
citations.

## Deliverables

### New Files

| File | Purpose |
|------|---------|
| `frontend/src/features/research/CitationTypes.ts` | TypeScript types matching backend `WebResearchCitation` / `WebResearchResult` models, plus trust-level display mapping utilities |
| `frontend/src/features/research/CitationCard.tsx` | Card component for a single citation with trust indicator, provider badge, snippet, expandable preview |
| `frontend/src/features/research/CitationList.tsx` | List component with sort controls (relevance/trust/date), group-by-provider toggle, empty state |
| `frontend/src/features/research/ProviderBadge.tsx` | Provider name badge with color-coded styling per known provider |
| `frontend/src/features/research/__tests__/CitationCard.test.tsx` | 30 tests covering all components and utility functions |

### Modified Files

| File | Change |
|------|--------|
| `frontend/src/features/research/Dashboard.tsx` | Added tabbed UI with "Memory Search" and "Web Research" tabs; web research tab calls `/v1/research/search` and renders results via `CitationList` |

## Architecture Decisions

### Trust Level Alignment

The task spec proposed `trust_level: 'high' | 'medium' | 'low' | 'unknown'`,
but the backend `ResearchTrustLevel` enum uses `search-indexed`, `fetch-verified`,
and `blocked`. The TypeScript types match the backend exactly. A
`trustLevelToDisplayTier()` mapping translates backend values to visual tiers
(high/medium/low) for color-coding:

- `fetch-verified` -> high (green) -- content was actually retrieved
- `search-indexed` -> medium (yellow) -- appeared in search index only
- `blocked` -> low (red) -- fetch was blocked by policy

### Component Patterns

Components follow existing frontend conventions:
- Inline styles (consistent with SecurityDashboard, ToolCatalogPage, etc.)
- `data-testid` attributes for test targeting
- `vi.stubGlobal("fetch", ...)` pattern for API mocking in tests
- Factory functions (`buildCitation`, `buildResult`) for test data construction

### Dashboard Integration

The existing `ResearchDashboard` was a memory-search-only component. Rather than
creating a separate dashboard, a tab switcher was added to let users toggle
between "Memory Search" (existing RAG vector search) and "Web Research" (new
grounded web research via citation cards). The web research tab calls the
`/v1/research/search` endpoint and renders results through `CitationList`.

## Test Coverage

30 tests across 5 describe blocks:

- **CitationTypes utilities** (4): display tier mapping, labels, sort comparator
- **ProviderBadge** (4): known providers, unknown fallback, case-insensitive lookup, styling
- **CitationCard** (12): title link, display URL, provider badge, trust indicators for all 3 levels, snippet presence/absence, published date, missing optional fields, expand/collapse toggle, border color
- **CitationList** (10): empty state, multiple cards, singular count, sort by trust level, group by provider toggle, initial sortBy prop, initial groupByProvider prop, snippet passthrough

## Verification

```
vitest run: 27 files, 219 tests passed (30 new)
tsc --noEmit: 0 errors
```
