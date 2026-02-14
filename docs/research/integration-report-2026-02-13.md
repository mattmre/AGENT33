# AGENT-33 Research Sprint Integration Report

**Date:** 2026-02-13
**Scope:** 30 repository/resource dossiers analyzed
**Purpose:** Synthesize cross-cutting findings, identify priority adaptations, and map capability gaps

---

## Executive Summary

This report synthesizes findings from a 30-dossier research sprint covering multi-agent orchestration frameworks, RAG systems, security scanners, workflow engines, browser automation tools, document processors, system prompt archives, and developer productivity platforms. The research targeted specific gaps in AGENT-33's architecture and identified actionable patterns from production-grade projects.

**The single most critical finding** is the governance-prompt disconnect: AGENT-33's `GovernanceConstraints` model exists in `definition.py` but is never injected into LLM prompts by `_build_system_prompt()` in `runtime.py:29-63`. This was independently confirmed by 5 dossiers (Agent-Zero, Claude Code, awesome-claude-skills, system-prompts-ai-tools, ZeroClaw). Every production AI tool studied embeds safety and governance rules directly in system prompts as defense-in-depth alongside code-level enforcement.

**Top 5 priority adaptations by effort-to-impact ratio:**

1. **Wire governance into prompts** -- Inject `GovernanceConstraints` into `_build_system_prompt()` (Low effort, Critical impact)
2. **Batch embeddings** -- Replace sequential embedding in `embeddings.py:36` with batched calls (Low effort, High impact -- 67x speedup)
3. **HTTP client pooling** -- Pool httpx clients in `ollama.py` instead of creating per-request (Low effort, High impact)
4. **Add BM25 hybrid search** -- Add full-text search alongside pgvector for hybrid retrieval (Medium effort, High impact -- 20-40% precision gain)
5. **Typed exception hierarchy** -- Define workflow step exception types for per-step error isolation (Low effort, Medium impact)

---

## Repository Table

| # | Repository | Focus Area | Key Takeaway for AGENT-33 |
|---|-----------|-----------|--------------------------|
| 1 | openai/swarm | Agent orchestration | LLM-driven routing via function-return handoffs; hub-and-spoke escalation |
| 2 | agent0ai/agent-zero | Autonomous agent framework | Prompt-driven governance (102 prompt files composed into system message); LLM-driven memory consolidation |
| 3 | Continuous-Claude-v3 | Session persistence | TLDR 5-layer code analysis (95% token savings); pre-compact handoff at 90% capacity |
| 4 | anthropic/claude-code | Developer tool | Three-tier permission system (deny-first); hooks with decision control (14 event types) |
| 5 | anomalyco/opencode | AI coding agent | Wildcard glob permission patterns; doom_loop protection (blocks after 3 identical calls) |
| 6 | alexzhang13/rlm | Recursive LLM agents | Depth-based model routing (expensive at root, cheap for sub-calls); fail-fast error handling |
| 7 | Tencent/WeKnora | Enterprise RAG | Hybrid retrieval (BM25 + vector + GraphRAG); reranking pipeline; query rewriting |
| 8 | HKUDS/AI-Researcher | Automated research | Atomic concept decomposition; debiased multi-evaluator assessment |
| 9 | claude-plugins-official | Plugin architecture | Optional manifest with auto-discovery; persistent agent memory (user/project/local scopes) |
| 10 | awesome-claude-skills | Skill ecosystem | Progressive skill disclosure (3-tier loading); frontmatter-driven invocation control |
| 11 | ui-ux-pro-max-skill | Design knowledge base | BM25 text search over CSV as lightweight vector alternative; priority keyword injection |
| 12 | trigger.dev | Durable execution | Checkpoint-at-wait (release concurrency during pauses); batch trigger primitives; idempotency keys |
| 13 | cc-wf-studio | Workflow authoring | Dual-purpose schema (runtime + AI context); validation-as-authoring-constraint |
| 14 | n8n-workflows | Workflow composition | Sub-workflow action; HTTP request action; merge/join (6 modes); circuit breaker; DLQ |
| 15 | EdgeQuake | Performance-oriented RAG | HTTP client pooling; embedding batch constants (2048 OpenAI, 512 Ollama); 1200-token chunks |
| 16 | GhidraMCP | MCP bridge | Transaction-wrapped modifications with auto-rollback; tool categorization with pagination |
| 17 | katanaml/sparrow | Document processing | Vision-first document processing (VLM over raw images); factory pattern for multi-backend VLM |
| 18 | PaddlePaddle/PaddleOCR | OCR engine | MCP server pattern for tool integration; incremental batch processing |
| 19 | ChromePilot | Browser automation | Accessibility-first element identification; dual-LLM token optimization |
| 20 | RAG-Anything | Multimodal RAG | Tokenizer-aware chunking (1200 tokens, tiktoken); dual-graph representation; reranking with cross-encoder |
| 21 | livekit/livekit | Real-time communication | Plugin architecture for swappable providers; worker dispatch model; fine-grained JWT capability tokens |
| 22 | yt-dlp/yt-dlp | Media downloader | Auto-discovery via base-class scanning; embedded test cases per module; typed exception hierarchy |
| 23 | aquasecurity/trivy | Security scanner | Multi-scanner parallel pipeline; severity filtering with expiration; SARIF output; VEX suppression |
| 24 | envhush-cli | Secret management | (Stub -- source inaccessible) |
| 25 | makeplane/plane | Project management | Workspace-scoped URL namespacing prevents IDOR; hierarchical RBAC; activity stream audit log |
| 26 | system-prompts-ai-tools | Prompt archive | Structured multi-section prompts; tool-use governance in natural language; anti-hallucination patterns |
| 27 | multi-agent-rl-survey | RL survey paper | (Stub -- source inaccessible; training is single-agent with no multi-agent coordination) |
| 28 | anthropic-building-skills | Skill guide | (Stub -- source inaccessible) |
| 29 | zeroclaw | Rust AI agent | Hybrid search memory (FTS5 + vector + weighted merge); security policy with autonomy levels; encrypted secrets |
| 30 | petabridge/memorizer-v1 | Agent memory service | Event-sourced versioning; typed relationship graphs; dual embedding strategy; lightweight search results |

---

## Cross-Cutting Findings

### 1. Orchestration Patterns

Five distinct orchestration paradigms emerged from the research:

**a) LLM-driven routing (Swarm, OpenCode)**
The LLM decides which agent handles the next step by returning a function call that triggers a handoff. No fixed DAG. AGENT-33 currently uses static DAGs only. Adding an `invoke_agent_dynamic` action that lets the LLM select the next agent (constrained by an allowlist) would enable conversational routing without abandoning DAG safety.

**b) Prompt-driven governance (Agent-Zero, ZeroClaw, system-prompts-ai-tools)**
Agent behavior is defined entirely through composable prompt files (Agent-Zero: 102 files; ZeroClaw: SOUL.md, IDENTITY.md, TOOLS.md). AGENT-33 has `AgentDefinition.prompts.system` pointing to template paths but `_build_system_prompt()` ignores them. This is the governance-prompt disconnect.

**c) Checkpoint-resume durable execution (Trigger.dev)**
Long-running tasks checkpoint at wait points, releasing concurrency. AGENT-33's workflow engine has checkpoint persistence but no concurrency release during waits.

**d) Sequential pipeline with refinement loops (AI-Researcher, RAG-Anything)**
Multi-stage pipelines where later stages can loop back to earlier ones for iterative improvement. AGENT-33's DAG engine supports sequential execution but has no native loop/refinement construct.

**e) Hub-and-spoke escalation (Swarm, LiveKit)**
A triage/orchestrator agent routes to specialists and receives results back for synthesis. AGENT-33's orchestrator agent definition exists but the workflow engine lacks a native "fan-out then aggregate" pattern.

### 2. Capability Gaps

**a) RAG is first-generation (confirmed by 6 dossiers)**

| Gap | Current State | Target State | Sources |
|-----|--------------|-------------|---------|
| No BM25/sparse search | Vector-only (pgvector cosine) | Hybrid BM25 + vector with weighted merge | WeKnora, EdgeQuake, ZeroClaw, ui-ux-pro-max |
| No reranking | Direct retrieval | Cross-encoder reranking (BGE/Cohere/Jina) | WeKnora, RAG-Anything |
| No query rewriting | Raw user query | Conversational context rewriting | WeKnora |
| Small chunks (500 chars) | Character-based splitting | 1200 tokens with tiktoken-aware splitting | RAG-Anything, EdgeQuake, WeKnora |
| No embedding cache | Recompute every time | Cache embeddings with content hash, LRU eviction | ZeroClaw, EdgeQuake |

**b) Cannot process documents (confirmed by 3 dossiers)**

AGENT-33's `ReaderTool` is web-only; `FileOpsTool` is UTF-8 text only. No PDF, image, or table extraction.

| Capability | Solution Pattern | Source |
|-----------|-----------------|--------|
| PDF ingestion | Vision-first VLM processing | Sparrow |
| OCR for images | MCP server wrapping PaddleOCR | PaddleOCR |
| Table extraction | Layout-aware detection + extraction | Sparrow, RAG-Anything |

**c) Missing workflow actions (confirmed by 2 dossiers)**

| Missing Action | Description | Source |
|---------------|-------------|--------|
| `sub_workflow` | Invoke a workflow from within a workflow step | n8n |
| `http_request` | Make HTTP calls as a workflow action | n8n |
| `merge_join` | Combine outputs from parallel branches (6 modes) | n8n |
| `circuit_breaker` | Fail-fast after N consecutive errors | n8n |

**d) No conversational routing (confirmed by 2 dossiers)**

AGENT-33 uses static DAGs only. Swarm's function-return handoff pattern and RLM's recursive sub-call pattern both enable dynamic, LLM-decided agent selection that AGENT-33 lacks.

### 3. Security Patterns

**a) Three-tier permission systems**

Multiple projects implement layered permission tiers:
- Claude Code: read-only / modify / execute (deny-first)
- ZeroClaw: ReadOnly / Supervised / Full (enforced at every tool execution)
- OpenCode: allow / ask / deny (glob-based patterns)

AGENT-33's scope-based auth (`["admin"]`) is flat. Recommendation: adopt per-agent autonomy levels with per-tool permission tiers.

**b) SSRF and injection protection**

- WeKnora: IP blocklist for `web_fetch` (blocks private ranges, loopback, link-local)
- ZeroClaw: Multi-segment command validation blocking subshells, backticks, `$()`
- Trivy: Read-only scanning model (never modifies targets)

AGENT-33's `web_fetch.py` has no SSRF protection. The shell tool does not validate command pipelines.

**c) Prompt injection defense**

Every production AI tool studied (ChatGPT, Claude, Copilot, Cursor, Grok) includes instruction-hiding directives in system prompts. AGENT-33 has `security/prompt_injection.py` for detection but no instruction-hiding in agent prompts.

**d) URL-scoped tenant isolation (IDOR prevention)**

Plane's pattern: `/api/v1/workspaces/{workspace_slug}/projects/{project_id}/issues/` makes tenant isolation structural. AGENT-33's routes (`/v1/workflows/{name}`) lack tenant scoping in the URL, relying solely on middleware filtering.

### 4. Performance Patterns

| Quick Win | Current | Fix | Speedup | Sources |
|-----------|---------|-----|---------|---------|
| Batch embeddings | Sequential in `embeddings.py:36` | Batch with provider-specific limits (2048 OpenAI, 512 Ollama) | 67x | EdgeQuake, RAG-Anything |
| HTTP client pooling | New httpx client per request in `ollama.py:41,69` | Create once in `__init__`, reuse | ~10x latency reduction | EdgeQuake |
| Chunk size | 500 chars | 1200 tokens with tiktoken | Better recall | RAG-Anything, EdgeQuake, WeKnora |
| Embedding cache | None | Hash-based cache table with LRU eviction | Eliminates redundant API calls | ZeroClaw |
| Empty text filtering | Not checked | Filter empty/whitespace strings before embedding | Prevents wasted API calls | EdgeQuake |

### 5. Extensibility Patterns

**a) Plugin architecture for providers**

LiveKit's `livekit-plugins-*` pattern (separate packages per provider, common base class) is the gold standard. AGENT-33's `llm/` providers are monolithic modules. Formalizing a `BaseLLMPlugin` interface would enable community-contributed providers.

**b) Auto-discovery via base-class scanning**

yt-dlp scans all `InfoExtractor` subclasses with `_VALID_URL` regex for auto-routing. AGENT-33's `AgentRegistry` auto-discovers JSON definitions but the `ToolRegistry` uses explicit YAML registration. Extending auto-discovery to tools would reduce boilerplate.

**c) Embedded test cases in definitions**

yt-dlp's `_TESTS` class attribute ensures every extractor ships with at least one test. AGENT-33's agent definitions (`agent-definitions/*.json`) have no embedded test cases. Adding a `tests` array to definitions would enable auto-generated behavioral tests.

**d) Skills/SKILL.md standard**

Agent-Zero, awesome-claude-skills, ZeroClaw, and claude-plugins-official all converge on a portable skill format: YAML/TOML frontmatter + markdown body with metadata, tool definitions, and prompts. AGENT-33 could adopt this as an extension mechanism for agent capabilities.

### 6. Observability Patterns

**a) Audit trail as append-only activity log**

Plane's `IssueActivity` model records every field change with actor, timestamp, old value, new value. AGENT-33's `observability/lineage.py` provides lineage tracking but lacks field-level change auditing for workflow state transitions.

**b) Event-sourced versioning**

Memorizer's discriminated union events (ContentUpdated, MetadataUpdated, MemoryReverted) enable full audit trails and rollback. AGENT-33's memory system has no version history for observations.

**c) Observer trait pattern**

ZeroClaw's `Observer` trait with events (AgentStart, AgentEnd, ToolCall, Error) and metrics (RequestLatency, TokensUsed) is a clean abstraction. AGENT-33's observability is more comprehensive (structlog, tracing, metrics, lineage) but could benefit from a unified event taxonomy.

---

## Priority Recommendations

Ranked by effort-to-impact ratio (highest value first):

### Tier 1: Quick Wins (< 1 day each, high impact)

| # | Recommendation | Effort | Impact | Phase | Key Sources |
|---|---------------|--------|--------|-------|-------------|
| 1 | **Wire GovernanceConstraints into `_build_system_prompt()`** | 2h | Critical | 14 | Agent-Zero, ZeroClaw, system-prompts |
| 2 | **Batch embedding calls in `embeddings.py`** | 2h | High | Any | EdgeQuake, RAG-Anything |
| 3 | **Pool httpx clients in `ollama.py`** | 1h | High | Any | EdgeQuake |
| 4 | **Add anti-hallucination guardrails to agent prompts** | 2h | High | 14 | system-prompts, Perplexity patterns |
| 5 | **Add instruction-hiding directives to agent prompts** | 1h | Medium | 14 | system-prompts (all production tools) |

### Tier 2: Medium Effort (1-3 days each, high impact)

| # | Recommendation | Effort | Impact | Phase | Key Sources |
|---|---------------|--------|--------|-------|-------------|
| 6 | **Add BM25 full-text search + hybrid merge to RAG pipeline** | 2d | High | 15+ | WeKnora, ZeroClaw, EdgeQuake |
| 7 | **Typed workflow step exception hierarchy** | 1d | Medium | 14 | yt-dlp |
| 8 | **SSRF protection in `web_fetch.py`** (IP blocklist for private ranges) | 1d | High | 14 | WeKnora |
| 9 | **Multi-segment command validation in shell tool** | 1d | High | 14 | ZeroClaw |
| 10 | **Cross-encoder reranking in RAG pipeline** | 2d | High | 15+ | WeKnora, RAG-Anything |
| 11 | **Tokenizer-aware chunking (1200 tokens, tiktoken)** | 1d | Medium | 15+ | RAG-Anything, EdgeQuake |
| 12 | **Embedding cache with content hash** | 1d | Medium | Any | ZeroClaw |

### Tier 3: Larger Efforts (1-2 weeks each, strategic impact)

| # | Recommendation | Effort | Impact | Phase | Key Sources |
|---|---------------|--------|--------|-------|-------------|
| 13 | **Sub-workflow action for hierarchical composition** | 1w | High | 15 | n8n |
| 14 | **HTTP request workflow action** | 3d | High | 15 | n8n |
| 15 | **Per-agent autonomy levels (read-only/supervised/full)** | 1w | High | 14 | ZeroClaw, Claude Code |
| 16 | **URL-scoped tenant isolation** (`/v1/tenants/{id}/...`) | 1w | High | 14 | Plane |
| 17 | **Hierarchical RBAC** (`workspace:admin`, `project:{id}:member`) | 1w | High | 14 | Plane, LiveKit |
| 18 | **LLM-driven dynamic agent routing** | 1w | Medium | 18 | Swarm, RLM |
| 19 | **Plugin architecture for LLM providers** | 1w | Medium | 15+ | LiveKit |
| 20 | **Document ingestion pipeline** (PDF/image/table) | 2w | Medium | 15+ | Sparrow, PaddleOCR |

---

## Gap Analysis Matrix

This matrix maps AGENT-33 subsystems against capabilities observed across the 30 dossiers.

| Capability | AGENT-33 Status | Gap Severity | Relevant Dossiers | Recommended Phase |
|-----------|----------------|-------------|-------------------|------------------|
| **Orchestration** | | | | |
| Static DAG execution | Complete | -- | -- | -- |
| LLM-driven dynamic routing | Missing | Medium | Swarm, RLM | 18 |
| Sub-workflow composition | Missing | High | n8n | 15 |
| Fan-out/aggregate (merge/join) | Missing | Medium | n8n | 15 |
| Checkpoint-resume with concurrency release | Partial (checkpoint only) | Low | Trigger.dev | 19 |
| Circuit breaker pattern | Missing | Medium | n8n | 15 |
| **RAG/Memory** | | | | |
| Vector similarity search | Complete (pgvector) | -- | -- | -- |
| BM25/sparse keyword search | Missing | High | WeKnora, ZeroClaw, ui-ux-pro-max | 15+ |
| Hybrid merge (vector + BM25) | Missing | High | WeKnora, ZeroClaw, EdgeQuake | 15+ |
| Cross-encoder reranking | Missing | High | WeKnora, RAG-Anything | 15+ |
| Query rewriting | Missing | Medium | WeKnora | 15+ |
| Tokenizer-aware chunking | Missing (500-char) | Medium | RAG-Anything, EdgeQuake | 15+ |
| Embedding cache | Missing | Medium | ZeroClaw | Any |
| Memory consolidation (LLM-driven) | Missing | Low | Agent-Zero | 20 |
| Event-sourced versioning | Missing | Low | Memorizer | 20 |
| Knowledge graph relationships | Missing | Low | Memorizer, RAG-Anything | 20 |
| **Security** | | | | |
| Governance in prompts | Missing (critical) | Critical | Agent-Zero, ZeroClaw, system-prompts | 14 |
| Per-agent autonomy levels | Missing | High | ZeroClaw, Claude Code | 14 |
| SSRF protection | Missing | High | WeKnora | 14 |
| Command pipeline validation | Missing | High | ZeroClaw | 14 |
| URL-scoped tenant isolation | Missing | High | Plane | 14 |
| Prompt injection detection | Present | -- | -- | -- |
| Instruction-hiding in prompts | Missing | Medium | system-prompts | 14 |
| Anti-hallucination guardrails | Missing | Medium | system-prompts | 14 |
| Encrypted secrets at rest | Partial (vault exists) | Low | ZeroClaw | 14 |
| Severity-based finding suppression with expiration | Missing | Low | Trivy | 14 |
| **Performance** | | | | |
| Batch embeddings | Missing | High | EdgeQuake, RAG-Anything | Any |
| HTTP client pooling | Missing | High | EdgeQuake | Any |
| Proper chunk sizing | Missing (500 chars) | Medium | RAG-Anything, EdgeQuake | Any |
| Empty text filtering for embeddings | Missing | Low | EdgeQuake | Any |
| **Document Processing** | | | | |
| PDF ingestion | Missing | Medium | Sparrow | 15+ |
| Image/OCR processing | Missing | Medium | PaddleOCR | 15+ |
| Table extraction | Missing | Medium | Sparrow, RAG-Anything | 15+ |
| **Extensibility** | | | | |
| Auto-discovery for agents (JSON) | Complete | -- | -- | -- |
| Auto-discovery for tools | Missing (YAML manual) | Low | yt-dlp | 15 |
| Embedded test cases in definitions | Missing | Medium | yt-dlp | 17 |
| Plugin architecture for providers | Missing | Medium | LiveKit | 15+ |
| Skill/SKILL.md portable format | Missing | Low | Agent-Zero, ZeroClaw, awesome-claude-skills | 15+ |
| **Observability** | | | | |
| Structured logging | Complete (structlog) | -- | -- | -- |
| Distributed tracing | Present | -- | -- | -- |
| Field-level change audit trail | Missing | Medium | Plane | 16 |
| Unified event taxonomy | Missing | Low | ZeroClaw | 16 |
| **Testing** | | | | |
| Unit tests | Complete (197 passing) | -- | -- | -- |
| MockLLMProvider | Complete | -- | -- | -- |
| Embedded test cases in definitions | Missing | Medium | yt-dlp | 17 |
| Multi-evaluator assessment | Missing | Low | AI-Researcher | 17 |
| Prompt effectiveness evaluation | Missing | Medium | system-prompts | 17 |

---

## Appendix: Dossiers Not Fully Generated

Three dossiers could not be fully generated due to source access limitations:

1. **envhush-cli** -- GitHub source inaccessible to researcher agent
2. **multi-agent-rl-survey** -- arXiv paper (2602.11865) after training cutoff; partial mapping provided
3. **anthropic-building-skills-claude** -- PDF source inaccessible to researcher agent

These should be regenerated with web access in a future session if their content is needed.

---

## Methodology

Each dossier was generated by a dedicated researcher agent with access to the repository source code and documentation. Dossiers follow a standardized 10-section format: summary, orchestration model, tooling/execution, observability/evaluation, extensibility, notable practices for AGENT-33, risks/limitations, feature extraction, evidence links, and AGENT-33 adaptation analysis. Cross-cutting findings were synthesized by comparing practices, risks, and adaptations across all 30 dossiers.
