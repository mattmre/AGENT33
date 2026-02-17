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
