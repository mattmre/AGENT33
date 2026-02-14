# ZeroClaw -- Research Dossier

**Repository**: https://github.com/theonlyhennygod/zeroclaw
**Language**: Rust (631K LoC), Dockerfile, Shell
**License**: MIT
**Stars**: 293 | **Forks**: 16
**Created**: 2026-02-13 | **Last Updated**: 2026-02-14
**Test Count**: 1,017 | **Binary Size**: ~3.4 MB

---

## 1. Summary & Purpose

ZeroClaw is a fully autonomous AI assistant built entirely in Rust, designed as a zero-overhead, provider-agnostic CLI agent. Its tagline -- "Zero overhead. Zero compromise. 100% Rust. 100% Agnostic." -- captures the core design philosophy: every subsystem is a trait, every dependency is swappable via configuration alone, and the binary ships at ~3.4 MB with <10ms startup.

**Key differentiators**:
- **Pure Rust, zero-framework**: No LangChain, no LlamaIndex, no Python runtime. The entire stack -- memory, search, embeddings, gateway, channels, security -- is hand-rolled in Rust with minimal dependencies.
- **Trait-based pluggability**: 8 core traits (`Provider`, `Channel`, `Memory`, `Tool`, `Observer`, `RuntimeAdapter`, `SecurityPolicy`, `Tunnel`) allow swapping any subsystem without code changes.
- **22+ LLM providers**: OpenRouter, Anthropic, OpenAI, Ollama, Venice, Groq, Mistral, xAI, DeepSeek, Together, Fireworks, Perplexity, Cohere, Bedrock, plus any OpenAI-compatible endpoint via `custom:https://your-api.com`.
- **Full-stack hybrid search memory**: SQLite-backed with FTS5 (BM25) + vector cosine similarity + weighted merge -- all custom, zero external search dependencies.
- **Security-first**: Workspace sandboxing, command allowlisting, path traversal blocking, rate limiting, encrypted secrets (ChaCha20-Poly1305 AEAD), gateway pairing with brute-force lockout, tunnel-only public exposure.
- **Multi-channel**: CLI, Telegram, Discord, Slack, iMessage, Matrix, Webhook -- all running concurrently through a shared message bus.

The project directly positions itself against "OpenClaw" (likely a Node.js-based predecessor or competitor), benchmarking at 50-100x less memory, 8x less disk, and near-instant startup.

## 2. Architecture & Design

### 2.1 Module Structure

```
src/
  main.rs          -- Clap CLI with subcommands: onboard, agent, gateway, status, cron, channel, integrations, skills
  lib.rs           -- Library crate (config, heartbeat, memory, observability, providers, runtime, security)
  agent/
    loop_.rs       -- Core agent loop: wire subsystems, build prompt, call provider, manage memory
  channels/
    mod.rs         -- System prompt builder, channel orchestration, health checks
    traits.rs      -- Channel trait (name, send, listen, health_check)
    cli.rs, telegram.rs, discord.rs, slack.rs, imessage.rs, matrix.rs
  config/
    schema.rs      -- TOML config with all subsystem configs (gateway, autonomy, memory, tunnel, etc.)
  gateway/
    mod.rs         -- Raw TCP HTTP server (zero framework), pairing, webhook handling
  heartbeat/
    engine.rs      -- Periodic task runner reading HEARTBEAT.md
  integrations/
    registry.rs    -- 50+ integration catalog across 9 categories
  memory/
    traits.rs      -- Memory trait (store, recall, get, list, forget, count, health_check)
    sqlite.rs      -- SQLite with FTS5 + vector BLOB + embedding cache + safe reindex
    markdown.rs    -- File-based markdown memory backend
    vector.rs      -- Cosine similarity, vec-to-bytes serialization, hybrid merge
    embeddings.rs  -- EmbeddingProvider trait, OpenAI-compatible + Noop implementations
    chunker.rs     -- Line-based markdown chunker with heading preservation
  observability/
    traits.rs      -- Observer trait with events and metrics
    log.rs, noop.rs, multi.rs
  providers/
    traits.rs      -- Provider trait (chat, chat_with_system)
    openrouter.rs, anthropic.rs, openai.rs, ollama.rs, compatible.rs
  runtime/
    traits.rs      -- RuntimeAdapter trait
    native.rs
  security/
    policy.rs      -- SecurityPolicy with command allowlisting, path validation, rate limiting
    pairing.rs     -- Gateway pairing guard with brute-force lockout, constant-time comparison
    secrets.rs     -- ChaCha20-Poly1305 encrypted secret store with legacy XOR migration
  skills/
    mod.rs         -- TOML/Markdown skill loading, skill-to-prompt builder, install/remove CLI
  tools/
    traits.rs      -- Tool trait (name, description, parameters_schema, execute, spec)
    shell.rs, file_read.rs, file_write.rs, memory_store.rs, memory_recall.rs, memory_forget.rs
    browser_open.rs, composio.rs
  tunnel/
    mod.rs         -- Tunnel trait + factory, shared process management
    cloudflare.rs, tailscale.rs, ngrok.rs, custom.rs, none.rs
```

### 2.2 Design Patterns

- **Trait-based dependency injection**: Every subsystem is a Rust trait. The `main.rs` function wires concrete implementations based on TOML config at startup. No runtime reflection, no dependency container -- just `Box<dyn Trait>` and `Arc<dyn Trait>`.
- **Factory functions**: Each module has a `create_*` factory (e.g., `providers::create_provider`, `memory::create_memory`, `tunnel::create_tunnel`) that maps config strings to concrete types.
- **Zero-framework HTTP**: The gateway uses raw `tokio::net::TcpListener` + manual HTTP parsing. No Axum, no Actix, no Warp. This keeps the binary small but limits HTTP feature coverage.
- **Message bus pattern**: Channels use `tokio::sync::mpsc` as a shared message bus. All channel listeners send to a single `mpsc::Sender<ChannelMessage>`, and the main loop receives and dispatches.
- **Config-driven composition**: The TOML config file at `~/.zeroclaw/config.toml` controls which implementations are active. Changing `[memory] backend = "sqlite"` to `"markdown"` swaps the entire memory backend.

### 2.3 Binary Optimization

The `Cargo.toml` release profile is aggressively optimized:
- `opt-level = "z"` (optimize for size)
- `lto = true` (link-time optimization)
- `codegen-units = 1` (better optimization at cost of compile time)
- `strip = true` (remove debug symbols)
- `panic = "abort"` (no unwinding, smaller binary)

## 3. Orchestration Model

ZeroClaw is a **single-agent system**, not a multi-agent orchestrator. There is no agent-to-agent communication, no DAG-based workflows, no handoffs, and no routing between specialized agents.

### 3.1 Agent Loop

The agent loop (`agent/loop_.rs`) follows a simple cycle:

1. Initialize subsystems (observer, runtime, security, memory, tools, provider)
2. Build system prompt from workspace markdown files and skills
3. For each user message:
   a. Auto-save to memory (if enabled)
   b. Retrieve relevant memories via `mem.recall(query, 5)` (hybrid search)
   c. Prepend memory context to user message
   d. Call `provider.chat_with_system(system_prompt, enriched_message, model, temperature)`
   e. Print response
   f. Auto-save response to daily memory

### 3.2 System Prompt Construction

The `build_system_prompt()` function in `channels/mod.rs` assembles context from workspace files in a structured order:

1. **Tools** -- list of available tools with descriptions
2. **Safety** -- hardcoded safety guardrails (no exfiltration, no destructive commands without asking, prefer `trash` over `rm`)
3. **Skills** -- compact XML list of installed skills with on-demand loading
4. **Workspace** -- working directory path
5. **Project Context** -- injected content from workspace markdown files: AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md, BOOTSTRAP.md (optional), MEMORY.md
6. **Date & Time** -- current timezone
7. **Runtime** -- hostname, OS, model name

Files are truncated at 20,000 characters with a notice. Missing files get a `[File not found]` marker.

### 3.3 Channel Multiplexing

Multiple channels run concurrently via `tokio::spawn`, all feeding into a shared `mpsc::channel`. The main loop processes messages sequentially, calling the LLM and routing replies back to the originating channel.

### 3.4 No Tool Use Loop

Critically, ZeroClaw does **not** implement a tool-use loop. The LLM is told about tools in the system prompt, but there is no mechanism in `loop_.rs` or elsewhere to parse tool calls from the LLM response, execute them, and feed results back. The tools exist as data structures (`Tool` trait, `ToolSpec`, `ToolResult`) but the agent loop only calls `provider.chat_with_system()` once per message with no iteration. This means the tools are effectively documentation-only in the current implementation -- the LLM knows about them but cannot invoke them.

## 4. Tooling & Capabilities

### 4.1 Built-in Tools

| Tool | Source | Description |
|------|--------|-------------|
| `shell` | `tools/shell.rs` | Execute terminal commands (subject to SecurityPolicy allowlist) |
| `file_read` | `tools/file_read.rs` | Read file contents (path validation, workspace scoping) |
| `file_write` | `tools/file_write.rs` | Write file contents (path validation, workspace scoping) |
| `memory_store` | `tools/memory_store.rs` | Save to memory with key and category |
| `memory_recall` | `tools/memory_recall.rs` | Search memory (hybrid keyword + vector) |
| `memory_forget` | `tools/memory_forget.rs` | Delete a memory entry by key |
| `browser_open` | `tools/browser_open.rs` | Open URLs in Brave Browser (allowlist-only, opt-in) |
| `composio` | `tools/composio.rs` | 1000+ OAuth apps via composio.dev (opt-in) |

### 4.2 Tool Trait Design

```rust
#[async_trait]
pub trait Tool: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn parameters_schema(&self) -> serde_json::Value;  // JSON Schema
    async fn execute(&self, args: serde_json::Value) -> anyhow::Result<ToolResult>;
    fn spec(&self) -> ToolSpec;  // Default implementation from above
}
```

Tools carry their own JSON Schema for parameters, making them self-describing for LLM function calling. The `ToolSpec` struct packages name, description, and schema together.

### 4.3 Gateway API

Raw TCP HTTP server with three endpoints:
- `GET /health` -- unauthenticated health check (no secrets leaked)
- `POST /pair` -- exchange 6-digit one-time code for bearer token
- `POST /webhook` -- send message to agent (bearer token + optional webhook secret required)

30-second read timeout prevents slow-loris attacks. 64KB max request size.

### 4.4 Skills System

Skills are user-defined capability packs stored as directories under `~/.zeroclaw/workspace/skills/<name>/`. Each skill has either:
- `SKILL.toml` -- structured manifest with metadata, tool definitions, and prompts
- `SKILL.md` -- simple markdown file read as instructions for the agent

Skills are loaded at startup, their descriptions injected into the system prompt as compact XML, and their full content loaded on-demand via file read. Skills can be installed from GitHub URLs or local paths.

### 4.5 Integration Catalog

50+ integrations across 9 categories (Chat, Development, Productivity, Cloud, Data, AI/ML, Monitoring, Security, Automation). These are mostly a catalog with status tracking -- not all are implemented as active channel adapters.

## 5. Observability & Monitoring

### 5.1 Observer Trait

```rust
pub trait Observer: Send + Sync {
    fn record_event(&self, event: &ObserverEvent);
    fn record_metric(&self, metric: &ObserverMetric);
    fn flush(&self) {}
    fn name(&self) -> &str;
}
```

**Events**: `AgentStart`, `AgentEnd`, `ToolCall`, `ChannelMessage`, `HeartbeatTick`, `Error`
**Metrics**: `RequestLatency`, `TokensUsed`, `ActiveSessions`, `QueueDepth`

### 5.2 Implementations

- **NoopObserver** -- discards all events (default for minimal overhead)
- **LogObserver** -- writes events to tracing/structured logs
- **MultiObserver** -- fans out to multiple observers

### 5.3 Limitations

- No Prometheus exporter (mentioned as "extend" option in docs)
- No OpenTelemetry integration
- No dashboard or UI
- Token counting is `Option<u64>` and appears to always be `None` in the agent loop
- No distributed tracing

## 6. Extensibility & Plugin Model

### 6.1 Trait-Based Extension Points

Every subsystem is a trait. To add a new implementation:

| Extension Point | Trait | Where to Add |
|----------------|-------|--------------|
| LLM provider | `Provider` | `src/providers/` |
| Channel | `Channel` | `src/channels/` |
| Memory backend | `Memory` | `src/memory/` |
| Tool | `Tool` | `src/tools/` |
| Observer | `Observer` | `src/observability/` |
| Runtime | `RuntimeAdapter` | `src/runtime/` |
| Tunnel | `Tunnel` | `src/tunnel/` |

New implementations require code changes and recompilation. There is no dynamic plugin loading (no `dlopen`, no WASM plugin host).

### 6.2 Skills as Soft Plugins

Skills provide a no-recompile extension mechanism. A skill can define:
- Custom tools (shell, HTTP, script types)
- Custom prompts (injected into the system prompt)
- Metadata (name, version, author, tags)

Skills are installed via `zeroclaw skills install <github-url>` (git clone) or local path (symlink on Unix).

### 6.3 Custom Provider Escape Hatch

Any OpenAI-compatible API can be used as a provider by setting `default_provider = "custom:https://your-api.com"`. This is the lowest-friction extension point.

### 6.4 Custom Tunnel Escape Hatch

The `custom` tunnel provider runs any shell command and optionally parses a public URL from stdout using a regex pattern. This allows using any tunnel binary without writing Rust code.

## 7. Practices Relevant to AGENT-33

### 7.1 Hybrid Search Memory (HIGH PRIORITY)

ZeroClaw's `SqliteMemory` implements the exact hybrid search pattern AGENT-33 needs but currently lacks:

- **FTS5 + BM25 keyword search**: SQLite's built-in full-text search with BM25 scoring
- **Vector cosine similarity**: Embeddings stored as BLOBs in SQLite, cosine similarity computed in Rust
- **Weighted hybrid merge**: `final_score = vector_weight * vector_score + keyword_weight * keyword_score` with configurable weights (default 0.7/0.3)
- **Embedding cache**: SQLite `embedding_cache` table with LRU eviction to avoid redundant API calls
- **Safe reindex**: Atomic rebuild of FTS5 + re-embedding

**Adaptation for AGENT-33**: The current AGENT-33 RAG pipeline (`memory/`) is vector-only with no BM25, no reranking, no query rewriting, and 500-char chunks. ZeroClaw's `vector.rs` `hybrid_merge()` function could be directly ported to Python. The pattern is simple enough -- normalize scores, weighted sum, deduplicate by ID. The embedding cache pattern (hash input text, check cache before calling API) could save significant API costs during re-indexing.

**Concrete changes**:
- Add BM25/FTS search to `memory/rag.py` (use SQLite FTS5 or PostgreSQL full-text search alongside pgvector)
- Implement `hybrid_merge()` in Python -- ~30 lines
- Add embedding cache table to avoid redundant embedding API calls
- Make vector/keyword weights configurable (currently AGENT-33 is vector-only)

### 7.2 Security Policy Design (HIGH PRIORITY)

ZeroClaw's `SecurityPolicy` addresses the exact governance-prompt disconnect identified in AGENT-33's memory file:

- **Three autonomy levels**: ReadOnly, Supervised, Full -- enforced at every tool execution
- **Command allowlisting with full command validation**: Blocks subshell operators (backticks, `$()`), validates every command in pipes/chains, blocks output redirections
- **Path validation with symlink escape detection**: Blocks `..`, null bytes, absolute paths (when workspace_only), forbidden system paths, and verifies resolved paths stay within workspace
- **Rate limiting**: Sliding-window action tracker (max actions per hour)
- **Safety guardrails injected into prompts**: The `build_system_prompt()` function hardcodes safety rules directly into the LLM system prompt

**Adaptation for AGENT-33**: AGENT-33 has `GovernanceConstraints` in `definition.py` but never injects them into prompts (the #1 priority finding from research). ZeroClaw shows the pattern: safety rules belong in the system prompt, not just in code. The command validation logic (checking entire pipelines, blocking subshells) is more thorough than AGENT-33's current shell tool.

**Concrete changes**:
- In `runtime.py:_build_system_prompt()`, inject `GovernanceConstraints` from agent definitions
- Port the multi-segment command validation pattern from `policy.rs::is_command_allowed()` to the shell tool
- Add autonomy levels to agent definitions (read-only, supervised, full)
- Add rate limiting to the tool execution pipeline

### 7.3 Encrypted Secret Store (MEDIUM PRIORITY)

ZeroClaw uses ChaCha20-Poly1305 AEAD for API keys in config files, with:
- Random per-encryption nonce (different ciphertext each time)
- Key file at `~/.zeroclaw/.secret_key` with 0600 permissions
- Legacy XOR cipher migration path
- Tamper detection (authentication tag)

**Adaptation for AGENT-33**: AGENT-33's `security/vault.py` could adopt this pattern for encrypting secrets at rest. The `enc2:` prefix convention allows mixing encrypted and plaintext values in the same config.

### 7.4 Channel Multiplexing Pattern (MEDIUM PRIORITY)

ZeroClaw's channel system uses a clean pattern:
- `Channel` trait with `listen()` that takes an `mpsc::Sender`
- All channels feed into a shared message bus
- Single processing loop dispatches to the originating channel

**Adaptation for AGENT-33**: AGENT-33's `messaging/` module uses NATS as a message bus, which is more sophisticated but also heavier. The trait-based channel design with health checks (`channel doctor`) is a good pattern for the messaging subsystem.

### 7.5 System Prompt from Workspace Files (MEDIUM PRIORITY)

ZeroClaw's `build_system_prompt()` assembles identity, soul, tools, and context from workspace markdown files. This is the "personality layer" pattern -- the agent's behavior is defined by editable files, not code.

**Adaptation for AGENT-33**: AGENT-33's agent definitions use JSON with `prompts.system` pointing to template paths, but `_build_system_prompt()` ignores them. The workspace-file pattern could complement the JSON definitions: load the system prompt template, inject governance constraints, inject tool descriptions, inject workspace context.

### 7.6 Gateway Pairing Security (LOW PRIORITY)

The pairing guard pattern (6-digit code, bearer token exchange, brute-force lockout, constant-time comparison) is a solid pattern for webhook security without requiring full OAuth.

### 7.7 What NOT to Adopt

- **Zero-framework HTTP**: ZeroClaw's raw TCP gateway works for its minimal needs but would be a regression from FastAPI. Do not replicate.
- **Single-agent model**: ZeroClaw has no multi-agent orchestration. AGENT-33's DAG-based workflow engine is far more capable.
- **No tool-use loop**: ZeroClaw's tools exist as definitions but the agent loop never actually parses and executes tool calls. This is a significant limitation.
- **Compile-time plugins only**: The trait-based extension model requires recompilation. AGENT-33's JSON agent definitions and tool registry are more flexible for runtime extension.

## 8. Risks & Limitations

### 8.1 No Actual Tool Execution

The most significant limitation: ZeroClaw defines tools with JSON schemas and tells the LLM about them, but the agent loop (`loop_.rs`) never parses tool calls from the LLM response. There is no `tool_call` handling, no result injection, no iterative tool-use cycle. The tools are effectively decorative.

### 8.2 Single-Agent, Single-Turn

Each message gets one LLM call. No multi-turn reasoning, no chain-of-thought, no agent delegation, no workflow execution. Complex tasks requiring multiple steps must be manually broken down by the user.

### 8.3 No Conversation History

The agent loop does not maintain a multi-turn conversation history. Each call to the provider includes only the system prompt and the current message (with memory context). Previous turns are not carried forward unless they happen to be recalled via memory search.

### 8.4 Raw TCP HTTP Gateway

The gateway parses HTTP manually from raw TCP. This means:
- No HTTP/2, no WebSocket upgrade, no chunked transfer
- No CORS headers
- No request routing beyond exact string matching
- No middleware pipeline
- Potential for parsing bugs on edge-case HTTP requests

### 8.5 SQLite Single-Writer

The SQLite memory backend uses `Mutex<Connection>`, meaning all memory operations are serialized through a single lock. Under concurrent channel load, this could become a bottleneck.

### 8.6 No Multi-Tenancy

ZeroClaw is a single-user system. There is no tenant isolation, no user-scoped memory, no role-based access control. The pairing system provides device-level auth but not user-level.

### 8.7 Very New Project

Created 2026-02-13 (one day before this analysis). Despite having 293 stars and 1,017 tests, the codebase is extremely new. API stability, documentation coverage, and community support are all unknown quantities.

## 9. Feature Extraction Table

| Feature | Source (file/module) | Adaptation Needed | Priority for AGENT-33 |
|---------|---------------------|-------------------|----------------------|
| Hybrid search (BM25 + vector + weighted merge) | `memory/vector.rs::hybrid_merge()`, `memory/sqlite.rs` | Port merge logic to Python, add FTS to RAG pipeline | HIGH |
| Safety guardrails in system prompt | `channels/mod.rs::build_system_prompt()` | Inject `GovernanceConstraints` into `_build_system_prompt()` | HIGH |
| Multi-segment command validation | `security/policy.rs::is_command_allowed()` | Port pipeline/subshell blocking to shell tool | HIGH |
| Autonomy levels (ReadOnly/Supervised/Full) | `security/policy.rs::AutonomyLevel` | Add to agent definitions, enforce in tool execution | HIGH |
| Embedding cache with LRU eviction | `memory/sqlite.rs` (embedding_cache table) | Add cache table to pgvector setup | MEDIUM |
| ChaCha20-Poly1305 secret encryption | `security/secrets.rs` | Adopt for vault.py at-rest encryption | MEDIUM |
| Channel health checks (`doctor`) | `channels/mod.rs::doctor_channels()` | Add health check command to messaging subsystem | MEDIUM |
| TOML skill manifests | `skills/mod.rs` | Consider for agent definition extensions | LOW |
| Gateway pairing with brute-force lockout | `security/pairing.rs` | Consider for webhook security | LOW |
| Tunnel trait abstraction | `tunnel/mod.rs` | Not needed (AGENT-33 uses standard reverse proxy) | SKIP |
| Heartbeat periodic tasks | `heartbeat/engine.rs` | Already have APScheduler automation | SKIP |
| Rate limiting (sliding window) | `security/policy.rs::ActionTracker` | Add to tool execution pipeline | MEDIUM |

## 10. Evidence Links

**Core Architecture**:
- Main entry: [src/main.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/main.rs)
- Agent loop: [src/agent/loop_.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/agent/loop_.rs)
- Config schema: [src/config/schema.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/config/schema.rs)

**Memory System**:
- Memory trait: [src/memory/traits.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/memory/traits.rs)
- SQLite backend: [src/memory/sqlite.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/memory/sqlite.rs)
- Hybrid merge: [src/memory/vector.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/memory/vector.rs)
- Embeddings: [src/memory/embeddings.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/memory/embeddings.rs)

**Security**:
- Security policy: [src/security/policy.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/security/policy.rs)
- Gateway pairing: [src/security/pairing.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/security/pairing.rs)
- Encrypted secrets: [src/security/secrets.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/security/secrets.rs)
- Security policy doc: [SECURITY.md](https://github.com/theonlyhennygod/zeroclaw/blob/main/SECURITY.md)

**Tools & Skills**:
- Tool trait: [src/tools/traits.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/tools/traits.rs)
- Tool registry: [src/tools/mod.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/tools/mod.rs)
- Skills system: [src/skills/mod.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/skills/mod.rs)

**Channels & Gateway**:
- System prompt builder: [src/channels/mod.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/channels/mod.rs)
- Channel trait: [src/channels/traits.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/channels/traits.rs)
- Gateway: [src/gateway/mod.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/gateway/mod.rs)

**Infrastructure**:
- Cargo.toml: [Cargo.toml](https://github.com/theonlyhennygod/zeroclaw/blob/main/Cargo.toml)
- CI: [.github/workflows/ci.yml](https://github.com/theonlyhennygod/zeroclaw/blob/main/.github/workflows/ci.yml)
- Tunnel system: [src/tunnel/mod.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/tunnel/mod.rs)
- Observability: [src/observability/traits.rs](https://github.com/theonlyhennygod/zeroclaw/blob/main/src/observability/traits.rs)
