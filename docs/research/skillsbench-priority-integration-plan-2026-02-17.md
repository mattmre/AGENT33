# SkillsBench Priority Integration Plan (2026-02-17)

## Goal
Validate and lock in AGENT-33 support for the four SkillsBench high-priority capability areas while documenting concrete next integration steps.

## Current implementation status
- **Iterative tool-use loop**: implemented (`agent33/agents/tool_loop.py`, `AgentRuntime.invoke_iterative`)
- **4-stage hybrid skill matching**: implemented (`agent33/skills/matching.py`)
- **Context window management**: implemented (`agent33/agents/context_manager.py`)
- **Multi-trial + CTRF reporting**: implemented (`agent33/evaluation/multi_trial.py`, `agent33/evaluation/ctrf.py`, `EvaluationService.export_ctrf`)

## Gap to close in this slice
- Existing repository-level analysis still contains historical text describing these as missing.
- There was no focused regression test ensuring these capability surfaces remain present after future refactors.

## Implemented in this slice
- Added `engine/tests/test_skillsbench_priority_surfaces.py` with regression checks for:
  - `AgentRuntime.invoke_iterative`
  - `ToolLoopConfig` iterative defaults
  - `ContextBudget` completion reservation + summarization thresholds
  - `SkillMatcher.match` contract surface
  - `EvaluationService.export_ctrf` and multi-trial/CTRF class availability

## Next integration actions
1. Add a small benchmark-style smoke harness that executes selected golden tasks in with/without-skills mode.
2. Persist generated CTRF artifacts to CI for PR-level visibility.
3. Reconcile `docs/research/skillsbench-analysis.md` historical gap statements with current implementation state and add a dated status appendix.

## Validation commands
```bash
cd engine
python -m ruff check src tests
python -m pytest tests/test_skillsbench_priority_surfaces.py -q
```

---

## Post-Stage1 Follow-Up (2026-02-18)

### Benchmark Smoke Monitoring
With Phase 27/29/30 Stage 1 backend slices complete, the next SkillsBench integration phase focuses on:

1. **Expand benchmark coverage from smoke to selected golden tasks**
   - Leverage existing `test_skillsbench_priority_surfaces.py` regression checks
   - Add `engine/tests/benchmarks/test_skills_smoke.py` with 3-5 simple task executions
   - Target runtime: <5 seconds total

2. **CI integration for artifact visibility**
   - Add non-blocking `benchmark-smoke` job to `.github/workflows/ci.yml`
   - Use `continue-on-error: true` to prevent PR disruption
   - Upload CTRF artifacts for historical tracking

3. **Expand to broader task scenarios post-Stage1**
   - After operations hub (Phase 27 Stage 2) provides monitoring UI
   - After multimodal adapters (Phase 29 Stage 2) integrate real providers
   - After outcome metrics (Phase 30 Stage 2) enable trend-driven improvement cycles

### Validation Evidence Commands
```bash
# Verify existing SkillsBench surfaces remain present
cd engine
python -m pytest tests/test_skillsbench_priority_surfaces.py -v

# Future: Run expanded benchmark smoke tests
python -m pytest tests/benchmarks/test_skills_smoke.py -v

# Future: Check CTRF artifact generation
ls benchmark-results/*.json
```

### Timeline
- **Current**: Regression checks validate core surfaces remain accessible
- **Next sprint**: Add smoke benchmark harness with CI artifact upload
- **Post-Stage2**: Expand to broader SkillsBench golden task coverage
