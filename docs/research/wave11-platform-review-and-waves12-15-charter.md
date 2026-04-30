# Wave 11 Platform Review and Waves 12-15 Charter

## Scope

Wave 11 is an odd-numbered research and refinement wave. Its job is to reset the program after Wave 10, choose the next implementation priorities, and prevent the next implementation cycle from drifting into either "more shallow UI" or "control-plane-only hardening."

Baseline:

- `origin/main` is `96e1c3e` after Wave 10 recovery-impact preview (`#507`).
- Wave 10 completed the starter/outcome pack queue: manifest model, readiness policy, preview/trust badges, official seed packs, install-to-launch, pack provenance, and recovery previews.
- Hosted GitHub Actions are not the merge gate for this cycle; local tests, lint, build, and focused security validation are the gate.

Inputs:

- Independent Wave 11 platform audit agent.
- Independent Wave 11 competitor refresh agent.
- Existing research: Wave 5 competitor refresh, Wave 7 runtime readiness, Wave 9 starter/outcome packs charter, Loop 5A/5B harness/cadre research, `docs/functionality-and-workflows.md`, and `docs/sessions/research-security-gaps.md`.
- Source checks against current code where historical docs appeared stale.
- Current external references: OpenAI Codex, Claude Code, OpenHands, Agent Zero, and Google Jules public docs/pages.

## Executive finding

AGENT33 now has the right product nouns: cockpit, projects, workflow catalog, model setup, safety center, Agent OS, improvement loops, outcome packs, and recovery previews. The next gap is not another navigation reshuffle. The platform needs deeper operating substance:

1. Users must be able to start from a project/outcome and see a concrete run plan, artifacts, checkpoints, and recoverable next steps.
2. Safety and governance must be real runtime behavior, not just labels or separate admin pages.
3. State that matters for reviews, traces, evaluations, budgets, releases, and improvement learning must survive restarts.
4. Agent OS must become the default safe workspace for execution and dry-runs, with visible readiness and recovery.
5. The harness/cadre model must become visible enough that users understand who is researching, building, reviewing, governing, and improving.

The Wave 12 implementation should therefore combine foundation closure with beginner-visible value. Pure UX would deepen the shallow-product problem. Pure backend security would not address the user's core pain that AGENT33 still does not feel usable out of the box.

## Current platform health after Wave 10

| Area | Health | What is now solid | Remaining gap |
| --- | --- | --- | --- |
| Help Assistant/docs | 3/5 | Context help and curated corpus exist. | Needs generated docs index, source-cited search from every surface, and setup-specific answers. |
| Connect/model setup | 4/5 | OpenRouter/Ollama/LM Studio readiness and unified model health are in place. | Needs fallback policy, cost/speed/quality guidance, and clearer "recommended for this workflow" routing. |
| Workflow starter/catalog | 4/5 | Productized workflows and starter routing exist. | Needs dry-run preview, generated execution plan, and task-to-model routing. |
| Outcome packs/marketplace | 4/5 | Installable outcome packs, trust/readiness, launch, provenance, and recovery preview exist. | Needs Agent OS sandbox dry-runs, export-from-workflow, richer community submission, and analytics. |
| Artifact/replay/timeline | 3/5 | Artifact models, command blocks, mailbox/activity models, and timeline surfaces exist. | Needs backend-backed artifact download/view, replay, resume, and run outcome pages. |
| Safety/approvals | 3.5/5 | Tool approval queue and permission UX exist. | Needs true bulk decision API, time-bound approval presets, and route-level security/prompt-injection closeout. |
| Project/workspace/task cockpit | 3.5/5 | Sidebar, workspace selector, task board, agent roster, shipyard lanes, and drawer scaffolds exist. | Needs project coordination tied to persisted runs, artifacts, and Agent OS sessions. |
| Agent OS/container runtime | 3.5/5 | Contained Linux runtime, named sessions, scripts, and docs exist. | Needs UI recovery, self-checks, dry-run integration, resource/secrets posture, and default workspace flow. |

## Competitive refresh

| Reference | Source-backed signal | AGENT33 implication |
| --- | --- | --- |
| OpenAI Codex | Codex is positioned as a coding agent for writing, understanding, reviewing, debugging, and automating software work. | AGENT33 should keep run plans, review evidence, and automation outcomes visible, not hide them behind generic workflow forms. |
| Claude Code | Claude Code spans terminal, VS Code, desktop, web, JetBrains, remote control, channels, routines, actions, and review surfaces. | AGENT33 needs cross-surface continuity: local cockpit, recurring loops, PR/review artifacts, and project/session state should share one operating record. |
| OpenHands | OpenHands exposes SDK, CLI, Local GUI, Cloud, Enterprise, REST/React GUI, integrations, RBAC, collaboration, budgeting, and Docker/local modes. | AGENT33's local-first advantage is meaningful only if setup, sandbox status, approvals, and project artifacts are clearer than a raw local GUI. |
| Agent Zero | Agent Zero emphasizes a full Linux system in Docker, visible working surfaces, projects, profiles, skills, plugins, MCP/A2A, and inspectable agent work. | AGENT33 should double down on Agent OS, but add stronger governance, recovery, artifact lineage, and beginner-safe templates. |
| Google Jules | Jules markets workflows from quick fixes to async, multi-agent development. | AGENT33 should make scale levels obvious: quick task, project build, research loop, long-running program, and multi-agent shipyard. |
| Dify/Langflow/n8n/Activepieces pattern family | Low-code products win by presenting templates, connectors, visual flow, replay/history, and plain-language setup. | AGENT33 needs prebuilt outcome strategies and setup recipes; users should not need to understand internal JSON/import concepts. |

## Panel synthesis

The Wave 11 synthesis used the standing panel model from earlier waves: non-technical founder, small-business operator, solo developer, agency operator, enterprise product owner, customer-success lead, UX researcher, AI workflow architect, DevOps/SRE operator, and security/compliance reviewer. Three passes were applied: beginner comprehension, functional workflow depth, and feasibility/safety/recovery.

### Pass A: first-time comprehension

- The product now looks more like a cockpit than a settings dump, but first-time users still need one primary action per state.
- The Start/Outcome path must ask for the user's goal, classify the work, recommend a workflow/model/runtime, and show what will happen before anything runs.
- Advanced surfaces should remain available but not visually compete with "connect model," "choose outcome," "run safely," and "review result."

### Pass B: workflow/product depth

- Outcome packs are the strongest beginner-facing asset. They should become the default way to ship "pre-canned" capabilities, not just another marketplace tab.
- Workflows need generated run plans and dry-run previews so lay users understand inputs, outputs, risks, and likely artifacts.
- The cockpit needs to show the agent team and their output contracts: coordinator, researcher, builder, reviewer, safety/governance, and improvement analyst.

### Pass C: feasibility, safety, and recovery

- The historical security and persistence docs cannot be ignored, but several findings have already changed. For example, current `chat.py` calls `scan_input()`, and current settings fail or warn on default production secrets. Wave 12 must therefore perform a route-by-route verification and close the real remaining gaps rather than blindly replaying old notes.
- Persistence remains a credible blocker: `docs/functionality-and-workflows.md` still identifies review, trace/failure, evaluation, autonomy, release, improvement, workflow registry, and auth stores as in-memory or partially in-memory boundaries.
- Agent OS should become the safe dry-run and recovery substrate, but not by embedding a full IDE first. Start with readiness, session recovery, command/artifact evidence, and clear sandbox boundaries.

## Wave 12 implementation charter

Wave 12 is an even-numbered implementation wave. It should be split into fresh worktrees and PR-sized slices, merged sequentially.

### Wave 12 goal

Make AGENT33 safer and more useful out of the box by closing verified security/persistence gaps while adding a project/outcome path that lets a beginner start, preview, run, recover, and understand results without raw configuration.

### Wave 12 slices

1. **Security and persistence reality check**
   - Re-audit the historical IDOR, prompt-injection, SSRF, secret, CORS, approval-gate, and in-memory-state findings against `96e1c3e` or later.
   - Produce failing tests for any still-real route or persistence gaps before fixing them.
   - Close or supersede stale findings in docs so future agents do not keep planning from obsolete risk data.

2. **Prompt-injection and route-ownership closeout**
   - Ensure agent invoke, workflow execute, webhook, memory, and auth-key routes scan or authorize user-controlled inputs consistently with current patterns.
   - Add focused backend tests for rejected injection payloads and tenant/subject ownership checks.

3. **Durable operational state foundation**
   - Prioritize the state users rely on for continuity: review records, trace/failure records, workflow run history, evaluations/baselines, autonomy budgets, release/rollback records, and improvement lessons.
   - Prefer existing storage patterns and migrations over new bespoke stores.
   - Add restart-survival tests for one representative state path before expanding.

4. **Agent OS default workspace readiness**
   - Add an operator-facing Agent OS readiness and recovery surface: current session, last active workspace, health checks, tool versions, safe mount boundaries, and restart instructions.
   - Connect workflow/pack dry-run language to Agent OS when available.
   - Keep host execution opt-in and explicit.

5. **Outcome/project launch path v2**
   - Add a plain-language launch path: choose project or outcome, answer a short intake, see recommended workflow/outcome pack/model/runtime, then preview a run plan.
   - Route to existing Workflow Starter, Workflow Catalog, Pack Marketplace, Model Setup, and Agent OS surfaces rather than duplicating them.

6. **Bulk safety decisions and time-bound presets**
   - Add true batch decisions for routine approvals with a preview of affected tools, risk class, duration, and rollback/expiration.
   - Keep high-risk actions excluded unless explicitly selected in Pro mode.

7. **Artifact/replay backend depth**
   - Add backend-backed artifact download/view routes and richer run replay/timeline records.
   - Ensure artifacts can be tied to project, task, workflow, pack provenance, command block, and approval state.

### Wave 12 non-goals

- No full IDE clone.
- No 16-pane terminal default.
- No unsupervised browser/computer-use launch.
- No automatic model downloads.
- No enterprise RBAC expansion unless required to close a verified security flaw.
- No broad visual workflow builder until run plans, artifacts, approvals, and persistence are reliable.

### Wave 12 local validation gates

- Focused backend tests for each modified route/service.
- Migration or restart-survival tests for each new persistent state path.
- Focused frontend tests for any new beginner launch, Agent OS readiness, safety preset, or artifact UI.
- `npm run lint` and `npm run build` for frontend changes.
- Targeted pytest with `PYTHONPATH` set to the worktree's `engine\src`.
- Docker/Compose config validation for Agent OS changes.

## Wave 13 research/refinement charter

Wave 13 should evaluate Wave 12 results and decide how far to move the harness/cadre model from documentation into product behavior.

Research questions:

1. Which state paths remain in-memory or not restart-safe after Wave 12?
2. Did the beginner project/outcome path reduce clicks and setup confusion, or did it create another shallow wrapper?
3. Which cadres should be visible in the UI without adding cognitive load?
4. Which external patterns are now worth adopting: visual workflow builder, replay inspector, project collaboration, browser/computer-use, or marketplace curation depth?
5. What Evokore-MCP skills need updates so panel, research, implementation, and review loops produce reusable artifacts?

Wave 13 should reuse the Loop 5A/5B direction:

- AGENT33 is a harness-and-skills ecosystem, not a governance-first control plane.
- Governance is a cadre and guardrail, not the product's whole identity.
- Specialist cadres should have bounded inputs, outputs, tool scopes, model posture, and promotion rules.

Expected Wave 14 charter candidates:

- Cadre-aware agent invocation and UI labels.
- Task-to-model routing and fallback policy UI.
- Guided intake wizard depth.
- Skill contract language and runtime enforcement.
- Marketplace curation depth and featured outcome sets.

## Wave 14 implementation charter

Wave 14 should implement the strongest Wave 13 findings.

Likely implementation slices:

1. **Cadre-aware invocation**
   - Add runtime metadata and UI labels for Governance, Research/Ingestion, Synthesis/Judgment, Execution/Orchestration, Environment Specialist, and Improvement/Learning cadres.
   - Show what each cadre can do, what tools it can use, and what artifact it must return.

2. **Task-to-model routing and fallback policy**
   - Extend model setup from "connected or not" to "recommended for this task."
   - Add fallback behavior that is understandable by beginners and auditable by operators.

3. **Guided intake v3**
   - Convert "I only know the outcome" into a concrete intake-to-plan-to-preview path.
   - Classify quick task, project build, research workflow, improvement loop, and long-running program.

4. **Skill contract enforcement**
   - Define skill I/O expectations, evidence requirements, model/tool boundaries, and promotion metadata.
   - Surface contract failures as reviewable artifacts instead of silent agent drift.

5. **Marketplace curation depth**
   - Add featured sets, quality scoring explanations, contributor feedback, and pack analytics.

## Wave 15 research/refinement charter

Wave 15 should inspect whether the platform is ready to add more autonomous learning and environment control.

Research gates:

1. Are persistence, replay, approvals, and artifact lineage reliable enough for proposal-only self-improvement?
2. Does the cadre model reduce context rot and PR drift in real implementation waves?
3. Which project/workspace features are still blocking beginner adoption?
4. Is browser/computer-use safe enough behind feature flags and environment specialist oversight?
5. Do help/RAG answers reliably cite docs and route users to the right UI action?

Expected Wave 16 charter candidates:

- Replay checkpoint and resume UI.
- Multi-model panel judgment for high-impact proposals.
- Skill lineage and promotion audit.
- Proposal-only self-improvement sandbox.
- Browser/computer-use pilot behind strict feature flags.
- Demo mode with a sample project and canned artifacts.

## Onward wave ladder

The odd/even loop should continue:

| Wave | Type | Theme |
| --- | --- | --- |
| 16 | Implementation | Replay/resume, judgment panels, skill lineage, proposal-only learning sandbox. |
| 17 | Research | Compare replay/learning results against Codex, Claude Code, OpenHands, Agent Zero, v0, and low-code platforms. |
| 18 | Implementation | Browser/computer-use pilot, demo project, richer delivery artifacts, deployment readiness workflows. |
| 19 | Research | Enterprise/project collaboration review, pack ecosystem review, privacy/local-first review. |
| 20 | Implementation | Project collaboration, permissions depth, pack ecosystem scale, local/private helper RAG. |
| 21 | Research | Platform-balance review: ensure no single module consumed more than the allowed share of effort and rebalance the next implementation wave. |

## Rotation and drift controls

To avoid one idea taking over the entire platform:

1. Every implementation wave must include at least one beginner-facing slice and one foundation/reliability slice unless the wave charter explicitly documents why not.
2. No module may consume more than 40% of a four-wave window without a written exception.
3. Each implementation PR must state whether it improves setup, execution, safety, recovery, artifact visibility, or learning.
4. Odd waves must refresh competitor evidence and run at least three panel passes.
5. Any new subsystem must reuse existing cockpit, workflow, pack, session, approval, artifact, or Agent OS primitives unless the charter proves they are insufficient.

## Bottom line

Wave 11 recommends that Wave 12 start immediately with verified security/persistence closeout plus visible beginner launch/recovery depth. Waves 13-15 should then turn the harness/cadre model into a usable product layer and prepare replay, learning, and environment-control capabilities. This keeps AGENT33 aimed at the market position the user wants: a beginner-usable, local-first, governed agent operating cockpit with real workflows, real artifacts, and recoverable autonomous work.
