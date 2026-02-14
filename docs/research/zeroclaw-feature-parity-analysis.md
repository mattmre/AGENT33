# ZeroClaw Feature Parity Analysis -- AGENT-33

**Date**: 2026-02-14
**ZeroClaw commit**: Initial analysis (repo created 2026-02-13)
**AGENT-33 commit**: a444afb (main, Phases 1-13 complete)

---

## Executive Summary

**AGENT-33** is a Python/FastAPI multi-agent orchestration engine with a governance layer, DAG-based workflows, session-spanning memory, self-evolving training loops, multi-tenancy, and evidence capture. It prioritizes multi-agent coordination, workflow complexity, and enterprise-grade observability. ~197 tests, ~15 subsystems.

**ZeroClaw** is a Rust single-agent CLI assistant with zero-overhead design, 22+ LLM provider support, hybrid search memory (BM25 + vector), ChaCha20 encryption, multi-channel support, and a skills/plugin system. It prioritizes binary size (~3.4 MB), startup speed (<10ms), and provider agnosticism. ~1,017 tests, 8 core traits.

**Analysis scope**: Every feature in both systems is compared. The goal is to identify features ZeroClaw has that AGENT-33 should absorb, features AGENT-33 already does better, and anti-patterns to avoid. This is a one-way absorption analysis -- ZeroClaw's functional improvements flow into AGENT-33's architecture.

**Key finding**: ZeroClaw's primary advantages over AGENT-33 are in four areas: (1) hybrid search memory, (2) security policy depth (command validation, rate limiting, autonomy levels), (3) provider breadth, and (4) skills/plugin extensibility. AGENT-33 is significantly more capable in orchestration, multi-tenancy, code execution, training, and workflow complexity. The absorption path is clear and non-disruptive.

---

## Feature-by-Feature Comparison Matrix

### 1. LLM Providers

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Provider abstraction | `Provider` trait (`providers/traits.rs`) | `LLMProvider` protocol (`llm/base.py:32-44`) | No | Both use interface-based abstraction |
| Ollama | Yes (`providers/ollama.rs`) | Yes (`llm/ollama.py`) | No | Parity |
| OpenAI-compatible | Yes (`providers/compatible.rs`) | Yes (via `openai_base_url` config, `llm/openai_compat.py`) | No | Parity |
| Anthropic | Yes (`providers/anthropic.rs`) | Via OpenAI-compat proxy (`router.py:18`) | Partial | Add native Anthropic provider |
| OpenRouter | Yes (`providers/openrouter.rs`) | No | **YES** | Add OpenRouter provider |
| Groq | Yes (via compatible) | No | **YES** | Add via OpenAI-compat |
| Mistral | Yes (via compatible) | No | **YES** | Add via OpenAI-compat |
| xAI / Grok | Yes (via compatible) | No | **YES** | Add via OpenAI-compat |
| DeepSeek | Yes (via compatible) | No | **YES** | Add via OpenAI-compat |
| Together | Yes (via compatible) | No | **YES** | Add via OpenAI-compat |
| Fireworks | Yes (via compatible) | No | **YES** | Add via OpenAI-compat |
| Perplexity | Yes (via compatible) | No | **YES** | Add via OpenAI-compat |
| Cohere | Yes (via compatible) | No | **YES** | Add via OpenAI-compat |
| Bedrock | Yes (via compatible) | No | **YES** | Add via dedicated provider |
| Venice | Yes (via compatible) | No | **YES** | Add via OpenAI-compat |
| Custom endpoint | Yes (`custom:https://...`) | Yes (`openai_base_url` config) | No | Parity (different syntax) |
| AirLLM (layer-sharded) | No | Yes (`airllm_enabled` config) | AGENT-33 has | Preserve |
| Model routing | No (single default_provider) | Yes (`llm/router.py:57-73`, prefix-based routing) | AGENT-33 has | Preserve |
| Provider fallback chain | No | No (single provider per prefix) | Both lack | Add fallback chain |
| Connection pooling | Yes (reqwest client reuse) | Yes (`httpx.AsyncClient` with `Limits`, `ollama.py:35-41`) | No | Parity |
| Retry with backoff | No (single attempt in ZeroClaw) | Yes (3 attempts, exponential backoff, `ollama.py:50-73`) | AGENT-33 has | Preserve |
| Provider count | 22+ | 3 (Ollama, OpenAI-compat, AirLLM) | **YES** | Expand via OpenAI-compat registry |

### 2. Memory System

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Memory trait/protocol | `Memory` trait (`memory/traits.rs`) | No unified trait (direct class usage) | **YES** | Add memory protocol |
| Vector search | Cosine similarity in Rust (`memory/vector.rs`) | pgvector cosine distance (`memory/long_term.py:87-93`) | No | Parity |
| BM25/FTS keyword search | SQLite FTS5 with BM25 scoring (`memory/sqlite.rs`) | No | **YES** | Add PostgreSQL full-text search |
| Hybrid search (BM25+vector) | Weighted merge (`memory/vector.rs::hybrid_merge()`) | No | **YES** | Port hybrid merge to Python |
| Configurable weights | `vector_weight`/`keyword_weight` (default 0.7/0.3) | No | **YES** | Add to config |
| Embedding cache | SQLite `embedding_cache` table with LRU | No | **YES** | Add cache to embeddings pipeline |
| Chunking | Line-based markdown chunker (`memory/chunker.rs`) | 500-char chunks (confirmed gap in MEMORY.md) | **YES** | Implement tokenizer-aware chunking |
| RAG pipeline | Memory recall prepended to user message | RAG pipeline with context injection (`memory/rag.py`) | No | Parity (different design) |
| Long-term storage | SQLite with FTS5 + vector BLOBs | PostgreSQL with pgvector extension | No | Different backends, both valid |
| Short-term buffer | No | Yes (`memory/short_term.py`) | AGENT-33 has | Preserve |
| Session state | No | Yes (`memory/session_state.py`) | AGENT-33 has | Preserve |
| Observation capture | No | Yes (`memory/observation.py`) | AGENT-33 has | Preserve |
| Session summarization | No | Yes (`memory/summarizer.py`) | AGENT-33 has | Preserve |
| Memory ingestion | No (auto-save to daily memory) | Yes (`memory/ingestion.py`) | AGENT-33 has | Preserve |
| Retention policies | No | Yes (`memory/retention.py`) | AGENT-33 has | Preserve |
| Progressive recall | No | Yes (used in `runtime.py:196-208`) | AGENT-33 has | Preserve |
| Multi-tenant memory | No (single-user) | Yes (`tenant_id` on all DB models) | AGENT-33 has | Preserve |
| Batch embeddings | No (one at a time) | Yes (`embeddings.py:48-58`, `embed_batch()`) | AGENT-33 has | Preserve |
| Safe reindex | Atomic FTS5 + re-embedding rebuild | No | **YES** | Add reindex capability |

### 3. Security

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| JWT auth | No | Yes (`security/auth.py:32-50`) | AGENT-33 has | Preserve |
| API key auth | No (bearer token via pairing) | Yes (`security/auth.py:66-92`) | AGENT-33 has | Preserve |
| Scope-based permissions | No | Yes (`security/permissions.py`, 8 scopes) | AGENT-33 has | Preserve |
| Auth middleware | No (gateway pairing only) | Yes (`security/middleware.py`, `AuthMiddleware`) | AGENT-33 has | Preserve |
| Command allowlisting | Yes (`security/policy.rs::is_command_allowed()`) | Yes (`tools/governance.py:51-59`, `tools/builtin/shell.py:49-53`) | Partial | ZeroClaw's is deeper -- see Security Deep Dive |
| Multi-segment command validation | Yes (validates every command in pipes/chains, blocks subshells) | No (only checks first executable) | **YES** | Port pipeline validation |
| Path traversal prevention | Yes (blocks `..`, null bytes, symlink escape, absolute paths) | Partial (`tools/builtin/file_ops.py:101-109`, uses `resolve()` + prefix check) | **YES** | Add null byte, symlink, absolute path checks |
| Rate limiting | Yes (sliding-window `ActionTracker`) | No | **YES** | Add to tool execution pipeline |
| Autonomy levels | Yes (ReadOnly/Supervised/Full) | No | **YES** | Add to agent definitions |
| Encryption at rest | ChaCha20-Poly1305 AEAD (`security/secrets.rs`) | AES-256-GCM AESGCM (`security/encryption.py`) | No | Both use modern AEAD -- AES-256-GCM is equivalent |
| Secret store | File-based with `enc2:` prefix | In-memory `CredentialVault` (`security/vault.py`) | Different | Both valid; AGENT-33's is ephemeral |
| Prompt injection detection | No | Yes (`security/injection.py`, 15+ regex patterns, base64 decode) | AGENT-33 has | Preserve |
| Safety guardrails in prompt | Yes (hardcoded in `build_system_prompt()`) | Yes (hardcoded in `runtime.py:114-123`) | No | Parity (both have guardrails) |
| Governance constraints in prompt | No (no governance model) | Partial (model exists in `definition.py:153-159`, injected in `runtime.py:64-74`) | AGENT-33 has | Was fixed -- now injected |
| Gateway pairing | Yes (6-digit code, brute-force lockout, constant-time comparison) | Partial (`messaging/pairing.py`, 6-digit code, TTL, no brute-force lockout) | **YES** | Add lockout + constant-time compare |
| Workspace sandboxing | Yes (workspace_only mode, path scoping) | Yes (`ToolContext.working_dir`, path allowlist) | No | Parity |
| Production secret warnings | No | Yes (`config.py:86-98`, `check_production_secrets()`) | AGENT-33 has | Preserve |
| Request size limits | Yes (64KB max) | No explicit limit (FastAPI defaults) | **YES** | Add request size middleware |
| Read timeout (slow-loris) | Yes (30s read timeout on raw TCP) | No explicit (uvicorn defaults) | Partial | Configure uvicorn timeouts |

### 4. Tool System

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Tool trait/protocol | `Tool` trait with JSON Schema (`tools/traits.rs`) | `Tool` protocol (`tools/base.py:39-53`) | No | Parity |
| JSON Schema for parameters | Yes (self-describing via `parameters_schema()`) | No (params are untyped `dict[str, Any]`) | **YES** | Add JSON Schema to Tool protocol |
| Tool registry | Manual registration in `main.rs` | Yes (`tools/registry.py`, YAML defs, entry points) | AGENT-33 has | Preserve |
| Tool governance/audit | No | Yes (`tools/governance.py`, permission checks, audit logging) | AGENT-33 has | Preserve |
| Shell tool | Yes (`tools/shell.rs`) | Yes (`tools/builtin/shell.py`) | No | Parity |
| File read | Yes (`tools/file_read.rs`) | Yes (`tools/builtin/file_ops.py`, read operation) | No | Parity |
| File write | Yes (`tools/file_write.rs`) | Yes (`tools/builtin/file_ops.py`, write operation) | No | Parity |
| File list | No | Yes (`tools/builtin/file_ops.py`, list operation) | AGENT-33 has | Preserve |
| Memory store/recall/forget | Yes (3 separate tools) | Via memory subsystem (not as tool interface) | Different | Consider tool wrappers for memory ops |
| Browser (Playwright) | No (only `browser_open` -- opens URL in Brave) | Yes (`tools/builtin/browser.py`, full Playwright automation) | AGENT-33 has | Preserve |
| Web fetch | No | Yes (`tools/builtin/web_fetch.py`) | AGENT-33 has | Preserve |
| Web search (SearXNG) | No | Yes (`tools/builtin/search.py`) | AGENT-33 has | Preserve |
| Reader (web content extraction) | No | Yes (`tools/builtin/reader.py`) | AGENT-33 has | Preserve |
| Composio (1000+ OAuth apps) | Yes (`tools/composio.rs`) | No | **YES** | Consider Composio integration |
| Tool-use loop (iterative) | No (tools are decorative -- never parsed from LLM response) | Partial (agent loop calls LLM once, no tool iteration) | Both lack | Implement tool-use loop |
| Tool entrypoint discovery | No | Yes (`registry.py:78-98`, `discover_from_entrypoints()`) | AGENT-33 has | Preserve |
| Tool status management | No | Yes (`registry.py:118-130`, active/deprecated) | AGENT-33 has | Preserve |

### 5. Channel/Messaging

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Telegram | Yes (`channels/telegram.rs`) | Yes (`messaging/telegram.py`) | No | Parity |
| Discord | Yes (`channels/discord.rs`) | Yes (`messaging/discord.py`) | No | Parity |
| Slack | Yes (`channels/slack.rs`) | Yes (`messaging/slack.py`) | No | Parity |
| iMessage | Yes (`channels/imessage.rs`) | No | **YES** | Consider (macOS-only) |
| Matrix | Yes (`channels/matrix.rs`) | No | **YES** | Add Matrix adapter |
| WhatsApp | No | Yes (`messaging/whatsapp.py`) | AGENT-33 has | Preserve |
| CLI channel | Yes (`channels/cli.rs`) | No (FastAPI routes serve as interface) | Different | Not needed -- API-first design |
| Webhook channel | Yes (via gateway) | Yes (via webhook routes) | No | Parity |
| Channel trait/protocol | `Channel` trait (`channels/traits.rs`) | `MessagingAdapter` protocol (`messaging/base.py`) | No | Parity |
| Channel health checks | Yes (`doctor_channels()`) | No | **YES** | Add health check to adapters |
| Message bus | `tokio::sync::mpsc` (in-process) | NATS (`messaging/bus.py`) | Different | NATS is more capable (distributed) |
| Channel multiplexing | Yes (all channels -> single mpsc) | Yes (all adapters -> NATS bus) | No | Parity |
| Signature verification | Yes (Discord Ed25519 in gateway) | Yes (Slack HMAC, Discord Ed25519) | No | Parity |
| Pairing system | Yes (`messaging/pairing.py`) | Yes (`messaging/pairing.py`) | No | Parity |

### 6. Configuration

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Config format | TOML (`~/.zeroclaw/config.toml`) | Environment variables + .env (`config.py`) | Different | Both valid approaches |
| Config schema validation | Rust struct with serde (`config/schema.rs`) | Pydantic BaseSettings (`config.py`) | No | Parity (both type-safe) |
| Hot-reload | No (compile-time) | No (startup-time) | Both lack | Consider for future |
| Extensible config sections | Yes (per-subsystem TOML sections) | Yes (flat env vars) | Different | TOML is more structured |
| Config-driven composition | Yes (change backend by config string) | Partial (limited to LLM routing) | **YES** | Add config-driven subsystem swapping |

### 7. Observability

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Observer trait | `Observer` trait (`observability/traits.rs`) | No unified trait | Different | AGENT-33 uses structlog + OTel |
| Structured logging | Via `tracing` crate (Rust) | Yes (`structlog`) | No | Parity |
| OpenTelemetry | No | Yes (`observability/tracing.py`, OTel integration) | AGENT-33 has | Preserve |
| Metrics | `ObserverMetric` enum (RequestLatency, TokensUsed, etc.) | Implicit in structlog | Partial | Add explicit metrics types |
| Event types | 6 events (AgentStart, AgentEnd, ToolCall, etc.) | Flexible structlog events | No | Parity |
| Multi-observer fanout | Yes (`MultiObserver`) | No (single log pipeline) | **YES** | Add observer composition |
| Lineage tracking | No | Yes (`observability/lineage.py`) | AGENT-33 has | Preserve |
| Replay | No | Yes (`observability/replay.py`) | AGENT-33 has | Preserve |
| Alerts | No | Yes (`observability/alerts.py`) | AGENT-33 has | Preserve |
| Token counting | `Option<u64>` (always None) | Yes (tracked in `LLMResponse.total_tokens`) | AGENT-33 has | Preserve |

### 8. Skills/Plugins

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Skill format | TOML manifest + Markdown (`skills/mod.rs`) | No skill system | **YES** | Implement skill loading |
| Skill installation | `skills install <github-url>` (git clone) | No | **YES** | Add skill install CLI |
| Skill-to-prompt injection | Skills injected as XML in system prompt | No | **YES** | Add skill prompt injection |
| On-demand skill loading | Compact XML summary; full content loaded on demand | No | **YES** | Design lazy skill loading |
| Integration catalog | 50+ integrations across 9 categories | No formal catalog | **YES** | Consider integration registry |
| Runtime plugins (dynamic) | No (compile-time only) | Yes (entrypoint discovery, YAML defs) | AGENT-33 has | Preserve |

### 9. Orchestration

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Multi-agent | No (single-agent system) | Yes (6 agent definitions, registry, DAG workflows) | AGENT-33 has | Preserve -- core differentiator |
| DAG workflows | No | Yes (`workflows/executor.py`, topological sort, parallel groups) | AGENT-33 has | Preserve |
| Agent-to-agent handoffs | No | Yes (via workflow steps + `invoke_agent` action) | AGENT-33 has | Preserve |
| Conditional branching | No | Yes (`StepAction.CONDITIONAL`, then/else branches) | AGENT-33 has | Preserve |
| Parallel execution | No | Yes (`StepAction.PARALLEL_GROUP`, semaphore-limited) | AGENT-33 has | Preserve |
| Step retries | No | Yes (per-step retry config with backoff) | AGENT-33 has | Preserve |
| Step timeouts | No | Yes (`asyncio.wait_for` per step) | AGENT-33 has | Preserve |
| Expression evaluation | No | Yes (`workflows/expressions.py`, condition + input resolution) | AGENT-33 has | Preserve |
| Backpressure control | No | Yes (`BackpressureController` in `executor.py:358-396`) | AGENT-33 has | Preserve |
| Wait/delay steps | No | Yes (`StepAction.WAIT`) | AGENT-33 has | Preserve |

### 10. Gateway/API

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| HTTP server | Raw TCP (`gateway/mod.rs`) | FastAPI (`main.py`) | AGENT-33 has | Preserve -- FastAPI is far superior |
| REST API | 3 endpoints (health, pair, webhook) | 9+ route files, full CRUD, versioned under /v1 | AGENT-33 has | Preserve |
| OpenAPI docs | No | Yes (FastAPI auto-generates) | AGENT-33 has | Preserve |
| CORS | No | Yes (`cors_allowed_origins` config) | AGENT-33 has | Preserve |
| Pairing endpoint | `POST /pair` (6-digit code -> bearer) | Via webhook routes | Different | Consider adding dedicated pair endpoint |
| Webhook endpoint | `POST /webhook` | Yes (`routes/webhooks.py`) | No | Parity |
| Health check | `GET /health` | Yes (`routes/health.py`) | No | Parity |
| Dashboard | No | Yes (`routes/dashboard.py`) | AGENT-33 has | Preserve |
| Memory search API | No | Yes (`routes/memory_search.py`) | AGENT-33 has | Preserve |

### 11. Tunnel/Deployment

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Tunnel abstraction | `Tunnel` trait + factory (`tunnel/mod.rs`) | No | Different | Not needed -- Docker/K8s deployment |
| Cloudflare tunnel | Yes (`tunnel/cloudflare.rs`) | No | Low priority | Standard reverse proxy suffices |
| Tailscale tunnel | Yes (`tunnel/tailscale.rs`) | No | Low priority | Standard reverse proxy suffices |
| ngrok tunnel | Yes (`tunnel/ngrok.rs`) | No | Low priority | Standard reverse proxy suffices |
| Docker support | Yes (Dockerfile) | Yes (`docker-compose.yml`) | No | Parity |
| Docker Compose | No | Yes (full stack: postgres, redis, nats, ollama) | AGENT-33 has | Preserve |

### 12. Code Execution

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Execution contracts | No | Yes (`execution/models.py`, `ExecutionContract`) | AGENT-33 has | Preserve |
| Sandbox config | No | Yes (`SandboxConfig`: timeout, memory, CPU, filesystem, network, process limits) | AGENT-33 has | Preserve |
| Adapter abstraction | No | Yes (`execution/adapters/`, BaseAdapter, CLIAdapter) | AGENT-33 has | Preserve |
| Input validation | No | Yes (`execution/validation.py`, IV-01..05 validators) | AGENT-33 has | Preserve |
| Progressive disclosure | No | Yes (`execution/disclosure.py`, L0-L3 levels) | AGENT-33 has | Preserve |
| Code executor pipeline | No | Yes (`execution/executor.py`) | AGENT-33 has | Preserve |
| Adapter types | No | Yes (CLI, API, SDK, MCP) | AGENT-33 has | Preserve |

### 13. Training/Self-Improvement

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Self-evaluation | No | Yes (`training/evaluator.py`, LLM-as-judge) | AGENT-33 has | Preserve |
| Rollout capture | No | Yes (`training/runner.py`, trace-and-evaluate) | AGENT-33 has | Preserve |
| Optimization loop | No | Yes (`training/optimizer.py`) | AGENT-33 has | Preserve |
| Training scheduler | No | Yes (`training/scheduler.py`, idle-optimize) | AGENT-33 has | Preserve |
| Training store | No | Yes (`training/store.py`) | AGENT-33 has | Preserve |
| Code evaluation | No | Yes (`evaluator.py:63-73`, `evaluate_code()`) | AGENT-33 has | Preserve |
| Workflow evaluation | No | Yes (`evaluator.py:75-91`, `evaluate_workflow()`) | AGENT-33 has | Preserve |
| Batch rollouts | No | Yes (`runner.py:84-95`, bounded parallelism) | AGENT-33 has | Preserve |

### 14. Multi-Tenancy

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Tenant isolation | No (single-user) | Yes (`tenant_id` on all DB models) | AGENT-33 has | Preserve |
| User management | No | Yes (JWT subjects, API key subjects) | AGENT-33 has | Preserve |
| RBAC | No | Yes (scope-based, `permissions.py`) | AGENT-33 has | Preserve |
| Per-tenant config | No | No | Both lack | Consider for future |

### 15. Performance

| Feature | ZeroClaw | AGENT-33 | Gap? | Action |
|---------|----------|----------|------|--------|
| Binary size | ~3.4 MB | N/A (Python) | Different paradigm | N/A |
| Startup time | <10ms | ~2-5s (FastAPI + subsystem init) | Different paradigm | Optimize lifespan init |
| Memory usage | ~20 MB | ~100-200 MB (Python + deps) | Different paradigm | N/A |
| Connection pooling | Yes (reqwest) | Yes (`httpx.AsyncClient` with `Limits`) | No | Parity |
| Batch embeddings | No | Yes (`embed_batch()` in `embeddings.py:48`) | AGENT-33 has | Preserve |
| Concurrent channels | Yes (tokio::spawn per channel) | Yes (asyncio tasks per adapter) | No | Parity |

---

## Features ZeroClaw Has That AGENT-33 Lacks

### Gap 1: Hybrid Search Memory (BM25 + Vector + Weighted Merge)

**What ZeroClaw does**: `memory/vector.rs::hybrid_merge()` combines FTS5 BM25 keyword scores with vector cosine similarity using configurable weights (default 0.7 vector, 0.3 keyword). `memory/sqlite.rs` provides the SQLite FTS5 backend. This gives dramatically better recall for both exact-term queries and semantic queries.

**Why AGENT-33 needs it**: AGENT-33's RAG pipeline (`memory/rag.py`) is vector-only. This was identified as the #1 architecture gap in the research sprint (see `docs/research/integration-report-2026-02-13.md`). Vector-only search fails on exact terms, identifiers, error codes, and proper nouns -- precisely the things agents need most.

**How to implement**: PostgreSQL has native full-text search via `tsvector`/`tsquery` with ranking. No new dependencies needed.

1. Add a `tsvector` column to `memory_records` in `memory/long_term.py`
2. Create a GIN index on the tsvector column
3. Add a `keyword_search()` method that uses `ts_rank()` for BM25-like scoring
4. Implement `hybrid_search()` that runs both searches and merges: `final = vector_weight * vector_score + keyword_weight * keyword_score`
5. Add `vector_weight` and `keyword_weight` to `config.py`
6. Update `RAGPipeline.query()` in `memory/rag.py` to use hybrid search

**Estimated effort**: 2-3 days
**Dependencies**: None (PostgreSQL FTS is built-in)
**Priority**: HIGH

### Gap 2: Multi-Segment Command Validation

**What ZeroClaw does**: `security/policy.rs::is_command_allowed()` validates entire command pipelines, not just the first executable. It blocks: backtick subshells, `$()` substitutions, output redirections (`>`, `>>`, `|`), and validates every command in pipe chains.

**Why AGENT-33 needs it**: AGENT-33's shell tool (`tools/builtin/shell.py:49-53`) and governance (`tools/governance.py:51-59`) only check the first executable in a command string. An attacker could bypass allowlisting with `ls | rm -rf /` where `ls` is allowed but `rm` is not.

**How to implement**:

1. Add `validate_command_pipeline()` function to `tools/builtin/shell.py`
2. Split command on `;`, `&&`, `||`, `|` separators
3. Check each segment's executable against the allowlist
4. Block subshell operators: backticks, `$(...)`, `>(...)`, `<(...)`
5. Optionally block output redirections (`>`, `>>`, `2>`)
6. Integrate into `ShellTool.execute()` before subprocess creation

**Target files**: `engine/src/agent33/tools/builtin/shell.py`, `engine/src/agent33/tools/governance.py`
**Estimated effort**: 1 day
**Dependencies**: None
**Priority**: HIGH

### Gap 3: Autonomy Levels (ReadOnly / Supervised / Full)

**What ZeroClaw does**: `security/policy.rs::AutonomyLevel` defines three levels that gate what the agent can do. ReadOnly prevents any writes/commands. Supervised requires approval. Full allows autonomous execution. Enforced at every tool invocation.

**Why AGENT-33 needs it**: AGENT-33 has `GovernanceConstraints` in `definition.py:153-159` but no autonomy level concept. All agents operate at the same permission level. This is needed for Phase 14 (Security Hardening).

**How to implement**:

1. Add `AutonomyLevel` enum to `agents/definition.py`: `READ_ONLY`, `SUPERVISED`, `FULL`
2. Add `autonomy_level` field to `GovernanceConstraints` (default `SUPERVISED`)
3. Add autonomy check in `ToolGovernance.pre_execute_check()` (`tools/governance.py:27`)
4. For `SUPERVISED` level, return a pending-approval result instead of executing
5. Inject autonomy level into system prompt via `runtime.py:_build_system_prompt()`
6. Update the 6 JSON agent definitions to declare appropriate levels

**Target files**: `engine/src/agent33/agents/definition.py`, `engine/src/agent33/tools/governance.py`, `engine/src/agent33/agents/runtime.py`
**Estimated effort**: 2 days
**Dependencies**: Phase 14 (Security Hardening)
**Priority**: HIGH

### Gap 4: Rate Limiting on Tool Execution

**What ZeroClaw does**: `security/policy.rs::ActionTracker` implements a sliding-window rate limiter. Tracks actions per hour and blocks execution when the limit is exceeded.

**Why AGENT-33 needs it**: AGENT-33 has no rate limiting on tool invocations. A runaway agent could execute unlimited commands.

**How to implement**:

1. Add `RateLimiter` class to `tools/governance.py`
2. Use a sliding window with Redis (already a dependency) or in-memory deque
3. Configure via `config.py`: `tool_rate_limit_per_hour: int = 100`
4. Check in `ToolGovernance.pre_execute_check()` before permission checks
5. Return `ToolResult.fail("Rate limit exceeded")` when blocked

**Target files**: `engine/src/agent33/tools/governance.py`, `engine/src/agent33/config.py`
**Estimated effort**: 1 day
**Dependencies**: None (Redis already available)
**Priority**: HIGH

### Gap 5: Embedding Cache

**What ZeroClaw does**: SQLite `embedding_cache` table stores hash(text) -> embedding vector, with LRU eviction. Avoids redundant API calls for identical text.

**Why AGENT-33 needs it**: During reindexing or when the same content is embedded multiple times, AGENT-33 calls the embedding API redundantly. This wastes time and API credits.

**How to implement**:

1. Add `embedding_cache` table via Alembic migration (columns: `text_hash`, `embedding`, `created_at`, `access_count`)
2. In `EmbeddingProvider.embed()` (`memory/embeddings.py:38`), check cache before API call
3. In `embed_batch()`, filter out cached embeddings, only request uncached
4. Add LRU eviction: delete oldest entries when cache exceeds configurable size
5. Add `embedding_cache_size: int = 10000` to `config.py`

**Target files**: `engine/src/agent33/memory/embeddings.py`, `engine/src/agent33/config.py`
**Estimated effort**: 1-2 days
**Dependencies**: None
**Priority**: MEDIUM

### Gap 6: JSON Schema on Tool Protocol

**What ZeroClaw does**: `Tool` trait includes `parameters_schema() -> serde_json::Value` that returns a JSON Schema describing the tool's parameters. This makes tools self-describing for LLM function calling.

**Why AGENT-33 needs it**: AGENT-33's `Tool` protocol (`tools/base.py:39-53`) has no schema method. Parameters are untyped `dict[str, Any]`. When tools are listed in the system prompt, there's no structured way to describe parameters.

**How to implement**:

1. Add `parameters_schema` property to `Tool` protocol in `tools/base.py`
2. Return a JSON Schema dict describing expected parameters
3. Add schema to each builtin tool (shell, file_ops, web_fetch, browser, search, reader)
4. Use schema in system prompt construction to describe available tools
5. Use schema for input validation before tool execution

**Target files**: `engine/src/agent33/tools/base.py`, all builtin tools
**Estimated effort**: 2 days
**Dependencies**: None
**Priority**: MEDIUM

### Gap 7: Skills/Plugin System

**What ZeroClaw does**: Skills are user-defined capability packs stored as directories with `SKILL.toml` (structured manifest with tools and prompts) or `SKILL.md` (simple instructions). Installed via `zeroclaw skills install <github-url>`. Skills are injected into the system prompt as compact XML summaries with on-demand full loading.

**Why AGENT-33 needs it**: AGENT-33 has agent definitions (JSON) and tool registry (YAML), but no user-installable skill packs that combine tools + prompts + configuration. The skills pattern would enable community contributions.

**How to implement**:

1. Define a `SkillManifest` Pydantic model (name, version, author, tools, prompts, tags)
2. Create `skills/` module with `load_skill()`, `install_skill()`, `remove_skill()`
3. Support YAML manifest format (aligned with existing tool YAML defs)
4. Add skill installation from GitHub URL or local path
5. Inject skill summaries into agent system prompts
6. Add `agent33 skills install/list/remove` CLI commands

**Target files**: New module `engine/src/agent33/skills/`
**Estimated effort**: 3-4 days
**Dependencies**: None
**Priority**: MEDIUM

### Gap 8: Channel Health Checks

**What ZeroClaw does**: `doctor_channels()` in `channels/mod.rs` runs health checks on all configured channels, reporting connection status, latency, and configuration validity.

**Why AGENT-33 needs it**: AGENT-33's messaging adapters have no health check method. When a channel fails silently, there's no diagnostic path.

**How to implement**:

1. Add `async def health_check(self) -> HealthStatus` to `MessagingAdapter` protocol
2. Implement per-adapter health checks (Telegram: `getMe`, Discord: gateway ping, Slack: `auth.test`)
3. Add `/v1/messaging/health` endpoint that runs all adapter health checks
4. Add `agent33 messaging doctor` CLI command

**Target files**: `engine/src/agent33/messaging/base.py`, all adapters, new route
**Estimated effort**: 1-2 days
**Dependencies**: None
**Priority**: MEDIUM

### Gap 9: Provider Registry Expansion (OpenRouter, Groq, etc.)

**What ZeroClaw does**: Supports 22+ providers. Most are OpenAI-compatible endpoints with different base URLs and auth patterns.

**Why AGENT-33 needs it**: AGENT-33 only has 3 providers (Ollama, OpenAI-compat, AirLLM). The `ModelRouter` already has prefix-based routing, but needs more providers registered.

**How to implement**:

1. Create a `providers.yaml` config listing well-known OpenAI-compatible providers
2. Each entry: name, base_url, auth_header_name, model_prefix, env_var for API key
3. In `main.py` lifespan, auto-register providers from the YAML for any that have API keys configured
4. Add config vars: `openrouter_api_key`, `groq_api_key`, `anthropic_api_key`, etc.
5. Add prefix mapping entries to `ModelRouter._DEFAULT_PREFIX_MAP`

**Target files**: `engine/src/agent33/config.py`, `engine/src/agent33/llm/router.py`, `engine/src/agent33/main.py`
**Estimated effort**: 2 days
**Dependencies**: None
**Priority**: MEDIUM

### Gap 10: Pairing Brute-Force Lockout

**What ZeroClaw does**: `security/pairing.rs` implements constant-time comparison, tracks failed attempts per IP, and locks out after N failures.

**Why AGENT-33 needs it**: AGENT-33's `PairingManager` (`messaging/pairing.py:57-72`) verifies codes but has no brute-force protection. An attacker could try all 1M codes.

**How to implement**:

1. Add `_failed_attempts: dict[str, int]` and `_lockouts: dict[str, datetime]` to `PairingManager`
2. After 5 failures, lock out the source for 15 minutes
3. Use `hmac.compare_digest()` for constant-time code comparison (Python stdlib)
4. Clear failure count on successful verification

**Target files**: `engine/src/agent33/messaging/pairing.py`
**Estimated effort**: 0.5 days
**Dependencies**: None
**Priority**: LOW

### Gap 11: Matrix Channel Adapter

**What ZeroClaw does**: `channels/matrix.rs` provides a Matrix protocol adapter.

**Why AGENT-33 needs it**: Matrix is an open, federated messaging protocol. Adding it expands self-hosted deployment options.

**How to implement**:

1. Add `MatrixAdapter` in `messaging/matrix.py`
2. Use `matrix-nio` library (async Matrix client for Python)
3. Implement `MessagingAdapter` protocol: send, receive, start, stop
4. Add `matrix_homeserver_url` and `matrix_access_token` to config

**Target files**: New file `engine/src/agent33/messaging/matrix.py`, `engine/src/agent33/config.py`
**Estimated effort**: 1-2 days
**Dependencies**: `matrix-nio` optional dependency
**Priority**: LOW

### Gap 12: Request Size Limits

**What ZeroClaw does**: Gateway enforces 64KB max request size to prevent memory exhaustion.

**Why AGENT-33 needs it**: FastAPI/Starlette has no built-in request size limit. Large payloads could cause OOM.

**How to implement**:

1. Add `ContentSizeLimitMiddleware` to `main.py`
2. Check `Content-Length` header and reject if > configurable limit
3. Add `max_request_size_bytes: int = 1_048_576` to `config.py` (1 MB default)

**Target files**: `engine/src/agent33/main.py`, `engine/src/agent33/config.py`
**Estimated effort**: 0.5 days
**Dependencies**: None
**Priority**: LOW

---

## Features AGENT-33 Has That ZeroClaw Lacks

These represent AGENT-33's competitive advantages and must not be regressed during absorption.

### 1. Multi-Agent Orchestration (Critical)
AGENT-33 has a full DAG-based workflow engine (`workflows/executor.py`) with 8 action types (invoke_agent, run_command, validate, transform, conditional, parallel_group, wait, execute_code), topological sort, expression evaluation, conditional branching, parallel execution with semaphore limiting, retry with backoff, timeouts, and backpressure control. ZeroClaw has none of this -- it is a single-agent, single-turn system.

### 2. Code Execution Layer (Critical)
Full `execution/` subsystem with `ExecutionContract` (declaring sandbox config, inputs, expected outputs), `SandboxConfig` (timeout, memory, CPU, filesystem, network, process limits), 5 input validators, adapter abstraction (CLI, API, SDK, MCP), and progressive disclosure (L0-L3). ZeroClaw has no code execution abstraction.

### 3. Training/Self-Improvement Loop (Critical)
Complete training subsystem: `TrainingRunner` (rollout capture), `SelfEvaluator` (LLM-as-judge scoring), `TraceEmitter` (span capture), `TrainingStore` (persistence), `TrainingAlgorithm` (optimization), `TrainingScheduler` (idle-optimize triggers). ZeroClaw has no self-improvement capability.

### 4. Multi-Tenancy (Important)
`tenant_id` on all DB models, JWT/API-key auth with subject tracking, scope-based RBAC (8 scopes), auth middleware on all routes. ZeroClaw is single-user only.

### 5. Prompt Injection Defense (Important)
`security/injection.py` has 15+ regex patterns across 3 categories (system override, delimiter injection, instruction override), base64 encoded payload detection, recursive nested structure scanning. ZeroClaw has no injection defense.

### 6. Memory Sophistication (Important)
Short-term buffer, long-term pgvector store, observation capture, session state, session summarization, ingestion pipeline, retention policies, progressive recall. ZeroClaw has simple auto-save-to-daily-memory only.

### 7. Evidence/Audit Capture (Important)
Structured audit logging in `tools/governance.py`, observation capture in `memory/observation.py`, lineage tracking in `observability/lineage.py`, replay in `observability/replay.py`. ZeroClaw logs events but has no replay or lineage.

### 8. Agent Definition Schema (Moderate)
Rich Pydantic models: `AgentDefinition` with role taxonomy (10 roles), capability taxonomy (25 spec capabilities across 5 categories), governance constraints, ownership, dependencies, input/output parameters, execution constraints. ZeroClaw agents are configured by workspace markdown files only.

### 9. OpenTelemetry Integration (Moderate)
`observability/tracing.py` has OTel `TracerProvider`, span management, console exporter. ZeroClaw mentions extending to Prometheus but has no implementation.

### 10. Browser Automation (Moderate)
Full Playwright integration (`tools/builtin/browser.py`) with 10 actions (navigate, screenshot, extract_text, click, type_text, select, scroll, wait_for, get_elements, close_session), persistent sessions with TTL cleanup, headless and one-shot modes. ZeroClaw only has `browser_open` which opens URLs in Brave.

### 11. Web Search (Moderate)
SearXNG integration (`tools/builtin/search.py`) providing privacy-respecting web search. ZeroClaw has no search capability.

### 12. Automation/Scheduling (Minor)
APScheduler integration, webhooks, dead-letter queue, event sensors. ZeroClaw has a `HEARTBEAT.md`-based periodic runner that is far simpler.

---

## Security Deep Dive

### Authentication Models

| Aspect | ZeroClaw | AGENT-33 |
|--------|----------|----------|
| Auth mechanism | Gateway pairing (6-digit code -> bearer token) | JWT + API keys (SHA256 hashed) |
| Token format | Opaque bearer string | Signed JWT with claims (sub, scopes, exp, iat) |
| Multi-user | No | Yes (subjects + scopes) |
| Session expiry | No explicit expiry | Configurable (`jwt_expire_minutes`, default 60) |
| Revocation | No (bearer token is permanent) | Yes (`revoke_api_key()` in `auth.py:95-107`) |

**Winner**: AGENT-33 -- significantly more mature auth with JWT claims, scopes, expiry, and revocation.

### Encryption

| Aspect | ZeroClaw | AGENT-33 |
|--------|----------|----------|
| Algorithm | ChaCha20-Poly1305 AEAD | AES-256-GCM AESGCM |
| Nonce | Random per-encryption | Random per-encryption |
| Key derivation | Raw 256-bit key from file | `AESGCM.generate_key()` |
| Storage | File at `~/.zeroclaw/.secret_key` (0600 perms) | In-memory (ephemeral) |
| Legacy migration | XOR cipher -> ChaCha20 migration path | None needed |
| Tamper detection | Poly1305 authentication tag | GCM authentication tag |

**Verdict**: Equivalent security strength. Both are modern AEAD ciphers. ChaCha20-Poly1305 is marginally faster in software (no AES-NI), AES-256-GCM is hardware-accelerated. No gap.

### Command Allowlisting

| Aspect | ZeroClaw | AGENT-33 |
|--------|----------|----------|
| Scope | Full pipeline validation | First executable only |
| Subshell blocking | Backticks, `$()` | None |
| Pipe validation | Each command in pipe chain | Only first command |
| Redirect blocking | `>`, `>>`, `|` optionally | None |
| Null byte blocking | Yes | No |
| Full command parsing | Yes (split on operators) | `shlex.split()` for first token |

**Winner**: ZeroClaw -- significantly more thorough. This is the highest-priority security gap to close.

### Path Validation

| Aspect | ZeroClaw | AGENT-33 |
|--------|----------|----------|
| Traversal (`..`) | Explicit block | Handled by `Path.resolve()` (implicit) |
| Null bytes | Explicit block | Not checked |
| Symlink escape | Verify resolved path stays in workspace | Uses `resolve()` but no explicit symlink check |
| Absolute paths | Block when workspace_only | Not restricted (only prefix check) |
| Forbidden system paths | `/etc`, `/proc`, etc. blocked | Not blocked |

**Winner**: ZeroClaw -- more defense-in-depth layers. AGENT-33's `resolve()` + prefix approach handles traversal implicitly but misses null bytes and system path blocking.

### Rate Limiting

| Aspect | ZeroClaw | AGENT-33 |
|--------|----------|----------|
| Implementation | Sliding window `ActionTracker` | None |
| Scope | Per-agent actions per hour | N/A |
| Configurability | Max actions configurable | N/A |

**Winner**: ZeroClaw -- AGENT-33 has no rate limiting at all.

### Pairing/Brute-Force Protection

| Aspect | ZeroClaw | AGENT-33 |
|--------|----------|----------|
| Code format | 6-digit numeric | 6-digit numeric |
| TTL | Yes | Yes (15 minutes) |
| Brute-force lockout | Yes (failed attempt tracking) | No |
| Constant-time compare | Yes | No (`==` operator) |
| Auto-cleanup | Not documented | Yes (periodic cleanup task) |

**Winner**: ZeroClaw -- lockout + constant-time comparison prevent timing and brute-force attacks.

### Prompt Injection Defense

| Aspect | ZeroClaw | AGENT-33 |
|--------|----------|----------|
| Detection | None | 15+ patterns across 3 categories |
| Base64 decoding | None | Yes (decode + re-scan) |
| Recursive scanning | None | Yes (nested dicts/lists) |
| System prompt hardening | Safety rules in prompt | Safety rules in prompt + governance constraints |

**Winner**: AGENT-33 -- ZeroClaw has zero prompt injection defense.

---

## Runtime Security Comparison

### Sandbox Isolation Models

**ZeroClaw**: No formal sandbox. Security is enforced at the command allowlist level (`SecurityPolicy`). The agent runs in the user's process with full filesystem access (scoped by workspace_only flag). No memory limits, no CPU limits, no network restrictions.

**AGENT-33**: Full `SandboxConfig` model (`execution/models.py:39-47`) with timeout (1-600s), memory (64-4096 MB), CPU cores (1-4), filesystem policy (read/write/deny lists), network policy (enabled/allow/deny), process policy (max children, fork control). Enforced by the `CodeExecutor` pipeline.

**Winner**: AGENT-33 -- formal contract-based sandboxing vs. ad-hoc allowlisting.

### Permission Enforcement Timing

**ZeroClaw**: Compile-time trait bounds + runtime allowlist checks. The Rust type system prevents certain categories of errors at compile time.

**AGENT-33**: Runtime checks in `ToolGovernance.pre_execute_check()` before every tool invocation. Python's dynamic typing means all checks are runtime.

**Verdict**: Different paradigms. Rust's compile-time guarantees are stronger for the checks that can be expressed in the type system. AGENT-33's runtime approach is more flexible for dynamic policies.

### Autonomy Levels

**ZeroClaw**: Three levels (ReadOnly, Supervised, Full) enforced at every tool call.

**AGENT-33**: No autonomy levels yet. All tools execute at the same permission level (subject to scope checks).

**Action**: Adopt ZeroClaw's three-level model in AGENT-33's governance layer.

### Approval Gates

**ZeroClaw**: Supervised mode would require approval, but the implementation details are unclear (single-user CLI system).

**AGENT-33**: `GovernanceConstraints.approval_required` field exists but is not enforced at runtime. Phase 14 is planned to implement enforcement.

**Action**: Phase 14 should implement approval gates using the `approval_required` field combined with autonomy levels.

---

## Library & Dependency Analysis

### ZeroClaw's Key Dependencies (Cargo.toml)

| Crate | Purpose | AGENT-33 Equivalent |
|-------|---------|-------------------|
| `tokio` | Async runtime | `asyncio` (built-in) |
| `reqwest` | HTTP client | `httpx` |
| `serde`/`serde_json` | Serialization | `pydantic` |
| `toml` | Config parsing | `pydantic-settings` (env vars) |
| `rusqlite` | SQLite (memory backend) | `sqlalchemy` + PostgreSQL |
| `chacha20poly1305` | Encryption | `cryptography` (AES-256-GCM) |
| `clap` | CLI parsing | `typer` |
| `tracing` | Structured logging | `structlog` |
| `uuid` | ID generation | `uuid` (Python stdlib) |
| `sha2`/`hmac` | Hashing | `hashlib`/`hmac` (Python stdlib) |
| `base64` | Encoding | `base64` (Python stdlib) |
| `chrono` | Date/time | `datetime` (Python stdlib) |
| `regex` | Pattern matching | `re` (Python stdlib) |
| `directories` | Platform paths | `pathlib` (Python stdlib) |
| `rand` | Random numbers | `secrets`/`os.urandom` (Python stdlib) |
| `constant_time_eq` | Timing-safe compare | `hmac.compare_digest()` (Python stdlib) |

### AGENT-33's Dependencies Not in ZeroClaw

| Package | Purpose | ZeroClaw Gap |
|---------|---------|-------------|
| `fastapi`/`uvicorn` | Full HTTP framework | Raw TCP only |
| `pydantic` | Data validation | Serde (less expressive validation) |
| `asyncpg`/`sqlalchemy` | PostgreSQL | SQLite only |
| `redis` | Caching/sessions | None |
| `nats-py` | Message bus | In-process mpsc only |
| `pgvector` | Vector search | Custom vector similarity |
| `alembic` | DB migrations | None |
| `langchain-core`/`langgraph` | LLM framework | None (hand-rolled) |
| `apscheduler` | Task scheduling | Custom heartbeat |
| `playwright` | Browser automation | None (Brave open only) |
| `cryptography` | Crypto | `chacha20poly1305` crate |
| `pyjwt` | JWT auth | None |
| `jinja2` | Templating | None |
| `opentelemetry` | Distributed tracing | None |

### Gaps in Library Coverage

AGENT-33 is missing:
- No SQLite FTS5 equivalent for BM25 search (use PostgreSQL `tsvector` instead)
- No constant-time comparison utility (use `hmac.compare_digest()` -- already in stdlib)
- No TOML config support (use `pydantic-settings` with TOML backend if needed)

ZeroClaw is missing:
- No data validation framework (Pydantic-level validation)
- No migration system
- No distributed message bus
- No browser automation
- No JWT/auth framework
- No task scheduling
- No OpenTelemetry

---

## Adaptation Roadmap

| Phase | Feature to Adapt | Source (ZeroClaw) | Target Files in AGENT-33 | Effort | Priority |
|-------|-----------------|-------------------|-------------------------|--------|----------|
| 14a | Multi-segment command validation | `security/policy.rs::is_command_allowed()` | `tools/builtin/shell.py`, `tools/governance.py` | 1 day | P0 |
| 14b | Autonomy levels (R/O, Supervised, Full) | `security/policy.rs::AutonomyLevel` | `agents/definition.py`, `tools/governance.py`, `runtime.py` | 2 days | P0 |
| 14c | Rate limiting on tool execution | `security/policy.rs::ActionTracker` | `tools/governance.py`, `config.py` | 1 day | P0 |
| 14d | Path traversal hardening | `security/policy.rs` path validation | `tools/builtin/file_ops.py` | 1 day | P0 |
| 14e | Pairing brute-force lockout | `security/pairing.rs` | `messaging/pairing.py` | 0.5 day | P1 |
| 14f | Request size limits | `gateway/mod.rs` (64KB limit) | `main.py`, `config.py` | 0.5 day | P1 |
| 15a | Hybrid search (BM25 + vector) | `memory/vector.rs::hybrid_merge()` | `memory/long_term.py`, `memory/rag.py`, `config.py` | 3 days | P0 |
| 15b | Embedding cache with LRU | `memory/sqlite.rs` (embedding_cache) | `memory/embeddings.py`, migration | 1.5 days | P1 |
| 15c | Tokenizer-aware chunking | `memory/chunker.rs` | New `memory/chunker.py` | 1 day | P1 |
| 16a | JSON Schema on Tool protocol | `tools/traits.rs::parameters_schema()` | `tools/base.py`, all builtins | 2 days | P1 |
| 16b | Memory as tool interface | `tools/memory_store.rs` etc. | New tools in `tools/builtin/` | 1 day | P2 |
| 17a | Provider registry expansion | `providers/` (22+ providers) | `llm/router.py`, `config.py` | 2 days | P1 |
| 17b | Provider fallback chains | Not in ZeroClaw (but needed by both) | `llm/router.py` | 1.5 days | P2 |
| 18a | Skills/plugin system | `skills/mod.rs` | New `skills/` module | 4 days | P2 |
| 18b | Channel health checks | `channels/mod.rs::doctor_channels()` | `messaging/base.py`, all adapters | 1.5 days | P2 |
| 19a | Matrix channel adapter | `channels/matrix.rs` | New `messaging/matrix.py` | 2 days | P3 |
| 19b | Multi-observer composition | `observability/multi.rs` | `observability/` | 1 day | P3 |
| 20a | Config-driven subsystem swapping | `config/schema.rs` (backend selection by string) | `config.py`, `main.py` | 2 days | P3 |
| 20b | Composio integration | `tools/composio.rs` | New `tools/builtin/composio.py` | 2 days | P3 |

**Total estimated effort**: ~30 developer-days
**Phases map to AGENT-33's Phase 14-20 roadmap**

---

## Risks & Anti-Patterns

### Features That Should NOT Be Adopted

1. **Zero-framework HTTP server** -- ZeroClaw's raw TCP gateway (`gateway/mod.rs`) manually parses HTTP from raw sockets. This provides no CORS, no HTTP/2, no WebSocket, no middleware pipeline, no request routing, and is a source of parsing bugs. AGENT-33's FastAPI is categorically better. **Do not replicate.**

2. **Single-agent model** -- ZeroClaw's entire architecture assumes one agent with one loop. Adopting this pattern would destroy AGENT-33's core differentiator (multi-agent orchestration). **Do not replicate.**

3. **No tool-use loop** -- ZeroClaw defines tools but the agent loop (`loop_.rs`) never parses tool calls from LLM responses. Tools are effectively decorative. AGENT-33 should implement a proper tool-use loop, but should NOT copy ZeroClaw's non-implementation. **Implement properly, not as in ZeroClaw.**

4. **SQLite as primary store** -- ZeroClaw uses SQLite with `Mutex<Connection>`, which serializes all memory operations. AGENT-33's PostgreSQL + pgvector is better for concurrent multi-tenant workloads. **Do not downgrade to SQLite.**

5. **Compile-time-only plugins** -- ZeroClaw requires recompilation to add new trait implementations. AGENT-33's runtime discovery (entrypoints, YAML defs) is more flexible. **Do not require recompilation for extensions.**

6. **No conversation history** -- ZeroClaw does not maintain multi-turn conversation history. Each call is independent. AGENT-33 should maintain conversation context via its memory system. **Do not adopt this limitation.**

### Features That Need Redesign Before Adoption

1. **Skills system** -- ZeroClaw's TOML skill format and git-clone installation are straightforward but need adaptation for AGENT-33's multi-agent context. Skills should declare which agent roles they apply to, and should integrate with the existing tool registry rather than bypassing it.

2. **Autonomy levels** -- ZeroClaw's three levels (ReadOnly/Supervised/Full) are per-system. In AGENT-33, they should be per-agent (different agents at different autonomy levels within the same workflow).

3. **Channel health checks** -- ZeroClaw's `doctor_channels()` is synchronous and blocking. AGENT-33's version should be async and integrate with the existing health check endpoint.

### Compatibility Concerns

1. **Agent definition schema** -- Adding `autonomy_level` to `GovernanceConstraints` must preserve backward compatibility. Use default values for existing JSON definitions.

2. **Memory table schema** -- Adding a `tsvector` column to `memory_records` requires an Alembic migration. Existing data must be backfilled.

3. **Tool protocol change** -- Adding `parameters_schema` to the `Tool` protocol will break existing custom tools unless it has a default implementation.

4. **Config expansion** -- Adding 10+ new config vars (API keys for providers, rate limits, weights) should not require them to be set. All must have sensible defaults.

---

## Identity Preservation

AGENT-33's identity is defined by four unique capabilities that ZeroClaw lacks entirely. These must be preserved and strengthened during absorption:

### 1. Multi-Agent Orchestration (AGENT-33 Core)

AGENT-33's DAG-based workflow engine with 6 specialized agents is its primary differentiator. ZeroClaw is a single-agent system with no orchestration. Every ZeroClaw feature absorbed must be integrated in a way that works across multiple agents. Examples:
- Autonomy levels should be per-agent, not per-system
- Rate limiting should be per-agent, not global
- Skills should declare agent-role compatibility
- Channel health checks should report per-adapter, not system-wide

### 2. Governance Layer (AGENT-33 Unique)

The governance-first approach (`GovernanceConstraints`, `ToolGovernance`, scope-based permissions, approval requirements) is unique to AGENT-33. ZeroClaw has security policies but no governance model. Absorbing ZeroClaw's security improvements (command validation, rate limiting, autonomy levels) should flow through the governance layer, not bypass it:
- Command validation should be a governance check, not just a shell tool feature
- Rate limits should be governance-enforced, not hardcoded
- Autonomy levels are a governance concept, not a security concept

### 3. Training/Self-Improvement Loop (AGENT-33 Unique)

The complete `training/` subsystem (rollout capture, LLM-as-judge evaluation, optimization, scheduling) has no equivalent in ZeroClaw. This should be leveraged to evaluate the effectiveness of absorbed features:
- After absorbing hybrid search, training should evaluate RAG quality improvement
- After absorbing autonomy levels, training should evaluate safety compliance
- After absorbing skills, training should evaluate skill effectiveness

### 4. Evidence Capture (AGENT-33 Unique)

Structured audit logging, observation capture, lineage tracking, and replay provide provenance for every action. ZeroClaw has basic event logging but no replay or lineage. All absorbed features must produce evidence:
- Rate limit rejections should be audit-logged
- Autonomy level violations should be captured as observations
- Tool schema validation failures should be traceable
- Skill installations should have provenance records

### Design Principle

The absorption formula is: **ZeroClaw's breadth + AGENT-33's depth = superior system**. ZeroClaw contributes breadth (22+ providers, hybrid search, skills, channels). AGENT-33 contributes depth (multi-agent orchestration, governance, training, evidence). No feature from ZeroClaw should be adopted in a way that flattens AGENT-33's depth.
