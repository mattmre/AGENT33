# ARCH-AEP Loop 8 -- POST-2 Gate Review

**Date**: 2026-04-07
**Scope**: POST-2 cluster -- PRs #388--#391 (SkillsBench CI, weekly workflow, eval mode, staged matching)
**Verdict**: PASS-WITH-CONDITIONS -- 0C / 2H / 6M / 6L

## Executive Summary

The POST-2 cluster delivers functional SkillsBench CLI integration, evaluation-mode context eviction in ToolLoop (with run/run_stream parity), and 4-stage staged matching wiring. The code is generally well-structured with appropriate error fallbacks. Two HIGH findings require remediation: the `_active_skills` mutation in the adapter is not concurrency-safe, and `agent33 bench run` generates empty CTRF reports (0 trials) without invoking any LLM, which silently misleads operators. Both are fixed in this same PR.

## Findings

### Panel A: Security & Correctness

| ID | Sev | Finding | File:Line | Recommendation |
|----|-----|---------|-----------|----------------|
| A-01 | H | **`_active_skills` mutation is not concurrency-safe.** `evaluate()` mutates `runtime._active_skills` and restores it in a `finally` block. Concurrent trials sharing one `AgentRuntime` will race on this list. | `adapter.py:203-234` | Add `asyncio.Lock` around mutation+invoke+restore. **Fixed in this PR.** |
| A-02 | M | **CI `benchmark-smoke` job has no explicit `permissions` block.** Inherits workflow defaults. | `.github/workflows/ci.yml` (benchmark-smoke job) | Add `permissions: { contents: read }`. |
| A-03 | L | Path traversal in `SkillsBenchArtifactStore.read_artifact()` is correctly guarded. | `storage.py` | No action. |
| A-04 | M | **Staged matching fallback keeps all skills on matcher error** with no metadata signal. Inflated scores possible on LLM outage. | `adapter.py` (staged matching block) | Add `trial_metadata["staged_matching_skipped"] = True` in except block. |
| A-05 | L | Context eviction correctly excludes system messages and preserves >=2 non-system messages. | `tool_loop.py` | No action. |

### Panel B: Architecture & Design

| ID | Sev | Finding | File:Line | Recommendation |
|----|-----|---------|-----------|----------------|
| B-01 | H | **`bench run` generates empty CTRF (0 trials) without LLM invocation.** Comment says "no live LLM" but docstring promises a full 86-task run. Weekly CI workflow will silently produce 0-trial reports. | `cli/bench.py` | Wire actual `SkillsBenchAdapter.run_benchmark()` call. **Fixed in this PR.** |
| B-02 | M | **`evaluation_mode` has no feature-flag lifecycle metadata.** Per locked decision (Session 122 panel), every flag needs ship/stable/default-on/removal dates and a kill switch. | `tool_loop.py:67` | Add comment block with lifecycle dates. |
| B-03 | M | **Token heuristic `* 1.3` under-estimates for code/JSON content** (typical ratio is 2--3x). May cause context overflow on code-heavy messages. | `tool_loop.py` (eviction calculation) | Increase multiplier to 1.5 or make it configurable on `ToolLoopConfig`. |
| B-04 | L | `search_staged()` correctly lives on `SkillRegistry` as a thin delegation method. | `registry.py` | No action. |
| B-05 | M | **`reindex()` called inside `evaluate()` -- runs 430x for a full 86-task x 5-trial run.** BM25 rebuild is wasteful when skills unchanged between trials of the same task. | `adapter.py` (staged matching block) | Move `reindex()` to `_load_bundled_skills()` after registry mutation. |
| B-06 | L | `run()` / `run_stream()` parity maintained for eviction calls. | `tool_loop.py` | No action. |
| B-07 | L | ~~Weekly workflow missing~~ -- **FALSE ALARM.** Reviewer read stale worktree. `benchmarks-weekly.yml` confirmed present on `origin/main`. | N/A | No action. |
| B-08 | M | **Benchmarks API route does not pass `skill_matcher` to adapter.** API-triggered runs skip 4-stage matching. | `api/routes/benchmarks.py` (build_skillsbench_adapter) | Pass `getattr(request.app.state, "skill_matcher", None)` to adapter constructor. |

### Panel C: Test Quality

| ID | Sev | Finding | File:Line | Recommendation |
|----|-----|---------|-----------|----------------|
| C-01 | M | **Eval mode tests do not cover `run_stream()`.** Regression in streaming eviction path would not be caught. | `test_tool_loop_eval_mode.py` | Add streaming integration test with eviction trigger. |
| C-02 | L | Staged matching tests mock at the right layer. | `test_skillsbench_staged_matching.py` | No action. |
| C-03 | M | **Error-fallback test does not assert skill count passed to agent.** | `test_skillsbench_staged_matching.py:223-259` | Add assertion on agent invocation skill list. |
| C-04 | L | Smoke tests validate evaluation infrastructure, not SkillsBench code paths. Acceptable for smoke suite. | `test_skills_smoke.py` | No action. |
| C-05 | L | Weekly workflow is inherently untestable (CI-only). | N/A | No action. |

## Verdict Rationale

**PASS-WITH-CONDITIONS.** 0 CRITICAL, 2 HIGH (both fixed in this PR), 6 MEDIUM, 6 LOW. The HIGH findings are addressed: A-01 via `asyncio.Lock` in `SkillsBenchAdapter`, and B-01 by wiring actual `SkillsBenchAdapter.run_benchmark()` invocation in `bench run`. MEDIUM findings are improvement candidates for future sessions.

## Required Remediations

Both HIGH findings are fixed in the same PR as this document (ARCH-AEP-POST2-R1).

POST-3 (Pack Ecosystem) may proceed.
