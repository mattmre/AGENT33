---
title: "Session 17: Integration Testing Gap Analysis"
date: 2026-02-15
session: 17
type: research
status: complete
---

# Session 17: Integration Testing Gap Analysis

## Overview

This document analyzes the integration testing gaps in AGENT-33's engine, identifying cross-subsystem integration points, critical flows that lack end-to-end test coverage, and concrete test scenarios to close those gaps. The analysis covers all 9 major subsystems wired together in `main.py`'s lifespan initialization.

## Cross-Subsystem Integration Points

29 integration points were identified across 9 subsystems. The initialization order in `main.py` establishes the dependency graph:

```
PostgreSQL → Redis → NATS → AgentRegistry → CodeExecutor → ModelRouter
→ ToolRegistry → EmbeddingProvider(+Cache) → BM25(+warmup)
→ HybridSearcher → RAGPipeline → ProgressiveRecall
→ SkillRegistry(+Injector) → Agent-Workflow Bridge
```

### Subsystem Integration Map

| Subsystem | Depends On | Depended On By |
|-----------|-----------|----------------|
| EmbeddingProvider | Config | EmbeddingCache, HybridSearcher |
| EmbeddingCache | EmbeddingProvider | HybridSearcher, RAGPipeline |
| BM25Index | LongTermMemory (warmup) | HybridSearcher |
| HybridSearcher | BM25Index, EmbeddingCache | RAGPipeline |
| RAGPipeline | HybridSearcher | ProgressiveRecall |
| ProgressiveRecall | RAGPipeline | AgentRuntime |
| SkillRegistry | Config, filesystem | SkillInjector |
| SkillInjector | SkillRegistry | AgentRuntime |
| AgentRuntime | ModelRouter, SkillInjector, ProgressiveRecall | API routes, Workflow bridge |

### Key Integration Boundaries

- **Memory pipeline**: Ingestion (chunking + embedding) feeds BM25Index and LongTermMemory, which feed HybridSearcher, which feeds RAGPipeline, which feeds ProgressiveRecall
- **Skill pipeline**: SkillRegistry discovers SKILL.md files, SkillInjector resolves context at L0/L1/L2, AgentRuntime receives injected skill context in prompts
- **Agent pipeline**: AgentRegistry loads definitions, AgentRuntime constructs prompts with skill injection + memory recall, invokes LLM via ModelRouter
- **Tool pipeline**: ToolRegistry validates schemas, ToolLoop parses LLM output for tool calls, executes via validated_execute, feeds results back

## 7 Critical Integration Flows

### Flow 1: Ingestion -> BM25 Warmup -> Hybrid Search -> RAG (Core Memory Pipeline)

```
Document → TokenAwareChunker.chunk()
  → EmbeddingProvider.embed() (cached via EmbeddingCache)
  → LongTermMemory.store()
  → BM25Index.add_documents()
  → HybridSearcher.search() [BM25 + vector via RRF]
  → RAGPipeline.retrieve()
  → ProgressiveRecall.recall()
```

**Status**: Each component tested in isolation. Zero tests for the full chain. The ingestion endpoint stores chunks, but no test verifies those chunks are retrievable via hybrid search.

### Flow 2: Ingestion -> BM25 Warmup (Startup) -> Search

```
Startup:
  LongTermMemory.scan() → paginated rows
  → BM25Index.add_documents(batch)
  → warm_up_bm25() completes

Runtime:
  BM25Index.search(query) → ranked results
```

**Status**: `warm_up_bm25()` tested with mocked LTM. No test verifies that documents ingested before startup are searchable after warmup.

### Flow 3: Agent Invoke with Skill Injection + Memory Recall

```
POST /v1/agents/{name}/invoke
  → AgentRuntime.invoke()
    → SkillInjector.inject(task_description, level)
    → ProgressiveRecall.recall(query, tenant_id)
    → prompt construction with skill context + memory context
    → ModelRouter.generate()
```

**Status**: AgentRuntime tested with mocked injector and recall. The invoke route pulls subsystems from `app.state` but no test verifies the full chain with real SkillRegistry content and real memory retrieval.

### Flow 4: Agent Iterative Tool Loop with Governance + Autonomy

```
POST /v1/agents/{name}/invoke-iterative
  → AgentRuntime.invoke_iterative()
    → ToolLoop.run()
      → parse LLM output for tool calls
      → governance check (allowlist)
      → validated_execute() (schema validation)
      → feed result back to LLM
      → repeat until max_iterations or final answer
```

**Status**: ToolLoop tested with mock tools and mock LLM. No test exercises real tool execution with governance enforcement.

### Flow 5: 4-Stage Skill Matching -> Skill Injection -> Agent Invoke

```
SkillMatcher.match(task_description)
  → Stage 1: BM25 retrieval (top-k candidates)
  → Stage 2: LLM lenient filter
  → Stage 3: Content load (full SKILL.md)
  → Stage 4: LLM strict filter (with leakage detection)
  → matched skills

SkillInjector.inject(task_description, level)
  → resolve_tool_context() for L2
  → formatted skill context string

AgentRuntime.invoke(message, skill_context=...)
```

**Status**: SkillMatcher tested independently. SkillInjector tested independently. No test verifies the full matching-to-injection-to-invocation chain.

### Flow 6: Context Window Management during Iterative Tool Loop

```
ToolLoop.run()
  → iteration N
    → ContextManager.manage(messages)
      → estimate token count
      → if over budget: unwind old messages / summarize
    → LLM call with managed context
  → iteration N+1
```

**Status**: **NOT YET WIRED** -- this is both a test gap AND an implementation gap. ContextManager exists and is fully tested in isolation. ToolLoop exists and is fully tested. But ToolLoop has no integration point for ContextManager. Long-running tool loops will eventually exceed context windows with no mitigation.

### Flow 7: API Endpoint -> Full Pipeline E2E

```
POST /v1/memory/ingest (document)
  → chunking, embedding, storage, BM25 indexing

POST /v1/memory/search (query)
  → hybrid search → results

Verify: ingested content appears in search results
```

**Status**: Each endpoint tested independently with mocks. No test calls ingest followed by search to verify the roundtrip.

## Coverage Gaps

| Gap | Severity | Type |
|-----|----------|------|
| Zero cross-subsystem flow tests | HIGH | Test gap |
| Ingestion -> retrieval chain untested | HIGH | Test gap |
| ContextManager not wired into ToolLoop | HIGH | Implementation gap + Test gap |
| SkillMatcher -> SkillInjector chain untested | MEDIUM | Test gap |
| Agent bridge with real subsystems untested | MEDIUM | Test gap |
| resolve_tool_context() never called from invoke endpoints | MEDIUM | Implementation gap |
| BM25 warmup -> search functional verification | MEDIUM | Test gap |
| Multi-trial evaluation chain untested | LOW | Test gap (not yet implemented) |

## 10 Test Scenarios Defined

### Scenario 1: Full Ingestion-to-Retrieval Pipeline

**Description**: Ingest a document via TokenAwareChunker, store in LTM and BM25, then retrieve via HybridSearcher.

**Components exercised**: TokenAwareChunker, EmbeddingProvider (mocked with deterministic vectors), EmbeddingCache, LongTermMemory (in-memory fake), BM25Index (real), HybridSearcher (real `_fuse()`).

**Assertions**: Retrieved results contain the ingested content. BM25 scores and vector scores are both non-zero. RRF fusion produces correct ranking.

### Scenario 2: BM25 Warmup -> Keyword Search Functional

**Description**: Pre-populate in-memory LTM with documents, run `warm_up_bm25()`, then verify keyword search returns expected results.

**Components exercised**: LongTermMemory.scan() (fake), warm_up_bm25(), BM25Index.search().

**Assertions**: After warmup, BM25 search returns documents matching query terms. Documents not matching return empty.

### Scenario 3: Agent Invoke with Real Skill Injection

**Description**: Register skills in SkillRegistry, invoke agent with skill injection enabled, verify skill context appears in the prompt sent to LLM.

**Components exercised**: SkillRegistry, SkillInjector (L0/L1/L2), AgentRuntime.invoke().

**Assertions**: LLM receives prompt containing skill descriptions. Correct skills are injected based on task description matching.

### Scenario 4: Agent Invoke with Real Memory Recall

**Description**: Populate memory, invoke agent with progressive recall enabled, verify memory context appears in prompt.

**Components exercised**: ProgressiveRecall, RAGPipeline, HybridSearcher, AgentRuntime.invoke().

**Assertions**: LLM receives prompt containing relevant memory fragments. Memory recall respects tenant isolation.

### Scenario 5: Iterative Tool Loop with Real Tool Execution

**Description**: Register a real tool (e.g., a simple calculator), run ToolLoop with a task requiring tool use, verify correct tool invocation and result feeding.

**Components exercised**: ToolLoop, ToolRegistry, validated_execute(), governance checks.

**Assertions**: Tool is called with correct arguments. Tool result is fed back to LLM. Final answer incorporates tool output.

### Scenario 6: Skill Matching -> Injection Pipeline

**Description**: Load skills into SkillRegistry, run SkillMatcher.match() with a task description, pass results to SkillInjector, verify formatted output.

**Components exercised**: SkillMatcher (stages 1-4, with mocked LLM for stages 2+4), SkillInjector.inject().

**Assertions**: Correct skills are matched. Answer leakage detection works. Injected context is properly formatted at each disclosure level.

### Scenario 7: Ingestion -> BM25 + Hybrid Search Consistency

**Description**: Ingest the same document, search via BM25-only and hybrid, verify both return the document and hybrid score >= BM25 score.

**Components exercised**: Ingestion pipeline, BM25Index, HybridSearcher.

**Assertions**: Both search paths return the document. Hybrid search score reflects both BM25 and vector contributions.

### Scenario 8: Context Manager Integration with Long Conversation

**Description**: Build a message list that exceeds context budget, run ContextManager.manage(), verify messages are unwound/summarized within budget.

**Components exercised**: ContextManager, token estimation, message unwinding.

**Assertions**: Output message count <= input. Total tokens within budget. System message preserved. Most recent messages preserved.

### Scenario 9: Ingest Endpoint -> Memory Search Endpoint Roundtrip

**Description**: Call POST /v1/memory/ingest with a document, then call POST /v1/memory/search with a matching query, verify the document is returned.

**Components exercised**: Full API stack including auth middleware, ingestion pipeline, search pipeline.

**Assertions**: Search results include the ingested document. Response schema matches expected format.

### Scenario 10: ContextManager NOT Wired into ToolLoop (Regression Detection)

**Description**: Verify that ToolLoop currently does NOT manage context window size. This is a regression-detection test that should FAIL once the implementation gap is closed.

**Components exercised**: ToolLoop constructor signature, ToolLoop.run() behavior.

**Assertions**: ToolLoop has no `context_manager` parameter. Running a long tool loop does not trigger any context management. (This test becomes an integration test once the gap is fixed.)

## Mock Boundaries

### Must Be Real (actual implementations, not mocks)

These components must use their real implementations in integration tests because their internal logic IS the integration behavior being tested:

- **BM25Index**: Tokenization, term frequency, scoring -- these are the behaviors we need to verify work end-to-end
- **TokenAwareChunker**: Chunking boundaries affect retrieval quality
- **EmbeddingCache**: LRU eviction, cache hit/miss behavior
- **HybridSearcher._fuse()**: RRF fusion logic combining BM25 and vector scores
- **SkillRegistry**: Discovery, CRUD, search -- real filesystem interaction with test SKILL.md files
- **SkillInjector**: L0/L1/L2 disclosure formatting, tool context resolution
- **ContextManager**: Token counting, message unwinding, budget enforcement

### Should Be Mocked (external dependencies or non-deterministic components)

- **EmbeddingProvider**: Replace with deterministic vector function (e.g., hash-based). Real embeddings are non-deterministic and require model loading.
- **LongTermMemory**: In-memory fake with dict-based storage. Real LTM requires PostgreSQL + pgvector.
- **ModelRouter**: Canned LLM responses. Real LLM calls are slow, non-deterministic, and require API keys.
- **Redis**: Not needed for integration tests (used for caching, not core logic).
- **NATS**: Not needed (messaging bus, not core pipeline).
- **PostgreSQL**: Replaced by in-memory LTM fake.

## Recommendations

### 1. Create In-Memory LTM Fake for Integration Tests

Build a `FakeLongTermMemory` class implementing the same interface as `LongTermMemory` but backed by a Python dict. Must support `store()`, `search()`, `scan()`, and `count()`.

### 2. Create Deterministic Embedding Function

Build a `DeterministicEmbeddingProvider` that generates consistent vectors from text content (e.g., using a hash function mapped to a fixed-dimension vector space). This ensures reproducible search results in tests.

### 3. Wire ContextManager into ToolLoop (Implementation Gap)

Add optional `context_manager: ContextManager | None = None` parameter to `ToolLoop.__init__()`. When present, call `context_manager.manage()` after each iteration to keep the conversation within token budget. This is the highest-priority implementation gap.

### 4. Wire SkillInjector.resolve_tool_context() into Invoke-Iterative Route

The `invoke-iterative` endpoint should call `resolve_tool_context()` to provide tool-specific skill context during the tool loop, not just at initial invocation.

### 5. Create conftest.py with Shared Integration Fixtures

Build `tests/test_integration/conftest.py` with fixtures for:
- `fake_ltm` -- FakeLongTermMemory instance
- `deterministic_embedder` -- DeterministicEmbeddingProvider
- `bm25_index` -- Real BM25Index (empty, ready for use)
- `hybrid_searcher` -- Real HybridSearcher wired to fake LTM + deterministic embedder
- `skill_registry` -- Real SkillRegistry with test SKILL.md files
- `canned_model_router` -- ModelRouter returning predefined responses

### 6. Target ~30-40 Integration Tests

Based on the 10 scenarios above, with multiple assertions per scenario and edge cases, the target is 30-40 integration tests. This provides meaningful cross-subsystem coverage without duplicating unit test scope.

## Priority Order

1. **Recommendation 3** (wire ContextManager into ToolLoop) -- fixes implementation gap
2. **Recommendation 4** (wire resolve_tool_context) -- fixes implementation gap
3. **Recommendations 1+2** (test infrastructure) -- enables all integration tests
4. **Recommendation 5** (conftest) -- organizes test fixtures
5. **Recommendation 6** (write tests) -- closes coverage gaps
