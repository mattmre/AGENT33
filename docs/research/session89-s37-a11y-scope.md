# S37: Accessibility Audit and Fixes - Scope Document

**Session**: 89
**Slice**: S37
**Date**: 2026-03-15

## Objective

Comprehensive accessibility (a11y) audit and remediation of the AGENT-33
frontend. The goal is to ensure all interactive elements are usable by keyboard
users and screen reader users, following WCAG 2.1 AA guidelines where
applicable.

## Audit Findings

### Critical Issues Fixed

1. **No skip navigation link** - Keyboard users had to tab through all nav
   elements on every page load. Fixed by adding a `SkipLink` component.

2. **No main content landmark** - Screen readers could not identify the
   primary content area. Fixed by adding `id="main-content"` and `role="main"`.

3. **Color-only status indicators** - Health status (green/red/yellow dots),
   operation results, and activity log entries conveyed meaning through color
   alone. Fixed by adding `sr-only` text and `role="img"` with `aria-label`.

4. **Missing form labels** - GlobalSearch input had no label or `aria-label`.
   Chat textarea had no accessible name. Translation selects had no associated
   labels. Fixed with appropriate `aria-label` and `aria-labelledby` attributes.

5. **Emoji-only buttons** - Microphone, translate, speak, replay, stop, and
   settings buttons used only emoji as their label. Screen readers would
   announce gibberish. Fixed with `aria-label` and `aria-hidden="true"` on the
   emoji spans.

6. **Non-focusable interactive elements** - OperationsHub process items and
   OutcomesDashboard trend cards were clickable `<article>` elements with no
   keyboard access. FindingsTable rows had click handlers but no `tabIndex` or
   `onKeyDown`. Fixed by adding `tabIndex={0}`, `role="button"`, and Enter/Space
   key handlers.

7. **No focus indicator** - The CSS globally suppressed `outline: none` on
   inputs/textareas. Keyboard users had no visible focus ring. Fixed by adding
   `*:focus-visible` rule with `outline: 2px solid var(--accent)`.

### Moderate Issues Fixed

8. **Missing navigation labels** - Main nav and domain nav lacked `aria-label`.
   Fixed with descriptive labels.

9. **No `aria-current` on active tabs** - Screen readers could not identify
   which tab was selected. Fixed with `aria-current="page"`.

10. **Decorative elements not hidden** - Logo orb, card icons in MessagingSetup,
    and emoji characters in buttons were read by screen readers. Fixed with
    `aria-hidden="true"`.

11. **Missing `role="alert"` on error messages** - Error states in AuthPanel,
    HealthPanel, OperationCard, OperationsHubPanel, OutcomesDashboardPanel, and
    SecurityDashboard were not announced. Fixed with `role="alert"`.

12. **Settings popover lacks dialog semantics** - Chat settings modal had no
    `role="dialog"` or `aria-label`. Fixed.

13. **Missing `aria-expanded` on toggle buttons** - CitationCard expand toggle
    and chat settings button did not communicate open/closed state. Fixed.

14. **Missing `aria-sort` on sortable table headers** - FindingsTable headers
    were clickable but did not communicate sort direction. Fixed with `aria-sort`
    and keyboard handlers.

15. **Audio visualizer not hidden** - Decorative bars in the voice panel were
    read by screen readers. Fixed with `aria-hidden="true"` and `role="status"`.

16. **SVG sparklines lack accessible name** - Trend sparkline SVGs had no
    `role="img"` or `aria-label`. Fixed.

17. **Fact-check status badge** - ExplanationView badge had no accessible
    context. Fixed with `role="status"` and `aria-label`.

18. **Workflow node status** - WorkflowStatusNode used color-only borders to
    indicate step status. Fixed with `role="group"` and `aria-label` combining
    node name and status.

## Components Created

| File | Purpose |
|------|---------|
| `frontend/src/components/SkipLink.tsx` | Skip-to-main-content link for keyboard users |
| `frontend/src/components/VisuallyHidden.tsx` | Screen-reader-only text utility (`sr-only` class) |

## Components Modified

| File | Changes |
|------|---------|
| `frontend/src/App.tsx` | SkipLink, `id="main-content"`, `role="main"`, `aria-current`, nav labels, `aria-hidden` on logo, sr-only on status |
| `frontend/src/components/GlobalSearch.tsx` | `role="search"`, `aria-label` on input, close button, results region |
| `frontend/src/components/HealthPanel.tsx` | `role="img"` + `aria-label` on status icons, `aria-hidden` on emoji, `role="alert"` on error |
| `frontend/src/components/ObservationStream.tsx` | `role="log"`, `aria-live`, `aria-hidden` on emoji |
| `frontend/src/components/OperationCard.tsx` | `aria-label` on Run button, sr-only on status, `aria-hidden` on health emoji, `role="alert"` on errors |
| `frontend/src/components/ExplanationView.tsx` | `role="status"` + `aria-label` on fact-check badge |
| `frontend/src/components/WorkflowStatusNode.tsx` | `role="group"` + `aria-label`, `role="status"` on badge |
| `frontend/src/features/chat/ChatInterface.tsx` | `role="log"` on messages, `aria-label` on textarea/buttons, `aria-pressed`/`aria-expanded`, `role="dialog"`, `aria-hidden` on emoji, `aria-labelledby` on selects |
| `frontend/src/features/voice/LiveVoicePanel.tsx` | `aria-label` on connect button, `aria-hidden` on visualizer bars, `role="status"` |
| `frontend/src/features/integrations/MessagingSetup.tsx` | `aria-hidden` on decorative card icons |
| `frontend/src/features/operations-hub/OperationsHubPanel.tsx` | Keyboard support on process items, `role="alert"` on errors |
| `frontend/src/features/outcomes-dashboard/OutcomesDashboardPanel.tsx` | Keyboard support on trend cards, `role="img"` on SVG, `role="alert"` on errors |
| `frontend/src/features/security-dashboard/SecurityDashboard.tsx` | `role="alert"` on error |
| `frontend/src/features/security-dashboard/FindingsTable.tsx` | `aria-sort` on headers, keyboard handlers, `aria-expanded` on rows, `aria-label` on table |
| `frontend/src/features/research/CitationCard.tsx` | `aria-expanded` on toggle, `aria-hidden` on trust color dot |
| `frontend/src/styles.css` | `.sr-only`, `.skip-link`, `*:focus-visible` CSS rules |

## Tests Created

| File | Test Count | Coverage |
|------|-----------|----------|
| `frontend/src/components/__tests__/Accessibility.test.tsx` | 30 tests | SkipLink, VisuallyHidden, App landmarks, nav labels, aria-current, GlobalSearch a11y, ChatInterface a11y, HealthPanel a11y, OperationsHub keyboard, MessagingSetup icons, heading hierarchy, FindingsTable a11y, CitationCard a11y |

## Existing Tests Updated

| File | Change |
|------|--------|
| `frontend/src/components/OperationCard.test.tsx` | Updated Run button queries to match new `aria-label` pattern |
| `frontend/src/components/GlobalSearch.test.tsx` | Updated close button query to match new `aria-label` |
| `frontend/src/features/voice/LiveVoicePanel.test.tsx` | Updated Connect/Disconnect button queries to match new `aria-label` patterns |

## Verification

- 321 tests pass across 33 test files (30 new + 291 existing)
- TypeScript: 0 errors (`tsc --noEmit`)
- No visual behavior changes -- only ARIA attributes and CSS utilities added
