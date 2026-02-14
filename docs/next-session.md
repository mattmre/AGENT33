# Next Session Briefing

Last updated: 2026-02-14T18:00

## Current State
- **Branch**: `main`
- **Main**: 533 tests passing, 0 lint errors
- **Open PRs**: 0
- **Merged PRs**: #2 (Trivy), #3 (Performance), #4 (Governance), #5 (IDOR)
- **Phases 1-17, 21**: Complete
- **Phases 18-20**: Planned
- **Research**: 29 dossiers + 5 strategy docs complete

## What Was Done This Session (2026-02-14, Session 9)

### Phase 15 Complete — Review Automation & Two-Layer Review (65 new tests)

Built the `engine/src/agent33/review/` module implementing the two-layer review workflow.

### Phase 16 Complete — Observability & Trace Pipeline (54 new tests)

Built the trace pipeline in `engine/src/agent33/observability/`: trace models, failure taxonomy (10 categories), trace collector, retention policies, trace API.

### Phase 17 Complete — Evaluation Suite Expansion & Regression Gates (77 new tests)

Built the evaluation framework in `engine/src/agent33/evaluation/`:

| # | Component | Module | Description |
|---|-----------|--------|-------------|
| 1 | Data models | `evaluation/models.py` | 10 enums, 10 Pydantic models for gates, metrics, regressions, baselines |
| 2 | Golden tasks | `evaluation/golden_tasks.py` | GT-01..GT-07 tasks, GC-01..GC-04 cases, tag-based lookups |
| 3 | Metrics calculator | `evaluation/metrics.py` | M-01 through M-05 computation |
| 4 | Gate enforcer | `evaluation/gates.py` | 8 default thresholds (v1.0.0), gate execution matrix |
| 5 | Regression detector | `evaluation/regression.py` | RI-01, RI-02, RI-04 detection; RegressionRecorder with triage |
| 6 | Evaluation service | `evaluation/service.py` | Full pipeline: runs, metrics, gates, regressions, baselines |
| 7 | Evaluation API | `api/routes/evaluations.py` | 12 REST endpoints under `/v1/evaluations` |

## Priority 1: Next Phase (Phase 18 — Autonomy Budget Enforcement & Policy Automation)

Phase dependency chain: ~~14 (Security)~~ → ~~15 (Review)~~ → ~~16 (Observability)~~ → ~~17 (Evaluation Gates)~~ → **18 (Autonomy Enforcement)** → 19 (Release Automation) → 20 (Continuous Improvement)

## Priority 2: ZeroClaw Feature Parity

Remaining ZeroClaw parity items to integrate into Phases 18-20:

| # | Item | Source | Priority | Effort |
|---|------|--------|----------|--------|
| 13 | Hybrid search (BM25 + vector) | ZeroClaw `memory/vector.rs` | P0 | 3 days |
| 14 | Embedding cache with LRU | ZeroClaw `memory/sqlite.rs` | P1 | 1.5 days |
| 15 | Tokenizer-aware chunking | ZeroClaw `memory/chunker.rs` | P1 | 1 day |
| 16 | JSON Schema on Tool protocol | ZeroClaw `tools/traits.rs` | P1 | 2 days |
| 17 | Provider registry expansion (22+) | ZeroClaw providers | P1 | 2 days |
| 18 | Skills/plugin system | ZeroClaw `skills/mod.rs` | P2 | 4 days |
| 19 | Channel health checks | ZeroClaw `channels/mod.rs` | P2 | 1.5 days |
| 20 | Matrix channel adapter | ZeroClaw `channels/matrix.rs` | P3 | 2 days |

## Key Files to Know
| Purpose | Path |
| --- | --- |
| Entry point | `engine/src/agent33/main.py` |
| Config | `engine/src/agent33/config.py` |
| Agent runtime | `engine/src/agent33/agents/runtime.py` |
| Agent registry | `engine/src/agent33/agents/registry.py` |
| Agent definitions | `engine/agent-definitions/*.json` |
| Tool registry | `engine/src/agent33/tools/registry.py` |
| Execution layer | `engine/src/agent33/execution/` |
| Review automation | `engine/src/agent33/review/` |
| Observability | `engine/src/agent33/observability/` |
| Evaluation suite | `engine/src/agent33/evaluation/` |
| Security | `engine/src/agent33/security/` |
| Phase plans | `docs/phases/` |

## Test Commands
```bash
cd engine
python -m pytest tests/ -q               # full suite (~14 min, 533 tests)
python -m pytest tests/ -x -q            # stop on first failure
python -m pytest tests/test_phase17_evaluation.py -x -q  # Phase 17 tests (77 tests)
python -m pytest tests/test_phase16_observability.py -x -q  # Phase 16 tests (54 tests)
python -m pytest tests/test_phase15_review.py -x -q  # Phase 15 tests (65 tests)
python -m ruff check src/ tests/         # lint (0 errors)
```
