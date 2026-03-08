# Session 57 Runtime and Benchmark Implementation Brief

**Date:** 2026-03-06
**Scope:** Phase 38 Docker container kernels, SkillsBench richer reporting, and A5/A6 comparative scoring.

## Key Findings
- Jupyter execution is only partially integrated today: `execution/adapters/jupyter.py` is local-kernel only, does not subclass `BaseAdapter`, returns plain dicts, and is not properly wired through `CodeExecutor`.
- `workflows/actions/execute_code.py` currently drops artifacts, so notebook outputs are not preserved through workflow execution.
- `engine/pyproject.toml` is missing the optional Jupyter dependency group described by the phase docs.
- SkillsBench has a working smoke path, but reporting is shallow: benchmark runs are kept in module-level in-memory storage, per-trial pytest/stdout/stderr artifacts are not persisted, and the adapter risks skill-registry contamination between trials.
- A5 bundle persistence exists in `SyntheticEnvironmentService`, but there is no A6 bundle-comparative evaluation harness and current comparative scoring loses task/bundle alignment.

## Dependency-Ordered Plan
1. Phase 38 Stage 3: refactor Jupyter execution into a real execution backend and add Docker-backed kernel sessions.
2. SkillsBench reporting: fix trial isolation, extend reporting models, persist artifacts, and add richer benchmark API surfaces.
3. A5/A6 comparative scoring: define bundle evaluation contracts, preserve bundle/task alignment, add a bundle evaluation runner, and expose bundle-driven comparison endpoints.

## Recommended PR Boundaries
- PR 1: Phase 38 Docker container kernels and execution-framework alignment
- PR 2: SkillsBench reporting + artifact persistence
- PR 3: A5/A6 bundle evaluation contract + comparative integration
- Optional split: PR 3a bundle evaluation/service uplift, PR 3b comparative refactor for aligned scores

## Key Files
- `engine/src/agent33/execution/adapters/jupyter.py`
- `engine/src/agent33/execution/models.py`, `validation.py`, `executor.py`
- `engine/src/agent33/workflows/actions/execute_code.py`
- `engine/src/agent33/benchmarks/skillsbench/*`
- `engine/src/agent33/api/routes/benchmarks.py`
- `engine/src/agent33/evaluation/synthetic_envs/*`
- `engine/src/agent33/evaluation/comparative/*`
- `engine/src/agent33/api/routes/synthetic_envs.py`, `comparative.py`
- `engine/pyproject.toml`, `engine/src/agent33/config.py`

## Recommended New Research Docs
- `docs/research/session57-phase38-docker-kernel-architecture.md`
- `docs/research/session57-skillsbench-reporting-artifacts-design.md`
- `docs/research/session57-a5-a6-bundle-comparative-evaluation-design.md`
- `docs/runbooks/jupyter-kernel-containers.md`

## Highest-Risk Integration Points
- Comparative scoring is not task-aligned today; bundle-driven comparisons would be misleading without model/storage changes.
- Persisted A5 bundles are still data-only without a runnable evaluation harness.
- SkillsBench trials are not fully isolated because loaded benchmark skills are not removed from the shared registry.
- Container kernels materially change the security posture and need explicit image/network/mount controls.
