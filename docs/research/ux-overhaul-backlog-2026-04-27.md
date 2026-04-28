# AGENT-33 UX Overhaul Backlog — Cycle 1

**Date:** 2026-04-27  
**Baseline:** `b9bac47`  
**Scope:** 125 concrete improvement candidates distilled from a 10-persona expert panel, current UI audit, repo research mining, and competitive scan.  

**Implementation status:** The first wave is merged on `main` through PR `#454`. Completed initial slices: Outcome Home (`#450`), Workflow Catalog (`#451`), Model Connection Wizard (`#452`), Run Timeline (`#453`), and Advanced quarantine / Beginner-Pro mode (`#454`). Treat those backlog items as implemented in v1 form and use the remaining items below for the next scoped UX wave.

Impact: `H` high, `M` medium, `L` low. Effort: `S`, `M`, `L`, `XL`.

## A. Information architecture and first-run experience

| ID | Improvement | Why it matters | Impact | Effort |
|---|---|---|---|---|
| IA-001 | Outcome-first home screen | Replaces tab overload with jobs-to-be-done. | H | M |
| IA-002 | "What do you want to build?" launcher | Gives lay users an obvious first action. | H | S |
| IA-003 | Role-based start paths | Tailors UI for founder, developer, agency, enterprise, admin. | H | M |
| IA-004 | Hide Advanced by default | Prevents raw API surfaces from dominating. | H | S |
| IA-005 | Beginner/Pro mode switch | Preserves power-user access without scaring beginners. | H | M |
| IA-006 | Persona-specific examples | Shows "people like me use this for..." examples. | M | S |
| IA-007 | Unified Connect area | Merges Integrations, MCP Health, model setup, and tool setup. | H | M |
| IA-008 | Global command/search bar | Lets users find workflows, tools, docs, and settings quickly. | M | M |
| IA-009 | Home readiness meter | Shows model, tools, workspace, permissions, and safety status. | H | M |
| IA-010 | "Next best action" panel | Prevents users from staring at a dead dashboard. | H | M |
| IA-011 | Recent outcomes feed | Shows finished work instead of raw system activity. | M | M |
| IA-012 | Guided tour by job type | Reduces first-session confusion. | M | S |
| IA-013 | Demo mode with sample project | Lets users experience value without setup. | H | M |
| IA-014 | Inline glossary | Explains agent, workflow, skill, tool, MCP, pack, run, approval. | M | S |
| IA-015 | Empty-state action cards | Every blank page should propose a useful next step. | H | S |

## B. Intake and prompt-to-program

| ID | Improvement | Why it matters | Impact | Effort |
|---|---|---|---|---|
| INTAKE-001 | Guided idea intake | Converts vague goals into specs. | H | M |
| INTAKE-002 | Product brief wizard | Captures audience, outcome, constraints, success metrics. | H | M |
| INTAKE-003 | "I only know the outcome" mode | Supports non-technical users. | H | M |
| INTAKE-004 | Example prompt chips | Reduces blank-page anxiety. | M | S |
| INTAKE-005 | Voice-to-brief capture | Lets users explain naturally. | M | M |
| INTAKE-006 | Clarifying question ladder | Asks only necessary questions before starting. | H | M |
| INTAKE-007 | Scope-size classifier | Separates task, project, and program. | H | M |
| INTAKE-008 | App archetype picker | Lets users choose SaaS, dashboard, landing page, internal tool. | H | M |
| INTAKE-009 | Cost/time/budget slider | Gives users autonomy boundaries. | H | M |
| INTAKE-010 | Deliverable selector | Lets users choose PR, prototype, report, deployed app, plan. | H | S |
| INTAKE-011 | "Do it for me" vs "teach me" mode | Matches desired level of explanation. | M | S |
| INTAKE-012 | Requirements translator | Converts business language into technical plan. | H | L |
| INTAKE-013 | Constraint library | Adds compliance, stack, brand, deadline, budget constraints. | M | M |
| INTAKE-014 | Minimum viable first step suggestion | Prevents over-scoping. | H | M |
| INTAKE-015 | Intake quality score | Shows whether a request is actionable. | M | M |

## C. Model attach and capability selection

| ID | Improvement | Why it matters | Impact | Effort |
|---|---|---|---|---|
| MDL-001 | Model attach wizard | Simplifies the first critical setup step. | H | M |
| MDL-002 | Recommended model default | Avoids model choice paralysis. | H | S |
| MDL-003 | Provider cards with plain labels | Explains OpenRouter/Ollama/local/private options. | H | M |
| MDL-004 | Cost/speed/quality comparison | Makes tradeoffs understandable. | H | M |
| MDL-005 | Test prompt sandbox | Verifies setup before real workflows. | H | S |
| MDL-006 | Model health and quota status | Prevents mysterious failures. | H | M |
| MDL-007 | Task-to-model routing presets | Picks models by workflow type. | H | L |
| MDL-008 | Fallback model policy | Keeps workflows running when providers fail. | M | M |
| MDL-009 | Local/private model profile | Supports sensitive enterprise users. | H | L |
| MDL-010 | Plain-English model labels | Replaces raw model IDs with purpose labels. | M | S |

## D. Workflow catalog and pre-canned systems

| ID | Improvement | Why it matters | Impact | Effort |
|---|---|---|---|---|
| WF-001 | Workflow catalog home | Makes built-in workflows the core product. | H | M |
| WF-002 | Build my first app | Demonstrates the platform promise. | H | L |
| WF-003 | Analyze my repo | Immediate value for developers. | H | M |
| WF-004 | Create landing page | High-value beginner/founder workflow. | H | M |
| WF-005 | Workflow cards with inputs/outputs | Clarifies what each workflow does. | H | S |
| WF-006 | Dry-run simulation | Reduces fear before execution. | H | L |
| WF-007 | Save as reusable workflow | Turns one-off success into repeatable automation. | H | M |
| WF-008 | Enterprise modernization workflow | Supports high-value enterprise work. | H | XL |
| WF-009 | Client project kickoff | Helps agencies standardize delivery. | H | M |
| WF-010 | SaaS scaffold workflow | Creates auth, billing, dashboard, tests. | H | L |
| WF-011 | Internal tool builder | Builds CRUD/admin tools from requirements. | H | L |
| WF-012 | Data dashboard generator | Turns spreadsheets/APIs into dashboards. | H | L |
| WF-013 | Bug fix workflow | Takes issue -> branch -> tests -> PR. | H | M |
| WF-014 | Documentation generator | Produces docs from repo/product context. | M | M |
| WF-015 | Marketing campaign builder | Helps founders/agencies ship collateral. | M | M |
| WF-016 | Competitor research workflow | Aligns with current strategic need. | M | M |
| WF-017 | Dependency upgrade workflow | Routine developer automation. | M | M |
| WF-018 | Security review workflow | Adds safety to generated systems. | H | M |
| WF-019 | Test generation workflow | Improves build quality. | H | M |
| WF-020 | Release readiness workflow | Packages checks before shipping. | H | M |

## E. Product builder lifecycle

| ID | Improvement | Why it matters | Impact | Effort |
|---|---|---|---|---|
| BUILD-001 | Product brief wizard | Turns ideas into product specs. | H | M |
| BUILD-002 | MVP builder workflow | Central product promise. | H | XL |
| BUILD-003 | Generated execution plan | Builds trust before action. | H | M |
| BUILD-004 | App preview environment | Makes outputs tangible and safe. | H | L |
| BUILD-005 | Stack recommendation wizard | Picks tech stack from constraints. | M | M |
| BUILD-006 | Prototype-first mode | Builds clickable mock before full implementation. | H | L |
| BUILD-007 | Design-system starter | Avoids ugly/inconsistent generated UI. | H | M |
| BUILD-008 | Brand intake kit | Captures logo, colors, tone, examples. | M | M |
| BUILD-009 | Regenerate only this section | Reduces destructive broad edits. | M | M |
| BUILD-010 | Product QA checklist | Ensures obvious quality gates. | H | M |
| BUILD-011 | Deployment readiness checklist | Helps users know when app can ship. | H | M |
| BUILD-012 | One-click staging deploy | Makes built products usable. | H | L |
| BUILD-013 | Generated user docs | Packages the built product. | M | M |
| BUILD-014 | Maintenance plan generator | Explains what happens after MVP. | M | M |
| BUILD-015 | Product health score | Summarizes tests, security, UX, docs. | H | L |

## F. Agent OS and safe execution

| ID | Improvement | Why it matters | Impact | Effort |
|---|---|---|---|---|
| AGOS-001 | Agent OS default workspace | Makes execution contained and repeatable. | H | M |
| AGOS-002 | Workspace selector in UI | Lets users choose project/session context. | H | M |
| AGOS-003 | Snapshot and rollback | Makes long-running work recoverable. | H | L |
| AGOS-004 | Workspace health card | Shows disk, tools, git, model, service status. | M | M |
| AGOS-005 | "Open shell" and "open files" actions | Gives power users escape hatches. | M | M |
| AGOS-006 | Session template gallery | Preloads startup, SaaS, enterprise, data, research sessions. | H | M |
| AGOS-007 | Workspace permissions profile | Separates safe read-only, build, deploy modes. | H | M |
| AGOS-008 | Artifact browser | Shows outputs created by agents. | H | L |
| AGOS-009 | Run resume/checkpoint UI | Makes interrupted work resumable. | H | L |
| AGOS-010 | Resource limits and budget controls | Prevents runaway builds. | H | M |

## G. Operations, safety, and observability

| ID | Improvement | Why it matters | Impact | Effort |
|---|---|---|---|---|
| OPS-001 | Human-readable run timeline | Replaces raw logs with clear progress. | H | M |
| OPS-002 | Unified attention queue | One place for approvals, failures, decisions. | H | M |
| OPS-003 | Context-aware retry/fix buttons | Helps users recover from failures. | H | M |
| OPS-004 | Failure explanation cards | Turns stack traces into recommended fixes. | H | M |
| OPS-005 | Reviewable diff/PR output | Gives developer trust. | H | M |
| OPS-006 | Artifact and deliverable tracker | Shows what the agent produced. | H | M |
| OPS-007 | Cost/time budget monitor | Makes autonomy accountable. | H | M |
| OPS-008 | Milestone notifications | Helps users follow long runs. | M | M |
| SAFE-001 | Risk explanation before tool use | Makes approvals meaningful. | H | M |
| SAFE-002 | Approve once / time-bound / constrained decisions | Replaces binary approve/reject. | H | M |
| SAFE-003 | Action outcome preview | Shows what a tool will do before approval. | H | M |
| SAFE-004 | Bulk approval with safety grouping | Reduces approval fatigue. | M | M |
| SAFE-005 | Policy profiles | Lets users pick safe/default/aggressive modes. | H | M |
| SAFE-006 | Audit trail for every agent action | Enterprise prerequisite. | H | L |
| SAFE-007 | Human escalation rules | Defines when agents must stop and ask. | H | M |

## H. Connectors, packs, and ecosystem

| ID | Improvement | Why it matters | Impact | Effort |
|---|---|---|---|---|
| CONN-001 | Unified Connect center | Simplifies setup mental model. | H | M |
| CONN-002 | Connector test buttons | Verifies credentials/tools instantly. | H | S |
| CONN-003 | Connector health dashboard | Explains what is connected and broken. | H | M |
| CONN-004 | GitHub starter connector | Essential for build/PR workflows. | H | M |
| CONN-005 | Slack/Discord starter connector | Enables notifications and collaboration. | M | M |
| CONN-006 | Jira/Linear starter connector | Enables enterprise issue-to-PR work. | H | M |
| CONN-007 | GitHub/Jira/Slack starter bundle | One-click team setup. | H | L |
| PACK-001 | Outcome packs | Bundle workflow, tools, model policy, prompts, docs. | H | L |
| PACK-002 | Pack health/audit UI | Makes installed packs trustworthy. | H | M |
| PACK-003 | Pack dependency graph | Explains what a pack needs before install. | M | M |
| PACK-004 | Community workflow marketplace | Makes ecosystem useful to lay users. | H | L |
| PACK-005 | Pack trust badges | Helps users understand source/risk. | H | M |
| PACK-006 | Install wizard with test run | Confirms a pack works after install. | H | M |
| PACK-007 | Save current setup as pack | Turns working configs into reusable assets. | M | L |
| PACK-008 | Persona-specific pack collections | Startup, agency, enterprise, devops collections. | H | M |

## I. Enterprise programs

| ID | Improvement | Why it matters | Impact | Effort |
|---|---|---|---|---|
| ENT-001 | Autonomous Program Builder | Turns large goals into governed programs. | H | XL |
| ENT-002 | Milestones and release gates | Structures multi-month work. | H | L |
| ENT-003 | Program dashboard | Shows status, risks, budget, deliverables. | H | L |
| ENT-004 | Stakeholder status reports | Makes long-running work communicable. | H | M |
| ENT-005 | Program charter generator | Captures scope, owners, risks, outcomes. | H | M |
| ENT-006 | Dependency map | Makes program risk visible. | H | L |
| ENT-007 | Agent team roster | Shows which agents own which workstreams. | M | M |
| ENT-008 | Risk register | Required for enterprise governance. | H | M |
| ENT-009 | Decision log | Preserves why plans changed. | H | M |
| ENT-010 | Budget and burn-down view | Shows cost/time against plan. | H | M |
| ENT-011 | Release train planner | Organizes multiple PRs/milestones. | H | L |
| ENT-012 | Executive summary generator | Helps leaders understand progress. | M | M |
| ENT-013 | Compliance evidence bundle | Packages logs, approvals, tests, artifacts. | H | L |
| ENT-014 | Vendor/model risk report | Explains provider and data risk. | M | M |
| ENT-015 | Program resume protocol | Makes interruption recovery explicit. | H | M |

## J. Analytics, docs, and support

| ID | Improvement | Why it matters | Impact | Effort |
|---|---|---|---|---|
| OBS-001 | Outcome analytics by workflow | Shows value, not only activity. | H | M |
| OBS-002 | ROI dashboard with assumptions | Makes impact credible. | M | M |
| OBS-003 | Friction analytics | Reveals where users fail or abandon. | H | M |
| OBS-004 | Model cost/latency breakdown | Helps users choose better defaults. | M | M |
| OBS-005 | Success-rate trend diagnosis | Explains declining outcomes. | H | M |
| DOC-001 | Embedded help by screen | Reduces support load. | M | S |
| DOC-002 | "What can I do here?" card | Fixes shallow panel confusion. | H | S |
| DOC-003 | Guided troubleshooting | Turns errors into repair steps. | H | M |
| DOC-004 | "Why this matters" explainers | Teaches concepts without docs hunting. | M | S |
| DOC-005 | Workflow examples with outputs | Shows expected value. | H | M |
| CS-001 | Demo mode with sample data | Lets users evaluate without setup. | H | M |
| CS-002 | Support bundle export | Helps debug without back-and-forth. | M | M |
| CS-003 | First-success checklist | Gets users to a meaningful output quickly. | H | S |
| CS-004 | In-app feedback capture | Feeds UX improvement loops. | M | S |
| CS-005 | "Ask support agent" guided help | Routes users to contextual assistance. | M | M |

## Recommended first implementation wave

1. **Outcome Home shell** (`IA-001`, `IA-002`, `IA-009`, `IA-010`, `CS-001`).
2. **Workflow Catalog v1** (`WF-001`, `WF-005`, `WF-004`, `WF-016`, `DEV-001 equivalent via WF-003`).
3. **Model Attach Wizard** (`MDL-001` through `MDL-006`).
4. **Human-readable Run Timeline** (`OPS-001`, `OPS-002`, `OPS-004`, `OPS-006`).
5. **Advanced quarantine** (`IA-004`, `IA-005`, `DOC-002`).

## Tracking note

This backlog is intentionally wider than one sprint. It is the raw material for the next implementation queue and should be deduplicated against code reality before each PR slice.
