# Repo Dossier: anthropics/claude-code
**Snapshot date:** 2026-02-14

## 1) One-paragraph summary
Claude Code is Anthropic's official agentic coding tool designed as a production-grade CLI/IDE framework that executes routine tasks, explains code, and handles git workflows through natural language. The architecture implements a **deny-first permission system with three tiers** (read-only tools require no approval, file modifications auto-approve until session end, bash commands permanently approve per project+command), comprehensive MCP integration for external tool connectivity, a hooks system for lifecycle automation, and a skills/subagents framework for reusable workflows. The codebase (66.8k stars, Shell/Python/TypeScript) prioritizes security through sandboxing, prompt injection defenses, and managed enterprise policies while supporting multi-surface deployment (terminal, VS Code, JetBrains, desktop app, web, mobile).

## 2) Core orchestration model
Claude Code uses a **single-agent-with-delegation** model rather than multi-agent orchestration. The main Claude agent runs in a primary context window and delegates specialized tasks to **subagents**—isolated AI assistants with independent contexts, custom system prompts, and restricted tool access. Subagents execute in foreground (blocking) or background (concurrent) modes, return summarized results to the main agent, and cannot spawn other subagents (preventing infinite nesting). Agent teams exist for parallel work across separate sessions but require explicit team definition. The orchestration layer provides:

- **Built-in subagents**: `Explore` (Haiku, read-only), `Plan` (planning research), `general-purpose` (full tools), `Bash` (terminal), plus utility agents
- **Delegation triggers**: Automatic (Claude decides based on subagent description) or explicit user requests
- **Context isolation**: Each subagent runs with fresh context, no shared memory except explicit resume
- **Forked skills**: Skills can run in subagent contexts via `context: fork` frontmatter
- **Permission inheritance**: Subagents inherit parent permissions but can override via `permissionMode`
- **Session persistence**: Subagent transcripts stored separately (`~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`), survive main conversation compaction
- **Auto-compaction**: Subagents compact at 95% capacity (configurable via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`)

Unlike AGENT-33's `OrchestrationPolicy` with explicit team composition and task routing, Claude Code keeps orchestration implicit—Claude decides when to delegate based on task descriptions.

## 3) Tooling and execution
The tool governance system implements **three permission tiers** with deny-first defaults:

### Permission Architecture
**Tier 1 - Read-only tools** (no approval): `Read`, `Grep`, `Glob`
**Tier 2 - File modifications** (session-scoped approval): `Edit`, `Write` auto-approve until session end
**Tier 3 - Bash commands** (permanent project-level approval): "Yes, don't ask again" persists per `(project_dir, command)` tuple

Permission rules follow **deny → ask → allow** precedence with pattern matching:
```json
{
  "permissions": {
    "deny": ["Bash(git push *)"],
    "ask": ["Bash(npm run test)"],
    "allow": ["Bash(npm run build)", "Read(*.env)"]
  }
}
```

### Permission Modes
- `default`: Standard prompts on first use
- `acceptEdits`: Auto-approve file edits for session
- `plan`: Read-only exploration mode
- `delegate`: Team-lead coordination mode (restricts to team management tools)
- `dontAsk`: Auto-deny unless pre-approved
- `bypassPermissions`: Skip all checks (requires isolated environment)

### Tool-Specific Patterns
**Bash**: Supports glob wildcards (`Bash(npm run *)`, `Bash(git * main)`), enforces word boundaries (`Bash(ls *)` matches `ls -la` but not `lsof`). Command injection detection blocks suspicious patterns even if allowlisted.

**Read/Edit**: Follow gitignore spec with four pattern types:
- `//path` → absolute from filesystem root
- `~/path` → from home directory
- `/path` → relative to settings file
- `path` → relative to current directory

**WebFetch**: Domain-based rules (`WebFetch(domain:example.com)`)

**MCP tools**: Named `mcp__<server>__<tool>`, matched via regex (`mcp__memory__.*` matches all Memory server tools)

**Task (subagents)**: `Task(AgentName)` controls which subagents Claude can spawn

### Sandboxing
Provides OS-level enforcement via `/sandbox` command:
- Filesystem isolation (chroot-like boundaries)
- Network restrictions (allowedDomains list)
- Works alongside permissions for defense-in-depth
- Only applies to Bash commands and child processes

### MCP Integration
Claude Code acts as both MCP client (consumes servers) and MCP server (exposes tools to other apps). Three transport types:

**HTTP servers** (recommended):
```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
```

**SSE servers** (deprecated):
```bash
claude mcp add --transport sse asana https://mcp.asana.com/sse
```

**Stdio servers** (local):
```bash
claude mcp add --transport stdio --env AIRTABLE_API_KEY=KEY airtable \
  -- npx -y airtable-mcp-server
```

**Scopes**: `local` (project-specific, stored in `~/.claude.json`), `project` (shared via `.mcp.json`), `user` (cross-project, in `~/.claude.json`)

**OAuth support**: Built-in dynamic registration or pre-configured credentials with `--client-id`/`--client-secret`

**MCP Tool Search**: Auto-activates when tool definitions exceed 10% of context window, dynamically loads tools on-demand instead of preloading

**Managed MCP**: Organizations deploy `managed-mcp.json` for exclusive server control or use allowlists/denylists in managed settings

## 4) Observability and evaluation
Claude Code provides lightweight observability through:

### Logging
- **Debug mode**: `claude --debug` shows hook execution, tool calls, permission checks
- **Verbose mode**: `Ctrl+O` toggles verbose output in transcript
- **Transcript files**: JSONL format stored at `~/.claude/projects/{project}/{sessionId}.jsonl`
- **Subagent transcripts**: Separate files in `subagents/agent-{agentId}.jsonl`

### Monitoring
- **OpenTelemetry metrics**: Export usage data via `/monitoring-usage` endpoint
- **MCP output warnings**: Alerts when tool output exceeds 10,000 tokens (configurable via `MAX_MCP_OUTPUT_TOKENS`)
- **Context tracking**: `/context` command shows skill budget utilization

### Testing
No built-in evaluation gates, but hooks enable custom checks:
- `PreToolUse` hooks can validate operations before execution
- `PostToolUse` hooks can verify results after completion
- `TaskCompleted` hooks can enforce completion criteria (e.g., tests pass)
- `Stop` hooks can prevent Claude from finishing until conditions met

### Replay & Lineage
- Transcript persistence (default 30 days via `cleanupPeriodDays`)
- Session resume via `--resume` flag
- Subagent transcripts survive main conversation compaction

Notable gap: No built-in rollout capture, A/B testing, or automated evaluation—evaluation is implicit through user interaction and explicit through custom hooks.

## 5) Extensibility
Claude Code provides **four extension mechanisms**:

### 1. Skills (slash commands)
Markdown files with YAML frontmatter that extend Claude's capabilities:

```yaml
---
name: explain-code
description: Explains code with diagrams and analogies
allowed-tools: Read, Grep
model: sonnet
context: fork  # Runs in subagent
---
When explaining code, include:
1. Analogy from everyday life
2. ASCII diagram
3. Step-by-step walkthrough
```

**Location scopes**: Enterprise (managed settings) > Personal (`~/.claude/skills/`) > Project (`.claude/skills/`) > Plugin

**Invocation control**:
- `disable-model-invocation: true` → only user can invoke
- `user-invocable: false` → only Claude can invoke

**Dynamic context injection**: `!`command`` syntax executes shell commands and injects output into skill content before Claude sees it

**Supporting files**: Skills can include `template.md`, `examples.md`, `scripts/` referenced from main `SKILL.md`

**String substitutions**: `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, `${CLAUDE_SESSION_ID}`

### 2. Hooks (lifecycle automation)
Shell commands, LLM prompts, or agents that execute at specific points:

**Event types**:
- Session: `SessionStart`, `SessionEnd`
- User interaction: `UserPromptSubmit`, `Notification`
- Tool execution: `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`
- Agent lifecycle: `SubagentStart`, `SubagentStop`, `Stop`, `TeammateIdle`
- Context: `PreCompact`, `TaskCompleted`

**Hook types**:
- **Command hooks**: Execute shell scripts, receive JSON via stdin, control behavior via exit codes
- **Prompt hooks**: Single-turn LLM evaluation returning `{ "ok": true/false, "reason": "..." }`
- **Agent hooks**: Multi-turn subagent with tool access, up to 50 turns

**Decision control patterns**:
- Exit code 0 = success, exit 2 = blocking error (behavior varies by event)
- JSON output for fine-grained control (`permissionDecision`, `updatedInput`, `additionalContext`)
- `PreToolUse` uses `hookSpecificOutput` with `permissionDecision: allow/deny/ask`
- `PermissionRequest` uses `decision.behavior: allow/deny` plus `updatedInput`/`updatedPermissions`

**Async execution**: `"async": true` runs hooks in background, delivers output on next conversation turn

**Locations**: User settings (`~/.claude/settings.json`), project settings (`.claude/settings.json`), managed policies, plugin `hooks/hooks.json`, skill/agent frontmatter

### 3. Subagents (custom agents)
Independent AI assistants with isolated contexts:

```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
model: sonnet
permissionMode: plan
maxTurns: 50
skills: [api-conventions, error-handling]
memory: user  # Persistent knowledge directory
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
---
System prompt for the subagent...
```

**Scopes**: CLI flag (session-only) > Project (`.claude/agents/`) > User (`~/.claude/agents/`) > Plugin

**Persistent memory**: `memory: user/project/local` gives subagent directory that survives across sessions, auto-includes Read/Write/Edit tools

### 4. Plugins (distribution packages)
Bundle skills, subagents, MCP servers, hooks, and commands:

```
my-plugin/
├── plugin.json           # Metadata
├── skills/
│   └── review/SKILL.md
├── agents/
│   └── reviewer.md
├── hooks/hooks.json
├── .mcp.json             # MCP servers
└── commands/             # Legacy commands
```

Plugin namespace: `plugin-name:skill-name` prevents conflicts

## 6) Notable practices worth adopting in AGENT-33

### 1. Three-tier permission system with deny-first defaults
AGENT-33 currently uses scope-based auth (`["admin"]`, `["developer"]`) but lacks per-tool permission tiers. Adopting:
- **Read-only tier** (no prompts): `FileOpsTool`, `SearchTool`, `ListDirectoryTool`
- **Modify tier** (session-scoped): `ExecuteCodeTool`, `WriteTool`
- **Execute tier** (persistent per project+command): `ShellTool`, `BrowserTool`

**Implementation path**:
1. Add `PermissionTier` enum to `models/security.py`: `READ_ONLY`, `MODIFY`, `EXECUTE`
2. Tag each tool in `tools/registry.py` with tier
3. Extend `AuthMiddleware` to track session-scoped and persistent approvals
4. Store project-level approvals in `~/.agent33/project_approvals.json` keyed by `(tenant_id, project_path, tool_name, args_hash)`

### 2. Hooks with decision control
AGENT-33's `WorkflowAction` model is synchronous—hooks would add **event-driven control points** without blocking the main execution loop. Critical for governance:

**PreToolUse hook** replaces prompt-level governance injection:
```python
# Current: GovernanceConstraints exists but never reaches LLM
# Proposed: PreToolUse hook validates before execution
@dataclass
class PreToolUseHook:
    tool_name: str
    tool_input: dict
    permission_decision: Literal["allow", "deny", "ask"]
    permission_reason: str
    updated_input: dict | None = None
```

**Implementation**: Add `hooks/` module mirroring Claude Code's event types, integrate with `execution/executor.py` pipeline.

### 3. MCP Tool Search pattern
AGENT-33 preloads all tool definitions into context. When tool count exceeds ~20, this consumes 10%+ of context. Adopt:
- `ToolSearchTool` that queries `tools/registry.py` on-demand
- Defer non-critical tool loading until LLM requests
- Threshold: when tool definitions exceed 8,000 tokens (configurable)

### 4. Persistent agent memory
AGENT-33's `memory/` subsystem provides short-term buffer and pgvector long-term store but lacks **agent-scoped persistent directories**. Adopt:
```python
# agents/definition.py
class AgentDefinition:
    memory_scope: Literal["user", "project", "session"] | None = None
    # Enables ~/.agent33/agent-memory/{agent_id}/ for cross-session learning
```

Benefits:
- Agents accumulate codebase patterns across sessions
- No database dependency (filesystem-based)
- User/project scopes align with existing multi-tenancy

### 5. Skill dynamic context injection
Claude Code's `!`command`` pattern executes shell commands **before** LLM sees the prompt. Enables:
```markdown
## PR context
- Diff: !`gh pr diff`
- Comments: !`gh pr view --comments`
```

AGENT-33 could add preprocessing phase to `agents/runtime.py`:
```python
def _preprocess_prompt(prompt: str) -> str:
    # Find !`...` patterns, execute, replace with output
    return re.sub(r'!`([^`]+)`', lambda m: subprocess.check_output(m[1], shell=True).decode(), prompt)
```

### 6. Managed settings for enterprise
AGENT-33's `config.py` loads from `.env` only. Add **system-wide managed settings** at `/etc/agent33/managed-settings.json` (Linux) / `C:\Program Files\AGENT33\managed-settings.json` (Windows) with:
- `allowManagedPermissionRulesOnly: true` → users can't override permission rules
- `allowManagedHooksOnly: true` → blocks user/project hooks
- `strictKnownMarketplaces` → controls plugin sources

Priority: Managed > CLI args > Project > User

### 7. Sandbox integration for code execution
AGENT-33's `CLIAdapter` in `execution/adapters/` runs subprocess without isolation. Add optional sandboxing:
```python
class SandboxConfig:
    filesystem_root: Path  # chroot-like boundary
    allowed_domains: list[str]  # network whitelist
    timeout_ms: int

class CLIAdapter(BaseAdapter):
    def execute(self, contract: ExecutionContract, config: SandboxConfig | None) -> ExecutionResult:
        # Use firejail/bwrap on Linux, sandbox-exec on macOS
```

Benefit: Defense-in-depth against prompt injection that bypasses permission checks.

## 7) Risks / limitations to account for

### 1. Governance-prompt disconnect (same issue as AGENT-33)
Claude Code's permission system exists in code but **governance constraints are never injected into agent prompts**. The `description` field in subagent frontmatter is the only governance signal Claude sees. This mirrors AGENT-33's exact problem:
- `GovernanceConstraints` defined in `agents/definition.py` but unused
- `PermissionRequest` hooks happen **after** Claude decides to use a tool
- No safety instructions in system prompts

**Risk**: LLM decides to use dangerous tools before permission checks fire.

### 2. Tool permission patterns are fragile
Claude Code documentation explicitly warns:
> "Bash permission patterns that try to constrain command arguments are fragile. For example, `Bash(curl http://github.com/ *)` won't match `curl -X GET http://github.com/...`"

AGENT-33 should avoid argument-based allowlisting. Use **deny rules + PreToolUse hooks** instead.

### 3. Implicit orchestration limits observability
Claude decides when to delegate to subagents based on natural language descriptions. No explicit routing DAG, no visibility into delegation logic. AGENT-33's `WorkflowDefinition` with explicit steps is **more auditable** than Claude Code's implicit delegation.

**Mitigation**: AGENT-33 should keep explicit workflows but add optional "smart routing" where orchestrator decides which agent to invoke based on task description.

### 4. No built-in evaluation gates
Claude Code relies on user approval and custom hooks for validation. No built-in:
- Rollout capture (logs exist but not structured for replay)
- A/B testing (no variant tracking)
- Automated evaluation (no `assert` on tool outputs)

AGENT-33's Phase 17 (Evaluation Gates) should remain—this is a differentiator.

### 5. MCP security burden shifts to users
> "Anthropic does not manage or audit any MCP servers. You are able to configure Claude Code permissions for MCP servers."

AGENT-33's tool governance must account for **untrusted MCP tools**. User-installed MCP servers are effectively arbitrary code execution.

**Mitigation**: Require explicit `mcp__` prefix in allowlists, default-deny all MCP tools.

### 6. Session-based permissions don't survive restarts
Claude Code's "Yes, don't ask again" for Bash commands persists **per project** but file edit approvals reset on session end. AGENT-33's `SecurityPolicy` should decide: do we want persistent file edit approvals?

**Trade-off**: Convenience vs. defense against stale approvals.

### 7. Skill discovery scales poorly
Skill descriptions loaded into context at 2% of context window (16,000 char fallback). With 50+ skills, budget exceeded. AGENT-33's capability taxonomy (25 entries in `agents/capabilities.py`) is smaller but will hit same limit.

**Mitigation**: Implement skill search tool (like MCP Tool Search) instead of preloading all descriptions.

## 8) Feature extraction (for master matrix)

| Feature | AGENT-33 | Claude Code | Notes |
|---------|----------|-------------|-------|
| **Permission system** | Scope-based (tenant+role) | Three-tier deny-first | CC more granular per-tool |
| **Permission persistence** | Session-only | Project-level for Bash, session for edits | CC hybrid approach |
| **Permission rules** | None | Deny/ask/allow with pattern matching | CC allows `Bash(npm *)` wildcards |
| **Sandbox isolation** | None | Filesystem + network boundaries | CC uses firejail/bwrap |
| **Prompt injection defenses** | Basic (security prompt) | Multi-layer (blocklist, context isolation, fail-closed) | CC more mature |
| **Hooks system** | None | 14 event types, 3 hook types | CC event-driven automation |
| **Hook decision control** | N/A | Exit codes + JSON with updatedInput | CC allows modifying tool params |
| **MCP integration** | None planned | Client + server, 3 transports | CC production-ready |
| **MCP Tool Search** | N/A | Auto-activates at 10% context | CC defers tool loading |
| **Managed policies** | None | System-wide managed-settings.json | CC enterprise feature |
| **Skills/commands** | None | Skills with frontmatter | CC reusable workflows |
| **Skill dynamic context** | N/A | !\`command\` preprocessing | CC shell injection before LLM |
| **Subagents** | Via workflows | Built-in with isolated contexts | CC auto-delegation |
| **Agent memory** | Short-term buffer + pgvector | Persistent directories per agent | CC filesystem-based |
| **Observability** | structlog + tracing | Debug mode + transcripts | AGENT-33 more instrumented |
| **Evaluation gates** | Planned (Phase 17) | Custom hooks only | AGENT-33 will have built-in |
| **Rollout capture** | training/ subsystem | None | AGENT-33 advantage |
| **Multi-tenancy** | DB-backed (tenant_id) | OS users + managed policies | AGENT-33 more scalable |
| **Orchestration model** | DAG-based workflows | Implicit delegation | AGENT-33 more explicit |
| **Tool governance** | Capability taxonomy | Permission rules + hooks | Different paradigms |
| **Auto-compaction** | Alembic migrations | Context window at 95% | Different concerns |

**Key takeaways**:
1. **Permission architecture**: Claude Code's three-tier system is more mature than AGENT-33's scope-based auth
2. **Hooks are critical**: Event-driven control points solve governance-prompt disconnect
3. **MCP Tool Search**: Mandatory for scaling beyond ~20 tools
4. **AGENT-33 advantages**: Explicit workflows, built-in evaluation, multi-tenancy, training loop
5. **Claude Code advantages**: Permission system, hooks, MCP integration, sandbox isolation

## 9) Evidence links

### Documentation (primary sources)
- Overview: https://code.claude.com/docs/en/overview
- Security: https://code.claude.com/docs/en/security
- Permissions: https://code.claude.com/docs/en/permissions
- Hooks reference: https://code.claude.com/docs/en/hooks
- Skills: https://code.claude.com/docs/en/skills
- Subagents: https://code.claude.com/docs/en/sub-agents
- MCP integration: https://code.claude.com/docs/en/mcp
- Settings: https://code.claude.com/docs/en/settings

### Repository
- GitHub: https://github.com/anthropics/claude-code
- 66.8k stars, 5.2k forks, 507 commits, 50 contributors
- Languages: Shell (45.1%), Python (30.6%), TypeScript (18.0%)
- Examples: https://github.com/anthropics/claude-code/tree/main/examples/settings

### Key patterns
- Bash command validator reference: https://github.com/anthropics/claude-code/blob/main/examples/hooks/bash_command_validator_example.py
- Permission configuration examples: https://github.com/anthropics/claude-code/tree/main/examples/settings

### Standards
- Agent Skills specification: https://agentskills.io
- Model Context Protocol: https://modelcontextprotocol.io/introduction
- MCP SDK quickstart: https://modelcontextprotocol.io/quickstart/server

### Community
- Discord: https://anthropic.com/discord
- Bug reports: `/bug` command or GitHub issues
- Trust Center: https://trust.anthropic.com (SOC 2 Type 2, ISO 27001)
