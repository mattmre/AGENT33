# AGENT-33 UX Overhaul Expert Panel — Cycle 1

**Date:** 2026-04-27  
**Baseline:** `b9bac47` (`docs: refresh Operator UX expansion handoff`)  
**Purpose:** respond to the finding that AGENT-33 is still too shallow, too power-user-centric, and not useful enough out of the box for layman users.  
**Status:** exploratory brain-map cycle 1, using EVOKORE panel methodology and competitive research.  

## Executive finding

The current UI has improved from raw API exposure, but it still behaves like a **feature catalog** instead of an **outcome-first agent operating platform**. Users can see many tabs, health panels, wizards, and API-derived surfaces, but they are not pulled into a clear path such as:

> connect a model -> describe an outcome -> choose a proven workflow -> approve the plan -> watch agents build -> review deliverables -> continue or scale into a program.

The product advantage should not be "we expose many agent primitives." It should be **pre-canned, safe, explainable, repeatable outcomes** for non-experts and power users alike.

## Method used

This cycle used the EVOKORE panel-of-experts method:

1. **Convene** 10 personas tied to real users and user-related professionals.
2. **Brief** the panel on the user's complaint and the current AGENT-33 UI.
3. **Solo review** across five rounds.
4. **Challenge** competing assumptions.
5. **Converge** on a product thesis.
6. **Feasibility gate** top recommendations.
7. **Deliver** a ranked implementation roadmap and backlog.

Parallel agents were used to reduce context rot:

| Agent | Purpose | Output used |
|---|---|---|
| `ui-auditor` | Audited `frontend/src/App.tsx`, feature directories, panels, styles, and current UI mental model. | 150+ UI-specific improvement candidates and top dead zones. |
| `repo-research-miner` | Mined `docs/`, `task_plan.md`, `progress.md`, `findings.md`, and roadmap docs for prior decisions. | Prior research evidence, stale-context risks, and 75+ implications. |
| `persona-panel` | Ran the 10-persona, five-round expert panel. | 220 improvement candidates, top 50 ranked set, and staged roadmap. |

## Panel personas

| Persona | Product lens | What they protect against |
|---|---|---|
| Non-technical founder | "Can I build a product without knowing agent jargon?" | Blank-page anxiety, model/setup confusion, hidden complexity. |
| Solo developer | "Can this accelerate real repo work without wrecking my code?" | Unreviewable changes, missing git/test affordances. |
| Enterprise product owner | "Can I run multi-month programs safely?" | Lack of milestones, ownership, budget, status reporting. |
| Agency operator | "Can I deliver repeatable client outcomes?" | One-off flows, no packaging, poor client reporting. |
| DevOps/SRE | "Can it run, resume, fail safely, and explain state?" | Fragile long-running jobs, no health/runbooks/recovery. |
| Security/compliance officer | "Can non-experts understand and control risk?" | Unsafe tool approvals, missing audit trail, unclear blast radius. |
| UX research lead | "Can users understand what to do next on every screen?" | Shallow panels, jargon, no empty-state guidance. |
| AI workflow architect | "Are workflows composable, observable, and outcome-led?" | Disconnected tools/skills/workflows and no orchestration spine. |
| Open-source maintainer | "Can contributors install, extend, and trust the platform?" | Poor extension packaging, unclear docs, no community loop. |
| Customer-success lead | "Can support get a user to first value quickly?" | No demo mode, poor troubleshooting, no guided success path. |

## Five panel rounds

### Round 1 — first-impression layman usability critique

The panel agreed the current UI still asks users to understand AGENT-33's internals before they receive value. The grouped navigation (`Start`, `Operate`, `Build`, `Improve`, `Extend`) is better than a flat nav, but still maps to platform architecture rather than user goals.

Key failures:

- The home experience does not ask "What do you want to build?"
- Chat is generic instead of connected to a workflow or active agent.
- Integrations, MCP Health, Tool Fabric, and Advanced all feel like setup/admin surfaces with overlapping language.
- "Advanced" still exposes domain/API thinking, creating fear and confusion.
- Users cannot tell which path creates an app, automates a business process, launches research, or starts a long-running program.

### Round 2 — out-of-box workflow and automation blueprint critique

The platform needs "batteries-included outcomes", not only workflow authoring. The panel recommended a workflow catalog that starts with common goals:

- "Build my first app"
- "Create a landing page"
- "Generate a SaaS scaffold"
- "Analyze my repo and propose fixes"
- "Launch a competitive research loop"
- "Create an internal dashboard"
- "Modernize this legacy app"
- "Run an enterprise delivery program"

Each workflow should ship with:

- plain-language description;
- required inputs;
- output examples;
- model/tool prerequisites;
- safety gates;
- run duration and cost estimate;
- dry-run preview;
- one-click launch.

### Round 3 — competitor pattern critique

Competitive patterns from OpenHands/OpenCode/Aider/Cline/Cursor/Devin-like products, MCP ecosystems, no-code builders, and workflow automation tools point to a clear direction.

| Pattern | Competitive examples | AGENT-33 implication |
|---|---|---|
| Plan/Act modes | Cline, OpenCode, Cursor-like agents | Add explicit **Plan only**, **Build with review**, and **Autopilot** modes across workflows. |
| Git-native delivery | Aider, OpenHands, SWE-agent | Every build workflow should produce reviewable diffs/PRs, rollback, and commit history. |
| Sandboxed workspaces | OpenHands, agent OS patterns | Agent OS should become the default safe build workspace, not an optional runtime doc. |
| Template galleries | AutoGPT/CrewAI/LangGraph-style ecosystems | Ship a workflow/template marketplace oriented around outcomes, not primitives. |
| Session/task continuity | OpenCode, Devin-like agents | Long-running work needs resumable programs, checkpoints, and stakeholder reports. |
| Tool ecosystem setup | MCP-native IDE agents | Hide MCP config behind connector packs, validation, health, and guided fixes. |
| Visual progress and logs | IDE/web agents | Replace raw logs/JSON dumps with "what happened / what is next / what needs approval." |

Selected web research sources used in this cycle:

- <https://github.com/PackmindHub/coding-agents-matrix>
- <https://agentic.ai/best/open-source-coding-agents>
- <https://agentwiki.org/coding_agent_comparison>
- <https://codegen.com/blog/best-ai-coding-agents/>
- <https://stoneforge.ai/blog/open-source-ai-coding-agents/>
- <https://toolhalla.ai/blog/devin-vs-openhands-vs-swe-agent-2026>

### Round 4 — enterprise and long-running autonomous program critique

Enterprise users need **program management**, not a bigger chat window. AGENT-33 should support multi-month autonomous programs with:

- program charter;
- milestones and release trains;
- agent team roster;
- budgets and resource limits;
- governance gates;
- risk register;
- dependency map;
- status reports;
- artifacts and decision log;
- escalation and handoff points.

This is the bridge from "build a small thing" to "run a two-to-three-month autonomous development program."

### Round 5 — feasibility and implementation sequencing

The feasibility panel rejected a giant UI rewrite as the first step. The recommended strategy is a staged transformation:

1. **Create an outcome-first shell** while preserving existing pages behind "Pro/Advanced".
2. **Ship a curated workflow catalog** with real baked-in templates.
3. **Turn Agent OS into the default build workspace** for safe execution.
4. **Add program mode** only after small/medium workflows prove reliable.
5. **Instrument the UX** so future layman-UX research loops identify friction continuously.

## Converged product thesis

AGENT-33 should become an **outcome-first agent operating platform** where users select a goal, attach a model, choose an autonomy level, and launch a safe workflow with built-in planning, tools, review gates, observability, and deliverables.

### Proposed primary navigation

Replace the current feature-first navigation with an outcome-first shell:

| New section | Job-to-be-done | Current surfaces absorbed |
|---|---|---|
| **Home** | Pick a goal and see readiness. | Start Here, recent outcomes, model/tool readiness. |
| **Build** | Create products, apps, docs, dashboards, automations. | Chat, Workflow Starter, Skill Wizard, Agent Builder. |
| **Run** | Watch active work, approvals, incidents, and deliverables. | Operations Hub, Review Queue, Safety Center, Outcomes. |
| **Workflows** | Browse, launch, customize, and save workflows. | Workflow Starter, Improvement Loops, Tool Fabric. |
| **Connect** | Models, tools, MCP, packs, credentials, Agent OS. | Integrations, MCP Health, Marketplace, Tool Catalog. |
| **Programs** | Multi-week/multi-month autonomous initiatives. | New program builder + analytics + milestones. |
| **Admin** | Raw operations, policies, diagnostics, developer settings. | Advanced and technical domains, hidden by default. |

## Top 50 ranked recommendations

| Rank | ID | Recommendation | Stage | Why it matters |
|---:|---|---|---:|---|
| 1 | IA-001 | Outcome-first home screen | 1 | Stops tab overload and frames the platform around value. |
| 2 | INTAKE-001 | Guided idea intake | 1 | Converts vague user goals into actionable specs. |
| 3 | MDL-001 | Model attach wizard | 1 | Users cannot start without simple model setup. |
| 4 | MDL-002 | "Use recommended model" default | 1 | Removes model choice paralysis. |
| 5 | WF-001 | Workflow catalog home | 1 | Makes prebuilt outcomes discoverable. |
| 6 | WF-005 | Workflow cards with inputs/outputs | 1 | Shows exactly what will happen. |
| 7 | IA-004 | Hide Advanced by default | 1 | Prevents power-user surfaces from dominating first use. |
| 8 | WF-004 | "Create landing page" workflow | 1 | Fast visible value for founders/agencies. |
| 9 | BUILD-003 | Generated execution plan | 1 | Builds trust before agents act. |
| 10 | OPS-001 | Human-readable live run timeline | 1 | Replaces logs with comprehensible progress. |
| 11 | SAFE-001 | Risk explanation before tool use | 1 | Makes approvals usable by non-experts. |
| 12 | CONN-001 | Unified Connect center | 1 | Merges integrations, MCP, models, and tools. |
| 13 | INTAKE-012 | Desired deliverable selector | 1 | Helps users choose prototype, PR, report, app, or plan. |
| 14 | WF-006 | Dry-run simulation | 1 | Reduces fear before execution. |
| 15 | OPS-002 | "What needs my attention?" queue | 1 | Unifies approvals, failed jobs, and next decisions. |
| 16 | BUILD-001 | Product brief wizard | 2 | Turns business ideas into product specs. |
| 17 | BUILD-002 | MVP builder workflow | 2 | Central product promise. |
| 18 | WF-010 | SaaS scaffold workflow | 2 | High-value canned stack. |
| 19 | BUILD-004 | App preview environment | 2 | Lets users inspect outputs safely. |
| 20 | BUILD-014 | Product QA checklist | 2 | Prevents low-quality generated products. |
| 21 | AGOS-001 | Agent OS as default workspace | 2 | Makes execution safe and repeatable. |
| 22 | AGOS-003 | Workspace snapshots and rollback | 2 | Makes long-running builds recoverable. |
| 23 | WF-011 | Internal tool builder | 2 | Common business automation outcome. |
| 24 | WF-012 | Data dashboard generator | 2 | Common data-to-value workflow. |
| 25 | PACK-001 | Outcome packs | 2 | Packages models/tools/workflows together. |
| 26 | ENT-001 | Autonomous Program Builder | 3 | Unlocks enterprise-class multi-month work. |
| 27 | ENT-002 | Milestones and release gates | 3 | Adds program structure. |
| 28 | ENT-005 | Program charter generator | 3 | Captures scope, owners, risks, outcomes. |
| 29 | GOV-001 | Audit log for every agent action | 3 | Enterprise prerequisite. |
| 30 | GOV-002 | Role-based access control | 3 | Enterprise prerequisite. |
| 31 | GOV-003 | Policy profiles | 3 | Lets lay users choose safety posture. |
| 32 | OPS-007 | Cost/time budget monitor | 3 | Prevents runaway autonomy. |
| 33 | WF-008 | Enterprise modernization workflow | 3 | High-value enterprise workflow. |
| 34 | WF-027 | App migration workflow | 3 | Long-running professional use case. |
| 35 | ENT-006 | Dependency map | 3 | Makes program risk visible. |
| 36 | ENT-008 | Risk register | 3 | Required for enterprise governance. |
| 37 | CONN-007 | GitHub/Jira/Slack starter bundle | 3 | Makes team workflows plug-and-play. |
| 38 | OBS-001 | Outcome analytics by workflow | 3 | Shows value instead of only activity. |
| 39 | OBS-003 | Friction analytics | 3 | Feeds continuous UX improvement. |
| 40 | CS-001 | Demo mode with sample data | 1 | Lets users see value without setup. |
| 41 | DOC-001 | Embedded help by screen | 1 | Reduces support load. |
| 42 | DOC-004 | "Why this matters" explainers | 1 | Makes jargon understandable. |
| 43 | ENT-004 | Stakeholder status reports | 3 | Makes long-running work communicable. |
| 44 | QA-001 | Built-in test generation workflow | 2 | Quality baseline for product builder. |
| 45 | SEC-001 | Security review workflow | 2 | Makes generated systems safer. |
| 46 | WF-016 | Competitor research workflow | 1 | Already aligned with user priority. |
| 47 | WF-029 | Fundraising data-room workflow | 2 | Founder-focused packaged value. |
| 48 | MKT-001 | Marketing campaign builder | 2 | Agency/founder value. |
| 49 | DEV-001 | Repo triage workflow | 1 | Developer-focused first value. |
| 50 | PROG-001 | Multi-month roadmap generator | 3 | Bridges simple task to enterprise program. |

## Staged roadmap

### Stage 1 — rescue first-run usability

Goal: make the first 10 minutes obvious.

- Outcome-first home.
- Model attach wizard with recommended defaults.
- Demo mode with sample data.
- Workflow catalog home.
- Hide Advanced behind Pro/Admin mode.
- Unified attention queue.
- Human-readable run timeline.
- Risk explanation before approvals.

### Stage 2 — product-building workflows

Goal: ship real "do this for me" workflows.

- Build my first app.
- Create landing page.
- SaaS scaffold.
- Internal tool builder.
- Data dashboard generator.
- Product brief wizard.
- App preview environment.
- QA/security checklist.
- Agent OS default workspace with snapshots.

### Stage 3 — business automation and agency packaging

Goal: make AGENT-33 useful for repeatable client/business outcomes.

- Client project kickoff.
- Marketing campaign builder.
- Sales ops workflow.
- Fundraising data-room workflow.
- Outcome packs.
- Report/export templates.
- GitHub/Jira/Slack starter bundle.

### Stage 4 — enterprise autonomous programs

Goal: support large multi-month autonomous initiatives.

- Autonomous Program Builder.
- Milestones and release gates.
- Program charter generator.
- Dependency map.
- Risk register.
- Stakeholder status reports.
- RBAC, audit log, policy profiles.
- Cost/time budget monitor.

### Stage 5 — ecosystem and continuous improvement

Goal: create durable advantage beyond single workflows.

- Workflow marketplace.
- Pack health/audit UI.
- Policy marketplace.
- Friction analytics.
- UX research loop dashboards.
- Community-contributed outcome packs.

## Research implications from existing repo docs

The repo already contains evidence that this is not a backend capability problem alone.

| Evidence | Source | Implication |
|---|---|---|
| The current handoff says Operator UX/MCP/Agent OS queues are complete through `#447`. | `docs/next-session.md`, `progress.md` | The next wave should not be "add another tab"; it must reframe the product shell. |
| Prior findings say layman operators had to discover JSON/API-shaped actions. | `findings.md` | The redesign must remove API-shaped mental models from default surfaces. |
| Workflow registry / traces still have persistence caveats in older functionality docs. | `docs/functionality-and-workflows.md` | UX for long-running programs needs durable state, not only frontend affordances. |
| Pack audit / pack health surfaces were previously deferred. | `findings.md` historical notes | Outcome packs need health/trust visibility before they become default user workflows. |
| MCP Health, Tool Fabric, Workflow Starter, and Improvement Loops are separate pages. | `frontend/src/App.tsx`, `frontend/src/features/*` | These should be combined into a user-facing Connect/Workflow experience rather than scattered primitives. |

## Non-negotiable design principles

1. **Outcome before primitive.** Users should start from "what do you want done?", not "which subsystem do you want?"
2. **Recommended defaults.** Every open-ended setting needs a default and an explanation.
3. **Explain before execution.** Show plan, cost, risk, inputs, outputs, and review gates before running.
4. **Visible progress.** Every agent run needs a human timeline, not raw logs only.
5. **Safe autonomy ladder.** Plan only -> build with review -> autopilot -> governed program.
6. **Agent OS by default.** Real building should occur in contained workspaces with snapshots and rollback.
7. **Workflow catalog as product surface.** Workflows are the product, not just a configuration format.
8. **Advanced exists, but hidden.** Power-user controls should be available without dominating the layman path.
9. **Every page has a next action.** Empty states must tell users what to do now.
10. **Instrument friction.** The platform should learn where users fail, abandon, or need support.

## Immediate implementation recommendation

Do not start by styling existing pages. Start by creating a new **Outcome Home + Workflow Catalog** shell that can route users into existing capabilities with much better framing.

Recommended first PR sequence:

1. **Outcome Home shell**: "What do you want to build?" plus readiness meter, model status, recent outcomes, and demo mode.
2. **Workflow Catalog v1**: 12 curated workflows with cards, required inputs, outputs, estimated time/cost, safety gates, and launch buttons.
3. **Model Attach Wizard**: provider selection, recommended default, test prompt, cost/speed/quality labels.
4. **Run Timeline**: plain-English execution timeline for active jobs and approvals.
5. **Advanced quarantine**: move raw domain operation UI behind Admin/Pro mode and add search/export, but remove it from default path.

