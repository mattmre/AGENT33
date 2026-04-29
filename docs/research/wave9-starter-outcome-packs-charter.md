# Wave 9 Starter and Outcome Packs Charter

## Scope

Wave 9 defines the next beginner-usability move after Wave 8 local model readiness: make repeatable outcomes installable, explainable, and runnable through starter packs instead of forcing operators to assemble workflows, skills, tools, governance, and provider settings by hand.

This is a research and architecture charter for Wave 10 implementation. It does not implement a new marketplace or workflow engine. It narrows the next work to a PR-sized sequence that turns existing pack, workflow, marketplace, provenance, and cockpit surfaces into an outcome-pack path a layperson can understand.

## Baseline evidence

Research for this wave used three focused passes:

1. Repo workflow/pack audit: current frontend/backend surfaces for outcome home, workflow starter, workflow catalog, pack marketplace, pack provenance, pack governance, workflow definitions, discovery, and outcomes.
2. Architecture and safety review: minimal starter-pack manifest, validation, install/run flow, approval gates, provenance, and test boundaries.
3. Competitive pattern review: Dify, Flowise, Langflow, Open WebUI, AnythingLLM, n8n, Activepieces, CrewAI, AutoGen Studio, LangGraph/LangSmith, Vercel v0, Claude Code, Codex-style task templates, and BridgeSpace-style workspace templates.

Relevant existing AGENT33 artifacts:

| Artifact | Reusable finding |
| --- | --- |
| `frontend/src/features/outcome-home/catalog.ts` | Twelve outcome templates already exist, but they are not installable pack units. |
| `frontend/src/features/outcome-home/productization.ts` | Per-workflow inputs, outputs, estimates, dry-run steps, and starter-pack hints already frame outcomes for beginners. |
| `frontend/src/features/workflow-starter/` | Plain-language goal to workflow draft exists, but it is not packaged as an installable starter experience. |
| `frontend/src/features/workflow-catalog/` | Catalog browse/filter exists, but it does not own pack install, trust, preview, and launch as one beginner flow. |
| `frontend/src/features/pack-marketplace/` | Pack browse/search/install and curation models exist, but the UI does not yet present outcome packs as the default way to start. |
| `engine/src/agent33/packs/` | Pack models, provenance, governance, marketplace, curation, dependencies, and registry concepts exist. |
| `engine/src/agent33/workflows/definition.py` | Workflow definitions can represent multi-step execution, dependencies, inputs, outputs, and metadata. |
| `engine/src/agent33/discovery/service.py` | Tools, skills, and workflow resolution can support pack search and recommendation. |
| `engine/src/agent33/outcomes/models.py` | Outcome events and trends can become the pack-run success and recovery layer. |
| `docs/research/session64-phase33-marketplace-integration.md` | Marketplace was intentionally shipped as a local, installable, testable MVP compatible with later registry promotion. |
| `docs/research/ux-overhaul-expert-panel-2026-04-27.md` | The durable UX principle remains "outcome before primitive"; workflows are the product surface. |
| `docs/research/wave5-competitor-refresh.md` | The market is converging on task, artifact, permission, approval, and outcome workbenches. |

## Problem statement

AGENT33 has many strong primitives, but beginners still see too much of the internal machinery. Workflows, skills, packs, marketplace records, providers, approval policies, and outcome tracking are split across surfaces. A layperson wants to start with "build my app", "research this market", "review this repo", or "run an improvement loop", then see what will happen, what it needs, whether it is safe, and how to recover.

Wave 10 should make starter and outcome packs the connective tissue:

- A pack is the installable unit.
- A workflow is the runnable plan inside the pack.
- Provider/tool requirements are checked before launch.
- Trust/provenance is visible before install.
- Safety defaults are enforced before execution.
- Artifacts and outcomes explain what happened after execution.

## Competitive synthesis

| Pattern | Strong external examples | AGENT33 implication |
| --- | --- | --- |
| Template-first onboarding | Dify, n8n, Activepieces, Vercel v0 | Put curated outcome packs before raw workflow/skill configuration. |
| Progressive disclosure | Dify-style app templates, Open WebUI-style extension UX, AGENT33 skill disclosure patterns | Beginner view should show outcome, trust, setup needs, and one primary action; advanced manifest details stay expandable. |
| Provider readiness before run | Dify, Flowise, Langflow, Open WebUI, AnythingLLM | Packs should declare model/tool needs and route users to Connect Center/local readiness before failed execution. |
| Dry-run and sandbox preview | n8n dry-run patterns, LangGraph trace/replay, Dify sandbox patterns | Operators should preview what a pack adds and run safe sample inputs before full use. |
| Trust badges and curation tiers | n8n/Activepieces community marketplace patterns | Official, verified, community, and imported packs need distinct badges and warnings. |
| Artifact-first completion | Claude Code/Codex/Vercel v0 review and handoff patterns | Pack runs should end in a visible artifact, PR/package, blocker, or next action. |
| Workspace templates and task boards | BridgeSpace-style shipyard pattern | Starter packs should map to cockpit tasks, roles, lanes, and review drawers instead of isolated forms. |
| Recovery and rollback | n8n versioning, LangGraph checkpoints, Agent OS recovery patterns | Install, upgrade, uninstall, and rollback should be previewable and auditable. |

AGENT33 should not copy visual marketplaces for their own sake. The competitive advantage is an outcome-first, safety-aware Agent OS cockpit: installable packs that explain requirements, set safe defaults, launch visible work, and preserve recovery.

## Starter/outcome pack concept

An outcome pack is an installable package that can include:

1. One or more workflow definitions.
2. Beginner-facing presentation metadata.
3. Required inputs and sample inputs.
4. Provider and tool requirements.
5. Governance constraints and approval requirements.
6. Provenance and trust metadata.
7. Setup checklist and demo/dry-run behavior.
8. Starter prompts, role hints, and expected deliverables.
9. Artifact and outcome tracking hints.

The pack should reuse existing pack and workflow infrastructure rather than create a separate marketplace subsystem.

## Minimal manifest extension

Wave 10 should avoid a broad schema rewrite. The smallest useful extension is an outcome-pack/starter-pack manifest layer that references or embeds existing workflow definitions and adds UX, setup, and governance metadata.

Recommended fields:

| Field | Purpose |
| --- | --- |
| `name`, `version`, `description`, `author`, `category`, `tags` | Existing pack identity and discovery. |
| `kind` | `workflow-starter`, `improvement-loop`, `automation-loop`, or `outcome-pack`. |
| `workflows` | Embedded workflow definitions or references to bundled workflow files. |
| `presentation` | Beginner title, audience, summary, difficulty, icon, estimated duration, expected deliverables. |
| `customization` | Required inputs, sample inputs, preset values, locked settings. |
| `provider_requirements` | LLM, embedding, local runtime, MCP, tool, and environment requirements with fallback preferences. |
| `governance` | Approval requirement, risk level, autonomy floor/ceiling, max parallel runs, max daily executions, allowed models/tools. |
| `provenance` | Source tier, signer, signature metadata, license, source URL, verification status. |
| `installation` | Setup checklist, dry-run support, auto-enable default, required runtime features. |
| `artifacts` | Expected artifacts, retention hint, and cockpit drawer sections to populate. |

Validation rules:

1. Pack name and version follow existing pack rules.
2. Every workflow reference resolves to a valid `WorkflowDefinition`.
3. Required inputs are present in workflow input specs.
4. Preset and locked values do not conflict.
5. Provider/tool requirements use known provider and tool identifiers.
6. Governance scopes and risk levels use known policy values.
7. All user-visible strings pass injection scanning consistent with existing security utilities.
8. Provenance is evaluated before install and again before execution for packs with revocation data.

## Beginner flow

The default path should be:

1. **Choose an outcome**: "Build a first app", "Research competitors", "Review a repo", "Generate tests", "Prepare release", or "Run improvement loop".
2. **See what the pack does**: plain-language summary, required inputs, expected outputs, estimated effort/cost, trust badge, and safety mode.
3. **Check readiness**: provider/model, local runtime, required tools, MCP services, and permissions.
4. **Preview install**: show added workflows, skills/tools, governance, and risks before changing state.
5. **Try sample**: dry-run with sample inputs or demo mode if full setup is missing.
6. **Install and launch**: create or enable the workflow and route the user into the cockpit task/run surface.
7. **Review result**: show artifacts, command blocks/logs, approvals, blockers, and the next action.

Beginner copy should avoid raw terms as the primary labels. Use "starter", "workflow", "tools it needs", "safety checks", and "what you will get" first; expose manifest, governance, dependency, and provenance details behind advanced sections.

## Safety and trust model

Trust tiers:

| Tier | Meaning | Default behavior |
| --- | --- | --- |
| Official | Maintained by AGENT33 maintainers | Install with clear trust badge and normal approval gates. |
| Verified | Reviewed community author or signed trusted source | Install with light warning and visible signer/source. |
| Community | Format-valid community submission without verified maintainer trust | Require explicit review before enable. |
| Imported | Local or unknown source | Require admin or high-friction approval before enable/run. |
| Untrusted | Failed signature, revoked, malformed, or policy-denied source | Block install or execution. |

Beginner-safe defaults:

1. No pack should auto-run after install.
2. First execution of medium/high-risk packs requires review.
3. Unknown or imported packs default to disabled after install.
4. Packs cannot silently request higher autonomy than the current cockpit permission mode.
5. Packs with missing provider/tool requirements route to setup, not failed execution.
6. Destructive tools require clear risk copy and approval.
7. Uninstall/upgrade should preview dependent workflows and possible breakage before action.

## Wave 10 implementation sequence

Each item should be its own fresh worktree and PR from latest `origin/main`, merged before the next slice.

### 10.1 Research charter and docs handoff

Deliver this Wave 9 charter as the durable scope lock for Wave 10.

Acceptance:

- Records repo audit, competitive synthesis, architecture decisions, non-goals, and PR queue.
- Updates session plan and SQL task tracker.
- Does not change runtime behavior.

### 10.2 Starter/outcome pack manifest model

Add a small backend model and schema for outcome/starter pack metadata that composes existing pack and workflow models.

Likely files:

- `engine/src/agent33/packs/outcome_pack.py`
- `engine/tests/test_outcome_pack.py`
- optional shared schema under `core/schemas/` if the repo already uses that convention.

Acceptance:

- Valid manifest parses.
- Invalid workflow references fail.
- Required inputs must match workflow inputs.
- Provider/tool requirements validate against known identifiers where available.
- Injection-like strings are rejected using existing security helpers.

### 10.3 Pack readiness and safe-default policy

Create a readiness/policy service that evaluates whether a starter pack can be installed or run safely for the current operator mode.

Likely files:

- `engine/src/agent33/packs/starter_policy.py`
- route/service tests near existing pack tests.

Acceptance:

- Reports provider/model/tool/MCP requirements as ready, missing, or blocked.
- Applies beginner defaults without breaking advanced users.
- Refuses untrusted/revoked packs where trust data is present.
- Emits human-readable reasons suitable for UI cards.

### 10.4 Pack preview and trust badges in marketplace UI

Make trust, setup requirements, workflows added, and safety defaults visible before install.

Likely files:

- `frontend/src/features/pack-marketplace/TrustBadge.tsx`
- `frontend/src/features/pack-marketplace/PackPreview.tsx`
- existing marketplace page/detail tests.

Acceptance:

- Official/verified/community/imported/untrusted badges render with clear copy.
- Preview shows workflows, required providers/tools, governance, and expected outputs.
- Install button state reflects blocked or review-required status.
- Advanced manifest details are available without dominating beginner view.

### 10.5 Official seed outcome packs

Ship a small set of official seed packs that prove the path.

Recommended seeds:

1. Founder MVP Builder.
2. Competitor Research Brief.
3. Repository Security Review.
4. Test Generation Sprint.
5. Release Readiness Checklist.

Acceptance:

- Each seed pack includes beginner summary, required inputs, sample input, expected deliverables, governance, and workflow reference.
- Packs are discoverable in existing marketplace/catalog surfaces.
- Tests prove seed manifests load and pass validation.

### 10.6 Install pack to launch outcome flow

Connect Outcome Home/Workflow Catalog to pack preview, install, and workflow launch.

Likely files:

- `frontend/src/features/outcome-home/`
- `frontend/src/features/workflow-catalog/`
- `frontend/src/features/pack-marketplace/`

Acceptance:

- Beginner can start from an outcome card and reach preview/install/launch without raw JSON.
- Missing providers route to Connect Center/model readiness.
- Installed pack launches a workflow draft or execution path using existing workflow APIs.
- Empty and error states explain the next action.

### 10.7 Pack run artifacts and outcome tracking

Link pack-launched workflows to cockpit artifacts and outcome events.

Acceptance:

- Pack run records include pack name/version, workflow, inputs summary, status, and artifacts.
- Outcome events can distinguish pack-launched workflows.
- Cockpit drawer or run timeline can show pack context and next action.

### 10.8 Upgrade, uninstall, and rollback preview

Expose recovery before enabling community-scale pack use.

Acceptance:

- Preview upgrade/uninstall impacts before action.
- Show dependent workflows or agent/tool settings where detectable.
- Rollback path is visible where backend support exists.
- Unsafe uninstall states require confirmation or are blocked.

## Non-goals for Wave 10

Wave 10 should not attempt:

1. A full remote marketplace redesign.
2. A visual workflow builder.
3. Full enterprise RBAC.
4. Multi-user collaboration.
5. Native terminal/editor panes.
6. Browser model downloads.
7. SAT-solver-grade dependency resolution if existing dependency support is enough.
8. Community submission UI expansion beyond trust/readiness surfaces.
9. Long-running autonomous program builder.
10. A new workflow execution engine.

## Architecture decisions

| Decision | Rationale |
| --- | --- |
| Reuse packs and workflows instead of creating a new subsystem. | Existing models already cover identity, governance, provenance, dependencies, marketplace, and workflow structure. |
| Start with official seed packs. | Beginner value needs curated examples before community scale. |
| Make readiness evaluation explicit. | Failed execution is worse UX than setup guidance. |
| Keep trust visible but progressive. | Beginners need simple badges; experts need signer/source/manifest details. |
| Route launch into cockpit artifacts. | Packs should produce reviewable work, not disappear into background jobs. |
| Treat imported packs as high-friction by default. | Safety and provenance are central to user trust. |

## Panel synthesis

| Persona | Key concern | Wave 10 response |
| --- | --- | --- |
| Non-technical founder | "What can I do right now?" | Outcome cards and seed packs lead with deliverables and sample inputs. |
| Small-business operator | "Will this break my setup or cost money?" | Readiness and governance preview before install/run. |
| Solo developer | "Can I inspect what it will run?" | Advanced manifest, workflow, dependency, and command/artifact details remain available. |
| Agency operator | "Can I repeat this for clients?" | Packs become reusable, auditable starter workflows with predictable outputs. |
| Enterprise product owner | "Can this scale into programs later?" | Pack context and outcome events prepare for program-level orchestration. |
| Customer-success lead | "Can users recover when setup is missing?" | Missing provider/tool states route to setup and sample/demo paths. |
| UX researcher | "Does this reduce anxiety?" | Progressive disclosure and one primary next action per state. |
| AI workflow architect | "Are workflows first-class products?" | Workflows are bundled, versioned, governed, and launched as packs. |
| SRE/DevOps operator | "Can we observe and roll back?" | Artifacts, audit, and uninstall/upgrade preview are required follow-ups. |
| Security/compliance reviewer | "Can untrusted code run?" | Trust tiers, approval gates, and revocation checks block unsafe paths. |

## Success criteria

Wave 10 is successful when a fresh operator can:

1. Choose a curated outcome pack from the cockpit or workflow catalog.
2. Understand what it will do, what it needs, what it will produce, and why it is trusted.
3. See missing provider/tool/runtime requirements before installation or execution.
4. Install a safe official pack without raw JSON or manifest editing.
5. Launch the associated workflow and see artifacts/outcome state afterward.
6. Avoid or recover from unsafe install, missing setup, failed run, upgrade, or uninstall states.

## Open follow-ups after Wave 10

These should remain backlog unless Wave 10 evidence proves they are blocking:

1. Remote marketplace promotion and external registry trust.
2. Community pack submission UI and contributor analytics.
3. Full pack analytics dashboard.
4. Advanced dependency visualization.
5. Pack export from custom workflows.
6. Agent OS sandbox integration for pack dry-runs.
7. Optional local RAG/help assistant integration for pack-specific support.

## Bottom line

Wave 9 recommends making installable starter and outcome packs the next major usability layer. AGENT33 already has enough infrastructure to stop presenting workflows, skills, packs, providers, and safety policies as separate primitives. Wave 10 should connect them into a guided path: choose outcome, preview trust and setup, install safely, run visibly, review artifacts, and recover confidently.
