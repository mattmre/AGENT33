# Session 47 — Priority Items Research Findings

**Date**: 2026-02-26
**Scope**: Research sprint covering all 15 priority items from CLAUDE.md + next-session.md analysis.

## PR Audit Summary

| PR | Title | Recommendation | Rationale |
|---|---|---|---|
| #86 | ci: migrate AI review auth to safer defaults | **REBASE+MERGE** | Narrow CI fix, no overlap |
| #85 | feat: Phase 35 Multimodal Async-Governance | **REBASE+MERGE** | Priority 1 from next-session.md |
| #84 | docs: add session governance tracking | **NEEDS_WORK** | next-session.md pointer stale |
| #83 | docs: sync Wave 2 handoff evidence | **CLOSE** | Superseded — evidence already on main |
| #82 | test: harden connector boundary regressions | **REBASE+MERGE** | Additive tests, not superseded |
| #80 | feat(multimodal): async boundary path | **CLOSE** | Branch name mismatch, likely superseded by #85 |

**Merge order**: #86 -> #82 -> #85 (close #83, #80, assess #84)

## Phase 35 Multimodal Async-Governance Gap

**Problem**: Multimodal adapters use sync `enforce_connector_governance()` instead of async `ConnectorExecutor.execute()`. This bypasses timeout, circuit breaker, metrics, and retry middleware.

**Solution**: Create `multimodal/boundary.py` (mirror messaging pattern), convert adapters to `async run_async()` with `httpx.AsyncClient`, make `MultimodalService.execute_request()` async.

**Scope**: 1 new file, 5 modified files, 7-9 new tests

## Phase 32 Plugin SDK Gap

**What exists**: Full connector boundary framework, MCP bridge, basic PluginLoader (entry-point only), skills system, tool registry.

**What's missing**: Hook framework (32.1 — prerequisite), PluginManifest, PluginBase/PluginContext, PluginRegistry lifecycle, capability grants enforcement, plugin API endpoints.

**Build order**: Hook framework (32.1) FIRST -> Plugin SDK (32.8)

**Scope**: 9-11 new files, 60-80 tests, 6-8 endpoints

## Phase 33 Skill Packs & Distribution

**Status**: Zero existing Phase 33 code. Rich skills foundation to build on.

**Key deliverables**: Pack manifest (PACK.yaml), semver dependency resolution, distribution (tar.gz/git), capability discovery, marketplace API.

**4 differentiation features**: (1) Cross-skill semver deps, (2) User overlay survival, (3) Deprecation lifecycle, (4) Composition declarations.

**Scope**: 7-9 new files, 70-90 tests, 6-8 endpoints

## SkillsBench Readiness

**What exists**: Multi-trial evaluation, CTRF reporter, experiment runner, iterative tool loop, 4-stage skill matching, context window manager. All infrastructure is complete.

**Critical gap**: No `SkillsBenchAdapter` bridging `TrialEvaluatorAdapter` to real agent invocations. Current evaluator uses deterministic hash fallback.

**3 files needed**: `skillsbench/task_loader.py`, `skillsbench/adapter.py`, `skillsbench/pytest_runner.py`

## AWM Tier 2-3 Scope

**Tier 2 (implement)**: A5 Synthetic environment generation, A6 GRPO-inspired group-relative scoring, A7 Environment diversity scaling.

**Tier 3 (monitor)**: A8 Arctic-AWM model integration, A9 GRPO training pipeline, A10 Agent GPA framework.

**Highest value**: A5 (synthetic task generation) + A6 (group-relative scoring)

## CI/Infra Cleanup

- **Ruff**: Already blocking and passing. No action needed.
- **Mypy**: Non-blocking (37 type-ignores across 18 files). Remediate then re-enable.
- **Untracked files**: 70+ review/diff artifacts in repo root. Add to .gitignore.
- **Missing**: `ruff format --check` in CI pipeline.
- **Category D docs**: 7 legitimate research docs need committing.
