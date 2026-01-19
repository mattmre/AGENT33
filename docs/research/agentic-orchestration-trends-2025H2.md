# Agentic Orchestration for Coding (Trends & Practices — last 6 months)

**Window covered:** 2025-07-16 → 2026-01-16  
**Audience:** engineers building or operating multi-agent coding systems  
**Target repo:** **AGENT 33** (master aggregation repo for model-agnostic workflows)

---

## 0) Executive summary (what changed recently)

Over the last ~6 months, agentic coding has converged on a few practical “production patterns”:

1) **Standardized tool connectivity** is moving from bespoke adapters to **Model Context Protocol (MCP)** plus registries/discovery (notably GitHub’s MCP Registry). This reduces integration churn while increasing the need for governance and trust signals in tool catalogs.  
2) **Spec-first / plan-first** workflows are becoming default for non-trivial changes. “Spec-driven development” is now an explicit, repeatable process used to keep agents aligned, reduce thrash, and gate autonomy.  
3) **Agent harnesses** are being treated like CI runners: reproducible environments, initializer steps, progress logs, and clean-state guarantees—because autonomy only works when the environment is controlled.  
4) **Code execution (not just tool calls)** is trending as the scaling strategy for agents interacting with many tools. Agents write code to call tools on-demand, keep large intermediate data out of the LLM context, and preserve privacy.  
5) **Security posture is hardening** around sandboxing, approvals, network/domain allowlists, and explicit prompt-injection controls—especially when agents are allowed to browse or pull external context.  
6) **Evaluation and observability** are becoming first-class: teams are building internal benchmark suites and traces for “agent regressions,” not just model regressions.

---

## 1) Definitions (model-agnostic)

- **Orchestrator:** The component (or “role”) that decomposes, sequences, assigns, and verifies work across agents and tools.  
- **Agent harness:** The execution environment + runtime that provides filesystem, tool connectivity, run controls, logs, and persistence.  
- **Tool:** Any deterministic capability invoked by an agent (CLI commands, APIs, MCP servers, code execution environments, etc.).  
- **Evidence-first workflow:** A workflow where every non-trivial decision/change is backed by commands, tests, artifacts, and review outcomes.  
- **Autonomy budget:** A scoped permission envelope (files, commands, network) and task boundary that defines what an agent can do without human approval.

---

## 2) Trend map (last 6 months)

### 2.1 MCP consolidation + discovery registries
**Trend:** “tool sprawl” is being addressed by MCP plus centralized discovery experiences.  
**Implication:** adopt MCP, but treat MCP servers as supply-chain dependencies that require ownership, provenance, and verification signals.

- GitHub MCP Registry launches to reduce fragmented MCP discovery and its security risks, with curated listings and VS Code discovery/installation.  
- MCP is being used as a “common language” across coding agents and dev tools.

### 2.2 Spec-driven development and plan-first orchestration
**Trend:** Teams are formalizing a spec → implement → verify loop for agentic work.  
**Implication:** Make “spec artifacts” the stable anchor for multi-agent coordination, acceptance criteria, and auditability.

Practical effects:
- Fewer “agent wander” behaviors.
- Easier handoffs between agents (spec is the shared truth).
- Clearer review and minimal-diff enforcement.

### 2.3 Harnesses for long-running agents
**Trend:** “Agent runtime engineering” is now a discipline: initializer steps, deterministic environments, progress logs, and resumable state.  
**Implication:** Your orchestrator should treat environment setup and audit logging as mandatory.

Common harness patterns:
- **Initializer agent** to set up repo state, dependencies, and baseline checks.
- **Progress log** file updated every N steps.
- **Clean-state** guarantees between tasks (to prevent contamination).

### 2.4 Code execution with MCP to scale tool usage
**Trend:** As tool counts increase, direct tool-calling becomes token-expensive; agents increasingly **write code** to call tools only when needed.  
**Implication:** Provide a code execution environment (TypeScript/Python/etc.) plus a “tools-as-code” layer so agents can:
- Load only relevant tool schemas on-demand (“progressive disclosure”).
- Keep large intermediate results out of context.
- Apply deterministic policies to sensitive data flows.

### 2.5 Multi-agent “mission control” experiences
**Trend:** Platforms/IDEs are adding “manager views” and multi-agent coordination hubs.  
**Implication:** Your own orchestration layer should provide:
- Agent registry (roles/skills/capabilities)
- Work queue + priority system
- Audit and trace collection
- Unified evidence capture (commands/tests/artifacts)

### 2.6 Security hardening: sandbox + approvals + prompt injection
**Trend:** More vendors ship **sandboxing and approvals** as default for coding agents, and explicitly warn about prompt injection risks when enabling web/network access.  
**Implication:** Default to least privilege and make “danger modes” explicit and rare.

### 2.7 Benchmarking + regression control
**Trend:** Agents are being measured on task suites (e.g., SWE-bench–style tasks), with internal “golden tasks” becoming common.  
**Implication:** Build your own eval harness:
- “Golden PR” set (representative diffs)
- “Golden issues” set (repro steps + expected outcome)
- Continuous tracking of success, time-to-green, and diff size

---

## 3) Best practices (procedural intuitions)

### 3.1 Treat agents like junior engineers operating in a controlled environment
**Intuition:** Autonomy increases throughput only if you constrain scope and make verification cheap.  
**Practice:**
- Narrow tasks to a single subsystem or acceptance slice.
- Require tests or deterministic checks per slice.
- Enforce “minimal diffs” (patch-size limits, file allowlists).

### 3.2 Separate *planning* from *execution* and store both
**Intuition:** Agents hallucinate less when they can “see the contract” (spec) and you minimize mid-flight reinterpretation.  
**Practice:**
- PLAN artifact: goals, non-goals, assumptions, risks, acceptance checks.
- TASKS artifact: ordered queue with owners, preconditions, evidence required.
- STATUS artifact: what changed, what remains, blockers.
- DECISIONS artifact: what was chosen and why.
- PRIORITIES artifact: what to do next and what not to touch.

(Your AGENT 33 handoff protocol already matches this; the “trend” is that industry tooling is converging toward the same structure.)

### 3.3 Establish an “autonomy budget” per task
**Intuition:** A single task should have an explicit permission envelope and a hard stop condition.  
**Practice:**
- Workspace write scope (paths, file patterns)
- Command allowlist (safe commands)
- Network policy (off by default; allowlist by domain if needed)
- Approval gates (security-sensitive actions always require approval)
- Stop conditions (when tests fail twice; when scope expands; when ambiguity persists)

### 3.4 Always close the loop with verification
**Intuition:** Code generation is not the deliverable; passing checks is.  
**Practice:** For every task, define:
- **Primary verification** (unit/integration tests; lints; typecheck)
- **Secondary verification** (static analysis; security scan; smoke run)
- **Human review trigger** (risk triggers, see §4.3)

### 3.5 Prefer “diff-first” workflows
**Intuition:** PR diffs are the cheapest, most universal audit artifact.  
**Practice:**
- Require the agent to produce a patch/diff plus a rationale.
- Keep changes small, composable, and reviewable.
- Avoid “rewrite everything” unless explicitly authorized.

### 3.6 Use code execution + tool discovery instead of loading all tool schemas
**Intuition:** Tool schema bloat kills context.  
**Practice:**
- Provide a `search_tools` and “detail level” parameter (name-only vs full schema).
- Generate a “tools-as-code” filesystem tree; let agents read just what they need.
- Transform/filter large tool results in code before summarizing to the LLM.

### 3.7 Build “context files” that persist between sessions
**Intuition:** Agents improve when you preserve architectural context, conventions, and “gotchas.”  
**Practice:**
- Create a repo-level context file (e.g., `AGENTS.md`, `GEMINI.md`, etc.) with:
  - conventions, build/test commands
  - risky areas / do-not-touch zones
  - dependency pinning notes
  - where logs/evidence live
- Update it at the end of each session with deltas and lessons learned.

### 3.8 Adopt “two-layer review” for risky work
**Intuition:** A second “Reviewer agent” or human catches systemic issues the Worker misses.  
**Practice:**
- Reviewer reads the spec and the diff.
- Reviewer runs the verification commands (or checks logs).
- Reviewer checks security posture (secrets, dependencies, auth flows).
- Reviewer signs off in DECISIONS + PR summary.

---

## 4) Concrete guidance for AGENT 33 (what to add to `core/`)

### 4.1 Add a canonical “Agentic Coding Orchestration” research doc
**Recommended location:**
- `core/research/agentic-orchestration-trends-2025H2.md` (this file)
- Keep raw source captures (PDFs, copied excerpts) in `collected/` with a timestamp.

### 4.2 Add a portable “policy pack” to sync to all repos
**Goal:** push a small, consistent set of instruction files and checklists to every repo.

**Suggested pack (canonical in `core/packs/policy-pack-v1/`):**
- `AGENTS.md` (repo agent instructions / “how to work here”)
- `ORCHESTRATION.md` (handoff protocol + roles + AEP cycle)
- `EVIDENCE.md` (what evidence to capture, where to store it)
- `RISK_TRIGGERS.md` (security/schema/API/CI/CD/large-refactor review triggers)
- `ACCEPTANCE_CHECKS.md` (test/lint/typecheck conventions; per-language templates)
- `PROMOTION_GUIDE.md` (how to promote reusable workflows into `core/`)

### 4.3 Extend risk triggers with “agentic-specific” security triggers
Add the following to `core/*/risk-triggers` (or consolidate into one file):

- **Prompt injection exposure**
  - agent enabled web/network
  - agent consumes external content (docs, issues, PR comments) without sanitization
- **Sandbox escape / expanded permissions**
  - network enabled
  - running commands outside allowlist
  - editing outside workspace scope
- **Secrets + tokens**
  - changes touching auth, secrets loading, config files, CI variables
- **Supply chain**
  - new dependencies, lockfile changes, build scripts, package manager configs

### 4.4 Update promotion criteria to include “traceability artifacts”
When promoting from `collected/` → `core/`, require:
- a short “Why reusable?” note
- explicit acceptance checks
- evidence/log format compliance
- security notes if the workflow uses network/tooling

---

## 5) Reference orchestration loop (AEP++ aligned to your handoff protocol)

**A — Align (PLAN + PRIORITIES)**
- Clarify goal, constraints, non-goals.
- Define acceptance checks and evidence required.
- Set autonomy budget and risk triggers.

**E — Execute (TASKS + STATUS)**
- Orchestrator assigns tasks to Worker agents.
- Workers produce patches + evidence.
- Orchestrator updates STATUS after each milestone.

**P — Prove (DECISIONS + verification)**
- Run verification commands.
- Reviewer agent audits diff vs spec and checks risk triggers.
- Log decisions and promote reusable assets if applicable.

---

## 6) Evidence capture checklist (copy/paste friendly)

**Minimum evidence for any change beyond trivial edits:**
- Commands run (exact CLI)
- Tool outputs (test summary, lints, build logs)
- Artifacts generated (reports, screenshots, trace files)
- Diff summary (files changed, rationale)
- Verification results (pass/fail + follow-up)

**Suggested structure:**
- `docs/sessions/YYYY-MM-DD/<topic>/`
  - `plan.md`
  - `status.md`
  - `decisions.md`
  - `evidence.log` (or `evidence.md`)
  - `artifacts/` (reports, screenshots, traces)

---

## 7) Metrics that matter (agentic coding)

Track these at minimum:
- **Success rate** on your internal task suite (pass/fail)
- **Time-to-green** (first passing test run)
- **Diff size** (lines/files changed; “small diff” compliance)
- **Rework rate** (number of agent iterations before pass)
- **Human intervention points** (approvals requested, escalations)
- **Security signals** (dependency diffs, secrets scans, SAST results)

---

## 8) Common failure modes (and mitigations)

1) **Scope creep / refactor drift**  
   *Mitigation:* enforce file allowlists, patch-size limits, spec-based non-goals.

2) **Tool schema overload**  
   *Mitigation:* progressive disclosure + code execution, search_tools, tools-as-code.

3) **Non-deterministic environments**  
   *Mitigation:* initializer agent, pinned dependencies, containerized harness.

4) **Shallow verification**  
   *Mitigation:* acceptance checks required; run in CI; require logs.

5) **Prompt injection / confused deputy**  
   *Mitigation:* default no network; domain allowlists; sanitize external content; explicit approvals.

---

## 9) Source list (primary, dated)

**MCP + registries**
- GitHub: “Meet the GitHub MCP Registry” (Sep 16, 2025)  
  https://github.blog/ai-and-ml/github-copilot/meet-the-github-mcp-registry-the-fastest-way-to-discover-mcp-servers/
- GitHub: “Agentic AI, MCP, and spec-driven development” (Dec 30, 2025; updated Jan 14, 2026)  
  https://github.blog/developer-skills/agentic-ai-mcp-and-spec-driven-development-top-blog-posts-of-2025/

**Harnesses + code execution**
- Anthropic: “Code execution with MCP: Building more efficient agents” (Nov 4, 2025)  
  https://www.anthropic.com/engineering/code-execution-with-mcp
- Anthropic: “Harnesses for long-running agents” (Nov 26, 2025)  
  https://www.anthropic.com/engineering/harnesses-long-running-agents

**Spec-driven / context engineering**
- GitHub: “Spec-driven development with Spec Kit” (Sep 2, 2025)  
  https://github.blog/developer-skills/github/spec-driven-development-with-spec-kit/
- GitHub: “Agentic AI: agentic primitives and context engineering” (Oct 13, 2025)  
  https://github.blog/developer-skills/agentic-ai-agentic-primitives-and-context-engineering/
- Google Cloud: “Five Best Practices for Using AI Coding Assistants” (Oct 7, 2025)  
  https://cloud.google.com/blog/topics/developers-practitioners/five-best-practices-for-using-ai-coding-assistants

**Security + governance**
- OpenAI (Codex): “Security” (sandbox, approvals, network defaults; ongoing doc)  
  https://developers.openai.com/codex/security/
- OWASP: “Prompt Injection” (LLM Top 10 related guidance; ongoing page)  
  https://owasp.org/www-community/attacks/PromptInjection
- GitHub Security Lab: “Taskflow Agent” (Jan 14, 2026)  
  https://github.blog/security/community-powered-security-with-ai-an-open-source-framework-for-security-research/

**Evaluation**
- SWE-EVO benchmark paper (Dec 22, 2025)  
  https://arxiv.org/abs/2512.12470

---

## 10) Notes for maintainers (how to keep this “fresh”)

Every month:
1) Ingest new vendor/academic posts into `collected/` with timestamps.  
2) Extract reusable patterns into `core/` with a short decision log entry.  
3) Add/adjust checklists and templates only when they generalize (avoid tool-specific coupling).  
4) Update internal eval suite with 2–5 new tasks that reflect current pain points.  
5) Run a “refinement cycle” on the last N PRs and promote proven assets.

---

*End of file.*
