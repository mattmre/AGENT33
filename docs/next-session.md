# Next Session Briefing

Last updated: 2026-02-15T01:00

## Current State
- **Branch**: `main`
- **Main**: ~973 tests passing, 0 lint errors
- **Open PRs**: 0
- **All 21 Phases**: Complete
- **Research**: 29 dossiers + 5 strategy docs complete
- **Integration Wiring**: Complete (Session 12)

## What Was Done This Session (2026-02-15, Session 12)

### Session 12: Integration Wiring (10 new tests)

Connected all previously-built subsystems into the application lifecycle (`main.py`):

| # | Subsystem | Wired To | Details |
|---|-----------|----------|---------|
| 1 | EmbeddingProvider | `app.state.embedding_provider` | Pooled httpx client using config settings (http_max_connections, http_max_keepalive) |
| 2 | EmbeddingCache | `app.state.embedding_cache` | LRU cache wrapping provider when `embedding_cache_enabled` (default True) |
| 3 | BM25Index | `app.state.bm25_index` | Starts empty, populated incrementally via ingestion pipeline |
| 4 | HybridSearcher | `app.state.hybrid_searcher` | Created when `rag_hybrid_enabled` (default True), combines BM25 + pgvector |
| 5 | RAGPipeline | `app.state.rag_pipeline` | Uses cached embedder, long-term memory, hybrid searcher, config thresholds |
| 6 | ProgressiveRecall | `app.state.progressive_recall` | 3-layer token-efficient retrieval, passed to AgentRuntime |
| 7 | SkillRegistry | `app.state.skill_registry` | Auto-discovers from `skill_definitions_dir`, starts empty if dir missing |
| 8 | SkillInjector | `app.state.skill_injector` | Wraps SkillRegistry, passed to AgentRuntime |

**Agent Runtime Integration**:
- `_register_agent_runtime_bridge()` now accepts and passes `skill_injector` and `progressive_recall` to `AgentRuntime`
- `agents.py` invoke endpoint pulls `skill_injector` and `progressive_recall` from `app.state` and passes to `AgentRuntime`
- Embedding provider closed on shutdown (cache.close() delegates to provider.close())

**Tests added** to `test_integration_wiring.py`:
- TestEmbeddingSubsystem (6 tests): provider, cache, BM25, RAG pipeline, hybrid searcher, progressive recall
- TestSkillSubsystem (3 tests): registry, injector, empty-when-no-dir
- TestAgentInvokeSubsystemPassthrough (1 test): verifies invoke route passes subsystems to AgentRuntime

### Previous Sessions (10-11): See git history

## Next Priorities

### Priority 1: Critical Architecture Gaps (from Research Sprint)

1. **Governance-Prompt Disconnect** — RESOLVED in Session 10
2. **Integration Wiring** — RESOLVED in Session 12
3. **No document processing** — can't ingest PDFs/images (Sparrow, PaddleOCR patterns)
4. **Workflow engine gaps** — no sub-workflows, http-request, merge/join (n8n-workflows)
5. **No conversational routing** — only static DAGs, no LLM-decided handoffs (Swarm)

### Priority 2: BM25 Warm-Up from Existing Memories

The BM25 index currently starts empty and relies on new ingestion to populate. For existing deployments with data in pgvector, add:
- `LongTermMemory.scan(limit, offset)` — paginated read of all stored content
- Startup warm-up loop that populates BM25 from existing records (with configurable limit)

### Priority 3: Remaining ZeroClaw Parity

| # | Item | Priority | Effort |
|---|------|----------|--------|
| 20 | Matrix channel adapter | P3 | 2 days |

## Key Files to Know
| Purpose | Path |
| --- | --- |
| Entry point | `engine/src/agent33/main.py` |
| Config | `engine/src/agent33/config.py` |
| Agent runtime | `engine/src/agent33/agents/runtime.py` |
| Agent invoke route | `engine/src/agent33/api/routes/agents.py` |
| Skill definition | `engine/src/agent33/skills/definition.py` |
| Skill registry | `engine/src/agent33/skills/registry.py` |
| Skill injector | `engine/src/agent33/skills/injection.py` |
| Provider catalog | `engine/src/agent33/llm/providers.py` |
| Tool schema | `engine/src/agent33/tools/schema.py` |
| BM25 index | `engine/src/agent33/memory/bm25.py` |
| Hybrid search | `engine/src/agent33/memory/hybrid.py` |
| Embedding cache | `engine/src/agent33/memory/cache.py` |
| RAG pipeline | `engine/src/agent33/memory/rag.py` |
| Progressive recall | `engine/src/agent33/memory/progressive_recall.py` |
| Health checks | `engine/src/agent33/api/routes/health.py` |
| Integration wiring tests | `engine/tests/test_integration_wiring.py` |
| Phase plans | `docs/phases/` |

## Test Commands
```bash
cd engine
python -m pytest tests/ -q                            # full suite (~973 tests)
python -m pytest tests/ -x -q                         # stop on first failure
python -m pytest tests/test_integration_wiring.py -x -q  # integration wiring (19 tests)
python -m pytest tests/test_skills.py -x -q           # skills tests (48 tests)
python -m pytest tests/test_channel_health.py -x -q   # channel health tests (32 tests)
python -m pytest tests/test_tool_schema.py -x -q      # tool schema tests (37 tests)
python -m pytest tests/test_provider_catalog.py -x -q # provider catalog tests (24 tests)
python -m pytest tests/test_hybrid_rag.py -x -q       # hybrid RAG tests (57 tests)
python -m ruff check src/ tests/                       # lint (0 errors)
```
