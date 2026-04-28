# Wave 5 Implementation Reality Audit

## Scope

This audit reviews the merged Wave 4 cockpit work on `origin/main` at `759856e`.
It covers PRs #466-#474:

1. Navigation registry extraction.
2. Cockpit sidebar shell.
3. Primary/secondary navigation split.
4. Workspace/session selector.
5. BridgeSpace-style task board and agent roster.
6. Cockpit permission mode control.
7. Operations dashboard and artifact drawer scaffold.
8. Shipyard lane scaffold.
9. Cockpit deep-link and responsive pass.

Wave 5's job is not to reopen the Wave 4 shell work. It is to establish what is real, what is still scaffold, and what Wave 6 should implement next so the cockpit becomes useful for a beginner instead of only better organized.

## Executive assessment

Wave 4 succeeded at changing the product shape from a sprawling tab row into a cockpit foundation. It added a visible workspace context, demoted advanced/tooling surfaces, introduced beginner-readable permission modes, created BridgeSpace-inspired task and role lanes, added an artifact/review drawer, and made the major cockpit state shareable through URL params.

The implementation is still mostly a shell. The most important user-facing gap is that the cockpit does not yet bind task lanes, artifact sections, permission choices, or completion state to real run/session data. A layperson can see the intended operating model, but cannot yet trust it as the place where work actually moves from idea to plan to execution to review to done.

Wave 6 should therefore avoid more navigation polish and focus on artifact/review usefulness: typed artifact view models, command blocks, mailbox/activity events, dashboard artifact cards, review drawer v2, and clear done states.

## What Wave 4 achieved

### Navigation and cockpit shell

- `frontend/src/data/navigation.ts` now centralizes tab IDs, labels, groupings, primary nav items, and type guards.
- `frontend/src/components/AppNavigation.tsx` renders a primary cockpit section and collapsible tool groups.
- Existing feature panels remain reachable, but the user is no longer forced to parse every surface as a top-level choice.
- App-level tests cover tab registry completeness, primary/secondary split, active tab marking, and Help Assistant compatibility.

### Workspace/session context

- `frontend/src/data/workspaces.ts` defines four starter workspace templates:
  - Solo Builder.
  - Research + Build.
  - Test + Review.
  - Multi-Agent Shipyard.
- `WorkspaceSessionSelector` exposes workspace switching with plain-language goals, counts, and actions.
- Selected workspace is persisted in `sessionStorage` and is also represented in cockpit URL state.

### Task board and agent roster

- `frontend/src/data/workspaceBoard.ts` defines beginner-readable task lanes:
  - Todo.
  - Running.
  - Review.
  - Complete.
  - Blocked.
- `WorkspaceTaskBoard` groups tasks by status and shows a compact agent roster.
- Workspace counts are aligned with board data.

### Permission model

- `frontend/src/data/permissionModes.ts` defines the visible cockpit permission ladder:
  - Observe only.
  - Ask before action.
  - Auto within workspace.
  - PR-first implementation.
  - Restricted / high-risk locked.
- `PermissionModeControl` makes allowed actions, review gates, and Beginner/Pro compatibility visible.
- Invalid mode selection now throws explicit errors instead of failing silently.

### Dashboard, artifact drawer, and shipyard lanes

- `CockpitProjectDashboard` gives the Operations surface a workspace summary, task attention count, recommended next action, safety gate, and placeholder artifact cards.
- `ArtifactReviewDrawer` provides sections for Plan, Command Blocks, Logs, Tests, Risks, Approval, Activity/Mailbox, and Outcome.
- `frontend/src/data/artifactDrawerSections.ts` is the shared source of truth for drawer sections and URL validation.
- `ShipyardLaneScaffold` introduces role-based Coordinator, Scout, Builder, and Reviewer lanes.
- Drawer tabs use ARIA tab semantics, roving `tabIndex`, Arrow/Home/End keyboard support, and controlled state from `App`.

### Deep links and browser navigation

- `frontend/src/lib/cockpitUrlState.ts` supports typed URL state for:
  - `view`.
  - `workspace`.
  - `permission`.
  - `drawer`.
- Invalid params fall back safely.
- Browser back/forward restores the major cockpit state.
- Drawer state is only retained in URLs for the Operations view.

## Implementation gaps

### P0 gaps

| Gap | Evidence | User impact | Wave 6 action |
| --- | --- | --- | --- |
| Artifact drawer is still mostly static | Drawer bodies are static section descriptions from `artifactDrawerSections.ts` | Users cannot inspect real plans, commands, tests, logs, risks, approvals, or outcomes | Add typed artifact adapters and render real/demo artifact cards per workspace/session |
| Task board is not connected to execution | `workspaceBoard.ts` is static frontend data | Lanes explain a workflow but do not move when work runs | Add adapter layer from existing Operations/session data into workspace task cards |
| Permission mode is descriptive, not enforcing UI behavior | Permission selection changes copy and tone, but does not gate action buttons | Users may think a safety mode changes allowed actions when it does not | Add permission-gated action affordances for Observe, Ask, Workspace, PR-first, and Restricted |
| Done state is not operational | Dashboard says no PR/package linked and drawer outcome is static | Users do not know whether work ended as PR ready, artifact package ready, or blocked | Add completion model and outcome cards |
| Operations Hub remains separate from cockpit primitives | `OperationsHubPanel` still receives token/apiKey and renders below cockpit scaffolds | Cockpit can feel like a wrapper around old panels instead of the operating system | Adapt Operations data into the dashboard, board, drawer, and timeline |

### P1 gaps

| Gap | Evidence | User impact | Wave 6 action |
| --- | --- | --- | --- |
| Root app still owns too much cross-cutting state | `App.tsx` manages active tab, workspace, permission, drawer section, auth, activity, workflow draft, role, legacy domain | Future artifact/session work will increase prop threading and coupling | Extract cockpit state hooks and introduce context only where repeated prop threading becomes costly |
| API/data adapter seam is missing for cockpit artifacts | New cockpit data is static and feature APIs remain panel-specific | Every feature will need one-off mapping into the cockpit | Create `artifactModels` / `workspaceArtifactAdapters` instead of immediately adding backend schema |
| Help Assistant is not context-aware for new cockpit surfaces | Help drawer remains mounted but not supplied with workspace/task/drawer context | Beginners still need guidance for new cockpit concepts | Add help topics for permission modes, task lanes, drawer sections, and workspace templates |
| Responsive behavior is improved but not proven deeply | CSS has narrow-screen drawer tab scrolling and shipyard stacking, but no viewport-level automated coverage | Mobile users may still hit wide controls and dense cards | Add targeted responsive smoke tests or manual validation checklist |
| Accessibility coverage is still partial | Drawer tabs are strong, but full cockpit keyboard path and sidebar/mobile behavior need more coverage | Keyboard and screen-reader confidence remains incomplete | Add integration-level a11y tests for Operations cockpit path |

### P2 gaps

| Gap | Rationale | Wave 6+ action |
| --- | --- | --- |
| Dynamic navigation registry | Static registry is acceptable for current scope; plugin/dynamic nav is not needed yet | Revisit when marketplace/workflow packs need nav registration |
| Workspace-scoped auth | Current workspace model is frontend-only; token/API scoping would be premature without backend workspace semantics | Defer to Agent OS/runtime or backend workspace phases |
| Full router migration | Query-state helper works for current cockpit needs | Consider React Router/TanStack Router only if route complexity grows |
| Drag/drop task board | Useful later, but could distract from artifact review substance | Defer until task cards are backed by real state |

## Architecture findings

### Accurate current architecture

- Wave 4 does have centralized nav data in `data/navigation.ts`.
- Wave 4 does have frontend workspace/session data in `data/workspaces.ts`.
- Wave 4 does have permission mode definitions in `data/permissionModes.ts`.
- Wave 4 does have cockpit URL state in `lib/cockpitUrlState.ts`.
- Wave 4 does not yet have a backend workspace model, artifact API, command-block API, or event/mailbox API.
- Wave 4 intentionally uses static/demo data for workspace boards and drawer sections.

### Coupling risks

1. `App.tsx` is still the orchestration bottleneck. It owns routing, cockpit state, legacy auth props, activity, workflow starter draft, role intake state, and many direct navigation callbacks.
2. The new cockpit components are composable, but their data models are static. If Wave 6 wires APIs directly into each component, the cockpit will accumulate hard-to-test side effects.
3. Feature APIs use local adapters and local loading/error state. This was acceptable for independent panels, but artifact/review UX needs a shared frontend model that multiple surfaces can render consistently.
4. `styles.css` is very large and continues to collect unrelated feature styles. Wave 6 should avoid broad CSS rewrites but should keep new artifact/review styles grouped and small.

### Recommended seam for Wave 6

Start with frontend view-model adapters, not backend schema:

```ts
type ArtifactKind =
  | "plan"
  | "command"
  | "log"
  | "test"
  | "risk"
  | "approval"
  | "activity"
  | "outcome";

interface CockpitArtifactCard {
  id: string;
  kind: ArtifactKind;
  title: string;
  summary: string;
  status: "ready" | "running" | "needs-review" | "blocked" | "done";
  ownerRole: "Coordinator" | "Scout" | "Builder" | "Reviewer" | "Operator";
  workspaceId: string;
  sourceLabel: string;
  actionLabel?: string;
}
```

Adapters can map existing Operations, workflow, safety, review, and static demo data into these cards. This keeps Wave 6 frontend-only unless existing backend data proves insufficient.

## Module health matrix

| Module | Health | Wave 4 effect | Main risk | Next action |
| --- | --- | --- | --- | --- |
| Cockpit navigation | Strong | Became structured and type-safe | Static nav could grow again if every feature demands primary placement | Preserve primary/secondary split |
| Workspace/session selector | Medium | Added templates and persistence | Frontend-only; not tied to real projects | Add artifact/task adapter keyed by workspace |
| Task board/agent roster | Medium | Clear BridgeSpace-inspired model | Static tasks; no execution lifecycle | Adapt existing run/session state into cards |
| Permission mode control | Medium | Visible and beginner-readable | Not enforcing UI affordances | Add `PermissionGate` or action-gating helper |
| Operations dashboard | Medium | Gives Operations a cockpit summary | Placeholder artifacts and done state | Add artifact cards and outcome state |
| Artifact drawer | Medium-low | Good shell, accessible tabs, URL state | Static copy; no review utility | Implement drawer v2 around real artifact view models |
| Shipyard lanes | Medium | Clear role split | Role state is derived from static tasks only | Bind role lanes to artifact/task ownership |
| Help Assistant | Medium-low | Still available | Not context-aware for new cockpit | Add cockpit-specific help intents |
| Connect/model setup | Medium | Preserved behind nav | Not improved by Wave 4 | Keep for Wave 7 runtime readiness |
| Workflow Catalog/Starter | Medium | Preserved and linked | Still not acting as cockpit template engine | Use in Wave 6 only where artifact adapters need starter labels |
| Agent Builder/Spawner | Medium-low | Preserved behind tools | Not connected to workspace roster or lanes | Defer deeper agent creation until artifact foundation lands |
| Safety Center | Medium | Linked from dashboard/board/lanes | Permission mode and safety queue not unified | Add approval artifacts and permission-gated actions |

## Panel synthesis

### Product/UX reviewer

Truth score: 0.74.

Wave 4 reduced the visible navigation anxiety but did not yet create the "I can safely start work now" moment. The first-run user can choose a workspace and see roles, but most surfaces still say what will happen later rather than showing what happened now.

### Architecture reviewer

Truth score: 0.78.

The implementation is type-safe and PR-sized, with useful extraction of navigation, workspace, permission, drawer, and URL primitives. The next risk is wiring real data straight into UI components. Wave 6 needs adapter/view-model seams before adding more interactivity.

### Governance/safety reviewer

Truth score: 0.70.

Permission mode visibility is a strong improvement. However, the modes are not yet operational policy. Wave 6 should connect permission choices to enabled/disabled actions, approval artifacts, and plain-language explanations before adding more autonomy.

### Beginner operator reviewer

Truth score: 0.66.

The cockpit is easier to scan than the old header, but a layperson still sees many conceptual placeholders. They need recommended next action, visible artifacts, and one clear completion state more than more panes.

## Wave 6 backlog recommendation

### P0

1. **Artifact view-model adapters**
   - Define typed plan, command, log, test, risk, approval, activity, and outcome artifact models.
   - Add tests for valid data, missing optional data, and unknown/empty state.
   - Adapt current static workspace data and any existing Operations/Safety data that can be reused safely.

2. **Artifact timeline/cards on dashboard**
   - Replace placeholder artifact cards with cards from the shared artifact adapter.
   - Include status, owner/source, review state, and next action.

3. **Review drawer v2**
   - Render real section content from the same artifact models.
   - Keep the current accessible tab behavior and URL state.
   - Add empty states that tell beginners what will appear after a run.

4. **Permission-gated cockpit actions**
   - Observe: action buttons become read-only explanations.
   - Ask: actions show approval-required copy.
   - Workspace: low-risk local actions remain visible while high-risk actions explain the gate.
   - PR-first: implementation actions route toward branch/PR workflows.
   - Restricted: only guidance and triage actions remain available.

5. **Clear done state**
   - Every cockpit run/session summary should end as one of:
     - PR ready.
     - Artifact package ready.
     - Blocked with required action.

### P1

1. Add command block models with collapsed summaries, status, duration, redaction state, and linked artifacts.
2. Add mailbox/activity event models for Coordinator, Scout, Builder, Reviewer, and Operator handoffs.
3. Add integration tests for deep link restore, workspace switching, permission mode switching, and drawer section rendering.
4. Add Help Assistant cockpit topics for workspace templates, task lanes, permission modes, and artifact sections.
5. Add a small cockpit state hook to reduce `App.tsx` coupling where it directly improves Wave 6 implementation.

### P2

1. Dynamic workflow/template registration.
2. Workspace-scoped auth tokens.
3. Full router migration.
4. Drag/drop task cards.
5. Multi-tab synchronization.
6. Export cockpit state as Markdown/PDF.

## Explicit Wave 6 non-goals

Wave 6 should not implement:

1. A full IDE or BridgeSpace pane clone.
2. Backend workspace/project schema unless existing frontend adapters hit a documented hard limit.
3. Browser LLM downloads or semantic docs indexing.
4. Marketplace/tool provenance.
5. Dynamic plugin navigation.
6. Drag/drop task orchestration.
7. Workspace-scoped secret management.
8. A complete mobile redesign.

## Acceptance criteria for the next implementation wave

Wave 6 is successful if:

1. The dashboard shows artifact/review state instead of only static placeholder cards.
2. The right drawer is useful for reviewing at least one realistic run/session shape.
3. Command blocks and mailbox/activity events have typed frontend models and tests.
4. Permission mode changes visibly affect cockpit actions.
5. Completion state is clear: PR, artifact package, or blocker.
6. Focused tests, lint, build, PR review, hosted CI, and session tracker updates pass for each slice.
