# Wave 5 Neglected Module Review

## Scope

This review looks beyond the Wave 4 cockpit shell and asks which user-facing modules remain shallow, over-focused, under-tested, or disconnected from the beginner workflow. It uses the merged `origin/main` state at commit `dc8455f` after the Wave 5 competitor refresh and consolidates three module audits:

1. Beginner setup modules.
2. Build/workflow modules.
3. Operations, safety, review, analytics, and cockpit modules.

The review is intentionally practical: it identifies where a layperson gets stuck, which modules should feed Wave 6, and which items should be deferred to later waves so the program does not over-focus on navigation chrome.

## Feature/test inventory snapshot

The frontend has broad feature coverage but uneven test depth. Current feature directories with zero colocated tests include:

| Feature | Files | Tests | Notes |
| --- | ---: | ---: | --- |
| `impact-dashboard` | 4 | 0 | ROI and pack-impact UI lacks direct tests. |
| `spawner` | 5 | 0 | Backend tests exist elsewhere, but frontend workflow builder/execution tree lack colocated tests. |
| `modules` | 1 | 0 | Small area, low immediate concern. |
| `outcomes` | 1 | 0 | Low immediate concern compared with dashboard modules. |
| `tasks` | 1 | 0 | Low immediate concern until task execution binding lands. |

Feature directories with thin coverage relative to UX risk include:

| Feature | Files | Tests | Risk |
| --- | ---: | ---: | --- |
| `improvement-loops` | 5 | 1 | Only utility/preset coverage; main panel flow is not covered. |
| `outcomes-dashboard` | 5 | 1 | Helper coverage exists, but main dashboard behavior remains shallow. |
| `mcp-health` | 4 | 1 | Expert-heavy statuses need error/recovery coverage. |
| `tool-fabric` | 4 | 1 | Discovery is tested, but no install/compose action exists. |
| `pack-marketplace` | 6 | 1 | Install flow exists but rollback/uninstall/prerequisite states are weak. |

## Cross-module findings

### 1. Setup is clearer, but failure recovery is weak

Modules affected:

- `frontend/src/features/connect-center/UnifiedConnectCenterPanel.tsx`.
- `frontend/src/features/model-connection/ModelConnectionWizardPanel.tsx`.
- `frontend/src/features/integrations/MessagingSetup.tsx`.
- `frontend/src/features/mcp-health/McpHealthPanel.tsx`.
- `frontend/src/features/outcome-home/OutcomeHomePanel.tsx`.

Waves 1-4 replaced raw settings with guided surfaces, provider presets, readiness cards, and help prompts. The remaining problem is what happens when setup breaks. Users still see generic HTTP failures, "unknown" statuses, expert words like proxy/circuit/CLI drift, and duplicate OpenRouter-like setup paths.

The highest-risk issue is deceptive placeholder behavior in Messaging Setup: Telegram/Discord/Signal/iMessage-style cards appear actionable but do not represent complete integrations. This is worse than a missing feature because it can convince a beginner that something is connected when it is not.

### 2. Workflow creation is strong, but workflow operation is shallow

Modules affected:

- `frontend/src/features/workflow-catalog/WorkflowCatalogPanel.tsx`.
- `frontend/src/features/workflow-starter/WorkflowStarterPanel.tsx`.
- `frontend/src/features/improvement-loops/ImprovementLoopsPanel.tsx`.
- `frontend/src/features/spawner/SpawnerPage.tsx`.
- `frontend/src/features/tool-fabric/ToolFabricPanel.tsx`.

Workflow Catalog and Workflow Starter are among the strongest surfaces: they support plain-language intent, filtering, previews, recommendations, and backend calls. Improvement Loops, Spawner, and Tool Fabric are less complete:

- Improvement Loops has useful presets and one-click launcher concepts, but the main panel lacks direct tests and cadence explanations.
- Spawner has meaningful backend concepts and live execution polling, but the frontend is raw for beginners: manual agent entry, advanced prompt fields, isolation choices without readiness checks, and no obvious abort/recovery path.
- Tool Fabric discovers tools/skills/workflows but does not let a user install, compose, save, or use a discovered result.

### 3. Operations and safety are functional but isolated

Modules affected:

- `frontend/src/features/operations-hub/OperationsHubPanel.tsx`.
- `frontend/src/features/safety-center/SafetyCenterPanel.tsx`.
- `frontend/src/features/operations-hub/IngestionReviewPanel.tsx`.
- `frontend/src/components/CockpitProjectDashboard.tsx`.
- `frontend/src/components/WorkspaceTaskBoard.tsx`.
- `frontend/src/components/ArtifactReviewDrawer.tsx`.

The safety and review surfaces have useful individual workflows. The gap is causality. A beginner needs to know:

1. What is blocked?
2. Which approval or artifact unblocks it?
3. What changed after approval?
4. Did the run end as PR ready, artifact package ready, or blocked?

Today, approvals, task cards, artifact placeholders, ingestion review, and operations status are separate surfaces. They do not yet form an operator-visible cause-and-effect loop.

### 4. Analytics and impact are under-served

Modules affected:

- `frontend/src/features/session-analytics/SessionAnalyticsDashboard.tsx`.
- `frontend/src/features/outcomes-dashboard/OutcomesDashboardPanel.tsx`.
- `frontend/src/features/impact-dashboard/ImpactDashboardPanel.tsx`.

These modules expose valuable concepts but remain difficult for a layperson:

- Session Analytics can show trends/costs, but lacks obvious cost attribution and remediation guidance.
- Outcomes Dashboard has metrics, but the main panel is not tested deeply enough and lacks plain-language interpretation.
- Impact Dashboard has ROI/impact ideas, but no colocated tests and limited drill-down from a metric to a responsible session, pack, workflow, or task.

Wave 6 should not make analytics the primary focus, but artifact models should carry enough metadata to make these dashboards useful later.

## Module health matrix

| Module | Current health | Over/under focus | Main beginner failure | Recommended priority |
| --- | --- | --- | --- | --- |
| Connect Center | Medium | Served | Error recovery is too generic | P1 |
| Model Connection Wizard | Medium | Served | Key removal and dual key paths are confusing | P1 |
| Messaging Setup | Low | Under-served | Placeholder integrations imply false success | P0 |
| MCP Health | Medium-low | Under-served | Jargon and recovery steps are unclear | P1 |
| Help Assistant | Medium | Served | Corpus is too small for cockpit/setup failures | P1 |
| Demo Mode | Medium-high | Served | Demo-to-real-run expectations are too optimistic | P2 |
| Role Intake | Medium | Served | Roles and brief quality are too limited | P2 |
| Outcome Home | Medium-low | Under-served | Too many first-step choices | P1 |
| Workflow Catalog | High | Served | Needs related/recommended flows later | P2 |
| Workflow Starter | High | Served | Cron/schedule clarity and undo are missing | P2 |
| Improvement Loops | Medium-low | Under-served | Main panel lacks test coverage and cadence clarity | P0 |
| Spawner | Low | Under-served | Frontend is raw and untested for lay users | P0 |
| Agent Builder | High | Served | Provider/version handoff could improve | P2 |
| Skill Wizard | Medium-high | Served | Template copying/version guidance missing | P2 |
| Tool Fabric | Medium-low | Under-served | Discovery-only; no use/install/compose actions | P1 |
| Tool Catalog | Medium-high | Served | Browse-only; no "use in workflow" path | P2 |
| Pack Marketplace | Medium-low | Under-served | Install lifecycle lacks rollback/uninstall/prereq clarity | P1 |
| Operations Hub | Medium | Over-served but isolated | Process state does not explain produced artifacts | P1 |
| Safety Center | Medium | Over-served but isolated | Approvals do not explain blocked task impact | P0 for artifact linkage |
| Ingestion Review | Medium | Over-served but isolated | Approval outcome is not visible elsewhere | P1 |
| Session Analytics | Medium-low | Under-served | Costs/trends lack attribution and next action | P2 |
| Outcomes Dashboard | Low | Under-served | Metrics lack interpretation and direct main-panel coverage | P1 |
| Impact Dashboard | Low | Under-served | ROI/pack impact lacks tests, drill-down, and interpretation | P1 |
| Cockpit Dashboard | Medium | New shell | Artifact cards are placeholders | P0 |
| Workspace Task Board | Medium | New shell | Blocked/running tasks lack reasons and artifact links | P0 |
| Artifact Review Drawer | Medium-low | New shell | Sections are static descriptions | P0 |
| Shipyard Lanes | Medium | New shell | Lanes infer static status rather than observed handoffs | P1 |

## Layperson failure scenarios

### Scenario A: "I connected a provider, but AGENT33 still says unknown."

The user may pass through Connect Center, Model Connection Wizard, Messaging Setup, and MCP Health. Each module has its own status wording and recovery path. There is no single readiness explanation that says "engine is offline," "model key is missing," "MCP proxy is not configured," or "this feature is not implemented yet."

### Scenario B: "I clicked a messaging integration and it said success, but nothing works."

Placeholder integrations create a false-positive success path. A coming-soon card is safer than a fake connection.

### Scenario C: "I approved something. Did it unblock my work?"

Safety Center and Ingestion Review can approve items, but the task board, dashboard, and drawer do not show the causal result. This is the exact artifact/review gap Wave 6 should address.

### Scenario D: "Tool Fabric found a tool. Now what?"

Tool Fabric can discover relevant tools, skills, and workflows, but does not provide a clear "use this," "install this," "compose into skill," or "save this combo" action.

### Scenario E: "I want a multi-agent workflow, but Spawner asks me for system prompts and isolation modes."

Spawner exposes powerful concepts too early. It needs agent discovery, safe defaults, examples, and abort/recovery before it becomes a beginner-ready workflow builder.

## Wave 6 impact

The neglected-module review reinforces the Wave 6 artifact/review focus. Wave 6 should not try to fix every module. Instead, it should build a shared cockpit artifact layer that improves the highest-risk modules indirectly:

1. Cockpit Dashboard gets real artifact cards.
2. Task Board can explain blocked/running/review states.
3. Safety Center approvals can produce approval artifacts.
4. Artifact Drawer can show plan, command, test, risk, approval, activity, and outcome records.
5. Operations Hub can feed artifact/timeline cards instead of sitting below the cockpit as a separate old panel.

## P0 recommendations

1. **Remove or clearly demote fake messaging integration success paths**
   - Replace incomplete integration cards with "coming soon" states or route to the real OpenRouter/model setup path.
   - Files: `frontend/src/features/integrations/MessagingSetup.tsx`, `frontend/src/features/integrations/MessagingSetup.test.tsx`.

2. **Add main-panel coverage for Improvement Loops**
   - Cover preset switching, one-click launch, schedule/cadence display, API failures, and credential gates.
   - Files: `frontend/src/features/improvement-loops/ImprovementLoopsPanel.tsx`, new `ImprovementLoopsPanel.test.tsx`.

3. **Add frontend coverage for Spawner's existing flow**
   - Cover the current empty state, create workflow path, child agent validation, execution tree status, error display, and no-token states without redesigning the visual workflow builder.
   - Keep beginner guidance features such as agent discovery, safe defaults, examples, and abort/recovery as later Wave 7+ candidates unless Wave 6 artifact work exposes a narrow shared-state dependency.
   - Files: `frontend/src/features/spawner/SpawnerPage.tsx`, `frontend/src/features/spawner/ExecutionTree.tsx`, new tests.

4. **Implement artifact/review view models before deeper module polish**
   - This is the common adapter that lets cockpit, task board, approvals, operations, and analytics speak the same language.
   - Files to start: new `frontend/src/data` or `frontend/src/features/operations-hub` artifact model/adapters.

5. **Connect permission/safety decisions to visible cockpit state**
   - Approval actions should generate visible approval artifacts and update blocked-task explanations.
   - Files: `SafetyCenterPanel.tsx`, `WorkspaceTaskBoard.tsx`, `ArtifactReviewDrawer.tsx`, shared artifact adapters.

## P1 recommendations

1. Expand Help Assistant corpus for cockpit/setup failure modes and permission modes.
2. Add actionable error recovery copy to Connect Center and MCP Health.
3. Simplify Outcome Home by reducing simultaneous first-step choices.
4. Add Tool Fabric "use this," "save," or "compose" affordances after discovery.
5. Add Pack Marketplace install safeguards: prerequisites, progress, uninstall, rollback, and failure recovery.
6. Add Outcomes/Impact dashboard tests and plain-language metric interpretation.
7. Add workspace/template readiness blockers to the cockpit dashboard.

## P2 recommendations

1. Add related workflows in Workflow Catalog.
2. Add cron/cadence preview improvements in Workflow Starter and Improvement Loops.
3. Add role-intake "not sure" quiz and richer complex-project follow-up questions.
4. Add Tool Catalog sorting, provider filters, and "use in workflow" routing.
5. Add Agent Builder import/version migration.
6. Add marketplace author profiles and reviews.

## Explicit deferrals

Do not spend Wave 6 on:

1. Full analytics dashboard overhaul.
2. Full Spawner visual workflow redesign.
3. Marketplace social features.
4. New backend workspace/project schema.
5. Full MCP proxy troubleshooting UI.
6. Role intake overhaul.
7. Tool marketplace install provenance.

These are real issues, but they should not displace artifact/review foundations.

## Bottom line

Waves 1-4 improved breadth and first impressions. The most neglected product behavior is not another missing page; it is cross-module causality. Beginners need to see how a setup status, task, command, approval, artifact, and outcome relate. Wave 6 should implement that shared artifact/review layer first, then use later waves to polish the specific modules that remain under-served.
