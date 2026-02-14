# Repo Dossier: anthropics/claude-plugins-official
**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

The `claude-plugins-official` repository is Anthropic's curated marketplace for Claude Code extensions, providing a standardized plugin architecture that enables both Anthropic-developed and third-party plugins to extend Claude Code functionality. The system supports multiple integration types (slash commands, agent definitions, skills, MCP servers, LSP servers, and lifecycle hooks) through a unified manifest-based structure, with plugins distributed via git repositories, npm, pip, or direct URLs. The architecture emphasizes security through explicit user trust requirements, scoped installations (user/project/local/managed), and organizational controls via managed settings, while maintaining simplicity through optional manifests, automatic component discovery from conventional directory layouts, and environment variable expansion for shared configurations.

## 2) Core orchestration model

**Plugin discovery and installation:**
- **Marketplace-based distribution:** Plugins are organized into marketplaces defined by `marketplace.json` files containing plugin catalogs with name, source, and metadata
- **Multi-source support:** Plugins can be installed from relative paths (same repo), GitHub repositories (`owner/repo`), git URLs (`.git` suffix), npm packages, or pip packages
- **Namespace isolation:** Plugin components are namespaced by plugin name (e.g., `/my-plugin:hello`) to prevent conflicts between multiple installed plugins
- **Scope hierarchy:** Installation scopes (user → project → local → managed) with clear precedence rules, where higher-priority scopes override lower ones
- **Version pinning:** Support for git refs, SHAs, and semantic versioning in marketplace entries
- **Caching system:** Plugins are copied to a cache directory rather than used in-place, with symlink support for external dependencies

**Agent/skill registration:**
- **Auto-discovery:** Components are discovered from conventional directory layouts (`commands/`, `agents/`, `skills/`, `hooks/`, `.mcp.json`, `.lsp.json`)
- **Optional manifest:** `.claude-plugin/plugin.json` is optional; if omitted, plugin name derives from directory name and components auto-discover from default locations
- **Subagent definitions:** Markdown files with YAML frontmatter defining agent metadata (`name`, `description`, `tools`, `model`, `permissionMode`, `hooks`, `skills`, `memory`)
- **Skill structures:** Two formats supported: legacy `commands/` (simple markdown) and modern `skills/` (directories with `SKILL.md` + optional supporting files)
- **Component path overrides:** Manifest can specify custom paths for components, supplementing (not replacing) default directories

**Delegation model:**
- **Automatic delegation:** Claude automatically delegates based on agent `description` field matching task requirements
- **Foreground vs background:** Subagents can run blocking (with permission prompts) or concurrent (pre-approved permissions, auto-deny missing ones)
- **No nesting:** Subagents cannot spawn other subagents (prevents infinite recursion)
- **Context isolation:** Each subagent runs in its own context window with independent conversation history
- **Resume capability:** Subagents can be resumed by agent ID to continue previous work with full context

**Built-in agent types:**
- **Explore:** Fast Haiku-based read-only agent for codebase search (quick/medium/thorough modes)
- **Plan:** Research agent for plan mode, read-only with Sonnet/Opus
- **General-purpose:** Full tool access for complex multi-step tasks
- **Specialized:** Bash, statusline-setup, Claude Code Guide for specific workflows

## 3) Tooling and execution

**MCP server integration:**
- **Three transport types:** stdio (local processes), HTTP (recommended for remote), SSE (deprecated)
- **Configuration locations:** `.mcp.json` at plugin root, inline in `plugin.json`, or user/project-scoped `~/.claude.json`
- **Environment variable expansion:** `${CLAUDE_PLUGIN_ROOT}`, `${VAR}`, `${VAR:-default}` syntax for portable configurations
- **OAuth 2.0 support:** Dynamic client registration or pre-configured credentials with `--client-id`/`--client-secret`
- **Tool Search:** Dynamic tool loading when MCP tool descriptions exceed 10% context (configurable via `ENABLE_TOOL_SEARCH=auto:N`)
- **Resource system:** MCP resources exposed as `@mentions` (e.g., `@github:issue://123`)
- **Prompt-to-command:** MCP prompts become slash commands (`/mcp__servername__promptname`)
- **Plugin bundling:** Plugins can bundle MCP servers that start/stop with plugin lifecycle

**LSP server configuration:**
- **Language support:** Pre-built plugins for 15+ languages (Python, TypeScript, Rust, Go, Java, Kotlin, Swift, Lua, PHP, C/C++, C#)
- **Binary requirement:** Plugin configures connection but users must install language server binary separately
- **`.lsp.json` format:** Maps language IDs to server commands, args, environment, initialization options
- **Transport options:** stdio (default) or socket, with configurable timeouts and restart policies
- **Extension mapping:** `extensionToLanguage` dictionary maps file extensions to LSP language identifiers

**Hook system:**
- **12 event types:** PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, UserPromptSubmit, Notification, Stop, SubagentStart, SubagentStop, SessionStart, SessionEnd, TeammateIdle, TaskCompleted, PreCompact
- **Three hook types:** `command` (shell scripts), `prompt` (LLM evaluation), `agent` (agentic verifier with tools)
- **Matchers:** Regex patterns to filter events (e.g., `"Write|Edit"` for file operations)
- **JSON input via stdin:** Hooks receive event context as JSON with tool name, inputs, outputs, session info
- **Exit code semantics:** 0 = allow, 1 = error, 2 = block operation (Claude sees failure message)
- **Subagent scoping:** Hooks in frontmatter only active while subagent runs; hooks in settings.json respond to SubagentStart/Stop globally

**Code execution layer:**
- **Skill execution:** Skills can include shell scripts in `scripts/` directory alongside `SKILL.md`
- **Background tasks:** Ctrl+B to background running tasks; pre-approve permissions upfront, auto-deny missing ones
- **Tool restrictions:** `tools` field (allowlist) and `disallowedTools` field (denylist) for subagents
- **Permission modes:** `default`, `acceptEdits`, `dontAsk`, `delegate`, `bypassPermissions`, `plan`
- **Max turns:** `maxTurns` field limits agentic loop iterations per subagent invocation
- **Bash validation:** PreToolUse hooks can inspect/block commands before execution (exit code 2 pattern)

## 4) Observability and evaluation

**Plugin debugging:**
- **`claude --debug` flag:** Shows plugin loading details, command/agent/hook registration, MCP server init
- **`/plugin validate` command:** Validates `plugin.json` and `marketplace.json` JSON syntax and schema
- **Error message types:** Manifest validation errors, loading errors, conflicting manifests, path resolution failures
- **Transcript persistence:** Subagent transcripts stored as `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`
- **Compaction logging:** System events in transcripts with `compactMetadata.preTokens` showing pre-compaction token count
- **Auto-compaction:** Triggers at 95% capacity (configurable via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`)

**MCP observability:**
- **`/mcp` command:** Check server status, authenticate OAuth servers, view available tools/resources
- **`claude mcp list/get` CLI:** List all configured servers, get details for specific server
- **Output warnings:** Display warning when MCP tool output exceeds 10,000 tokens (configurable via `MAX_MCP_OUTPUT_TOKENS`)
- **Startup timeout:** `MCP_TIMEOUT` env var controls server startup wait time (default unspecified)
- **Dynamic updates:** `list_changed` notifications allow servers to update tools/prompts/resources without reconnect

**Agent context management:**
- **Resume by ID:** Agent IDs available in main conversation after completion; resume for continued work with full history
- **Context isolation:** Subagent compaction independent of main conversation compaction
- **Session persistence:** Subagent transcripts survive main conversation restarts within same session
- **Cleanup policy:** `cleanupPeriodDays` setting (default 30 days) for automatic transcript removal
- **Foreground output:** Permission prompts and AskUserQuestion passed through to user
- **Background limitations:** Auto-deny unpermitted operations, no MCP tools, no clarifying questions

## 5) Extensibility

**Plugin component types:**
- **Commands/Skills:** Markdown files (legacy) or `SKILL.md` directories with supporting files + progressive disclosure
- **Agents:** Markdown with YAML frontmatter defining specialized subagents
- **Hooks:** Lifecycle event handlers in `hooks/hooks.json` or inline in manifest
- **MCP servers:** Tool integrations via Model Context Protocol
- **LSP servers:** Language intelligence for code navigation/diagnostics
- **Output styles:** Custom output formatting in `outputStyles/` directory

**Marketplace system:**
- **`.claude-plugin/marketplace.json` schema:** Required fields: `name`, `owner` (name, email), `plugins` array
- **Plugin entry fields:** `name`, `source` (required); `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `category`, `tags` (optional)
- **Reserved names:** 7 reserved marketplace names (claude-code-marketplace, claude-code-plugins, etc.) blocked for official use
- **`strict` flag:** When true (default), marketplace entry merges with plugin.json; when false, marketplace fully defines plugin
- **`metadata.pluginRoot`:** Base directory prepended to relative plugin source paths
- **Component path arrays:** Can specify multiple custom paths for commands, agents, skills, hooks

**Distribution patterns:**
- **GitHub (recommended):** Add with `owner/repo`, supports private repos via `GITHUB_TOKEN` env var
- **Git URLs:** Any `.git` URL, supports GitLab/Bitbucket with `GITLAB_TOKEN`/`BITBUCKET_TOKEN`
- **Local paths:** Relative paths for same-repo plugins (only works with git-based marketplaces, not direct URL)
- **npm/pip packages:** Future support indicated in source type enum
- **Private repo auth:** Manual install uses git credential helpers; background auto-update requires env var tokens

**Organizational controls:**
- **Managed MCP:** `managed-mcp.json` in system-wide directories for exclusive control of MCP servers
- **MCP allowlists/denylists:** `allowedMcpServers`/`deniedMcpServers` in managed settings with serverName/serverCommand/serverUrl matching
- **Managed marketplace restrictions:** `strictKnownMarketplaces` in managed settings: undefined = no restrictions, `[]` = complete lockdown, list = exact matching
- **Plugin settings:** `extraKnownMarketplaces` for team-required marketplaces, `enabledPlugins` for default plugin activation
- **`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`:** Disable all background subagent functionality

**Skill preloading:**
- **`skills` field in agent frontmatter:** Array of skill names to inject at subagent startup
- **Full content injection:** Entire skill content injected into context, not just made available for invocation
- **No inheritance:** Subagents don't inherit skills from parent; must be explicitly listed
- **Use case:** Provide domain knowledge without discovery overhead during execution

**Persistent memory:**
- **`memory` field:** `user` (all projects), `project` (shareable), `local` (gitignored)
- **Memory directory:** `~/.claude/agent-memory/<name>/`, `.claude/agent-memory/<name>/`, or `.claude/agent-memory-local/<name>/`
- **Automatic prompting:** System prompt includes Read/Write/Edit instructions and first 200 lines of `MEMORY.md`
- **Cross-session learning:** Subagent builds knowledge base over time (patterns, conventions, architectural decisions)
- **Curation instructions:** Agent prompted to keep `MEMORY.md` under 200 lines

## 6) Notable practices worth adopting in AGENT-33

**1. Optional manifest with auto-discovery:**
- AGENT-33 requires explicit `definition.json` files for all agents. Adopting optional manifests with conventional directory discovery would reduce boilerplate for simple agents and improve developer experience.
- Implementation: Make `agent_definitions_dir` auto-discover JSON files, infer agent name from filename/directory if `name` field missing.

**2. Skill directory structure with supporting files:**
- Claude Code's `skills/<name>/SKILL.md` pattern allows skills to bundle scripts, reference files, and documentation alongside the skill definition.
- AGENT-33 currently treats agent definitions as atomic JSON files. Allowing directory-based definitions with supporting files would enable richer agent capabilities.
- Implementation: Check if `agent_definitions_dir` entry is directory; if so, load `definition.json` + scan for `scripts/`, `docs/`, `tools/` subdirectories.

**3. Plugin caching with symlink support:**
- Claude Code copies plugins to cache directory to prevent path traversal attacks, but honors symlinks for external dependencies.
- AGENT-33 has no plugin/extension system yet. When building one, adopt this security-by-isolation pattern.
- Implementation: `shutil.copytree(plugin_path, cache_path, symlinks=True, ignore_dangerouspatterns)`.

**4. Environment variable expansion in config files:**
- `${VAR}`, `${VAR:-default}` syntax in `.mcp.json` enables team-shared configs with machine-specific values.
- AGENT-33 config loading is direct Pydantic Settings with no templating. Adding expansion would enable shared team configs with per-developer secrets.
- Implementation: `config_loader.py` pre-processes JSON/YAML with `os.path.expandvars()` + custom `${VAR:-default}` parser before Pydantic validation.

**5. Managed settings with allowlist/denylist patterns:**
- Claude Code's `strictKnownMarketplaces`, `allowedMcpServers`, `deniedMcpServers` provide org-level controls without breaking user customization.
- AGENT-33's governance layer exists in code but isn't enforced at runtime. Adopting this pattern for tools, agents, and workflows would provide actual governance.
- Implementation: Add `managed-settings.json` loader in `config.py`, check allowlists/denylists in `tool_registry.py`, `agent_registry.py`, `workflow_engine.py` before invocation.

**6. Skill preloading into agent context:**
- Claude Code's `skills` field in agent frontmatter injects full skill content at startup for domain knowledge without discovery overhead.
- AGENT-33's workflows have actions but no skill injection. Adding this to agent definitions would enable knowledge-heavy agents.
- Implementation: Add `preloaded_skills: List[str]` to `AgentDefinition`, resolve from skill registry at agent spawn, inject into `_build_system_prompt()`.

**7. Persistent agent memory:**
- `memory: user|project|local` gives agents a persistent directory to build knowledge over time.
- AGENT-33 has session state and observation capture but no cross-session agent memory. This would enable self-improving agents.
- Implementation: Add `memory_scope` to `AgentDefinition`, create memory dir in `agent_runtime.py`, inject memory instructions + first N lines of `MEMORY.md` into system prompt.

**8. Hook exit code 2 for blocking:**
- Exit code 0 = allow, 1 = error, 2 = block operation (Claude sees failure message from stderr).
- AGENT-33's hooks are planned (Phase 18) but no spec exists. Adopting this three-code pattern provides clear control flow.
- Implementation: `subprocess.run(hook_script, capture_output=True)`, check `returncode`, raise `ToolBlockedError` on 2 with stderr message.

**9. Background task pre-approval pattern:**
- Claude Code backgrounds tasks by pre-prompting for all needed permissions, then auto-denying missing ones during execution.
- AGENT-33 has no background execution. When adding it, this upfront-approval pattern prevents permission deadlocks.
- Implementation: Before backgrounding, walk workflow DAG to collect all required tool permissions, prompt once, then spawn with `auto_deny_unpermitted=True`.

**10. MCP Tool Search for scale:**
- When MCP tool descriptions exceed 10% of context, dynamically load tools on-demand instead of preloading all.
- AGENT-33 preloads all tools into every prompt. As tool count grows, this becomes unsustainable. Tool Search is a proven scaling pattern.
- Implementation: Add `enable_tool_search: bool|str` to config, move tool defs to separate registry, inject search tool when threshold hit, load tools on-demand when requested.

## 7) Risks / limitations to account for

**1. Plugin trust model relies on user judgment:**
- Warning: "Anthropic does not control what MCP servers, files, or other software are included in plugins and cannot verify that they will work as intended."
- Risk for AGENT-33: If we build a plugin system, we inherit the same trust problem. External code running in the engine context is high-risk.
- Mitigation: Sandbox plugins in separate processes, use capability-based security, require code signing for org-approved plugins.

**2. Relative path plugins fail with URL-based marketplaces:**
- Plugins with `"source": "./plugins/my-plugin"` only work when marketplace is git-cloned, not when fetched as raw `marketplace.json` URL.
- Risk for AGENT-33: If we support both git and HTTP distribution, path resolution becomes inconsistent.
- Mitigation: Document clearly, validate source types at marketplace parse time, fail fast with actionable error.

**3. No plugin versioning enforcement:**
- Marketplace entries can specify version but there's no automatic update checking or conflict resolution when multiple marketplaces provide same plugin.
- Risk for AGENT-33: Plugin version sprawl, dependency hell, no reproducible builds.
- Mitigation: Implement lockfile pattern (like `package-lock.json`), version conflict resolution in registry, deprecation warnings.

**4. Subagent context isolation prevents collaboration:**
- Subagents cannot spawn other subagents, cannot share context mid-execution, must return full results to parent.
- Risk for AGENT-33: Our multi-agent workflows assume agents can collaborate. Claude's model is strictly hierarchical.
- Mitigation: Use agent teams (separate sessions with message passing) for collaboration, use subagents only for isolated delegation.

**5. Hook scripts are shell-based, not portable:**
- All hook examples use bash scripts. No Windows support without WSL.
- Risk for AGENT-33: We already have Windows subprocess issues. Adding bash-only hooks makes it worse.
- Mitigation: Support `"type": "python"` hooks with Python script paths, use `subprocess.list2cmdline()` for proper quoting, document platform requirements.

**6. MCP OAuth requires user interaction:**
- OAuth flow opens browser and blocks until user completes login. Cannot automate in CI/CD.
- Risk for AGENT-33: Headless execution (Phase 16) breaks if tools require OAuth.
- Mitigation: Separate credential provisioning from tool execution, support service account auth, fail fast in non-interactive mode.

**7. Plugin caching breaks relative imports:**
- Plugins copied to cache directory can't reference `../shared-utils` because parent dir not copied.
- Risk for AGENT-33: If we copy plugins instead of running in-place, we inherit this limitation.
- Mitigation: Follow symlink pattern, document clearly, or skip caching for trusted internal plugins.

**8. No plugin dependency resolution:**
- Plugins cannot declare dependencies on other plugins. If plugin A requires plugin B, user must know to install both.
- Risk for AGENT-33: Complex plugin ecosystems become brittle.
- Mitigation: Add `dependencies: [...]` to plugin manifest, auto-install missing deps with user confirmation.

**9. Managed settings are inflexible:**
- `strictKnownMarketplaces=[]` means complete lockdown; no way to allowlist patterns (e.g., "all internal git servers").
- Actually: `hostPattern` source type with regex matching exists for this case.
- Not a risk: Pattern matching already supported via `hostPattern` source type.

**10. Background tasks lose MCP tools:**
- "MCP tools are not available in background subagents."
- Risk for AGENT-33: If we background workflow steps that need external tools, they'll fail silently.
- Mitigation: Check workflow DAG for MCP tool usage before backgrounding, warn user, require foreground execution for MCP-dependent steps.

## 8) Feature extraction (for master matrix)

**Plugin architecture:**
- Optional manifests with auto-discovery from conventional layouts
- Multi-source plugin installation (git, npm, pip, local paths)
- Namespace isolation with plugin-name prefixing
- Scoped installations (user/project/local/managed) with precedence
- Plugin caching with symlink support for external dependencies
- Environment variable expansion in config files (`${VAR:-default}`)
- Managed settings for organizational controls (allowlists/denylists)

**Agent system:**
- Subagent definitions as Markdown + YAML frontmatter
- Automatic delegation based on description matching
- Foreground (blocking) vs background (concurrent) execution modes
- Context isolation with independent conversation history
- Resume capability by agent ID with full context preservation
- Built-in agent types (Explore, Plan, general-purpose) with role specialization
- No nesting (subagents cannot spawn subagents)

**Skill/tool framework:**
- Skill directories with `SKILL.md` + supporting files (scripts, docs, reference materials)
- Tool restrictions via `tools` (allowlist) and `disallowedTools` (denylist)
- Permission modes (default, acceptEdits, dontAsk, delegate, bypassPermissions, plan)
- Skill preloading into agent context for domain knowledge
- Progressive disclosure (implied by directory-based skill structure)
- Background task pre-approval pattern (upfront permission prompting)

**MCP integration:**
- Three transport types (stdio, HTTP, SSE) with OAuth 2.0 support
- Plugin-bundled MCP servers with automatic lifecycle management
- MCP Tool Search for dynamic tool loading when context threshold exceeded
- Resource system with `@mention` syntax for references
- Prompt-to-command conversion for MCP server prompts
- Output limit warnings with configurable thresholds
- Dynamic tool updates via `list_changed` notifications

**LSP support:**
- Pre-built LSP plugins for 15+ languages
- `.lsp.json` configuration with extension-to-language mapping
- Transport options (stdio, socket) with timeouts and restart policies
- User-installed language server binaries (plugin configures, doesn't bundle)

**Hook system:**
- 12 event types covering tool use, permissions, sessions, subagents, compaction
- Three hook types (command, prompt, agent) with different execution models
- JSON input via stdin with tool context (name, inputs, outputs)
- Exit code semantics (0=allow, 1=error, 2=block)
- Subagent-scoped hooks vs global session hooks
- Matchers for event filtering (regex patterns on tool names, agent types)

**Agent memory:**
- Persistent memory directories with three scopes (user, project, local)
- Automatic `MEMORY.md` injection (first 200 lines) into system prompt
- Curation instructions to keep memory concise
- Cross-session learning for pattern accumulation
- Automatic tool enablement (Read, Write, Edit) when memory configured

**Observability:**
- Plugin validation CLI (`claude plugin validate`)
- Debug mode showing plugin loading, component registration, MCP init
- Subagent transcript persistence with compaction events logged
- Auto-compaction at 95% capacity (configurable threshold)
- MCP server status checks and authentication management
- Error message categorization (validation, loading, conflicts, paths)

**Distribution/marketplace:**
- `marketplace.json` schema with plugin catalog
- Version pinning via git refs/SHAs and semantic versioning
- Private repository support via environment variable tokens
- Team-required marketplaces with auto-prompt on project trust
- Reserved marketplace names to prevent impersonation
- `strict` flag for manifest merge vs full definition in marketplace

**Security/governance:**
- Managed MCP configuration for exclusive server control
- MCP allowlists/denylists with serverName/serverCommand/serverUrl matching
- Managed marketplace restrictions (undefined/empty array/allowlist)
- Plugin approval before using project-scoped configs
- Tool-specific permission rules (deny via `Task(subagent-name)`)
- Background task permission pre-approval to prevent deadlocks

## 9) Evidence links

**Repository:**
- GitHub: https://github.com/anthropics/claude-plugins-official (7.4k stars, 711 forks)
- Official documentation: https://code.claude.com/docs/en/plugins

**Documentation pages:**
- Plugin creation guide: https://code.claude.com/docs/en/plugins
- Plugin reference: https://code.claude.com/docs/en/plugins-reference
- Plugin marketplace guide: https://code.claude.com/docs/en/plugin-marketplaces
- MCP integration: https://code.claude.com/docs/en/mcp
- Subagent configuration: https://code.claude.com/docs/en/sub-agents
- Skill development: https://code.claude.com/docs/en/skills
- Hook system: https://code.claude.com/docs/en/hooks

**Key concepts:**
- Model Context Protocol: https://modelcontextprotocol.io/introduction
- Language Server Protocol: https://microsoft.github.io/language-server-protocol/
- Semantic versioning: https://semver.org/

**Plugin examples in repository:**
- 28 internal Anthropic plugins in `/plugins` (LSP plugins, dev tools, code review)
- 13 external partner plugins in `/external_plugins` (Asana, GitHub, GitLab, Linear, Slack, Stripe, Supabase, Playwright, Firebase, etc.)
- Example plugin structure: `/plugins/example-plugin`

**MCP server registry:**
- API endpoint: https://api.anthropic.com/mcp-registry/v0/servers
- Registry documentation: https://api.anthropic.com/mcp-registry/docs

**Additional resources:**
- Plugin submission form: https://clau.de/plugin-directory-submission
- MCP server examples: https://github.com/modelcontextprotocol/servers
- MCP SDK quickstart: https://modelcontextprotocol.io/quickstart/server
