# S38: Research Dashboard Web Research Upgrade

## Scope

This slice upgrades the Research Dashboard (partially built in S35 with citation
cards and tabs) by adding provider status monitoring, search history, and
provider diagnostics.

## Deliverables

### Backend

1. **New model: `ProviderStatusInfo`** in `engine/src/agent33/web_research/models.py`
   - Fields: `name`, `enabled`, `status`, `last_check`, `total_calls`, `success_rate`
   - Dashboard-facing slim model derived from the full `ResearchProviderStatus`

2. **New service method: `WebResearchService.provider_status_summary()`**
   - Converts full provider diagnostics into `ProviderStatusInfo` list
   - Located in `engine/src/agent33/web_research/service.py`

3. **New endpoint: `GET /v1/research/providers/status`**
   - Scope: `agents:read` (lower than `tools:execute` used by search/fetch)
   - Returns `list[ProviderStatusInfo]`
   - Located in `engine/src/agent33/api/routes/research.py`

4. **Backend tests: `engine/tests/test_research_provider_status.py`**
   - Model construction and serialization tests
   - Service-level `provider_status_summary()` unit tests
   - API route tests with auth, scope enforcement, response shape validation

### Frontend

5. **New component: `ProviderStatus.tsx`**
   - Fetches from `GET /v1/research/providers/status`
   - Renders each provider with status indicator dot, connected/disconnected badge,
     call count, success rate, and last-check timestamp
   - Refresh button for re-fetching

6. **New component: `SearchHistory.tsx`**
   - Renders recent web search entries from React state (no backend persistence)
   - Shows query text, timestamp, result count, provider used
   - Click-to-rerun button that triggers a new search with the same query

7. **Updated `Dashboard.tsx`**
   - Third tab: "Providers" showing the `ProviderStatus` component
   - Search history panel below the Web Research tab content
   - Provider health indicator dots in the dashboard header (fetched on mount)
   - Shared `doWebSearch()` helper used by both form submit and re-run

8. **Frontend tests**
   - `ProviderStatus.test.tsx`: 13 tests covering fetch, rendering, error states,
     refresh, status colors, empty state
   - `SearchHistory.test.tsx`: 10 tests covering rendering, empty state, re-run
     clicks, pluralization, timestamp formatting

## Dependencies

- Builds on S35 citation cards (`CitationCard.tsx`, `CitationList.tsx`,
  `CitationTypes.ts`, `ProviderBadge.tsx`)
- Uses existing `WebResearchService` and `ResearchProviderStatus` models
- No database changes required

## Testing

- Backend: `python -m pytest tests/test_research_provider_status.py -q`
- Frontend: `npx vitest run --reporter=verbose src/features/research/__tests__/`
