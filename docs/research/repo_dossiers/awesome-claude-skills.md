# Repo Dossier: ComposioHQ/awesome-claude-skills
**Snapshot date:** 2026-02-14

## 1) One-paragraph summary
ComposioHQ/awesome-claude-skills is a community-curated catalog of 944+ Claude Skills and integrations, serving as both a skill marketplace and distribution channel for the Claude ecosystem (Claude.ai, Claude Code, Claude API). The repository combines two distinct models: (1) standalone skills following Anthropic's SKILL.md standard for task automation, documentation, and workflows; and (2) Composio-powered integrations providing authenticated tool access to 500+ SaaS applications through a unified MCP-based API abstraction layer. With 34.7k stars and 3.4k forks, it represents the largest community-driven skill ecosystem for Claude, emphasizing real-world problem-solving, contribution accessibility, and cross-platform portability (skills work identically across all Claude surfaces).

## 2) Core orchestration model
**No orchestration** — this is a catalog and distribution repository, not a runtime framework. The orchestration models exist externally in two forms:

1. **Anthropic Agent Skills Standard** (agentskills.io): Skills are YAML frontmatter + Markdown instruction files (`SKILL.md`) that extend Claude's capabilities. Orchestration happens at runtime when Claude Code or Claude.ai loads skill descriptions into context (2% of context window, ~16k chars) and invokes full skill content when relevant or when users trigger via `/skill-name` slash commands. Skills can set `context: fork` to run in isolated subagent contexts with specific agent types (Explore, Plan, general-purpose, or custom `.claude/agents/` definitions). The skill itself becomes the prompt that drives the subagent.

2. **Composio Integration Platform**: For 500+ app integrations (Slack, GitHub, Gmail, Salesforce, etc.), Composio serves as a Tool Router + MCP Gateway that abstracts authentication (OAuth, API keys via centralized dashboard at app.composio.dev), translates LLM tool calls into API requests, and handles response formatting. The `connect-apps` plugin enables Claude to "send emails, create issues, post to Slack" through function calling without custom code.

**Key insight**: The repository conflates two paradigms — lightweight Markdown skills (zero infrastructure) and heavy platform integrations (Composio backend required). Both share the "skill" label but have radically different runtime dependencies.

## 3) Tooling and execution
**Skill-level execution** (SKILL.md standard):
- **Dynamic command injection**: `!`command`` syntax preprocesses shell commands before sending to Claude. Example: `!`gh pr diff`` fetches live PR data, replaces placeholder with output, then Claude sees rendered result. This is preprocessing, not LLM-executable code.
- **Bundled scripts**: Skills can include `/scripts`, `/references`, `/assets` directories. Example: `codebase-visualizer` skill bundles a Python script that generates interactive HTML tree views. Claude runs `python ~/.claude/skills/codebase-visualizer/scripts/visualize.py .` via allowed-tools: `Bash(python *)`.
- **String substitution**: `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, `${CLAUDE_SESSION_ID}` for parameterized skills.
- **Tool restrictions**: `allowed-tools` field grants Claude pre-approved tool access (e.g., `allowed-tools: Read, Grep, Glob` for read-only mode).
- **Model override**: `model` field specifies which Claude model to use when skill is active.

**Composio-level execution**:
- Skills in `*-automation/` directories are Composio tool definitions with "real tool slugs from APIs" (per README).
- Execution path: Claude function call → Composio Tool Router → authenticated API request → response normalization → return to Claude.
- Authentication handled externally via `platform.composio.dev` API key + OAuth flows managed by Composio.
- Observability: "Tool Visualization - See tool inputs/outputs in the sidebar" (from open-claude-cowork repo).

**No local runtime** — skills are passive Markdown files until Claude Code or Composio MCP server activates them.

## 4) Observability and evaluation
**Zero observability in the repository itself.** The repo is a catalog, not an execution environment. Observability exists only in the runtimes that load these skills:

1. **Claude Code runtime** (per documentation):
   - `/context` command shows skill loading budget (2% of context window, 16k char fallback)
   - Warning when skills exceed budget and are excluded
   - Tool call logs visible in sidebar (for Composio integrations)
   - No telemetry on skill success/failure rates, usage frequency, or error patterns

2. **Composio platform** (inferred):
   - "Complete audit trails" (SOC2/ISO certified)
   - Tool input/output visualization
   - Action-level RBAC
   - No mention of skill performance metrics, A/B testing, or quality gates

**No evaluation framework.** Contribution guidelines require skills be "tested across Claude.ai, Claude Code, and/or API" but provide no test harnesses, assertions, or regression suites. Quality control is manual PR review, not automated testing.

**Community signals as proxy metrics**:
- 116 open PRs → high contribution volume, potentially slow review velocity
- 48 open issues → modest bug/enhancement backlog
- 3.4k forks → many derivative skill sets, fragmentation risk

## 5) Extensibility
**High extensibility through multiple mechanisms**:

1. **Contribution model** (Apache 2.0 license):
   - Fork → feature branch → PR workflow
   - Required: `SKILL.md` in `skill-name/` directory
   - Optional: bundled scripts, references, assets
   - Documentation standard: 8 sections (When to Use, What It Does, How to Use, Examples, Tips, Use Cases, Attribution)
   - Alphabetical ordering within 5 categories: Business & Marketing, Communication & Writing, Creative & Media, Development, Productivity & Organization

2. **Skill packaging layers**:
   - **Enterprise**: Managed settings (organization-wide deployment)
   - **Personal**: `~/.claude/skills/` (all projects for user)
   - **Project**: `.claude/skills/` (version-controlled, repo-specific)
   - **Plugin**: `<plugin>/skills/` (distributed via Claude Code plugin system)
   - **Additional directories**: `--add-dir` flag for monorepo/multi-project setups

3. **Composio SDK extensibility**:
   - `composio-sdk/` directory in repo suggests developers can create custom app integrations
   - `skill-creator/` utility for scaffolding new skills
   - `mcp-builder/` for MCP server construction
   - 128M+ org identifier suggests large ecosystem beyond this single repo

4. **Cross-platform portability**:
   - Skills work identically on Claude.ai (skill icon in chat), Claude Code (`/skill-name` commands), and Claude API (programmatic invocation)
   - Agent Skills standard (agentskills.io) claims compatibility with "Codex, Antigravity, Gemini CLI, Cursor" (per VoltAgent/awesome-agent-skills fork)

**Limitations**:
- No versioning standard for skills (README suggests "git tags" but no enforcement)
- No dependency declaration format (skills can't declare "requires skill X" or "Python 3.11+")
- No namespace collision prevention beyond directory names
- Composio integrations require external platform account (not self-hostable)

## 6) Notable practices worth adopting in AGENT-33

### 1. **Progressive skill disclosure model** ⭐⭐⭐
**What**: Skills have three loading tiers:
- L0: Metadata (name + description, ~100 words) — always in context
- L1: SKILL.md body (<5k words) — loaded when skill triggers
- L2: Bundled resources (scripts, references, assets) — loaded as needed by Claude

**Why it matters**: AGENT-33 currently injects full `AgentDefinition.prompts.system` at startup (all-or-nothing). Skill descriptions are essentially agent capability summaries. Loading only summaries until invocation would dramatically reduce base prompt size.

**AGENT-33 adoption**: Modify `agents/runtime.py:_build_system_prompt()` to inject only `AgentDefinition.description` + capability list into base prompt. Load full system prompt template only when agent is invoked via `POST /v1/agents/{agent_id}/invoke`.

### 2. **Frontmatter-driven invocation control** ⭐⭐⭐
**What**: Skills use YAML frontmatter to declare:
- `disable-model-invocation: true` → only users can invoke (for `/deploy`, `/commit`, etc.)
- `user-invocable: false` → only LLM can invoke (for background knowledge)
- `allowed-tools: Read, Grep, Glob` → pre-approved tool access when skill active
- `context: fork` + `agent: Explore` → run in isolated subagent

**Why it matters**: AGENT-33's governance layer exists in `GovernanceConstraints` but is never enforced in prompts. Frontmatter makes governance declarative and enforceable at runtime.

**AGENT-33 adoption**:
- Add `invocation_mode: Literal["user-only", "llm-only", "both"]` to `AgentDefinition`
- Add `allowed_tools: list[str]` to override global tool allowlist per agent
- Add `execution_context: Literal["inline", "fork"]` for subagent routing
- Enforce in `agents/runtime.py:invoke()` before LLM call

### 3. **Dynamic command injection (`!`command``)** ⭐⭐
**What**: Skills can embed shell commands in prompts that run *before* the prompt is sent to the LLM:
```markdown
## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`
```
Output replaces placeholders, so Claude receives actual data, not commands.

**Why it matters**: AGENT-33's workflow actions are static (no runtime data fetching in prompt construction). This pattern enables "just-in-time context injection" without hardcoding API calls in workflow definitions.

**AGENT-33 adoption**:
- Add `_preprocess_prompt()` method to `agents/runtime.py` that regex-scans for `!`cmd`` patterns
- Execute via `execution/executor.py:CodeExecutor` with disclosure level L0 (no user approval for read-only commands)
- Security: restrict to allowlisted commands (e.g., `git`, `gh`, `curl`, `jq`) or require `allowed-tools` declaration

**Risk**: Command injection vulnerability if user-controlled input reaches prompt templates. Mitigation: only allow in agent definitions (trusted), not user messages.

### 4. **Skill bundling with scripts + references** ⭐⭐
**What**: Skills are directories, not single files:
```
codebase-visualizer/
├── SKILL.md (instructions)
├── scripts/visualize.py (generates interactive HTML)
└── examples/sample-output.html (reference)
```
SKILL.md references bundled files: "Run `python ~/.claude/skills/codebase-visualizer/scripts/visualize.py .`"

**Why it matters**: AGENT-33 agents have no bundled artifacts. The `codebase-visualizer` pattern (script generates HTML, opens in browser) shows how to extend agents beyond text I/O.

**AGENT-33 adoption**:
- Allow `agent_definitions_dir` to contain subdirectories: `agent-id/definition.json`, `agent-id/scripts/`, `agent-id/templates/`
- Add `artifacts_dir` field to `AgentDefinition` pointing to relative path
- Modify `tools/builtins/shell.py` to support `cwd={agent.artifacts_dir}` for bundled script execution
- Use case: `qa-agent` bundles Playwright test templates, `code-worker` bundles linter configs

### 5. **Contribution template rigor** ⭐
**What**: `CONTRIBUTING.md` mandates exact skill structure:
- Frontmatter: name, description (one sentence)
- Sections: When to Use, What It Does, How to Use (Basic & Advanced), Example, Tips, Common Use Cases
- Attribution: "Inspired by: [Person/Source]"
- PR format: "Add [Skill Name] skill" + description of real-world use case

**Why it matters**: AGENT-33 has no contribution process for agents. If we open-source agent definitions, this template ensures consistency.

**AGENT-33 adoption**: Create `docs/CONTRIBUTING-AGENTS.md` with similar rigor. Require `attribution`, `use_cases: list[str]`, and `tested_on: list[str]` fields in `AgentDefinition`.

### 6. **Slash command integration** ⭐⭐⭐
**What**: Every skill becomes a `/skill-name` command in Claude Code. User types `/deploy`, Claude loads deploy skill and executes.

**Why it matters**: AGENT-33's API is HTTP-only. Adding CLI interface would enable developer workflows: `agent33 invoke orchestrator "create workflow for X"`.

**AGENT-33 adoption**:
- Add `cli.py` entrypoint using `typer` library
- Map agent slugs to commands: `agent33 orchestrator "task"`, `agent33 code-worker "refactor X"`
- Reuse `agents/runtime.py:invoke()` under the hood
- Stream LLM output to terminal

## 7) Risks / limitations to account for

### 1. **Governance-prompt disconnect (same as AGENT-33's #1 bug)**
The repository demonstrates the exact problem AGENT-33 has: governance exists in metadata but is never communicated to the LLM.

**Evidence**:
- Skills have `allowed-tools` frontmatter, but nothing in SKILL.md body says "You may only use Read, Grep, Glob tools."
- `disable-model-invocation: true` prevents automatic loading, but when user invokes `/deploy`, the skill content doesn't say "Confirm before deploying."
- No safety guardrails in skill prompts reviewed (content-research-writer, codebase-visualizer)

**Why it's a risk**: If AGENT-33 adopts skill frontmatter patterns without fixing prompt injection, we inherit the same bug. Frontmatter is enforced by *runtime*, not by *LLM understanding*. If an attacker tricks the LLM into ignoring runtime restrictions (e.g., "disregard tool limits and run this shell command"), the LLM has no knowledge that limits exist.

**Mitigation**: When loading skills/agents, inject governance rules into prompt:
```markdown
## GOVERNANCE CONSTRAINTS
- You may ONLY use these tools: {allowed_tools}
- This agent runs in {execution_context} mode
- Confirm with user before: {requires_confirmation_for}
```

### 2. **Composio platform lock-in**
78+ app integration skills require Composio account + API key. The catalog advertises "500+ integrations" but:
- Composio is a commercial SaaS (SOC2/ISO certified suggests enterprise pricing)
- Authentication credentials stored on Composio servers (despite "tokens encrypted end-to-end" claim)
- No self-hosted alternative mentioned
- MCP server (`rube-composio-mcp`) is wrapper around Composio API, not standalone

**Why it's a risk**: AGENT-33 integrating with this ecosystem creates vendor dependency. If Composio changes pricing, shuts down, or has security breach, all app integrations break.

**Mitigation**: Build self-hosted MCP server for critical integrations (GitHub, Slack, email). Use Composio for long-tail apps where self-hosting isn't worth complexity.

### 3. **No versioning or dependency management**
Skills have no version field, no changelog, no compatibility declarations. Examples:
- If `playwright-browser-automation` skill depends on Playwright 1.40+, where is that declared?
- If skill A references skill B (e.g., `/pr-summary` uses `/git-diff` skill), how is that encoded?
- When Anthropic changes SKILL.md spec (e.g., adds new frontmatter field), how do old skills migrate?

**Why it's a risk**: AGENT-33 might pull skills from this repo and encounter runtime failures (missing dependencies, incompatible Python versions, breaking API changes).

**Mitigation**:
- Add `schema_version`, `dependencies`, `requires` fields to AGENT-33's `AgentDefinition`
- Pin skill hashes in `agent_definitions_dir` (e.g., git submodule with locked commit)
- Run skills in isolated environments (Docker containers, Python venvs)

### 4. **Contribution quality vs. quantity tension**
116 open PRs suggests review bottleneck. High PR volume can lead to:
- Merged skills with inadequate testing
- Duplicate/overlapping skills (e.g., 5 different changelog generators)
- Malicious skills (e.g., skill that exfiltrates env vars to attacker server)

**Evidence**:
- Contributing guide says "tested across Claude.ai, Claude Code, and/or API" but provides no test harness
- No CI/CD checks visible (no `.github/workflows/` mentioned)
- 944 skills but only 48 open issues → either skills are flawless (unlikely) or users don't report bugs in catalog

**Why it's a risk**: If AGENT-33 auto-imports skills from this repo, we inherit untested/malicious code.

**Mitigation**:
- Curate allowlist of verified skills (don't auto-sync entire repo)
- Require code review + sandboxed execution test before importing
- Run skills in restricted sandbox (Phase 13's `SandboxConfig` with `network_access: false`, `filesystem_access: "read-only"`)

### 5. **Context window budget exhaustion**
Skills load descriptions into Claude's context (2% of window, 16k chars fallback). With 944 skills:
- Assume avg 50 chars per description → 47k chars → exceeds budget by 3x
- Claude Code's solution: exclude skills that don't fit
- No prioritization mechanism (which skills are excluded? Random? Alphabetical?)

**Why it's a risk**: AGENT-33's agent registry loads all 6 agents' capabilities into prompt. If we adopt skill model and scale to 100+ agents, we hit same limit.

**Mitigation**:
- Semantic skill search: embed skill descriptions, retrieve top-K relevant to user query
- Lazy loading: only load agent descriptions when user asks "what can you do?"
- Hierarchical summaries: group agents by category, load category list first, expand on demand

### 6. **No execution isolation for bundled scripts**
Skills can bundle arbitrary Python/Bash scripts. Example: `codebase-visualizer` runs Python script that:
- Scans filesystem (`path.iterdir()`)
- Writes HTML file (`output.write_text(html)`)
- Opens browser (`webbrowser.open()`)

**Security issues**:
- Script has full filesystem access (could read `~/.ssh/id_rsa`, `.env` files)
- Script has network access (could exfiltrate data)
- Script runs in user's Python environment (could `pip install malware`)
- No sandboxing mentioned in documentation

**Why it's a risk**: If AGENT-33 executes bundled scripts from community skills, we enable arbitrary code execution.

**Mitigation**: Use Phase 13's `CodeExecutor` with:
- `SandboxConfig(network_access: false, filesystem_access: "project-only")`
- `ExecutionContract` validation for all script invocations
- Disclosure level L2 (show user full script + confirm before execution)

## 8) Feature extraction (for master matrix)

| Feature | Implementation | AGENT-33 Status | Priority |
|---------|---------------|-----------------|----------|
| **Progressive skill disclosure** | 3-tier loading (metadata → body → resources) | ❌ All-or-nothing agent loading | P0 |
| **Frontmatter governance** | `allowed-tools`, `disable-model-invocation`, `context: fork` | ❌ Governance exists but not enforced | P0 |
| **Dynamic command injection** | `!`cmd`` preprocessing in prompts | ❌ Static workflow actions only | P1 |
| **Skill bundling** | Directory structure with scripts/references/assets | ❌ Single JSON definition per agent | P1 |
| **Slash command interface** | `/skill-name` triggers skill invocation | ❌ HTTP API only, no CLI | P2 |
| **String substitution** | `$ARGUMENTS`, `$N`, `${CLAUDE_SESSION_ID}` | ✅ Workflow expressions support similar patterns | ✅ |
| **Skill packaging layers** | Enterprise/personal/project/plugin scopes | ⚠️ Single `agent_definitions_dir`, no hierarchy | P2 |
| **Composio-style MCP gateway** | Unified auth + tool router for 500+ apps | ❌ Direct tool implementation, no abstraction layer | P3 |
| **Community contribution flow** | Fork → PR with strict template | ❌ No contribution process for agents | P3 |
| **Cross-platform skill portability** | Same skill works on Claude.ai, Code, API | ⚠️ Agents only work in AGENT-33 engine | P2 |
| **Subagent context forking** | `context: fork` + `agent: Explore` | ✅ Subagent workflows exist (Phase 21) | ✅ |
| **Tool access restrictions** | `allowed-tools` per skill | ⚠️ Global allowlist only, no per-agent override | P1 |
| **Visual output generation** | Scripts generate HTML/visualizations | ❌ Text-only agent responses | P2 |
| **Session-scoped variables** | `${CLAUDE_SESSION_ID}` for logging/files | ⚠️ Session tracking exists but not exposed to agents | P2 |
| **Model override** | `model` field per skill | ❌ Global model config, no per-agent override | P2 |
| **Skill versioning** | Suggested (git tags) but not enforced | ❌ No versioning for agents | P2 |
| **Dependency declaration** | ❌ Not implemented | ❌ Not implemented | P3 |
| **Automatic nested discovery** | Monorepo support via `.claude/skills/` in subdirs | ❌ Flat `agent_definitions_dir` only | P3 |
| **Skill marketplace/catalog** | 944 skills, 34.7k stars, 116 PRs | ❌ No agent marketplace | P3 |
| **Attribution tracking** | Required "Inspired by: [Source]" field | ❌ No attribution in `AgentDefinition` | P3 |
| **Hooks integration** | Skills can define lifecycle hooks | ⚠️ Global hooks exist, no skill-scoped | P2 |

**Legend**: ✅ Implemented | ⚠️ Partial | ❌ Missing | P0 = Critical | P1 = High | P2 = Medium | P3 = Low

## 9) Evidence links

### Primary Repository
- [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) - Main repository (34.7k stars, 944 skills)
- [awesome-claude-skills README](https://github.com/ComposioHQ/awesome-claude-skills/blob/master/README.md) - Skill categories and installation
- [CONTRIBUTING.md](https://github.com/ComposioHQ/awesome-claude-skills/blob/master/CONTRIBUTING.md) - Contribution guidelines and skill template

### Official Anthropic Documentation
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills) - Official skill specification
- [Agent Skills Standard](https://agentskills.io) - Open standard for agent skills (cross-platform)
- [Anthropic Skills Repository](https://github.com/anthropics/skills) - Official Anthropic skills repo
- [skill-creator/SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) - Official skill template

### Example Skills Reviewed
- [content-research-writer/SKILL.md](https://github.com/ComposioHQ/awesome-claude-skills/blob/master/content-research-writer/SKILL.md) - Content creation workflow
- [document-skills/](https://github.com/ComposioHQ/awesome-claude-skills/tree/master/document-skills) - Document processing skills

### Composio Platform Integration
- [ComposioHQ/open-claude-cowork](https://github.com/ComposioHQ/open-claude-cowork) - Open source Composio integration
- [ComposioHQ/composio](https://github.com/ComposioHQ/composio) - Main Composio platform (100+ integrations)
- [Composio MCP Gateway](https://composio.dev/mcp-gateway) - MCP integration architecture
- [rube-composio-mcp](https://github.com/DrDavidHall/rube-composio-mcp) - MCP server for 500+ apps
- [Composio Integrations](https://composio.dev/toolkits/composio) - Platform overview

### Community Forks & Alternatives
- [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) - Community fork focused on Claude Code
- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) - 300+ skills compatible with multiple AI tools
- [karanb192/awesome-claude-skills](https://github.com/karanb192/awesome-claude-skills) - 50+ verified skills collection

### Technical Guides
- [Inside Claude Code Skills: Structure, prompts, invocation](https://mikhail.io/2025/10/claude-code-skills/) - Technical deep dive
- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/) - Architecture analysis
- [SKILL.md Structure Guide](https://skywork.ai/blog/ai-agent/claude-skills-skill-md-resources-runtime-loading/) - Format specification
- [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) - Anthropic engineering blog

### Related Resources
- [Anthropic Building Skills for Claude](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) - Official skill creation guide
- [MCP Integration Guides](https://composio.dev/toolkits/front/framework/claude-code) - Framework integrations
- [The Ultimate Claude Code Resource List (2026 Edition)](https://www.scriptbyai.com/claude-code-resource-list/) - Community resources
- [Claude Skills for DevOps](https://www.pulumi.com/blog/top-8-claude-skills-devops-2026/) - Industry use cases
