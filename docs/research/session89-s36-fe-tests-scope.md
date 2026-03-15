# S36: Frontend Test Matrix Expansion

**Session**: 89
**Slice**: S36
**Status**: Complete
**Date**: 2026-03-15

## Objective

Expand frontend test coverage across major components. Session 82 identified
AuthPanel, GlobalSearch, HealthPanel, and ObservationStream as under-tested.
This slice closes those gaps and adds first-time coverage for previously
untested components.

## Baseline

Before this slice, the frontend had **27 test files** with **219 tests**.

## Deliverables

### Expanded existing test files (4 files, +28 tests)

| File | Before | After | New tests |
|------|--------|-------|-----------|
| `components/AuthPanel.test.tsx` | 5 | 11 | Login body validation, loading state, network error, empty token response, whitespace-only token, no-error-box rendering |
| `components/GlobalSearch.test.tsx` | 5 | 9 | Empty query skip, loading state, token/match metadata display, disabled input without token |
| `components/HealthPanel.test.tsx` | 5 | 9 | Configured status icon, overall card rendering, no-services graceful handling, API call verification |
| `components/ObservationStream.test.tsx` | 6 | 11 | A2A subordinate event, AST extraction event, fetch rejection handling, non-ok response handling, timestamp rendering |

### New test files (5 files, +53 tests)

| File | Tests | Coverage scope |
|------|-------|----------------|
| `components/DomainPanel.test.tsx` | 11 | Title/description rendering, operation card rendering, filter by title/path/description, case-insensitive filter, clear filter, SecurityDashboard conditional rendering, ImprovementCycleWizard conditional rendering |
| `features/chat/ChatInterface.test.tsx` | 14 | Initial greeting, message input, send message + reply display, input clear, loading indicator, 401 error, 500 error, network error, Enter key send, empty input guard, system message hiding, settings popover open/close, auth credential passthrough |
| `features/sessions/Dashboard.test.tsx` | 9 | Heading/description, empty state, no-token guard, fetch + display sessions, refresh button, loading state, fetch error graceful handling, session ID rendering, missing ID fallback |
| `features/integrations/MessagingSetup.test.tsx` | 11 | Heading, all 4 platform cards, platform descriptions, connect buttons, Telegram/Discord/Signal/iMessage input, save alert, password vs text input types |
| `features/self-evolution/Dashboard.test.tsx` | 8 | Heading, action buttons, empty PR state, mock PR loading, merge/reject buttons, audit trigger with auth, no-token guard, PR description/branch display |

## Test totals

- **Before**: 27 files, 219 tests
- **After**: 32 files, 291 tests
- **Delta**: +5 files, +72 tests

## Patterns used

- `vi.hoisted()` + `vi.mock()` for module-level mock hoisting (apiRequest)
- `vi.stubGlobal("fetch", ...)` for components using raw fetch
- `userEvent.setup()` for realistic user interaction simulation
- `waitFor()` for async state assertions
- Component harness pattern (wrapping controlled components with state)
- `Element.prototype.scrollIntoView = vi.fn()` for jsdom scrollIntoView gap
- `vi.mock()` for child components in DomainPanel (OperationCard, SecurityDashboard, ImprovementCycleWizard)

## Components still without dedicated tests

These components were assessed and deemed lower priority for this slice:

- `features/modules/Dashboard.tsx` (ModulesDashboard) - Simple list/table, follows same pattern as SessionsDashboard
- `features/tasks/Dashboard.tsx` (TasksDashboard) - Simple list, follows same pattern
- `features/outcomes/Dashboard.tsx` (OutcomesDashboard) - Trends display with improvement trigger
- `components/WorkflowStatusNode.tsx` - Pure function (`statusToColor`) already tested in WorkflowGraph.test.ts; the React component wraps ReactFlow's Handle/Position which requires full ReactFlow mock infrastructure

## Anti-corner-cutting checklist

- [x] Every test asserts on behavior that would catch a real regression
- [x] No placeholder values or TODO comments shipped
- [x] No assertions on two possible outcomes (each assertion checks one specific expected value)
- [x] Mock infrastructure built where needed (scrollIntoView, speechSynthesis, child components)
- [x] All 291 tests pass on `vitest run`
