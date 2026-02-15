# Next Session Briefing

Last updated: 2026-02-15T12:00

## Current State
- **Branch**: `main` (clean working tree)
- **Open PRs**: #7 (P0), #8 (P1), #9 (P2), #10 (P5), #11 (P3), #12 (P4)
- **Tests**: ~1,030+ passing (across feature branches), 0 lint errors
- **All 21 Phases**: Complete
- **Session 15**: P0-P5 implemented (6 PRs pending review)
- **ZeroClaw Parity**: Items 13-19 complete, #20 (Matrix) remaining
- **AWM Analysis**: Complete — `docs/research/agent-world-model-analysis.md`
- **SkillsBench Analysis**: Complete — `docs/research/skillsbench-analysis.md`

## What Was Done (Session 15)

**P0: Iterative Tool-Use Loop** (PR #7 — `feat/p0-iterative-tool-loop`)
- `agents/tool_loop.py` — Core iterative loop (ToolLoopConfig, ToolLoopState, ToolLoop)
- `agents/runtime.py` — `IterativeAgentResult`, `invoke_iterative()` method
- `api/routes/agents.py` — `POST /{name}/invoke-iterative` endpoint
- `main.py` — LLM provider registration on model_router, ToolRegistry + ToolGovernance init
- 64 new tests (40 tool_loop + 24 invoke_iterative)

**P1: 4-Stage Hybrid Skill Matching** (PR #8 — `feat/p1-4stage-skill-matching`)
- `skills/matching.py` — SkillMatcher with BM25 retrieval → LLM lenient → content load → LLM strict
- Answer leakage detection in strict filter
- 51 new tests

**P2: Context Window Management** (PR #9 — `feat/p2-context-window-management`)
- `agents/context_manager.py` — ContextBudget, ContextSnapshot, ContextManager
- Token estimation, message unwinding, LLM handoff summaries, proactive management
- MODEL_CONTEXT_LIMITS lookup table (15+ models)
- 38 new tests

**P3: Architecture Gaps** (PR #11 — `feat/p3-architecture-gaps`)
- `memory/ingestion.py` — DocumentExtractor (PDF via pymupdf/pdfplumber, image OCR via pytesseract)
- `workflows/actions/http_request.py` — HTTP request action (httpx)
- `workflows/actions/sub_workflow.py` — Nested workflow execution
- `workflows/actions/route.py` — LLM-based conversational routing
- 3 new StepAction enum values, executor dispatch integration
- 40 new tests

**P4: BM25 Warm-Up & Ingestion Pipeline** (PR #12 — `feat/p4-bm25-warmup-ingestion`)
- `memory/long_term.py` — scan(limit, offset), count()
- `memory/warmup.py` — warm_up_bm25() for startup population
- `config.py` — bm25_warmup_enabled, bm25_warmup_max_records, bm25_warmup_page_size
- `main.py` — Warm-up in lifespan after BM25 index creation
- `api/routes/memory_search.py` — POST /v1/memory/ingest (chunk → embed → pgvector → BM25)
- 21 new tests

**P5: Agent World Model Analysis** (PR #10 — `feat/p5-awm-analysis`)
- `docs/research/agent-world-model-analysis.md` — 23-section comprehensive analysis (685 lines)
- Covers: repo structure, 5-stage pipeline, benchmark results, security analysis, feature comparison
- 10-item adaptation roadmap (3 tiers), philosophical framework for evolutionary absorption

## Next Priorities

### Priority 0: Merge Session 15 PRs
Review and merge PRs #7-#12. Resolve any merge conflicts between branches (they all branch from the same main commit, so conflicts should be minimal — mostly in main.py and config.py).

### Priority 1: Multi-Trial Evaluation & CTRF Reporting
- Multi-trial evaluation methodology (5 trials, binary reward, skills impact measurement)
- CTRF test result format for standardized reporting
- Aligns with both SkillsBench and AWM evaluation paradigms

### Priority 2: Integration Testing
- End-to-end test of iterative tool loop with real tool execution
- Test ingestion pipeline → BM25 warm-up → hybrid search flow
- Test context manager integration with tool loop

### Priority 3: AWM Adaptation (Tier 1 items)
From `docs/research/agent-world-model-analysis.md` adaptation roadmap:
- A1: MCP interface interop bridge for Tool Registry
- A2: Database-backed verification in evaluation gates
- A3: Multi-turn evaluation scenarios for golden tasks
- A4: Optional tiktoken integration for exact token counting

### Priority 4: Remaining Items
- Matrix channel adapter (ZeroClaw parity #20)
- Answer leakage prevention in skill injection (already in P1 strict filter, may need runtime integration)
- Failure mode taxonomy alignment with SkillsBench
- BM25 warm-up from existing deployments (startup warm-up in P4, needs integration testing)

## Key Files to Know

| Purpose | Path |
| --- | --- |
| Entry point | `engine/src/agent33/main.py` |
| Config | `engine/src/agent33/config.py` |
| Agent runtime | `engine/src/agent33/agents/runtime.py` |
| **Tool loop (NEW)** | `engine/src/agent33/agents/tool_loop.py` |
| **Context manager (NEW)** | `engine/src/agent33/agents/context_manager.py` |
| **Skill matcher (NEW)** | `engine/src/agent33/skills/matching.py` |
| **BM25 warm-up (NEW)** | `engine/src/agent33/memory/warmup.py` |
| Agent invoke route | `engine/src/agent33/api/routes/agents.py` |
| Memory/ingest route | `engine/src/agent33/api/routes/memory_search.py` |
| Skill definition | `engine/src/agent33/skills/definition.py` |
| Skill registry | `engine/src/agent33/skills/registry.py` |
| Skill injector | `engine/src/agent33/skills/injection.py` |
| Provider catalog | `engine/src/agent33/llm/providers.py` |
| Tool schema | `engine/src/agent33/tools/schema.py` |
| Tool registry | `engine/src/agent33/tools/registry.py` |
| BM25 index | `engine/src/agent33/memory/bm25.py` |
| Hybrid search | `engine/src/agent33/memory/hybrid.py` |
| Embedding cache | `engine/src/agent33/memory/cache.py` |
| RAG pipeline | `engine/src/agent33/memory/rag.py` |
| Progressive recall | `engine/src/agent33/memory/progressive_recall.py` |
| Ingestion / chunking | `engine/src/agent33/memory/ingestion.py` |
| **HTTP request action (NEW)** | `engine/src/agent33/workflows/actions/http_request.py` |
| **Sub-workflow action (NEW)** | `engine/src/agent33/workflows/actions/sub_workflow.py` |
| **Route action (NEW)** | `engine/src/agent33/workflows/actions/route.py` |
| Workflow executor | `engine/src/agent33/workflows/executor.py` |
| **AWM analysis** | `docs/research/agent-world-model-analysis.md` |
| **SkillsBench analysis** | `docs/research/skillsbench-analysis.md` |
| Session logs | `docs/sessions/` |

## Test Commands
```bash
cd engine
python -m pytest tests/ -q                                # full suite (~1030+ tests)
python -m pytest tests/ -x -q                             # stop on first failure
python -m pytest tests/test_tool_loop.py -x -q            # tool loop (40 tests)
python -m pytest tests/test_invoke_iterative.py -x -q     # invoke iterative (24 tests)
python -m pytest tests/test_skill_matching.py -x -q       # skill matching (51 tests)
python -m pytest tests/test_context_manager.py -x -q      # context manager (38 tests)
python -m pytest tests/test_architecture_gaps.py -x -q    # architecture gaps (40 tests)
python -m pytest tests/test_bm25_warmup_ingestion.py -x -q # BM25 warmup (21 tests)
python -m pytest tests/test_integration_wiring.py -x -q   # integration wiring (19 tests)
python -m ruff check src/ tests/                           # lint (0 errors)
```
