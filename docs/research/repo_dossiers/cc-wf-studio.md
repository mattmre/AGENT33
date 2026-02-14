# Repo Dossier: breaking-brake/cc-wf-studio

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

CC Workflow Studio is a VS Code extension (3,735 stars, actively maintained) that provides a visual drag-and-drop workflow designer for AI agent orchestration across Claude Code, GitHub Copilot, OpenAI Codex, and Roo Code. It combines a React Flow-based node canvas with conversational AI refinement ("Edit with AI"), enabling users to design workflows through visual composition or natural language, then export to platform-specific formats (.claude/agents/, .github/skills/, etc.). The system enforces strict DAG validation (max 50 nodes, no cycles, all paths reach End), supports 11 node types (SubAgent, AskUserQuestion, IfElse, Switch, Skill, MCP, SubAgentFlow, Codex, Start, End, Prompt, legacy Branch), and integrates Model Context Protocol for external tool access. Built with TypeScript, it stores workflows as JSON in `.vscode/workflows/`, uses semantic-release automation, and targets a <15KB schema file optimized for AI context consumption. The project represents the state-of-the-art in visual workflow authoring UX for AI coding tools, with a particular strength in bidirectional workflow-AI communication via MCP server integration.

## 2) Core orchestration model

**DAG-based workflow execution with strict structural constraints:**
- Exactly one Start node, at least one End node, all nodes reachable from Start, all paths lead to End
- No cycles allowed (enforced by validation rules in `workflow-definition.ts`)
- Maximum 50 nodes per workflow, 30 nodes per sub-agent flow

**11 node types in a hierarchical taxonomy:**
- **Linear nodes** (single input → single output): start, end, prompt, subAgent, skill, mcp, subAgentFlow, codex
- **Conditional nodes** (single input → multiple outputs): ifElse (2-way), switch (3+ way), askUserQuestion (2-4 options)
- All conditional branches must have exactly one outgoing connection

**SubAgent execution model:**
- Configurable models: sonnet/opus/haiku/inherit (from parent context)
- Memory scopes: user (cross-session persistent), project (shared within repo), local (workflow-scoped)
- Tool access controlled per agent (tools allowlist embedded in node data)
- Critical constraint: "SubAgent nodes cannot be used inside sub-agent flows" due to Claude Code sequential execution limitations

**Sub-agent flows as reusable components:**
- Workflows can define named sub-flows (stored in same JSON file)
- SubAgentFlow nodes reference these by name for composition
- Sub-flows have tighter constraints: max 30 nodes, no subAgent/subAgentFlow/askUserQuestion types allowed

**Connection framework:**
- Nodes connect via typed ports: "output"/"input" for linear, "branch-0"/"branch-1"/etc. for conditional
- Connections include optional condition labels (for switch nodes matching case values)
- Port naming enforces structural correctness at the type level

**Execution semantics (inferred from schema):**
- Workflows compile to platform-specific formats (Claude Code commands/agents, Copilot skills, Codex CLI)
- No runtime engine in this repo—execution delegated to target platforms
- Workflows are **authoring artifacts** that export to **execution artifacts**

## 3) Tooling and execution

**Visual design interface:**
- React Flow-based drag-and-drop canvas in webview
- Node palette with 11 types (grouped by category: control flow, agents, tools)
- Real-time validation with visual feedback (invalid nodes/connections highlighted)
- Custom editor registers for `**/.vscode/workflows/*.json` files

**AI-assisted refinement workflow:**
- "Edit with AI" button launches bidirectional conversation
- MCP server auto-starts when AI agent selected (native MCP integration)
- User provides natural language requests → AI modifies workflow JSON → extension updates canvas
- Conversation history stored in workflow file for iterative refinement
- Supported AI providers: Claude Code (sonnet/opus/haiku), Copilot, Codex
- Timeout configuration: 10-120 seconds per refinement request

**Tool integration via MCP:**
- McpNode supports three modes: manual parameter config, AI parameter config, AI tool selection
- MCP servers discovered from project/user scopes (`.mcp.json`, `~/.copilot/mcp-config.json`, etc.)
- Tool schemas fetched via MCP protocol, injected into workflow schema for AI context
- Cache refresh mechanism for MCP server updates

**Skill library integration:**
- Skill nodes reference Claude Code Skills from system/project/user scopes
- Validation during workflow load: valid/missing/invalid states computed
- Execution modes: "load" (include skill in export) vs. "execute" (invoke at runtime)
- Cross-platform detection: Copilot and Codex CLI skills with grouped UI display

**Export targets (multi-platform):**
1. **Claude Code**: `.claude/agents/*.md` (agents) and `.claude/commands/*.md` (commands)
2. **GitHub Copilot**: `.github/prompts/` (Chat) and `.github/skills/` (CLI)
3. **OpenAI Codex**: `.codex/skills/`
4. **Roo Code**: `.roo/skills/`

**Export includes slash command hooks:**
- PreToolUse, PostToolUse, Stop hooks configurable per workflow
- Hooks compile to platform-specific lifecycle events

**Execution model delegation:**
- No built-in runtime—workflows are **static artifacts**
- Execution occurs in target AI platform (Claude Code runs commands, Copilot executes skills, etc.)
- SubAgentFlow nodes execute sequentially when invoked by host platform

**Validation enforcement:**
- Workflow names: lowercase only (cross-platform filesystem compatibility)
- Skill names: lowercase, numbers, hyphens only (pattern: `^[a-z0-9-]+$`)
- AskUserQuestion: 2-4 options for single-select, descriptions max 200 chars
- Prompt nodes: max 10,000 chars
- Connection validation: all branches connected, no dangling nodes, no unreachable paths

## 4) Observability and evaluation

**No built-in observability layer:**
- Extension is an **authoring tool**, not an execution runtime
- Observability delegated to target platforms (Claude Code, Copilot, etc.)
- No tracing, metrics, or lineage capture within cc-wf-studio itself

**AI refinement telemetry (minimal):**
- A/B testing for schema format (Toon vs. JSON) with optional metrics collection
- Toon format reduces token consumption by ~23% vs. JSON (per package.json config)
- No details on what metrics are collected or where they're sent

**Validation as quality gate:**
- Real-time validation during authoring prevents invalid workflows from being saved
- Skill validation detects missing/invalid references before export
- MCP tool validation ensures referenced tools exist in configured servers
- SubAgent tool warnings flag unsupported tools during export (open issue #31)

**Conversation history for reproducibility:**
- AI refinement conversations stored in workflow JSON
- Enables tracing how a workflow evolved through AI iterations
- No formal evaluation of AI-suggested changes—user accepts/rejects manually

**Release automation includes implicit quality gates:**
- Semantic-release enforces conventional commits (breaking changes → major version)
- CI builds extension and packages `.vsix` (build failure blocks release)
- No explicit test suite runs in release.yml workflow (notable gap)
- Changelog auto-generated from commit messages

**User-reported gaps (from open issues):**
- No warnings for SubAgent nodes using tools unavailable in export target (#31)
- MCP tool name validation in AI-generated workflows needed (#30)
- Sequential MCP tool loading lacks progress visibility (#21)

## 5) Extensibility

**Schema-driven architecture:**
- `workflow-schema.json` (resources/) defines node types, validation rules, connection constraints
- Schema serves dual purpose: runtime validation + AI context for workflow generation
- Target size: <15KB (optimized for AI token budgets)
- Synchronization required: `src/shared/types/workflow-definition.ts` ↔ `workflow-schema.json`

**Node type additions:**
- New node types added by: (1) extending `NodeType` enum, (2) adding data interface, (3) updating schema, (4) updating validation rules
- Backward compatibility enforced: deprecated nodes maintained with deprecation notices (not immediate removal)
- Example evolution: legacy "branch" node deprecated but still in schema

**MCP as primary extensibility mechanism:**
- MCP nodes provide unlimited external tool access (no hardcoded tool registry)
- Tool schemas dynamically fetched from MCP servers
- Three operational modes support varying levels of AI autonomy vs. manual control
- Open issue: MCP tool name validation needed for AI-generated workflows (#30)

**AI provider abstraction:**
- Refinement supports multiple providers: Claude Code, Copilot, Codex
- Provider-specific translation keys in i18n system
- Model selection abstracted: sonnet/opus/haiku map to provider-specific models
- Execution mode selection varies by provider (e.g., Copilot load vs. execute modes)

**Export format modularity:**
- Four export targets with distinct file structure conventions
- Config reference doc (`ai-coding-tools-config-reference.md`) maps cross-platform patterns
- No automated translation between platforms—manual restructuring required
- Portable components: rule files (Markdown), skills (frontmatter schema), MCP configs (JSON key renaming)

**Sub-agent flows as reusable components:**
- Workflows can define multiple named sub-flows
- Sub-flows stored in same JSON file (composition within single artifact)
- SubAgentFlow nodes reference by name → enables DRY principle
- Limitation: cannot nest SubAgentFlow nodes (single-level composition only)

**Slack integration for workflow sharing (recent addition per changelog):**
- Import/export workflows to Slack workspaces
- Multi-workspace authentication via OAuth
- Sensitive data detection before sharing
- Indicates direction toward collaborative workflow libraries

**Internationalization support:**
- `i18n/` directory in extension suggests multi-language UI
- Provider-specific translation keys (claude-code, copilot, codex)
- Locale files not inspected (would need deeper dive)

**Gaps in extensibility:**
- Custom node types require modifying extension source (no plugin system)
- Schema must stay <15KB → limits node type proliferation
- No API for programmatic workflow generation (only visual + AI chat)
- Sub-agent flow nesting limitation reduces compositional depth

## 6) Notable practices worth adopting in AGENT-33

### 1. **Dual-purpose schema design (runtime + AI context)**
- `workflow-schema.json` serves both validation enforcement and AI generation context
- Size-constrained (<15KB) to fit in AI prompts—forces clarity and conciseness
- **For AGENT-33**: Create `agent33-schema.json` combining governance constraints, capability taxonomy, and workflow action specs in <20KB; inject into AgentRuntime system prompts

### 2. **Toon format for token efficiency**
- Custom schema format reduces prompt size by 23% vs. JSON
- A/B tested with metrics to validate optimization
- **For AGENT-33**: Audit current prompt templates for token waste; consider compressed schema format for governance rules (currently verbose in definition.py)

### 3. **Bidirectional workflow-AI communication**
- Workflows aren't just executed—they're **collaboratively designed** with AI
- User provides intent → AI modifies structure → user refines → AI iterates
- MCP server enables AI to read/write workflow JSON directly
- **For AGENT-33**: Extend workflow engine with `/refine` endpoint accepting natural language → LLM edits DAG → returns updated workflow JSON

### 4. **Validation-as-authoring-constraint**
- Real-time validation prevents invalid workflows from being saved
- Validation rules enforced in TypeScript types (compile-time) + JSON schema (runtime) + visual UI (user feedback)
- **For AGENT-33**: Strengthen workflow validation in `engine/src/agent33/workflows/definition.py`—currently minimal; add topological validation, port-type checking, resource limit enforcement

### 5. **Multi-platform export strategy**
- Single workflow source → multiple execution targets
- Config reference doc normalizes cross-platform patterns
- **For AGENT-33**: Build export layer transforming AGENT-33 workflows to external formats (Temporal workflows, n8n JSON, Prefect DAGs) for interop with ecosystem tools

### 6. **Conversation history in workflow artifact**
- AI refinement conversations stored in workflow JSON
- Enables tracing design evolution and understanding intent
- **For AGENT-33**: Add `design_rationale` field to WorkflowDefinition model; capture LLM refinement conversations in workflow metadata; use for observability/debugging

### 7. **Semantic-release automation with branch sync**
- Conventional commits → automatic versioning → changelog generation
- Production branch auto-syncs back to main (maintains parity without manual merges)
- **For AGENT-33**: Adopt semantic-release for `engine/` package; configure `.releaserc.json` with conventional commit parser; add branch sync to release workflow

### 8. **Schema-TypeScript synchronization discipline**
- `schema-maintenance.md` enforces: (1) update TypeScript types first, (2) sync JSON schema, (3) update examples, (4) verify through tests
- Backward compatibility for deprecated node types (graceful migration)
- **For AGENT-33**: Document sync protocol for `agent_definitions/*.json` ↔ `agents/definition.py` ↔ `core/specs/agents/`; add pre-commit hook validating schema consistency

### 9. **SubAgent memory scope taxonomy**
- Three-level memory: user (persistent cross-session), project (repo-scoped), local (workflow-scoped)
- Explicit scoping prevents unintended data sharing
- **For AGENT-33**: Extend memory system with explicit scope declarations; add `scope` field to `SessionState` model; enforce isolation in `memory/store.py`

### 10. **MCP as extensibility escape hatch**
- Hardcoded tools limit flexibility—MCP provides unlimited external access
- Tool schemas dynamically fetched → no schema drift
- **For AGENT-33**: Prioritize MCP server development over expanding `tools/builtins.py`; build MCP adapters for shell/file_ops/browser tools; deprecate hardcoded registry in favor of MCP discovery

### 11. **Visual workflow authoring for non-programmers**
- Drag-and-drop canvas lowers barrier vs. YAML/JSON editing
- AI assistance enables "describe what you want" → visual workflow
- **For AGENT-33**: Build web UI for workflow designer (Phase 22 candidate); use React Flow library (proven choice); integrate with AgentRuntime for AI-assisted design

### 12. **Skill validation during workflow load**
- Skills checked against available system/project/user libraries
- Invalid skills flagged before execution → prevents runtime failures
- **For AGENT-33**: Add skill/tool validation in workflow engine startup; verify `workflow_actions/*.py` imports succeed; check tool allowlists exist in registry before DAG execution

## 7) Risks / limitations to account for

### 1. **No execution runtime → observability gap**
- cc-wf-studio is authoring-only; execution happens in external platforms
- Cannot trace workflow execution, measure performance, or capture intermediate state
- **For AGENT-33**: Ensure workflow engine (`workflows/executor.py`) captures full lineage; don't replicate cc-wf-studio's delegation model—AGENT-33 must own execution

### 2. **SubAgent nesting limitation**
- "SubAgent nodes cannot be used inside sub-agent flows" due to Claude Code sequential execution
- Limits compositional depth for complex workflows
- **For AGENT-33**: Verify workflow executor supports arbitrary nesting; if not, document limitation and add validation preventing nested agent invocations

### 3. **No automated testing in release pipeline**
- `release.yml` workflow has build/package steps but no `npm test` or similar
- Quality relies on manual testing pre-merge
- **For AGENT-33**: Never skip tests in CI/CD; `release.yml` equivalent must run full pytest suite before deploying

### 4. **Schema size constraint limits node type proliferation**
- <15KB target for AI context consumption prevents adding many node types
- Trade-off: expressiveness vs. token budget
- **For AGENT-33**: If building visual workflow designer, accept this constraint—25 action types in `workflows/actions/` may already exceed reasonable schema size for AI consumption

### 5. **Multi-platform export requires manual restructuring**
- No automated translation between Claude Code, Copilot, Codex, Roo formats
- Config reference doc shows mappings, but user must manually adapt
- **For AGENT-33**: If implementing multi-platform export, build automated transformers (not just documentation); test round-trip conversions

### 6. **MCP tool validation gap**
- Open issue #30: AI-generated workflows reference non-existent MCP tools
- No validation until export/execution fails
- **For AGENT-33**: When integrating MCP, add tool existence checks in workflow validation phase; query MCP servers for available tools before allowing references

### 7. **Conversation history bloat**
- AI refinement conversations stored in workflow JSON
- Could grow unbounded for heavily-iterated workflows
- **For AGENT-33**: If storing design rationale, implement retention policy (e.g., keep last 10 refinement rounds, summarize older history)

### 8. **Toon format is proprietary**
- 23% token savings from custom format requires maintaining separate schema
- Ecosystem tooling expects JSON—Toon adds conversion overhead
- **For AGENT-33**: Evaluate token savings vs. interop cost; prefer standard formats unless savings are substantial (>20%) and measured

### 9. **Single-level sub-flow composition**
- Cannot nest SubAgentFlow nodes → limits hierarchical decomposition
- Flat structure acceptable for simple workflows, limiting for complex ones
- **For AGENT-33**: Support arbitrary nesting in `invoke_agent.py` action; test recursion depth limits; enforce max depth via governance constraints

### 10. **AGPL-3.0 license requires source disclosure**
- Network deployment triggers copyleft (not just distribution)
- Forking cc-wf-studio for AGENT-33 UI would require open-sourcing modifications
- **For AGENT-33**: If building visual designer, implement from scratch or use MIT/Apache-licensed alternatives (e.g., React Flow is MIT); avoid GPL/AGPL dependencies in proprietary contexts

### 11. **No role-based access control**
- All users have full workflow edit rights
- No approval gates for AI-generated changes
- **For AGENT-33**: Multi-tenant architecture requires RBAC; extend workflow engine with approval workflows (Phase 15) before exposing visual designer to multiple users

### 12. **Windows compatibility issues noted**
- Version 3.15.3 normalized CRLF endings, improved CLI detection
- Suggests Windows was not primary development platform
- **For AGENT-33**: Already has Windows-specific handling in `execution/adapters/cli_adapter.py`; ensure visual designer (if built) tests on Windows (path separators, line endings, subprocess spawning)

## 8) Feature extraction (for master matrix)

| Feature | cc-wf-studio | AGENT-33 Status | Priority for Integration |
|---------|--------------|-----------------|--------------------------|
| **Visual workflow designer** | React Flow drag-and-drop canvas | ❌ None (text-based DAGs only) | **HIGH** — Phase 22 candidate; dramatically improves accessibility |
| **AI-assisted workflow refinement** | "Edit with AI" via MCP server | ❌ None (workflows are static YAML/Python) | **HIGH** — `/refine` endpoint for LLM-driven workflow edits |
| **Multi-platform workflow export** | Claude/Copilot/Codex/Roo formats | ❌ AGENT-33-only execution | MEDIUM — Interop with n8n, Temporal, Prefect for ecosystem integration |
| **DAG validation (topological)** | No cycles, all paths reach End, reachability checks | ⚠️ Partial (basic validation in executor) | **HIGH** — Strengthen validation in `workflows/definition.py` |
| **Sub-workflow composition** | SubAgentFlow nodes reference named sub-flows | ✅ Yes (`parallel_group` action supports sub-DAGs) | LOW — Already supported, ensure nesting depth limits |
| **MCP tool integration** | Dynamic tool discovery, three operational modes | ⚠️ In progress (Phase 12 delivered tool registry) | **CRITICAL** — Phase 14 must integrate MCP for external tools |
| **Skill library with validation** | Cross-scope detection, valid/missing/invalid states | ❌ No skill abstraction (tools hardcoded) | MEDIUM — Build skill layer on top of tool registry |
| **Memory scope taxonomy** | user/project/local scopes | ⚠️ Partial (session-scoped only) | MEDIUM — Extend `memory/store.py` with explicit scope declarations |
| **Conversation history in artifacts** | AI refinement logs stored in workflow JSON | ❌ None | MEDIUM — Add `design_rationale` to WorkflowDefinition |
| **Semantic-release automation** | Conventional commits → auto-versioning → changelog | ❌ Manual versioning | MEDIUM — Adopt for `engine/` package releases |
| **Toon schema format (token-optimized)** | 23% reduction vs. JSON | ❌ Standard JSON/YAML | LOW — Evaluate after prompt token audit |
| **Slash command export with hooks** | PreToolUse, PostToolUse, Stop lifecycle events | ❌ No lifecycle hooks | LOW — Not needed for current orchestration model |
| **Real-time validation UI feedback** | Visual highlighting of invalid nodes/connections | ❌ N/A (no UI) | N/A — Depends on visual designer adoption |
| **Schema-TypeScript sync discipline** | Documented process, backward compatibility | ⚠️ Informal (no sync protocol) | MEDIUM — Document in CLAUDE.md, add pre-commit hook |
| **Configurable AI timeouts** | 10-120 sec per refinement request | ⚠️ Global timeout only (no per-request config) | LOW — Add to workflow action definitions if needed |
| **Conditional branching (switch nodes)** | 3+ way multi-case with required default | ✅ Yes (`conditional` action) | LOW — Already supported |
| **User interaction nodes** | AskUserQuestion with 2-4 options | ❌ No interactive prompts in workflows | MEDIUM — Add `user_prompt` action for interactive workflows |
| **Platform-specific model selection** | sonnet/opus/haiku/inherit from context | ⚠️ Partial (ModelRouter supports providers) | LOW — Already flexible via `llm/router.py` |
| **Workflow size limits** | 50 nodes max, 30 for sub-flows | ❌ No enforced limits | MEDIUM — Add to governance constraints |
| **Cross-platform filesystem compatibility** | Lowercase workflow names enforced | ✅ Yes (Windows support in Phase 13) | LOW — Already handled |

## 9) Evidence links

### Primary Sources
- **Repository**: https://github.com/breaking-brake/cc-wf-studio (3,735 stars, 426 forks, last updated 2026-02-14)
- **Package Metadata**: https://raw.githubusercontent.com/breaking-brake/cc-wf-studio/main/package.json (v3.21.0, TypeScript, Vite build)
- **Workflow Schema**: https://raw.githubusercontent.com/breaking-brake/cc-wf-studio/main/resources/workflow-schema.json (DAG constraints, 11 node types)
- **Type Definitions**: https://raw.githubusercontent.com/breaking-brake/cc-wf-studio/main/src/shared/types/workflow-definition.ts (NodeType enum, validation rules)
- **Message Protocol**: https://raw.githubusercontent.com/breaking-brake/cc-wf-studio/main/src/shared/types/messages.ts (Extension-Webview-MCP communication)

### Documentation
- **AI Tool Config Reference**: https://raw.githubusercontent.com/breaking-brake/cc-wf-studio/main/docs/ai-coding-tools-config-reference.md (Cross-platform export patterns)
- **Schema Maintenance**: https://raw.githubusercontent.com/breaking-brake/cc-wf-studio/main/docs/schema-maintenance.md (Sync discipline, backward compatibility)
- **Release Automation**: https://raw.githubusercontent.com/breaking-brake/cc-wf-studio/main/docs/release-automation.md (Semantic-release process)

### CI/CD
- **Release Workflow**: https://raw.githubusercontent.com/breaking-brake/cc-wf-studio/main/.github/workflows/release.yml (Build, package, branch sync)
- **Semantic-Release Config**: https://raw.githubusercontent.com/breaking-brake/cc-wf-studio/main/.releaserc.json (Commit analysis, changelog)

### Community Activity
- **Open Issues**: https://github.com/breaking-brake/cc-wf-studio/issues (32 open, key themes: MCP validation, multi-agent support, SubAgent tool warnings)
- **Pull Requests**: https://github.com/breaking-brake/cc-wf-studio/pulls (9 open, mostly dependency updates via Dependabot)
- **Changelog**: https://github.com/breaking-brake/cc-wf-studio/blob/main/CHANGELOG.md (Recent: v3.21.0 MCP server, v3.20.0 Roo Code, v3.19.0 Codex agent)

### Technical Stack
- **Primary Language**: TypeScript (97.6%)
- **UI Framework**: React Flow (inferred from package.json dependencies)
- **Build Tool**: Vite
- **License**: AGPL-3.0-or-later (requires source disclosure for network deployments)
- **MCP Integration**: `@modelcontextprotocol/sdk` ^1.26.0
- **Extension Platform**: VS Code (custom editor for `.vscode/workflows/*.json`)

### Key Findings
- **Governance-prompt disconnect analog**: cc-wf-studio's schema exists but isn't validated until export (MCP tool names, SubAgent tool warnings)—parallels AGENT-33's governance constraints never reaching LLM prompts
- **Visual authoring as accessibility win**: 3,735 stars indicate strong demand for visual workflow design over text-based DAG editing
- **MCP as future-proof extensibility**: Dynamic tool discovery eliminates hardcoded registry maintenance burden
- **Schema size as design constraint**: <15KB target forces ruthless clarity—valuable lesson for AGENT-33 prompt engineering
- **Execution delegation trade-off**: Authoring-only tool gains simplicity, loses observability—AGENT-33 must maintain full execution ownership
