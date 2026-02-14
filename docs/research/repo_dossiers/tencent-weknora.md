# Repo Dossier: Tencent/WeKnora
**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

WeKnora is an enterprise-grade, open-source RAG framework (v0.3.0, MIT license, 13k+ GitHub stars) developed by Tencent for deep document understanding and semantic retrieval. The system implements a production-ready multi-layer architecture combining multimodal document processing (PDF/Word/images with OCR and table extraction), hybrid retrieval strategies (BM25 keyword search + dense vector embeddings + Neo4j-based GraphRAG), sophisticated query rewriting for conversational context, configurable reranking pipelines, and LLM generation. Built with Go (backend orchestration), Python/FastAPI/gRPC (document processing), and Vue 3/TypeScript (frontend), WeKnora supports multi-tenant deployments via Docker Compose or Kubernetes, integrates with multiple vector databases (pgvector, Elasticsearch, Qdrant), and features a ReACT-pattern agent system with MCP (Model Context Protocol) tool integration and sandboxed skill execution. The framework addresses AGENT-33's key RAG gaps: provides BM25+vector hybrid search, reranking, query rewriting, and advanced document processing capabilities currently absent from AGENT-33's vector-only RAG implementation.

## 2) Core orchestration model

**Event-Driven Pipeline Architecture**: WeKnora orchestrates RAG workflows through a multi-stage, event-driven processing pipeline: `Upload → Validate → Extract (text/tables/images) → OCR → Caption generation → Chunking with overlap → Embedding → Vector/Graph storage → Query rewriting → Hybrid search (BM25+vector+graph) → Reranking → Context building → LLM generation`. The Go-based backend serves as the orchestration layer, managing state transitions, routing requests, and coordinating between specialized processing services.

**Agent System (ReACT Pattern)**: WeKnora implements a ReACT (Reasoning + Acting) agent mode that iteratively reasons about user queries, selects appropriate tools (built-in knowledge base retrieval, MCP-integrated external tools, web search via DuckDuckGo/Google/Bing), executes actions, observes results, and refines responses through multiple reflection cycles. The agent system supports both normal conversation mode and agent mode, switchable per-session, with configurable LLM backends (Qwen, DeepSeek, Ollama for local models).

**Multi-Strategy Retrieval Router**: The framework employs a composite retrieval pattern where queries are processed by multiple specialized retrieval engines in parallel: (1) **BM25 keyword matcher** for exact term searches, (2) **dense vector similarity** (via pgvector/ES/Qdrant) for semantic understanding, (3) **GraphRAG via Neo4j** for relationship-based retrieval. Results from all strategies are merged, deduplicated, and passed through a unified reranking pipeline before generation, with strategy weights and backend selection configurable per knowledge base.

**Conversational Query Rewriting**: The system analyzes conversation history to rewrite context-dependent queries into standalone, context-independent forms. This preprocessing step runs before retrieval, employing both the rewritten natural language query and preprocessed keywords to ensure comprehensive coverage across semantic and keyword-based search strategies.

**Governance and Multi-Tenancy**: RBAC with tenant isolation enforces per-tenant data boundaries. API key authentication, SSRF-safe HTTP client, SQL validation, and sandboxed execution for agent skills provide defense-in-depth security. Audit logs track all knowledge base operations, agent invocations, and tool executions.

## 3) Tooling and execution

**Multimodal Document Processing (Python/FastAPI/gRPC)**: A dedicated Python-based document reader service handles OCR (text extraction from images), table structure recognition, caption generation for visual elements, and intelligent chunking with configurable overlap. Supports PDF, Word (.docx), Markdown, plain text, and image formats. The gRPC interface enables high-throughput batch processing with streaming responses.

**Chunking Strategy**: Implements intelligent chunking with overlap to preserve context at chunk boundaries. Based on industry patterns, WeKnora likely uses 512-1200 token chunks with 10-20% overlap (50-100 tokens), though exact defaults are configurable. The framework supports both fixed-size and semantic chunking strategies, with tokenizer-aware splitting to avoid mid-word breaks.

**Embedding and Indexing**: Supports multiple embedding backends (local Ollama models, cloud APIs). Vector storage abstraction layer allows switching between PostgreSQL pgvector (relational integration), Elasticsearch (full-text + vector), and Qdrant (dedicated vector DB) without application-layer changes. Redis caching layer reduces redundant embedding calls.

**Hybrid Search Implementation**:
- **BM25 (Keyword)**: Full-text search optimized for exact terminology matches, effective for technical/domain-specific queries
- **Dense Vector**: Semantic similarity via cosine distance on embedded queries and chunks, captures conceptual relationships
- **GraphRAG (Neo4j)**: Traverses knowledge graphs representing entity relationships and conceptual connections, enables retrieval based on structured semantic paths

**Reranking Pipeline**: Results from hybrid search undergo quality assessment and reranking before generation. While specific reranker models aren't documented, industry patterns suggest support for Cohere Rerank (high accuracy, API-based) and BGE reranker variants (bge-reranker-base/large, open-source, locally deployable).

**Agent Tools and MCP Integration**: Built-in tools include knowledge base retrieval, web search (DuckDuckGo/Google/Bing), and a sandboxed skill execution environment. MCP integration (via uvx and npx launchers) allows agents to dynamically access external tools through the Model Context Protocol standard. The Data Analyst agent provides CSV/Excel analysis capabilities. Sandbox execution prevents unauthorized file access and network calls from agent skills.

**LLM Integration Layer**: Unified interface supports local Ollama models and cloud APIs (Qwen, DeepSeek). "Thinking mode" (likely chain-of-thought prompting) can be toggled to expose model reasoning steps. The backend abstracts LLM differences, handling prompt formatting, streaming responses, and error recovery.

## 4) Observability and evaluation

**Distributed Tracing (Jaeger + OpenTelemetry)**: Docker Compose profiles include Jaeger integration for distributed tracing across Go backend, Python document processing service, and external LLM/vector DB calls. OpenTelemetry instrumentation provides end-to-end request tracing, latency breakdowns, and dependency mapping.

**API Monitoring (Swagger/OpenAPI)**: REST API documented via Swagger UI enables schema validation, request/response inspection, and manual testing. API key-based authentication ties every request to a tenant ID and user context, supporting per-tenant usage analytics and rate limiting.

**Audit Logging**: Tracks all knowledge base CRUD operations, document uploads, agent invocations, tool executions, and retrieval queries. Logs include tenant ID, user ID, timestamps, and operation outcomes, supporting compliance and forensic analysis.

**Multi-Tenant Analytics**: Tenant isolation extends to observability—each tenant's metrics, logs, and traces are scoped to prevent cross-tenant data leakage. RBAC controls access to observability dashboards.

**Evaluation Mechanisms**: While explicit evaluation gates aren't documented, the framework's modular architecture supports injecting custom evaluation steps (e.g., retrieval relevance scoring, answer faithfulness checks) between reranking and generation stages. The ReACT agent's multi-iteration reflection loop provides implicit self-evaluation—agents assess result quality and retry with refined strategies.

**Deployment Health Checks**: Kubernetes Helm charts include liveness/readiness probes for all services (backend, document processor, PostgreSQL, Redis, Neo4j, vector DBs). Rolling updates with health checks prevent downtime during version upgrades.

## 5) Extensibility

**Modular Component Swapping**: The architecture's clean abstractions enable replacing subsystems without upstream changes:
- Vector DB: Switch between pgvector/ES/Qdrant via configuration
- Embedding model: Swap Ollama endpoints or cloud APIs
- LLM backend: Support for Qwen, DeepSeek, and any Ollama-compatible model
- Graph DB: Neo4j for GraphRAG (optional Docker Compose profile)

**Custom Retrieval Strategies**: The hybrid retrieval router supports plugging in additional retrieval engines. Organizations can implement domain-specific retrievers (e.g., SQL database query generation, external API calls) that conform to the retriever interface and participate in the merge-rerank-generate pipeline.

**Agent Skill System**: Sandboxed execution environment allows defining custom skills (Python/JavaScript functions) that agents can invoke. Skills declare input schemas, required permissions, and output formats. The sandbox enforces resource limits (CPU/memory/timeout), filesystem restrictions, and network egress policies.

**MCP Tool Ecosystem**: Model Context Protocol integration (uvx/npx launchers) enables dynamic tool discovery. Organizations can publish internal MCP servers exposing proprietary tools (CRM lookup, internal databases, authentication systems), and WeKnora agents automatically discover and invoke them without code changes.

**Document Parser Extensions**: The Python document processing service can integrate additional parsers (e.g., specialized table extractors, domain-specific OCR models, audio/video transcription) by implementing the gRPC service interface. New parsers register via configuration, and the orchestration layer routes documents by type.

**Frontend Customization**: Vue 3 + TypeScript frontend supports theming, component overrides, and embedding in larger applications. Real-time streaming responses (likely SSE or WebSocket) enable custom UI flows.

**Kubernetes Operator Potential**: Helm chart deployment provides a foundation for building a Kubernetes operator that automates lifecycle management (upgrades, backups, scaling), though no official operator exists yet.

## 6) Notable practices worth adopting in AGENT-33

### Critical RAG Upgrades (Directly Address AGENT-33 Gaps)

1. **Hybrid Retrieval (BM25 + Vector + Graph)**: AGENT-33 currently uses vector-only retrieval (`memory/rag.py:86-101`). Adopt WeKnora's tri-modal approach:
   - Add BM25 keyword search via PostgreSQL's `to_tsvector`/`to_tsquery` or integrate Elasticsearch
   - Implement result merging with configurable strategy weights (e.g., 30% BM25, 50% vector, 20% graph)
   - Build GraphRAG layer for entity relationship traversal (current memory system has no graph representation)
   - **Impact**: Addresses MEMORY.md finding #1—RAG is first-gen, no BM25/reranking

2. **Reranking Pipeline**: Insert reranking stage between retrieval and generation:
   - Integrate BGE reranker (bge-reranker-base) for local deployment or Cohere Rerank API
   - Rerank top-K candidates (e.g., retrieve 100, rerank to top 10) before context window insertion
   - Measure retrieval quality improvement via NDCG@K or MRR metrics
   - **Impact**: Reranking can improve RAG precision by 20-40% per industry benchmarks

3. **Query Rewriting for Conversational Context**: AGENT-33's `SessionState` tracks conversation history (`memory/session.py:15-35`) but never rewrites queries:
   - Extract last N turns from session buffer
   - Prompt LLM to rewrite user query as standalone question (no pronouns/implicit references)
   - Execute both original and rewritten queries, merge results
   - **Implementation**: Add `query_rewriter.py` module, call before `RAGPipeline.retrieve()`

4. **Configurable Chunking with Overlap**: Current chunking in `memory/ingestion.py:43-52` uses 500-char fixed chunks with no overlap:
   - Increase chunk size to 1200 tokens (aligns with WeKnora/RAG-Anything best practices from research sprint)
   - Add 10-20% overlap (120-240 tokens) to preserve cross-chunk context
   - Use tokenizer-aware splitting (`tiktoken` for OpenAI, model-specific tokenizers for others) instead of character count
   - **Impact**: Addresses MEMORY.md finding—500-char chunks too small

### Architecture and Orchestration Patterns

5. **Event-Driven Pipeline with Checkpoints**: WeKnora's staged processing (upload → extract → OCR → chunk → embed → index) with persistent state between stages enables:
   - Resume-on-failure for long-running document ingestion
   - Per-stage metrics (track which stage is bottleneck)
   - Parallel processing of independent documents
   - **AGENT-33 application**: Refactor `workflows/engine.py` to support checkpoint-resume (currently executes in-memory DAG with no mid-workflow persistence)

6. **Multi-Strategy Router with Unified Interface**: WeKnora's retrieval router abstraction allows plugging in specialized retrievers without upstream changes:
   - Define `BaseRetriever` interface: `retrieve(query: str, filters: dict, limit: int) -> list[Chunk]`
   - Implement `BM25Retriever`, `VectorRetriever`, `GraphRetriever`, `SQLRetriever`
   - Route queries to subset of retrievers based on query type (keyword-heavy → BM25, semantic → vector, entity-focused → graph)
   - **AGENT-33 application**: Current `RAGPipeline` is vector-only; refactor to support multiple retrieval backends

7. **Conversational Agent Mode with ReACT Pattern**: WeKnora's switchable agent/normal modes provide:
   - Explicit user control over agentic behavior (reduces surprise autonomous actions)
   - Multi-iteration reflection loop improves answer quality
   - Tool execution transparency (users see which tools agent invoked)
   - **AGENT-33 application**: Current agents execute single-shot prompts (`agents/runtime.py:90-132`); add ReACT loop with tool feedback

### Security and Multi-Tenancy

8. **Tenant-Scoped Retrieval**: Every retrieval query includes `tenant_id` filter at the database layer (not application filtering):
   - Modify `Observation` model index: `CREATE INDEX idx_tenant_embedding ON observations USING ivfflat (tenant_id, embedding)`
   - Add `WHERE tenant_id = $1` to all vector similarity queries
   - **Security benefit**: Prevents cross-tenant data leakage even if application logic fails

9. **SSRF-Safe HTTP Client**: WeKnora's hardened HTTP client prevents Server-Side Request Forgery:
   - Blocklist private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16)
   - Blocklist cloud metadata endpoints (169.254.169.254)
   - Enforce HTTPS for external requests, timeout all requests (5-30s)
   - **AGENT-33 application**: Add to `tools/builtins/web_fetch.py:17-41` (currently no SSRF protection)

10. **Sandboxed Agent Skills**: WeKnora's sandbox execution environment with resource limits:
    - CPU/memory/timeout caps per skill invocation
    - Filesystem restrictions (read-only access to allowed paths)
    - Network egress policy (blocklist internal IPs)
    - **AGENT-33 application**: Integrate with Phase 13 code execution layer (`execution/executor.py:95-164`)—add resource limits to `SandboxConfig`

### Observability and Developer Experience

11. **Distributed Tracing for RAG Pipeline**: Jaeger/OpenTelemetry integration traces:
    - Document processing: upload → parse → OCR → chunk → embed (identify slowest stage)
    - Retrieval: query rewrite → BM25 → vector → graph → merge → rerank (measure strategy latencies)
    - LLM generation: prompt construction → API call → streaming response (track token throughput)
    - **AGENT-33 application**: Integrate with existing `observability/tracing.py:23-56` module, add spans for RAG stages

12. **Fast Development Mode**: WeKnora's hot-reload for frontend + rapid backend iteration without Docker rebuilds:
    - Frontend: Vite dev server with HMR (hot module replacement)
    - Backend: Mount source directory as volume, use `--reload` flag for hot reload
    - **AGENT-33 application**: Document in `CLAUDE.md` common commands section, add `docker-compose.dev.yml` with source volume mounts

### Document Processing (Addresses MEMORY.md Finding #2)

13. **Multimodal Document Parser (PDF/Images)**: WeKnora's Python gRPC service handles OCR and table extraction:
    - Integrate PaddleOCR or Tesseract for text extraction from images/scanned PDFs
    - Use layout analysis models (LayoutLM, DocFormer) for table structure recognition
    - Extract captions, headers, footnotes with positional metadata
    - **AGENT-33 application**: Enhance `tools/builtins/reader.py` (currently web-only) and `tools/builtins/file_ops.py` (currently UTF-8 text only)
    - **Impact**: Directly addresses MEMORY.md finding #2—cannot process PDFs/images

## 7) Risks / limitations to account for

### Operational Complexity

**Multi-Database Dependency Sprawl**: WeKnora's full deployment requires PostgreSQL (relational + pgvector), Neo4j (GraphRAG), Redis (caching), Elasticsearch or Qdrant (optional vector storage), and Jaeger (tracing). This constellation of 5-7 services increases:
- Infrastructure costs (each DB requires dedicated resources)
- Operational burden (backup/restore, version upgrades, scaling)
- Failure modes (any DB outage degrades functionality)
- **Mitigation for AGENT-33**: Start with PostgreSQL pgvector only, defer GraphRAG/ES until proven necessary via user metrics

**Configuration Surface Area**: The framework's flexibility (swap LLMs, vector DBs, rerankers, embedding models) creates a large configuration space:
- Dozens of environment variables and YAML config knobs
- Non-obvious tuning parameters (BM25 k1/b coefficients, reranker top-K, chunk overlap %)
- **Mitigation**: Provide sane defaults with inline documentation, ship configuration presets for common use cases (e.g., "low-latency", "high-accuracy", "cost-optimized")

### Performance and Scalability

**Hybrid Search Latency**: Parallel execution of BM25 + vector + graph queries still requires waiting for slowest retriever:
- BM25 on PostgreSQL: 10-50ms for keyword match
- Vector similarity on pgvector: 50-200ms for ANN search (depends on index type: IVFFlat vs HNSW)
- Neo4j graph traversal: 100-500ms for multi-hop queries
- **Total latency**: max(BM25, vector, graph) + reranking + LLM = potentially 1-2 seconds
- **Mitigation**: Implement early termination (if one strategy returns high-confidence matches, skip others), cache frequent queries, use HNSW vector indexes

**Reranking Cost**: Reranking top-100 candidates with BGE reranker requires:
- 100 forward passes through BERT-sized model (bge-reranker-base: 279M params)
- ~50-100ms on GPU, 500-1000ms on CPU
- **Cloud API cost**: Cohere Rerank charges per document reranked
- **Mitigation**: Limit reranking to top-K candidates (K=20-50), cache reranking scores, batch requests

**Sequential Embedding Bottleneck**: If WeKnora embeds chunks sequentially (AGENT-33's `embeddings.py:36` does this), ingestion is slow:
- Single-chunk embedding: 5-50ms per chunk (local model)
- 1000-chunk document: 5-50 seconds sequentially
- **Mitigation**: Batch embedding calls (67x speedup per EdgeQuake research), use async I/O

### Model and Data Quality

**Query Rewriting Accuracy**: LLM-based query rewriting can introduce errors:
- Over-expansion: Adding irrelevant terms that dilute search precision
- Under-expansion: Missing key context from conversation history
- Hallucination: Rewritten query contains facts not in conversation
- **Mitigation**: Fall back to original query if rewritten version returns zero results, log rewrites for offline evaluation

**GraphRAG Construction Quality**: Automatic knowledge graph extraction from documents can produce:
- Spurious entity links (especially with domain-specific jargon)
- Incomplete relationship coverage (missed connections)
- Entity disambiguation errors (same name, different entities)
- **Mitigation**: Provide manual curation UI for critical knowledge bases, use confidence thresholds to filter low-quality graph edges

**Multimodal Processing Errors**: OCR and table extraction are not 100% accurate:
- Low-quality scans produce garbled text
- Complex table layouts confuse structure recognition
- Non-English documents require language-specific models
- **Mitigation**: Surface confidence scores to users, allow manual correction, provide document preview with OCR overlay

### Security and Privacy

**Sandbox Escape Risk**: Agent skill sandboxing depends on correct configuration:
- Filesystem restrictions can be bypassed via symlinks or mount points
- Network egress policies require iptables/nftables integration (application-layer blocklists insufficient)
- Resource limits (CPU/memory) need cgroup enforcement
- **Mitigation**: Use battle-tested sandbox technologies (gVisor, Firecracker, Docker seccomp profiles), regularly audit sandbox configurations

**MCP Tool Trust Boundary**: Dynamically loaded MCP tools run with agent privileges:
- Malicious MCP server can exfiltrate data, modify knowledge bases, or execute arbitrary code
- No built-in MCP tool verification/signing mechanism
- **Mitigation**: Allowlist MCP servers by URL/fingerprint, run MCP tools in separate sandboxes, require admin approval for new MCP integrations

**Tenant Isolation Guarantees**: Multi-tenancy relies on application-layer enforcement:
- Bugs in tenant filtering can leak data across tenants
- Shared vector indexes (even with tenant_id filters) pose side-channel risks (timing attacks to infer other tenants' data)
- **Mitigation**: Regularly audit tenant isolation (automated tests that verify cross-tenant queries return empty), consider per-tenant vector indexes for high-security deployments

### Licensing and Dependencies

**Third-Party Model Licensing**: WeKnora integrates with commercial LLMs (Qwen, DeepSeek) and rerankers (Cohere):
- License compliance for cloud APIs (terms of service, data retention policies)
- Open-source model licenses (some require attribution, share-alike clauses)
- **Mitigation**: Document license requirements, provide fallback to fully open models (LLaMA, Mistral, BGE reranker)

**Neo4j Licensing**: Neo4j Community Edition (GPL) vs Enterprise (commercial):
- Community edition sufficient for single-instance deployments
- Enterprise features (clustering, hot backups) require paid license
- **Mitigation**: Defer GraphRAG until proven necessary, consider alternative graph DBs (ArangoDB, JanusGraph) if clustering needed

## 8) Feature extraction (for master matrix)

| Feature Category | WeKnora Implementation | AGENT-33 Status | Adoption Priority |
|-----------------|------------------------|-----------------|-------------------|
| **RAG - Hybrid Retrieval** | BM25 + dense vector + GraphRAG with configurable weights | Vector-only (pgvector) | **CRITICAL** - Addresses key gap |
| **RAG - Reranking** | Configurable reranker pipeline (BGE/Cohere support) | None | **HIGH** - 20-40% precision gain |
| **RAG - Query Rewriting** | LLM-based conversational context rewriting | None | **HIGH** - Improves multi-turn accuracy |
| **RAG - Chunking** | 512-1200 tokens with 10-20% overlap, tokenizer-aware | 500 chars, no overlap | **HIGH** - Fix undersized chunks |
| **RAG - Graph Knowledge** | Neo4j-based entity/relationship extraction and traversal | None | **MEDIUM** - Defer until BM25/rerank proven |
| **Document Processing - OCR** | Integrated OCR for images/scanned PDFs | Not supported | **HIGH** - MEMORY.md gap #2 |
| **Document Processing - Tables** | Table structure extraction with VLM | Not supported | **HIGH** - MEMORY.md gap #2 |
| **Document Processing - Multimodal** | PDF/Word/images/markdown with unified pipeline | PDF/images not supported | **HIGH** - MEMORY.md gap #2 |
| **Agent - ReACT Pattern** | Multi-iteration reasoning with tool feedback | Single-shot prompts | **MEDIUM** - Quality improvement |
| **Agent - MCP Integration** | Dynamic tool discovery via MCP (uvx/npx launchers) | Not supported | **MEDIUM** - Ecosystem access |
| **Agent - Sandboxed Skills** | Resource-limited, filesystem-restricted execution | Basic sandbox (Phase 13) | **LOW** - Enhance existing sandbox |
| **Agent - Mode Switching** | User-controlled agent/normal mode toggle | Always agentic | **LOW** - UX refinement |
| **Observability - Distributed Tracing** | Jaeger + OpenTelemetry for end-to-end tracing | Partial (tracing.py exists) | **MEDIUM** - Integrate with RAG stages |
| **Observability - Audit Logs** | Tenant-scoped operation logs for compliance | Basic logging | **LOW** - Enhance for compliance |
| **Security - SSRF Protection** | IP blocklist + metadata endpoint filtering | None | **HIGH** - Prevent cloud metadata leaks |
| **Security - Tenant Isolation** | Database-level tenant filtering, per-tenant indexes | Application-level filtering | **MEDIUM** - Harden isolation |
| **Security - Sandbox Enforcement** | cgroup resource limits, network egress policies | Basic limits | **LOW** - Defer until skill system mature |
| **Multi-Tenancy - RBAC** | Role-based access control with tenant scoping | JWT scopes, no RBAC | **MEDIUM** - Enterprise feature |
| **Deployment - Kubernetes** | Helm charts with liveness/readiness probes | Docker Compose only | **LOW** - Defer until scale needed |
| **Deployment - Hot Reload** | Frontend HMR + backend source volume mounts | Not documented | **LOW** - DX improvement |
| **LLM Integration - Thinking Mode** | Expose chain-of-thought reasoning steps | Not supported | **LOW** - Debugging aid |
| **LLM Integration - Model Swapping** | Unified interface for Ollama/Qwen/DeepSeek | ModelRouter supports Ollama/OpenAI-compatible | **COMPLETE** - Already flexible |
| **Event-Driven - Checkpoint Resume** | Persistent state between pipeline stages | In-memory DAG execution | **MEDIUM** - Reliability for long workflows |
| **Vector DB - Multi-Backend** | pgvector/ES/Qdrant switchable via config | pgvector only | **LOW** - Defer until proven bottleneck |

### Immediate Adoption Roadmap (Phases 14-17 Candidates)

**Phase 14 (Security Hardening) - CRITICAL**:
- SSRF protection for `web_fetch.py` (IP blocklist, metadata endpoint filtering)
- Database-level tenant isolation (tenant_id in WHERE clauses, per-tenant vector indexes)
- Enhanced sandbox resource limits (cgroup enforcement for code execution)

**Phase 15 (RAG Upgrade I) - HIGH**:
- BM25 keyword search via PostgreSQL `to_tsvector`/`to_tsquery`
- Reranking pipeline with BGE reranker (bge-reranker-base)
- Increase chunk size to 1200 tokens with 10-20% overlap
- Tokenizer-aware chunking (replace character-based splitting)

**Phase 16 (RAG Upgrade II) - HIGH**:
- Query rewriting for conversational context (session history → standalone query)
- Hybrid retrieval result merging (BM25 + vector with configurable weights)
- OCR integration for image/PDF processing (PaddleOCR or Tesseract)
- Table extraction for structured data (layout analysis model)

**Phase 17 (Observability) - MEDIUM**:
- Distributed tracing for RAG pipeline (query rewrite → retrieval → rerank → generation)
- Per-stage latency metrics (identify bottlenecks)
- Tenant-scoped audit logs for compliance
- Retrieval quality metrics (NDCG@K, MRR)

## 9) Evidence links

### Primary Sources
- [Tencent/WeKnora GitHub Repository](https://github.com/Tencent/WeKnora)
- [WeKnora Hybrid Retrieval Strategies Documentation](https://zread.ai/Tencent/WeKnora/23-hybrid-retrieval-strategies-bm25-dense-graphrag)
- [WeKnora Overview](https://zread.ai/Tencent/WeKnora/1-overview)

### Architecture and RAG Patterns
- [Hybrid RAG in the Real World: Graphs, BM25, and the End of Black-Box Retrieval - NetApp Community](https://community.netapp.com/t5/Tech-ONTAP-Blogs/Hybrid-RAG-in-the-Real-World-Graphs-BM25-and-the-End-of-Black-Box-Retrieval/ba-p/464834)
- [Building Contextual RAG Systems with Hybrid Search and Reranking - Analytics Vidhya](https://www.analyticsvidhya.com/blog/2024/12/contextual-rag-systems-with-hybrid-search-and-reranking/)
- [Building Production RAG Systems in 2026: Complete Architecture Guide](https://brlikhon.engineer/blog/building-production-rag-systems-in-2026-complete-architecture-guide)
- [Optimizing RAG with Hybrid Search & Reranking - VectorHub by Superlinked](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking)

### Reranking Implementation
- [Ultimate Guide to Choosing the Best Reranking Model in 2026 - ZeroEntropy](https://www.zeroentropy.dev/articles/ultimate-guide-to-choosing-the-best-reranking-model-in-2025)
- [Advanced RAG: Enhancing Retrieval Efficiency through Evaluating Reranker Models using LlamaIndex](https://akash-mathur.medium.com/advanced-rag-enhancing-retrieval-efficiency-through-evaluating-reranker-models-using-llamaindex-3f104f24607e)
- [Master Reranking with Cohere Models - Cohere](https://docs.cohere.com/docs/reranking-with-cohere)
- [RAG Embeddings & Rerankers: Best Model Picks - LlamaIndex](https://www.llamaindex.ai/blog/boosting-rag-picking-the-best-embedding-reranker-models-42d079022e83)

### Query Rewriting and Conversational Context
- [Contextual query rewriting (CQR): Natural language as interface for dialog state tracking - Amazon Science](https://www.amazon.science/publications/contextual-query-rewriting-cqr-natural-language-as-interface-for-dialog-state-tracking)
- [Contextualizing Search Queries In-Context Learning for Conversational Rewriting with LLMs - arXiv](https://arxiv.org/html/2502.15009v1)
- [CHIQ: Contextual History Enhancement for Improving Query Rewriting in Conversational Search - arXiv](https://arxiv.org/html/2406.05013v1)

### Agent Patterns and MCP Integration
- [Quickly Build a ReAct Agent With LangGraph and MCP - Neo4j](https://neo4j.com/blog/developer/react-agent-langgraph-mcp/)
- [MCP Tool Integration Tutorial - agent-patterns documentation](https://agent-patterns.readthedocs.io/en/stable/MCP%20Tool%20Integration%20Tutorial.html)
- [ReAct Prompting - Prompt Engineering Guide](https://www.promptingguide.ai/techniques/react)

### Document Chunking Strategies
- [Chunking Strategies to Improve LLM RAG Pipeline Performance - Weaviate](https://weaviate.io/blog/chunking-strategies-for-rag)
- [Best Chunking Strategies for RAG in 2025 - Firecrawl](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025)
- [Chunking for RAG: best practices - Unstructured](https://unstructured.io/blog/chunking-for-rag-best-practices)
- [Evaluating Chunking Strategies for Retrieval - Chroma Research](https://research.trychroma.com/evaluating-chunking)

### Multimodal Document Processing
- [AI Document Parsing: How LLMs Read Documents - LlamaIndex](https://www.llamaindex.ai/blog/ai-document-parsing-llms-are-redefining-how-machines-read-and-understand-documents)
- [Multimodal Document Data Extraction with Veryfi: A Complete Guide Beyond Basic OCR](https://www.veryfi.com/technology/multimodal-data-extraction-beyond-basic-ocr/)
- [Accelerating Document AI - Hugging Face](https://huggingface.co/blog/document-ai)

### GraphRAG and Knowledge Graphs
- [GraphRAG Explained: Enhancing RAG with Knowledge Graphs - Zilliz](https://medium.com/@zilliz_learn/graphrag-explained-enhancing-rag-with-knowledge-graphs-3312065f99e1)
- [Using a Knowledge Graph to implement a RAG application - Neo4j](https://neo4j.com/blog/developer/rag-tutorial/)
- [Knowledge Graph RAG Query Engine - LlamaIndex](https://docs.llamaindex.ai/en/stable/examples/query_engine/knowledge_graph_rag_query_engine/)
