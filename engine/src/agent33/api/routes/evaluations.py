"""FastAPI router for evaluation suite and regression gates."""

# NOTE: no ``from __future__ import annotations`` — Pydantic needs these
# types at runtime for request-body validation.

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent33.evaluation.models import (
    GateType,
    TaskResult,
    TriageStatus,
)
from agent33.evaluation.service import EvaluationService
from agent33.security.permissions import require_scope

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/evaluations", tags=["evaluations"])

# Singleton service
_service = EvaluationService()


def get_evaluation_service() -> EvaluationService:
    """Return the evaluation service singleton (for testing injection)."""
    return _service


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class CreateRunRequest(BaseModel):
    gate: GateType = GateType.G_PR
    commit_hash: str = ""
    branch: str = ""


class TaskResultInput(BaseModel):
    item_id: str
    result: TaskResult = TaskResult.PASS
    checks_passed: int = 0
    checks_total: int = 0
    duration_ms: int = 0
    notes: str = ""


class SubmitResultsRequest(BaseModel):
    task_results: list[TaskResultInput] = Field(default_factory=list)
    rework_count: int = 0
    scope_violations: int = 0


class SaveBaselineRequest(BaseModel):
    commit_hash: str = ""
    branch: str = ""


class UpdateTriageRequest(BaseModel):
    status: TriageStatus
    assignee: str = ""


class ResolveRegressionRequest(BaseModel):
    resolved_by: str = ""
    fix_commit: str = ""


# ---------------------------------------------------------------------------
# Golden task routes
# ---------------------------------------------------------------------------


@router.get(
    "/golden-tasks",
    dependencies=[require_scope("workflows:read")],
)
async def list_golden_tasks() -> list[dict[str, Any]]:
    """List all golden task definitions."""
    return _service.list_golden_tasks()


@router.get(
    "/golden-cases",
    dependencies=[require_scope("workflows:read")],
)
async def list_golden_cases() -> list[dict[str, Any]]:
    """List all golden case definitions."""
    return _service.list_golden_cases()


@router.get(
    "/gates/{gate}/tasks",
    dependencies=[require_scope("workflows:read")],
)
async def get_tasks_for_gate(gate: GateType) -> list[str]:
    """Get golden task IDs required for a specific gate."""
    return _service.get_tasks_for_gate(gate)


# ---------------------------------------------------------------------------
# Evaluation run routes
# ---------------------------------------------------------------------------


@router.post(
    "/runs",
    status_code=201,
    dependencies=[require_scope("tools:execute")],
)
async def create_run(body: CreateRunRequest) -> dict[str, Any]:
    """Create a new evaluation run."""
    run = _service.create_run(
        gate=body.gate,
        commit_hash=body.commit_hash,
        branch=body.branch,
    )
    return {"run_id": run.run_id, "gate": run.gate.value}


@router.get(
    "/runs",
    dependencies=[require_scope("workflows:read")],
)
async def list_runs(limit: int = 50) -> list[dict[str, Any]]:
    """List evaluation runs."""
    runs = _service.list_runs(limit=limit)
    return [
        {
            "run_id": r.run_id,
            "gate": r.gate.value,
            "started_at": r.started_at.isoformat(),
            "completed": r.completed_at is not None,
        }
        for r in runs
    ]


@router.get(
    "/runs/{run_id}",
    dependencies=[require_scope("workflows:read")],
)
async def get_run(run_id: str) -> dict[str, Any]:
    """Get evaluation run details."""
    run = _service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run.model_dump(mode="json")


@router.post(
    "/runs/{run_id}/results",
    dependencies=[require_scope("tools:execute")],
)
async def submit_results(run_id: str, body: SubmitResultsRequest) -> dict[str, Any]:
    """Submit golden task results to an evaluation run."""
    from agent33.evaluation.models import TaskRunResult

    task_results = [
        TaskRunResult(
            item_id=tr.item_id,
            result=tr.result,
            checks_passed=tr.checks_passed,
            checks_total=tr.checks_total,
            duration_ms=tr.duration_ms,
            notes=tr.notes,
        )
        for tr in body.task_results
    ]
    run = _service.submit_results(
        run_id=run_id,
        task_results=task_results,
        rework_count=body.rework_count,
        scope_violations=body.scope_violations,
    )
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return {
        "run_id": run.run_id,
        "gate_result": run.gate_report.overall.value if run.gate_report else None,
        "metrics": [m.model_dump() for m in run.metrics],
        "regressions_found": len(run.regressions),
    }


# ---------------------------------------------------------------------------
# Baseline routes
# ---------------------------------------------------------------------------


@router.post(
    "/runs/{run_id}/baseline",
    status_code=201,
    dependencies=[require_scope("tools:execute")],
)
async def save_baseline_from_run(run_id: str, body: SaveBaselineRequest) -> dict[str, Any]:
    """Save the results of a completed run as a baseline."""
    run = _service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if run.completed_at is None:
        raise HTTPException(status_code=409, detail="Run not yet completed")
    baseline = _service.save_baseline(
        metrics=run.metrics,
        task_results=run.task_results,
        commit_hash=body.commit_hash or run.commit_hash,
        branch=body.branch or run.branch,
    )
    return {"baseline_id": baseline.baseline_id}


@router.get(
    "/baselines",
    dependencies=[require_scope("workflows:read")],
)
async def list_baselines(limit: int = 20) -> list[dict[str, Any]]:
    """List baseline snapshots."""
    baselines = _service.list_baselines(limit=limit)
    return [
        {
            "baseline_id": b.baseline_id,
            "commit_hash": b.commit_hash,
            "branch": b.branch,
            "created_at": b.created_at.isoformat(),
        }
        for b in baselines
    ]


# ---------------------------------------------------------------------------
# Regression routes
# ---------------------------------------------------------------------------


@router.get(
    "/regressions",
    dependencies=[require_scope("workflows:read")],
)
async def list_regressions(
    status: str | None = None,
    severity: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List regression records."""
    from agent33.evaluation.models import RegressionSeverity

    status_filter = TriageStatus(status) if status else None
    severity_filter = RegressionSeverity(severity) if severity else None
    records = _service.recorder.list_all(
        status=status_filter, severity=severity_filter, limit=limit
    )
    return [r.model_dump(mode="json") for r in records]


@router.patch(
    "/regressions/{regression_id}/triage",
    dependencies=[require_scope("tools:execute")],
)
async def update_triage(regression_id: str, body: UpdateTriageRequest) -> dict[str, Any]:
    """Update triage status for a regression."""
    record = _service.recorder.update_triage(
        regression_id=regression_id,
        status=body.status,
        assignee=body.assignee,
    )
    if record is None:
        raise HTTPException(status_code=404, detail=f"Regression not found: {regression_id}")
    return {"regression_id": record.regression_id, "status": record.triage_status.value}


@router.post(
    "/regressions/{regression_id}/resolve",
    dependencies=[require_scope("tools:execute")],
)
async def resolve_regression(regression_id: str, body: ResolveRegressionRequest) -> dict[str, Any]:
    """Mark a regression as resolved."""
    record = _service.recorder.resolve(
        regression_id=regression_id,
        resolved_by=body.resolved_by,
        fix_commit=body.fix_commit,
    )
    if record is None:
        raise HTTPException(status_code=404, detail=f"Regression not found: {regression_id}")
    return {
        "regression_id": record.regression_id,
        "status": record.triage_status.value,
    }


# ---------------------------------------------------------------------------
# Multi-trial experiment routes
# ---------------------------------------------------------------------------


class StartExperimentRequest(BaseModel):
    tasks: list[str] = Field(min_length=1, max_length=50)
    agents: list[str] = Field(min_length=1, max_length=20)
    models: list[str] = Field(min_length=1, max_length=20)
    trials_per_combination: int = Field(default=5, ge=1, le=100)
    skills_modes: list[bool] = Field(default_factory=lambda: [True, False])
    timeout_per_trial_seconds: int = Field(default=300, ge=1)
    parallel_trials: int = Field(default=1, ge=1)


@router.post(
    "/experiments",
    status_code=201,
    dependencies=[require_scope("tools:execute")],
)
async def start_experiment(body: StartExperimentRequest) -> dict[str, Any]:
    """Start a multi-trial experiment."""
    from agent33.evaluation.multi_trial import ExperimentConfig

    config = ExperimentConfig(
        tasks=body.tasks,
        agents=body.agents,
        models=body.models,
        trials_per_combination=body.trials_per_combination,
        skills_modes=body.skills_modes,
        timeout_per_trial_seconds=body.timeout_per_trial_seconds,
        parallel_trials=body.parallel_trials,
    )
    run = await _service.start_multi_trial_run(config)
    return {
        "run_id": run.run_id,
        "status": run.status,
        "results_count": len(run.results),
        "skills_impacts_count": len(run.skills_impacts),
    }


@router.get(
    "/experiments/{run_id}",
    dependencies=[require_scope("workflows:read")],
)
async def get_experiment(run_id: str) -> dict[str, Any]:
    """Get multi-trial experiment status and results."""
    run = _service.get_multi_trial_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Experiment not found: {run_id}")
    return run.model_dump(mode="json")


@router.get(
    "/experiments/{run_id}/ctrf",
    dependencies=[require_scope("workflows:read")],
)
async def get_experiment_ctrf(run_id: str) -> dict[str, Any]:
    """Export multi-trial experiment as a CTRF report."""
    report = _service.export_ctrf(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Experiment not found: {run_id}")
    return report


@router.get(
    "/experiments/{run_id}/skills-impact",
    dependencies=[require_scope("workflows:read")],
)
async def get_experiment_skills_impact(run_id: str) -> dict[str, Any]:
    """Get skills impact data for a multi-trial experiment."""
    run = _service.get_multi_trial_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Experiment not found: {run_id}")
    return {
        "run_id": run.run_id,
        "impacts": [i.model_dump(mode="json") for i in run.skills_impacts],
    }
