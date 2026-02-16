---
title: "Session 17: Multi-Trial Evaluation & CTRF Analysis"
date: 2026-02-15
session: 17
type: research
status: complete
---

# Session 17: Multi-Trial Evaluation & CTRF Analysis

## Overview

This document analyzes the requirements for adding multi-trial evaluation and CTRF (Common Test Results Format) reporting to AGENT-33's existing evaluation subsystem. The goal is to align with SkillsBench's evaluation methodology -- 5 trials per task with binary reward scoring -- while preserving AGENT-33's existing Phase 17 evaluation infrastructure.

## Current Evaluation Capabilities (Phase 17)

### Golden Tasks and Cases

- **7 golden tasks** (GT-01 through GT-07): Single-action documentation tasks used as baseline evaluation scenarios
- **4 golden cases** (GC-01 through GC-04): Grouped evaluation scenarios for broader coverage

### Metrics (M-01 through M-05)

| Metric | Name | Description |
|--------|------|-------------|
| M-01 | Success Rate | Percentage of tasks completed successfully |
| M-02 | Time-to-Green | Duration from task start to first passing state |
| M-03 | Rework Rate | Number of revision cycles before acceptance |
| M-04 | Diff Size | Lines of code changed per task |
| M-05 | Scope Adherence | Percentage of deliverables matching original scope |

### Gate Types

- **G-PR**: Pull request gate (blocks merge if thresholds not met)
- **G-MRG**: Merge gate (post-merge validation)
- **G-REL**: Release gate (pre-release validation)
- **G-MON**: Monitoring gate (continuous production checks)

### Regression Indicators (RI-01 through RI-05)

5 regression indicators that detect performance degradation across evaluation runs.

### Infrastructure

- 12 API endpoints for evaluation management
- All in-memory storage (no database persistence)
- Single-run evaluation model

### KEY LIMITATION

The current evaluation system runs each task exactly once and reports pass/fail. This is insufficient for:
- **Stochastic LLM behavior**: The same task may pass on one run and fail on the next
- **Statistical significance**: Single-run results have no confidence interval
- **Skills impact measurement**: Cannot compare with-skills vs. without-skills pass rates
- **SkillsBench compatibility**: SkillsBench requires 5 trials with binary reward

## Multi-Trial Methodology (SkillsBench-Aligned)

### Core Principles

1. **5 trials per combination**: Each (task, agent, model, skills_mode) tuple is evaluated 5 times
2. **Binary reward**: Each trial scores 0 (any assertion fails) or 1 (all assertions pass)
3. **Pass rate**: `trials_passed / total_trials` (value between 0.0 and 1.0)
4. **Skills impact**: `pass_rate_with_skills - pass_rate_without_skills` (value between -1.0 and 1.0)

### Experiment Dimensions

```
task x agent x model x skills_mode x trials
  |      |       |         |           |
  |      |       |         |           +-- 5 (default, configurable)
  |      |       |         +-- with_skills / without_skills
  |      |       +-- ollama/llama3.2, openai/gpt-4o, etc.
  |      +-- orchestrator, code-worker, researcher, etc.
  +-- GT-01..GT-07, custom tasks
```

### Statistical Measures

- **Pass rate**: Primary metric, directly comparable to SkillsBench results
- **Variance**: `sum((trial_score - pass_rate)^2) / n` -- measures consistency
- **Standard deviation**: `sqrt(variance)` -- human-readable spread
- **Skills impact**: Delta between with-skills and without-skills pass rates
- **Confidence**: Based on trial count and variance (higher trials + lower variance = higher confidence)

## CTRF Format

### Standard Structure

CTRF (Common Test Results Format) provides a standardized JSON schema for test results. The base structure:

```json
{
  "results": {
    "tool": {
      "name": "agent33-eval",
      "version": "1.0.0"
    },
    "summary": {
      "tests": 35,
      "passed": 28,
      "failed": 5,
      "skipped": 2,
      "pending": 0,
      "other": 0,
      "start": 1708012800000,
      "stop": 1708013400000
    },
    "tests": [
      {
        "name": "GT-01: Create documentation file",
        "status": "passed",
        "duration": 4521
      }
    ]
  }
}
```

### Status Values

- `passed`: All assertions passed
- `failed`: One or more assertions failed
- `skipped`: Test was skipped (e.g., missing dependency)
- `pending`: Test is queued but not yet executed
- `other`: Non-standard outcome

### AGENT-33 Extensions for Multi-Trial

Additional fields in each test entry to support multi-trial evaluation:

```json
{
  "name": "GT-01: Create documentation file",
  "status": "passed",
  "duration": 4521,
  "extra": {
    "trials": 5,
    "pass_rate": 0.8,
    "variance": 0.16,
    "skills_enabled": true,
    "agent": "code-worker",
    "model": "ollama/llama3.2",
    "tokens_used": 12450,
    "trial_results": [1, 1, 0, 1, 1]
  }
}
```

The `status` field reflects the aggregate: `passed` if pass_rate >= threshold (default 0.6), `failed` otherwise.

## New Models

### TrialResult

```python
class TrialResult(BaseModel):
    trial_number: int          # 1-indexed
    score: Literal[0, 1]      # binary reward
    duration_ms: int           # execution time
    error_message: str | None  # if score == 0
    tokens_used: int           # total tokens consumed
    timestamp: datetime
```

### MultiTrialResult

```python
class MultiTrialResult(BaseModel):
    task_id: str               # e.g., "GT-01"
    agent: str                 # e.g., "code-worker"
    model: str                 # e.g., "ollama/llama3.2"
    skills_enabled: bool
    trials: list[TrialResult]
    pass_rate: float           # computed
    variance: float            # computed
    total_tokens: int          # sum of trial tokens
    total_duration_ms: int     # sum of trial durations
```

### SkillsImpact

```python
class SkillsImpact(BaseModel):
    task_id: str
    agent: str
    model: str
    pass_rate_with_skills: float
    pass_rate_without_skills: float
    skills_impact: float       # delta
    confidence: float          # based on trial count + variance
```

### MultiTrialRun

```python
class MultiTrialRun(BaseModel):
    run_id: str                # UUID
    config: ExperimentConfig
    results: list[MultiTrialResult]
    skills_impacts: list[SkillsImpact]
    started_at: datetime
    completed_at: datetime | None
    status: Literal["running", "completed", "failed", "cancelled"]
```

### ExperimentConfig

```python
class ExperimentConfig(BaseModel):
    tasks: list[str]           # task IDs to evaluate
    agents: list[str]          # agent names
    models: list[str]          # model identifiers
    trials_per_combination: int = 5
    skills_modes: list[bool] = [True, False]  # with and without
    timeout_per_trial_seconds: int = 300
    parallel_trials: int = 1   # concurrency limit
```

### AgentExperimentConfig

```python
class AgentExperimentConfig(BaseModel):
    agent: str
    model: str
    skills_enabled: bool
    context_manager_enabled: bool = True
    max_tool_iterations: int = 10
```

## New Files

### evaluation/multi_trial.py (~250 lines)

Core multi-trial execution engine:

- `MultiTrialExecutor` class
  - `execute_trial(task, agent_config) -> TrialResult`: Run a single trial with binary reward scoring
  - `execute_multi_trial(task, agent_config, num_trials) -> MultiTrialResult`: Run N trials and aggregate
  - `compute_pass_rate(trials) -> float`: Calculate pass rate from trial list
  - `compute_variance(trials, pass_rate) -> float`: Calculate score variance
- Binary reward logic: Wraps existing evaluation assertions, catches any failure as score=0
- Token counting integration: Tracks tokens per trial via ModelRouter metrics

### evaluation/ctrf.py (~100 lines)

CTRF report generation:

- `CTRFGenerator` class
  - `generate_report(run: MultiTrialRun) -> dict`: Produce CTRF-compliant JSON
  - `generate_summary(run: MultiTrialRun) -> dict`: Produce summary statistics
  - `write_report(run: MultiTrialRun, path: Path) -> None`: Write CTRF JSON file
- Handles the `extra` fields for multi-trial extensions
- Status mapping: pass_rate >= threshold -> "passed", else "failed"

### evaluation/experiment.py (~200 lines)

Experiment orchestration:

- `ExperimentRunner` class
  - `run_experiment(config: ExperimentConfig) -> MultiTrialRun`: Execute full experiment matrix
  - `compute_skills_impacts(results: list[MultiTrialResult]) -> list[SkillsImpact]`: Pair with/without results
  - `generate_comparison_matrix(run: MultiTrialRun) -> dict`: Tabular comparison across agents/models
- Iterates over all combinations of (task, agent, model, skills_mode)
- Supports parallel execution with configurable concurrency
- Progress tracking via run status updates

### tests/test_multi_trial_evaluation.py (~300 lines)

Comprehensive test suite:

- `TestTrialResult`: Model validation, binary score enforcement
- `TestMultiTrialResult`: Pass rate computation, variance computation, edge cases (0/5, 5/5, 3/5)
- `TestMultiTrialExecutor`: Single trial execution, multi-trial aggregation, timeout handling, error capture
- `TestSkillsImpact`: Impact calculation, confidence scoring, edge cases (negative impact, zero impact)
- `TestCTRFGenerator`: Report structure validation, summary statistics, status mapping, extra fields
- `TestExperimentRunner`: Full experiment matrix, skills impact pairing, progress tracking
- `TestExperimentConfig`: Validation, defaults, edge cases

## Modified Files

### evaluation/service.py

Additions:
- `start_multi_trial_run(config: ExperimentConfig) -> MultiTrialRun`: Create and start a new multi-trial run
- `get_multi_trial_run(run_id: str) -> MultiTrialRun | None`: Retrieve run status and results
- `list_multi_trial_runs() -> list[MultiTrialRun]`: List all runs
- `export_ctrf(run_id: str) -> dict`: Generate CTRF report for a run

### evaluation/regression.py

Modifications:
- RI-01 through RI-05 updated to accept `MultiTrialResult` as input
- New regression indicator: **RI-06 (Pass Rate Regression)** -- detects when pass_rate drops below historical baseline
- New regression indicator: **RI-07 (Skills Impact Regression)** -- detects when skills_impact decreases
- Regression detection uses pass_rate instead of single-run pass/fail

### api/routes/evaluations.py

New endpoints:
- `POST /v1/evaluations/experiments`: Start a new multi-trial experiment
- `GET /v1/evaluations/experiments/{run_id}`: Get experiment status and results
- `GET /v1/evaluations/experiments/{run_id}/ctrf`: Export CTRF report
- `GET /v1/evaluations/experiments/{run_id}/skills-impact`: Get skills impact analysis

## Integration with Existing Systems

### Backward Compatibility

All existing Phase 17 functionality is preserved:
- Single-run evaluation continues to work unchanged
- Golden tasks and cases are reused as multi-trial task definitions
- Existing metrics (M-01..M-05) remain for single-run use
- Gate types work with both single-run and multi-trial results

### New Metrics for Multi-Trial

| Metric | Name | Description |
|--------|------|-------------|
| M-06 | Multi-Trial Pass Rate | Aggregate pass rate across all trials |
| M-07 | Skills Impact Score | Average skills_impact across tasks |
| M-08 | Evaluation Consistency | 1 - average variance (higher = more consistent) |

### SkillsBench Comparison

With multi-trial evaluation, AGENT-33 results become directly comparable to SkillsBench:

| Dimension | SkillsBench | AGENT-33 (Current) | AGENT-33 (After) |
|-----------|-------------|--------------------|--------------------|
| Trials | 5 | 1 | 5 (configurable) |
| Reward | Binary | Pass/fail | Binary |
| Skills impact | Yes | No | Yes |
| CTRF output | Yes | No | Yes |
| Multi-agent | No | Yes | Yes |
| Multi-tenant | No | Yes | Yes |
