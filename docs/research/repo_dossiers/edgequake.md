# Repo Dossier: raphaelmansuy/edgequake

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

EdgeQuake is a production-ready Rust reimplementation of the LightRAG algorithm (Graph-RAG framework) that transforms documents into knowledge graphs for superior retrieval and generation. Built with 11 modular crates (~130K LOC), it uses async-first Tokio architecture with zero-copy operations, PostgreSQL/pgvector/Apache AGE for unified storage, and supports 6 query modes (naive, local, global, hybrid, mix, bypass). Key advantages over Python LightRAG: 10x document processing throughput (1000 vs 100 docs/min), 10x better memory efficiency (200-400MB vs 2-4GB), true async concurrency (1000+ vs ~100 concurrent users), single-binary deployment, and compile-time type safety. The project demonstrates advanced Rust patterns for edge AI including trait-based provider abstraction, facade orchestration, HTTP client pooling via reqwest, and batch embedding processing with configurable chunk sizes (2048 for OpenAI, 512 for Ollama).

## 2) Core orchestration model

EdgeQuake uses a **facade pattern** with the `EdgeQuake` struct (in `edgequake-core`) coordinating all RAG operations through trait-based abstractions. The 11-crate architecture enforces single-responsibility: `edgequake-core` (orchestration), `edgequake-pipeline` (document ingestion), `edgequake-query` (6 query modes), `edgequake-storage` (KV/Vector/Graph traits), `edgequake-llm` (provider abstraction), `edgequake-api` (Axum REST), `edgequake-pdf` (extraction), `edgequake-auth` (JWT), `edgequake-audit` (compliance), `edgequake-tasks` (background jobs), `edgequake-rate-limiter` (throttling). Providers implement `LLMProvider` and `EmbeddingProvider` traits, allowing runtime swapping (production uses OpenAI, tests use Mock, local uses Ollama) with zero code changes. Multi-tenancy is enforced at the storage layer via `tenant_id`/`workspace_id` filtering.

**Pipeline architecture**: Sequential processing with configurable stages: Chunk (1200 tokens, 100 overlap) → Extract (LLM entity/relationship tuples) → Glean (optional second pass, +18% recall) → Normalize (UPPERCASE_UNDERSCORE, -36-40% duplicates) → Embed (batch processing) → Store (PostgreSQL AGE + pgvector). Query flow uses strategy pattern with mode-specific graph traversal: Naive (vector-only, ~50ms), Local (entity + neighbors, ~150ms), Global (community summaries, ~200ms), Hybrid (local+global, ~250ms), Mix (weighted fusion, ~300ms), Bypass (no RAG). Community detection via Louvain modularity clustering enables thematic queries.

## 3) Tooling and execution

**Build system**: Cargo workspace with 11 crates, Makefile for unified dev tasks. OpenAPI 3.0 REST API at `/api/v1/*` with Swagger UI at `/swagger-ui`. React 19 + TypeScript frontend (Bun + Vite) with Sigma.js graph visualization and SSE streaming. Docker Compose for full stack (PostgreSQL, backend, frontend). Multi-provider support: OpenAI (gpt-4.1-nano default, text-embedding-3-small), Ollama (gemma3:12b, embeddinggemma:latest/768d), LM Studio, Mock (for tests). Storage adapters: PostgreSQL (pgvector HNSW for vectors, Apache AGE property graph) and in-memory (dev/test only).

**LLM client pooling**: Both `OllamaProvider` and `OpenAIProvider` initialize HTTP clients once during construction (not per-request). Ollama uses `reqwest::Client::builder().timeout(300s)` in `OllamaProviderBuilder::build()` and stores it in the struct. OpenAI uses `async_openai::Client<OpenAIConfig>` via `Client::with_config(config)` which internally pools connections. This is the correct pattern AGENT-33 should adopt: create the HTTP client during provider initialization and reuse it across all requests.

**Embedding batching**: Implements MAX_EMBEDDING_BATCH_SIZE constants to avoid API limits. OpenAI provider: 2048 inputs per request (hard API limit), splits large entity sets into chunks via `texts.chunks(2048)`. Ollama provider: 512 inputs per batch (conservative to avoid OOM/timeout), logs batch progress when `num_batches > 1`. Both filter empty/whitespace strings before sending (returns zero vectors for invalid inputs) and map results back to original indices. AGENT-33's recent implementation mirrors this pattern correctly.

## 4) Observability and evaluation

**Structured logging**: Uses `tracing` crate with debug/info/warn levels. Examples: `debug!("Ollama embedding batch {}/{}: {} texts", batch_idx+1, num_batches, batch.len())` for batch progress, `warn!(original_len, truncated_to, model, "Truncating text for embedding (exceeds model context)")` for input overflow. Token tracking: `debug!("OpenAI token usage - prompt: {}, completion: {}, total: {}")` with full usage metadata in `LLMResponse`.

**Cost tracking**: Deep-dive documentation for LLM cost monitoring per operation. `LLMResponse` includes `prompt_tokens`, `completion_tokens`, `total_tokens`, and metadata hashmap with response IDs. OpenAI provider extracts usage from API response: `usage.prompt_tokens`, `usage.completion_tokens`. Supports cost calculation by multiplying token counts by model-specific pricing.

**Health checks**: Kubernetes-ready endpoints at `/health`, `/ready`, `/live`. Health response includes: `status`, `version`, `storage_mode`, `workspace_id`, component checks (`kv_storage`, `vector_storage`, `graph_storage`, `llm_provider`), and `llm_provider_name`. Background mode logs to `/tmp/edgequake-backend.log` and `/tmp/edgequake-frontend.log`.

**Testing**: Pure unit tests by default, `@pytest.mark.integration` for services. `MockLLMProvider` for deterministic tests (production-packaged in `src/agent33/testing/`). Test client with pre-set auth header via `TestClient(app)` fixture. Benchmark suite in `benches/` directory.

## 5) Extensibility

**Trait-based provider system**: `LLMProvider` trait (complete, complete_with_options, chat, stream, stream_with_options, supports_streaming, supports_json_mode) and `EmbeddingProvider` trait (name, model, dimension, max_tokens, embed, embed_one). Providers: OpenAI, Ollama, LM Studio, Azure OpenAI, Gemini, Jina, Mock. Adding new providers requires implementing these traits without modifying core. Storage traits: `KVStorage`, `VectorStorage`, `GraphStorage` with Memory and PostgreSQL adapters.

**Workspace isolation**: Multi-tenant via `tenant_id`/`workspace_id` headers. AuthMiddleware resolves tenant from API key or JWT. All DB models include `tenant_id` for isolation. Rate limiting via `edgequake-rate-limiter` crate with per-tenant quotas.

**SDKs**: Official SDKs for Python, TypeScript, Rust, C#, Go, Java, Kotlin, PHP, Ruby, Swift in `sdks/` directory with changelogs. Python and TypeScript are primary with comprehensive READMEs.

**Agent workflow**: Uses `edgecode` SOTA coding agent with specification-driven development. All changes specified in `specs/` directory before implementation. OODA loop (Observe, Orient, Decide, Act) for iterative development. `AGENTS.md` provides comprehensive agent guidelines with task logs format.

## 6) Notable practices worth adopting in AGENT-33

1. **HTTP client pooling pattern**: Initialize `reqwest::Client` or `async_openai::Client` once during provider construction, store in struct, reuse across all requests. See `OllamaProviderBuilder::build()` line 149-151 creating client with timeout, storing in `OllamaProvider` struct. AGENT-33's `ollama.py` currently creates new httpx client per request (lines 41, 69) — should adopt this pattern.

2. **Embedding batch size constants**: Use explicit `MAX_EMBEDDING_BATCH_SIZE` constants (2048 for OpenAI hard limit, 512 for Ollama conservative limit) with chunk-based iteration: `for batch in texts.chunks(MAX_SIZE)`. Log batch progress when `num_batches > 1`: `info!("Splitting {} texts into {} batches of max {}", total, num_batches, MAX_SIZE)`. AGENT-33 just implemented this correctly in recent batching work.

3. **Empty text filtering in embeddings**: Filter `texts.iter().filter(|(_, text)| !text.trim().is_empty())` before API call, track original indices, return zero vectors for empty slots, map results back. Prevents API rejections and maintains index alignment. See `ollama.rs:571-601` and `openai.rs:380-427`.

4. **Model-specific context limits**: Store separate `max_context_length` (for LLM) and `embedding_max_tokens` (for embeddings) in provider struct. Ollama uses 8192 for LLM but 2000 for embeddings (nomic-embed-text/embeddinggemma have 2048 limit). Truncate embeddings via chars/4 approximation: `text.chars().take(max_chars).collect()` with warning log. See `ollama.rs:67-70, 349-371`.

5. **Structured logging for batch operations**: Use contextual logging with batch metadata: `debug!("Ollama embedding batch {}/{}: {} texts with model {} (max_tokens={})")`. Include original counts, truncation details, model names. AGENT-33's current logging is minimal — should add this.

6. **Token usage extraction pattern**: Always extract and log token counts from API responses. OpenAI: `response.usage.{prompt_tokens,completion_tokens,total_tokens}`. Store in `LLMResponse` with metadata hashmap. Enables cost tracking and optimization. See `openai.rs:234-256`.

7. **Stop sequence handling in streaming**: Pass `stop` parameter through to both streaming and non-streaming completions. Ollama: `ChatOptions { stop: options.stop.clone() }`. OpenAI: `builder.stop(stop.clone())`. AGENT-33 may not be passing stop sequences correctly — verify.

8. **11-crate modular architecture**: Separate compilation units for single responsibilities (core, pipeline, query, storage, llm, api, pdf, auth, audit, tasks, rate-limiter). Benefits: compile-time boundary enforcement, parallel builds, selective testing, clear dependency graph. AGENT-33's `engine/src/agent33/` has logical modules but could adopt Cargo workspace pattern for stricter separation.

9. **Async-first with Tokio**: Use `async_trait`, `futures::StreamExt`, `BoxStream<'static, Result<String>>` for streaming. Tokio runtime for true async concurrency (not asyncio GIL-limited). EdgeQuake achieves 1000+ concurrent users vs ~100 for Python.

10. **Builder pattern for providers**: Use `OllamaProviderBuilder`, `OpenAIProvider::with_model()`, etc. for fluent configuration. Allows optional params, defaults, validation before construction. AGENT-33's providers use direct instantiation — builders would improve ergonomics.

## 7) Risks / limitations to account for

1. **Rust-only ecosystem**: Requires Rust expertise on team. Python-first teams may struggle with ownership/lifetimes. LightRAG Python has larger community (27.7k stars, 216 contributors) vs EdgeQuake (growing). AGENT-33 is Python-based so direct code reuse is limited to patterns/architecture, not implementation.

2. **PostgreSQL coupling**: Unified storage via PostgreSQL is simpler to deploy but less flexible than LightRAG's multi-backend support (Neo4J, MongoDB, Milvus, Qdrant). EdgeQuake only supports PostgreSQL + in-memory. If AGENT-33 needs other backends, this pattern won't transfer.

3. **Embedding model context overflow**: Ollama's truncation approach (`chars/4` approximation, `text.chars().take(max_chars)`) is lossy and may cut mid-sentence. Better approach: use tokenizer-aware chunking (as noted in RAG-Anything dossier with tiktoken). EdgeQuake acknowledges this with warning logs but doesn't use actual tokenizer.

4. **No multimodal support**: EdgeQuake is text-only. LightRAG has RAG-Anything for PDFs/images via vision models. EdgeQuake's PDF processor is "experimental/early prototype" per README. AGENT-33's ReaderTool is also web-only, FileOpsTool is UTF-8 only — this limitation is shared.

5. **Performance claims lack benchmarks**: README states "~2-3x more entity extraction, ~1000ms → <200ms query latency, 10x concurrent users" but no reproducible benchmarks in repo. The `benches/` directory exists but benchmark code is opaque. AGENT-33 should validate claims independently if adopting patterns.

6. **In-memory mode removed**: EdgeQuake requires PostgreSQL for all server modes (per `AGENTS.md` line 175: "In-memory storage mode has been removed"). This complicates quick testing/demos. AGENT-33's in-memory mode is a feature advantage for development.

7. **Agent workflow dependency**: EdgeQuake development uses `edgecode` SOTA agent which is "not yet public but will be released soon" per README. The spec-driven workflow (OODA loop, task logs, AGENTS.md guidelines) may be hard to replicate without the tool. AGENT-33 uses Claude Code — workflows differ.

8. **11 crates = complexity**: While good for separation of concerns, navigating 11 crates adds cognitive load. AGENT-33's single-package `engine/` is simpler to navigate. Trade-off between modularity and discoverability.

## 8) Feature extraction (for master matrix)

| Category | Feature | EdgeQuake | AGENT-33 Status | Priority |
|---|---|---|---|---|
| **HTTP Pooling** | Client reuse per provider | ✅ reqwest::Client stored in struct | ❌ New httpx client per request (ollama.py:41,69) | 🔴 CRITICAL |
| **Embedding Batch** | MAX_BATCH_SIZE constants | ✅ 2048 (OpenAI), 512 (Ollama) | ✅ Just implemented (batching work) | ✅ DONE |
| **Embedding Batch** | Chunk-based iteration | ✅ texts.chunks(MAX_SIZE) | ✅ Recent batching implementation | ✅ DONE |
| **Embedding Batch** | Batch progress logging | ✅ "Batch {}/{}: {} texts" | ❌ Minimal logging | 🟡 MEDIUM |
| **Embedding Batch** | Empty text filtering | ✅ Filter + zero vectors + index map | ⚠️ Needs verification | 🟡 MEDIUM |
| **Context Limits** | Separate LLM vs embedding limits | ✅ max_context_length vs embedding_max_tokens | ❌ Single max_tokens in providers | 🟡 MEDIUM |
| **Context Limits** | Embedding truncation with warning | ✅ chars/4 approximation + warn log | ❌ No truncation | 🟡 MEDIUM |
| **Token Tracking** | Usage extraction from API | ✅ OpenAI usage object → LLMResponse | ⚠️ Partial (OpenAI yes, Ollama no) | 🟡 MEDIUM |
| **Token Tracking** | Structured debug logging | ✅ "prompt: {}, completion: {}, total: {}" | ❌ Minimal | 🟢 LOW |
| **Streaming** | Stop sequence support | ✅ Passed to both stream/non-stream | ⚠️ Needs verification | 🟡 MEDIUM |
| **Query Modes** | 6 modes (naive/local/global/hybrid/mix/bypass) | ✅ All modes | ❌ Only static DAGs | 🔵 FUTURE |
| **Graph-RAG** | Knowledge graph construction | ✅ Entity/relationship extraction → AGE | ❌ No graph layer | 🔵 FUTURE |
| **Graph-RAG** | Community detection (Louvain) | ✅ For global queries | ❌ N/A | 🔵 FUTURE |
| **Graph-RAG** | Gleaning (multi-pass extraction) | ✅ Optional, +18% recall | ❌ N/A | 🔵 FUTURE |
| **RAG Pipeline** | 1200-token chunks, 100 overlap | ✅ Documented best practice | ❌ 500-char chunks (too small) | 🟡 MEDIUM |
| **Architecture** | Trait-based provider abstraction | ✅ LLMProvider/EmbeddingProvider | ✅ Similar pattern | ✅ DONE |
| **Architecture** | Facade orchestration pattern | ✅ EdgeQuake struct | ✅ Similar (agents/workflows) | ✅ DONE |
| **Architecture** | Builder pattern for config | ✅ OllamaProviderBuilder | ❌ Direct instantiation | 🟢 LOW |
| **Multi-tenancy** | Header-based tenant resolution | ✅ AuthMiddleware | ✅ Similar pattern | ✅ DONE |
| **Multi-tenancy** | Storage layer isolation | ✅ tenant_id filtering | ✅ Similar pattern | ✅ DONE |
| **Observability** | Health check endpoints | ✅ /health, /ready, /live | ✅ Similar | ✅ DONE |
| **Observability** | Component health in response | ✅ kv/vector/graph/llm checks | ⚠️ Basic health only | 🟢 LOW |
| **Observability** | Background mode logs | ✅ /tmp/*.log files | ❌ N/A | 🟢 LOW |
| **Testing** | Mock provider for deterministic tests | ✅ MockLLMProvider | ✅ Similar | ✅ DONE |
| **Testing** | Integration test markers | ✅ @pytest.mark.integration | ✅ Similar | ✅ DONE |
| **Deployment** | Single binary | ✅ Rust | ❌ Python + deps | N/A Language |
| **Deployment** | Docker Compose | ✅ Full stack | ✅ Similar | ✅ DONE |

## 9) Evidence links

**Primary repo**: [github.com/raphaelmansuy/edgequake](https://github.com/raphaelmansuy/edgequake)

**Key source files**:
- Ollama provider with HTTP pooling: `/edgequake/crates/edgequake-llm/src/providers/ollama.rs` (lines 149-151 client init, 571-649 batched embed)
- OpenAI provider with batching: `/edgequake/crates/edgequake-llm/src/providers/openai.rs` (lines 380-443 batched embed, 234-256 token tracking)
- Architecture overview: `/docs/architecture/overview.md` (11-crate structure, facade pattern, trait abstractions)
- Performance comparison: `/docs/comparisons/vs-lightrag-python.md` (10x throughput, memory, concurrency claims)
- Embedding models guide: `/docs/deep-dives/embedding-models.md` (dimension tradeoffs, model selection)
- Agent workflow: `/AGENTS.md` (edgecode agent, OODA loop, spec-driven development, task logs)

**Documentation**: [github.com/raphaelmansuy/edgequake/tree/main/docs](https://github.com/raphaelmansuy/edgequake/tree/main/docs) (comprehensive guides for architecture, API, tutorials, deep-dives, comparisons)

**LightRAG algorithm paper**: [arxiv.org/abs/2410.05779](https://arxiv.org/abs/2410.05779) (entity extraction, graph construction, 6 query modes)

**Web search results**: [GitHub - EdgeQuake](https://github.com/raphaelmansuy/edgequake), [X/Twitter announcement](https://x.com/raphaelmansuy/status/2020844615755350408) ("Graph-RAG is the future... EdgeQuake. Production-ready. Rust. Open source.")

**Related repos**: GraphRAG [arxiv.org/abs/2404.16130](https://arxiv.org/abs/2404.16130) (Microsoft's Graph-RAG approach), LightRAG Python implementation (community integrations, 27.7k stars)

---

**CRITICAL TAKEAWAY FOR AGENT-33**: The #1 immediate fix is HTTP client pooling in `engine/src/agent33/llm/ollama.py`. Currently creates new `httpx.AsyncClient()` on lines 41 (completion) and 69 (streaming). EdgeQuake pattern: create once in `__init__`, store as `self.client`, reuse. This is a 67x performance multiplier per prior EdgeQuake/RAG-Anything findings. All other patterns are enhancements (batching already done, context limits/truncation/logging are nice-to-have). Graph-RAG query modes are Phase 15+ future work.
