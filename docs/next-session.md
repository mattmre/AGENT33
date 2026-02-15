# Next Session Briefing

Last updated: 2026-02-15T05:30

## Current State
- **Branch**: `main` (clean working tree)
- **PR #6**: Merged (sessions 10-14 work)
- **Tests**: 973 passing, 0 lint errors
- **All 21 Phases**: Complete
- **ZeroClaw Parity**: Items 13-19 complete, #20 (Matrix) remaining
- **Integration Wiring**: Complete — all subsystems connected in main.py lifespan
- **SkillsBench Analysis**: Complete — 108KB research doc with adaptation roadmap
- **Security**: IDOR fix merged (memory observation filtering)

## What Was Done (Sessions 10-14)

**Session 10** — Hybrid RAG: BM25 engine, hybrid search (RRF), embedding cache, token-aware chunking (57 tests)
**Session 11** — ZeroClaw parity: JSON Schema tools, 22+ provider registry, skills/plugin system, channel health checks (141 tests)
**Session 12** — Integration wiring: all subsystems wired into main.py lifespan, agent runtime bridge and invoke route updated (10 tests)
**Session 13** — SkillsBench analysis: comprehensive 108KB research document comparing AGENT-33 vs SkillsBench (benchflow-ai/skillsbench), prioritized adaptation roadmap, CLAUDE.md updated
**Session 14** — PR review: fixed IDOR vulnerability in memory_search.py (Gemini Code Assist finding), merged PR #6 to main

## Next Priorities

### Priority 0: Iterative Tool-Use Loop (THE critical gap)

This is the single largest capability gap. Without it, AGENT-33 cannot complete any multi-step task. Full analysis at `docs/research/skillsbench-analysis.md`.

**Current**: `AgentRuntime.invoke()` makes a single LLM call and returns.
**Needed**: Iterative loop — LLM call → parse tool calls → execute → observe → repeat until done.

Implementation plan:
1. **New `agents/tool_loop.py`** — Core loop logic:
   - Send messages to LLM via ModelRouter
   - Parse response for tool_calls (function calling format)
   - Execute tools via ToolRegistry (with governance/allowlist checks)
   - Append tool results as observation messages
   - Repeat until: (a) LLM returns text-only (no tool calls), or (b) max iterations reached, or (c) stop condition met
   - Track iteration count, tokens used, tools invoked

2. **New `invoke_iterative()` in `agents/runtime.py`** — Wraps tool_loop with:
   - System prompt construction (existing logic)
   - Skill injection (existing SkillInjector)
   - Context from progressive recall
   - Autonomy budget enforcement integration
   - Observation capture for each step

3. **Task completion double-confirmation** — Enhancement to loop:
   - When LLM says "done", ask one more time "Are you sure the task is complete?"
   - Prevents premature exit on ambiguous responses

**Estimated effort**: 3-4 days
**Test coverage needed**: Loop termination conditions, tool execution, error handling, max iterations, budget enforcement, double-confirmation

### Priority 1: 4-Stage Hybrid Skill Matching

**Current**: BM25 + vector via RRF (2 stages in `skills/registry.py` search).
**Needed**: Add 2 LLM-based refinement stages to prevent irrelevant/leaking skills.

Stages:
1. BM25 + vector retrieval (existing) → top-K candidates
2. LLM lenient filter — keep anything potentially relevant
3. Full skill content loading for surviving candidates
4. LLM strict filter — remove skills that leak answers or are truly irrelevant

Implementation: New `skills/matching.py` using existing `HybridSearcher` + `ModelRouter`.
**Estimated effort**: 2 days

### Priority 2: Context Window Management

**Current**: No context management — messages grow unbounded until LLM context is exhausted.
**Needed**: Proactive management to prevent context overflow.

Features:
- Token counting for conversation history
- Message unwinding (remove oldest non-system messages when near limit)
- Handoff summaries (compress older context into a summary message)
- Proactive summarization trigger when tokens exceed threshold

Implementation: New `agents/context_manager.py`.
**Estimated effort**: 2 days

### Priority 3: Architecture Gaps (from Research Sprint)

1. **No document processing** — can't ingest PDFs/images
   - Add adapters to `memory/ingestion.py` for PDF extraction and image OCR
   - Dependencies: `pymupdf` or `pdfplumber` for PDF, optional `pytesseract` for images

2. **Workflow engine gaps** — no sub-workflows, http-request, merge/join actions
   - New actions in `workflows/actions/` (sub_workflow, http_request, merge)

3. **No conversational routing** — only static DAGs, no LLM-decided agent handoffs
   - Add a `route` action type that uses LLM to select next agent

### Priority 4: BM25 Warm-Up & Ingestion Pipeline

BM25 index starts empty. For deployments with existing pgvector data:
- Add `LongTermMemory.scan(limit, offset)` — paginated read of all stored content
- Add startup warm-up loop in `main.py` lifespan (with configurable limit)
- Complete the ingestion pipeline: chunk → embed → store in pgvector → add to BM25
- Add `/v1/memory/ingest` endpoint

### Priority 5: Multi-Trial Evaluation & Remaining Items

- Multi-trial evaluation methodology (5 trials, binary reward, skills impact measurement)
- Answer leakage prevention in skill injection
- Failure mode taxonomy alignment with SkillsBench
- CTRF test result format for standardized reporting
- Matrix channel adapter (ZeroClaw parity #20)

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
| Tool registry | `engine/src/agent33/tools/registry.py` |
| BM25 index | `engine/src/agent33/memory/bm25.py` |
| Hybrid search | `engine/src/agent33/memory/hybrid.py` |
| Embedding cache | `engine/src/agent33/memory/cache.py` |
| RAG pipeline | `engine/src/agent33/memory/rag.py` |
| Progressive recall | `engine/src/agent33/memory/progressive_recall.py` |
| Ingestion / chunking | `engine/src/agent33/memory/ingestion.py` |
| Health checks | `engine/src/agent33/api/routes/health.py` |
| Workflow actions | `engine/src/agent33/workflows/actions/` |
| Integration wiring tests | `engine/tests/test_integration_wiring.py` |
| **SkillsBench analysis** | `docs/research/skillsbench-analysis.md` |
| Session logs | `docs/sessions/` |
| Phase plans | `docs/phases/` |
| Research dossiers | `docs/research/repo_dossiers/` |
| Research strategy | `docs/research/adaptive-evolution-strategy.md` |

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
