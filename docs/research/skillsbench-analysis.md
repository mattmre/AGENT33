# SkillsBench vs AGENT-33: Comprehensive Capability Analysis

**Date**: 2026-02-14
**SkillsBench repo**: benchflow-ai/skillsbench
**AGENT-33 branch**: feat/sessions-10-12-zeroclaw-parity-integration-wiring
**AGENT-33 state**: 21 phases complete, ~973 tests, 0 lint errors
**Author**: Documentation Agent (automated analysis)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Philosophical Alignment](#2-philosophical-alignment)
3. [Feature-by-Feature Comparison Matrix](#3-feature-by-feature-comparison-matrix)
4. [What AGENT-33 Should Absorb (Prioritized)](#4-what-agent-33-should-absorb-prioritized)
5. [What AGENT-33 Already Does Better](#5-what-agent-33-already-does-better)
6. [Anti-Patterns to Avoid](#6-anti-patterns-to-avoid)
7. [Adaptation Strategy: Evolutionary Integration](#7-adaptation-strategy-evolutionary-integration)
8. [Concrete Implementation Roadmap](#8-concrete-implementation-roadmap)
9. [Security Considerations for Adaptation](#9-security-considerations-for-adaptation)
10. [Benchmark Performance Predictions](#10-benchmark-performance-predictions)

---

## 1. Executive Summary

### SkillsBench

SkillsBench is the first benchmark framework specifically designed to evaluate how well AI agents
use **skills** -- modular folders of instructions, scripts, and resources that augment an agent's
capabilities at runtime. Built on the Harbor framework, it contains **86 tasks** across **62+
categories** spanning financial analysis, scientific computing, security/CVE analysis, document
processing, software engineering, control systems, ML/AI, media processing, and more.

SkillsBench is not an agent framework. It is an **evaluation framework** that tests any agent's
ability to discover, select, load, and apply skills to concrete tasks. Its most sophisticated
component is the **Terminus-2** agent, which implements a 4-stage hybrid skill matching pipeline
(BM25 + vector retrieval, LLM lenient selection, content loading, LLM strict filtering) and an
iterative tool-use loop with context window management.

The benchmark uses **binary reward** (0 or 1 -- all pytest tests must pass), runs **5 trials** per
task/agent/model combination, and measures **skills impact** as the pass-rate delta between
with-skills and without-skills runs. This deterministic, pytest-based evaluation avoids the
subjectivity problems inherent in LLM-as-judge approaches.

### AGENT-33

AGENT-33 is a **multi-agent orchestration framework** with a Python/FastAPI runtime engine, a
governance layer, evidence capture, and session-spanning workflows. It contains 21 completed
development phases, 15+ subsystems, and ~973 passing tests. Key architectural differentiators
include:

- **Multi-agent DAG orchestration** with 10 action types (invoke-agent, run-command, validate,
  transform, conditional, parallel-group, wait, execute-code)
- **Progressive disclosure skill system** with L0/L1/L2 layers, SKILL.md/YAML loading,
  SkillRegistry, and SkillInjector wired into AgentRuntime
- **Hybrid RAG pipeline** (BM25 + vector via Reciprocal Rank Fusion) with embedding cache,
  token-aware chunking, and progressive recall
- **Enterprise infrastructure**: PostgreSQL + pgvector, Redis, NATS, multi-tenancy, JWT/API-key
  auth, rate limiting, encryption, autonomy levels
- **Lifecycle management**: review automation, release management, autonomy budgets, evaluation
  gates, continuous improvement, observability with failure taxonomy

### Analysis Goal

This document provides a deep structural comparison between SkillsBench and AGENT-33 to answer
three questions:

1. **What can AGENT-33 absorb from SkillsBench** to improve its agents' skill-use effectiveness
   and introduce rigorous, deterministic evaluation?
2. **What does AGENT-33 already do better** than SkillsBench's Terminus-2 agent and how should
   those strengths be preserved?
3. **How should integration proceed** without compromising AGENT-33's multi-agent identity or
   introducing architectural anti-patterns?

The core finding is that SkillsBench and AGENT-33 are **complementary, not competitive**. SkillsBench
tests what AGENT-33 builds. The optimal path is to make AGENT-33 agents runnable against
SkillsBench tasks, absorb SkillsBench's skill matching refinements, and use benchmark results as a
feedback loop into AGENT-33's existing continuous improvement system.

---

## 2. Philosophical Alignment

### 2.1 Shared Principles

SkillsBench and AGENT-33 share several foundational design choices, making integration natural
rather than forced.

#### Progressive Disclosure of Skills

Both systems implement a progressive disclosure model for skills -- showing agents minimal metadata
first, then loading full content only when needed, to stay within context budgets.

| Disclosure Layer | SkillsBench / Terminus-2 | AGENT-33 |
|-----------------|--------------------------|----------|
| **L0: Index** | Skill name + description in system prompt; skill index built at startup | `SkillInjector.build_skill_metadata_block()` -- name + description for all available skills |
| **L1: Instructions** | Full SKILL.md loaded via XML/JSON tool call (`Read Skill` tool) | `SkillInjector.build_skill_instructions_block()` -- full instructions + governance metadata |
| **L2: Resources** | References loaded on demand via tool call | `SkillRegistry.get_resource()` -- file content loaded from bundled resource path |

Both systems use SKILL.md with YAML frontmatter as the canonical skill format. This is not a
coincidence -- it reflects the Anthropic standard for skill definitions. The alignment means
AGENT-33 can load SkillsBench skill folders natively with minimal adapter work.

#### Hybrid Search (BM25 + Vector)

Both systems combine keyword (BM25) and semantic (vector) retrieval for skill/memory search:

| Component | SkillsBench / Terminus-2 | AGENT-33 |
|-----------|--------------------------|----------|
| **BM25 engine** | `rank-bm25` Python library | Custom `BM25Index` class (`memory/bm25.py`) with Okapi BM25 |
| **Vector engine** | `sentence-transformers` (BAAI/bge-small-en-v1.5) | `EmbeddingProvider` via Ollama/Jina + pgvector cosine distance |
| **Fusion method** | Reciprocal Rank Fusion (k=60) | Reciprocal Rank Fusion (k=60, configurable) |
| **Fusion weights** | Vector 0.7 / BM25 0.3 (default) | Vector 0.7 / BM25 0.3 (configurable via `rag_vector_weight`) |
| **Candidate pool** | Top 50 from fusion | `top_k * 3` from each source |

The RRF parameters are effectively identical. This is because both implementations reference the
same Cormack et al. 2009 paper establishing k=60 as the standard constant.

#### Deterministic Testing over LLM-as-Judge

Both systems reject LLM-as-judge evaluation in favor of deterministic, code-based testing:

- **SkillsBench**: Binary reward via `pytest test_outputs.py` -- all tests must pass for a reward
  of 1. No subjective scoring.
- **AGENT-33**: Golden tasks (GT-01..GT-07) with concrete checks, gate thresholds with specific
  operators (GTE, LTE), regression detection (RI-01..RI-05) with triage. Evaluation suite runs
  actual test assertions, not LLM judgment calls.

This alignment is important because it means AGENT-33's evaluation harness can be extended to
consume SkillsBench's test format without philosophical friction.

### 2.2 Complementary Roles

The fundamental relationship between these systems is that **SkillsBench tests what AGENT-33
builds**:

```
+-----------------------+     produces     +---------------------+
|                       | ──────────────► |                     |
|    AGENT-33           |                  |  Skilled Agents     |
|    (orchestration     |   agents with    |  (runtime agents    |
|     framework)        |   skill system   |   using skills)     |
|                       |                  |                     |
+-----------------------+                  +----------+----------+
                                                      |
                                              evaluated by
                                                      |
                                                      v
                                           +----------+----------+
                                           |                     |
                                           |    SkillsBench      |
                                           |    (evaluation      |
                                           |     framework)      |
                                           |                     |
                                           +---------------------+
```

AGENT-33 is a **builder** -- it provides the runtime, orchestration, memory, and skill injection
that agents need. SkillsBench is an **evaluator** -- it provides the tasks, metrics, and scoring
that measure how well those agents perform. Neither replaces the other.

### 2.3 Key Philosophical Differences

| Dimension | SkillsBench | AGENT-33 |
|-----------|-------------|----------|
| **Agent model** | Single-agent with iterative tool-use loop | Multi-agent DAGs with role specialization |
| **Execution model** | Docker containers, ephemeral per-task | Long-running server, persistent state |
| **Skill matching** | 4-stage pipeline with LLM refinement | 2-stage pipeline (BM25 + vector only) |
| **Context management** | Message unwinding, handoff summaries | Progressive recall with 3 detail levels |
| **Result format** | Binary (0/1), pass/fail per task | Multi-metric (M-01..M-05), gate thresholds |
| **Scope** | Evaluation and benchmarking | Full lifecycle from development to production |
| **Tenancy** | Single-user, local execution | Multi-tenant, API-key/JWT scoped |

---

## 3. Feature-by-Feature Comparison Matrix

### 3.1 Skill System

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Skill format** | SKILL.md (YAML frontmatter + markdown body), skill.yaml | SKILL.md (YAML frontmatter + markdown body) | Full parity. Both follow Anthropic standard. | -- |
| **Skill directory structure** | `SKILL.md`, `scripts/`, `templates/`, `references/` auto-discovered by `load_from_directory()` | `SKILL.md`, `scripts/`, `references/`, `assets/` copied to agent paths at Docker build time | Minor difference: AGENT-33 uses `templates/` where SkillsBench uses `assets/`. Add `assets/` discovery. | P3 |
| **Skill registry** | `SkillRegistry` with discover, register, get, remove, search, find_by_tag, find_by_tool | Index built at startup by Terminus-2 agent; no persistent registry | AGENT-33's is richer (CRUD, tagging, tool filtering). Preserve. | -- |
| **Progressive disclosure** | L0 (metadata), L1 (instructions), L2 (resources) via `SkillInjector` + `SkillRegistry` | L0 (metadata in system prompt), L1 (full SKILL.md via tool call), L2 (references via tool call) | Parity in concept. SkillsBench uses tool calls for L1/L2; AGENT-33 injects directly. | -- |
| **Skill matching** | Text search across name/description/tags (`SkillRegistry.search()`) | 4-stage hybrid pipeline: BM25+vector -> LLM lenient -> content load -> LLM strict | **Major gap.** AGENT-33 lacks LLM-based refinement stages 2 and 4. | **P0** |
| **Skill matching candidates** | All matching skills returned | Stage 1: top 50 via RRF. Stage 2: LLM narrows to 10-12. Stage 3: loads 3,000 chars/skill. Stage 4: LLM narrows to 3-6. | AGENT-33 has no staged narrowing with quality filtering. | **P0** |
| **Answer leakage prevention** | Not implemented | Skill content is screened during LLM selection to prevent the model from extracting direct answers from skill metadata | **Gap.** Important for benchmark integrity and production security. | P1 |
| **Skill quality validation** | No automated validation | Quality Checker contrib agent with 12-criterion analysis | **Gap.** Useful for skill catalog governance. | P2 |
| **Skill definition model** | `SkillDefinition` Pydantic model with 20+ fields: name, version, description, instructions, allowed_tools, disallowed_tools, tool_parameter_defaults, invocation_mode, execution_context, autonomy_level, approval_required_for, scripts_dir, templates_dir, references, tags, author, status, dependencies, schema_version, base_path | Lighter model: name, description, version, tags in frontmatter; body is instructions | AGENT-33's model is significantly richer with governance fields. Preserve. | -- |
| **Skill governance** | `SkillInvocationMode` (user-only, llm-only, both), `SkillExecutionContext` (inline, fork), autonomy_level override, approval requirements | No governance layer | AGENT-33 advantage. Skills can restrict tool access, require approval, override autonomy. | -- |
| **Tool context resolution** | `SkillInjector.resolve_tool_context()` merges skill tool restrictions into agent's ToolContext | No tool access control per skill | AGENT-33 advantage. | -- |
| **Skill dependencies** | `SkillDependency` model (name, kind, optional) | No dependency management | AGENT-33 advantage. | -- |
| **Skill lifecycle** | `SkillStatus` enum (active, deprecated, experimental) | No lifecycle management | AGENT-33 advantage. | -- |

### 3.2 Memory / Search

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Vector embeddings** | `EmbeddingProvider` via Ollama/Jina, `embed()` and `embed_batch()` | `sentence-transformers` with BAAI/bge-small-en-v1.5 | Different providers, same concept. AGENT-33 supports batch. | -- |
| **Embedding cache** | `EmbeddingCache` with LRU, SHA-256 keys, thread-safe via asyncio.Lock, hit/miss tracking, batch support | No caching observed | AGENT-33 advantage. | -- |
| **BM25 index** | Custom `BM25Index` with Okapi BM25, stop-word removal, add_document/add_documents, search | `rank-bm25` library (external dependency) | AGENT-33 has zero-dependency custom implementation. SkillsBench uses proven library. Trade-off. | -- |
| **Hybrid search** | `HybridSearcher` with configurable weights, RRF fusion (k=60), vector_rank/bm25_rank tracking | RRF fusion (k=60) in Stage 1 of 4-stage pipeline | Parity at Stage 1. AGENT-33 lacks Stages 2-4. | **P0** |
| **RRF constant** | Configurable (`rrf_k` parameter, default 60) | Fixed k=60 | AGENT-33 is more flexible. | -- |
| **Fusion weights** | Configurable (`vector_weight`, default 0.7) | Fixed 0.7/0.3 | AGENT-33 is more flexible. | -- |
| **RAG pipeline** | `RAGPipeline` with vector-only and hybrid modes, similarity threshold, augmented prompt formatting | No standalone RAG pipeline (skill matching is the retrieval layer) | AGENT-33 advantage. RAG is general-purpose, not skill-specific. | -- |
| **Token-aware chunking** | `TokenAwareChunker` with configurable chunk_tokens (1200), overlap_tokens (100), sentence boundary preservation, markdown support | No chunking (skills are loaded as-is; Terminus-2 truncates to 3,000 chars per skill in Stage 3) | AGENT-33 advantage. Proper chunking produces better embeddings. | -- |
| **Progressive recall** | `ProgressiveRecall` with 3 layers: index (~50 tokens), timeline (~200 tokens), full (~1000 tokens) | No progressive recall; all context loaded at once or truncated | AGENT-33 advantage. ~10x token savings. | -- |
| **Long-term storage** | PostgreSQL + pgvector, multi-tenant, persistent | No persistent memory (evaluation is stateless per task) | Different paradigms. AGENT-33 is production-grade. | -- |
| **Short-term buffer** | `ShortTermMemory` in-memory buffer | Agent loop maintains message history | Both have working short-term context. | -- |
| **Session state** | `SessionState` with persistence | No session concept (each task run is independent) | AGENT-33 advantage for production use. | -- |
| **Memory retention** | Tiered policies (hot/warm/cold), 7d-permanent, per-artifact-type | No retention (ephemeral) | AGENT-33 advantage. | -- |

### 3.3 Tool System

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Tool protocol** | `Tool` protocol with name, description, execute; `SchemaAwareTool` with `parameters_schema` property | XML/JSON tool calls parsed from LLM response (Bash, Read File, Write File, Read Skill, List Files) | Different architectures. AGENT-33 has formal protocol; SkillsBench parses free-form tool calls. | -- |
| **JSON Schema validation** | `validate_params()` using `jsonschema.Draft7Validator`, `validated_execute()` wrapper | No schema validation on tool inputs | AGENT-33 advantage. | -- |
| **Tool descriptions for LLM** | `generate_tool_description()` produces OpenAI-style function schema | Tools defined in system prompt as XML/JSON format instructions | Both expose tools to LLMs differently. AGENT-33's approach is more structured. | -- |
| **Governance/allowlist** | Tool allowlist/denylist enforcement, command validation (pipe/chain/subshell blocking) | Container isolation (Docker) provides boundary | Different security models. Both effective. | -- |
| **Built-in tools** | shell, file_ops, web_fetch, browser | Bash, Read File, Write File, Read Skill, List Files | Similar core set. AGENT-33 has web_fetch and browser; SkillsBench has specialized Read Skill. | -- |
| **Tool-use loop** | Single LLM call with structured output parsing | Iterative loop: LLM response -> parse tool calls -> execute -> capture output -> append to history -> loop | **Gap.** AGENT-33's AgentRuntime does a single LLM call. No iterative tool-use loop. | **P0** |
| **Tool call parsing** | JSON output parsing (`_parse_output()`) | XML and JSON format parsing with regex fallback | SkillsBench supports both formats. AGENT-33 only parses JSON output. | P2 |

### 3.4 Agent Architecture

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Agent model** | Multi-agent with 6 role types (orchestrator, director, worker, qa, researcher, browser-agent), AgentDefinition with 20+ fields | Single Terminus-2 agent with iterative loop | AGENT-33 advantage. Multi-agent DAGs are the core differentiator. | -- |
| **System prompt construction** | `_build_system_prompt()` with identity, capabilities, governance, autonomy, ownership, dependencies, I/O, constraints, safety rules, output format | System prompt with task instruction, skill index, tool definitions, context window budget | Both construct structured system prompts. AGENT-33 includes governance; SkillsBench includes skill index. | -- |
| **Context window management** | Not implemented beyond progressive recall | Message unwinding (removing oldest messages when near limit), handoff summaries (summarizing conversation before handoff), proactive summarization when tokens low | **Major gap.** AGENT-33 lacks context window management strategies. | **P0** |
| **Task completion confirmation** | Single response, parsed as JSON | Double-confirmation: agent must confirm task completion explicitly before the loop ends | **Gap.** Reduces false-positive completions. | **P0** |
| **Agent invocation** | `AgentRuntime.invoke()` -> single LLM call -> parse output -> return `AgentResult` | Iterative loop: construct prompt -> LLM call -> parse tool calls -> execute tools -> capture output -> append to messages -> repeat until done | **Major gap.** AGENT-33 agents do not have an iterative tool-use loop. They make a single LLM call. | **P0** |
| **Retry logic** | `max_retries` from `AgentConstraints` (retry on LLM call failure) | Loop continues until task complete or max iterations reached | Different retry semantics. AGENT-33 retries failed API calls; SkillsBench retries the whole task. | -- |
| **Capability taxonomy** | 25 entries across P/I/V/R/X categories in `agents/capabilities.py` | No capability taxonomy | AGENT-33 advantage. | -- |
| **Agent definitions** | 6 JSON files auto-discovered from `agent_definitions_dir` | Single agent defined in code | AGENT-33 advantage. Declarative, extensible. | -- |
| **Observation capture** | `ObservationCapture` records LLM responses as observations | Token/cost tracking via LiteLLM | Different focus. AGENT-33 captures for memory; SkillsBench captures for cost analysis. | -- |
| **Trace emission** | Trace spans emitted via `trace_emitter` | No tracing | AGENT-33 advantage. | -- |

### 3.5 Evaluation / Testing

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Golden tasks** | GT-01..GT-07 (doc update, queue update, cross-ref validation, template instantiation, scope lock, evidence capture, multi-file update) | 86 tasks across 62+ categories (financial, scientific, security, document, engineering, control, ML, media, planning, manufacturing, formal methods) | SkillsBench has vastly more diverse tasks. AGENT-33's golden tasks are governance-focused. | P1 |
| **Task format** | `GoldenTaskDef` Pydantic model with task_id, name, description, tags, owner, checks | `instruction.md` + `task.toml` (metadata) + `environment/` (Dockerfile + skills) + `solution/` (oracle) + `tests/` (pytest) | SkillsBench format is more complete: includes environment, oracle, and tests per task. | P1 |
| **Scoring** | Multi-metric: M-01 (Success Rate), M-02 (Time-to-Green), M-03 (Rework Rate), M-04 (Diff Size), M-05 (Scope Adherence) | Binary reward (0 or 1) per task; skills impact = pass_rate_with - pass_rate_without | Different approaches. AGENT-33 is richer but harder to aggregate. | -- |
| **Multi-trial evaluation** | Single run per evaluation | 5 trials per task/agent/model combination to account for LLM non-determinism | **Gap.** AGENT-33 should run multiple trials and report variance. | P1 |
| **Regression detection** | RI-01..RI-05 indicators, `RegressionRecorder` with triage | No regression detection (point-in-time benchmark) | AGENT-33 advantage. | -- |
| **Gate enforcement** | 4 gate types (G-PR, G-MRG, G-REL, G-MON) with 8 default thresholds | No gates (benchmark only, no enforcement) | AGENT-33 advantage. | -- |
| **Baseline comparison** | `BaselineSnapshot` with commit hash, branch, metrics, task results | Experiment configs comparing with/without skills across agents/models | Different comparison models. Both valid. | -- |
| **Result format** | Custom Pydantic models (`EvaluationRun`, `GateReport`, `TaskRunResult`) | CTRF (Common Test Results Format) + reward.txt | **Gap.** AGENT-33 should support CTRF for interoperability. | P1 |
| **Oracle / reference solution** | No oracle solutions | Each task has `solution/solve.sh` -- a shell script that solves the task deterministically | **Gap.** Oracle solutions enable validating test correctness. | P2 |
| **Experiment configs** | No experiment configuration system | YAML-driven configs: oracle, claude with/without skills, codex with/without skills | **Gap.** Batch evaluation configuration would improve AGENT-33's eval workflow. | P2 |
| **Failure mode tracking** | `FailureCategory` enum (F-ENV..F-UNK) with severity, retryability, escalation metadata | Failure mode enum tracking (not detailed in public docs) | Both track failure modes. AGENT-33's is more detailed with 10 categories. | -- |
| **CI integration** | No CI evaluation pipeline | GitHub Actions runs oracle for every task on PR; automated PR review with 5-config benchmark | **Gap.** AGENT-33 should integrate evaluation into CI. | P2 |
| **Metrics dashboard** | No dashboard | React + TypeScript + Recharts dashboard for visualizing agent performance | **Gap.** Visualization would improve iteration speed. | P2 |

### 3.6 Security

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Authentication** | JWT + API key, multi-tenant, AuthMiddleware | API key management via env vars + direnv | AGENT-33 advantage. | -- |
| **Authorization** | Deny-first permission evaluation, 8 scopes, tenant isolation | No authorization model | AGENT-33 advantage. | -- |
| **Execution isolation** | Subprocess sandbox with `SandboxConfig` (timeout, memory, CPU, filesystem, network, process limits) | Docker containers with resource limits per task | SkillsBench uses stronger isolation (full containerization). | P2 |
| **Answer leakage prevention** | Not implemented | Skill selection pipeline screens for answer leakage during LLM-based filtering stages | **Gap.** Relevant for both evaluation integrity and production prompt injection defense. | P1 |
| **API key management** | `SecretStr` for sensitive config, env var loading | env vars + direnv, per-provider key isolation | Both use env vars. AGENT-33 has Pydantic SecretStr protection. | -- |
| **Command validation** | Multi-segment validation (pipe/chain/subshell blocking), autonomy levels (ReadOnly/Supervised/Full) | Container boundary prevents unauthorized commands | Different approaches, both effective. | -- |
| **Rate limiting** | Sliding-window + burst, per-subject | No rate limiting (benchmarks run sequentially) | AGENT-33 advantage (production concern, not evaluation concern). | -- |
| **Path traversal** | Null byte detection, `..` blocking, symlink resolution, `relative_to()` checks | Docker filesystem isolation | AGENT-33 has explicit checks; SkillsBench relies on container boundary. | -- |
| **Prompt injection detection** | Dedicated detection module | AI detection for human-written instructions (quality assurance, not injection defense) | AGENT-33 advantage for production; SkillsBench has novel AI detection for skill authorship. | -- |
| **Skill validation as security gate** | No automated skill validation pipeline | 12-criterion Quality Checker validates skills before use | **Gap.** Skill validation prevents malicious or low-quality skills from entering the system. | P1 |
| **Brute-force lockout** | Pairing brute-force lockout | N/A | AGENT-33 advantage. | -- |
| **Request size limits** | `RequestSizeLimitMiddleware` | N/A (no HTTP API) | AGENT-33 advantage. | -- |
| **Encryption** | ChaCha20 via vault | N/A | AGENT-33 advantage. | -- |

### 3.7 Workflow / Orchestration

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Workflow engine** | DAG-based engine with topological sort, step executor, retries, timeouts, expression evaluator, state machine, checkpoint persistence | No workflow engine. Terminus-2 is an iterative loop, not a workflow. | AGENT-33 advantage. This is a core differentiator. | -- |
| **Step actions** | 8 action types: invoke-agent, run-command, validate, transform, conditional, parallel-group, wait, execute-code | Tool calls only: Bash, Read/Write File, Read Skill, List Files | AGENT-33 has structured workflow actions; SkillsBench has free-form tool calls. | -- |
| **Execution modes** | Sequential, parallel, dependency-aware | Sequential only (single agent loop) | AGENT-33 advantage. | -- |
| **Trigger events** | session-start, session-end, artifact-created, review-complete, webhook, schedule | Docker container startup per task | AGENT-33 advantage. | -- |
| **Agent-workflow bridge** | `_register_agent_runtime_bridge()` wires AgentRuntime into workflow executor with skill_injector and progressive_recall | No bridge concept (single agent) | AGENT-33 advantage. | -- |
| **Multi-agent coordination** | 6 agent definitions with role-based specialization, dependency declarations | No multi-agent support | AGENT-33's primary differentiator. | -- |
| **Checkpoint persistence** | Workflow checkpoints for resume after failure | No persistence (task runs are ephemeral) | AGENT-33 advantage. | -- |

### 3.8 Providers / Models

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Provider catalog** | 22+ providers in `PROVIDER_CATALOG` with ProviderInfo dataclass | LiteLLM for unified multi-provider routing | Different approaches. AGENT-33 has explicit catalog; SkillsBench uses LiteLLM proxy. | P1 |
| **Auto-registration** | `auto_register()` scans env vars, creates OpenAIProvider for each configured provider | LiteLLM handles provider detection automatically | Both auto-configure from env. LiteLLM is more battle-tested. | P1 |
| **Model routing** | `ModelRouter` with prefix-based routing (e.g., `gpt-` -> openai, `claude-` -> anthropic) | LiteLLM model routing | Both have routing. LiteLLM supports more edge cases. | P1 |
| **Token/cost tracking** | `tokens_used` in `AgentResult`, observation capture | LiteLLM integration for per-call cost tracking across all providers | **Gap.** AGENT-33 tracks tokens but not costs. LiteLLM provides cost data. | P1 |
| **Supported models** | All OpenAI-compatible providers via auto-registration + Ollama + AirLLM | Claude Opus 4.5/Sonnet 4.5/Haiku 4.5, GPT-5.2, Gemini 3 Flash/Pro | AGENT-33 supports more providers; SkillsBench has tested on specific frontier models. | -- |
| **Embedding models** | Ollama-based (`nomic-embed-text`, configurable), Jina alternative | BAAI/bge-small-en-v1.5 via sentence-transformers | Different embedding models. Both work for their use cases. | -- |
| **Connection pooling** | httpx.AsyncClient with configurable limits | LiteLLM handles connection management | Both handle pooling. | -- |
| **Retry with backoff** | Exponential backoff on LLM call failure | LiteLLM retry configuration | Both have retry logic. | -- |

### 3.9 Observability

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Trace pipeline** | TraceRecord, TraceStep, TraceAction with 6 statuses, 9 artifact types, TRC-timestamp IDs, TraceCollector | No tracing infrastructure | AGENT-33 advantage. | -- |
| **Failure taxonomy** | 10 categories (F-ENV..F-UNK), 4 severity levels, retryable/escalation metadata, `FailureRecord.from_exception()` | Failure mode enum (less detailed) | AGENT-33 advantage. More categories, richer metadata. | -- |
| **Retention policies** | 9 artifact types, tiered storage (hot/warm/cold), 7d-permanent configurable | No retention (ephemeral) | AGENT-33 advantage. | -- |
| **Structured logging** | structlog throughout | Standard Python logging | AGENT-33 advantage. | -- |
| **Metrics** | IM-01..IM-05 improvement metrics with trend computation (improving/stable/declining) | CTRF result format + per-task reward + aggregate pass rates | Different metrics. AGENT-33 tracks trends; SkillsBench tracks point-in-time results. | -- |
| **Alerting** | Alert rules in observability subsystem | No alerting | AGENT-33 advantage. | -- |
| **API endpoints** | 7 trace endpoints under `/v1/traces` | Metrics dashboard (React) | Different interfaces. AGENT-33 has API; SkillsBench has UI. | P2 |

### 3.10 Configuration

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Config system** | Pydantic Settings with `env_prefix=""`, loads from `.env`, typed fields with defaults | Python dataclasses + env vars + direnv | Both use env-based config. AGENT-33's is more structured. | -- |
| **Experiment configs** | No experiment configuration | YAML files defining agent/model/skill combinations for batch evaluation | **Gap.** Would improve AGENT-33's evaluation workflow. | P2 |
| **Sensitive values** | `SecretStr` for all API keys, encryption keys, JWT secrets | Env vars via direnv | AGENT-33 advantage. SecretStr prevents accidental logging. | -- |
| **Production safety** | `check_production_secrets()` warns about insecure defaults at startup | N/A (not a production system) | AGENT-33 advantage. | -- |
| **Docker Compose** | Full compose file with postgres, redis, nats, ollama | Harbor framework for container orchestration | Both use containerization. Different orchestrators. | -- |

### 3.11 Contrib / Development Tooling

| Feature | AGENT-33 Status | SkillsBench Approach | Gap / Opportunity | Priority |
|---------|----------------|---------------------|-------------------|----------|
| **Task creation** | No automated task creation | Task Wizard contrib agent creates new benchmark tasks | **Gap.** Would accelerate evaluation suite expansion. | P3 |
| **Quality checking** | No automated quality checking for skills/tasks | Quality Checker with 12-criterion analysis | **Gap.** | P2 |
| **Result auditing** | No automated result auditing | Result Auditor reviews benchmark results for anomalies | **Gap.** | P3 |
| **PR review automation** | Review automation module (Phase 15) with risk assessment, reviewer assignment, signoff state machine | PR Reviewer runs automated 5-config benchmark on PRs | Different focus. AGENT-33 reviews code changes; SkillsBench reviews benchmark results. | -- |
| **Skill finder** | `SkillRegistry.search()` with text search | Skill Finder contrib agent discovers relevant skills | Both have skill search. SkillsBench's is LLM-powered. | P2 |
| **Policy checking** | Security policies enforced at runtime | Policy Checker validates compliance | Both enforce policies. Different mechanisms. | -- |

---

## 4. What AGENT-33 Should Absorb (Prioritized)

### Critical (P0) -- Features that directly improve AGENT-33's competitive performance

#### 4.1. Iterative Tool-Use Loop for AgentRuntime

**Current state**: `AgentRuntime.invoke()` makes a single LLM call, parses the output as JSON, and
returns an `AgentResult`. The agent cannot use tools, observe results, and iterate.

**SkillsBench approach**: Terminus-2 implements a full iterative loop:

```
while not done:
    response = llm.call(messages)
    tool_calls = parse_tool_calls(response)
    if tool_calls:
        for call in tool_calls:
            result = execute_tool(call)
            messages.append(tool_result(result))
    elif is_task_complete(response):
        if double_confirm(response):
            done = True
    else:
        messages.append(assistant_message(response))
```

**Why this is P0**: Without an iterative tool-use loop, AGENT-33 agents cannot interact with their
environment. They receive inputs, call an LLM once, and return a response. This fundamentally
limits what agents can accomplish. Every SkillsBench task requires multiple tool calls to complete.

**Implementation sketch**:

```python
# engine/src/agent33/agents/runtime.py -- enhanced invoke method

async def invoke_iterative(
    self, inputs: dict[str, Any], max_iterations: int = 20
) -> AgentResult:
    """Run the agent in an iterative tool-use loop."""
    system_prompt = self._build_full_system_prompt(inputs)
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=json.dumps(inputs, indent=2)),
    ]

    total_tokens = 0
    for iteration in range(max_iterations):
        response = await self._router.complete(
            messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._definition.constraints.max_tokens,
        )
        total_tokens += response.total_tokens

        tool_calls = self._parse_tool_calls(response.content)
        if tool_calls:
            messages.append(ChatMessage(role="assistant", content=response.content))
            for call in tool_calls:
                result = await self._execute_tool(call)
                messages.append(ChatMessage(role="tool", content=result))
        elif self._is_task_complete(response.content):
            if self._double_confirm or iteration > 0:
                output = _parse_output(response.content, self._definition)
                return AgentResult(
                    output=output,
                    raw_response=response.content,
                    tokens_used=total_tokens,
                    model=response.model,
                )
        else:
            messages.append(ChatMessage(role="assistant", content=response.content))

        # Context window management
        messages = self._manage_context_window(messages)

    raise RuntimeError(f"Agent '{self._definition.name}' reached max iterations")
```

**Effort**: 3 days (includes tool call parsing, execution, context management).

#### 4.2. 4-Stage Hybrid Skill Matching Pipeline

**Current state**: `SkillRegistry.search()` does simple text matching across name, description, and
tags. The `HybridSearcher` does BM25 + vector retrieval for memory, but this is not wired into
skill matching.

**SkillsBench approach**: A 4-stage pipeline that progressively narrows candidates:

| Stage | Input | Process | Output |
|-------|-------|---------|--------|
| **1. BM25 + Vector** | Task description + all skill metadata | Embed query, run BM25, fuse via RRF (k=60) | Top 50 candidates |
| **2. LLM Lenient Selection** | Top 50 skill summaries + task description | LLM selects all potentially relevant skills (generous filter) | 10-12 candidates |
| **3. Content Loading** | 10-12 candidate skill names | Load first 3,000 characters of each SKILL.md | Loaded skill content |
| **4. LLM Strict Quality Filter** | Loaded content + task description | LLM selects only high-quality, directly relevant skills | 3-6 final skills |

**Why this is P0**: Skill selection quality directly determines task success. The current text-based
search produces too many false positives and misses semantically relevant skills. The LLM refinement
stages address the "last mile" problem that pure retrieval cannot solve.

**Implementation sketch**:

```python
# engine/src/agent33/skills/matching.py -- new module

class SkillMatcher:
    """4-stage hybrid skill matching pipeline."""

    def __init__(
        self,
        registry: SkillRegistry,
        hybrid_searcher: HybridSearcher,
        llm_router: ModelRouter,
        model: str = "gpt-4o-mini",
    ) -> None:
        self._registry = registry
        self._searcher = hybrid_searcher
        self._router = llm_router
        self._model = model

    async def match(
        self,
        task_description: str,
        max_final: int = 6,
    ) -> list[SkillDefinition]:
        """Run 4-stage matching pipeline."""
        # Stage 1: BM25 + Vector retrieval
        stage1 = await self._stage1_retrieval(task_description, top_k=50)

        # Stage 2: LLM lenient selection
        stage2 = await self._stage2_llm_lenient(task_description, stage1, max_out=12)

        # Stage 3: Content loading (first 3000 chars per skill)
        stage3 = self._stage3_load_content(stage2, max_chars=3000)

        # Stage 4: LLM strict quality filter
        stage4 = await self._stage4_llm_strict(
            task_description, stage3, max_out=max_final
        )

        return stage4
```

**Effort**: 2 days (BM25 index for skills already exists as pattern; LLM calls are straightforward).

#### 4.3. Context Window Management

**Current state**: No context window management. `AgentRuntime.invoke()` sends all messages to the
LLM. The only token-awareness is in `TokenAwareChunker` (for ingestion) and `ProgressiveRecall`
(for memory retrieval).

**SkillsBench approach**: Three strategies for staying within context limits:

1. **Message unwinding**: When approaching the context limit, remove the oldest user/assistant
   message pairs while keeping the system prompt and most recent exchanges.
2. **Handoff summaries**: When a conversation needs to be handed off (to a new context window or
   a different agent), summarize the current state and carry it forward.
3. **Proactive summarization**: When token count exceeds a threshold (e.g., 80% of context window),
   automatically summarize older messages and replace them with a compact summary.

**Why this is P0**: Without context window management, AGENT-33 agents will fail on any task that
requires many iterations of tool use. The message history will exceed the model's context window,
causing truncation or API errors. This is a prerequisite for the iterative tool-use loop (4.1).

**Implementation sketch**:

```python
# engine/src/agent33/agents/context_manager.py -- new module

class ContextWindowManager:
    """Manages message history to stay within LLM context limits."""

    def __init__(
        self,
        max_tokens: int = 128_000,
        summarize_at_pct: float = 0.8,
        keep_recent: int = 4,
    ) -> None:
        self._max_tokens = max_tokens
        self._summarize_threshold = int(max_tokens * summarize_at_pct)
        self._keep_recent = keep_recent

    def estimate_tokens(self, messages: list[ChatMessage]) -> int:
        """Estimate total token count for message list."""
        return sum(
            max(1, len(m.content.split()) * 1.3)  # word-based heuristic
            for m in messages
        )

    def unwind(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        """Remove oldest message pairs to stay within limits."""
        while self.estimate_tokens(messages) > self._summarize_threshold:
            # Keep system prompt (index 0) and recent messages
            if len(messages) <= self._keep_recent + 1:
                break
            messages.pop(1)  # Remove oldest non-system message
        return messages

    async def summarize_and_compact(
        self,
        messages: list[ChatMessage],
        router: ModelRouter,
        model: str,
    ) -> list[ChatMessage]:
        """Summarize old messages and replace with compact summary."""
        if self.estimate_tokens(messages) < self._summarize_threshold:
            return messages

        # Split into system, old, and recent
        system = messages[0]
        old = messages[1:-self._keep_recent]
        recent = messages[-self._keep_recent:]

        if not old:
            return messages

        # Summarize old messages
        summary = await self._generate_summary(old, router, model)
        summary_msg = ChatMessage(
            role="user",
            content=f"[Context Summary]\n{summary}",
        )

        return [system, summary_msg] + recent
```

**Effort**: 2 days (token estimation, unwinding, summarization call).

#### 4.4. Task Completion Double-Confirmation

**Current state**: `AgentRuntime.invoke()` returns the first LLM response as the final result. No
confirmation step.

**SkillsBench approach**: When the agent signals task completion, the system sends a confirmation
prompt asking the agent to verify it has actually completed all requirements. This catches cases
where the agent prematurely declares success.

**Why this is P0**: False-positive completions waste resources and produce incorrect results. This is
especially important in multi-agent workflows where downstream agents depend on upstream results.
The double-confirmation pattern is simple to implement and has outsized impact on reliability.

**Implementation**: Integrate into the iterative tool-use loop (4.1). When the agent's response
indicates completion, send a follow-up message:

```python
CONFIRMATION_PROMPT = """You indicated the task is complete. Please verify:
1. Have all requirements been met?
2. Are all outputs present and correct?
3. Is there anything left to do?

Respond with CONFIRMED if complete, or continue working if not."""
```

**Effort**: 0.5 days (integrated with 4.1).

#### 4.5. Binary Reward + Multi-Trial Evaluation Methodology

**Current state**: AGENT-33's evaluation harness runs golden tasks once and computes M-01..M-05
metrics. No multi-trial evaluation, no skills-impact measurement.

**SkillsBench approach**: Each task is run 5 times per agent/model combination. Results are
aggregated into pass rates. Skills impact is measured as the delta between with-skills and
without-skills pass rates.

**Why this is P0**: LLM outputs are non-deterministic. A single trial cannot distinguish between a
genuinely capable agent and one that got lucky. Multi-trial evaluation with variance tracking is the
minimum standard for credible agent evaluation.

**Implementation**:

```python
# engine/src/agent33/evaluation/multi_trial.py -- new module

@dataclass
class TrialResult:
    trial_number: int
    passed: bool
    duration_ms: float
    tokens_used: int

@dataclass
class TaskEvaluation:
    task_id: str
    trials: list[TrialResult]
    pass_rate: float  # passed / total
    variance: float  # statistical variance across trials
    skills_impact: float | None  # with_skills - without_skills (if both runs exist)
```

**Effort**: 1 day (wrapping existing evaluation service in a multi-trial runner).

### High (P1) -- Features that strengthen AGENT-33's architecture

#### 4.6. Answer Leakage Prevention in Skill Injection

**Current state**: Skills are injected into the system prompt without checking whether their content
contains direct answers to the task. This is a concern for both evaluation integrity (an agent might
"cheat" by finding answers in skill metadata) and production security (skill content might contain
sensitive information that should be filtered before injection).

**SkillsBench approach**: During the LLM-based skill selection stages (2 and 4), the prompt
explicitly instructs the LLM to evaluate skills for relevance without extracting answers. Skill
content is truncated to prevent full-answer leakage.

**Implementation**: Add a screening step in `SkillInjector` that checks whether injected skill
content appears to contain direct answers to the current task. This can be a heuristic check (high
n-gram overlap between skill content and expected output format) or an LLM-based check.

**Effort**: 1 day.

#### 4.7. Failure Mode Taxonomy Alignment with SkillsBench

**Current state**: AGENT-33 has a 10-category failure taxonomy (F-ENV, F-INP, F-EXE, F-TMO, F-RES,
F-SEC, F-DEP, F-VAL, F-REV, F-UNK). SkillsBench tracks failure modes but with a different
categorization.

**Implementation**: Map SkillsBench failure modes to AGENT-33's taxonomy. Add any missing categories.
Ensure evaluation results from SkillsBench runs can be classified using AGENT-33's failure system.

**Effort**: 0.5 days.

#### 4.8. LiteLLM Integration for Unified Multi-Provider Routing

**Current state**: AGENT-33 has a custom `ModelRouter` with prefix-based routing and a 22+ provider
catalog with auto-registration from env vars. Each provider is an `OpenAIProvider` instance.

**SkillsBench approach**: Uses LiteLLM as a unified proxy for all providers. LiteLLM handles:
- Automatic provider detection from model name
- Cost tracking per call
- Retry with backoff
- Fallback between providers
- Token counting
- Rate limit handling

**Why P1**: AGENT-33's custom provider catalog works but requires manual maintenance. LiteLLM is
battle-tested across thousands of deployments and handles edge cases that AGENT-33's custom code
does not (e.g., provider-specific response parsing, streaming, function calling format differences).

**Implementation**: Add LiteLLM as an optional provider backend. Keep the existing custom catalog as
a fallback. Route through LiteLLM when available.

```python
# engine/src/agent33/llm/litellm_provider.py -- new module

class LiteLLMProvider:
    """LLM provider backed by LiteLLM for unified multi-provider routing."""

    async def complete(
        self, messages: list[ChatMessage], **kwargs
    ) -> LLMResponse:
        import litellm
        response = await litellm.acompletion(
            model=kwargs.get("model", "gpt-4o"),
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            total_tokens=response.usage.total_tokens,
            cost=response._hidden_params.get("response_cost", 0.0),
        )
```

**Effort**: 2 days (provider implementation, config integration, optional dependency handling).

#### 4.9. CTRF Test Result Format for Standardized Reporting

**Current state**: AGENT-33 uses custom Pydantic models for evaluation results (`EvaluationRun`,
`GateReport`, `TaskRunResult`). These are not compatible with external tools.

**SkillsBench approach**: Uses CTRF (Common Test Results Format), a standardized JSON format for
test results that can be consumed by CI tools, dashboards, and reporting systems.

**Implementation**: Add a CTRF serializer for `EvaluationRun`:

```python
# engine/src/agent33/evaluation/ctrf.py -- new module

def to_ctrf(run: EvaluationRun) -> dict:
    """Convert an EvaluationRun to CTRF format."""
    return {
        "results": {
            "tool": {"name": "agent33", "version": "0.1.0"},
            "summary": {
                "tests": len(run.task_results),
                "passed": sum(1 for t in run.task_results if t.result == TaskResult.PASS),
                "failed": sum(1 for t in run.task_results if t.result == TaskResult.FAIL),
                "skipped": sum(1 for t in run.task_results if t.result == TaskResult.SKIP),
                "other": sum(1 for t in run.task_results if t.result == TaskResult.ERROR),
                "start": run.started_at.isoformat(),
                "stop": (run.completed_at or run.started_at).isoformat(),
            },
            "tests": [
                {
                    "name": t.item_id,
                    "status": t.result.value,
                    "duration": t.duration_ms,
                }
                for t in run.task_results
            ],
        }
    }
```

**Effort**: 1 day.

#### 4.10. Skill Quality Validation Pipeline (12-Criterion Analysis)

**Current state**: Skills are loaded and registered without quality checks. A skill with missing
instructions, invalid YAML, or poor-quality content will be registered as-is.

**SkillsBench approach**: Quality Checker contrib agent evaluates skills against 12 criteria:

| # | Criterion | Description |
|---|-----------|-------------|
| 1 | Frontmatter completeness | All required YAML fields present |
| 2 | Name uniqueness | No name collisions in registry |
| 3 | Description quality | Description is informative, not just the name |
| 4 | Instructions clarity | Instructions are actionable and specific |
| 5 | Script validity | Referenced scripts exist and are executable |
| 6 | Reference availability | Referenced files exist |
| 7 | Tag consistency | Tags follow naming conventions |
| 8 | Version format | Semver compliance |
| 9 | Dependency resolution | All declared dependencies can be resolved |
| 10 | AI detection | Instructions appear human-authored (not LLM-generated boilerplate) |
| 11 | Answer leakage | Content does not contain direct answers to benchmark tasks |
| 12 | Security scan | No suspicious commands, no credential exposure |

**Implementation**: Add a `SkillValidator` class that runs these checks before registration:

```python
# engine/src/agent33/skills/validator.py -- new module

@dataclass
class ValidationReport:
    skill_name: str
    passed: bool
    criteria_results: list[CriterionResult]
    score: float  # 0.0 to 1.0

class SkillValidator:
    def validate(self, skill: SkillDefinition) -> ValidationReport:
        results = [
            self._check_frontmatter(skill),
            self._check_name_uniqueness(skill),
            self._check_description_quality(skill),
            self._check_instructions_clarity(skill),
            self._check_scripts(skill),
            self._check_references(skill),
            self._check_tags(skill),
            self._check_version(skill),
            self._check_dependencies(skill),
            self._check_security(skill),
        ]
        passed = all(r.passed for r in results if r.required)
        score = sum(1 for r in results if r.passed) / len(results)
        return ValidationReport(
            skill_name=skill.name, passed=passed,
            criteria_results=results, score=score,
        )
```

**Effort**: 1 day.

### Medium (P2) -- Nice-to-have improvements

#### 4.11. Metrics Dashboard (React + Recharts)

**Current state**: No visualization. Evaluation results are accessible only via API endpoints
(`/v1/evaluations`). Improvement metrics (`IM-01..IM-05`) are available via
`/v1/improvements/metrics` but have no visual representation.

**SkillsBench approach**: React + TypeScript + Recharts dashboard showing:
- Pass rates per task over time
- Skills impact heatmap (which skills help which tasks)
- Token/cost breakdown per model
- Comparison charts between agents and configurations
- Trend lines for improvement metrics

**Why P2**: Visualization accelerates iteration. Without a dashboard, developers must query API
endpoints and manually analyze JSON. But the API endpoints already exist and can be consumed by
any frontend.

**Effort**: 3 days (React app with Recharts, consuming existing AGENT-33 API endpoints).

#### 4.12. Container-Based Task Execution (Docker Isolation)

**Current state**: Code execution uses `CLIAdapter` with subprocess spawning, `SandboxConfig` for
resource limits (timeout, memory, CPU, filesystem, network, process policies). Isolation is
process-level.

**SkillsBench approach**: Each task runs in a Docker container with:
- Isolated filesystem (skills copied to container at build time)
- Network restrictions (configurable per task)
- Resource limits (CPU, memory, timeout)
- Clean environment per run

**Why P2**: Docker provides stronger isolation than subprocess sandboxing, but AGENT-33's adapter
pattern (`BaseAdapter`, `CLIAdapter`) already supports plugging in new adapters. A `DockerAdapter`
would be a natural extension.

**Implementation**: Add a `DockerAdapter` that extends `BaseAdapter`:

```python
# engine/src/agent33/execution/adapters/docker.py -- new module

class DockerAdapter(BaseAdapter):
    """Execute code in Docker containers for strong isolation."""

    async def execute(self, contract: ExecutionContract) -> ExecutionResult:
        container = await self._create_container(contract)
        try:
            result = await self._run_in_container(container, contract)
            return result
        finally:
            await self._cleanup_container(container)
```

**Effort**: 3 days (Docker SDK integration, image building, result extraction).

#### 4.13. Automated PR Review Workflow (Benchmark-Driven)

**Current state**: AGENT-33 has review automation (Phase 15) with risk assessment, reviewer
assignment, and a signoff state machine. But reviews are governance-focused, not benchmark-driven.

**SkillsBench approach**: Every PR triggers a GitHub Actions workflow that:
1. Runs the oracle for every task to verify test correctness
2. Runs 5 experiment configurations (oracle, claude with/without skills, codex with/without skills)
3. Compares results against the previous benchmark run
4. Posts results as a PR comment

**Implementation**: Extend AGENT-33's review automation to include benchmark runs:
- Add a "benchmark" trigger type to the review workflow
- Run evaluation suite as part of PR checks
- Compare against baseline snapshot
- Flag regressions using existing RI-01..RI-05 indicators

**Effort**: 2 days (GitHub Actions workflow, evaluation service integration).

#### 4.14. Experiment Config Format (YAML-Driven Batch Evaluation)

**Current state**: Evaluation runs are triggered via API calls. No batch configuration system.

**SkillsBench approach**: YAML files define complete experiment configurations:

```yaml
# experiments/full-benchmark.yaml
name: full-benchmark
description: Run all tasks against all agents
agents:
  - name: orchestrator
    model: claude-sonnet-4-20250514
    skills_enabled: true
  - name: orchestrator
    model: claude-sonnet-4-20250514
    skills_enabled: false
  - name: code-worker
    model: gpt-4o
    skills_enabled: true
tasks:
  - all  # or list specific task IDs
trials: 5
timeout_per_task: 300
```

**Implementation**: Add an experiment config loader and batch runner:

```python
# engine/src/agent33/evaluation/experiment.py -- new module

class ExperimentConfig(BaseModel):
    name: str
    description: str = ""
    agents: list[AgentExperimentConfig]
    tasks: list[str]  # "all" or specific task IDs
    trials: int = 5
    timeout_per_task: int = 300

class ExperimentRunner:
    async def run(self, config: ExperimentConfig) -> ExperimentResults:
        ...
```

**Effort**: 1.5 days.

### Low (P3) -- Track but don't prioritize

#### 4.15. Matrix Channel Adapter

**Current state**: AGENT-33 has Telegram, Discord, Slack, and WhatsApp adapters via NATS bus with
per-channel health checks. Matrix is missing.

**SkillsBench context**: Matrix is not directly relevant to SkillsBench, but was identified as a gap
in the ZeroClaw parity analysis. Noted here for completeness.

**Effort**: 2 days.

#### 4.16. BrowseComp Adapter Pattern

**Current state**: AGENT-33 has a browser tool in `tools/builtins`. SkillsBench does not include
browser-based tasks.

**Effort**: 1 day (if needed).

#### 4.17. Task Wizard (Automated Task Creation)

**Current state**: Golden tasks are defined in code (`golden_tasks.py`). No automated task creation.

**SkillsBench approach**: Task Wizard contrib agent generates new benchmark tasks given a category
and difficulty level.

**Effort**: 2 days.

#### 4.18. Result Auditor

**Current state**: No automated result auditing beyond regression detection.

**SkillsBench approach**: Result Auditor reviews benchmark results for anomalies (suspiciously high
scores, impossible task completions, etc.).

**Effort**: 1 day.

---

## 5. What AGENT-33 Already Does Better

This section documents capabilities where AGENT-33 is architecturally superior to SkillsBench and
its Terminus-2 agent. These should be preserved and leveraged during integration.

### 5.1 Multi-Agent DAG Orchestration

AGENT-33's workflow engine is its core differentiator. SkillsBench has no equivalent.

| Capability | AGENT-33 | SkillsBench |
|-----------|----------|-------------|
| DAG execution | Topological sort with parallel/sequential/dependency-aware modes | N/A |
| Action types | 8 types: invoke-agent, run-command, validate, transform, conditional, parallel-group, wait, execute-code | N/A |
| Agent composition | 6 role-based agents with dependency declarations | Single Terminus-2 agent |
| Checkpoint persistence | Resume workflows after failure | N/A |
| Expression evaluation | Dynamic expressions in workflow steps | N/A |
| State machine | Workflow lifecycle with state transitions | N/A |

**Impact**: Multi-agent orchestration enables AGENT-33 to decompose complex tasks into subtasks
assigned to specialized agents. SkillsBench tasks are designed for single-agent execution, but
AGENT-33 could potentially achieve higher pass rates by using orchestrated multi-agent teams.

### 5.2 Multi-Tenancy

Every database model in AGENT-33 has a `tenant_id`. `AuthMiddleware` resolves tenant from API key
or JWT. All queries are tenant-scoped. SkillsBench is single-user by design.

### 5.3 Enterprise Security Stack

| Security Feature | AGENT-33 | SkillsBench |
|-----------------|----------|-------------|
| JWT authentication | Yes (TokenPayload with tenant_id) | No |
| API key authentication | Yes (with expiration) | Env vars only |
| Rate limiting | Sliding-window + burst, per-subject | No |
| Deny-first permissions | 8 scopes, deny-first evaluation | No |
| Command validation | Multi-segment (pipe/chain/subshell blocking) | Container isolation |
| Path traversal hardening | Null bytes, `..`, symlink, `relative_to()` | Container isolation |
| Prompt injection detection | Dedicated module | No |
| Encryption | ChaCha20 via vault | No |
| Brute-force lockout | Pairing lockout | No |
| Request size limits | `RequestSizeLimitMiddleware` | No |
| SecretStr protection | All sensitive config fields | No |
| Autonomy levels | ReadOnly / Supervised / Full per agent | No |

### 5.4 Observability Pipeline

AGENT-33's observability is production-grade:

| Component | AGENT-33 | SkillsBench |
|-----------|----------|-------------|
| Trace records | TraceRecord with TRC-timestamp IDs, 6 statuses, 9 artifact types | No tracing |
| Failure taxonomy | 10 categories (F-ENV..F-UNK), 4 severity levels, retryable/escalation metadata | Basic failure enum |
| Retention policies | Tiered (hot/warm/cold), per-artifact, 7d to permanent | Ephemeral |
| Structured logging | structlog throughout | Standard logging |
| Improvement metrics | IM-01..IM-05 with trend computation | Point-in-time only |
| Alerting | Alert rules | No alerting |

### 5.5 Autonomy Budget Enforcement

AGENT-33 Phase 18 provides fine-grained control over what agents can do:

- Budget lifecycle: DRAFT -> ACTIVE -> COMPLETED with preflight checks (PF-01..PF-10)
- Runtime enforcement: 8 enforcement rules (EF-01..EF-08) for file read/write, commands, network,
  iterations, duration, files modified, lines changed
- Stop conditions and escalation management
- 18 REST endpoints under `/v1/autonomy`

SkillsBench has no equivalent. Tasks run with full permissions inside containers.

### 5.6 Release Lifecycle Management

AGENT-33 Phase 19 manages the full release lifecycle:

- State machine: PLANNED -> FROZEN -> RC -> VALIDATING -> RELEASED -> ROLLED_BACK
- Pre-release checklist (RL-01..RL-08)
- Sync engine with dry-run and fnmatch matching
- Rollback manager with 12-entry decision matrix (severity x impact)

SkillsBench has no release management (it is a benchmark tool, not a production system).

### 5.7 Continuous Improvement System

AGENT-33 Phase 20 implements a complete improvement feedback loop:

- Research intake lifecycle: SUBMITTED -> TRIAGED -> ANALYZING -> ACCEPTED/DEFERRED/REJECTED -> TRACKED
- Lessons learned with action tracking
- Improvement checklists (CI-01..CI-15)
- Metrics tracker (IM-01..IM-05 with trend computation)
- Roadmap refresh records
- 22 REST endpoints under `/v1/improvements`

This system is directly relevant to SkillsBench integration: benchmark results can be ingested as
research intake items, processed through the improvement pipeline, and tracked to resolution.

### 5.8 Review Automation

AGENT-33 Phase 15 provides code review automation:

- Risk assessment with 5 levels, 14 triggers
- Reviewer assignment via 14-entry role matrix
- Signoff state machine with 10 states, terminal MERGED
- L1/L2 review checklists
- Full lifecycle from creation to merge

### 5.9 Memory Persistence and Progressive Recall

AGENT-33's memory system is far richer than SkillsBench's ephemeral approach:

| Memory Feature | AGENT-33 | SkillsBench |
|---------------|----------|-------------|
| Long-term storage | PostgreSQL + pgvector, persistent | None |
| Short-term buffer | In-memory, session-scoped | Message history in loop |
| Session state | Persistent across sessions | None |
| Observation capture | Records agent interactions as observations | None |
| Session summarization | Summarizes sessions for future reference | None |
| Progressive recall | 3-layer (index/timeline/full) with ~10x token savings | None |
| Memory retention | Tiered policies, configurable per artifact type | None |
| Batch embeddings | `embed_batch()` for efficient bulk operations | None |
| Embedding cache | LRU with SHA-256 keys, hit/miss tracking | None |

### 5.10 Skill Governance

AGENT-33's skill system includes governance features that SkillsBench does not:

| Governance Feature | AGENT-33 | SkillsBench |
|-------------------|----------|-------------|
| Invocation mode control | user-only, llm-only, both | No control |
| Execution context | inline (agent context) or fork (isolated subagent) | All inline |
| Autonomy override | Skill can override agent's autonomy level | No override |
| Approval requirements | Skill can require human approval for specific patterns | No approval |
| Tool access control | `resolve_tool_context()` narrows tool access per skill | No control |
| Dependency management | `SkillDependency` with optional flag | No dependencies |
| Lifecycle status | active, deprecated, experimental | No lifecycle |
| Parameter defaults | Per-tool parameter overrides when skill is active | No defaults |

---

## 6. Anti-Patterns to Avoid

### 6.1 Don't Overfit to SkillsBench Benchmarks

**Risk**: Optimizing AGENT-33 specifically for SkillsBench's 86 tasks rather than improving general
capability.

**Symptom**: Adding task-specific logic, hard-coding skill selections, or tuning prompts to pass
specific tests without improving the underlying system.

**Mitigation**: Treat SkillsBench as one of many evaluation signals. Use it alongside AGENT-33's
existing golden tasks (GT-01..GT-07), regression detection (RI-01..RI-05), and improvement metrics
(IM-01..IM-05). Never add code paths that only execute during benchmark runs.

**Concrete example of what NOT to do**:

```python
# BAD: Hard-coded skill selection for a specific benchmark task
if task_id == "financial-analysis-01":
    skills = ["pandas-expert", "financial-modeling"]
```

```python
# GOOD: Improved general skill matching that happens to score better
stage2_candidates = await self._llm_lenient_select(task, stage1_results)
```

### 6.2 Don't Adopt Harbor's Docker-Only Execution Model

**Risk**: Requiring Docker for all code execution, breaking the flexible adapter pattern.

**Symptom**: Removing `CLIAdapter` or making Docker a hard dependency.

**Mitigation**: Add `DockerAdapter` as an optional adapter alongside `CLIAdapter`. Let the
`ExecutionContract.adapter_id` field determine which adapter is used. Keep subprocess-based
execution as the default.

### 6.3 Don't Abandon Multi-Agent Architecture for Single-Agent Patterns

**Risk**: Simplifying AGENT-33's multi-agent DAG orchestration to match SkillsBench's single-agent
model because "it's simpler" or "SkillsBench only tests single agents."

**Symptom**: Routing all tasks through a single "universal" agent, removing the workflow engine, or
deprecating role-based specialization.

**Mitigation**: When running SkillsBench tasks, expose a single-agent interface that wraps
AGENT-33's multi-agent capabilities. The adapter presents a single agent externally while internally
it may orchestrate multiple specialized agents:

```python
class SkillsBenchAdapter:
    """Wraps AGENT-33's multi-agent system as a single-agent interface for benchmarks."""

    async def run_task(self, task: SkillsBenchTask) -> TaskResult:
        # Internally may use orchestrator -> code-worker -> qa pipeline
        workflow = self._select_workflow(task)
        result = await self._engine.execute(workflow, task.inputs)
        return self._format_result(result)
```

### 6.4 Don't Replace PostgreSQL + pgvector with SQLite

**Risk**: Adopting SkillsBench's SQLite usage for simplicity.

**Symptom**: Removing pgvector dependency, using SQLite for long-term memory.

**Mitigation**: Never. PostgreSQL + pgvector provides:
- Multi-tenant isolation via `tenant_id`
- Native vector similarity search (no Python-level computation)
- ACID transactions for concurrent multi-agent access
- Scalability beyond single-machine workloads
- Production-grade backup and replication

SQLite is appropriate for SkillsBench because it runs single-user, ephemeral tasks on a single
machine. It is not appropriate for AGENT-33's production use case.

### 6.5 Don't Adopt LLM-as-Judge (Alignment)

Both AGENT-33 and SkillsBench explicitly avoid LLM-as-judge evaluation. This is a point of
alignment, not a potential anti-pattern to avoid. But it is worth restating:

- Evaluation must be deterministic and reproducible
- Test assertions must check specific expected outcomes
- Scoring must not depend on the subjective judgment of an LLM
- Human review is appropriate for edge cases; LLM judgment is not

This aligns with AGENT-33's anti-corner-cutting rule: "Each assertion must check one specific
expected outcome."

### 6.6 Don't Use `rank-bm25` Library

**Risk**: Replacing AGENT-33's custom `BM25Index` with the `rank-bm25` library for "compatibility."

**Why to avoid**: AGENT-33's custom implementation:
- Has zero external dependencies beyond the standard library
- Is already tuned with the same Okapi BM25 algorithm (k1=1.2, b=0.75)
- Supports incremental document addition (no re-indexing required)
- Has a clean API that integrates with the existing `HybridSearcher`
- Is fully tested as part of the 973-test suite

Adding `rank-bm25` would introduce an unnecessary dependency without functional benefit.

### 6.7 Don't Copy Terminus-2's Monolithic Agent Design

**Risk**: Replicating Terminus-2's single-file, monolithic agent implementation.

**Symptom**: Putting tool call parsing, execution, context management, skill matching, and
completion detection all into `AgentRuntime` rather than decomposing into composable modules.

**Mitigation**: Each new capability should be its own module:
- `agents/tool_loop.py` -- iterative tool-use loop
- `agents/context_manager.py` -- context window management
- `skills/matching.py` -- 4-stage skill matching pipeline
- `agents/completion_detector.py` -- task completion detection and double-confirmation

These modules compose into `AgentRuntime` but can be tested and evolved independently.

---

## 7. Adaptation Strategy: Evolutionary Integration

### 7.1 Guiding Principles

1. **AGENT-33's identity is preserved**: Multi-agent orchestration, enterprise governance, and
   production-grade infrastructure remain core. SkillsBench insights flow into this architecture,
   not the other way around.

2. **Benchmark-aware but not benchmark-chasing**: Improvements should enhance general capabilities
   that happen to score well on benchmarks, not optimize specifically for benchmark tasks.

3. **Modular absorption**: Each SkillsBench insight becomes a composable module that plugs into
   AGENT-33's existing architecture. No monolithic rewrites.

4. **Feedback loop integration**: SkillsBench results feed into AGENT-33's existing continuous
   improvement system (Phase 20), creating a closed-loop optimization cycle.

### 7.2 Phase 1: Compatibility Layer (Days 1-3)

**Goal**: Make AGENT-33 agents runnable against SkillsBench tasks without modifying SkillsBench.

```
+-------------------+     +----------------------+     +-----------------+
|                   |     |                      |     |                 |
|   SkillsBench     |────>| AGENT-33 Adapter     |────>| AGENT-33        |
|   Task Runner     |     | (compatibility shim) |     | AgentRuntime    |
|                   |<────|                      |<────|                 |
+-------------------+     +----------------------+     +-----------------+
```

Deliverables:
- SkillsBench task loader (reads `instruction.md`, `task.toml`, `environment/`)
- AGENT-33 agent wrapper (presents AGENT-33 agent as SkillsBench-compatible interface)
- Result formatter (converts AGENT-33 output to SkillsBench reward format)
- Skill loader compatibility (load SkillsBench skill folders via AGENT-33's `SkillRegistry`)

### 7.3 Phase 2: Skill Matching Enhancement (Days 4-5)

**Goal**: Add LLM-based refinement stages to AGENT-33's existing hybrid search pipeline.

Current pipeline (2-stage):
```
Task Query -> BM25 + Vector (RRF) -> Results
```

Enhanced pipeline (4-stage):
```
Task Query -> BM25 + Vector (RRF) -> LLM Lenient -> Content Load -> LLM Strict -> Results
          Stage 1 (existing)     Stage 2 (new)   Stage 3 (new)  Stage 4 (new)
```

Deliverables:
- `SkillMatcher` class with 4-stage pipeline
- BM25 index for skill content (reuses existing `BM25Index` class)
- LLM prompts for lenient and strict selection stages
- Answer leakage prevention in LLM selection prompts
- Integration with `SkillInjector` (matcher selects skills, injector builds prompt blocks)

### 7.4 Phase 3: Agent Loop Enhancement (Days 6-8)

**Goal**: Add iterative tool-use loop and context window management to `AgentRuntime`.

Deliverables:
- `ToolLoop` class implementing iterative tool call -> execute -> observe cycle
- Tool call parser (JSON format, with XML fallback)
- `ContextWindowManager` with message unwinding and proactive summarization
- Task completion detector with double-confirmation
- Integration with existing `AgentRuntime` (new `invoke_iterative()` method alongside existing
  `invoke()`)

### 7.5 Phase 4: Evaluation Harness Integration (Days 9-10)

**Goal**: Extend AGENT-33's evaluation system to support SkillsBench-compatible evaluation.

Deliverables:
- Multi-trial runner (5 trials per task/agent/model)
- Skills impact calculator (with-skills vs without-skills delta)
- CTRF result serializer
- Experiment config loader (YAML-based batch evaluation)
- Integration with existing `EvaluationService` and regression detection

### 7.6 Phase 5: Visualization and Feedback (Days 11-14)

**Goal**: Build metrics dashboard and connect SkillsBench results to AGENT-33's improvement system.

Deliverables:
- React dashboard consuming AGENT-33 API endpoints
- Pass rate visualization per task, agent, model
- Skills impact heatmap
- Token/cost breakdown charts
- Improvement pipeline connector (benchmark regressions -> research intake -> lessons learned)

### 7.7 Feedback Loop Architecture

The complete feedback loop connects SkillsBench evaluation to AGENT-33's improvement system:

```
Run SkillsBench Tasks
        |
        v
Collect Results (CTRF + binary reward)
        |
        v
Compare Against Baseline Snapshot
        |
        v
Detect Regressions (RI-01..RI-05)
        |
        v
Create Improvement Intake (Phase 20)
        |
        v
Triage and Prioritize
        |
        v
Implement Improvements
        |
        v
Run SkillsBench Tasks Again <--- loop
```

This loop is powered by existing AGENT-33 infrastructure:
- **Evaluation service** (Phase 17): runs tasks, computes metrics, enforces gates
- **Regression detection**: RI-01 (previously passing now fails), RI-02 (metric drops), etc.
- **Research intake** (Phase 20): structured intake for improvement proposals
- **Improvement tracking**: lessons learned, action items, metrics trends

---

## 8. Concrete Implementation Roadmap

### Overview

| # | Work Item | Days | Dependencies | Modules Affected |
|---|-----------|------|-------------|-----------------|
| 1 | SkillsBench Compatibility Adapter | 3 | None | `evaluation/skillsbench/` (new) |
| 2 | Enhanced Skill Matching (4-stage) | 2 | Existing `BM25Index`, `HybridSearcher`, `ModelRouter` | `skills/matching.py` (new) |
| 3 | Context Window Management | 2 | None | `agents/context_manager.py` (new) |
| 4 | Iterative Tool-Use Loop | 3 | Context Window Management (#3) | `agents/tool_loop.py` (new), `agents/runtime.py` (enhanced) |
| 5 | Multi-Trial Evaluation Runner | 1 | None | `evaluation/multi_trial.py` (new) |
| 6 | CTRF Reporting Format | 0.5 | None | `evaluation/ctrf.py` (new) |
| 7 | Skill Quality Validation | 1 | None | `skills/validator.py` (new) |
| 8 | Experiment Config Format | 1 | Multi-Trial Runner (#5) | `evaluation/experiment.py` (new) |
| 9 | LiteLLM Provider (Optional) | 2 | None | `llm/litellm_provider.py` (new) |
| 10 | Metrics Dashboard | 3 | None | `dashboard/` (new frontend) |
| **Total** | | **18.5 days** | | |

### Detailed Plan

#### Step 1: SkillsBench Compatibility Adapter (3 days)

**Day 1**: Task loader and skill loader.

```python
# engine/src/agent33/evaluation/skillsbench/task_loader.py

import tomllib
from pathlib import Path
from pydantic import BaseModel, Field


class SkillsBenchTask(BaseModel):
    """A SkillsBench task definition loaded from disk."""
    task_id: str
    category: str
    instruction: str
    metadata: dict = Field(default_factory=dict)
    environment_path: Path | None = None
    solution_path: Path | None = None
    tests_path: Path | None = None
    skills: list[str] = Field(default_factory=list)


class TaskLoader:
    """Load SkillsBench tasks from directory structure."""

    def load_task(self, task_dir: Path) -> SkillsBenchTask:
        """Load a single task from its directory.

        Expected structure:
            task_dir/
                instruction.md
                task.toml
                environment/
                    Dockerfile
                    skills/
                solution/
                    solve.sh
                tests/
                    test_outputs.py
        """
        instruction = (task_dir / "instruction.md").read_text(encoding="utf-8")

        metadata = {}
        toml_path = task_dir / "task.toml"
        if toml_path.exists():
            with open(toml_path, "rb") as f:
                metadata = tomllib.load(f)

        skills = []
        skills_dir = task_dir / "environment" / "skills"
        if skills_dir.is_dir():
            skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]

        return SkillsBenchTask(
            task_id=task_dir.name,
            category=metadata.get("category", "unknown"),
            instruction=instruction,
            metadata=metadata,
            environment_path=task_dir / "environment" if (task_dir / "environment").exists() else None,
            solution_path=task_dir / "solution" if (task_dir / "solution").exists() else None,
            tests_path=task_dir / "tests" if (task_dir / "tests").exists() else None,
            skills=skills,
        )

    def discover_tasks(self, root: Path) -> list[SkillsBenchTask]:
        """Discover all tasks in a SkillsBench repository."""
        tasks = []
        tasks_dir = root / "tasks"
        if not tasks_dir.is_dir():
            return tasks

        for category_dir in sorted(tasks_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            for task_dir in sorted(category_dir.iterdir()):
                if not task_dir.is_dir():
                    continue
                if (task_dir / "instruction.md").exists():
                    tasks.append(self.load_task(task_dir))

        return tasks
```

**Day 2**: Agent wrapper and result formatter.

```python
# engine/src/agent33/evaluation/skillsbench/adapter.py

from agent33.agents.runtime import AgentRuntime, AgentResult


class SkillsBenchAgentAdapter:
    """Wraps AGENT-33's AgentRuntime as a SkillsBench-compatible interface."""

    def __init__(
        self,
        runtime: AgentRuntime,
        skill_registry: SkillRegistry,
        skill_matcher: SkillMatcher | None = None,
    ) -> None:
        self._runtime = runtime
        self._registry = skill_registry
        self._matcher = skill_matcher

    async def run_task(
        self,
        task: SkillsBenchTask,
        with_skills: bool = True,
    ) -> TaskRunResult:
        """Run a SkillsBench task using AGENT-33's agent runtime."""

        # Load skills if enabled
        active_skills: list[str] = []
        if with_skills and task.skills:
            for skill_name in task.skills:
                skill = self._registry.get(skill_name)
                if skill is not None:
                    active_skills.append(skill_name)

        # Construct inputs from task instruction
        inputs = {
            "instruction": task.instruction,
            "task_id": task.task_id,
            "category": task.category,
        }

        # Execute via AgentRuntime
        result = await self._runtime.invoke(inputs)

        # Convert to SkillsBench-compatible result
        return self._format_result(task, result, active_skills)

    def _format_result(
        self,
        task: SkillsBenchTask,
        result: AgentResult,
        active_skills: list[str],
    ) -> TaskRunResult:
        """Format AGENT-33 result as SkillsBench result."""
        return TaskRunResult(
            task_id=task.task_id,
            passed=self._check_success(result),
            output=result.raw_response,
            tokens_used=result.tokens_used,
            model=result.model,
            skills_used=active_skills,
        )
```

**Day 3**: Integration tests and end-to-end validation.

#### Step 2: Enhanced Skill Matching with LLM Refinement (2 days)

**Day 1**: Build the `SkillMatcher` class with Stage 1 (BM25 + vector) and Stage 2 (LLM lenient).

```python
# engine/src/agent33/skills/matching.py

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent33.llm.router import ModelRouter
    from agent33.memory.bm25 import BM25Index
    from agent33.memory.hybrid import HybridSearcher
    from agent33.skills.definition import SkillDefinition
    from agent33.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)

# Stage 2: LLM lenient selection prompt
_LENIENT_PROMPT = """Given the following task and skill candidates, select ALL skills that
could be even slightly relevant. Be generous -- include anything that might help.

Task: {task_description}

Available skills:
{skill_summaries}

Return a JSON array of skill names that could be relevant. Include borderline cases.
Example: ["skill-a", "skill-b", "skill-c"]"""

# Stage 4: LLM strict quality filter prompt
_STRICT_PROMPT = """Given the following task and skill content, select ONLY the skills that
directly help complete this specific task. Be strict -- exclude anything tangential.

IMPORTANT: Do not extract answers from skill content. Evaluate relevance only.

Task: {task_description}

Skill content:
{skill_content}

Return a JSON array of the most relevant skill names (maximum {max_final}).
Example: ["skill-a", "skill-b"]"""


class SkillMatcher:
    """4-stage hybrid skill matching pipeline.

    Stage 1: BM25 + Vector retrieval via RRF -> top 50 candidates
    Stage 2: LLM lenient selection -> 10-12 candidates
    Stage 3: Content loading (3,000 chars per skill)
    Stage 4: LLM strict quality filter -> 3-6 final skills
    """

    def __init__(
        self,
        registry: SkillRegistry,
        bm25_index: BM25Index,
        hybrid_searcher: HybridSearcher | None = None,
        llm_router: ModelRouter | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        self._registry = registry
        self._bm25 = bm25_index
        self._hybrid = hybrid_searcher
        self._router = llm_router
        self._model = model
        self._skill_index_built = False

    def build_skill_index(self) -> int:
        """Index all registered skills in BM25 for keyword search."""
        skills = self._registry.list_all()
        count = 0
        for skill in skills:
            text = f"{skill.name} {skill.description} {' '.join(skill.tags)}"
            if skill.instructions:
                text += f" {skill.instructions[:500]}"
            self._bm25.add_document(text, metadata={"skill_name": skill.name})
            count += 1
        self._skill_index_built = True
        return count

    async def match(
        self,
        task_description: str,
        max_final: int = 6,
        use_llm_refinement: bool = True,
    ) -> list[SkillDefinition]:
        """Run the matching pipeline.

        If llm_router is not available or use_llm_refinement is False,
        falls back to Stage 1 only (BM25 + vector retrieval).
        """
        if not self._skill_index_built:
            self.build_skill_index()

        # Stage 1: BM25 keyword search (+ vector if hybrid available)
        stage1_names = await self._stage1_retrieval(task_description, top_k=50)

        if not use_llm_refinement or self._router is None:
            # Fallback: return top results from Stage 1
            return self._resolve_skills(stage1_names[:max_final])

        # Stage 2: LLM lenient selection
        stage2_names = await self._stage2_llm_lenient(
            task_description, stage1_names, max_out=12
        )

        # Stage 3: Content loading
        stage3_content = self._stage3_load_content(stage2_names, max_chars=3000)

        # Stage 4: LLM strict quality filter
        stage4_names = await self._stage4_llm_strict(
            task_description, stage3_content, max_out=max_final
        )

        return self._resolve_skills(stage4_names)
```

**Day 2**: Implement Stages 3 and 4, write tests, integrate with `SkillInjector`.

#### Step 3: Context Window Management (2 days)

**Day 1**: `ContextWindowManager` with token estimation and message unwinding.

**Day 2**: Proactive summarization, handoff summaries, integration with `AgentRuntime`.

Key design decisions:
- Token estimation uses the same word-based heuristic as `TokenAwareChunker` (`words * 1.3`)
- System prompt is always preserved (never unwound)
- Most recent N messages are always preserved (configurable, default 4)
- Summarization uses the same LLM the agent is using (via `ModelRouter`)
- Summarization is triggered at 80% of context window capacity (configurable)

#### Step 4: Iterative Tool-Use Loop (3 days)

**Day 1**: Tool call parser (JSON format with XML fallback).

**Day 2**: `ToolLoop` class with execute-observe cycle, max iteration limit, completion detection.

**Day 3**: Double-confirmation, integration with `AgentRuntime.invoke_iterative()`, tests.

Key design decisions:
- Tool calls are parsed from assistant messages using JSON format by default
- `ContextWindowManager` (Step 3) is used to manage growing message history
- Completion detection looks for explicit completion signals in assistant messages
- Double-confirmation sends a verification prompt before accepting completion
- Max iterations is configurable (default 20) and enforced as a hard stop
- Each tool execution is recorded as an observation (existing `ObservationCapture`)
- Trace spans are emitted for each tool call (existing trace infrastructure)

#### Step 5: Multi-Trial Evaluation Runner (1 day)

Build on top of existing `EvaluationService`:

```python
# engine/src/agent33/evaluation/multi_trial.py

from dataclasses import dataclass, field
import statistics


@dataclass
class TrialResult:
    trial_number: int
    passed: bool
    duration_ms: float
    tokens_used: int
    skills_used: list[str] = field(default_factory=list)


@dataclass
class MultiTrialResult:
    task_id: str
    agent_name: str
    model: str
    trials: list[TrialResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if not self.trials:
            return 0.0
        return sum(1 for t in self.trials if t.passed) / len(self.trials)

    @property
    def variance(self) -> float:
        if len(self.trials) < 2:
            return 0.0
        return statistics.variance([1.0 if t.passed else 0.0 for t in self.trials])

    @property
    def avg_tokens(self) -> float:
        if not self.trials:
            return 0.0
        return statistics.mean(t.tokens_used for t in self.trials)

    @property
    def avg_duration_ms(self) -> float:
        if not self.trials:
            return 0.0
        return statistics.mean(t.duration_ms for t in self.trials)


@dataclass
class SkillsImpact:
    task_id: str
    with_skills_pass_rate: float
    without_skills_pass_rate: float

    @property
    def impact(self) -> float:
        return self.with_skills_pass_rate - self.without_skills_pass_rate

    @property
    def impact_pct(self) -> str:
        delta = self.impact * 100
        sign = "+" if delta >= 0 else ""
        return f"{sign}{delta:.1f}%"
```

#### Step 6: CTRF Reporting Format (0.5 days)

Straightforward serializer for existing evaluation models.

#### Step 7: Skill Quality Validation (1 day)

10-criterion validator (12 in SkillsBench, but 2 require LLM -- AI detection and answer leakage --
which are added as optional checks).

#### Step 8: Experiment Config Format (1 day)

YAML loader and batch runner.

#### Step 9: LiteLLM Provider (Optional) (2 days)

Optional dependency. Falls back to existing custom provider catalog if LiteLLM is not installed.

#### Step 10: Metrics Dashboard (3 days)

React + Recharts consuming existing AGENT-33 API endpoints. No new backend code required.

---

## 9. Security Considerations for Adaptation

### 9.1 Container Isolation Implications

If AGENT-33 adopts Docker-based task execution (P2, Step 12), security considerations include:

| Concern | Mitigation |
|---------|-----------|
| Container escape | Use read-only root filesystem, drop all capabilities, run as non-root user |
| Network access | Default-deny networking; allow only explicitly whitelisted endpoints |
| Resource exhaustion | Set CPU, memory, and PID limits per container |
| Persistent state leakage | Destroy container after each task; never reuse containers |
| Image supply chain | Build images from trusted base images; scan for vulnerabilities |
| Volume mounts | Never mount host filesystem; copy files into container at build time |

AGENT-33's existing `SandboxConfig` model maps naturally to Docker resource limits:

| SandboxConfig Field | Docker Equivalent |
|--------------------|-------------------|
| `timeout_ms` | `--stop-timeout` |
| `memory_mb` | `--memory` |
| `cpu_cores` | `--cpus` |
| `filesystem.read` | Volume mounts (read-only) |
| `filesystem.write` | Volume mounts (read-write) |
| `filesystem.deny` | Not mounted |
| `network.enabled` | `--network none` or `--network bridge` |
| `network.allow` | iptables rules inside container |
| `processes.max_children` | `--pids-limit` |

### 9.2 API Key Management Across Providers

With LiteLLM integration (P1, Step 9), API key management becomes more complex:

| Provider | Key Variable | Current AGENT-33 Handling | LiteLLM Handling |
|----------|-------------|--------------------------|-----------------|
| OpenAI | `OPENAI_API_KEY` | `SecretStr` in config | env var |
| Anthropic | `ANTHROPIC_API_KEY` | `SecretStr` in config | env var |
| Groq | `GROQ_API_KEY` | Auto-registration from env | env var |
| Together | `TOGETHER_API_KEY` | Auto-registration from env | env var |
| ... (22+ more) | Various | Auto-registration from env | env var |

**Security requirements**:
- All API keys must remain `SecretStr` in AGENT-33's config layer, even when passed to LiteLLM
- API keys must never appear in logs (structlog integration must filter them)
- API keys must never be included in trace records or evaluation results
- LiteLLM's built-in logging must be configured to redact API keys

**Implementation**: Create a `LiteLLMConfigBridge` that safely transfers `SecretStr` values to
LiteLLM's expected env var format at startup, without logging them:

```python
class LiteLLMConfigBridge:
    """Safely bridge AGENT-33 SecretStr config to LiteLLM env vars."""

    def configure(self, settings: Settings) -> None:
        import os
        key_mappings = {
            "openai_api_key": "OPENAI_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            # ... etc
        }
        for config_field, env_var in key_mappings.items():
            value = getattr(settings, config_field, None)
            if value is not None:
                os.environ[env_var] = value.get_secret_value()
```

### 9.3 Answer Leakage Prevention

Answer leakage occurs when skill content contains direct answers to benchmark tasks, allowing the
agent to "cheat" by extracting answers from skills rather than reasoning about the task.

**Prevention strategies**:

1. **Truncation**: Load only the first 3,000 characters of skill content during selection (Stage 3).
   This prevents the full skill (which might contain worked examples) from influencing selection.

2. **Prompt instruction**: The LLM selection prompts (Stages 2 and 4) explicitly instruct the model
   to evaluate relevance without extracting answers:
   ```
   IMPORTANT: Do not extract answers from skill content. Evaluate relevance only.
   ```

3. **Heuristic detection**: Check for high n-gram overlap between skill content and expected output
   patterns. Flag skills with suspiciously high overlap.

4. **Separate selection context**: Run skill selection with a different model or temperature than
   the main task execution, so the selection model cannot "remember" answers when the task model
   runs.

### 9.4 Skill Validation as Security Gate

The skill quality validation pipeline (P1, Step 7) doubles as a security gate:

| Security Check | What It Catches |
|---------------|-----------------|
| Script validity | Malicious scripts in skill bundles |
| Reference availability | Missing files (potential path traversal targets) |
| Security scan | Credential exposure, suspicious commands (`curl \| bash`, `eval`, etc.) |
| AI detection | LLM-generated boilerplate skills (quality concern, not strictly security) |
| Answer leakage | Skills designed to game benchmarks |

Integration with AGENT-33's existing security stack:
- Path traversal checks in `SkillRegistry.get_resource()` already block `..` traversal
- Command validation in `security/` already blocks dangerous command patterns
- The validator adds a pre-registration gate: skills that fail security checks are not registered

---

## 10. Benchmark Performance Predictions

### 10.1 Categories Where AGENT-33 Would Excel

Based on AGENT-33's current capabilities, the following SkillsBench categories should show strong
performance:

| Category | Why AGENT-33 Would Excel | Relevant AGENT-33 Subsystems |
|----------|------------------------|------------------------------|
| **Software Engineering** (Spring Boot migration, build fixes, translations) | Multi-step workflows with code analysis and modification | Workflow engine, code execution, file_ops tool |
| **Document Processing** (PDF, Excel, LaTeX) | Structured data extraction and transformation | Token-aware chunking, ingestion pipeline, transform actions |
| **Planning/Scheduling** | DAG decomposition and dependency management | Workflow engine with topological sort, parallel-group action |
| **Multi-File Coordinated Updates** | Exactly matches GT-07 golden task | Workflow engine, validate action, multi-agent coordination |
| **Security/CVE Analysis** | Structured analysis with evidence capture | Observation capture, evidence workflow, tool governance |
| **Financial Analysis** | Data processing with structured output | Token-aware chunking, RAG pipeline, structured JSON output |

**Expected pass rate on these categories**: 60-80% (with skills enabled, after implementing
iterative tool-use loop).

### 10.2 Categories Needing Work

| Category | Why AGENT-33 Would Struggle | Gap to Close |
|----------|---------------------------|--------------|
| **Scientific Computing** (quantum, crystallography, seismology, astronomy) | Requires specialized domain skills and computational libraries | Need domain-specific skills; current skill catalog is empty |
| **Media Processing** (video dubbing, diarization, speech) | No media processing tools or skills | Need new tools (ffmpeg, whisper) and corresponding skills |
| **Formal Methods** (Lean4 proofs) | Requires theorem prover integration | Need Lean4 adapter in execution layer |
| **Control Systems** (HVAC, cruise control, MPC) | Requires numerical computing libraries | Need numpy/scipy skills and execution environment |
| **ML/AI** (code reproduction, regression) | Requires ML framework integration | Need PyTorch/sklearn skills and GPU execution |
| **Manufacturing** | Specialized domain knowledge | Need manufacturing domain skills |

**Expected pass rate on these categories**: 10-30% initially (limited by missing domain skills and
tools).

### 10.3 Impact of Proposed Improvements

The following table predicts the pass rate improvement from each proposed enhancement:

| Enhancement | Baseline (current) | After Enhancement | Expected Lift |
|------------|-------------------|-------------------|---------------|
| Iterative tool-use loop (P0) | 5-10% (single LLM call cannot complete multi-step tasks) | 40-60% (agents can now interact with environment) | +35-50% |
| 4-stage skill matching (P0) | 40-60% (after tool loop) | 55-70% (better skill selection improves task-relevant context) | +10-15% |
| Context window management (P0) | 55-70% (after matching) | 60-75% (fewer context overflow failures) | +5% |
| Double-confirmation (P0) | 60-75% (after context mgmt) | 63-78% (fewer false-positive completions) | +3% |
| Multi-trial evaluation (P0) | N/A (statistical methodology) | More accurate measurement of true capability | Measurement improvement |

**Aggregate prediction**: With all P0 improvements implemented, AGENT-33 should achieve **60-75%
overall pass rate** on SkillsBench tasks across all categories, with **75-85%** on software
engineering and document processing categories.

### 10.4 Performance Improvement Trajectory

```
Week 0 (baseline):     ~5-10%  (single LLM call, no tool use)
                               Only tasks solvable with pure reasoning pass.

Week 1 (tool loop):    ~40-50% (iterative tool use, basic skill loading)
                               Agents can now execute commands and read/write files.

Week 2 (matching):     ~55-65% (4-stage skill matching, context management)
                               Better skill selection means better task context.

Week 3 (evaluation):   ~60-70% (multi-trial, skills impact measurement)
                               Accurate measurement drives targeted improvement.

Week 4+ (iteration):   ~65-75% (feedback loop through improvement system)
                               Each cycle identifies weak categories and skills to add.
```

### 10.5 Skills Impact Prediction

Based on SkillsBench's published methodology, skills impact (pass_rate_with - pass_rate_without)
varies by category:

| Category Type | Expected Skills Impact | Reasoning |
|--------------|----------------------|-----------|
| **Specialized domains** (quantum, crystallography) | +40-60% | Domain skills contain essential methodology that agents cannot infer |
| **Tool-heavy tasks** (build fixes, migrations) | +20-30% | Skills provide tool configuration and best practices |
| **General reasoning** (planning, analysis) | +5-15% | Skills add context but agent reasoning is primary |
| **Pure coding** (bug fixes, refactoring) | +10-20% | Skills provide codebase context and patterns |

AGENT-33's rich skill governance (invocation modes, execution contexts, tool access control) should
enable **higher skills impact** than baseline agents because AGENT-33 can precisely control how
skills influence agent behavior rather than bulk-injecting all skill content.

### 10.6 Multi-Agent Advantage Prediction

SkillsBench is designed for single-agent evaluation. AGENT-33's multi-agent orchestration provides
a potential advantage that is not measured by the standard benchmark:

| Scenario | Single Agent (SkillsBench standard) | Multi-Agent (AGENT-33) |
|----------|-------------------------------------|----------------------|
| Complex task requiring multiple skill domains | Agent must switch between domains, risking context loss | Orchestrator decomposes task; specialized agents handle each domain |
| Long task exceeding context window | Context management required; older context lost | Each agent works with fresh context on its subtask |
| Task requiring code + review | Agent self-reviews (conflict of interest) | Code-worker produces; QA agent reviews independently |
| Task requiring research + implementation | Agent must interleave research and coding | Researcher gathers context; code-worker implements; parallel execution |

**Prediction**: On complex multi-step tasks, AGENT-33's multi-agent approach should outperform
single-agent baselines by **15-25%**, but this advantage would not be visible in the standard
SkillsBench single-agent evaluation protocol. To measure this, AGENT-33 would need to run both
single-agent and multi-agent configurations against the same tasks.

### 10.7 Cost Efficiency Prediction

AGENT-33's token-saving features should reduce cost-per-task relative to naive approaches:

| Feature | Token Savings | Cost Impact |
|---------|--------------|-------------|
| Progressive recall (3-layer) | ~10x on memory retrieval | Fewer context tokens per LLM call |
| Embedding cache (LRU) | Eliminates duplicate embedding calls | Reduced embedding API costs |
| 4-stage skill matching | Loads content for only 10-12 skills (not all 50+) | Fewer tokens in skill selection |
| Token-aware chunking | Better chunk boundaries reduce redundant content | Higher quality per token |
| Context window management | Summarization reduces message history | Fewer tokens in long conversations |

**Estimated cost reduction**: 30-50% reduction in total tokens per task compared to a naive
approach (load all skills, no caching, no progressive recall).

---

## Appendix A: File Reference

### AGENT-33 Files Referenced in This Analysis

| File | Path | Relevance |
|------|------|-----------|
| Skill definition model | `engine/src/agent33/skills/definition.py` | SkillDefinition with 20+ fields, governance, lifecycle |
| Skill registry | `engine/src/agent33/skills/registry.py` | CRUD, search, progressive disclosure methods |
| Skill injector | `engine/src/agent33/skills/injection.py` | L0/L1 prompt building, tool context resolution |
| Skill loader | `engine/src/agent33/skills/loader.py` | SKILL.md frontmatter parsing, YAML loading, directory discovery |
| BM25 index | `engine/src/agent33/memory/bm25.py` | Custom Okapi BM25 with stop-word removal |
| Hybrid searcher | `engine/src/agent33/memory/hybrid.py` | RRF fusion (k=60) of BM25 + vector results |
| RAG pipeline | `engine/src/agent33/memory/rag.py` | Vector-only and hybrid retrieval modes |
| Token-aware chunker | `engine/src/agent33/memory/ingestion.py` | 1200-token chunks with sentence boundary preservation |
| Embedding cache | `engine/src/agent33/memory/cache.py` | LRU with SHA-256 keys, asyncio.Lock, batch support |
| Progressive recall | `engine/src/agent33/memory/progressive_recall.py` | 3-layer retrieval (index/timeline/full) |
| Agent runtime | `engine/src/agent33/agents/runtime.py` | System prompt construction, LLM invocation, skill/memory injection |
| Provider catalog | `engine/src/agent33/llm/providers.py` | 22+ providers with auto-registration from env vars |
| Tool schema validation | `engine/src/agent33/tools/schema.py` | JSON Schema (Draft 7) validation for tool parameters |
| Execution models | `engine/src/agent33/execution/models.py` | SandboxConfig, ExecutionContract, adapter definitions |
| Evaluation models | `engine/src/agent33/evaluation/models.py` | 10 enums, 10 Pydantic models for gates, metrics, regressions |
| Golden tasks | `engine/src/agent33/evaluation/golden_tasks.py` | GT-01..GT-07 task definitions, GC-01..GC-04 case definitions |
| Failure taxonomy | `engine/src/agent33/observability/failure.py` | 10 categories, 4 severity levels, resolution metadata |
| Main app | `engine/src/agent33/main.py` | Full lifespan wiring of all subsystems |

### SkillsBench Repository Structure (Key Files)

| Path | Purpose |
|------|---------|
| `tasks/` | 86 task directories organized by category |
| `tasks/<category>/<task>/instruction.md` | Task instructions for the agent |
| `tasks/<category>/<task>/task.toml` | Task metadata (category, difficulty, etc.) |
| `tasks/<category>/<task>/environment/Dockerfile` | Container build definition |
| `tasks/<category>/<task>/environment/skills/` | Skills available for this task |
| `tasks/<category>/<task>/solution/solve.sh` | Oracle solution (deterministic) |
| `tasks/<category>/<task>/tests/test_outputs.py` | Pytest assertions for pass/fail |
| `agents/terminus2/` | Terminus-2 agent implementation |
| `agents/terminus2/skill_matcher.py` | 4-stage hybrid matching pipeline |
| `agents/terminus2/context_manager.py` | Message unwinding, summarization |
| `agents/terminus2/tool_loop.py` | Iterative tool-use execution loop |
| `experiments/` | YAML experiment configurations |
| `dashboard/` | React + Recharts metrics visualization |
| `contrib/` | Task Wizard, Quality Checker, etc. |

---

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| **BM25** | Best Matching 25, a probabilistic ranking function for information retrieval based on term frequency and document length normalization |
| **CTRF** | Common Test Results Format, a standardized JSON schema for test results |
| **Double-confirmation** | A pattern where the agent must explicitly confirm task completion before the system accepts it |
| **Harbor** | Container orchestration framework used by SkillsBench for task execution |
| **Handoff summary** | A compact summary of conversation state used when transitioning to a new context window |
| **LiteLLM** | Python library providing a unified interface to 100+ LLM providers |
| **Message unwinding** | Removing the oldest messages from conversation history when approaching context limits |
| **Proactive summarization** | Automatically summarizing older messages when token usage exceeds a threshold |
| **Progressive disclosure** | Revealing information in layers (L0 metadata, L1 instructions, L2 resources) to manage context budgets |
| **Progressive recall** | AGENT-33's 3-layer memory retrieval (index ~50 tokens, timeline ~200 tokens, full ~1000 tokens) |
| **RRF** | Reciprocal Rank Fusion, a method for combining ranked lists without score normalization |
| **Skills impact** | The difference in pass rate between with-skills and without-skills evaluation runs |
| **Terminus-2** | SkillsBench's reference agent implementation with iterative tool use and 4-stage skill matching |

---

## Appendix C: Decision Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Add iterative tool-use loop as P0 | Without this, AGENT-33 agents cannot complete any multi-step SkillsBench task. This is the single largest capability gap. | 2026-02-14 |
| Keep custom BM25Index, don't adopt rank-bm25 | Zero-dependency, already tuned, well-tested, integrates with HybridSearcher. Adding a library adds dependency risk without functional benefit. | 2026-02-14 |
| Add LiteLLM as optional, not required | LiteLLM provides value but should not replace existing provider catalog. Optional dependency preserves AGENT-33's zero-external-LLM-dependency capability (Ollama-only deployments). | 2026-02-14 |
| Multi-agent adapter for SkillsBench, not single-agent simplification | AGENT-33's multi-agent architecture is its core differentiator. Expose a single-agent interface externally while internally leveraging multi-agent capabilities. | 2026-02-14 |
| Feedback loop through Phase 20 improvement system | SkillsBench results should flow through existing infrastructure (research intake, lessons learned, metrics tracking) rather than creating a parallel improvement pipeline. | 2026-02-14 |
| Docker adapter as P2, not P0 | Subprocess sandboxing is sufficient for initial SkillsBench compatibility. Docker isolation is stronger but adds deployment complexity. | 2026-02-14 |
| Binary reward + multi-trial as evaluation methodology | Aligns with SkillsBench's proven methodology. Single-trial evaluation is statistically unreliable for LLM-based agents. 5 trials is the minimum standard. | 2026-02-14 |
