# Repo Dossier: anomalyco/opencode
**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

OpenCode is a terminal-first, open-source AI coding agent built on TypeScript/Bun with a client-server architecture, monorepo structure (16 packages via Turbo), and multi-provider LLM support (75+ via Models.dev including Claude, GPT, Gemini, and local models). It distinguishes itself through a **granular wildcard-based permission system** that controls tool execution at the file-path and command-pattern level (allow/ask/deny states), **mode-based agent profiles** (Build=full-access, Plan=read-only-plus-prompts, Explore=read-only subagent), **native LSP integration** for semantic code understanding, **MCP server support** for extensibility, and a **plugin framework** (`@opencode-ai/plugin`) for custom tool development with Zod-validated schemas. The system explicitly avoids sandboxing—permissions are UX guardrails, not security boundaries—and has achieved 10M+ downloads (7.8M GitHub, 2.4M npm) with 104K+ stars since June 2025.

## 2) Core orchestration model

**Agent types**: OpenCode defines two categories: **primary agents** (user-facing, tab-switchable) and **subagents** (invoked via @ mentions or automatically by primary agents for specialized tasks). Built-in agents include Build (default, full tools), Plan (restricted: edit/bash set to "ask"), General (subagent, full access), and Explore (subagent, read-only). Three hidden agents handle system tasks: Compaction, Title, and Summary.

**Execution flow**: Agents operate through conversational interaction with slash commands (`/init`, `/undo`, `/share`), fuzzy file references (`@filename`), and image drag-and-drop. The system uses **Hono web framework** for HTTP routing and **Drizzle ORM (beta)** for persistence. No sandbox environment exists—agents run with host system privileges gated only by the permission system. Multi-session parallelism is supported, allowing concurrent agent instances on the same project.

**Configuration**: Agents are defined via **markdown files** in `~/.config/opencode/agents/` (global) or `.opencode/agents/` (project-local), or via JSON in `opencode.jsonc`. The markdown filename becomes the agent name. Configuration includes: mode (primary|subagent|all), model override, tools (true/false per tool), permissions (allow/ask/deny per action), temperature, and system prompt file reference. See `.opencode/agent/translator.md` for a 15KB production example.

**No DAG workflows**: Unlike AGENT-33's workflow engine, OpenCode uses **direct LLM-driven agent invocation** with no explicit DAG or state machine. Agents decide next actions through LLM reasoning and tool calls, similar to OpenAI Swarm's client-side handoff pattern but with richer permission controls.

## 3) Tooling and execution

**Built-in tools** (16 permissions mapped to tools):
- **File ops**: read, edit (includes write/patch/multiedit), glob, grep, list
- **Execution**: bash (shell commands), task (subagent launching), skill, lsp (language server queries)
- **State**: todoread, todowrite (task tracking)
- **External**: webfetch, websearch, codesearch, external_directory (outside working dir)
- **Safety**: doom_loop (blocks after 3 identical tool calls)

**LSP integration**: The system **auto-loads language servers** for the project's languages and exposes LSP queries as a tool (`lsp` permission). Agents can request diagnostics, go-to-definition, hover info, etc. Issues reveal challenges: 3-second diagnostic timeout too short for heavy servers (JDTLS, ESLint), memory leaks (111GB virt/21GB RSS causing OOM kills on Linux), and ephemeral JDTLS data directories forcing index rebuilds.

**Custom tool framework**: The `@opencode-ai/plugin` package provides tool development infrastructure. Tools export a default object with:
```typescript
{
  description: string,  // loaded from .txt file
  arguments: zodSchema, // Zod validation (e.g., enum assignees, label arrays)
  execute: async (args) => string  // validated args in, human-readable string out
}
```
Business logic validation occurs before API calls. Example: `github-triage.ts` enforces "adamdotdevin requires desktop label" before calling GitHub API. Tools integrate via dependency injection of validated args—no direct registry access needed.

**MCP server support**: Configuration includes `"mcp": {}` section in `opencode.jsonc`. MCP servers extend tool capabilities beyond built-ins, though exact integration mechanics are underdocumented.

**Tree-sitter parsing**: Dependencies include tree-sitter for code parsing, likely feeding LSP integration and code understanding. The `parsers-config.ts` (10.7KB) suggests complex language-specific parser configuration.

**No code-as-data execution layer**: Unlike AGENT-33's Phase 13 CodeExecutor with sandbox adapters and progressive disclosure, OpenCode directly invokes bash via subprocess with permission checks. No IV-01..05 validation, no ExecutionContract model, no L0-L3 disclosure levels.

## 4) Observability and evaluation

**Telemetry status**: OpenCode has experimental OpenTelemetry support (`experimental.openTelemetry` config flag) but **OTLP traces not emitting** as of Feb 13, 2026 (issue #13438). OTEL integration was marked complete (#13171) but is non-functional in practice. Download stats tracked meticulously in `STATS.md` (7.8M GitHub, 2.4M npm cumulative).

**No built-in evaluation**: No evidence of automated agent performance evaluation, rollout capture, A/B testing, or self-improvement loops. Unlike AGENT-33's `training/` module with rollout evaluation and optimization scheduling, OpenCode relies on manual user feedback and issue tracking (5,160 open issues).

**Observability gaps confirmed by issues**:
- Token usage not visible in UI (multiple requests)
- Session/parent-session ID tracking missing from API requests
- Diagnostic logging insufficient for debugging agent decisions
- No regression detection infrastructure
- Quality monitoring system features (#13207, #13206, #13204, #13205) marked "not planned"

**Performance monitoring**: Severe production issues reveal monitoring gaps: memory leak causing kernel soft lockups (356s on 7/8 CPUs), OOM kills at 111GB virt/21GB RSS, total system death on Linux (#13230). No auto-scaling, no resource limits, no circuit breakers.

**Session replay**: `/share` command creates shareable session links "for reference or to debug," suggesting session persistence and replay capability, but details undocumented.

## 5) Extensibility

**Multi-provider LLM support**: Integrates 15+ AI provider SDKs via Vercel AI SDK (Anthropic, OpenAI, Google, Azure, AWS Bedrock, Groq, Together, Fireworks, Cohere, Mistral, Perplexity, Replicate). Configuration via `opencode.jsonc` `"provider"` key. Premium "Zen" offering provides curated model access.

**Plugin system**: `@opencode-ai/plugin` package with dual exports (`./src/index.ts` and `./src/tool.ts`) enables tool-specific or core-functionality imports. Zod schema validation ensures runtime type safety. Tools register implicitly via export—no manual registry mutation like AGENT-33's `register_tool()`.

**MCP protocol**: First-class MCP support positions OpenCode as an MCP client. Users can add MCP servers via `opencode.jsonc` `"mcp": {}` configuration. This aligns with Anthropic's broader MCP ecosystem (Claude Desktop, Claude Code also support MCP).

**Agent customization**: Both global (`~/.config/opencode/agents/`) and project-local (`.opencode/agents/`) agent definitions enable team-shared agent templates. Markdown-based definitions are more approachable than JSON for non-developers. The translator agent (15KB) demonstrates complex production use cases.

**No workflow composition**: Unlike n8n-workflows' visual DAG builder or AGENT-33's YAML workflow definitions with actions (parallel_group, conditional, transform), OpenCode has no sub-workflow concept, no reusable workflow templates, no merge/join actions. Agents invoke other agents ad-hoc via task tool, not through declared orchestration graphs.

**Integration surface**: Dedicated packages for Slack (`packages/slack`), enterprise features (`packages/enterprise`), containers (`packages/containers`), and identity (`packages/identity`) suggest extensibility at the platform level, not just agent/tool level.

## 6) Notable practices worth adopting in AGENT-33

### 6.1) Wildcard-based permission pattern matching

OpenCode's **last-match-wins glob pattern system** with `*` (zero or more chars) and `?` (single char) for paths and commands is far more ergonomic than AGENT-33's allowlist of exact strings. Examples:
```json
{
  "permission": {
    "*": "ask",              // default: prompt
    "edit": {
      "~/projects/*": "allow",  // home dir expansion
      "*.env": "deny",          // deny all .env files
      "*.env.example": "allow"  // override: allow example files
    },
    "bash": {
      "git status*": "allow",   // allow all git status variants
      "rm -rf*": "deny"         // block destructive deletes
    }
  }
}
```

**Adoption path**: Extend `security/allowlist.py` to support glob patterns using `fnmatch` or `wcmatch`. Add pattern compilation at config load, evaluation at runtime with last-match-wins semantics. Store compiled patterns in `AllowlistRule` model.

### 6.2) Agent-level permission overrides

OpenCode merges global permissions with per-agent overrides (agent config takes precedence). This enables:
- Plan agent: `{"edit": "ask", "bash": "ask"}` — analysis mode
- Build agent: `{"edit": "allow", "bash": "allow"}` — full access
- Explore agent: `{"edit": "deny", "bash": "deny"}` — read-only

**Adoption path**: Add `permissions: dict[str, PermissionAction]` to `AgentDefinition` in `agents/definition.py`. In `tools/governance.py`, merge agent permissions with global allowlist, with agent taking precedence. This would resolve the governance-prompt disconnect identified in research findings.

### 6.3) Three-state permission model (allow/ask/deny)

OpenCode's "ask" state enables **progressive trust** — agents request permission with context, users approve once or create session-scoped patterns. AGENT-33 currently has binary allow/deny.

**Adoption path**: Extend `PermissionAction` enum to include `ASK`. Add `PermissionPrompt` event to NATS bus. Build UI in `packages/app` (or CLI prompt) for approval with "approve once" vs "approve pattern for session" options. Store session-scoped approvals in Redis with TTL.

### 6.4) Markdown-based agent definitions

Markdown agent files are **version-controllable, git-diffable, and readable** without tooling. The filename-as-name convention is intuitive. JSON in frontmatter could hold structured config.

**Adoption path**: Add `AgentDefinitionLoader.from_markdown()` that parses frontmatter (YAML/JSONC) for structured config and treats body as system prompt. Support both `.json` and `.md` in `agent_definitions_dir`. Translator agent example shows this scales to complex agents (15KB).

### 6.5) doom_loop protection

OpenCode blocks after **3 identical tool calls** to prevent infinite loops. Simple, effective, observable.

**Adoption path**: Add `RecentToolCallTracker` to `AgentRuntime` that stores last N calls in a ring buffer, compares hashes. Raise `DoomLoopDetected` exception after threshold. Make threshold configurable per agent. Log when triggered for eval dataset.

### 6.6) LSP-as-tool integration

Exposing **language server queries as a tool** gives agents semantic code understanding: diagnostics, go-to-def, hover, references. Far richer than grep/glob.

**Adoption path**: Create `LspTool` in `tools/builtins/` that wraps `pygls` or `lsprotocol`. Auto-detect language servers from `.vscode/settings.json`, `pyrightconfig.json`, etc. Add `lsp` permission. Cache LSP instances per session. This would elevate code-worker and qa agents beyond regex-based validation.

### 6.7) Session-scoped permission grants

Feature request #13505 proposes "allow for session" instead of permanent grants. Reduces permission creep.

**Adoption path**: Store session-scoped permissions in Redis with `SESSION:{session_id}:PERMISSIONS` key, TTL=session lifetime. Merge into permission evaluation. Clear on session end. This aligns with AGENT-33's existing Redis-based session state.

## 7) Risks / limitations to account for

### 7.1) No sandbox = permissions are UX, not security

OpenCode's security docs state explicitly: **"OpenCode does not sandbox the agent"** — permissions are for awareness, not isolation. For security, users must run inside Docker/VM. This is **antithetical to AGENT-33's governance model** where constraints are enforcement boundaries, not suggestions. If AGENT-33 adopts OpenCode's permission patterns, it must not inherit this security posture.

**Mitigation**: AGENT-33's Phase 13 `CodeExecutor` with CLI/Docker/Firecracker adapters already provides true sandboxing. Wildcard patterns should layer on top of sandbox enforcement, not replace it.

### 7.2) Permission fatigue → "allow all" risk

727 issues mention "permission" with complaints like "Why does open-source code need to request so many permissions?" (#13273). Excessive prompts train users to auto-approve.

**Mitigation**: Default to "allow" for common operations (read, non-destructive bash), "ask" for risky ops (edit .env, external_directory), "deny" for known-bad patterns (rm -rf /). Use ML to learn per-user/per-project patterns over time (AGENT-33 has training module, OpenCode doesn't).

### 7.3) LSP memory leaks and timeouts

Production issues show **111GB virt/21GB RSS memory leaks** causing kernel lockups and OOM kills. 3-second diagnostic timeout too short for JDTLS/ESLint on large codebases.

**Mitigation**: Run LSP servers in separate processes with cgroup memory limits (Docker adapter). Make timeout configurable per language server. Implement LSP request cancellation. Monitor RSS and restart servers above threshold.

### 7.4) OTLP traces not emitting despite config

Telemetry is non-functional in production (#13438) despite OTEL integration being marked complete. Observability is critical for multi-agent debugging.

**Mitigation**: AGENT-33's `observability/` module with structlog, tracing, and metrics is more mature. If adopting OTEL, validate trace emission in CI, not just integration tests.

### 7.5) No evaluation or self-improvement

OpenCode has no rollout capture, no A/B testing, no automated agent performance evaluation. Growth is viral (10M+ downloads) but quality relies on manual issue triage.

**Mitigation**: AGENT-33's Phase 21 training loop (rollout capture, eval, optimization, scheduling) is a strategic differentiator. Don't abandon it for OpenCode's ad-hoc approach.

### 7.6) Client-server architecture increases attack surface

OpenCode runs as HTTP server (opt-in, basic auth via `OPENCODE_SERVER_PASSWORD`). Docs state: **"It is the end user's responsibility to secure the server."** No HTTPS by default, no rate limiting, no CSRF protection evident.

**Mitigation**: AGENT-33's FastAPI app has `AuthMiddleware`, JWT/API-key auth, tenant isolation, and encryption. If adding server mode, enforce TLS, add rate limiting (via Redis), and security headers.

### 7.7) 5,160 open issues suggest overwhelmed maintenance

With 104K stars and 10M downloads, 5,160 open issues (as of Feb 14, 2026) indicates severe triage backlog. Quality monitoring features marked "not planned."

**Mitigation**: AGENT-33 is not viral (yet). Maintain strict issue triage, automate regression testing, and prioritize evaluation gates (Phase 17) to avoid this fate.

## 8) Feature extraction (for master matrix)

| Feature | OpenCode | AGENT-33 (current) | Gap / Action |
|---------|----------|-------------------|--------------|
| **Permission system** | Wildcard glob patterns (allow/ask/deny) | Exact-string allowlists (allow/deny) | **Adopt glob patterns + 3-state model** |
| **Agent-level permissions** | Per-agent permission overrides | Global allowlist only | **Add `permissions` to AgentDefinition** |
| **Permission scope** | Session-scoped + permanent | Permanent only | **Add session-scoped grants in Redis** |
| **doom_loop protection** | Blocks after 3 identical calls | None | **Add RecentToolCallTracker** |
| **LSP integration** | Native, auto-loaded, tool-exposed | None | **Create LspTool, auto-detect servers** |
| **MCP support** | First-class via config | Via mcp__* tools (imported) | **Document MCP client usage** |
| **Sandbox** | None (permissions are UX) | Phase 13 CodeExecutor (CLI/Docker/Firecracker) | **AGENT-33 advantage, do not regress** |
| **Tool framework** | `@opencode-ai/plugin` with Zod schemas | BaseToolSpec with JSON schemas | **Consider Zod for runtime validation** |
| **Custom tools** | Markdown .txt description + .ts impl | Python class + JSON spec | **Adopt Markdown descriptions** |
| **Agent definitions** | Markdown + JSON, filename-as-name | JSON only, registry auto-discovery | **Support .md agent definitions** |
| **Agent modes** | Primary vs subagent, mode flag | Role-based (orchestrator, worker, etc.) | **Add mode taxonomy** |
| **Workflow engine** | None (LLM-driven ad-hoc) | DAG-based with 9 action types | **AGENT-33 advantage** |
| **Observability** | Experimental OTEL (broken), download stats | structlog, tracing, metrics, lineage | **AGENT-33 advantage** |
| **Evaluation** | None | Phase 21 training loop | **AGENT-33 advantage** |
| **Multi-session** | Parallel agents on same project | Single-threaded per workflow | **Adopt parallel session support** |
| **Session sharing** | `/share` command for replay links | None | **Add shareable session URLs** |
| **Undo/redo** | Built-in commands | None | **Add command history + replay** |
| **LLM providers** | 75+ via Models.dev + Vercel AI SDK | 3 (Ollama, OpenAI-compatible, router) | **Expand provider support** |
| **Tree-sitter parsing** | Yes (10.7KB parsers-config.ts) | None | **Add for code understanding** |
| **External integrations** | Slack, enterprise packages | Telegram, Discord, Slack, WhatsApp via NATS | **Similar scope** |
| **Security model** | No sandbox, user-run Docker/VM | Sandboxed execution + governance | **AGENT-33 advantage** |
| **Auth** | HTTP Basic (server mode opt-in) | JWT + API keys + multi-tenant | **AGENT-33 advantage** |
| **Database** | Drizzle ORM (beta) | SQLAlchemy + Alembic | **Similar** |
| **Runtime** | Bun + TypeScript | Python 3.11+ | **Language difference** |

**Priority adoptions for Phase 14 (Security Hardening)**:
1. Wildcard glob permission patterns (governance layer)
2. Agent-level permission overrides (resolve governance-prompt disconnect)
3. Three-state allow/ask/deny model (progressive trust)
4. doom_loop protection (safety guardrail)
5. Session-scoped permissions (reduce permission creep)

**Phase 15+ considerations**:
6. LSP-as-tool integration (code understanding)
7. Markdown agent definitions (developer UX)
8. Multi-session parallelism (throughput)
9. Session sharing URLs (collaboration)
10. Tree-sitter parsing (semantic analysis)

## 9) Evidence links

### Official Resources
- **Repository**: https://github.com/anomalyco/opencode (104,405 stars, 10,135 forks)
- **Homepage**: https://opencode.ai
- **Documentation**: https://opencode.ai/docs
- **License**: MIT

### Key Documentation
- **Permissions**: https://opencode.ai/docs/permissions (glob patterns, 3-state model)
- **Agents**: https://opencode.ai/docs/agents (agent types, configuration)
- **Security**: https://github.com/anomalyco/opencode/blob/dev/SECURITY.md (threat model, no sandbox)
- **Stats**: https://github.com/anomalyco/opencode/blob/dev/STATS.md (7.8M GitHub, 2.4M npm downloads)

### Architecture Evidence
- **Monorepo structure**: https://api.github.com/repos/anomalyco/opencode/contents/packages (16 packages)
- **Technology stack**: https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/opencode/package.json (Bun, Hono, Drizzle, 15+ LLM SDKs)
- **Plugin framework**: https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/plugin/package.json (Zod validation)
- **Custom tool example**: https://raw.githubusercontent.com/anomalyco/opencode/dev/.opencode/tool/github-triage.ts (plugin API usage)
- **Agent example**: https://raw.githubusercontent.com/anomalyco/opencode/dev/.opencode/agent/translator.md (15KB production agent)
- **Permission UI**: https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/app/src/components/settings-permissions.tsx (16 configurable tools)
- **Permission context**: https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/app/src/context/permission.tsx (auto-accept logic)

### Issue Tracker Evidence
- **Permission fatigue**: https://github.com/anomalyco/opencode/issues?q=is%3Aissue+permission (727 issues)
- **LSP challenges**: https://github.com/anomalyco/opencode/issues?q=is%3Aissue+LSP (timeouts, memory leaks)
- **Observability gaps**: https://github.com/anomalyco/opencode/issues?q=is%3Aissue+observability+OR+telemetry (OTLP broken #13438, monitoring gaps)
- **Session-scoped permissions**: https://github.com/anomalyco/opencode/issues/13505 (feature request)
- **External directory prompts**: https://github.com/anomalyco/opencode/issues/13346 (permission UX bug)
- **Memory leaks**: https://github.com/anomalyco/opencode/issues/13230 (111GB virt/21GB RSS OOM kills)

### Metrics
- **Download stats**: 10,190,453 total (as of 2026-01-29), 326K/day GitHub, 60K/day npm
- **GitHub stars**: 104,405 (as of 2026-02-14)
- **Open issues**: 5,160 (as of 2026-02-14)
- **Forks**: 10,135
- **Repository size**: 175,150 KB
- **Primary language**: TypeScript
- **Default branch**: dev
