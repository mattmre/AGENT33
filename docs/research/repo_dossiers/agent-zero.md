# Repo Dossier: agent0ai/agent-zero
**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

Agent-Zero (14.5k stars, last updated 2026-02-14) is a prompt-driven autonomous agent framework emphasizing organic growth and transparent customization. Unlike task-specific frameworks, it treats the operating system itself as the primary tool—agents dynamically write code and terminal commands rather than invoking pre-built functions. It features hierarchical multi-agent cooperation (superior/subordinate chains), persistent FAISS-backed vector memory with LLM-driven consolidation, a modular skills system using the SKILL.md standard, and real-time WebSocket infrastructure for streaming UI updates. The entire agent behavior is defined through 102+ modular markdown prompt files rather than hardcoded logic, enabling full prompt-level customization. Built in Python with Docker containerization, it supports OpenAI, Anthropic, and local models via LiteLLM, includes speech capabilities, and runs multi-runtime code execution (Python/IPython, Node.js, shell, SSH, Docker) with layered timeout protection.

## 2) Core orchestration model

**Prompt-as-behavior architecture:** All agent behavior is defined in markdown prompt files in `prompts/default/`. The system uses 102+ prompts organized by scope (`agent.system.*`, `memory.*`, `fw.*`) and dynamically composed based on context. Unlike hardcoded decision trees, the LLM receives assembled prompts that define role, behavior, tool usage, and memory integration. This makes Agent-Zero fundamentally a "prompt-driven" rather than "code-driven" framework.

**Hierarchical subordinate spawning:** Every agent has a superior that assigns tasks. Users are the top-level supervisors. Agents spawn subordinates via `call_subordinate.py` tool to handle subtasks with focused contexts. Subordinates report results back up the chain. Agent definitions support three-tier origin hierarchy (Default → User → Project) where later tiers override predecessors while accumulating prompts, enabling specialized sub-agents to inherit base behavior with custom extensions.

**Tool-as-code execution:** Agents don't have fixed tool libraries. Instead, the `code_execution_tool.py` provides multi-runtime execution (Python/IPython, Node.js, shell, SSH, Docker) with session management via `ShellWrap` dataclass. Agents write code/commands on-the-fly to accomplish tasks. Sessions persist across calls with state preservation. This mirrors AGENT-33's Phase 13 code execution layer but goes further—execution is the *primary* interaction model, not a supplementary capability.

**LLM streaming loop:** `agent.py` implements the core message loop. The `Agent` class processes messages through:
1. `_prepare_messages()` assembles system prompts + conversation history
2. `call_llm()` invokes model with streaming via LangChain `astream()`
3. Tool calls extracted from LLM responses trigger `Tool.execute()`
4. Results feed back into history for next iteration
5. Loop continues until task completion or user intervention

**Multi-agent state isolation:** `AgentContext` manages execution contexts with lifecycle tracking (creation/retrieval/removal), pause status, task tracking, message communication, logging, and notifications. The `AgentContextType` enum distinguishes USER, TASK, and BACKGROUND contexts, enabling concurrent agent operations with isolated state.

## 3) Tooling and execution

**Dynamic tool discovery:** 23 tools in `python/tools/` are dynamically loaded. Tools inherit from base `Tool` class defining `execute()` abstract method. No static registry—tools are referenced by name in prompts, and the agent runtime resolves them. Tools include: `code_execution_tool`, `memory_save`/`load`/`delete`/`forget`, `call_subordinate`, `browser_*` (open/do/agent), `knowledge_tool`, `skills_tool`, `document_query`, `scheduler`, `search_engine`, `a2a_chat` (agent-to-agent), `notify_user`, `response`, `wait`, `vision_load`, `behaviour_adjustment`, `input`, `unknown`.

**Code execution safety mechanisms:**
- **Layered timeouts:** first_output (30s/90s), between_output (15s/45s), max_exec (180s/300s), dialog (5s)
- **Prompt detection:** Regex patterns identify shell readiness (venv prompts, SSH patterns, PowerShell) and interactive dialogs (Y/N, yes/no, colons, question marks)
- **Session isolation:** Each runtime session (local, SSH) tracked independently with running/idle status
- **Output sanitization:** Escape sequence removal, 1MB truncation threshold, line-by-line streaming
- **Error recovery:** Automatic reconnection retry on lost connections (single retry before propagation)
- **State reset:** "always reset state when ssh_enabled changes" for configuration consistency

Contrast with AGENT-33: AGENT-33's `CodeExecutor` in Phase 13 has IV-01..05 validation rules, progressive disclosure (L0-L3), and `SandboxConfig` with resource limits. Agent-Zero relies on timeout-based containment without input validation schema or disclosure levels—safety is enforcement-based (timeouts, output limits) rather than contract-based (validation rules, capability levels).

**Skills system (SKILL.md standard):** Skills are reusable capability modules defined by `SKILL.md` files with YAML frontmatter + markdown body. Data model captures: name, description, path, version, author, license, tags, compatibility, allowed tools, activation triggers, and markdown content. Discovery scans hierarchical skill roots (agent-specific → project → user → system) with priority-based resolution. Operations: `list_skills()` (deduplication by normalized name), `find_skill()` (name matching), `load_skill_for_agent()` (format with metadata + file tree), `search_skills()` (full-text with term scoring), `validate_skill()` (naming conventions: lowercase/numbers/hyphens, 1-64 chars). Two-stage frontmatter parser (PyYAML primary, regex fallback) ensures robustness. This is the same SKILL.md standard referenced in AGENT-33's CLAUDE.md for Claude Code compatibility.

**Browser automation:** Multiple browser tools: `browser.py` (core functionality), `browser_agent.py` (autonomous navigation), `browser_do.py` (execute actions), `browser_open.py` (launch/manage instances). Uses Playwright integration (`playwright.py` helper). AGENT-33 has a `BrowserTool` in Phase 12 tool registry but lacks autonomous navigation—Agent-Zero's browser_agent enables full self-directed web workflows.

## 4) Observability and evaluation

**Structured logging with state broadcasting:** `Log` class manages `LogItem` instances with threadsafe operations (`threading.RLock()`). Each log entry captures: type, heading, content, key-value pairs, timestamp, `agentno` (agent ID), automatic truncation (15k chars for content, 250k for responses), recursive secret masking via `_mask_recursive()`. State change broadcasting triggers lazy-loaded notification functions updating "both the active chat stream (sid-bound) and the global chats list (context metadata like last_message/log_version)" for multi-tab UI synchronization. Log items serialize to standard dict format (number, ID, type, timestamp, agent number) enabling execution flow tracing across distributed components.

**WebSocket real-time streaming:** `websocket_manager.py` handles real-time UI updates. Agent execution streams progress updates, tool calls, and results via WebSocket to web UI. The test suite includes 18+ WebSocket-specific tests covering CSRF protection, namespace isolation, multi-tab synchronization, and state sync handlers. This enables live intervention—users can pause, redirect, or stop agents mid-execution.

**Tool execution tracking:** Base `Tool` class implements three phases: before (displays name/args, creates log), execute (abstract, returns `Response`), after (sanitizes text, adds to history, prints result, updates log). Progress tracked via `set_progress()`/`add_progress()` methods. `get_log_object()` constructs log entries with contextual information. This provides granular visibility into tool invocation chains.

**Testing approach:** 28 test files focus heavily on WebSocket infrastructure, state management, and security (CSRF, namespace isolation). Tests include: `test_multi_tab_isolation.py`, `test_state_monitor.py`, `test_state_sync_handler.py`, `test_websocket_namespace_security.py`, `test_http_auth_csrf.py`, `test_persist_chat_log_ids.py`. Also covers: rate limiter, file tree visualization, email/chunk parsing, snapshot schema validation, developer settings. Emphasis on real-time communication correctness rather than unit tests of agent logic—reflects the prompt-driven nature (hard to unit test LLM behavior, easier to integration test infrastructure).

**No formal evaluation gates:** Unlike AGENT-33's planned Phase 17 (evaluation gates with pass/fail criteria), Agent-Zero has no automated quality checks on agent outputs. Evaluation is implicit through user feedback and memory consolidation. The `memory_consolidation.py` system learns from interaction patterns but doesn't enforce quality thresholds before task completion.

## 5) Extensibility

**Extension system:** `python/extensions/` directory (specific files not fetched, but referenced in agent initialization). Extensions hook into agent lifecycle: initialization, message processing, tool execution, memory operations. Fully customizable system prompts, tools, and behaviors through configuration files rather than code changes. The `AgentConfig` dataclass supports runtime configuration via CLI arguments, settings files, and environment variables with dynamic type conversion.

**Model provider flexibility:** Supports OpenAI, Anthropic, local models, and numerous providers via LiteLLM integration. `ModelConfig` dataclass defines: type (chat/embedding), provider, name, api_base, ctx_length, rate limits (requests/input/output), vision flag, custom kwargs. Factory functions `get_chat_model()` and `get_embedding_model()` instantiate wrappers with merged provider defaults and environment-based API credentials. Four model types configured: chat (primary with vision), utility (auxiliary tasks), embedding (vectors), browser (web interaction with vision).

**Multi-environment execution:** Supports local, SSH remote, and Docker container execution. `shell_local.py`, `shell_ssh.py`, and `docker.py` helpers abstract environment differences. Docker containerization (`DockerfileLocal`) enables isolated agent operation. The `tunnel_manager.py` helper provides network tunneling capabilities.

**84 helper modules:** Extensive helper library covering API/communication (websocket, message_queue), browser/web (playwright, duckduckgo_search, perplexity_search, searxng), file/data management (files, backup, history, vector_db, faiss_monkey_patch), development/execution (shell_local/ssh, docker, process, git), AI/LLM (call_llm, tokens, memory, memory_consolidation), security/config (crypto, secrets, security, dotenv, settings, login), utilities (log, print_style, strings, errors, wait, defer, update_check), and specialized features (email_client, whisper, kokoro_tts, notification, skills, subagents).

**Three-tier configuration overlay:** Agent definitions support Default → User → Project origins. `load_agent_data()` merges configurations with later origins overriding predecessors while preserving prompts from all levels. `get_paths()` searches resources in priority order (project profiles → user profiles → default profiles). `get_available_agents_dict()` filters agents based on project settings for dynamic enable/disable. This enables flexible agent composition where specialized sub-agents inherit from defaults while allowing project-level customization.

## 6) Notable practices worth adopting in AGENT-33

**1) Prompt-driven governance injection:** AGENT-33's governance layer exists in code (`GovernanceConstraints` in `definition.py`) but never reaches the LLM—`_build_system_prompt()` in `runtime.py:29-63` ignores `AgentDefinition.prompts.system` template paths. Agent-Zero demonstrates the correct pattern: all behavioral constraints, safety rules, tool allowlists, and capability boundaries live in *prompt files* that are actually composed into the system message. AGENT-33 should:
   - Move governance constraints from `GovernanceConstraints` model into `prompts/governance/{role}.md` templates
   - Modify `_build_system_prompt()` to load and inject these templates
   - Include capability taxonomy allowlist in system prompt: "You are authorized to use capabilities: [P01, I02, V03, ...]"
   - Add safety guardrails to every agent's system prompt (currently zero agents have safety rules)

**2) LLM-driven memory consolidation:** Agent-Zero's `memory_consolidation.py` uses the utility LLM to "Extract search keywords/queries from new memory" for semantic relationship discovery, then applies five consolidation actions (MERGE, REPLACE, UPDATE, KEEP_SEPARATE, SKIP) with 0.9 similarity threshold for safety. AGENT-33's memory system (`memory/`) has short-term buffer, pgvector long-term store, and embeddings, but no consolidation—memory grows indefinitely. Adopt Agent-Zero's pattern:
   - Add `memory_consolidation.py` that queries similar memories on new insertions
   - Use LLM to analyze relationships and decide consolidation action
   - Implement safety threshold (0.9+) for REPLACE to prevent degradation
   - Merge metadata (source, priority, tags) across consolidations
   - Validate memories still exist before processing (race condition handling)

**3) Hierarchical prompt composition:** Agent-Zero's three-tier origin system (Default → User → Project) allows specialized agents to *accumulate* prompts from all levels while overriding config. AGENT-33's `AgentDefinition` has flat JSON files with no inheritance. Implement:
   - Add `base_agent` field to agent definitions for inheritance
   - Load base agent definition and merge with current
   - Accumulate `prompts.system` from base + current (don't replace)
   - Override other fields (model, capabilities, tools) but preserve prompt hierarchy
   - Enable project-specific agent customization without duplicating base definitions

**4) Tool execution progress streaming:** Agent-Zero's `Tool` base class has `set_progress()`/`add_progress()` that update logs during execution, enabling real-time UI feedback. AGENT-33's tool framework (`tools/`) lacks progress tracking—tools are black boxes until completion. Add:
   - `progress: str` field to tool base class
   - `set_progress(status: str)` method that emits events
   - Hook progress events into observability layer (structlog + tracing)
   - Display progress in dashboard real-time view
   - Particularly valuable for long-running tools (web_fetch, shell commands)

**5) Skills as portable capabilities (SKILL.md standard):** Agent-Zero's skills system enables reusable, versioned, documented capabilities with discovery, validation, and hierarchical loading. AGENT-33 has workflow actions but no portable skill format. Adopt SKILL.md:
   - Define `skills/` directory with SKILL.md files (YAML frontmatter + markdown body)
   - Implement skill discovery scanning hierarchical roots (system → user → project → agent)
   - Add `skills_tool` that loads skills dynamically based on task requirements
   - Support allowed_tools, activation_triggers in frontmatter for governance
   - Enable skill search/validation for quality control
   - Compatible with Claude Code's SKILL.md standard (cross-platform portability)

**6) Multi-runtime code execution with session persistence:** Agent-Zero's `code_execution_tool.py` manages independent sessions per runtime (Python/IPython, Node.js, shell, SSH, Docker) via `ShellWrap` dataclass with running/idle status. Sessions persist across calls preserving environment state (installed packages, defined variables, working directory). AGENT-33's `CodeExecutor` creates fresh subprocess per execution—no state preservation. Enhance:
   - Add session management layer to `execution/executor.py`
   - Maintain `sessions: dict[str, ExecutionSession]` keyed by (runtime, session_id)
   - Implement session lifecycle (create, reuse, reset, destroy)
   - Preserve environment across calls within session
   - Add session_id parameter to `ExecutionContract`
   - Particularly valuable for iterative development workflows (install deps once, run multiple times)

**7) Recursive secret masking in logs:** Agent-Zero's `_mask_recursive()` traverses nested objects (dicts, lists, strings) to redact sensitive values from logs using centralized secrets manager. AGENT-33's observability layer (`observability/`) logs payloads without sanitization—API keys, tokens, credentials could leak. Implement:
   - Add `security/secrets_manager.py` with `is_sensitive(key: str) -> bool`
   - Implement `mask_recursive(obj: Any) -> Any` that deep-clones and redacts
   - Hook into structlog processor pipeline before persistence
   - Apply to tool arguments, LLM responses, workflow state, execution results
   - Define sensitive key patterns (api_key, token, password, secret, credential)

**8) Real-time WebSocket state sync with multi-tab support:** Agent-Zero broadcasts state changes to "both the active chat stream (sid-bound) and the global chats list" enabling multi-tab synchronization. AGENT-33's FastAPI app has REST endpoints only—dashboard polls for updates. Add:
   - WebSocket endpoint `/ws/state` for real-time agent state
   - Broadcast state changes (workflow steps, tool calls, agent invocations) to all connected clients
   - Implement namespace isolation for security (users only see their tenants' state)
   - Enable live intervention (pause/resume/cancel via WebSocket)
   - Test multi-tab isolation (Agent-Zero has `test_multi_tab_isolation.py`)

## 7) Risks / limitations to account for

**1) No input validation schema (execution safety gap):** Agent-Zero's code execution relies entirely on timeout-based containment—no validation of command structure, argument types, or capability authorization before execution. An agent can attempt *any* command; safety is enforced by killing it after timeout. AGENT-33's Phase 13 has IV-01..05 validation rules (command structure, sandbox requirements, capability verification, argument types, resource limits) that prevent dangerous commands from executing. Agent-Zero's approach trades safety for flexibility—faster to deploy but higher risk of destructive actions. Mitigation: If adopting Agent-Zero's code-as-tool pattern, *keep* AGENT-33's input validation layer. Validate before execute, not just timeout during.

**2) Prompt injection vulnerability (no isolation between system/user content):** Agent-Zero's entire behavior is prompt-driven with no hardcoded safety guardrails. The 102 prompt files define behavior, but there's no mention of prompt injection defenses in `security.py` (which only implements safe filename generation). An attacker can craft user messages that override system instructions via delimiter injection, role confusion, or context manipulation. AGENT-33 has `security/prompt_injection.py` with detection patterns and allowlists. Agent-Zero assumes trusted users; AGENT-33 must assume adversarial input. Mitigation: Do NOT adopt prompt-driven architecture without also implementing AGENT-33's Phase 14 prompt injection defenses. Treat all user input as untrusted.

**3) Unlimited autonomous loops (runaway agent risk):** Agent-Zero's message loop continues "until task completion or user intervention." There's no max iteration count, no cost budget, no automatic circuit breaker. The rate limiter (`rate_limiter.py`) throttles LLM calls but doesn't prevent infinite loops of cheap operations (memory queries, local commands). An agent stuck in a reasoning loop could consume resources indefinitely. AGENT-33's workflow engine has step timeout/retries but no per-workflow iteration cap either. Mitigation: Add max_iterations limit to agent message loop. Exponential backoff on repeated identical tool calls. Cost budget per task.

**4) No evaluation gates or quality assurance:** Agent-Zero's outputs go directly to users/downstream agents with no automated quality checks. The memory consolidation system *learns* from all interactions, including failures—bad consolidations degrade memory quality. AGENT-33's planned Phase 17 has evaluation gates with pass/fail criteria before accepting agent outputs. Agent-Zero's approach enables fast iteration but accumulates technical debt in memory. Mitigation: If adopting memory consolidation, implement quality gates: validate consolidated memories against schema, check for contradictions, require human approval for REPLACE actions above criticality threshold.

**5) FAISS-only vector search (no hybrid retrieval):** Agent-Zero uses FAISS with IndexFlatIP (inner product) and cosine normalization. No BM25 lexical search, no reranking, no query rewriting—same first-gen RAG limitations as AGENT-33. The `memory.py` implementation has `similarity_search_with_score()` with threshold filtering but single-pass retrieval. For specialized knowledge (code snippets, command syntax), pure semantic search misses exact keyword matches. Mitigation: Same as AGENT-33's research finding—add hybrid retrieval (BM25 + vector), reranker, query expansion.

**6) Secret masking is reactive, not proactive (secrets can reach logs before masking):** Agent-Zero's `_mask_recursive()` sanitizes logs *after* object construction. If a secret is logged before the log item is serialized, it exists in memory unmasked. The secrets manager is "centralized" but there's no mention of environment variable scanning or runtime secret detection. AGENT-33's `security/vault.py` manages secrets proactively. Mitigation: Implement secret detection at ingestion (environment variables, config files) and mark sensitive values *before* they enter workflow/execution context. Use sealed objects that redact on access, not just serialization.

**7) No structured workflow DAGs (only conversational task decomposition):** Agent-Zero's orchestration is entirely LLM-driven via subordinate spawning and tool chaining. There's no DAG-based workflow engine, no predefined action sequences, no parallel task groups—agents decide next steps conversationally. This is flexible but non-deterministic; the same task may execute differently each time. AGENT-33's workflow engine (`workflows/`) has topological sort, step executor, conditional/parallel_group actions, checkpoint persistence—deterministic, testable, auditable. Trade-off: Agent-Zero's approach is more adaptive but less governable. Mitigation: For regulated/audited workflows, *don't* replace AGENT-33's DAG engine with conversational routing. Use Agent-Zero's pattern for exploratory tasks only.

**8) Tool discovery is prompt-based (no runtime governance enforcement):** Agent-Zero's 23 tools are referenced by name in prompts. The agent runtime resolves them dynamically with no allowlist enforcement—if an agent hallucinates a tool name, it fails at runtime. AGENT-33's Phase 12 has `ToolRegistry` with governance/allowlist enforcement, capability-based authorization, and validation before execution. Agent-Zero relies on prompt quality ("only use these tools: [...]") rather than code enforcement. Mitigation: If adopting dynamic tool discovery, add runtime allowlist check in tool resolver. Reject disallowed tools even if prompted.

## 8) Feature extraction (for master matrix)

| Feature Category | Agent-Zero Capabilities | AGENT-33 Parity | Notes |
|---|---|---|---|
| **Orchestration** | Prompt-driven behavior (102 prompts), hierarchical subordinate spawning (3-tier origin), LLM streaming loop, multi-agent state isolation (AgentContext) | Partial | AGENT-33 has DAG workflows + 6 JSON agent defs; lacks prompt-driven governance injection and hierarchical prompt composition |
| **Memory** | FAISS vector store, LLM-driven consolidation (5 actions: MERGE/REPLACE/UPDATE/KEEP_SEPARATE/SKIP), 0.9 similarity threshold, metadata preservation, race condition handling | Partial | AGENT-33 has pgvector + short-term buffer; lacks consolidation, both are first-gen RAG (no BM25/reranking) |
| **Execution** | Multi-runtime (Python/IPython/Node.js/shell/SSH/Docker), session persistence (ShellWrap), layered timeouts (first_output/between_output/max_exec), prompt detection, output sanitization, error recovery | Partial | AGENT-33 has CodeExecutor with IV-01..05 validation + progressive disclosure; lacks session persistence and multi-runtime |
| **Tools** | 23 dynamic tools (code_execution, memory, browser_*, skills, subordinate, scheduler, search, a2a_chat), base Tool class with progress tracking, no static registry | Different | AGENT-33 has ToolRegistry with governance/allowlist enforcement; lacks progress tracking and dynamic discovery |
| **Skills** | SKILL.md standard (YAML frontmatter + markdown), hierarchical discovery (agent→project→user→system), search/validate, two-stage parser (PyYAML + regex fallback) | None | AGENT-33 has workflow actions but no portable skill format; high-value adoption target |
| **Browser** | Playwright integration, autonomous browser_agent, browser_do (actions), browser_open (management), vision support | Partial | AGENT-33 has BrowserTool in Phase 12; lacks autonomous navigation |
| **Security** | Timeout-based execution containment, safe filename generation (reserved names/unicode normalization), recursive secret masking in logs, WebSocket CSRF/namespace isolation | Partial | AGENT-33 has prompt injection detection, JWT/API-key auth, governance constraints (not in prompts); Agent-Zero lacks input validation schema |
| **Observability** | Threadsafe Log/LogItem with state broadcasting, WebSocket real-time streaming, tool execution tracking (before/execute/after), 18+ WebSocket tests | Partial | AGENT-33 has structlog + tracing + lineage; lacks real-time WebSocket state sync and multi-tab support |
| **Evaluation** | None (implicit via user feedback + memory consolidation) | Planned | AGENT-33 Phase 17 has evaluation gates; Agent-Zero has no quality assurance |
| **Extensibility** | Extension hooks (lifecycle/message/tool/memory), 84 helper modules, multi-provider LLM (LiteLLM), 3-tier config overlay (Default→User→Project), Docker containerization | Comparable | Both highly extensible; Agent-Zero's helper library more comprehensive |
| **RAG** | FAISS IndexFlatIP, cosine normalization, threshold filtering, single-pass retrieval | Equivalent | Both first-gen; need BM25 + reranking |
| **Self-improvement** | LLM-driven memory consolidation with safety threshold, metadata merging, similar memory querying | Different | AGENT-33 has training loop (rollout capture, evaluation, optimization, scheduling); Agent-Zero's is memory-focused, AGENT-33's is behavior-focused |
| **Governance** | Prompt-defined (tool allowlists, behavioral constraints in prompts), no runtime enforcement beyond timeouts | Partial | AGENT-33 has code-based governance (GovernanceConstraints, tool allowlist enforcement) but doesn't inject into prompts |
| **Testing** | 28 tests (WebSocket/state management/security focus), integration-heavy, infrastructure validation | Different | AGENT-33 has 197 tests (unit-heavy, route/component focus); Agent-Zero tests infrastructure, AGENT-33 tests logic |

**Summary:** Agent-Zero excels at prompt-driven flexibility, persistent code execution sessions, LLM-based memory consolidation, and real-time WebSocket observability. AGENT-33 excels at input validation, governance enforcement, DAG workflows, and comprehensive test coverage. Highest-value integrations: (1) prompt-driven governance injection, (2) memory consolidation, (3) skills system (SKILL.md), (4) session persistence, (5) progress tracking, (6) WebSocket state sync. Critical risks: (1) no input validation, (2) prompt injection vulnerability, (3) no quality gates.

## 9) Evidence links

**Repository & Statistics:**
- GitHub: https://github.com/agent0ai/agent-zero
- Stars: 14,458 | Forks: 2,963 | Last updated: 2026-02-14
- Primary language: Python | License: Other | Topics: agent, ai, assistant, autonomous, linux, zero

**Core Implementation Files:**
- Agent runtime: https://github.com/agent0ai/agent-zero/blob/main/agent.py
- Initialization: https://github.com/agent0ai/agent-zero/blob/main/initialize.py
- Model config: https://github.com/agent0ai/agent-zero/blob/main/models.py

**Key Subsystems:**
- Tools directory (23 tools): https://github.com/agent0ai/agent-zero/tree/main/python/tools
- Code execution: https://github.com/agent0ai/agent-zero/blob/main/python/tools/code_execution_tool.py
- Memory save: https://github.com/agent0ai/agent-zero/blob/main/python/tools/memory_save.py
- Prompts (102 files): https://github.com/agent0ai/agent-zero/tree/main/prompts

**Helpers (84 modules):**
- Helper directory: https://github.com/agent0ai/agent-zero/tree/main/python/helpers
- Memory system: https://github.com/agent0ai/agent-zero/blob/main/python/helpers/memory.py
- Memory consolidation: https://github.com/agent0ai/agent-zero/blob/main/python/helpers/memory_consolidation.py
- Skills: https://github.com/agent0ai/agent-zero/blob/main/python/helpers/skills.py
- Subordinate agents: https://github.com/agent0ai/agent-zero/blob/main/python/helpers/subagents.py
- LLM calling: https://github.com/agent0ai/agent-zero/blob/main/python/helpers/call_llm.py
- Tool base class: https://github.com/agent0ai/agent-zero/blob/main/python/helpers/tool.py
- Rate limiter: https://github.com/agent0ai/agent-zero/blob/main/python/helpers/rate_limiter.py
- Security: https://github.com/agent0ai/agent-zero/blob/main/python/helpers/security.py
- Logging: https://github.com/agent0ai/agent-zero/blob/main/python/helpers/log.py

**Testing:**
- Test directory (28 files): https://github.com/agent0ai/agent-zero/tree/main/tests

**Documentation:**
- README: https://github.com/agent0ai/agent-zero/blob/main/README.md
