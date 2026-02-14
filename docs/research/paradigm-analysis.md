# Paradigm Analysis -- Research Sprint Findings

**Date:** 2026-02-14
**Basis:** 30 repository dossiers from `docs/research/repo_dossiers/`
**Scope:** Identify distinct paradigms, assess AGENT-33's position, define adaptation paths

---

## Executive Summary

The 30-repo research sprint reveals eight distinct paradigms for building intelligent agent systems. No single repo implements all eight -- each excels in one or two while ignoring others. AGENT-33's current architecture (DAG workflows, agent registry, code execution, training loop) places it firmly in the **governed orchestration** niche, but leaves it exposed in six areas where competitors have mature solutions. The critical insight: paradigms are converging. The next generation of agent frameworks will fuse conversational routing with governed workflows, RAG-native retrieval with document processing, and self-improvement loops with security hardening. AGENT-33 must assimilate selectively, not chase feature checklists.

---

## Paradigm 1: Conversational Agent Routing

### How It Works
Agents transfer control to each other dynamically during conversation, with the LLM deciding routing based on task descriptions rather than static DAGs. State passes explicitly via context variables. Handoffs are first-class primitives -- an agent returning another agent object triggers control transfer.

### Exemplar Repos
- **OpenAI Swarm** -- Minimal two-primitive design (`Agent` + handoffs). Stateless client-side loop with `context_variables` for state passing. Deprecated in favor of OpenAI Agents SDK but pattern remains influential.
- **Agent-Zero** -- Hierarchical subordinate spawning where every agent has a superior. Users are top-level supervisors. Subordinates report results back up the chain. Three-tier origin hierarchy (Default, User, Project).
- **OpenCode** -- Direct LLM-driven agent invocation with no explicit DAG. Primary/subagent model with `@mention` delegation. Wildcard-based permission system gates routing decisions.

### AGENT-33 Current Position
AGENT-33 uses **static DAG workflows** with explicit step definitions. No conversational routing exists. The orchestrator agent cannot dynamically decide which agent handles a subtask at runtime -- it follows a predefined workflow graph.

### Adaptation Path
1. Add an `invoke_agent_dynamic` workflow action where the orchestrator LLM selects the target agent from the registry based on task description (Phase 18 territory)
2. Implement Swarm-style `context_variables` as a mutable dict passed through workflow steps, complementing the existing expression evaluator
3. Keep DAG workflows as the governed path; add conversational routing as an optional "autonomous mode" gated by policy
4. Preserve auditability: log every routing decision with the LLM's reasoning, creating an implicit DAG from conversational flow

### Risks
- Implicit routing reduces observability (Claude Code's main weakness per the dossier)
- LLM routing decisions are non-deterministic -- same input may route differently across runs
- Without governance injection into prompts, the LLM has no awareness of which agents it should or should not invoke

---

## Paradigm 2: Tool-Augmented Agents

### How It Works
A primary agent has access to a rich tool ecosystem with tiered permissions. Tools range from read-only (file search, grep) through modification (edit, write) to execution (shell, browser). Permission systems gate tool access with deny-first defaults. Hooks intercept tool calls for governance enforcement. MCP (Model Context Protocol) provides standardized external tool connectivity.

### Exemplar Repos
- **Claude Code** -- Three-tier permission system (read/modify/execute), 14 lifecycle hook event types, MCP integration for external tools, deny-first defaults with pattern matching. 66.8k stars.
- **OpenCode** -- 16 built-in tools with wildcard-based permissions (allow/ask/deny per action). LSP integration for semantic code understanding. Plugin framework for custom tools.
- **GhidraMCP** -- MCP bridge wrapping Ghidra's reverse engineering tools. Demonstrates progressive capability exposure through layered abstraction (domain API -> HTTP -> MCP).
- **CC Workflow Studio** -- Visual workflow designer for tool orchestration across Claude Code, Copilot, and Codex. 11 node types with DAG validation.

### AGENT-33 Current Position
AGENT-33 has a tool framework (`tools/`) with registry, governance/allowlist enforcement, and four builtins (shell, file_ops, web_fetch, browser). Phase 12 added tool registry operations. Phase 13 added code execution. However: no tiered permissions (just global allowlist), no lifecycle hooks, no MCP integration, and governance constraints exist in code but never reach the LLM.

### Adaptation Path
1. **Phase 14 (immediate):** Implement three-tier permission model per Claude Code pattern. Tag each tool with `PermissionTier` enum (READ_ONLY, MODIFY, EXECUTE). Extend `AuthMiddleware` for session-scoped and persistent approvals.
2. **Phase 14:** Add `PreToolUse`/`PostToolUse` hooks with decision control (allow/deny/ask + input modification). This directly solves the governance-prompt disconnect.
3. **Phase 15-16:** Implement MCP client support for external tool connectivity. Default-deny all MCP tools; require explicit `mcp__` prefix in allowlists.
4. **Phase 18:** Add `ToolSearchTool` for on-demand tool loading when tool definitions exceed 8,000 tokens (from Claude Code pattern).

### Risks
- Bash command argument-based allowlisting is fragile (Claude Code docs explicitly warn about this)
- MCP servers are effectively untrusted code execution -- security burden shifts to users
- Tool permission patterns at scale need careful UX to avoid approval fatigue

---

## Paradigm 3: RAG-Native Intelligence

### How It Works
Retrieval-augmented generation with hybrid search (BM25 keyword + dense vector + knowledge graph), query rewriting for conversational context, configurable reranking pipelines, and multimodal document processing. Knowledge graphs capture entity relationships alongside vector embeddings for "vector-graph fusion" retrieval.

### Exemplar Repos
- **Tencent WeKnora** -- Enterprise RAG with BM25 + vector + Neo4j GraphRAG. Query rewriting, reranking, multi-tenant. Go backend + Python/FastAPI processing. 13k stars.
- **RAG-Anything** -- Multimodal RAG extending LightRAG. Five-stage pipeline: parse, analyze, extract, index, query. 1200-token chunks with 100-token overlap. Six retrieval modes. Dual-graph representation.
- **EdgeQuake** -- Rust reimplementation of LightRAG with Graph-RAG. 10x throughput over Python. PostgreSQL/pgvector/Apache AGE. Batch embedding (2048 for OpenAI, 512 for Ollama). HTTP client pooling. 11-crate architecture.
- **Memorizer** -- .NET MCP-based memory service with typed relationships, versioning, and semantic search.

### AGENT-33 Current Position
AGENT-33's RAG is **first-generation**: vector-only search via pgvector, no BM25, no reranking, no query rewriting, 500-char chunks (too small). `embeddings.py:36` processes sequentially (should batch for 67x speedup). `ollama.py` creates new httpx client per request instead of pooling.

### Adaptation Path
1. **Quick wins (any phase):** Batch embeddings, pool HTTP clients, increase chunk size to 1200 tokens with tokenizer-aware splitting
2. **Phase 16-17:** Add BM25 keyword search alongside vector search (PostgreSQL FTS or dedicated index). Implement weighted merge scoring.
3. **Phase 17:** Add query rewriting using LLM to expand context-dependent queries into standalone forms
4. **Phase 18+:** Add reranking pipeline (Jina/Cohere or local model). Consider knowledge graph extraction for entity-relationship retrieval.
5. **Long-term:** Adopt EdgeQuake's Glean pattern (optional second extraction pass, +18% recall) and entity normalization (-36-40% duplicates)

### Risks
- Knowledge graph construction is LLM-intensive (entity extraction per chunk)
- BM25 + vector hybrid requires careful weight tuning per domain
- Reranking adds latency to every query; must be optional/configurable

---

## Paradigm 4: Autonomous Self-Improvement

### How It Works
Training loops that capture agent rollouts, evaluate performance via LLM judges or automated metrics, optimize prompts/policies/weights, and schedule retraining. Multi-agent RL extends this to team-level optimization with credit assignment across cooperating agents.

### Exemplar Repos
- **AGENT-33 (itself)** -- Training subsystem with rollout capture, evaluation, optimization, and scheduling. Single-agent optimization with LLM-as-judge.
- **RLM** -- Recursive Language Models that decompose prompts through self-calls. LLM writes Python code to systematically break down inputs. Fine-tuned RLM-Qwen3-8B approaches GPT-5 on long-context benchmarks.
- **Multi-Agent RL Survey** -- Identifies gaps in AGENT-33: no multi-agent coordination signals, no team-level reward decomposition, no credit assignment across workflow agents, no cooperative dynamics modeling.
- **AI-Researcher** -- Iterative refinement cycles modeling academic mentorship. Implementations undergo multiple review-feedback-improvement loops. 93.8% completion rates on Scientist-Bench.

### AGENT-33 Current Position
AGENT-33 has the training subsystem infrastructure (Phase 4 runtime, `training/` module) but it is single-agent only. No multi-agent credit assignment, no team reward decomposition, no communication learning between agents. The governance-prompt disconnect means the training loop optimizes prompts that never actually govern agent behavior.

### Adaptation Path
1. **Fix governance-prompt disconnect first** -- training loop optimizes prompts that must actually reach the LLM
2. **Phase 17:** Implement debiased multi-evaluator assessment: multiple LLM judges, randomized presentation order, temperature=1.0 (from AI-Researcher pattern)
3. **Phase 19-20:** Add workflow-level reward decomposition: score individual agent contributions to workflow outcomes. Implement Shapley-value or attention-based credit assignment.
4. **Phase 20:** Add progressive experimental cycles: test policy changes on minimal data first, validate, then full deployment (AI-Researcher's prototype-validate-full-scale pattern)

### Risks
- Multi-agent RL is research-grade, not production-ready
- LLM-as-judge evaluation is biased toward verbosity and positional order
- Training loop without governance injection optimizes the wrong thing

---

## Paradigm 5: DevOps and Security Integration

### How It Works
Security scanning integrated into CI/CD pipelines. Vulnerability databases updated continuously. Policy enforcement via exit codes and admission controllers. Secret management with encrypted storage and rotation. SBOM generation and supply chain hardening.

### Exemplar Repos
- **Trivy** -- Comprehensive security scanner (vulns, misconfigs, secrets, SBOM, licenses). 24k stars. Deterministic multi-scanner pipeline. Rego/OPA policy enforcement. SARIF output for GitHub Security integration. Default scanner in Harbor, GitLab CI.
- **envhush-cli** -- Secrets management CLI (dossier incomplete, requires re-generation).
- **ZeroClaw** -- Security-first design: workspace sandboxing, command allowlisting, path traversal blocking, rate limiting, ChaCha20-Poly1305 encrypted secrets, gateway pairing with brute-force lockout.

### AGENT-33 Current Position
AGENT-33 has JWT/API-key auth, `AuthMiddleware`, encryption module, vault, permissions, and prompt injection detection. However: no supply chain scanning, no SBOM generation, no policy-as-code enforcement, no secret rotation, `API_SECRET_KEY` and `JWT_SECRET` default to `"change-me-in-production"` with warn-only check.

### Adaptation Path
1. **Phase 14 (immediate):** Integrate Trivy scanning into CI/CD for container image and dependency vulnerability detection. Add `.trivyignore` for known acceptable findings.
2. **Phase 14:** Implement recursive secret masking in logs (Agent-Zero pattern): `mask_recursive()` in structlog processor pipeline before persistence.
3. **Phase 14:** Upgrade default secrets from warn-only to fail-hard in production mode. Add secret rotation support.
4. **Phase 19:** Generate SBOM (CycloneDX/SPDX) for AGENT-33 releases. Add supply chain verification (Sigstore/Cosign).

### Risks
- Security scanning adds CI/CD latency
- False positives from vulnerability scanners cause alert fatigue
- Secret rotation in multi-tenant environment requires careful coordination

---

## Paradigm 6: Document and Media Processing

### How It Works
Multimodal pipelines that convert PDFs, images, tables, audio, and video into structured data for LLM consumption. Vision-language models process raw document images directly rather than OCR-then-parse. Modality-specific processors handle heterogeneous content types.

### Exemplar Repos
- **Sparrow** -- VLM-based document extraction. Feeds raw images to vision models with JSON schemas. Table detection via Microsoft table-transformer. Multi-page PDF auto-splitting. FastAPI serving.
- **PaddleOCR** -- Production OCR (50k stars). PP-OCRv5 (100+ languages, 70MB), PP-StructureV3 (document parsing to Markdown), MCP server integration. 94.5% accuracy.
- **yt-dlp** -- Media downloader for 1800+ sites. Three-phase pipeline (extract, download, post-process). Extensible extractor architecture. 80k stars.
- **RAG-Anything** -- Multimodal RAG with modality routing. Specialized processors for images, tables, equations, charts.

### AGENT-33 Current Position
AGENT-33 **cannot process PDFs or images**. `ReaderTool` is web-only. `FileOpsTool` handles UTF-8 text only. No OCR, no document parsing, no media extraction, no vision model integration.

### Adaptation Path
1. **Phase 18:** Add `DocumentProcessorTool` wrapping PaddleOCR's Python API for PDF/image text extraction. Use PP-StructureV3 for table/layout extraction.
2. **Phase 18:** Add `MediaExtractorTool` wrapping yt-dlp for audio/video content extraction (transcripts, metadata).
3. **Phase 18:** Extend memory ingestion pipeline to accept multimodal inputs: PDF -> extract text/tables -> chunk -> embed -> store.
4. **Long-term:** Integrate vision-language model for direct document understanding (Sparrow pattern) without OCR intermediate step.

### Risks
- OCR/VLM models are large (PaddleOCR server models ~2GB) and GPU-dependent
- Document processing quality varies dramatically by document type
- Media extraction from web sources has legal/ToS implications

---

## Paradigm 7: Zero-Overhead Native Agents

### How It Works
Agent frameworks built in systems languages (Rust, Go) for minimal resource consumption, fast startup, and compile-time safety. Trait-based pluggability allows swapping any subsystem without code changes. Custom implementations replace heavy dependencies (custom BM25+vector search instead of Elasticsearch, custom embeddings instead of LangChain).

### Exemplar Repos
- **ZeroClaw** -- Pure Rust agent (631K LoC). 8 core traits, 22+ LLM providers, SQLite-backed hybrid search (FTS5 BM25 + vector cosine), ChaCha20 encryption, multi-channel (CLI, Telegram, Discord, Slack, iMessage, Matrix). ~3.4MB binary, <10ms startup. 50-100x less memory than Node.js alternatives.
- **EdgeQuake** -- Rust Graph-RAG (130K LoC). 11 modular crates. 10x throughput over Python LightRAG. 200-400MB vs 2-4GB memory. True async concurrency via Tokio.

### AGENT-33 Current Position
AGENT-33 is Python/FastAPI. This is the correct choice for a framework prioritizing developer productivity, LLM ecosystem integration, and rapid iteration. Python's dominance in ML/AI tooling (PyTorch, transformers, sentence-transformers, Ollama bindings) makes it the pragmatic choice.

### Adaptation Path
AGENT-33 should **not** rewrite in Rust. Instead, selectively adopt patterns:
1. **Performance-critical paths:** Use Rust extensions via PyO3/maturin for embedding batch processing, vector similarity computation, and BM25 scoring (where EdgeQuake demonstrates 10x gains).
2. **Trait-based abstractions:** AGENT-33's provider abstractions (`BaseLLMProvider`, `BaseAdapter`) already mirror this pattern in Python. Strengthen the interface contracts.
3. **Hybrid search:** Implement ZeroClaw's BM25+vector weighted merge in Python first, profile, then optimize hot paths in Rust if needed.
4. **Resource discipline:** Pool HTTP clients (EdgeQuake pattern), batch embeddings (already identified), minimize per-request allocations.

### Risks
- Python-Rust interop adds build complexity and debugging difficulty
- Premature optimization before profiling wastes effort
- Rust rewrite temptation is a common distraction from feature delivery

---

## Paradigm 8: Skill and Plugin Ecosystems

### How It Works
Modular, portable capability units (skills, plugins, extensions) that extend agent functionality. Standardized formats (SKILL.md, plugin manifests, MCP servers) enable cross-platform distribution. Marketplace models aggregate community contributions. Progressive loading manages context budgets.

### Exemplar Repos
- **Awesome-Claude-Skills** -- 944+ Claude skills catalog. SKILL.md standard with YAML frontmatter. Composio integration for 500+ SaaS apps. 34.7k stars.
- **Claude Plugins Official** -- Anthropic's plugin architecture. Multi-type (slash commands, agents, skills, MCP, LSP, hooks). Manifest-based, namespace-isolated, scope-hierarchical.
- **Continuous-Claude-v3** -- 109 skills, 32 agents, 30 hooks. TLDR code analysis with 95% token savings. PostgreSQL+pgvector session persistence. Compound-don't-compact philosophy.
- **Trigger.dev** -- Background job platform with checkpoint-resume durable execution. Task coordination primitives. Build hooks and middleware for extensibility.
- **UI UX Pro Max** -- BM25-powered skill with CSV knowledge bases. Demonstrates passive knowledge retrieval pattern.

### AGENT-33 Current Position
AGENT-33 has 6 agent definitions in JSON, flat `agent_definitions_dir`, no skill format, no plugin architecture, no marketplace, no portable distribution. Workflow actions (`actions/`) are the closest analog to skills but are not user-extensible.

### Adaptation Path
1. **Phase 15:** Define AGENT-33 skill format (YAML frontmatter + markdown, compatible with SKILL.md standard). Support `scripts/`, `templates/`, `references/` subdirectories.
2. **Phase 15:** Implement skill discovery scanning hierarchical roots (system -> user -> project -> agent). Progressive loading: L0 metadata always, L1 body on activation, L2 resources on demand.
3. **Phase 18:** Add `SkillSearchTool` for on-demand skill discovery when catalog exceeds context budget.
4. **Phase 20:** Community contribution pipeline with validation, review automation, and version pinning.

### Risks
- Skill ecosystem requires critical mass of contributors to provide value
- Community-contributed skills are untrusted code (must run through CodeExecutor with sandbox)
- Versioning and dependency management gaps (no skill in the ecosystem has solved this well)

---

## Paradigm Convergence Map

The eight paradigms are not independent. They converge along four axes:

```
                    INTELLIGENCE AXIS
                         |
    Autonomous           |           RAG-Native
    Self-Improvement     |           Intelligence
    (RLM, AI-Researcher) |           (WeKnora, EdgeQuake)
                         |
  -------GOVERNANCE------+-------CAPABILITY-------
                         |
    DevOps & Security    |           Document & Media
    (Trivy, ZeroClaw)    |           Processing
                         |           (Sparrow, PaddleOCR)
                         |
                    EFFICIENCY AXIS
                         |
    Zero-Overhead         |           Skill/Plugin
    Native Agents        |           Ecosystems
    (ZeroClaw, EdgeQuake)|           (Claude Skills, Trigger.dev)
                         |
                         |
    Conversational       |           Tool-Augmented
    Routing              |           Agents
    (Swarm, Agent-Zero)  |           (Claude Code, OpenCode)
```

**Convergence points:**
- **Governed Conversational Routing** = Paradigms 1 + 2: Dynamic routing with permission-gated tool access (AGENT-33's target)
- **Intelligent Retrieval** = Paradigms 3 + 6: RAG that understands documents, not just text chunks (WeKnora + PaddleOCR)
- **Self-Improving Security** = Paradigms 4 + 5: Training loops that optimize security policies, not just prompts (novel -- no repo does this yet)
- **Portable Performance** = Paradigms 7 + 8: Skills distributed as optimized native extensions (ZeroClaw + Claude Skills pattern)

---

## Recommended Adoption Order

Priority ordering based on: (1) fixes critical gaps, (2) enables downstream paradigms, (3) effort-to-impact ratio.

| Priority | Paradigm | Rationale | Target Phase |
|----------|----------|-----------|--------------|
| **P0** | Tool-Augmented (tiered perms, hooks) | Fixes governance-prompt disconnect. Blocks all other paradigms. | Phase 14 |
| **P0** | RAG-Native (quick wins) | Batch embeddings, HTTP pooling, chunk size. Zero architectural change. | Phase 14-15 |
| **P1** | DevOps/Security (Trivy, secret masking) | Phase 14 is Security Hardening. Direct alignment. | Phase 14 |
| **P1** | Self-Improvement (fix training loop) | Training optimizes wrong thing until governance reaches LLM. | Phase 15-17 |
| **P2** | Skill/Plugin Ecosystem | Enables community contribution and agent reuse. | Phase 15-18 |
| **P2** | RAG-Native (BM25, reranking, graph) | Major intelligence upgrade. Requires Phase 14 foundation. | Phase 16-17 |
| **P3** | Conversational Routing | Optional autonomous mode. Requires mature governance. | Phase 18 |
| **P3** | Document/Media Processing | Expands input modalities. Independent of core architecture. | Phase 18+ |
| **P4** | Zero-Overhead (selective Rust) | Performance optimization. Only after profiling reveals bottlenecks. | Phase 19-20 |

---

## Cross-Cutting Finding: The Governance-Prompt Disconnect

The single most important finding across all 30 dossiers: **governance constraints that exist only in code but never reach the LLM are security theater.** This is not unique to AGENT-33 -- Claude Code, Awesome-Claude-Skills, and OpenCode all exhibit the same pattern. Agent-Zero is the clearest counter-example, demonstrating that all behavioral constraints must live in prompt files composed into the system message.

Every paradigm adoption in this document assumes Phase 14 fixes the governance-prompt disconnect as its first deliverable. Without this fix:
- Tool permissions are bypassed if the LLM is tricked into ignoring runtime restrictions
- Training loop optimizes prompts that never govern behavior
- Conversational routing has no guardrails
- Skills/plugins inherit the same gap

**Evidence sources:** agent-zero.md (section 6 item 1), anthropic-claude-code.md (section 7 item 1), awesome-claude-skills.md (section 7 item 1), system-prompts-ai-tools.md (section 6 -- production AI tools all inject safety rules into system prompts).
