# Repo Dossier: HKUDS/RAG-Anything

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

RAG-Anything (13.2k stars, MIT license) is a multimodal retrieval-augmented generation framework built on LightRAG that extends traditional text-only RAG to handle heterogeneous document content—PDFs, Office documents, images, tables, equations, and charts—within a unified pipeline. The system implements a five-stage architecture: document parsing via MinerU/Docling, content analysis and modality routing, multimodal understanding with specialized processors, knowledge graph construction with entity/relationship extraction, and intelligent retrieval combining vector similarity with graph traversal. Unlike traditional chunking-then-embedding approaches, RAG-Anything constructs a dual-graph representation capturing both cross-modal relationships and textual semantics, enabling "vector-graph fusion" retrieval that performs structural knowledge navigation alongside semantic matching. The framework supports six retrieval modes (local, global, hybrid, naive, mix, bypass) with optional reranking via Jina/Cohere/Aliyun models, uses 1200-token chunks with 100-token overlap (configurable via TikToken), and provides direct content injection APIs for bypassing document parsing.

## 2) Core orchestration model

**Graph-augmented RAG with knowledge graph as first-class primitive, not traditional chunk-based retrieval.**

RAG-Anything implements orchestration through a `RAGAnything` class that delegates core RAG operations to the underlying LightRAG framework. The orchestration model is fundamentally different from AGENT-33's workflow DAGs:

- **Document processing pipeline**: Documents flow through `process_document_complete()` which invokes external parsers (MinerU 2.0 or Docling) as subprocesses, extracts structured content blocks (text, image, table, equation), and routes each modality through specialized processors. No agent delegation occurs—orchestration is purely pipeline-based.

- **Knowledge graph construction**: Instead of storing chunks directly, the system extracts entities and relationships via LLM-driven analysis (`entity_extract_max_gleaning` loops), merges duplicates with strategy-based conflict resolution, and persists to dual storage (graph + vectors). Entity vectors use "ent-" prefix with mdhash IDs; relationship vectors use "rel-" prefix from src+tgt concatenation.

- **Query routing**: Six retrieval modes determine execution path—local mode retrieves context-dependent info via vector similarity, global mode performs graph traversal, hybrid combines both, mix mode adds reranking, naive is basic vector search, bypass skips retrieval. No LLM-driven routing decisions; mode is user-specified at query time.

- **Modality-aware processing**: Content types trigger different processors (`get_processor_for_type()`) that generate descriptions (e.g., vision models for images, table formatters for structured data). Processors run concurrently via asyncio, controlled by `max_concurrent_files` config.

**Critical difference from AGENT-33**: RAG-Anything has no multi-agent orchestration, no workflow engine, no conditional branching based on LLM decisions. It's a sequential pipeline with parallel modality processing, not a DAG executor. Orchestration is implicit in method call chains (`parse → analyze → extract → index → query`) rather than explicit workflow definitions.

## 3) Tooling and execution

**External subprocess delegation for parsing, LLM APIs for extraction, pluggable storage backends.**

### Document Processing Tools

- **MinerU 2.0 parser**: Invoked via subprocess with command-line args, generates JSON+markdown output, supports GPU acceleration and language-specific OCR. Configuration via `parse_method` ("auto", "ocr", "txt") and parser-specific kwargs.

- **Docling parser**: Alternative subprocess-based parser with similar JSON/markdown output format. System converts Docling output to internal content structure.

- **Modality processors**: Extensible processor registry (`modalprocessors.py`) with builtin handlers for images (vision model integration), tables (structured data interpretation), equations (LaTeX parsing), and custom types. Processors implement async `get_description()` method returning formatted text.

### Retrieval and Embedding Tools

- **LightRAG core**: Provides chunking (`chunk_token_size=1200`, `chunk_overlap_token_size=100`), entity extraction, graph construction, and multi-mode retrieval. Uses TiktokenTokenizer with model-specific encoding (default "gpt-4o-mini").

- **Embedding function**: Wrapped in `EmbeddingFunc` dataclass with dimension validation, token limit enforcement (`max_token_size`), and automatic unwrapping of nested instances. Default: text-embedding-3-large (3072 dims). Supports batching via `embedding_batch_num` (default 10) and concurrent execution (`embedding_func_max_async=8`).

- **Reranking models**: Optional integration with Jina (`jina-reranker-v2-base-multilingual`), Cohere (`rerank-v3.5`), or Aliyun DashScope (`gte-rerank-v2`). Implements document chunking for token limits, score aggregation (max/mean/first), and exponential backoff retry.

### Storage Abstraction

Four storage backends with pluggable implementations:

1. **KV_STORAGE**: Document content, entities, relations, chunks (JsonKVStorage, PostgreSQL, Redis, MongoDB)
2. **VECTOR_STORAGE**: Embeddings (NanoVectorDB, FAISS, Milvus, Qdrant, PostgreSQL, MongoDB)
3. **GRAPH_STORAGE**: Knowledge graph (NetworkX, Neo4J, PostgreSQL, Memgraph)
4. **DOC_STATUS_STORAGE**: Processing state tracking (JSON-based)

**No code execution layer**: RAG-Anything is a pure data processing framework. No sandbox, no CLI adapter, no shell tools. Only data transformation via LLM APIs and storage operations.

**Comparison to AGENT-33**: AGENT-33's execution layer (Phase 13) provides subprocess sandboxing, input validation (IV-01..05), progressive disclosure (L0-L3), and contract-based execution. RAG-Anything has none of this—it's designed for document ingestion and retrieval, not command execution. However, its subprocess invocation of MinerU/Docling without sandboxing is a security risk if applied to untrusted documents.

## 4) Observability and evaluation

**Minimal observability; no evaluation framework; relies on external monitoring.**

### What Exists

- **Basic logging**: Uses Python logging throughout codebase for parser subprocess output, cache hits/misses, and error conditions. No structured logging, no trace IDs, no correlation.

- **Document status tracking**: `DOC_STATUS_STORAGE` maintains processing state (PENDING, PROCESSING, DONE, FAILED) with checkpoint recovery—failed docs reset to PENDING on restart. Provides `display_stats=True` flag for `insert_content_list()` to print processing counts.

- **Token tracking**: `TokenTracker` class monitors LLM token usage across calls but no aggregation, no cost calculation, no per-query breakdown.

- **Cache metrics**: LLM response caching enabled by default with cache key logging (`handle_cache()`, `save_to_cache()`) but no hit rate reporting, no size monitoring, no eviction policies documented.

### What's Missing

- **No tracing**: No OpenTelemetry, no span propagation, no distributed trace visualization. Async operations make debugging difficult without traces.

- **No metrics**: No Prometheus/StatsD instrumentation, no latency histograms, no throughput counters, no error rates. Would need external APM to monitor production.

- **No evaluation framework**: No test queries, no ground truth datasets, no retrieval quality metrics (precision@k, recall@k, NDCG). Users must build their own eval harness.

- **No lineage tracking**: Cannot trace which source chunks contributed to a response, which entities were retrieved, or how graph traversal paths were selected. The dual-storage architecture (graph + vectors) makes provenance reconstruction non-trivial.

- **No performance baselines**: README shows qualitative examples but no quantitative benchmarks. No comparisons to vanilla RAG, no chunking ablations, no retrieval mode latency profiles.

**Comparison to AGENT-33**: Phase 16 (Observability) in AGENT-33's roadmap plans structlog with context vars, OpenTelemetry tracing, lineage tracking, and replay capabilities. RAG-Anything has none of this, making it unsuitable for production without significant instrumentation work. However, its document status tracking with checkpoint recovery is a pattern worth adopting for AGENT-33's training loop (Phase 20) to handle interrupted long-running processes.

## 5) Extensibility

**Highly extensible through processor registry, pluggable storage, and custom LLM/embedding functions.**

### Extension Points

1. **Modality processors**: `modalprocessors.py` provides `get_processor_for_type()` registry. Custom processors implement async `get_description(content_item)` method. Example: PDF annotation processor, audio transcription processor, code syntax analyzer.

2. **Storage backends**: Abstract base classes for KV/Vector/Graph/DocStatus storage allow custom implementations. Existing integrations: NetworkX, Neo4J, PostgreSQL, FAISS, Milvus, Qdrant, Redis, MongoDB. Extension pattern: inherit base class, implement async CRUD methods, register via config.

3. **Parser backends**: Currently supports MinerU and Docling via subprocess. Extension: implement `parse_document()` method returning structured content list with type/page_idx metadata. No formal parser interface documented—extension by example.

4. **LLM/embedding functions**: Accepts any callable matching signature `Callable[[str], str]` for LLM, `Callable[[List[str]], List[List[float]]]` for embedding. Wrapped in `EmbeddingFunc` dataclass for dimension validation. Easy integration with any API (OpenAI, Anthropic, local models via Ollama/LM Studio).

5. **Query modes**: Six builtin modes, but no documented way to add custom modes. Would require forking LightRAG core—not a first-class extension point.

6. **Reranking models**: Three builtin APIs (Jina, Cohere, Aliyun), extensible via `rerank.py` functions. Extension: implement `rerank_documents(query, docs, top_n)` returning scored results.

### Direct Content Insertion API

The `insert_content_list()` method bypasses document parsing, accepting pre-structured content:

```python
content_list = [
    {"type": "text", "text": "...", "page_idx": 0},
    {"type": "image", "img_path": "...", "image_caption": [...], "page_idx": 1},
    {"type": "table", "table_body": "...", "table_caption": [...], "page_idx": 2},
    {"type": "equation", "latex": "...", "text": "...", "page_idx": 3},
]
```

This enables integration with external document processing pipelines (e.g., AGENT-33's ReaderTool could generate content lists for ingestion).

### Configuration Surface

`RAGAnythingConfig` exposes 20+ parameters via Pydantic model, enabling runtime behavior changes without code modification:

- `max_concurrent_files`, `context_window`, `max_context_tokens`
- `enable_image_processing`, `enable_table_processing`, `enable_equation_processing`
- `context_mode` ("page" vs "chunk"), `context_filter_content_types`
- `parser`, `parse_method`, `supported_file_extensions`

Plus `lightrag_kwargs` passthrough for 30+ LightRAG params (chunk sizes, entity extraction loops, top-k values, token budgets).

**Comparison to AGENT-33**: AGENT-33's extension model relies on agent definitions (JSON), tool registry (governance-enforced), and workflow actions (typed classes). RAG-Anything uses processor registry and pluggable storage but lacks governance—any processor can be registered, no allowlists, no capability taxonomy. For Phase 14 (Security Hardening), AGENT-33 should NOT adopt RAG-Anything's open extension model; instead, apply allowlist-based processor registration with audit logging.

## 6) Notable practices worth adopting in AGENT-33

### High-Priority Adoptions (Address Known Gaps)

1. **Tokenizer-aware chunking with 1200-token chunks**
   **Current AGENT-33 gap**: `memory/embeddings.py` uses 500-char chunks without tokenization awareness.
   **Adoption path**: Replace `RecursiveCharacterTextSplitter` with tiktoken-based chunking. Use `chunk_token_size=1200` and `chunk_overlap_token_size=100` as defaults. Implement `TiktokenTokenizer` wrapper in `memory/embeddings.py` following LightRAG pattern.
   **Impact**: Better semantic coherence, fewer embedding truncations, improved retrieval quality.

2. **Dual-graph representation for cross-modal relationships**
   **Current AGENT-33 gap**: pgvector storage is pure vector embeddings; no graph representation of entity relationships.
   **Adoption path**: Add `GRAPH_STORAGE` abstraction to `memory/` alongside existing `LongTermMemory`. Use NetworkX for local dev, Neo4J for production. Extract entities/relations from session observations using LLM (reuse `llm/router.py`). Store bidirectional edges with weighted relevance scores.
   **Impact**: Enables graph-traversal queries ("what agents did User X work with?"), better context assembly, relationship-aware retrieval.

3. **Reranking with cross-encoder models**
   **Current AGENT-39 gap**: No reranking in `memory/rag_pipeline.py`—returns raw cosine similarity results.
   **Adoption path**: Add `rerank_model_func` to `LongTermMemory.__init__()`, integrate Jina reranker (`jina-reranker-v2-base-multilingual`) via API or local model. Apply reranking post-retrieval, filter by `min_rerank_score` threshold. Use max-aggregation for chunked documents.
   **Impact**: Significantly improves precision@k, reduces false positives in retrieved context.

4. **Checkpoint recovery for long-running processes**
   **Current AGENT-33 gap**: No resume-from-checkpoint for interrupted workflows or training loops.
   **Adoption path**: Add `DOC_STATUS_STORAGE`-like state tracking to `workflows/state_machine.py`. Store workflow execution checkpoints in PostgreSQL with status (PENDING, EXECUTING, COMPLETED, FAILED). On restart, query for in-progress workflows and resume from last completed step.
   **Impact**: Critical for Phase 20 (Continuous Improvement) where training loops may run for hours. Prevents data loss from infrastructure failures.

5. **Embedding batching for 67x speedup**
   **Current AGENT-33 gap**: `memory/embeddings.py:36` embeds documents sequentially in `for` loop.
   **Adoption path**: Batch embeddings via `embedding_batch_num` (default 10), use `embedding_func_max_async=8` for concurrent API calls. Wrap embedding function in priority-limited async executor following LightRAG's `wrap_embedding_func_with_attrs()` pattern.
   **Impact**: Dramatic performance improvement for large document ingestion (already identified in EdgeQuake dossier).

6. **VLM-enhanced retrieval for image content**
   **Current AGENT-33 gap**: No image processing in RAG pipeline—`ReaderTool` is web-only, `FileOpsTool` is UTF-8 text-only.
   **Adoption path**: Add vision model integration to `memory/rag_pipeline.py`. Extract image paths from retrieved context via regex, convert to base64, construct multimodal messages with interleaved text+images, call vision model (e.g., GPT-4V, Claude 3 Opus). Use RAG-Anything's `aquery_vlm_enhanced()` as reference implementation.
   **Impact**: Enables processing of screenshots, diagrams, charts in memory observations. Critical for browser agent workflows.

### Medium-Priority Adoptions (Architecture Improvements)

7. **Content type registry with modality-specific processors**
   Implement `get_processor_for_type()` pattern in `memory/ingestion.py` to route different content types (code, logs, JSON, CSV) to specialized processors. Each processor extracts metadata, formats for embedding, generates descriptions. Use for Phase 16 (Observability) to process trace data, metrics, structured logs.

8. **Direct content injection API for pre-parsed data**
   Add `insert_content_list()` method to `LongTermMemory` accepting structured content arrays (bypassing file I/O). Enables workflow actions to inject observations directly: `{"type": "agent_response", "agent_id": "...", "output": "...", "timestamp": ...}`. Avoids serialization round-trips.

9. **Storage abstraction layer with pluggable backends**
   Refactor `memory/long_term.py` to define `KV_STORAGE`, `VECTOR_STORAGE`, `GRAPH_STORAGE` protocols. Implement PostgreSQL backend for all three, add Redis backend for KV, add Neo4J backend for graph. Configure via `memory_storage_backend` config var. Enables production optimization (e.g., Redis cache + Milvus vectors + Neo4J graph).

10. **Query mode selection for retrieval strategy**
    Expose `mode` parameter in `search()` method: "naive" (pure vector), "local" (context-dependent), "global" (graph traversal), "hybrid" (vector+graph), "mix" (hybrid+reranking). Default to "mix" when reranker available, fallback to "hybrid". Let orchestrator or agent definitions specify preferred mode.

### Low-Priority / Don't Adopt

- **Subprocess parser invocation**: RAG-Anything's pattern of invoking MinerU/Docling via subprocess is a security risk (no sandboxing, shell injection potential). AGENT-33 already has better isolation via `CLIAdapter` in Phase 13.

- **Global async executor limits**: LightRAG uses module-level `DEFAULT_MAX_ASYNC=4` which makes tuning difficult. AGENT-33's per-subsystem concurrency limits (Redis pool, NATS subscribers) are superior.

- **JSON-based document status storage**: File-based tracking is fine for research code but doesn't scale. AGENT-33's PostgreSQL-backed state machine is better for production.

## 7) Risks / limitations to account for

### Architectural Risks

1. **No BM25 implementation despite "hybrid" claims**
   Despite marketing as "hybrid retrieval," RAG-Anything's LightRAG foundation has no BM25 code. The `/lightrag/kg/` directory contains vector DBs (FAISS, Milvus, Qdrant) and graph stores (Neo4J, NetworkX) but no keyword search implementations. "Hybrid" refers to vector+graph fusion, NOT sparse+dense retrieval. AGENT-33 must implement true BM25+vector hybrid (see web search results from Superlinked, Medium articles) rather than adopting RAG-Anything's terminology.

2. **External parser dependency creates SPOF**
   MinerU and Docling are invoked as subprocesses; if they crash or hang, the entire document pipeline blocks. No timeout enforcement, no fallback parsing strategy. Stderr monitoring detects "is not recognized" but only for missing commands, not runtime failures. AGENT-33's code executor has timeouts and contract validation; similar protections needed if adopting external parsers.

3. **Knowledge graph construction is LLM-heavy**
   Entity/relationship extraction requires multiple LLM calls per document chunk (`entity_extract_max_gleaning` loops), making ingestion slow and expensive. For a 100-page document with 1200-token chunks (~42 chunks), extraction could require 100+ LLM calls (2 per chunk: entities + relations). Cost and latency may be prohibitive for large corpora. Consider pre-computed entity extraction or rule-based fallbacks.

4. **No query rewriting or expansion**
   User queries are passed verbatim to retrieval—no synonym expansion, no typo correction, no semantic query rewriting. Research literature (see web search results) shows query rewriting significantly improves recall. RAG-Anything provides raw infrastructure but users must implement query preprocessing.

5. **Vector-graph fusion logic is opaque**
   How the "hybrid" mode merges vector similarity scores with graph traversal weights is undocumented. No score normalization algorithm, no configurable weighting (e.g., 70% vector + 30% graph), no explanation of which takes precedence when results conflict. Makes debugging poor retrieval difficult.

### Operational Risks

6. **No rate limiting or cost controls**
   Embedding batch size and LLM concurrency are configurable but no per-tenant quotas, no daily spend limits, no circuit breakers when API errors spike. A single malicious user uploading 1000 PDFs could exhaust API budgets. AGENT-33's multi-tenancy model (Phase 14) must add rate limiting at tenant level.

7. **Cache invalidation strategy missing**
   LLM response caching uses MD5 hashes of prompts as keys with no TTL, no size limits, no eviction policy. Cache can grow unbounded. Also, caching LLM responses for entity extraction may cause staleness if extraction prompts change during system upgrades. Need versioned cache keys or explicit invalidation on model/prompt updates.

8. **Embedding dimension mismatch crashes ingestion**
   `EmbeddingFunc` validates dimensions but only raises exceptions—no graceful degradation. If embedding model changes (e.g., text-embedding-3-large → text-embedding-3-small), existing vectors are incompatible and queries fail. Need migration tooling or multi-index support.

9. **No multi-tenant isolation in storage**
   Storage implementations (PostgreSQL, Neo4J, etc.) have no namespace parameter—all tenants share same tables/collections. RAG-Anything assumes single-tenant deployment. AGENT-33 must enforce `tenant_id` filtering at storage layer (already implemented for PostgreSQL via ORM models).

### Security Risks

10. **Subprocess injection via untrusted filenames**
    MinerU/Docling invocation uses `subprocess` with shell=False but file paths may not be sanitized. A filename like `"; rm -rf /;` could cause issues if parser improperly handles args. AGENT-33's Phase 13 input validation (IV-01: path validation) is stricter.

11. **Untrusted LLM output in graph construction**
    Entity/relationship extraction parses LLM JSON responses and inserts into graph without validation. A compromised LLM or prompt injection could insert malicious entities (e.g., XSS payloads in entity names, SQL injection in descriptions). Need schema validation on extracted JSON before graph insertion.

12. **No content filtering for toxic/illegal material**
    Document ingestion has no content moderation. A user uploading illegal content creates liability and may poison the knowledge graph. Consider integrating content filters (e.g., OpenAI Moderation API, Azure Content Safety) in `process_document_complete()`.

### Performance Risks

13. **Sequential embedding bottleneck confirmed**
    Despite `embedding_batch_num` config, the implementation embeds one batch at a time synchronously. True parallelism requires async embedding with semaphore-controlled concurrency (which LightRAG implements but RAG-Anything's wrapper may serialize). Verify actual async execution before assuming performance.

14. **Graph traversal scales poorly without indexing**
    NetworkX graph storage is in-memory and unoptimized. For knowledge graphs with millions of nodes, global mode queries (full graph traversal) will be prohibitively slow. Neo4J/Memgraph backends add indexing but require infrastructure. AGENT-33 should start with vector-only retrieval, add graph later when scale demands.

## 8) Feature extraction (for master matrix)

| Feature | RAG-Anything | AGENT-33 Current | Gap | Adoption Priority |
|---------|--------------|------------------|-----|-------------------|
| **Chunking** | 1200 tokens, tiktoken-aware, 100-token overlap | 500 chars, character-based, no overlap | Major | **P0** |
| **Hybrid retrieval** | Vector+graph fusion (NOT BM25+vector) | Vector-only | Major | **P1** |
| **Reranking** | Jina/Cohere/Aliyun cross-encoders | None | Major | **P0** |
| **Knowledge graph** | Dual-graph (entities+relations, vector+graph storage) | None | Major | **P1** |
| **Multimodal** | Text, images, tables, equations, charts | Text-only | Major | **P2** |
| **Query modes** | 6 modes (local/global/hybrid/naive/mix/bypass) | Single mode (vector similarity) | Medium | **P2** |
| **Embedding batching** | Configurable batch size + async concurrency | Sequential | Major | **P0** |
| **VLM integration** | Vision model for image analysis in retrieval | None | Medium | **P2** |
| **Document parsing** | MinerU/Docling subprocess (PDF/Office/images) | None (web-only via ReaderTool) | Major | **P2** |
| **Direct content injection** | `insert_content_list()` API | File-based only | Minor | **P3** |
| **Storage abstraction** | 4 layers (KV/Vector/Graph/DocStatus), 10+ backends | PostgreSQL-only | Medium | **P2** |
| **Checkpoint recovery** | Document status tracking with PENDING/DONE/FAILED | None | Medium | **P1** |
| **Entity extraction** | LLM-driven with gleaning loops | None | Medium | **P2** |
| **Cache layer** | LLM response caching with MD5 keys | None in RAG pipeline | Minor | **P3** |
| **Query rewriting** | None | None | N/A | Out of scope |
| **Observability** | Basic logging, token tracking | structlog planned (Phase 16) | AGENT-33 ahead | N/A |
| **Multi-tenancy** | None | Full tenant isolation | AGENT-33 ahead | N/A |
| **Security** | No sandboxing, no input validation | Phase 13 validation, Phase 14 hardening planned | AGENT-33 ahead | N/A |
| **Evaluation** | None | None | Shared gap | **P1** |

**Immediate action items** (P0):
1. Implement 1200-token tiktoken-aware chunking in `memory/embeddings.py`
2. Add reranking with Jina reranker to `memory/rag_pipeline.py`
3. Batch embeddings with async concurrency (67x speedup)

**Next phase** (P1):
4. Build dual-graph storage with entity/relationship extraction
5. Implement checkpoint recovery for workflow state machine
6. Add BM25 keyword search alongside vector retrieval (true hybrid, not just graph fusion)
7. Create evaluation framework for retrieval quality (precision@k, recall@k, NDCG)

**Future enhancements** (P2):
8. Integrate vision models for image analysis
9. Add MinerU/Docling for PDF/Office document parsing (with sandboxing)
10. Implement query mode selection (naive/local/global/hybrid/mix)
11. Build storage abstraction layer with pluggable backends

## 9) Evidence links

### Repository & Research

- [RAG-Anything GitHub Repository](https://github.com/HKUDS/RAG-Anything) - Main codebase, 13.2k stars, MIT license
- [RAG-Anything arXiv Paper (2510.12323)](https://arxiv.org/abs/2510.12323) - Research validation of multimodal architecture
- [LightRAG GitHub Repository](https://github.com/HKUDS/LightRAG) - Underlying framework for knowledge graph RAG

### Implementation References

- [RAG-Anything Configuration (`config.py`)](https://github.com/HKUDS/RAG-Anything/blob/main/raganything/config.py) - RAGAnythingConfig parameters
- [RAG-Anything Query Processing (`query.py`)](https://github.com/HKUDS/RAG-Anything/blob/main/raganything/query.py) - Query modes and VLM enhancement
- [LightRAG Core (`lightrag.py`)](https://github.com/HKUDS/LightRAG/blob/main/lightrag/lightrag.py) - Chunking, entity extraction, storage abstraction
- [LightRAG Reranking (`rerank.py`)](https://github.com/HKUDS/LightRAG/blob/main/lightrag/rerank.py) - Jina/Cohere/Aliyun integrations
- [LightRAG Utilities (`utils.py`)](https://github.com/HKUDS/LightRAG/blob/main/lightrag/utils.py) - Tokenization, embedding, chunk selection algorithms

### Examples & Usage

- [RAG-Anything Example Usage (`raganything_example.py`)](https://github.com/HKUDS/RAG-Anything/blob/main/examples/raganything_example.py) - Initialization and query patterns
- [Content Insertion Example (`insert_content_list_example.py`)](https://github.com/HKUDS/RAG-Anything/blob/main/examples/insert_content_list_example.py) - Direct content injection API

### Related Research (from Web Search)

- [Optimizing RAG with Hybrid Search & Reranking | VectorHub by Superlinked](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking) - Hybrid BM25+vector patterns
- [Advanced RAG Implementation using Hybrid Search and Reranking | Medium](https://medium.com/@nadikapoudel16/advanced-rag-implementation-using-hybrid-search-reranking-with-zephyr-alpha-llm-4340b55fef22) - Practical implementation guide
- [Hybrid Retrieval and Reranking in RAG | Genzeon](https://www.genzeon.com/hybrid-retrieval-deranking-in-rag-recall-precision/) - Dual-stage approach for recall+precision
- [Hybrid RAG in the Real World: Graphs, BM25, and the End of Black-Box Retrieval | NetApp](https://community.netapp.com/t5/Tech-ONTAP-Blogs/Hybrid-RAG-in-the-Real-World-Graphs-BM25-and-the-End-of-Black-Box-Retrieval/ba-p/464834) - Graph+BM25 architecture
- [Stop the Hallucinations: Hybrid Retrieval with BM25, pgvector, embedding rerank | Medium](https://medium.com/@richardhightower/stop-the-hallucinations-hybrid-retrieval-with-bm25-pgvector-embedding-rerank-895d8f7c7242) - PostgreSQL-based hybrid implementation
