# Repo Dossier: parcadei/Continuous-Claude-v3
**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

Continuous-Claude-v3 is a persistent multi-agent development environment built on Claude Code that solves the context compaction problem through its "compound, don't compact" philosophy. Rather than losing nuanced understanding when context fills up, the system extracts learnings automatically via a PostgreSQL+pgvector backend, creates YAML-based handoffs at 90% capacity, spawns headless Claude daemons to mine thinking blocks for insights, and recalls relevant memories across sessions. The architecture combines 109 skills (modular capabilities), 32 specialized agents (autonomous workers in isolated contexts), and 30 lifecycle hooks (event interceptors) with a revolutionary TLDR code analysis system that achieves 95% token savings through five progressive layers (AST → Call Graph → Control Flow → Data Flow → Program Dependence Graph). Sessions maintain continuity through PostgreSQL tables tracking sessions, file claims, archival memories, and handoffs, while semantic search via BGE embeddings and FAISS indexing enables natural language queries like "authentication logic" to find relevant functions without exact text matches.

## 2) Core orchestration model

**Hybrid TypeScript/Python Architecture with Event-Driven Hooks**

The orchestration model operates through three distinct tiers as described in the [DeepWiki system overview](https://deepwiki.com/parcadei/Continuous-Claude-v3/3.1-system-overview-and-design-principles):

**Configuration Layer**: A 13-step setup wizard automates PostgreSQL initialization (4 core tables), 109 skill installations, 32 agent definitions, and 30 hook registrations. Supports progressive enhancement—core hooks work minimally, advanced features (TLDR, memory, diagnostics) enable incrementally.

**Execution Layer**: 30 hooks intercept 7 lifecycle events in Claude Code's Node.js runtime:
- `SessionStart` → Loads continuity ledgers (`CONTINUITY_CLAUDE-<session>.md`), finds latest handoff, registers session with heartbeat
- `UserPromptSubmit` → Skill activation system injects context hints based on keywords, recalls archival memories via vector search
- `PreToolUse` → TLDR-read-enforcer replaces raw file reads with structured summaries, smart-search-router routes grep queries to AST-grep for structural matching
- `PostToolUse` → Post-edit diagnostics validates changes, handoff-index updates embeddings, file-claims tracks dirty flags
- `PreCompact` → Auto-saves handoff YAML at 90% context capacity with files modified, tool outputs, work state
- `SubagentStop` → Saves agent state to preserve context from isolated worker sessions
- `SessionEnd` → Triggers cleanup, spawns daemon when heartbeat goes stale (>5 min)

**Intelligence Layer**: Background Python services provide TLDR daemon (5-layer code analysis), memory daemon (headless Claude Sonnet analyzes thinking blocks to extract learnings), and PostgreSQL coordination database for cross-session awareness.

**Agent Orchestration**: 32 specialized agents (sleuth for debugging, kraken for implementation, oracle for research, scout for codebase exploration, aegis/herald/scribe/chronicler/session-analyst/braintrust-analyst/memory-extractor/onboard) run via the Task tool in isolated context windows. Meta-skills chain agents through complex workflows: `/build greenfield` = discovery → plan-agent → validate → implement; `/fix` = sleuth (diagnose) → implement → test → commit; `/refactor` = extract → transform → validate; `/review` = multi-angle analysis including security and TDD perspectives.

**IPC Mechanisms**: TypeScript hooks integrate directly with Claude Code's runtime (5-40 second timeout requirements). Python backend handles heavy ML operations (sentence-transformers, asyncpg, sympy). Communication occurs via subprocess spawning with JSON stdin/stdout for single requests, Unix sockets (TCP on Windows) for persistent daemon connections.

**Graceful Degradation**: Every component includes fallback chains—PostgreSQL → SQLite → no-op. Database unavailability doesn't block core functionality; features degrade based on available dependencies.

## 3) Tooling and execution

**TLDR: 5-Layer Progressive Code Analysis**

The companion project [llm-tldr](https://github.com/parcadei/llm-tldr) provides the code understanding backbone with 95% token savings and 155x faster queries:

**L1 (AST)**: ~500 tokens—function/class signatures, imports, type definitions. "What functions exist?"
**L2 (Call Graph)**: +440 tokens—cross-file dependencies, who calls what. "Who calls this function?"
**L3 (Control Flow Graph)**: +110 tokens—branching complexity, loop structures. "How complex is this?"
**L4 (Data Flow Graph)**: +130 tokens—variable propagation, value transformations. "Where does this value go?"
**L5 (Program Dependence Graph)**: +150 tokens—program slicing, impact analysis. "What affects line 42?"

**Real-world performance**: Reduces 21,000-token function context to 175 tokens (99% savings), cuts 104,000-token codebase overview to 12,000 tokens (89% savings), improves query latency from 30s to 100ms with daemon (300x faster). Supports 16 languages via tree-sitter parsers: Python, TypeScript, JavaScript, Go, Rust, Java, C, C++, Ruby, PHP, C#, Kotlin, Scala, Swift, Lua, Elixir.

**Semantic Index**: BGE-large-en-v1.5 generates 1024-dimensional embeddings of function metadata across all 5 layers. FAISS index enables natural language queries—"validate JWT tokens" finds `verify_access_token()` without exact text matches. Auto-rebuild via dirty flag hooks that track file edits.

**Skills System (109 Total)**

Natural language activation—describe problems instead of memorizing commands. UserPromptSubmit hook scans messages for keywords defined in `skill-rules.json`, shows relevant skills as context hints. Meta-skills orchestrate multi-step workflows with modes, scopes, and flags:
- `/tdd "implement retry logic"` → test-first development
- `/refactor "extract auth module"` → safe code transformation
- `/security "authentication code"` → security-focused review
- `/release` → deployment preparation
- `/workflow` → goal-based routing (first-session recommended)
- `/explore` → codebase understanding walkthrough
- `/premortem` → risk analysis before implementation

Each skill supports interactive mode (type `/build` alone for question flow) or inline mode (`/build greenfield --scope=auth --plan`).

**File Claims and Dirty Tracking**

PostgreSQL `file_claims` table prevents concurrent modification conflicts across sessions. PostToolUse hook tracks which files were edited, triggering TLDR re-indexing only for modified files. Enables multi-terminal development without state corruption.

**Execution Environment**

Docker-based PostgreSQL for persistence. Optional dependencies: SymPy/Z3/Pint for mathematical computation, Lean4 for formal verification. Setup wizard configures environment variables (`CONTINUOUS_CLAUDE_DB_URL`), builds database schema, installs all components with backup of existing `.claude/` config.

## 4) Observability and evaluation

**Continuity Ledgers and Handoffs**

Two complementary state-tracking mechanisms address different continuity needs:

**Continuity Ledgers** (`CONTINUITY_CLAUDE-<session>.md`): Within-session tracking updated continuously during active work. Contains goal and constraints, what's completed vs. in-progress, key decisions with rationale, working files with current status. SessionStart hook loads the most recent ledger to prime context.

**Handoffs** (`thoughts/handoffs/<session>/handoff-<timestamp>.md`): Between-session knowledge transfer created at PreCompact (auto-handoff) or explicit user request. Detailed context with recent changes (file:line references), learnings and patterns observed, next steps with priorities, tool outputs and reasoning traces. Stored with BGE embeddings in PostgreSQL `handoffs` table for semantic recall.

**Token efficiency gain**: Structured handoff protocols reduce 10,000+ token knowledge transfer to 1,000-2,000 token resume operation, saving 30,000-50,000 tokens weekly with 3-5 handoffs per week ($1-5 in API costs per the [handoff protocol blog](https://blackdoglabs.io/blog/claude-code-decoded-handoff-protocol)).

**Archival Memory System**

Seven memory categories tracked via `archival_memory` PostgreSQL table with vector embeddings:
- `WORKING_SOLUTION` → Approaches that succeeded
- `FAILED_APPROACH` → Anti-patterns to avoid
- `ARCHITECTURAL_DECISION` → System design choices with rationale
- `ERROR_FIX` → Bug resolutions and root causes
- `CODEBASE_PATTERN` → Project-specific idioms
- `USER_PREFERENCE` → Developer workflow preferences
- `OPEN_THREAD` → Unresolved questions or TODOs

**Memory Extraction Daemon**: SessionEnd hook triggers PostgreSQL heartbeat detection (>5 min stale). Spawns headless Claude Sonnet instance that analyzes thinking blocks from completed session (the "why" not just the "what"), extracts structured learnings to `archival_memory` with confidence levels, deduplicates via vector similarity thresholds to prevent redundant storage.

**Memory Recall**: UserPromptSubmit hook performs hybrid text+vector search against `archival_memory`, surfaces relevant learnings as "MEMORY MATCH" indicators in context. Claude auto-incorporates these without explicit user request.

**Monitoring and Diagnostics**

According to the [DeepWiki overview](https://deepwiki.com/parcadei/Continuous-Claude-v3), the system includes:
- Status line & dashboard showing session state
- Hook activity tracking for execution flow visibility
- Token usage & cost metrics for optimization
- Braintrust integration for self-review (see [Ankur Goyal's commentary](https://x.com/ankrgyl/status/2005693479071146314): "extends the Braintrust Claude Code plugin to help Claude review its own work, which is a very cool meta use-case")

**Validation Agents**: Dedicated agents for validation & testing, review & quality assurance. Post-edit diagnostics hook validates code changes immediately after edits.

## 5) Extensibility

**Progressive Enhancement Philosophy**

The architecture explicitly rejects "plugin sprawl" through three principles articulated in the [system design](https://deepwiki.com/parcadei/Continuous-Claude-v3/3.1-system-overview-and-design-principles):
1. Time investment over monetary cost—no required paid services
2. Learning systems beat plugin accumulation—"A system that learns handles edge cases better than one that collects plugins"
3. Shift-left validation—pre-commit linting/analysis prevents errors rather than detecting them post-hoc

**Two Integration Modes**

Setup wizard offers:
- **Copy mode** (end-users): Isolated installation, updates via manual re-install, protects against upstream changes
- **Symlink mode** (contributors): Live updates from git repo, enables development workflow on the framework itself

**Hook Extensibility**

30 existing hooks demonstrate the full lifecycle coverage. New hooks can be added by:
1. Creating TypeScript module in `.claude/hooks/`
2. Registering in hook configuration with event type (SessionStart | UserPromptSubmit | PreToolUse | PostToolUse | PreCompact | SubagentStop | SessionEnd)
3. Implementing within 5-40 second timeout constraint
4. Optionally calling Python backend services via subprocess JSON IPC or Unix socket daemon connection

**Skill Composition**

109 skills in `.claude/skills/` directory. Each skill is a standalone module with:
- Natural language activation keywords in `skill-rules.json`
- Mode/scope/flag configuration for behavioral variants
- Interactive question flow for guided usage
- Integration with agents via Task tool spawning

Meta-skills chain multiple agents and skills through workflow definitions. New meta-skills can orchestrate custom sequences.

**Agent Specialization**

32 predefined agents handle common workflows. New agents can be added by defining:
- Agent prompt with domain expertise
- Tool access configuration
- Context isolation requirements
- Communication protocol for returning results to main session

Agents run in fully isolated context windows—no MCP pollution between agent and main session, no shared state corruption.

**TLDR Layer Selection**

The 5-layer architecture enables task-appropriate depth. Hooks can request specific layer combinations:
- Function signatures only: L1 (AST)
- Understand dependencies: L1+L2 (AST + Call Graph)
- Analyze complexity: L1+L3 (AST + CFG)
- Trace data flow: L1+L4 (AST + DFG)
- Impact analysis: All layers L1-L5

Custom layer combinations save tokens while providing exactly the needed context.

**Database Portability**

PostgreSQL primary, SQLite fallback, no-op last resort. The storage layer abstracts via Python backend services, allowing alternative implementations (e.g., DuckDB, cloud-hosted databases like AWS RDS/Supabase/Azure per setup wizard options).

**Embedding Model Swappability**

Current: BGE-large-en-v1.5 (1024 dimensions). Python backend uses sentence-transformers library, enabling swap to any compatible model (OpenAI embeddings, Cohere, custom fine-tuned) by changing configuration and re-indexing.

## 6) Notable practices worth adopting in AGENT-33

**1. "Compound, Don't Compact" Philosophy**

AGENT-33 should adopt this foundational insight: Instead of optimizing compaction algorithms when context fills, **extract learnings automatically and start fresh with full context**. This directly addresses the governance-prompt disconnect finding—we need automatic extraction of governance decisions, capability boundaries, and constraint violations into persistent memory.

**Implementation**: Create a post-session daemon that analyzes AGENT-33's `thoughts/` traces (similar to Continuous Claude's thinking block analysis), extracts governance violations/successes to PostgreSQL with embeddings, recalls them at session start via hooks that inject into agent system prompts.

**2. Pre-Compact Handoff Hook**

The PreCompact hook that auto-saves context at 90% capacity prevents catastrophic context loss. AGENT-33 workflows can run hours—having automatic checkpointing before compaction is critical.

**Implementation**: Add PreCompact lifecycle event to AGENT-33's workflow engine. When context usage exceeds threshold (detect via token counting or Claude Code's internal signals), trigger `create_handoff` action that writes `state_snapshot_<timestamp>.yaml` with: active workflow ID, completed steps, pending steps, agent states, key decisions, working files. Store in `thoughts/handoffs/` and index with embeddings.

**3. TLDR-Style Progressive Code Analysis**

The 5-layer AST/CFG/DFG/PDG approach achieving 95% token savings directly solves AGENT-33's "cannot process large codebases" limitation. Current RAG is first-gen vector-only; TLDR provides structural understanding.

**Implementation**: Integrate [llm-tldr](https://github.com/parcadei/llm-tldr) as an MCP server or direct Python library. Modify FileOpsTool to call TLDR instead of raw file reads. Add layer selection logic: L1 for discovery, L1+L2 for refactoring, all layers for impact analysis. Store FAISS indexes in `engine/data/tldr_index/` with dirty flag tracking via workflow hooks.

**4. Archival Memory with Deduplication**

The 7-category memory system (WORKING_SOLUTION, FAILED_APPROACH, etc.) with vector deduplication prevents redundant storage while enabling cross-session learning. AGENT-33's training loop captures rollouts but lacks semantic categorization.

**Implementation**: Extend `engine/src/agent33/memory/long_term.py` to add `memory_category` enum field, implement `deduplicate_via_embeddings()` method that checks cosine similarity before insert (threshold 0.92), create memory extraction daemon that analyzes workflow traces at session end. Recall via hybrid search in `agents/runtime.py:_build_system_prompt()` to **finally inject governance context into LLM prompts**.

**5. File Claims for Multi-Session Safety**

PostgreSQL `file_claims` table preventing concurrent modification is elegant. AGENT-33's multi-agent workflows could have race conditions if multiple agents edit the same file.

**Implementation**: Add `file_claims` table to Alembic migrations with columns: `file_path`, `claimed_by_agent`, `claimed_at`, `session_id`. Modify FileOpsTool to check claims before edits, block if claimed by different agent, auto-release claims on workflow completion or 30-minute timeout.

**6. Semantic Search Across Code Analysis Layers**

BGE embeddings + FAISS indexing enabling natural language queries like "authentication logic" → `verify_access_token()` is superior to AGENT-33's current keyword-only grep.

**Implementation**: Replace current vector-only RAG with hybrid approach: BM25 for keyword precision (already identified as gap in research sprint), FAISS for semantic recall, TLDR layers for structural understanding. Add `tools/builtin/semantic_code_search.py` that queries across all 5 layers with re-ranking.

**7. Hook-Based Architecture for Lifecycle Events**

The 7 lifecycle events (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, SubagentStop, SessionEnd) enabling transparent augmentation without modifying core systems is brilliant. AGENT-33's workflow engine has actions but lacks lifecycle interception.

**Implementation**: Add `WorkflowHooks` registry in `workflows/engine.py` with events: `workflow_start`, `step_start`, `step_end`, `tool_pre_invoke`, `tool_post_invoke`, `workflow_suspend`, `workflow_end`. Allow registration of Python callables via config. Use for automatic state persistence, governance validation, token usage tracking, error capture.

**8. Meta-Skills as Workflow Templates**

The `/fix`, `/build`, `/refactor` meta-skills that chain specialized agents through multi-step procedures map perfectly to AGENT-33's DAG-based workflows but with better UX—natural language activation instead of JSON definitions.

**Implementation**: Create `workflows/meta_templates/` directory with YAML definitions for common patterns (debug_and_fix, greenfield_feature, security_audit). Add natural language router in `routes/chat.py` that detects intent ("help me debug the auth module") and selects appropriate template, then executes via existing workflow engine.

**9. Graceful Degradation Chains**

PostgreSQL → SQLite → no-op fallback pattern ensures core functionality survives infrastructure failures. AGENT-33 currently fails hard if PostgreSQL is down.

**Implementation**: Modify `config.py` to add `DATABASE_FALLBACK_MODE` enum (POSTGRES | SQLITE | MEMORY | DISABLED). Update database initialization in `main.py` lifespan to attempt connection sequence. Wrap DB operations in try/except that logs degradation but allows execution to continue with limited features.

**10. Thinking Block Analysis for Learning Extraction**

The daemon that analyzes "thinking blocks" (the reasoning traces, not just action outputs) to extract learnings is the key to continuous improvement. AGENT-33 has observability traces but doesn't mine them for insights.

**Implementation**: Add `observability/learning_extractor.py` that runs post-workflow: parses `thoughts/` markdown files for decision rationales, identifies patterns (successful tool sequences, failed approaches), extracts to `archival_memory` table with confidence scores, uses as training data for the existing training loop in `training/optimization.py`.

## 7) Risks / limitations to account for

**1. Context Window Still Fundamentally Limited**

As noted in the [context window challenges research](https://www.vibesparking.com/blog/ai/claude-code/continuous-claude/2025-12-25-continuous-claude-context-management-guide/), the core problem remains: "after several compaction cycles, you're essentially working with a summary of a summary of a summary, and signal degrades into noise." Continuous Claude mitigates via external state but doesn't eliminate the constraint.

**AGENT-33 implication**: Cannot rely solely on handoffs for very long workflows (8+ hour multi-agent orchestrations). Need explicit checkpointing with full state serialization, not just summaries. Consider workflow hibernation/resume patterns where agents shut down completely and restart from serialized state.

**2. Daemon Dependency Creates Latency**

The memory extraction daemon requires spawning headless Claude instances, which incurs API costs and 5+ minute delays before learnings are available. Real-time learning requires in-session extraction.

**AGENT-33 implication**: Don't block workflow completion on memory extraction. Run asynchronously via background task. Provide immediate in-session memory via short-term buffer, augment with archival memory in subsequent sessions. Budget for daemon API costs in production ($0.50-2.00 per session extraction based on thinking block size).

**3. PostgreSQL as Single Point of Failure**

Despite graceful degradation claims, many features completely break without PostgreSQL: file claims (race condition protection), archival memory (cross-session learning), handoffs (session persistence), session coordination (multi-terminal awareness).

**AGENT-33 implication**: We already have PostgreSQL as core dependency; this isn't new risk. However, implement SQLite fallback for local dev environments and edge deployments. Critical: Ensure governance validation works in no-op mode using static rule files, not just DB queries.

**4. Tree-sitter Language Support Gaps**

TLDR supports 16 languages but many enterprise languages missing: Scala, Clojure, Haskell, OCaml, Perl, Visual Basic, COBOL, Fortran. Fallback to raw file reading negates token savings.

**AGENT-33 implication**: Document supported languages clearly. For unsupported languages, implement simplified AST extraction via regex-based function signature parsing (fragile but better than nothing). Contribute tree-sitter grammars for priority languages as community effort.

**5. BGE Embedding Model is Fixed-Size (1024d)**

Changing embedding dimensions requires complete re-indexing of all archival memories, handoffs, and TLDR semantic indexes. Migration path is expensive.

**AGENT-33 implication**: Choose embedding model carefully at initial deployment. If using OpenAI embeddings (text-embedding-3-large: 3072d), accept the dimensional mismatch upfront. Implement version tagging on embeddings to allow gradual migration: new embeddings in new dimension, query both indexes, deprecate old index after 90 days.

**6. Hook Timeout Constraints (5-40 seconds)**

TypeScript hooks must complete within tight timeouts or they're killed by Claude Code runtime. Complex operations (full codebase re-indexing, large file analysis) can't run synchronously.

**AGENT-33 implication**: Hooks should only trigger background jobs, not execute them inline. Use NATS for async job dispatch: hook publishes event, worker processes in background, next session benefits from completed work. Critical path operations (governance checks, security validation) must be fast (<5s) or they fail open—unacceptable for safety.

**7. Semantic Deduplication Can Lose Nuance**

The 0.92 cosine similarity threshold for memory deduplication prevents near-duplicates but can incorrectly merge genuinely different learnings that happen to have similar embeddings (e.g., "retry with exponential backoff worked for API calls" vs. "retry with exponential backoff worked for database connections").

**AGENT-33 implication**: Lower threshold to 0.95 for strict deduplication. Add metadata-based secondary checks: same workflow ID, same file path, same error code. Allow manual de-duplication override via admin endpoint. Implement learning merge UI showing both candidates before auto-merging.

**8. No Rollback Mechanism for Extracted Learnings**

Once daemon extracts incorrect learning (e.g., misinterprets failure as success, overgeneralizes pattern), it pollutes future sessions. No audit trail for "why was this learning extracted?"

**AGENT-33 implication**: Add `learning_provenance` table: source session ID, source thinking block excerpt, extraction timestamp, daemon version, confidence score. Implement learning quality feedback loop: if agent repeatedly ignores a learning, downweight it. Provide `/memory audit` command showing recent extractions with source context.

**9. IPC Security Surface**

Subprocess spawning with JSON stdin/stdout and Unix socket daemons create privilege escalation risks if malicious input can reach Python backend. The [Claude Code issues](https://github.com/anthropics/claude-code/issues/771) show subprocess handling is complex.

**AGENT-33 implication**: We already have subprocess execution as core feature (CLIAdapter). Apply same security model: input validation via `validation.py` IV-01 through IV-05 checks, subprocess sandboxing per `SandboxConfig`, non-root execution, resource limits. Never pass unsanitized user input to subprocess args.

**10. Setup Wizard Complexity Barrier**

13-step installation with Docker, PostgreSQL, 109 skills, 30 hooks creates high friction for first-time users. Failure at any step blocks entire system.

**AGENT-33 implication**: Provide three deployment tiers: "Lite" (core workflows only, SQLite, no TLDR), "Standard" (PostgreSQL + TLDR + memory), "Advanced" (full 109 skills + agents). Make Lite → Standard → Advanced upgradeable without data loss. Document each optional dependency clearly with "works without X but loses Y capability."

## 8) Feature extraction (for master matrix)

| Feature | Implementation Detail | AGENT-33 Gap |
|---------|----------------------|--------------|
| **Pre-Compact Auto-Handoff** | Hook at 90% context capacity writes YAML snapshot (files, decisions, next steps) | No context monitoring; sessions lose state at compaction |
| **Archival Memory Extraction** | Daemon analyzes thinking blocks post-session → PostgreSQL with 7 categories + embeddings | Training loop captures rollouts but no semantic categorization or cross-session recall |
| **TLDR 5-Layer Code Analysis** | AST/CallGraph/CFG/DFG/PDG progressive summaries, 95% token savings, 16 languages via tree-sitter | RAG is vector-only, no structural understanding, cannot parse code semantically |
| **File Claims Table** | PostgreSQL tracks which agent owns which file, prevents concurrent modification races | Multi-agent workflows have unprotected race condition potential |
| **Semantic Code Search** | BGE embeddings + FAISS across all 5 TLDR layers, natural language queries → ranked functions | Keyword-only grep, no semantic understanding, no re-ranking |
| **Continuity Ledgers** | Within-session `CONTINUITY_CLAUDE-<session>.md` updated continuously with goal/progress/decisions | Workflow state exists but not human-readable markdown summary |
| **Handoff Embeddings** | All handoffs stored with BGE vectors for semantic recall of past session contexts | No session-to-session knowledge transfer mechanism |
| **Hook Lifecycle Events** | 7 events (SessionStart/UserPromptSubmit/PreToolUse/PostToolUse/PreCompact/SubagentStop/SessionEnd) | Workflow actions but no lifecycle interception points |
| **Meta-Skills as Workflows** | `/fix`, `/build`, `/refactor` natural language → multi-agent orchestration | Workflows require JSON definitions, no NL activation |
| **Memory Deduplication** | Vector similarity check (0.92 threshold) before archival_memory insert | No deduplication; redundant learnings accumulate |
| **Agent Context Isolation** | Task tool spawns agents in fully separate contexts, no MCP pollution | Agents share same context; tool registry pollution risk |
| **Graceful Degradation** | PostgreSQL → SQLite → no-op fallback chain | Hard failure if PostgreSQL down |
| **Skill Activation Hints** | UserPromptSubmit hook scans keywords → injects relevant skill context | No proactive skill suggestion system |
| **Dirty Flag Tracking** | PostToolUse hook marks edited files → triggers selective TLDR re-indexing | Full re-index or no re-index, no incremental updates |
| **Daemon Heartbeat Detection** | PostgreSQL session.last_heartbeat > 5min → spawn learning extraction | No automatic post-session analysis |
| **Hybrid Memory Search** | Text + vector search across archival_memory on UserPromptSubmit | Vector-only RAG search |
| **Progressive Enhancement Install** | 3 tiers (Lite/Standard/Advanced) with incremental feature enabling | All-or-nothing installation |
| **Thinking Block Mining** | Extracts "why" reasoning from traces, not just "what" actions | Observability captures actions but no reasoning extraction |
| **Session Coordination** | PostgreSQL sessions table enables multi-terminal awareness | No cross-terminal state awareness |
| **Braintrust Self-Review Integration** | Claude reviews own work via external evaluation service | No self-evaluation loop |

## 9) Evidence links

**Primary Repository**
- [parcadei/Continuous-Claude-v3 GitHub](https://github.com/parcadei/Continuous-Claude-v3)
- [Continuous-Claude-v3 README](https://github.com/parcadei/Continuous-Claude-v3/blob/main/README.md)

**Architecture and Design**
- [System Overview & Design Principles - DeepWiki](https://deepwiki.com/parcadei/Continuous-Claude-v3/3.1-system-overview-and-design-principles)
- [Full Project Documentation - DeepWiki](https://deepwiki.com/parcadei/Continuous-Claude-v3)

**TLDR Code Analysis**
- [llm-tldr GitHub Repository](https://github.com/parcadei/llm-tldr)
- [TLDR Documentation](https://github.com/parcadei/llm-tldr/blob/main/docs/TLDR.md)

**Community and Integration**
- [Continuous Claude v3: Persistent Multi-Agent Dev Environment - AIBit](https://aibit.im/blog/post/continuous-claude-v3-a-persistent-multi-agent-open-source-dev-environment)
- [Continuous Claude MCP Server - LobeHub](https://lobehub.com/mcp/parcadei-continuous_claude)
- [Braintrust Integration Commentary - Ankur Goyal](https://x.com/ankrgyl/status/2005693479071146314)

**Handoff and Session Management**
- [Claude Code Handoff Protocol - Black Dog Labs](https://blackdoglabs.io/blog/claude-code-decoded-handoff-protocol)
- [Continuous Claude Context Management Guide - Vibe Sparking AI](https://www.vibesparking.com/blog/ai/claude-code/continuous-claude/2025-12-25-continuous-claude-context-management-guide/)
- [Session Handoff Feature Request - GitHub Issue](https://github.com/anthropics/claude-code/issues/11455)

**Hooks and Lifecycle**
- [Claude Code Hooks Configuration - Official Blog](https://claude.com/blog/how-to-configure-hooks)
- [Hooks Reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)
- [Claude Code Hooks Production Patterns - marc0.dev](https://www.marc0.dev/en/blog/claude-code-hooks-production-patterns-async-setup-guide-1770480024093)

**Agent Orchestration**
- [Agent Teams Documentation - Claude Code Docs](https://code.claude.com/docs/en/agent-teams)
- [Claude Code Multi-Agent System Analysis - paddo.dev](https://paddo.dev/blog/claude-code-hidden-swarm/)

**Technical Deep Dives**
- [Semantic Search with FAISS - Hugging Face Course](https://huggingface.co/learn/llm-course/en/chapter5/6)
- [Billion-scale Semantic Search with FAISS+SBERT - Towards Data Science](https://towardsdatascience.com/billion-scale-semantic-similarity-search-with-faiss-sbert-c845614962e2/)
- [RAG with LangChain, FAISS, NVIDIA BGE-M3 - Zilliz Tutorial](https://zilliz.com/tutorials/rag/langchain-and-faiss-and-nvidia-bge-m3-and-voyage-3)
