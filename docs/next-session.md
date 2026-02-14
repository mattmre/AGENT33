# Next Session Briefing

Last updated: 2026-02-15T04:00

## Current State
- **Branch**: `feat/sessions-10-12-zeroclaw-parity-integration-wiring`
- **PR**: [#6](https://github.com/mattmre/AGENT33/pull/6) open (sessions 10-12 work), not yet merged
- **Tests**: 973 passing, 0 lint errors
- **All 21 Phases**: Complete
- **ZeroClaw Parity**: Items 13-19 complete, #20 (Matrix) remaining
- **Integration Wiring**: Complete — all subsystems connected in main.py lifespan
- **Research**: 29 dossiers + 5 strategy docs + SkillsBench analysis committed

## What Was Done (Sessions 10-13)

**Session 10** — Hybrid RAG: BM25 engine, hybrid search (RRF), embedding cache, token-aware chunking (57 tests)
**Session 11** — ZeroClaw parity: JSON Schema tools, 22+ provider registry, skills/plugin system, channel health checks (141 tests)
**Session 12** — Integration wiring: all subsystems wired into main.py lifespan, agent runtime bridge and invoke route updated (10 tests)
**Session 13** — SkillsBench analysis: comprehensive 108KB research document comparing AGENT-33 vs SkillsBench (benchflow-ai/skillsbench), prioritized adaptation roadmap, CLAUDE.md updated

## First Action: Merge PR #6

PR [#6](https://github.com/mattmre/AGENT33/pull/6) contains all work from sessions 10-13 (includes SkillsBench research). Merge to main before starting new work. Then switch back to `main` branch.

## Next Priorities

### Priority 0: SkillsBench Adaptation (from Session 13 Analysis)

Full analysis at `docs/research/skillsbench-analysis.md` (108KB, 2,073 lines). The 5 P0 items that directly improve AGENT-33's competitive performance:

1. **Iterative tool-use loop for AgentRuntime** (3 days)
   - Current: `AgentRuntime.invoke()` makes a single LLM call and returns
   - Needed: Iterative loop — LLM call → parse tool calls → execute → observe → repeat
   - This is the single largest capability gap. Without it, AGENT-33 cannot complete any multi-step task
   - Implementation: New `invoke_iterative()` method in `agents/runtime.py`, new `agents/tool_loop.py`

2. **4-stage hybrid skill matching** (2 days)
   - Current: BM25 + vector via RRF (2 stages)
   - Needed: Add 2 LLM-based refinement stages (lenient selection → strict quality filter)
   - Prevents irrelevant/leaking skills from being injected
   - Implementation: New `skills/matching.py` using existing `HybridSearcher` + `ModelRouter`

3. **Context window management** (2 days)
   - Current: No context management — messages grow unbounded
   - Needed: Message unwinding, handoff summaries, proactive summarization when tokens run low
   - Implementation: New `agents/context_manager.py`

4. **Task completion double-confirmation** (0.5 days)
   - Prevents premature task exit — agent must explicitly confirm it's done
   - Implementation: Enhancement to iterative tool loop

5. **Multi-trial evaluation methodology** (1 day)
   - Binary reward (0 or 1, all tests must pass) with 5 trials per configuration
   - Skills impact = pass_rate_with_skills - pass_rate_without_skills
   - Implementation: New `evaluation/multi_trial.py`, CTRF reporting format

### Priority 1: Architecture Gaps (from Research Sprint)

These are the remaining critical gaps identified across 29 research dossiers:

1. **No document processing** — can't ingest PDFs/images
   - Research: Sparrow (pipeline-based), PaddleOCR (layout analysis), RAG-Anything (multi-modal)
   - Implementation: Add adapters to `memory/ingestion.py` for PDF extraction and image OCR
   - Dependencies: `pymupdf` or `pdfplumber` for PDF, optional `pytesseract` for images

2. **Workflow engine gaps** — no sub-workflows, http-request, merge/join actions
   - Research: n8n-workflows (compositional workflow patterns)
   - Implementation: New actions in `workflows/actions/` (sub_workflow, http_request, merge)
   - Key: sub-workflow action enables recursive DAG composition

3. **No conversational routing** — only static DAGs, no LLM-decided agent handoffs
   - Research: OpenAI Swarm (handoff functions), Agent-Zero (dynamic routing)
   - Implementation: Add a `route` action type that uses LLM to select next agent
   - Key: This is AGENT-33's biggest architectural differentiator gap

### Priority 2: BM25 Warm-Up from Existing Memories

BM25 index starts empty. For deployments with existing pgvector data:
- Add `LongTermMemory.scan(limit, offset)` — paginated read of all stored content
- Add startup warm-up loop in `main.py` lifespan (with configurable limit)
- Ensure ingestion pipeline adds to BM25 when storing new documents

### Priority 3: Remaining ZeroClaw Parity

| # | Item | Priority | Effort |
|---|------|----------|--------|
| 20 | Matrix channel adapter | P3 | 2 days |

### Priority 4: Ingestion Pipeline Completeness

Currently the ingestion pipeline (`memory/ingestion.py`) provides chunking but doesn't handle the full store-and-index flow:
- Chunk text → embed → store in pgvector → add to BM25 index
- Wire `TokenAwareChunker` into a complete `IngestDocument` pipeline
- Add an `/v1/memory/ingest` endpoint

### Priority 5: SkillsBench P1 Items

After P0 is complete, these strengthen the architecture:
- Answer leakage prevention in skill injection
- Failure mode taxonomy alignment with SkillsBench enum
- LiteLLM integration (optional, for true multi-provider routing)
- CTRF test result format for standardized reporting
- Skill quality validation pipeline (12-criterion analysis from SkillsBench contrib agents)

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
