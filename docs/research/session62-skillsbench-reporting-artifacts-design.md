# Session 62 SkillsBench Reporting and Artifact Design

Date: 2026-03-09

## Goal

Complete the SkillsBench reporting follow-up from the runtime benchmark brief by making benchmark runs durable, trial artifacts inspectable, and task-scoped skill loading isolated per trial.

## Verified Gaps

- Benchmark runs are stored only in module-level in-memory dicts in `api/routes/benchmarks.py`.
- `SkillsBenchAdapter` loads bundled skills into the shared `SkillRegistry` and never removes them after a trial.
- Per-trial pytest stdout/stderr and agent outputs are available transiently during execution but are not persisted.
- The benchmark API exposes only summary/detail JSON and cannot return CTRF or stored artifacts.

## Implementation Plan

### 1. Extend Benchmark Models

Add:

- `TrialArtifact` for persisted trial outputs
- `TaskBenchmarkSummary` for per-task aggregates
- artifact/excerpt fields on `TrialRecord`
- task summaries and artifact/CTRF paths on `BenchmarkRunResult`

### 2. Add Durable SkillsBench Storage

Introduce a file-backed store under `var/skillsbench_runs/` that can:

- persist `run.json`
- persist per-trial text artifacts
- persist `ctrf.json`
- list historical runs
- reload a run or artifact after process restart

### 3. Fix Trial Isolation

After each trial:

- restore any temporary runtime `_active_skills` changes
- remove newly loaded task skills from the shared `SkillRegistry`

That prevents one trial's bundled skills from leaking into later evaluations.

### 4. Persist Rich Trial Evidence

For each trial, persist:

- pytest stdout
- pytest stderr
- agent output
- agent raw response

The run model should retain short excerpts plus relative artifact paths so the API stays lightweight while detailed evidence remains available.

### 5. Add Richer API Surfaces

Add:

- persisted run listing/detail fallback from disk
- `GET /v1/benchmarks/skillsbench/runs/{run_id}/ctrf`
- `GET /v1/benchmarks/skillsbench/runs/{run_id}/artifacts/{artifact_path}`

## Validation Plan

- model tests for new artifact and task-summary fields
- adapter tests for skill cleanup and artifact persistence
- route tests for disk-backed run retrieval, CTRF export, and artifact fetch
- targeted pytest + ruff + mypy on benchmark modules
