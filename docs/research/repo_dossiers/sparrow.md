# Repo Dossier: katanaml/sparrow

**Snapshot date:** 2026-02-14

**Repository:** https://github.com/katanaml/sparrow
**Stars:** 5,121 | **Forks:** 509 | **Last push:** 2026-02-13
**Homepage:** https://sparrow.katanaml.io
**Topics:** machinelearning, huggingface-transformers, nlp-machine-learning, computer-vision, gpt, llm, rag, vllm

## 1) One-paragraph summary

Sparrow is a production-grade document processing framework that extracts structured data from PDFs, images, forms, invoices, and tables using Vision Language Models (VLMs). Unlike traditional OCR-then-parse approaches, Sparrow feeds raw document images directly to VLMs (Mistral-Small-3.2-24B, Qwen2.5-VL-72B, DeepSeek-OCR) with JSON schemas, getting structured outputs with bounding box annotations. It supports multiple inference backends (MLX for Apple Silicon, Ollama, vLLM, Hugging Face Cloud GPU), processes multi-page PDFs by auto-splitting and batching, and includes specialized table detection using Microsoft's table-transformer model. The architecture is modular: `sparrow-parse` (Python library, 1.3.4) handles VLM inference, `sparrow-ml/llm` provides FastAPI APIs with usage tracking and rate limiting, `sparrow-ml/agents` orchestrates multi-step workflows via Prefect, and `sparrow-ui` offers a drag-and-drop web interface. Commercial dual licensing (GPL 3.0 + proprietary for $5M+ revenue orgs) supports both OSS and enterprise use.

## 2) Core orchestration model

Sparrow uses **three-tier orchestration**: (1) **Pipeline layer** — `sparrow-parse`, `sparrow-instructor`, `sparrow-agents` are pluggable processing modes selected via API `pipeline` parameter; (2) **Agent layer** (optional) — Prefect-based workflow DAGs in `sparrow-ml/agents/` with `Agent` base class, `AgentManager` registry, and `@flow` decorators for complex multi-step processing (medical prescriptions, trading documents); (3) **Inference layer** — Factory pattern (`InferenceFactory`) selects backend (MLX, Ollama, vLLM, HuggingFace, local GPU) and `VLLMExtractor` handles document preparation (PDF splitting, table detection, image cropping) before invoking the VLM.

**Key orchestration mechanisms:**
- **Document routing:** `_process_query()` inspects flags (`instruction`, `validation`, `markdown`, `table`, `page_type`) and routes to specialized handlers or generic extraction
- **Multi-page processing:** `PDFOptimizer.split_pdf_to_pages()` converts PDFs to 300 DPI JPEGs, processes in batch via `model_inference_instance.inference(input_data, apply_annotation, ocr_callback)`, then aggregates results
- **Table-only mode:** `TableDetector.detect_tables()` crops tables using `microsoft/table-transformer-detection`, processes each table separately, merges into `{"page_tables": [...]}`
- **Progressive enhancement:** Optional OCR callback (`process_ocr_data`) preprocesses images before VLM inference
- **State management:** FastAPI lifespan manages database connection pool (Oracle 23ai for analytics), model cache (singleton per backend+model_name), and Prefect flow tracking

**No multi-agent conversation or LLM-driven routing** — workflows are static DAGs, not dynamic orchestration.

## 3) Tooling and execution

**Core tools:**

| Tool | Purpose | Implementation |
|------|---------|----------------|
| **sparrow-parse** | VLM document extraction | Python library, PyPI package, supports MLX/Ollama/vLLM/HuggingFace backends |
| **PDFOptimizer** | PDF → images | `pypdf` for splitting, `pdf2image` (poppler wrapper) for 300 DPI conversion |
| **ImageOptimizer** | Border cropping | PIL-based `crop_image_borders(crop_size=60)` — reduces image size for forms |
| **TableDetector** | Table extraction | `transformers` + `microsoft/table-transformer-detection` → bounding boxes → crop → VLM inference per table |
| **JSONValidator** | Schema validation | `genson` for schema generation, `jsonschema` for validation, rejects invalid LLM outputs |
| **OCR service** | Fallback OCR | Standalone FastAPI service with PaddleOCR (PP-OCRv5), optional table enhancement |

**Execution model:**
- **CLI:** `sparrow.sh` wrapper around `python -m sparrow_parse` (Typer-based) — passes `query`, `file_path`, `pipeline`, `options`, `crop_size`, `debug` flags
- **API:** FastAPI endpoints in `sparrow-ml/llm/api.py` — `/api/v1/sparrow-llm/inference` accepts form data (file upload, query, options), logs to Oracle, returns JSON
- **Agents:** Prefect flows decorated with `@flow(name="agent_flow")` — medical prescriptions agent calls Sparrow API in sequence, trading agent orchestrates market data + document extraction

**Code execution layer:** None. Sparrow does not generate or execute code — it's a pure document processing pipeline. All logic is predefined Python code in the `sparrow_parse` library.

**Security:** API key validation via config file or Oracle database (`sparrow_keys` table), rate limiting via `usage_count`/`usage_limit`, IP/country logging for analytics. No sandboxing needed since there's no dynamic code execution.

## 4) Observability and evaluation

**Observability:**

| Layer | Tool | Coverage |
|-------|------|----------|
| **API logging** | Oracle 23ai Free | Logs every inference: `client_ip`, `country_name`, `sparrow_key`, `page_count`, `model_name`, `inference_type`, `source`, `duration` (via `db_pool.log_inference_start()` + `update_inference_duration()`) |
| **Dashboard** | Sparrow UI | Visualizes usage analytics, geographic distribution, model performance, success rates (requires local Oracle setup) |
| **Debug mode** | `debug=True` flag | Saves intermediate images (cropped tables, debug PDFs) to `debug_dir`, prints processing steps via `rich` console |
| **Workflow tracking** | Prefect | Agent flows visible in Prefect UI (port 4200), shows task dependencies, retries, execution history |
| **Performance timing** | `timeit` | Measures per-request latency (`start = timeit.default_timer()`), logs "Time to retrieve answer: X.X" |

**Missing observability:**
- No distributed tracing (OpenTelemetry, Jaeger)
- No structured logging (uses `rich.print()` instead of structlog)
- No metrics export (Prometheus, StatsD)
- No error aggregation (Sentry, Rollbar)
- No lineage tracking for multi-page PDF processing (which page maps to which result)

**Evaluation:**
- **Schema validation:** `JSONValidator.validate_json()` checks LLM output against expected schema, adds `"valid": "true"/"false"` field
- **Confidence scores:** Returned by VLM for text regions (when `apply_annotation=True`), but not aggregated or thresholded
- **User feedback:** None — no ground truth comparison, accuracy metrics, or active learning
- **A/B testing:** Dashboard shows per-model performance, but no automated A/B routing

## 5) Extensibility

**Backend extensibility:**
- **Factory pattern:** `InferenceFactory.get_inference_instance()` selects backend via `config["method"]` — add new backends by subclassing `ModelInference` base class
- **Model agnostic:** Supports any MLX-compatible model (Qwen, Mistral, DeepSeek), any Ollama model, any vLLM-compatible model, or Hugging Face Spaces
- **Custom models:** `local_gpu` backend supports PyTorch models, though `_load_local_model()` is not implemented (raises `NotImplementedError`)

**Pipeline extensibility:**
- **Pipeline interface:** `Pipeline` base class in `pipelines/interface.py` defines `run_pipeline()` contract — current implementations: `SparrowParsePipeline`, `SparrowInstructorPipeline`
- **Agent extensibility:** Inherit from `Agent` base class, implement `execute()` method decorated with `@flow`, register via `AgentManager.register_agent()`
- **Custom actions:** No action registry — agents directly call Sparrow API via `sparrow_client.py` wrapper

**Integration points:**
- **OCR callback:** `ocr_callback` parameter in `run_inference()` allows custom preprocessing before VLM inference
- **API middleware:** FastAPI CORS middleware configured for `allow_origins=["*"]`
- **Webhook support:** None — no event-driven triggers

**Deployment:**
- **Multiple environments:** Separate virtual envs (`.env_sparrow_parse`, `.env_instructor`, `.env_ocr`) for dependency isolation
- **Docker:** No official Dockerfile — users deploy via uvicorn directly
- **Cloud:** Hugging Face Spaces integration for cloud GPU inference

**Limitations:**
- No plugin system
- No hot-reloading of models (requires restart)
- No tool registry (unlike AGENT-33's `ToolRegistry`)
- No dynamic workflow composition (Prefect flows are static Python code)

## 6) Notable practices worth adopting in AGENT-33

### 1. Vision-first document processing architecture

**Pattern:** Feed raw document images directly to VLMs with JSON schemas, bypassing OCR→parse pipeline.

**Implementation in Sparrow:**
```python
input_data = [{
    "file_path": "invoice.pdf",
    "text_input": "extract invoice data: {\"invoice_number\": \"str\", \"total\": 0}"
}]
results, num_pages = extractor.run_inference(model_inference_instance, input_data)
```

**Why AGENT-33 needs this:**
- Current gap: `ReaderTool` only handles web URLs, `FileOpsTool` only reads UTF-8 text
- Impact: Cannot process scanned documents, images, PDFs with complex layouts
- Use case: Agent workflows that need to extract data from uploaded documents

**Adoption path:**
1. Add `sparrow-parse` as optional dependency in `pyproject.toml` (`document` extra)
2. Create `DocumentReaderTool` in `tools/builtins/document_reader.py`
3. Register in `ToolRegistry` with governance allowlist entry
4. Wire into workflow actions via new `extract_document` action

### 2. Factory pattern for multi-backend VLM support

**Pattern:** Abstract inference backend selection via factory, support local (MLX/Ollama) and cloud (HuggingFace/vLLM) with same interface.

**Sparrow implementation:**
```python
class InferenceFactory:
    def get_inference_instance(self):
        if self.config["method"] == "mlx":
            return MLXInference(model_name=self.config["model_name"])
        elif self.config["method"] == "ollama":
            return OllamaInference(model_name=self.config["model_name"])
        # ... vllm, huggingface, local_gpu
```

**Why AGENT-33 needs this:**
- Current gap: `ModelRouter` in `llm/router.py` only supports Ollama and OpenAI-compatible APIs
- Impact: Cannot leverage Apple Silicon MLX acceleration, cannot use vLLM for high-throughput
- Use case: Local dev on Mac with MLX, production on NVIDIA with vLLM

**Adoption path:**
1. Add `MLXProvider` in `llm/providers/mlx.py` (optional dependency)
2. Add `VLLMProvider` in `llm/providers/vllm.py`
3. Update `ModelRouter._get_provider()` to support new provider types
4. Add config fields: `llm_backend` (mlx/ollama/vllm/openai), `vision_model_name`

### 3. Multi-page PDF processing with page tracking

**Pattern:** Split PDFs into per-page images, process in batch, maintain page-to-result mapping.

**Sparrow implementation:**
```python
pdf_optimizer = PDFOptimizer()
num_pages, output_files, temp_dir = pdf_optimizer.split_pdf_to_pages(
    file_path="doc.pdf",
    convert_to_images=True  # 300 DPI JPEGs
)
# Process all pages in one batch
input_data[0]["file_path"] = output_files  # List of image paths
results = model_inference_instance.inference(input_data)
```

**Why AGENT-33 needs this:**
- Current gap: No PDF ingestion, no page-level tracking in memory system
- Impact: Cannot process multi-page documents, cannot answer "what's on page 5?"
- Use case: Research agent needs to cite specific pages from papers

**Adoption path:**
1. Add `pypdf` and `pdf2image` to dependencies
2. Create `PDFProcessor` in `tools/builtins/pdf_processor.py`
3. Store page metadata in `ObservationData.context`: `{"page": 3, "total_pages": 10}`
4. Update RAG chunking to preserve page boundaries

### 4. Table detection and extraction

**Pattern:** Use specialized table detection model before VLM inference for higher accuracy on tabular data.

**Sparrow implementation:**
```python
table_detector = TableDetector()
cropped_tables = table_detector.detect_tables(file_path, debug=True)
# Process each detected table separately
for table in cropped_tables:
    result = model_inference_instance.inference([{"file_path": [table]}])
```

Uses `microsoft/table-transformer-detection` (transformers + torchvision) to detect bounding boxes, crops tables, then runs VLM inference per table.

**Why AGENT-33 needs this:**
- Current gap: No structured data extraction from tables
- Impact: Cannot parse financial reports, research papers with data tables
- Use case: QA agent needs to extract metrics from benchmark tables

**Adoption path:**
1. Add `transformers` and `torchvision` as optional dependencies
2. Create `TableExtractorTool` with table detection + VLM pipeline
3. Integrate with document processing workflow
4. Cache table-transformer model (780MB) on first use

### 5. Schema-driven extraction with validation

**Pattern:** Accept JSON schema as query, validate LLM output against schema, reject invalid responses.

**Sparrow implementation:**
```python
query = '[{"instrument_name":"str", "valuation":0}]'
# VLM prompt includes: "retrieve {schema}. return response in JSON format"
# Post-processing validates against schema
validator = JSONValidator()
is_valid = validator.validate_json(schema, llm_output)
```

**Why AGENT-33 needs this:**
- Current gap: No structured output validation in agent runtime
- Impact: Agents can produce malformed JSON that breaks downstream workflows
- Use case: Workflow expects specific data shape, needs to fail fast on invalid output

**Adoption path:**
1. Add `genson` and `jsonschema` to dependencies
2. Create `StructuredOutputValidator` in `agents/validators.py`
3. Add `output_schema` field to `AgentDefinition`
4. Validate agent responses in `runtime.py` before returning

### 6. Progressive image optimization

**Pattern:** Optionally crop image borders, resize while preserving aspect ratio, scale bounding boxes back to original dimensions.

**Sparrow implementation:**
```python
image_optimizer = ImageOptimizer()
cropped_path = image_optimizer.crop_image_borders(
    file_path, temp_dir, crop_size=60  # Remove 60px borders
)
# VLM processes cropped image (faster, less memory)
# Bounding boxes scaled back: bbox_orig = bbox_resized * (orig_size / resized_size)
```

**Why AGENT-33 needs this:**
- Current gap: No image preprocessing for memory efficiency
- Impact: Large images consume excessive GPU memory
- Use case: Processing scanned documents with wide margins

**Adoption path:**
1. Add to `DocumentReaderTool` as `crop_borders` parameter
2. Implement in `tools/builtins/image_utils.py`
3. Add config: `vision_max_image_size` (default 1250x1750)

### 7. Model caching for multi-request performance

**Pattern:** Cache loaded VLM models in dictionary keyed by `{backend}_{model_name}`, reuse across requests.

**Sparrow implementation:**
```python
# api.py lifespan
model_cache = {}

# In subprocess_inference()
cache_key = f"{config['method']}_{config['model_name']}"
if cache_key in model_cache:
    model_inference_instance = model_cache[cache_key]
else:
    model_inference_instance = factory.get_inference_instance()
    model_cache[cache_key] = model_inference_instance
```

**Why AGENT-33 needs this:**
- Current gap: No model caching in `ModelRouter`
- Impact: Model reloading on every request adds 5-10s latency
- Use case: High-throughput agent deployments

**Adoption path:**
1. Add `_model_cache: Dict[str, Any]` to `ModelRouter`
2. Cache in `_get_provider()` using `{provider_type}_{model_name}` key
3. Add cache eviction on config change

### 8. Usage tracking and rate limiting

**Pattern:** Log API usage to database with key-based rate limits, track IP/country/model for analytics.

**Sparrow implementation:**
```python
def validate_key_from_config(config, sparrow_key):
    usage_count = data.get('usage_count', 0)
    usage_limit = data.get('usage_limit', float('inf'))
    if usage_count >= usage_limit:
        raise HTTPException(status_code=403, detail="Usage limit exceeded")
    config.update_key_usage(key_name, usage_count + 1)
```

**Why AGENT-33 needs this:**
- Current gap: API keys in `security/` have no usage tracking
- Impact: Cannot enforce quotas, no usage analytics
- Use case: Multi-tenant deployments need per-tenant limits

**Adoption path:**
1. Add `usage_count`, `usage_limit` columns to `api_keys` table
2. Increment count in `AuthMiddleware.dispatch()`
3. Add `/v1/auth/usage` endpoint for analytics
4. Create Alembic migration

## 7) Risks / limitations to account for

### 1. VLM accuracy and hallucination risk

**Risk:** Vision LLMs can hallucinate structured data not present in documents.

**Evidence:** No ground truth validation in Sparrow — `JSONValidator` only checks schema compliance, not factual accuracy.

**Mitigation for AGENT-33:**
- Add confidence thresholds for document extraction
- Require human-in-the-loop for high-stakes data (invoices, contracts)
- Log extracted data + source images for audit trails
- Add accuracy evaluation against labeled dataset

### 2. No multi-backend fallback

**Risk:** If MLX backend fails (e.g., insufficient memory), no automatic fallback to Ollama/cloud.

**Evidence:** `InferenceFactory` selects backend based on config, single failure → entire request fails.

**Mitigation for AGENT-33:**
- Implement provider fallback chain in `ModelRouter`: `[mlx, ollama, openai]`
- Add retry logic with exponential backoff
- Cache provider health status

### 3. Memory consumption with large PDFs

**Risk:** 100-page PDF at 300 DPI = 100 JPEGs in memory, can OOM.

**Evidence:** `_process_pages()` loads all pages into `output_files` list, processes in batch.

**Mitigation for AGENT-33:**
- Stream processing: process pages in chunks (10 at a time)
- Add `max_pdf_pages` config (default 50)
- Reject oversized uploads at API boundary

### 4. Table detection model size and latency

**Risk:** `microsoft/table-transformer-detection` is 780MB, adds 200-500ms per page.

**Evidence:** `TableDetector.load_table_detection_model()` downloads on first use, no async loading.

**Mitigation for AGENT-33:**
- Make table detection optional (flag in `DocumentReaderTool`)
- Pre-download model during Docker build
- Add model warmup in lifespan startup

### 5. No streaming inference

**Risk:** Large documents have 30-60s latency, no progress feedback.

**Evidence:** `model_inference_instance.inference()` blocks until complete, FastAPI endpoint returns only after full processing.

**Mitigation for AGENT-33:**
- Use SSE (Server-Sent Events) for progress updates
- Add background task queue (Celery/NATS) for long-running extractions
- Return job ID immediately, poll for results

### 6. Schema inflexibility

**Risk:** JSON schema must be known upfront, cannot adapt to unknown document types.

**Evidence:** Query format is `[{"field": "type"}]` — requires manual schema definition per document type.

**Mitigation for AGENT-33:**
- Add schema inference mode: VLM proposes schema, user approves
- Build schema library for common document types (invoices, receipts, forms)
- Use generic extraction mode (`query="*"`) for exploration

### 7. Bounding box coordinate drift

**Risk:** Image resizing can cause bounding box coordinates to misalign.

**Evidence:** `scale_bbox_coordinates()` scales boxes back, but floating-point errors accumulate with multiple transforms (crop → resize → scale).

**Mitigation for AGENT-33:**
- Preserve original dimensions in metadata
- Use integer coordinates only
- Add coordinate validation (bbox within image bounds)

### 8. No incremental processing

**Risk:** Re-processing entire PDF on retry wastes compute.

**Evidence:** No checkpointing — if page 47 fails, restart from page 1.

**Mitigation for AGENT-33:**
- Add page-level checkpointing in workflow state
- Store partial results in Redis
- Resume from last successful page

## 8) Feature extraction (for master matrix)

### Document Processing

| Feature | Sparrow | AGENT-33 Current | Gap |
|---------|---------|------------------|-----|
| **PDF ingestion** | ✅ Multi-page, 300 DPI conversion | ❌ None | **Critical** — add `pypdf` + `pdf2image` |
| **Image ingestion** | ✅ PNG, JPG, JPEG | ❌ None | **Critical** — add PIL support |
| **Table detection** | ✅ `microsoft/table-transformer-detection` | ❌ None | **High** — specialized model for tables |
| **OCR fallback** | ✅ PaddleOCR (PP-OCRv5) | ❌ None | **Medium** — optional enhancement |
| **Bounding boxes** | ✅ With coordinate scaling | ❌ None | **Low** — nice-to-have for UI |
| **Multi-page tracking** | ✅ Page-level results | ❌ None | **High** — needed for citations |

### VLM Integration

| Feature | Sparrow | AGENT-33 Current | Gap |
|---------|---------|------------------|-----|
| **Vision LLM support** | ✅ MLX, Ollama, vLLM, HF | ❌ Text-only LLMs | **Critical** — add vision models |
| **MLX backend** | ✅ Apple Silicon optimized | ❌ None | **High** — 3-5x faster on M-series |
| **vLLM backend** | ✅ High-throughput serving | ❌ None | **Medium** — for production scale |
| **Model caching** | ✅ Per-backend+model | ❌ None | **Medium** — 5-10s latency reduction |
| **Schema-driven extraction** | ✅ JSON schema validation | ❌ None | **High** — structured outputs |

### Infrastructure

| Feature | Sparrow | AGENT-33 Current | Gap |
|---------|---------|------------------|-----|
| **Usage tracking** | ✅ Oracle 23ai, per-request logs | ❌ None | **Low** — use existing observability |
| **Rate limiting** | ✅ Key-based quotas | ✅ In AuthMiddleware | None |
| **Dashboard** | ✅ Oracle-based analytics | ❌ None | **Low** — use Grafana instead |
| **Model warmup** | ❌ Manual | ❌ None | **Medium** — add to lifespan |
| **Graceful degradation** | ❌ Single backend fails → fail | ✅ Partial (provider selection) | **Medium** — add fallback chain |

### Workflow Orchestration

| Feature | Sparrow | AGENT-33 Current | Gap |
|---------|---------|------------------|-----|
| **Agent DAGs** | ✅ Prefect flows | ✅ Custom DAG engine | None — different paradigms |
| **Dynamic routing** | ❌ Static flows | ❌ Static DAGs | **High** — both need LLM routing |
| **Multi-step document processing** | ✅ Agent workflows | ❌ Single-shot extraction | **Medium** — add classify→extract→validate |

### Key Sparrow Advantages

1. **Production-ready document processing** — 300 DPI conversion, table detection, schema validation
2. **Multi-backend flexibility** — MLX for Mac, vLLM for cloud, Ollama for dev
3. **Real-world usage** — Live demo at sparrow.katanaml.io, 5K+ stars, dual licensing model
4. **Specialized models** — Table transformer, OCR fallback, vision LLMs

### Key AGENT-33 Advantages

1. **True multi-agent orchestration** — Agent registry, capability taxonomy, team coordination
2. **Governance layer** — Permissions, allowlists, prompt injection detection
3. **Self-evolving training** — Rollout capture, evaluation, optimization (Sparrow has none)
4. **Memory system** — Embeddings, RAG, session state (Sparrow is stateless)
5. **Observability** — Structlog, tracing, lineage (Sparrow has basic logging)

## 9) Evidence links

### Primary Sources

1. **Main README:** `/tmp/sparrow-repo/README.MD` — Architecture, features, quickstart, performance tips
2. **Parse library README:** `sparrow-data/parse/README.md` — API reference, backend configuration, use cases
3. **Changelog:** `CHANGELOG.md` — Version history (v0.1.3 → v0.4.4), feature timeline
4. **Environment setup:** `environment_setup.md` — Pyenv, virtual envs, dependency installation

### Core Implementation Files

5. **VLM extractor:** `sparrow-data/parse/sparrow_parse/extractors/vllm_extractor.py:1-300` — Inference pipeline, PDF processing, table extraction
6. **Inference factory:** `sparrow-data/parse/sparrow_parse/vlmb/inference_factory.py` — Backend selection (MLX/Ollama/vLLM/HuggingFace)
7. **MLX backend:** `sparrow-data/parse/sparrow_parse/vlmb/mlx_inference.py:1-200` — Apple Silicon-optimized inference, image resizing, bbox scaling
8. **PDF optimizer:** `sparrow-data/parse/sparrow_parse/helpers/pdf_optimizer.py:1-80` — Page splitting, 300 DPI conversion
9. **Image optimizer:** `sparrow-data/parse/sparrow_parse/helpers/image_optimizer.py` — Border cropping
10. **Table detector:** `sparrow-data/parse/sparrow_parse/processors/table_structure_processor.py:1-200` — microsoft/table-transformer-detection integration

### API and Orchestration

11. **FastAPI server:** `sparrow-ml/llm/api.py:1-250` — Inference endpoint, usage validation, model caching, duration tracking
12. **Engine:** `sparrow-ml/llm/engine.py:1-150` — Pipeline selection, markdown/table processing
13. **Pipeline implementation:** `sparrow-ml/llm/pipelines/sparrow_parse/sparrow_parse.py:1-200` — Query processing, validation, LLM output handling
14. **Agent base:** `sparrow-ml/agents/base.py` — Prefect-based agent abstraction, AgentManager
15. **OCR service:** `sparrow-data/ocr/routers/ocr.py` — PaddleOCR integration, table enhancement

### Dependencies and Configuration

16. **Sparrow Parse requirements:** `sparrow-ml/llm/requirements_sparrow_parse.txt` — sparrow-parse[mlx]==1.3.4, genson, jsonschema
17. **Parse library requirements:** `sparrow-data/parse/requirements.txt` — pypdf, pdf2image, sentence-transformers, ollama

### Live Demo and Documentation

18. **Live demo:** https://sparrow.katanaml.io — Running on Mac Mini M4 Pro, drag-and-drop interface
19. **GitHub repo:** https://github.com/katanaml/sparrow — 5,121 stars, last push 2026-02-13
20. **PyPI package:** https://pypi.org/project/sparrow-parse/ — Version 1.3.4, install instructions

### Architecture Diagrams

21. **Architecture diagram:** Referenced in README as `sparrow-ui/assets/sparrow_architecture.jpeg` — Shows component interaction
22. **UI screenshots:** `sparrow-ui/assets/sparrow_ui.png`, `sparrow_ui_3.png` — Dashboard and extraction interface

### Commercial Model

23. **Dual licensing:** README + `sparrow-ui/README.md` — GPL 3.0 for <$5M revenue, proprietary for enterprises
24. **Author contact:** abaranovskis@redsamuraiconsulting.com — Commercial licensing, consulting, support

---

**Research methodology:** Cloned full repository, analyzed 20+ source files including core pipeline (`vllm_extractor.py`), all backends (MLX/Ollama/vLLM/HuggingFace), FastAPI server, Prefect agents, OCR service, and documentation. Cross-referenced README examples with actual implementation code to verify capabilities.
