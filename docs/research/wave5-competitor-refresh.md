# Wave 5 Competitor Refresh: Artifact, Review, and Project Coordination

## Scope

This refresh updates the Wave 3 competitor model after the Wave 4 cockpit shell landed. It focuses on what AGENT33 should learn for Wave 6: artifact/review UX, project/workspace coordination, task lifecycle, permissions, and beginner-ready setup.

Primary references:

- OpenAI Codex docs and `openai/codex` README.
- Claude Code documentation.
- Google Jules landing page.
- OpenHands README and local setup documentation.
- Agent Zero README.
- OpenClaw Mission Control README.
- Vercel v0 landing page.
- Existing AGENT33 research docs under `docs/research`.

BridgeSpace/BridgeMind remains a user-provided reference pattern. Public source material was not strong enough to treat it as independently verified, so this document separates the BridgeSpace pattern language from source-backed claims.

## Source-backed current signals

| System | Verified source signal | AGENT33 implication |
| --- | --- | --- |
| OpenAI Codex | Codex now spans CLI, IDE extension, desktop app, and Codex Web. IDE docs emphasize editor sidebar use, cloud delegation, follow-up on cloud work, approval modes, and Chat/Agent/Agent Full Access autonomy choices. | AGENT33 should keep the permission ladder visible and make cloud/PR-style handoff states first-class, not hidden in advanced tools. |
| Claude Code | Claude Code supports Terminal, VS Code, Desktop, Web, JetBrains, remote control, channels, routines, GitHub Actions, GitHub Code Review, Slack, Chrome, and Agent SDK. Desktop/web docs emphasize multiple sessions, scheduled tasks, cloud sessions, visual diff review, and recurring work. | AGENT33 needs cross-surface continuity: local cockpit, PR review, recurring loops, and artifact review should use the same session/project state. |
| Google Jules | Jules positions itself around workflow plans from quick fixes to async, multi-agent development. | AGENT33 should present scalable modes from "small fix" to "multi-agent shipyard" as beginner templates, not raw settings. |
| OpenHands | OpenHands offers SDK, CLI, Local GUI, Cloud, and Enterprise. It highlights REST API + React GUI, GitHub/GitLab login, Slack/Jira/Linear integrations, multi-user support, RBAC/permissions, collaboration sharing, and Docker/local setup. | AGENT33 should preserve local-first/Docker operation, but needs clearer provider setup, sandbox status, and project collaboration artifacts. |
| Agent Zero | Agent Zero emphasizes a full Linux environment in Docker, Web UI, Universal Canvas, visible browser/Office artifacts, projects that isolate workspaces/instructions/memory/secrets/repos/model presets, agent profiles, skills, MCP, A2A, plugins, Time Travel snapshots, and controlled host-machine access via A0 CLI. | AGENT33's Agent OS direction should prioritize isolation, recoverability, visible artifacts, project secrets boundaries, and explicit escalation from sandbox to host. |
| OpenClaw Mission Control | OpenClaw Mission Control presents organizations, board groups, boards, tasks, tags, agent lifecycle, governance approvals, gateway management, activity timeline, auth modes, and API-first operation. | AGENT33's cockpit should evolve from static workspace cards into boards/tasks/activity backed by a shared operational model. |
| Vercel v0 | v0 emphasizes prompt-to-app, publish/deploy, GitHub sync, integrations, visual design mode, templates, design systems, and agentic planning/tasks/database/API/deploy flow. | AGENT33 should package workflows as outcome templates that produce visible artifacts and deploy/PR handoffs, not just generic workflow forms. |

## Existing repo research to reuse

| Existing artifact | Reusable finding |
| --- | --- |
| `docs/research/wave5-implementation-audit.md` | Wave 4 shell is directionally correct but static; Wave 6 must add artifact adapters, real drawer content, permission-gated actions, and clear done states. |
| `docs/research/repo_dossiers/agent-zero.md` | Agent Zero patterns: prompt-driven governance, hierarchical subagents, skills, memory/project isolation. |
| `docs/research/repo_dossiers/anthropic-claude-code.md` | Claude Code patterns: deny-first permissions, hooks, MCP, subagents, persistent memory. |
| `docs/research/loop3-cross-batch-capability-synthesis-2026-04-21.md` | Cross-corpus synthesis favors action-observation-event contracts, checkpoint/review UX, and explicit governance surfaces. |
| `docs/research/integration-report-2026-02-13.md` | Critical prior finding: governance constraints must reach prompts and runtime behavior, not remain only in config/code. |
| `docs/research/openclaw-top20-agent-ecosystem-improvement-plan-2026-02-16.md` | OpenClaw and adjacent ecosystems point toward runtime tool catalogs, patch mutation tools, backups, and operational governance. |

## Competitive pattern matrix

| Pattern | Strong examples | AGENT33 state after Wave 4 | Wave 6 recommendation |
| --- | --- | --- | --- |
| Workspace/project isolation | Agent Zero projects; OpenHands local/cloud/enterprise modes; OpenClaw org/board groups | Frontend-only workspace templates | Keep frontend model, add artifact/task adapters keyed by workspace before backend schema |
| Permission/autonomy ladder | Codex Chat/Agent/Agent Full Access; Claude Code permissions; OpenHands RBAC; OpenClaw approvals | Visible permission labels, no action gating yet | Add permission-gated buttons, approval artifacts, and plain-language disabled states |
| Task board/lifecycle | OpenClaw boards/tasks/tags; BridgeSpace-inspired task board | Static kanban lanes and role ownership | Adapt existing operations/session data into Todo/Running/Review/Complete/Blocked cards |
| Artifact review | Claude visual diffs; Codex cloud follow-up/review; Agent Zero Universal Canvas/Office/browser artifacts | Drawer tabs exist with static descriptions | Add artifact cards, command blocks, logs, tests, risks, approvals, outcome content |
| Activity/mailbox | OpenClaw activity visibility; Claude channels/remote control; Agent Zero visible streamed output | Drawer has Activity/Mailbox placeholder | Add typed mailbox/activity events for Coordinator/Scout/Builder/Reviewer/Operator |
| Recoverability | Agent Zero Time Travel; PR/diff flows in Codex/Claude | No cockpit recovery model | Define done states and attach artifacts to PR/package/blocker outcomes |
| Beginner setup | OpenHands provider popup/local LLM docs; v0 templates/integrations; Agent Zero one-command Docker | AGENT33 has model/connect surfaces but cockpit does not guide setup from the workspace | Defer runtime readiness to Wave 7, but Wave 6 artifacts should explain missing setup blockers |
| Outcome templates | v0 templates/design systems; OpenClaw boards; Agent Zero project profiles | Workspace templates are labels with static tasks | Convert templates into starter configurations only after artifact adapter foundation exists |

## BridgeSpace pattern, without overclaiming

The user wants AGENT33 to replicate BridgeSpace's use cases and operating feel. The durable pattern we should keep from that reference is:

1. Workspace templates define a project mode.
2. Task board shows progress without requiring raw JSON or endpoint knowledge.
3. Agent roster assigns readable roles, not abstract imports.
4. Command blocks make tool execution reviewable and replayable.
5. Mailbox/activity feed makes agent handoffs visible.
6. Review drawer keeps plan, logs, tests, risks, approvals, and outcome in one place.
7. Operator can start simple and scale into longer multi-agent workflows.

Wave 4 implemented the visual vocabulary. Wave 6 must implement the content model and interaction depth.

## Competitor deltas versus AGENT33

### Where AGENT33 is now competitive

- Visible governance posture is stronger than many raw agent frameworks because permission modes are always present in the cockpit context.
- The Wave 4 cockpit now has the right conceptual primitives: workspace, task board, role lanes, review drawer, deep links, and old-tool demotion.
- The local-first/Docker direction remains valuable against cloud-only products.

### Where AGENT33 still lags

- Competitors increasingly show actual artifacts, diffs, browser sessions, Office files, timelines, PR state, and recoverability; AGENT33 mostly shows placeholders.
- Competitors make setup paths concrete: connect provider, choose model, mount local repo, run sandbox. AGENT33 has setup panels but the cockpit does not surface readiness blockers.
- Competitors support cloud delegation, multiple sessions, recurring tasks, or project isolation; AGENT33 has a frontend workspace selector but no durable workspace/run model.
- Competitors treat permissions as behavior; AGENT33 currently treats permission mode mostly as descriptive copy.

## Panel synthesis

### Non-technical founder

Truth score: 0.68.

The cockpit looks more trustworthy than the old nav, but still needs a clear "what do I click first and what happens next" path. Wave 6 should replace placeholders with artifact cards and completion outcomes.

### Solo developer

Truth score: 0.74.

Codex/Claude win by living beside code and diffs. AGENT33 can compete locally if the cockpit can show command blocks, test evidence, and PR-ready summaries without forcing terminal reading.

### Agency operator

Truth score: 0.72.

OpenClaw-style boards and Agent Zero-style project isolation matter because agencies juggle clients. AGENT33 should avoid backend workspace complexity for Wave 6, but the frontend artifact model must be workspace-aware.

### Security/compliance reviewer

Truth score: 0.76.

Permission modes must become real UI constraints. OpenHands/OpenClaw emphasize RBAC/approvals; Agent Zero emphasizes sandbox boundaries. Wave 6 should connect permission state to actions and approval artifacts.

### AI workflow architect

Truth score: 0.79.

The strongest common pattern is not "more tabs." It is a shared operational record: task, command, event, artifact, approval, outcome. AGENT33 should build that record as typed frontend view models first.

## Wave 6 adoption plan

### Adopt now

1. **Artifact cards and drawer content** inspired by Codex/Claude review surfaces and Agent Zero visible artifacts.
2. **Command blocks** inspired by BridgeSpace/OpenClaw operational auditability.
3. **Mailbox/activity events** inspired by OpenClaw activity timelines and Claude/Agent Zero multi-session visibility.
4. **Permission-gated actions** inspired by Codex approval modes, Claude permissions, OpenHands RBAC, and OpenClaw approvals.
5. **Done-state taxonomy** inspired by PR/diff/product handoff workflows:
   - PR ready.
   - Artifact package ready.
   - Blocked with required action.

### Distill later

1. Agent Zero project isolation and Time Travel into AGENT33 Agent OS/runtime phases.
2. OpenHands cloud/local/enterprise split into deployment modes and environment readiness checks.
3. v0-style prompt-to-deploy templates into installable workflow/outcome packs.
4. Claude/Codex cloud delegation into PR-first implementation lanes.

### Observe only

1. Full IDE/sidebar clones.
2. Universal canvas/editor surfaces.
3. Dynamic marketplace navigation.
4. Browser/Office coworking surfaces.
5. Multi-user RBAC and enterprise tenancy.

## Wave 6 backlog update from competitor refresh

### P0

1. Add typed artifact models for plan, command, log, test, risk, approval, activity, and outcome.
2. Add dashboard artifact timeline/cards from those models.
3. Upgrade review drawer sections from static text to rendered artifacts.
4. Gate cockpit action affordances based on permission mode.
5. Add clear completion states: PR ready, artifact package ready, or blocked with required action.

### P1

1. Add command block summaries with status, duration, redaction state, and linked task/artifact.
2. Add mailbox/activity events for agent role handoffs.
3. Add Help Assistant topics for cockpit workspaces, permissions, drawer sections, and completion state.
4. Add integration tests for workspace switching, URL restore, permission switching, and drawer artifact rendering.

### P2

1. Workspace template configurations that seed starter tasks.
2. Runtime/provider readiness blockers surfaced in cockpit.
3. Project isolation and recoverability research for Agent OS phases.
4. Dynamic skill/workflow provenance visualization.

## Explicit non-goals reinforced by competitor refresh

Wave 6 should not attempt:

1. A full IDE clone.
2. A universal canvas.
3. Enterprise RBAC.
4. Backend workspace schema unless adapters hit a hard limit.
5. Browser/Office coworking.
6. Marketplace expansion.
7. Multi-user collaboration.
8. Prompt-to-deploy template marketplace.

## Bottom line

The market is moving toward agent workbenches where the user can see tasks, artifacts, permissions, approvals, and outcomes in one recoverable project context. AGENT33 now has the cockpit shell for that model. The competitive gap is substance: Wave 6 must make the shell show real artifact/review/project coordination state instead of more navigation refinements.
