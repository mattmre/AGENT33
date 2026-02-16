# Session 17: Top 5 Priority Implementation

**Date**: 2026-02-15
**Orchestrator**: Claude Opus 4.6 (agentic orchestration)
**Goal**: Implement top 5 priority items from next-session.md

## Priority Items
1. Integration Testing (e2e subsystem tests)
2. Multi-Trial Evaluation & CTRF Reporting
3. AWM Tier 1 Adaptations (A1-A4)
4. Runtime Integration Gaps (answer leakage, context↔tool loop, failure taxonomy)
5. Matrix Channel Adapter (ZeroClaw parity #20)

## Orchestration Strategy
- Fresh agents per phase (no context rot)
- Research → Plan → Implement → PR for each item
- Parallel research where possible
- All research saved to `docs/research/`
- Session log updated throughout

## Timeline

### Phase A: Parallel Research (all 5 items)
| Agent | Task | Status | Start | End |
|-------|------|--------|-------|-----|
| researcher-p1 | Integration testing gap analysis | pending | | |
| researcher-p2 | Multi-trial eval & CTRF research | pending | | |
| researcher-p3 | AWM Tier 1 adaptation planning | pending | | |
| researcher-p4 | Runtime integration gaps analysis | pending | | |
| researcher-p5 | Matrix adapter requirements | pending | | |

### Phase B: Architecture & Planning
| Agent | Task | Status | Start | End |
|-------|------|--------|-------|-----|
| architect-p1 | Integration test plan | pending | | |
| architect-p2 | Multi-trial eval design | pending | | |
| architect-p3 | AWM Tier 1 design | pending | | |
| architect-p4 | Runtime gaps design | pending | | |
| architect-p5 | Matrix adapter design | pending | | |

### Phase C: Implementation & PRs
| Agent | Task | Branch | PR | Status |
|-------|------|--------|-----|--------|
| impl-p1 | Integration tests | feat/p1-integration-tests | | pending |
| impl-p2 | Multi-trial eval | feat/p2-multi-trial-eval | | pending |
| impl-p3 | AWM Tier 1 | feat/p3-awm-tier1 | | pending |
| impl-p4 | Runtime gaps | feat/p4-runtime-gaps | | pending |
| impl-p5 | Matrix adapter | feat/p5-matrix-adapter | | pending |

## Agent Activity Log

### Phase A: Research (all complete)
- **researcher-p1** (integration testing): 29 integration points mapped, 7 critical flows identified, 10 test scenarios defined. Key finding: ContextManager NOT wired into ToolLoop (implementation gap).
- **researcher-p2** (multi-trial eval): Full Phase 17 evaluation analysis. Identified need for TrialResult, MultiTrialResult, SkillsImpact models, CTRF serializer, ExperimentConfig loader.
- **researcher-p3** (AWM Tier 1): Detailed A1-A4 analysis. Recommended order: A4→A1→A2→A3. Total 135-175 new tests estimated. 4 new files, 11 modified files.
- **researcher-p4** (runtime gaps): 4 gaps analyzed. Gap 2 (ContextManager↔ToolLoop) is both implementation AND test gap. Gap 3 (failure taxonomy) needs mapping table.
- **researcher-p5** (Matrix adapter): Full adapter pattern analysis. Raw httpx approach (consistent with other adapters). 6 config fields, ~15-20 tests.

### Phase B: Research Documentation
- **doc-saver**: Saving 5 research docs to `docs/research/session17-*.md`

### Phase C: Implementation
- **impl-p1** (integration tests): Branch `feat/p1-integration-tests` — in progress
  - FakeLTM, deterministic embedder, 30-40 e2e tests, ContextManager→ToolLoop wiring
