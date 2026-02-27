# PAI Development Principles Analysis & AGENT-33 Adaptation Roadmap

**Date**: 2026-02-23
**Source**: Daniel Miessler's [PAI (Personal AI Infrastructure)](https://danielmiessler.com/blog/personal-ai-infrastructure) v3.0
**Repository**: [danielmiessler/Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure)
**Purpose**: Extract development cycle principles, extensibility patterns, and connector architecture from PAI to plan improvement phases for AGENT-33

---

## 1. Executive Summary

PAI is a personal AI infrastructure built natively on Claude Code that implements a **7-phase scientific method** (The Algorithm) with persistent memory, event-driven hooks, 38+ skills, and 12 named agents. While PAI targets individual productivity and AGENT-33 targets enterprise multi-agent orchestration, PAI's development principles around **verifiable iteration**, **automated agent scaffolding**, and **extensible connector architecture** are directly applicable.

This analysis identifies **15 adaptation items** across **5 proposed improvement phases** (Phases 29-33), focusing on making AGENT-33's automated agents more effective and the platform more extensible.

---

## 2. PAI Core Principles & AGENT-33 Mapping

### 2.1 The Algorithm: 7-Phase Scientific Method

**PAI Pattern**: Every task follows OBSERVE → THINK → PLAN → BUILD → EXECUTE → VERIFY → LEARN with quality gates between phases.

**Key Innovation — ISC (Ideal State Criteria)**: Binary-testable success conditions created at OBSERVE time. Example: "No credentials exposed in git history" rather than "clean git state." 8-12 word constraint forces specificity.

**AGENT-33 Gap**: Our workflow engine executes DAG steps and the tool-use loop (P0) handles action-observation cycles with stuck detection, but there's no formalized **requirement extraction, verification rehearsal, or ISC-style learning capture** per task. The existing ToolLoop (64 tests) provides the execution substrate; what's missing is the reasoning protocol wrapping it.

**Adaptation**: Phase 29 — Agent Reasoning Protocol (see Section 4.1)

### 2.2 Scaffolding > Model Intelligence

**PAI Principle**: "The model stays the same. The scaffolding gets better every day." Infrastructure (context management, skills, hooks, steering rules) wrapping the base model drives more improvement than model upgrades.

**AGENT-33 Alignment**: We already follow this via progressive skill disclosure (L0/L1/L2), context window management, and 4-stage skill matching. The gap is that **scaffolding improvements aren't captured and fed back automatically**.

**Adaptation**: Phase 31 — Continuous Learning Loop (see Section 4.3)

### 2.3 Code → CLI → Prompt → Skill Decision Hierarchy

**PAI Principle**: Always prefer deterministic code over AI. Use AI only for intelligence gaps. Each tier increases abstraction while maintaining reliability.

| Tier | Determinism | Example |
|------|-------------|---------|
| Code | Highest | TypeScript/Python scripts |
| CLI Tool | High | fabric, git, curl pipelines |
| Simple Prompt | Medium | Single-step LLM inference |
| Complex Skill | Lower | Multi-step workflow with state |

**AGENT-33 Gap**: Our skills system doesn't enforce or suggest this hierarchy. The code execution layer (Phase 13, CLIAdapter + CodeExecutor) and tool governance layer provide deterministic execution paths, but **there's no routing decision that selects between them**. An agent might use an LLM call where a Python script via CodeExecutor would be more reliable.

**Adaptation**: Phase 30 — Deterministic Routing Layer (see Section 4.2)

### 2.4 Spec/Test/Evals First

**PAI Principle**: Define success criteria before implementation. ISC criteria are created during OBSERVE, validated during VERIFY with mechanical tool-call verification (not prose claims of "PASS").

**AGENT-33 Alignment**: Phase 17 (Evaluation Gates) provides golden tasks/cases and regression detection. However, automated agents creating workflows **don't create verification criteria as a first step** — they jump to execution.

**Adaptation**: Incorporated into Phase 29 (Agent Reasoning Protocol)

### 2.5 Build Drift Prevention

**PAI Pattern**: Two-gate system during BUILD phase:
1. **ISC Adherence Check** (before each artifact): "Which constraints apply to this artifact?"
2. **Constraint Checkpoint** (after each artifact): "Does this artifact satisfy those constraints?"

**AGENT-33 Gap**: Workflow execution has no mid-step constraint validation. An agent can drift from requirements during long multi-step workflows without detection until final verification.

**Adaptation**: Phase 29 checkpoint system

### 2.6 Self-Interrogation Protocol

**PAI Pattern**: 5 structured questions detect blind spots:
1. What information am I missing?
2. What assumptions am I making?
3. What could I be misunderstanding?
4. Am I solving the right problem?
5. Am I abstracting away important details?

**AGENT-33 Gap**: Phase 15 (Review Automation) provides two-layer review at the workflow level, but there's no **per-invocation self-review** within the agent runtime itself. Agents proceed with initial assumptions without pausing to validate mid-execution.

**Adaptation**: Phase 29 — pre-execution interrogation step

### 2.7 Effort Level Classification

**PAI Pattern**: 8-tier system (Instant → Loop) gates features by complexity:

| Tier | Budget | Features Activated |
|------|--------|--------------------|
| Instant | <10s | Minimal formatting only |
| Fast | <1min | Skip THINK phase |
| Standard | <2min | Full 7-phase loop |
| Extended | <5min | Plan Mode + Verification Rehearsal |
| Extended+ | <8min | Constraint Extraction + Build Drift Prevention |
| Deep | <15min | Full self-interrogation |
| Comprehensive | <30min | Multi-agent council review |
| Loop | Unbounded | 8 parallel workers with effort decay |

**AGENT-33 Gap**: Our autonomy budget system (Phase 18) tracks resource consumption with preflight checks (PF-01..PF-10) and runtime enforcement (EF-01..EF-08), but doesn't **adapt execution strategy based on task complexity**. Simple tasks get the same pipeline as complex ones. The infrastructure for budget-gated execution exists; what's missing is the complexity classifier driving it.

**Adaptation**: Phase 30 — Adaptive Execution Strategy

---

## 3. PAI Extensibility Architecture & Connector Patterns

### 3.1 Hook System (Event-Driven Automation)

**PAI Implementation**: 20 hooks across 6 lifecycle events, registered in settings.json:

| Event | Hooks | Behavior |
|-------|-------|----------|
| SessionStart | LoadContext | **Blocking** — injects SKILL.md + TELOS |
| UserPromptSubmit | RatingCapture, FormatReminder | Async — captures signals |
| PreToolUse | SecurityValidator | **Blocking** — validates against patterns.yaml |
| PostToolUse | AlgorithmTracker | Async — monitors phase progression |
| Stop | VoiceNotification, StopOrchestrator | Async — session finalization |
| SubagentStop | AgentOutputCapture | Async — collects delegated results |

**Key Design**: Hooks are TypeScript files with <50ms execution budget. Blocking hooks prevent progression; async hooks fire-and-forget. StopOrchestrator prevents conflicts between multiple Stop hooks.

**AGENT-33 Current State**: No formal hook system, but event patterns exist across subsystems: Phase 16 observability emits structured traces, Phase 14 security middleware intercepts requests, and the ToolLoop has a `leakage_detector: Callable` callback. These are ad-hoc interception points, not a unified lifecycle hook framework. Event handling is hardcoded in `main.py` lifespan and individual route handlers.

**Adaptation**: Phase 32 — Event Hook System (see Section 4.4)

### 3.2 Skills/Packs Distribution

**PAI Implementation**: Skills are directories with standard structure:
```
~/.claude/skills/SkillName/
├── SKILL.md           # Trigger patterns + domain knowledge
├── Workflows/         # Step-by-step procedures
├── Tools/             # CLI utilities (TypeScript)
└── EXTEND.yaml        # User customization (optional)
```

**Packs** bundle multiple skills for distribution:
- `pai-core-install` — Core PAI system
- `pai-algorithm-skill` — The Algorithm implementation
- `pai-art-skill` — Art/creative workflows
- All packs depend on `pai-core-install`

**USER/SYSTEM Separation**: System skills update without breaking user customizations. `EXTEND.yaml` overlays user preferences with `deep_merge` strategy.

**AGENT-33 Current State**: Skills use `SkillDefinition` Pydantic model loaded from filesystem. No distribution, versioning, dependency management, or user/system separation.

**Adaptation**: Phase 33 — Skill Packs & Distribution (see Section 4.5)

### 3.3 TELOS (Deep Goal Understanding)

**PAI Implementation**: 10 markdown files capture user identity and goals, injected into every session context. This transforms stateless agent interactions into goal-aligned assistants.

**AGENT-33 Analog**: Agent definitions have static `description` and `governance` fields. No mechanism for agents to understand broader tenant/project goals beyond immediate task inputs.

**Adaptation**: Phase 29 — Goal Context Injection

### 3.4 Memory System (4-Layer Learning)

**PAI Implementation**:
1. **Capture**: Full session transcripts, work artifacts, research
2. **Sentiment**: Explicit ratings + implicit sentiment analysis → `ratings.jsonl`
3. **Learning**: Pattern extraction, algorithm reflections, structured Q1-Q3 critiques
4. **State**: PRD files with ISC checkboxes, `current-work.json` metadata

**Learning Loop**: Capture → Sentiment Overlay → Extract → Mine → Upgrade → Apply

**AGENT-33 Current State**: Memory subsystem (pgvector + BM25 hybrid RAG, 4-stage skill matching, embedding cache with LRU, token-aware chunking) handles document storage and retrieval. Phase 20 (Continuous Improvement) has research intake lifecycle, lessons learned with action tracking, improvement checklists (CI-01..CI-15), and metrics tracker (IM-01..IM-05). However, these are **manually triggered** — there's no automated sentiment capture, learning extraction from execution traces, or closed feedback loop that generates steering rules from failures.

**Adaptation**: Phase 31 — Continuous Learning Loop

### 3.5 Meta-Prompting (Template Primitives)

**PAI Implementation**: 5 template primitives generate context-appropriate prompts:
1. **Roster** — Lists of available items (agents, skills, tools)
2. **Voice** — Personality and communication style
3. **Structure** — Response format templates
4. **Briefing** — Context and background injection
5. **Gate** — Conditional logic (include/exclude based on state)

Result: 65% token reduction vs. hand-crafted prompts. Single-point updates propagate system-wide.

**AGENT-33 Current State**: Agent prompts start from static `system.md`/`user.md` files but are augmented at runtime via progressive skill disclosure (L0/L1/L2 injection by SkillInjector), progressive recall (RAG-based context enrichment), and context window management (token budgets, message unwinding). What's missing is a **composable template system** — the current augmentation is code-driven, not declarable or maintainable by non-developers.

**Adaptation**: Phase 30 — Dynamic Prompt Composition

### 3.6 Context Priming Pipeline

**PAI Implementation**: Automated sequence at session/task start:
1. Check if SKILL.md needs rebuilding (timestamp comparison)
2. Load context files from settings
3. Load relationship context and active work status
4. Inject as system reminder before first user message

Budget: ≤34s total for context recovery, preventing stalls on search/read operations.

**AGENT-33 Current State**: Context management (P2) handles token budgets and message unwinding, but there's no **automated context priming** before agent invocation. Agents start cold unless the caller explicitly provides context.

**Adaptation**: Phase 30 — Agent Context Priming

### 3.7 MCP Server Integration

**PAI Implementation**: External services connect via Model Context Protocol:
```json
{
  "mcpServers": {
    "content": {"type": "http", "url": "https://content-mcp..."},
    "daemon": {"type": "http", "url": "https://mcp.daemon..."},
    "brightdata": {"command": "bunx", "args": ["-y", "@brightdata/mcp"]}
  }
}
```

This "API-fies" external systems, making them tool-accessible within agent workflows.

**AGENT-33 Current State**: MCP bridge exists (`tools/mcp_bridge.py` — MCPBridge, MCPToolAdapter, JSON-RPC/httpx transport) from P3 delivery. Channel health checks exist on all 4 messaging adapters via `health_check()` protocol. What's missing is **dynamic registration, MCP server discovery, connection pooling, and health monitoring** for MCP connections specifically.

**Adaptation**: Phase 32 — MCP Connector Registry

### 3.8 Autonomous Capability Upgrades

**PAI Pattern**: When new model capabilities are released:
1. Monitor engineering blogs and changelogs
2. Analyze new features against existing workflow gaps
3. Generate prioritized recommendations
4. Implement improvements automatically

**AGENT-33 Gap**: No mechanism for the system to discover and adapt to new capabilities (new tool types, new model features, new API patterns).

**Adaptation**: Phase 33 — Capability Discovery

---

## 4. Proposed Improvement Phases

### Phase 29: Agent Reasoning Protocol
**Category**: Runtime / Agent Intelligence
**Dependencies**: Phase 18 (Autonomy), Phase 17 (Evaluation)
**Estimated Scope**: ~80-100 tests, 6-8 new files

#### Motivation
Automated agents currently execute tasks without structured reasoning. PAI's Algorithm demonstrates that wrapping agent execution in a formalized reasoning loop (with requirement extraction, self-interrogation, and mechanical verification) dramatically reduces failure modes.

#### Deliverables

**29.1 Structured Reasoning Loop**
- `agents/reasoning.py` — ReasoningProtocol with NextAction FSM (cf. Agno 38.1K stars):
  - States: CONTINUE → VALIDATE → FINAL_ANSWER, with RESET escape for critical errors
  - 5 phases: OBSERVE, PLAN, EXECUTE, VERIFY, LEARN
- Each phase produces typed artifacts (ObservationResult, PlanResult, etc.)
- Quality gates between phases (configurable strictness per effort level)
- Anti-criteria support (conditions that must NOT be true)
- Multi-agent ISC sharing via inter-task guardrail pattern (cf. CrewAI's inter-task gates)

**29.2 ISC (Ideal State Criteria) System**
- `agents/isc.py` — ISCManager for creating/tracking binary-testable success conditions
- Return type: `GuardrailResult(success: bool, result: Any | None, error: str | None)` (cf. CrewAI 44.5K stars)
- ISC criteria as `Callable[[ExecutionTrace], bool]` functions, composable with `&` / `|` operators (cf. AutoGen's `FunctionalTermination`)
- 8-12 word constraint enforcement via heuristic (word count + pattern match), not LLM
- ISC-to-task mapping with coverage validation
- Mechanical verification (tool-call based, not prose-based)

**29.3 Constraint Extraction**
- `agents/constraints.py` — 4-scan protocol for extracting explicit/implicit constraints from task inputs
- Constraint→ISC coverage map ensuring no unmapped constraints
- Abstraction gap detection (prevents "don't do too much damage" from replacing "don't burst 15+ damage")

**29.4 Build Drift Prevention**
- ISC adherence check before each artifact creation
- Constraint checkpoint after each artifact creation
- Drift detection and automatic re-alignment
- 5-scenario StuckDetector integration into ToolLoop (cf. OpenHands 68K stars):
  1. Repeating action+observation (4 consecutive)
  2. Repeating action+error (3 consecutive)
  3. Agent monologue without observations (3 consecutive)
  4. Alternating A-B-A-B oscillation (6 steps)
  5. Context window error loop (10 consecutive condensation events)

**29.5 Self-Interrogation**
- 5 structured blind-spot questions injected at configurable points
- Pre-execution interrogation: "Am I about to build something that violates my own criteria?"
- Deterministic checks first (Aider's reflected_message pattern: lint/test/schema validation), LLM-based interrogation only for subjective criteria
- Interrogation results stored as part of execution trace

**29.6 Goal Context Injection**
- `agents/goals.py` — TenantGoalContext model
- Load tenant/project goals at agent invocation time
- Inject goal alignment check during OBSERVE phase
- Per-tenant TELOS-style goal files (MISSION, GOALS, CONSTRAINTS)

### Phase 30: Adaptive Execution & Deterministic Routing
**Category**: Runtime / Efficiency
**Dependencies**: Phase 29 (Reasoning Protocol), Phase 13 (Code Execution)
**Estimated Scope**: ~60-80 tests, 5-7 new files

#### Motivation
Not every task needs the full reasoning pipeline. PAI's effort-level system demonstrates that classifying task complexity upfront and routing to the most deterministic solution path reduces latency, cost, and failure rates.

#### Deliverables

**30.1 Effort Level Classifier**
- `agents/effort.py` — EffortClassifier with 5 tiers (Instant/Fast/Standard/Extended/Deep)
- **Heuristic-first classification** (<10ms): input token count, tool count, keyword patterns, step count
  - LLM-based classification as upgrade path once training data accumulates (cf. DAAO VAE estimator achieving 41% cost reduction)
  - This addresses the <100ms latency gate from the review requirements
- Feature gating per tier (which reasoning phases activate)
- Auto-compression: if a phase exceeds 150% budget, drop to lower tier for remaining phases
- Self-adjusting: task success at a tier lowers future difficulty estimates for similar inputs (DAAO pattern)

**30.2 Deterministic Routing Layer**
- `agents/routing.py` — DeterministicRouter
- Decision hierarchy: Code Script → CLI Tool → Simple Prompt → Full Agent
- Pattern matching against known deterministic solutions
- Fallback escalation when deterministic path fails
- Registry of deterministic solutions (code snippets, CLI pipelines, templates)

**30.3 Dynamic Prompt Composition**
- `agents/prompt_templates.py` — 5 template primitives (Roster, Voice, Structure, Briefing, Gate)
- Template registry with variable substitution
- Context-aware prompt generation (only include relevant skills/tools)
- Token budget enforcement during composition
- Single-point update propagation (change a template, all prompts update)
- `PROMPT_RENDERING` middleware hook for runtime prompt modification (cf. Semantic Kernel 27.3K stars)

**30.6 Cost-Aware Model Selection**
- Integration with ModelRouter for cost-based routing (cf. LiteLLM 36.6K stars)
- Instant/Fast tiers route to cheapest model; Extended/Deep tiers route to most capable
- Fallback with cooldowns (5s default) triggered by 429s, >50% failure rate, or non-retryable errors
- Budget integration with Phase 18 autonomy enforcement

**30.4 Agent Context Priming**
- `agents/priming.py` — ContextPrimer with time-budgeted loading
- Automated pre-invocation context assembly (≤5s budget)
- Recent execution history injection (what was tried, what failed)
- Active workflow state summary
- Tenant goal alignment context

**30.5 Adaptive Execution Strategy**
- Integration with Phase 18 autonomy budgets
- Resource allocation based on effort classification
- Timeout adjustment per tier
- Retry strategy adaptation (simple tasks: fast fail; complex: patient retry)

### Phase 31: Continuous Learning & Signal Capture
**Category**: Intelligence / Memory
**Dependencies**: Phase 29 (Reasoning), Phase 20 (Improvement), Phase 16 (Observability)
**Estimated Scope**: ~50-70 tests, 5-6 new files

#### Relationship with Phase 20 (Continuous Improvement)
Phase 20 provides the **manual** improvement lifecycle: research intake (SUBMITTED→TRIAGED→ANALYZING), lessons learned with human-driven action tracking, and improvement checklists. Phase 31 builds the **automated** layer on top: signals captured from execution traces, LLM-generated behavioral rules from failure analysis (DSPy SIMBA `append_a_rule` pattern), and a closed feedback loop that generates Phase 20 improvement proposals automatically. Phase 20 is the human-in-the-loop governance; Phase 31 is the machine-driven signal pipeline feeding it.

#### Motivation
PAI's 4-layer memory system with sentiment capture and automated learning extraction demonstrates that systems improve faster when they capture signals from every interaction and feed them back into behavior modification. AGENT-33's Phase 20 provides manual improvement governance but has no automated signal capture or closed learning loop.

#### Deliverables

**31.1 Signal Capture System**
- `learning/signals.py` — SignalCollector using Langfuse Score schema (cf. Langfuse 22.2K stars):
  - `dataType`: NUMERIC | CATEGORICAL | BOOLEAN
  - `source`: ANNOTATION (human) | API (programmatic) | EVAL (LLM-judge)
  - Links to trace via `traceId` + optional `observationId` for step-level granularity
- Explicit ratings: numeric + optional comment (e.g., "7 - good result")
- Implicit sentiment: task completion time, retry count, escalation frequency
- Signal storage in PostgreSQL with tenant isolation
- OTel-compatible span attributes (cf. GenAI Semantic Conventions: `gen_ai.agent.id`, `gen_ai.usage.input_tokens`)
- API endpoints for signal submission and querying

**31.2 Execution History Analyzer**
- `learning/analyzer.py` — ExecutionAnalyzer
- Cluster execution patterns by outcome (success, failure, partial)
- Identify recurring failure modes per agent/skill/tool combination
- Compute quality signals: `(10 - sentiment) * over_budget_factor`
- Weighted prioritization of improvement opportunities

**31.3 Learning Extraction Pipeline**
- `learning/extractor.py` — LearningExtractor using DSPy SIMBA pattern (cf. DSPy 32.3K stars):
  - `append_a_rule`: LLM generates behavioral constraints from failure analysis
  - `append_a_demo`: Extract successful examples as few-shot demonstrations
- Post-execution reflection: structured Q1-Q3 critique per task
  - Q1: What went well?
  - Q2: What went wrong?
  - Q3: What should change?
- Pattern aggregation across reflections (theme clustering via existing BM25 + vector search)
- Upgrade proposal generation (suggested skill/agent/tool modifications)
- Auto-generated Phase 20 improvement proposals from frequency x severity scoring

**31.4 Steering Rules Engine**
- `learning/steering.py` — SteeringRuleEngine
- Behavioral constraints derived from failure analysis (DSPy `append_a_rule` extraction)
- Start with CrewAI's "feedback as mandatory instructions" pattern (cf. CrewAI 44.5K stars): failed guardrail error messages injected as constraints in next attempt
- Per-agent steering rules (e.g., "agent-X should always validate input schema before processing")
- Per-tenant steering rules
- Rules injected into agent system prompt at invocation time via Phase 30 prompt composition
- Rule effectiveness tracking (did the rule reduce failures? — compare pre/post failure rates)

**31.5 Automated Improvement Proposals**
- Integration with Phase 20 research intake
- Generate improvement items from learning extraction
- Auto-triage based on frequency × severity scoring
- Track proposal→implementation→verification lifecycle

### Phase 32: Event Hook System & MCP Connector Registry
**Category**: Extensibility / Integration
**Dependencies**: Phase 12 (Tool Registry), Phase 16 (Observability)
**Estimated Scope**: ~70-90 tests, 7-9 new files

#### Motivation
PAI's hook system and MCP integration demonstrate that event-driven automation and standardized external service connectors are essential for reducing agent friction. Automated agents struggle when they can't react to lifecycle events or connect to external services without manual configuration.

#### Deliverables

**32.1 Middleware Chain Framework**
- `hooks/framework.py` — 3-tier middleware chain (cf. MS Agent Framework 7.4K stars):
  - `AgentMiddleware` — Agent invocation pre/post interception
  - `ToolMiddleware` — Tool/function call pre/post interception
  - `WorkflowMiddleware` — Workflow step pre/post interception
- Each uses `process(context, next)` pattern supporting:
  - Pre/post interception (code before and after `await next()`)
  - Result modification via `context.result`
  - Early termination via `context.terminate`
  - Cross-middleware state via `context.metadata`
- 7 event names following OpenAI SDK convention (cf. OpenAI Agents SDK 19.1K stars):
  `on_agent_start`, `on_agent_end`, `on_llm_start`, `on_llm_end`, `on_tool_start`, `on_tool_end`, `on_handoff`
- Plus `PROMPT_RENDERING` filter (cf. Semantic Kernel 27.3K stars)
- Three authoring styles: class-based, function-based, decorator-based
- Blocking vs. async execution; execution budget per hook (default 500ms, configurable)
- Hook priority ordering

**32.2 Hook Implementations**
- `hooks/builtin/` directory with initial hook set:
  - `context_loader.py` — Load agent context at invocation time
  - `security_validator.py` — Pre-tool-use security checks (integrate Phase 14)
  - `signal_collector.py` — Post-execution signal capture (integrate Phase 31)
  - `trace_emitter.py` — Observability trace emission (integrate Phase 16)
  - `drift_detector.py` — Build drift detection during workflow execution
- Custom hook registration via plugin system

**32.3 Hook Configuration**
- YAML/JSON hook definitions (event type, matcher pattern, handler, priority, blocking flag)
- Per-tenant hook configuration
- Hook enable/disable without code changes
- Hook execution logging and metrics

**32.4 MCP Connector Registry**
- `connectors/mcp_registry.py` — MCPConnectorRegistry
- Dynamic MCP server registration (HTTP, Stdio, and StreamableHTTP transports per MCP SDK 21.8K stars)
- Integration with official MCP Registry API (cf. registry 6.5K stars, API frozen v0.1) for discovery
- Semantic tool discovery via existing hybrid search (cf. MCP Gateway's `POST /api/search/semantic`)
- Health monitoring via `send_ping()` with multi-tier status: healthy/degraded/unhealthy
- Connection resumability via `EventStore` interface and `Last-Event-ID` (StreamableHTTP)
- Connection pooling and retry logic

**32.5 Connector Configuration & Management**
- `connectors/config.py` — ConnectorConfig model with `CredentialType` base class (cf. n8n 176K stars)
- Standardized OAuth2 flows, API key injection, and automatic token refresh
- CRUD API for MCP connector management
- Credential storage integration (Phase 14 vault)
- Namespace-validated publishing for tenant isolation (cf. MCP Registry `io.github.username/server-name`)
- Connector status dashboard endpoint

**32.7 Circuit Breaker Layer** *(new — greenfield, first in ecosystem)*
- `tools/circuit_breaker.py` — CircuitBreaker wrapping all tool executions (cf. PyBreaker 655 stars)
- States: CLOSED (normal) → OPEN (failing, skip tool) → HALF_OPEN (test single request)
- Configurable: `fail_max=5`, `reset_timeout=60`, per-tool overrides
- Redis-backed state for multi-instance deployments
- Integration with ToolGovernance layer
- No AI agent framework currently implements circuit breakers — first-mover opportunity

**32.8 Plugin SDK**
- `hooks/sdk.py` — PluginBase, PluginManifest, PluginLoader
- Standardized interface for third-party extensions
- Plugin lifecycle: discover → validate → install → activate → deactivate → remove
- Manifest declares: middleware hooks, tool registrations, connector registrations, config schema
- Isolation: plugins run in sandboxed context with explicit capability grants

**32.6 Built-in Connectors**
- `connectors/builtin/` directory:
  - `github.py` — GitHub API via MCP (issues, PRs, repos)
  - `filesystem.py` — Filesystem MCP for sandboxed file access
  - `database.py` — Database MCP for query execution
  - `web.py` — Web browsing/scraping MCP
- Each connector follows standard registration pattern

### Phase 33: Skill Packs, Distribution & Capability Discovery
**Category**: Extensibility / Ecosystem
**Dependencies**: Phase 32 (Hooks & Connectors), Phase 31 (Learning)
**Estimated Scope**: ~60-80 tests, 6-8 new files

#### Motivation
PAI's Packs system demonstrates that distributable, versionable skill bundles with user/system separation are essential for building an ecosystem around an agent platform. AGENT-33's current skills are filesystem-local with no distribution mechanism.

#### Deliverables

**33.1 Skill Pack Format**
- `skills/packs.py` — SkillPack model, Agent Skills standard-compatible (cf. 73.8K+ combined stars, 30+ platforms)
- Pack manifest format (YAML), extending standard with ClawHub-style runtime requirements (cf. ClawHub 2.6K stars):
  ```yaml
  name: security-scanning
  version: 2.1.0
  description: Enterprise security scanning skills
  author: agent33-team
  dependencies:
    - core-tools >= 1.0.0
  skills:
    - sarif-converter
    - vulnerability-scanner
    - compliance-checker
  hooks:
    - pre-scan-validation
  connectors:
    - semgrep-mcp
  requires:
    env: [SEMGREP_TOKEN]
    bins: [semgrep, trivy]
    os: [linux, macos, windows]
  test_input: { "target": "example_repo" }
  test_output: [["findings", "sarif_report"]]
  ```
- Cross-skill semver dependency resolution *(no platform has this — differentiation opportunity)*
- Conflict detection between packs
- Behavior analysis: declared requirements vs actual code behavior (ClawHub security pattern)

**33.2 User/System Skill Separation**
- System skills: shipped with AGENT-33, updated via releases
- User skills: tenant-specific customizations, upgrade-safe
- EXTEND.yaml overlay pattern (user preferences merged with deep_merge)
- **User overlay survival across upgrades** *(no platform has this — differentiation opportunity)*
- Migration tooling for skill format upgrades
- **Formal deprecation lifecycle**: ANNOUNCED → SUNSET → REMOVED with timeline enforcement *(no platform has this)*

**33.3 Skill Distribution**
- `skills/distribution.py` — SkillDistributor
- Pack import/export (tar.gz with manifest)
- Git-based distribution (clone pack from repository)
- OCI container option for untrusted third-party packs (cf. Docker MCP containerized distribution)
- Integrity verification (SHA-256 checksums + digital signatures)
- Per-tenant pack installation with isolation
- **Skill composition declarations**: "skill A requires skill B" dependency graph *(no platform has this)*

**33.4 Skill Versioning**
- Semantic versioning for skills and packs
- Side-by-side versions during migration periods
- Deprecation warnings and sunset dates
- Changelog tracking per version

**33.5 Capability Discovery**
- `discovery/capabilities.py` — CapabilityDiscoverer
- Scan connected MCP servers for new tools
- Monitor LLM provider catalogs for new models
- Detect new skills from pack repositories
- Generate upgrade proposals when new capabilities match existing workflow gaps
- Integration with Phase 31 learning loop (capabilities that would have prevented past failures)

**33.6 Skill Marketplace API**
- `api/routes/marketplace.py` — Browse, search, install, update packs
- Skill rating/review system (from Phase 31 signals)
- Featured/recommended packs based on tenant workflow patterns
- Security review status per pack (manual approval workflow)

---

## 5. Phase Sequencing & Dependencies

```
Phase 29 (Reasoning)
  ├── 29.1-29.2 (core) ──→ Phase 30 (Routing) ──┐
  │                                                ├──→ Phase 32 (Hooks & Connectors)
  └── 29.1-29.2 (core) ──→ Phase 31 (Learning) ──┘           │
                                                          Phase 33
                                                     (Packs & Distribution)
```

### Dependency Chain (Revised — Reduces Phase 29 Bottleneck)
1. **Phase 29** (Agent Reasoning Protocol) — **stage the deliverables**: 29.1 (reasoning loop) and 29.2 (ISC system) are P0 and must complete first. Deliverables 29.3-29.6 can continue in parallel with Phases 30/31.
2. **Phase 30** (Adaptive Execution) — depends on 29.1-29.2 only (reasoning primitives for effort classification). Can start once core reasoning ships.
3. **Phase 31** (Continuous Learning) — depends on 29.1-29.2 only (structured reflection artifacts). Can start **in parallel** with Phase 30.
4. **Phase 32** (Hooks & Connectors) — depends on Phase 30 (context priming hooks) and Phase 31 (signal collection hooks). Note: the middleware framework (32.1) and circuit breakers (32.7) have no upstream dependencies and can start early as independent work.
5. **Phase 33** (Packs & Distribution) — depends on Phase 32 for plugin SDK and connector packaging

### Estimated Implementation Effort
| Phase | New Files | New Tests | New Endpoints | Sessions | Notes |
|-------|-----------|-----------|---------------|----------|-------|
| 29 | 6-8 | 80-100 | 4-6 | 2-3 | Stage 29.1-29.2 as P0 to unblock 30/31 |
| 30 | 6-8 | 70-90 | 4-6 | 2-3 | +cost-aware routing (30.6) |
| 31 | 5-6 | 50-70 | 4-6 | 2 | Leverage existing Phase 16/20 infra |
| 32 | 9-12 | 90-110 | 8-10 | 3-4 | +circuit breakers (32.7) + plugin SDK (32.8) |
| 33 | 7-9 | 70-90 | 6-8 | 2-3 | +4 differentiation features |
| **Total** | **33-43** | **360-460** | **26-36** | **11-16** | |

### Parallelization Opportunities
- Phase 30 and Phase 31 can proceed in parallel once 29.1-29.2 ship
- Phase 32.1 (middleware framework) and 32.7 (circuit breakers) can start as independent work before 30/31 complete
- Estimated critical path: 29 → 30/31 (parallel) → 32 → 33 = **8-12 sessions** (down from 10-14 serial)

---

## 6. What NOT to Adopt from PAI

PAI is optimized for **personal use** — a single user with a single assistant. Several patterns don't translate to AGENT-33's enterprise multi-tenant architecture:

| PAI Pattern | Why Not for AGENT-33 |
|-------------|---------------------|
| TELOS identity files | Too personal; AGENT-33 uses tenant/project-level goals instead |
| Voice/personality system | Entertainment feature; enterprise agents need consistency, not personality |
| ElevenLabs TTS | Non-essential; would add cost and latency |
| Single SKILL.md file | AGENT-33 uses proper database-backed skill registry |
| ~/.claude/ filesystem | AGENT-33 uses PostgreSQL + pgvector for multi-tenant isolation |
| CLI-first interface | AGENT-33 already has REST API + frontend (Phase 22) |
| Session-based memory | AGENT-33 has persistent pgvector memory with hybrid RAG |
| Manual hook configuration | AGENT-33 should use database-driven hook configuration |
| Complete release distribution | AGENT-33 uses Docker + standard deployment patterns |

---

## 7. Priority Classification

### P0 — Critical for Agent Effectiveness
- **29.1** Structured Reasoning Loop (Agno NextAction FSM) — single biggest impact on agent task completion quality
- **29.2** ISC System (CrewAI GuardrailResult interface) — prevents agents from claiming success without verification
- **30.2** Deterministic Routing — reduces failures by routing simple tasks away from LLM
- **32.1** Middleware Chain Framework (MS Agent Framework pattern) — enables all cross-cutting concerns without hardcoding

### P1 — High Impact for Extensibility
- **32.4** MCP Connector Registry (official MCP Registry integration) — enables dynamic service integration
- **32.7** Circuit Breaker Layer (first in ecosystem) — prevents cascading tool failures
- **33.1** Skill Pack Format (Agent Skills standard-compatible) — enables ecosystem growth
- **31.1** Signal Capture (Langfuse Score schema) — enables data-driven improvement
- **30.3** Dynamic Prompt Composition — reduces token waste and maintenance burden

### P2 — Medium Impact, Strategic Value
- **29.3** Constraint Extraction — prevents abstraction gap in complex tasks
- **29.4** Build Drift Prevention (OpenHands 5-scenario StuckDetector) — detects stuck agents early
- **30.1** Effort Level Classifier (heuristic-first, DAAO upgrade path) — optimizes resource allocation
- **30.6** Cost-Aware Model Selection (LiteLLM routing) — reduces inference costs
- **31.3** Learning Extraction Pipeline (DSPy SIMBA `append_a_rule`) — automates system improvement
- **33.5** Capability Discovery — future-proofs against new services

### P3 — Lower Priority, Ecosystem Building
- **29.5** Self-Interrogation — nice-to-have quality improvement
- **32.8** Plugin SDK — enables third-party extensions (requires 32.1 maturity)
- **33.6** Skill Marketplace API — requires ecosystem maturity
- **31.4** Steering Rules Engine — requires learning data accumulation
- **33.2** User Overlay Survival + Deprecation Lifecycle (differentiation features)

---

## 8. Key Architectural Decisions

### Decision 1: Hook System as Extension Point
All cross-cutting concerns (security, observability, learning, context loading) should flow through hooks rather than being hardcoded in route handlers or agent runtime. This makes the system extensible without modifying core code.

### Decision 2: ISC as First-Class Citizen
Binary-testable success criteria should be a required artifact of every agent task, not optional. This eliminates the "claim success in prose" failure mode that PAI identified as its #1 quality problem.

### Decision 3: Deterministic-First Resolution
The system should always attempt deterministic solutions before invoking LLM reasoning. This reduces cost, latency, and failure rates for tasks with known solutions.

### Decision 4: Closed Learning Loop
Every execution should capture signals, extract learnings, and feed them back into system behavior. This creates compounding returns on the installed base of executions.

### Decision 5: Pack-Based Distribution
Skills, hooks, and connectors should be distributable as versioned packs with dependency resolution. This enables ecosystem growth without monolithic releases.

---

## 9. Convergence Evidence

PAI's documentation notes: "Multiple independent systems (PAI, Claude Code, OpenCode, MoltBot) are converging on identical patterns." The convergent patterns are:

1. **Structured reasoning loops** (PAI Algorithm, Claude Code plan mode, OpenCode cycles)
2. **Event-driven hooks** (PAI hooks, Claude Code hooks, GitHub Actions)
3. **Skill-based modularity** (PAI skills, Claude Code skills, MCP tools)
4. **Signal capture + learning** (PAI ratings, A/B testing, feedback loops)
5. **Deterministic-first routing** (PAI hierarchy, function calling, tool use)

AGENT-33 should ride this convergence wave — these are not arbitrary design choices but **emergent consensus** on how AI agent infrastructure should work.

---

## References

### PAI Sources
- [Building a Personal AI Infrastructure (PAI)](https://danielmiessler.com/blog/personal-ai-infrastructure) — Daniel Miessler
- [PAI December 2025 Version](https://danielmiessler.com/blog/personal-ai-infrastructure-december-2025)
- [PAI GitHub Repository](https://github.com/danielmiessler/Personal_AI_Infrastructure)
- [PAI Core Architecture — DeepWiki](https://deepwiki.com/danielmiessler/Personal_AI_Infrastructure/3-core-architecture)
- [Pioneering PAI — Cognitive Revolution](https://www.cognitiverevolution.ai/pioneering-pai-how-daniel-miessler-s-personal-ai-infrastructure-activates-human-agency-creativity/)

### Landscape Research (30+ repos surveyed)
- [Landscape Amplification Analysis](./landscape-amplification-analysis.md) — Full survey with cross-framework comparison matrices
- [Hooks/MCP Plugin Architecture Research](./hooks-mcp-plugin-architecture-research.md) — Deep dive on middleware patterns

### Key Framework References (by pattern)
- **Reasoning**: [Agno](https://github.com/agno-agi/agno) (38.1K), [OpenHands](https://github.com/All-Hands-AI/OpenHands) (68K), [CrewAI](https://github.com/crewAIInc/crewAI) (44.5K), [AutoGen](https://github.com/microsoft/autogen) (54.7K)
- **Hooks**: [MS Agent Framework](https://github.com/microsoft/agents) (7.4K), [OpenAI SDK](https://github.com/openai/openai-agents-python) (19.1K), [Semantic Kernel](https://github.com/microsoft/semantic-kernel) (27.3K)
- **Learning**: [Langfuse](https://github.com/langfuse/langfuse) (22.2K), [DSPy](https://github.com/stanfordnlp/dspy) (32.3K), [LiteLLM](https://github.com/BerriAI/litellm) (36.6K)
- **Distribution**: [Agent Skills](https://github.com/agentskills/agentskills) (10.7K), [ClawHub](https://github.com/openclaw/clawhub) (2.6K), [Composio](https://github.com/ComposioHQ/composio) (27.1K)

### AGENT-33 Internal
- [SkillsBench Analysis](./skillsbench-analysis.md)
- [ZeroClaw Feature Parity Analysis](./zeroclaw-feature-parity-analysis.md)
- [Agent World Model Analysis](./agent-world-model-analysis.md)
