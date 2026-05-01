# Wave 6 Implementation Charter: Artifact, Review, and Coordination

## Source baseline

Wave 6 starts from `origin/main` commit `103fa69` after these Wave 5 artifacts merged:

1. `docs/research/wave5-implementation-audit.md`
2. `docs/research/wave5-competitor-refresh.md`
3. `docs/research/wave5-neglected-module-review.md`

The three artifacts agree on the same product risk: AGENT33 now has the right cockpit shell, but the shell still lacks a shared operational record that connects tasks, commands, approvals, artifacts, and outcomes.

## Charter

### Primary objective

Make the cockpit useful as a beginner-facing review and coordination surface by implementing typed frontend artifact/event models and wiring them into the dashboard, task board, drawer, permission affordances, and done-state summaries.

### Secondary objectives

1. Preserve the BridgeSpace-inspired operating model without copying terminal-pane density.
2. Use adapter seams over backend schema changes unless existing frontend data hits a documented hard limit.

### Non-goals

Wave 6 will not implement:

1. A full IDE, terminal grid, universal canvas, or 16-pane BridgeSpace clone.
2. Backend workspace/project tables.
3. Browser model downloads, embeddings, or local RAG.
4. Marketplace/tool provenance and rollback.
5. Full analytics dashboard overhaul.
6. Full Spawner visual workflow redesign.
7. Enterprise RBAC, multi-user collaboration, or workspace-scoped secrets.
8. Dynamic navigation/plugin routing.

## Skill and governance gate

EVOKORE-MCP workflow discovery was run before chartering. The relevant adopted guidance is:

- Build for workflows, not endpoint wrappers.
- Keep outputs concise and task-oriented.
- Prefer actionable error and blocked-state messages.
- Use evaluation-driven implementation with realistic scenarios.

Rejected for Wave 6:

- MCP server construction work. Wave 6 is frontend artifact/review work, not a new MCP server.
- New external API research. The competitor refresh already captured the relevant market signals.

## Truth-score synthesis

This table uses the session governance scale: 1 = weak/assumptive, 3 = implementation-plausible, 4 = evidence-backed enough for planning, and 5 = reproducible or directly supported by merged code/docs. It is separate from the fractional persona confidence scores used inside the Wave 5 panel writeups.

| Decision | Truth score | Evidence |
| --- | ---: | --- |
| Start with frontend artifact view models instead of backend schema | 5 | All three Wave 5 docs identify cockpit placeholders and recommend adapter seams before backend schema. |
| Make command blocks and activity/mailbox events first-class models | 5 | Competitor refresh and BridgeSpace pattern both call these out as core review primitives. |
| Add permission-gated action affordances in Wave 6 | 4 | Implementation audit and competitor refresh identify descriptive-only permission modes as a trust gap. |
| Defer analytics, Spawner redesign, and marketplace work | 4 | Neglected-module review identifies them as important but not the shared causality layer Wave 6 must build first. |
| Avoid a router/backend migration | 4 | Current URL helper and frontend workspace model are sufficient for Wave 6 scope. |

## Current seams to use

| Area | Current file | Wave 6 use |
| --- | --- | --- |
| Workspace/session templates | `frontend/src/data/workspaces.ts` | Key artifact fixtures/adapters by workspace id. |
| Task board and roles | `frontend/src/data/workspaceBoard.ts` | Attach artifact ids, blockers, owner roles, and review state to task cards. |
| Permission ladder | `frontend/src/data/permissionModes.ts` | Add action-gating definitions and disabled-state copy. |
| Dashboard scaffold | `frontend/src/components/CockpitProjectDashboard.tsx` | Replace placeholder artifacts with model-driven cards. |
| Drawer scaffold | `frontend/src/components/ArtifactReviewDrawer.tsx` | Render section content from artifact/event models while preserving tab accessibility and URL state. |
| Drawer section ids | `frontend/src/data/artifactDrawerSections.ts` | Keep as the section registry and map sections to model filters. |
| URL state | `frontend/src/lib/cockpitUrlState.ts` | Preserve `view`, `workspace`, `permission`, and `drawer` deep links. |
| Operations/session state | `frontend/src/features/operations-hub/OperationsHubPanel.tsx`, `frontend/src/features/sessions/runSummary.ts` | Feed existing process/session evidence into artifacts where the current data shape supports it. |
| Safety approvals | `frontend/src/features/safety-center/SafetyCenterPanel.tsx` | Produce or adapt approval artifacts after shared models exist. |

## Wave 6 P0 backlog

### 1. Artifact view-model adapters

Create typed frontend models for:

- Plan artifacts.
- Command blocks.
- Logs.
- Test/validation evidence.
- Risks/blockers.
- Approval artifacts.
- Activity/mailbox events.
- Outcome artifacts.

Acceptance criteria:

1. Models have stable ids, workspace id, source label, owner role, timestamp, status, review state, and next action where relevant.
2. Adapters can map existing static workspace/task data plus available Operations, Sessions, and Safety data into a realistic artifact set.
3. Unknown or missing input produces explicit empty-state artifacts, not silent success-shaped defaults.
4. Unit tests cover valid data, missing optional data, empty workspace state, and invalid workspace ids.

### 2. Command block models

Represent command/tool execution as collapsible review records with:

- source agent/role,
- command/tool label,
- status and exit state,
- duration,
- redaction state,
- output summary,
- linked task and artifact ids.

Acceptance criteria:

1. Command blocks are typed independently but renderable as artifacts.
2. Test coverage includes success, failure, redacted output, missing duration, and linked artifact/task behavior.

### 3. Mailbox and activity models

Represent coordination events for Coordinator, Scout, Builder, Reviewer, and Operator:

- decisions,
- blockers,
- approvals,
- handoffs,
- review comments,
- validation updates.

Acceptance criteria:

1. Events are typed and filterable by workspace, role, task, artifact, and severity.
2. Mailbox/activity items are not raw chat transcript dumps.
3. Tests cover handoff, blocker, approval, and review-comment events.

### 4. Operations and safety adapter bridge

Adapt existing Operations, Sessions, and Safety evidence into the shared artifact model before dashboard and drawer rendering depend on demo-only data.

Acceptance criteria:

1. Operations/session state can produce at least status, validation, log, or outcome artifacts where existing data supports it.
2. Safety approvals can produce approval artifacts and blocked-task explanations where existing data supports it.
3. Missing backend evidence is represented as an explicit "not available yet" artifact, not as a fake success.
4. Tests cover available evidence, missing evidence, and approval/blocker mapping.

### 5. Dashboard artifact timeline/cards

Replace static dashboard artifact placeholders with model-driven cards.

Acceptance criteria:

1. `CockpitProjectDashboard` shows artifact status, owner/source, timestamp, review state, and next action.
2. Empty states explain what appears after a run.
3. Cards can open the relevant drawer section.
4. Tests cover artifact-rich, empty, blocked, and completed workspace states.

### 6. Right review drawer v2

Render useful content for Plan, Command Blocks, Logs, Tests, Risks, Approval, Activity/Mailbox, and Outcome from shared models.

Acceptance criteria:

1. Existing ARIA tab behavior, keyboard support, URL state, and mobile scroll behavior remain intact.
2. Each section renders model-driven content or an explicit useful empty state.
3. Command blocks and activity/mailbox events use their typed models after the command/activity model slices have merged; until then, sections must show explicit empty states rather than placeholders that imply live execution.
4. Tests cover section rendering, keyboard navigation, controlled state, empty sections, and invalid drawer URL fallback.

### 7. Permission-gated cockpit actions

Turn permission mode from descriptive copy into visible action affordances.

Acceptance criteria:

1. Observe mode makes run/change buttons read-only with explanatory copy.
2. Ask mode marks action buttons as approval-required.
3. Workspace mode distinguishes low-risk local actions from high-risk gated actions.
4. PR-first mode routes implementation actions toward branch/PR review copy.
5. Restricted mode leaves only guidance and triage actions available.
6. Tests cover action-state output for every permission mode.

### 8. PR/artifact/blocker done state

Every session/run summary should end in a beginner-readable state:

- PR ready.
- Artifact package ready.
- Blocked with required action.

Acceptance criteria:

1. Dashboard and drawer show the same outcome state for the same workspace/session.
2. Demo/mock outcome state is clearly labeled.
3. Blocked outcome includes who/what unblocks it.
4. Tests cover PR-ready, package-ready, blocked, and no-run states.

### 9. Neglected-module P0 hardening guardrails

Close the highest-risk neglected-module issues without derailing the artifact/review focus.

Acceptance criteria:

1. Incomplete messaging integrations are removed, clearly demoted to "coming soon," or routed to the real model/provider setup path; they must not show fake connection success.
2. Improvement Loops gets main-panel test coverage for preset switching, one-click launch, cadence display, API failures, and credential gates.
3. Spawner gets frontend test coverage for its existing empty state, create workflow path, child agent validation, execution tree status, error display, and no-token states.
4. Spawner work remains test/coverage hardening only; agent discovery, safe defaults, examples, abort/recovery, and visual workflow redesign remain later-wave candidates.

## P1 backlog

1. Help Assistant topics for workspace templates, task lanes, permissions, drawer sections, and done states.
2. Targeted accessibility tests for cockpit dashboard-to-drawer flow.
3. Responsive smoke coverage or a documented manual checklist for drawer/card behavior.
4. Follow-up setup recovery copy for Connect Center and MCP Health.
5. Tool Fabric "use this" or "compose this" affordance after discovery.

## P2 backlog

1. Pack Marketplace install progress, uninstall, rollback, and prerequisite states.
2. Outcomes/Impact dashboard interpretation and drill-down.
3. Runtime/provider readiness blockers surfaced in cockpit.
4. Workspace template configurations that seed starter tasks.
5. Role-intake "not sure" quiz and richer complex-project follow-up.

## PR sequence

Each slice must use a fresh worktree from latest `origin/main`, open one PR, resolve review comments, wait for hosted CI, merge, and update the session tracker before the next slice.

| Sequence | Slice | Primary files | Why this order |
| ---: | --- | --- | --- |
| 1 | Artifact view-model adapters | new `frontend/src/data/cockpitArtifacts.ts`, tests | Foundation for dashboard, drawer, outcome, safety, and task-board wiring. |
| 2 | Command block models | `cockpitArtifacts.ts` or `frontend/src/data/commandBlocks.ts`, tests | Command evidence is core to BridgeSpace-style review and drawer content. |
| 3 | Mailbox/activity models | `cockpitArtifacts.ts` or `frontend/src/data/cockpitActivity.ts`, tests | Coordination events power activity/mailbox and lane handoffs. |
| 4 | Operations and safety adapter bridge | operations/session/safety adapters, tests | Prevents dashboard/drawer work from becoming demo-only artifact theater. |
| 5 | Dashboard artifact timeline/cards | `CockpitProjectDashboard.tsx`, dashboard tests, small CSS additions | Replaces the most visible placeholders after models and adapters exist. |
| 6 | Review drawer v2 | `ArtifactReviewDrawer.tsx`, drawer tests, `artifactDrawerSections.ts` if needed | Makes the right drawer useful without breaking current deep links. |
| 7 | Permission-gated cockpit actions | `permissionModes.ts`, new action-gate helper, cockpit/dashboard/task-board tests | Converts permission labels into visible behavior after action targets exist. |
| 8 | PR/artifact/blocker done state | artifact outcome adapters, dashboard/drawer/task-board tests | Gives every session a clear completion or blocker state. |
| 9 | Neglected-module P0 hardening | Messaging Setup, Improvement Loops tests, Spawner tests | Closes P0 trust/coverage gaps without taking over the artifact wave. |
| 10 | Observability and quality pass | focused tests, a11y coverage, docs touch-ups only as needed | Tightens trace/timing/validation/status coverage after behavior lands. |

## Rotation and scope-control rules

1. Do not add new primary navigation items in Wave 6.
2. Do not redesign the whole cockpit shell.
3. Do not start a backend schema unless a PR documents the frontend adapter hard limit first.
4. If a slice expands beyond the files listed above, split it into a follow-up PR.
5. If a module-specific P1/P2 item becomes urgent, land it after the shared model/drawer/dashboard foundation, not before.

## Verification plan

Every implementation PR should include the narrowest applicable tests:

1. Unit tests for data models and adapters.
2. Component tests for dashboard cards, drawer sections, permission action states, and done-state rendering.
3. Existing cockpit URL/deep-link tests where drawer state changes.
4. Existing accessibility tests where keyboard or ARIA behavior changes.
5. `npm run lint`.
6. `npm run build`.
7. Targeted `npm test -- <changed tests>`.
8. Hosted CI and PR review before merge.

## Stop/continue gate for Wave 6

Continue through Wave 6 while:

1. Shared models remain frontend-only and type-safe.
2. Dashboard/drawer/task-board behavior is becoming more causally connected.
3. Permission mode behavior is visible and test-covered.
4. The work does not drift into marketplace, analytics, full Spawner redesign, or backend workspace schema.

Pause or narrow if:

1. Existing frontend data cannot support a truthful artifact view without a backend contract.
2. Permission gating would imply hidden automation not enforced elsewhere.
3. Component changes require broad CSS/layout rewrites.
4. PRs start coupling unrelated modules directly instead of using adapters.

## Success definition

Wave 6 is complete when a beginner can open the cockpit, see real or clearly demo-labeled artifacts, inspect commands/logs/tests/risks/approvals/activity/outcome in the drawer, understand which permission mode affects each action, and finish a run as PR ready, artifact package ready, or blocked with a specific required action.
