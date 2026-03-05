# Next Session Briefing

Last updated: 2026-03-05T23:00:00Z

> **New:** Qwen-Agent competitive analysis completed in Session 55 — see
> [`docs/research/session55-qwen-agent-analysis.md`](research/session55-qwen-agent-analysis.md)
> for the full report. Seven adoption items have been integrated into the
> priority queue below (marked with 🔶).

## Current State

- **Merge status**: All Session 55 PRs (`#111`–`#130`) merged to `main`. Phase 2 completed all 9 outstanding development phases.
- **Open PRs**: None.
- **Latest session**: Session 55 (`docs/sessions/session-55-2026-03-05.md`).
- **Validation posture**:
  - Ruff check: clean (0 errors)
  - Ruff format: clean (414 files)
  - Pytest: 2722 passed, 2 pre-existing failures (`TestProductionSecrets`)
  - Frontend (vitest): 76 tests pass
- **ARCH-AEP tracker**: 29/29 closed, 0 in-progress, 0 open.
- **Pre-existing issue**: `test_production_mode_rejects_default_secrets` and `test_production_mode_rejects_other_default_secrets` fail — `Settings.validate_production_secrets` needs fix.

## Session 55 Highlights

### Phase 1 — PR Review & Merge
- Reviewed all 11 open PRs (#111–#121), addressed 27 review comments (including 5 security-critical fixes).
- Applied security fixes: multi-tenant IDOR on tool approvals (#120), reviewed_by spoof prevention (#120), RAG prompt injection sanitization (#121), broad exception narrowing (#118).
- Resolved 8 merge conflicts across wave-based rebasing.
- Merged all PRs in 4 dependency-safe waves with interim test runs.

### Phase 2 — Development Phase Completion
- Researched all 10 remaining development phases (22, 25–28, 30–33, 35).
- Phase 22 confirmed already complete; 9 phases implemented across 3 waves.
- 9 PRs created and merged (#122–#130): ~5,600 lines added across 48 files.
- 163 new tests added; final confidence gate: 2722 passed, 0 regressions.
- Created 11 research documents, 2 new workflow templates.
- All development phases now have refinement PRs merged.

## Top Priorities

1. **Phase 25 Stage 3**: Real-time WebSocket integration for workflow status updates; SSE fallback for status graph.
2. 🔶 **Streaming Agent Loop** _(P0/Critical — Qwen-Agent insight)_: Add `AsyncGenerator`-based streaming to `AgentRuntime.invoke()` and `tool_loop`. Yield `ToolLoopEvent` with token chunks, tool calls, tool results. Highest-impact UX improvement — eliminates 30 s+ silence during multi-step tool loops.
3. **Phase 26 Stage 3**: Improvement-cycle wizard UI; interactive plan-review/diff-review approval flows.
4. **Phase 27 Stage 3**: `improvement-cycle` workflow template wiring into frontend; multi-step wizard UX.
5. 🔶 **Multimodal ContentBlock** _(P1/High — Qwen-Agent insight)_: Extend `ChatMessage.content` to `Union[str, list[ContentBlock]]`. Update provider serialization (OpenAI, Ollama) for images/audio/video. Wire into existing `multimodal/` module.
6. 🔶 **Text-Based Tool Parsing** _(P1/High — Qwen-Agent insight)_: Add `TextToolCallParser` to `agents/tool_loop.py` for ReAct/XML/marker-based function calling fallback. Enables tool use for models without native `tool_calls` support.
7. **Phase 28 — LLMGuard/Garak adapter completion**: Current stubs need real adapter integration for enterprise security scanning.
8. **Frontend render/interaction tests**: Need `@testing-library/react` for component-level testing (current tests are unit/logic only).
9. **Phase 25/26 documentation & walkthroughs**: User-facing docs for visual explainer and decision/review pages.
10. 🔶 **GroupChat Action** _(P2/Medium — Qwen-Agent insight)_: Implement `group-chat` workflow action with speaker selection strategies (auto/round-robin/random/manual). Wire through existing workflow engine.
11. 🔶 **Agent Archetypes** _(P2/Medium — Qwen-Agent insight)_: Create configuration presets for common patterns — Assistant (RAG-integrated), Coder (code interpreter + persistent session), Router (LLM 1-of-N dispatch), GroupChat.
12. 🔶 **LLM Query Expansion** _(P2/Medium — Qwen-Agent insight)_: Add LLM-based keyword generation step in RAG pipeline before hybrid search. Improves retrieval recall for complex/ambiguous queries.
13. **Phase 22 validation**: Already complete on `main` but may need integration verification against new Phase 25–27 surfaces.
14. **SkillsBench integration**: Promote richer benchmark reporting and result artifacts beyond smoke runs.
15. **Fix `TestProductionSecrets`**: `Settings.validate_production_secrets` validator doesn't raise on default jwt_secret in production mode.
16. **A5/A6 integration**: Execute comparative scoring against persisted synthetic bundles.
17. 🔶 **Jupyter Kernel Adapter** _(P3/Medium — Qwen-Agent insight)_: Add `JupyterAdapter` to `execution/adapters/` with stateful sessions, image output capture, and Docker sandbox support. Enables iterative data-analysis and coding workflows.

## Remaining Phases of Development

All 10 development phases now have refinement PRs merged. Remaining work is Stage 3 (advanced features):

| Phase | Status on `main` | Remaining Stage 3 work |
| --- | --- | --- |
| 22 | ✅ Complete | Validation against new Phase 25–27 surfaces |
| 25 | Refinement merged (PR #128) | Real-time WebSocket; SSE status graph integration |
| 26 | Refinement merged (PR #129) | Interactive approval flows; improvement-cycle wizard |
| 27 | Refinement merged (PR #130) | Workflow template wiring; multi-step wizard UX |
| 28 | Refinement merged (PR #127) | LLMGuard/Garak real adapters (currently stubs) |
| 30 | Refinement merged (PR #122) | Production trace tuning |
| 31 | Refinement merged (PR #123) | Production-scale backup/restore validation |
| 32 | Refinement merged (PR #124) | Operationalization; cross-service tenant verification |
| 33 | Refinement merged (PR #125) | Ecosystem distribution; marketplace integration |
| 35 | Refinement merged (PR #126) | Voice daemon full implementation; policy tuning |

## Qwen-Agent Competitive Insights (Session 55)

Full analysis: [`docs/research/session55-qwen-agent-analysis.md`](research/session55-qwen-agent-analysis.md)

**Summary:** Qwen-Agent (Alibaba) excels at developer/user UX — streaming, multimodal messages, agent archetypes, and broad model compatibility. AGENT-33 is significantly stronger on infrastructure (governance, workflows, memory, MCP, hooks, multi-tenancy). Seven items adopted into the priority queue above.

### Adopted Items

| # | Item | Priority | Effort | AGENT-33 Gap | Qwen-Agent Pattern |
|---|------|----------|--------|--------------|--------------------|
| A1 | **Streaming Agent Loop** | P0/Critical | L | `invoke()` and `tool_loop` await complete responses; 30 s+ silence on multi-step | Generator-based snapshot streaming — every `_run()` yields `List[Message]` snapshots |
| A2 | **Multimodal ContentBlock** | P1/High | M | `ChatMessage.content` is `str` only; `multimodal/` module exists but isn't wired in | `ContentItem` with `text\|image\|file\|audio\|video` fields; `Message.content: Union[str, List[ContentItem]]` |
| A3 | **Text-Based Tool Parsing** | P1/High | M | Models without native `tool_calls` cannot use tools at all | `FnCallAgent` parses `✿FUNCTION✿`/XML/ReAct markers; transparent fallback |
| B1 | **GroupChat Action** | P2/Medium | M | Multi-agent is workflow-DAG or handoff only; no dynamic conversation loops | `GroupChat` with 4 speaker selection strategies + `@mention` routing |
| B2 | **Agent Archetypes** | P2/Medium | S | Every agent is a generic `AgentRuntime` + JSON config; no specialized presets | 16+ `Agent` subclasses; implement as config presets in AGENT-33 |
| B3 | **LLM Query Expansion** | P2/Medium | S | RAG pipeline uses raw user query for retrieval | LLM-based `keygen_strategies/` generates keywords before retrieval |
| C1 | **Jupyter Kernel Adapter** | P3/Medium | L | `CodeExecutor` is stateless CLI subprocess; no variable persistence | Docker Jupyter kernel with stateful sessions + image output capture |

### Patterns to Adopt (Non-Backlog)

These patterns from Qwen-Agent are worth incorporating as design conventions rather than discrete backlog items:

- **Snapshot streaming model**: Each yield contains the full response so far (not deltas). Simplifies consumer code — adopt for agent loop; use delta model only at the SSE API layer.
- **Agent-as-Tool bridge**: Register agents as tools in `ToolRegistry` for dynamic composition (complements existing `invoke-agent` workflow action).
- **Memory-as-Agent**: Make progressive recall available as a "memory agent" that participates in conversations, not only as a context injection mechanism.
- **`from_dict()` factory**: Add runtime agent creation from dicts without requiring JSON definition files on disk.

### Strengths to Preserve

The analysis confirms AGENT-33 is significantly ahead on: governance & security (★★★★★ vs ★★), workflow orchestration (★★★★★ vs ★★), memory & RAG (★★★★★ vs ★★★), hooks & observability (★★★★ vs ★), multi-tenancy (★★★★★ vs ★), and evaluation gates (★★★★ vs ★). **Do not compromise these strengths to adopt Qwen-Agent patterns.**

## Startup Checklist

```bash
git checkout main
git pull --ff-only
gh pr list --state open

cd engine
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src --config-file pyproject.toml
python -m pytest tests/ -q

cd ../frontend
npx vitest run
```

## Key Paths

| Purpose | Path |
| --- | --- |
| Session 55 log | `docs/sessions/session-55-2026-03-05.md` |
| Session 54 log | `docs/sessions/session-54-2026-03-05.md` |
| Session 53 log | `docs/sessions/session-53-2026-03-05.md` |
| Phase 25 research | `docs/research/session55-phase25-status-graph-design.md` |
| Phase 26 research | `docs/research/session55-phase26-html-preview-design.md` |
| Phase 27 research | `docs/research/session55-phase27-hub-alignment.md` |
| Phase 28 research | `docs/research/session55-phase28-persistence-architecture.md` |
| Phase 30 research | `docs/research/session55-phase30-api-policy-fixtures.md` |
| Phase 31 research | `docs/research/session55-phase31-production-tuning.md` |
| Phase 32 research | `docs/research/session55-phase32-connector-boundary-audit.md` |
| Phase 33 research | `docs/research/session55-phase33-provenance-architecture.md` |
| Phase 35 research | `docs/research/session55-phase35-policy-calibration.md` |
| Phase 30 acceptance research | `docs/research/session53-phase30-outcome-acceptance.md` |
| Phase 31 trend research | `docs/research/session53-phase31-trend-analytics.md` |
| Phase 31 calibration research | `docs/research/session53-phase31-threshold-tuning.md` |
| A5 persistence research | `docs/research/session53-a5-bundle-persistence.md` |
| Durable state research | `docs/research/session54-delta-durable-state-architecture-2026-03-05.md` |
| HITL approvals research | `docs/research/session54-delta-hitl-approvals-architecture-2026-03-05.md` |
| RAG diagnostics research | `docs/research/session54-delta-modular-retrieval-architecture-2026-03-05.md` |
| Orchestration landscape | `docs/research/session54-agent-orchestration-top30-landscape-2026-03-05.md` |
| Qwen-Agent analysis | `docs/research/session55-qwen-agent-analysis.md` |
| Session 52 roadmap research | `docs/research/session52-priority-and-phase-roadmap.md` |
| ARCH-AEP tracker | `docs/ARCH AGENTIC ENGINEERING AND PLANNING/cycles/2026-02-27/tracker-2026-02-27.md` |
| Phase index | `docs/phases/README.md` |
