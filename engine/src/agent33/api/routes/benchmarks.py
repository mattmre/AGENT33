"""FastAPI router for benchmark run management.

Provides endpoints to trigger SkillsBench benchmark runs, list tasks,
and retrieve results.
"""

# NOTE: no ``from __future__ import annotations`` -- Pydantic needs these
# types at runtime for request-body validation.

from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent33.benchmarks.skillsbench.models import (
    BenchmarkRunResult,
    BenchmarkRunStatus,
    TaskFilter,
)
from agent33.benchmarks.skillsbench.task_loader import SkillsBenchTaskLoader

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/benchmarks", tags=["benchmarks"])

# In-memory storage for benchmark run results (bounded).
_MAX_STORED_RUNS = 100
_runs: dict[str, BenchmarkRunResult] = {}
_run_order: list[str] = []


def _store_run(run: BenchmarkRunResult) -> None:
    """Store a benchmark run with bounded retention."""
    _runs[run.run_id] = run
    _run_order.append(run.run_id)
    if len(_run_order) > _MAX_STORED_RUNS:
        oldest = _run_order.pop(0)
        _runs.pop(oldest, None)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ListTasksRequest(BaseModel):
    skillsbench_root: str = Field(
        default="./skillsbench",
        description="Root directory of the SkillsBench repository checkout.",
    )
    categories: list[str] = Field(
        default_factory=list,
        description="Filter to specific categories.",
    )
    max_tasks: int = Field(
        default=0,
        ge=0,
        description="Maximum number of tasks to return. 0 = unlimited.",
    )


class TaskSummary(BaseModel):
    task_id: str
    category: str
    instruction_preview: str = Field(
        default="",
        description="First 200 characters of the instruction.",
    )
    has_skills: bool = False


class ListTasksResponse(BaseModel):
    total: int = 0
    categories: list[str] = Field(default_factory=list)
    tasks: list[TaskSummary] = Field(default_factory=list)


class RunBenchmarkRequest(BaseModel):
    skillsbench_root: str = Field(
        default="./skillsbench",
        description="Root directory of the SkillsBench repository checkout.",
    )
    agent_name: str = Field(default="code-worker")
    model: str = Field(default="llama3.2")
    trials_per_task: int = Field(default=5, ge=1, le=100)
    skills_enabled: bool = Field(default=True)
    pytest_timeout_seconds: float = Field(default=300.0, gt=0)
    task_filter: TaskFilter = Field(default_factory=TaskFilter)


class RunSummaryResponse(BaseModel):
    run_id: str
    status: BenchmarkRunStatus
    total_tasks: int = 0
    total_trials: int = 0
    passed_trials: int = 0
    pass_rate: float = 0.0
    total_duration_ms: float = 0.0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/skillsbench/tasks", response_model=ListTasksResponse)
async def list_skillsbench_tasks(
    request: ListTasksRequest,
) -> dict[str, Any]:
    """List available SkillsBench tasks from a repository checkout."""
    root = Path(request.skillsbench_root)
    if not root.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"SkillsBench root directory not found: {root}",
        )

    loader = SkillsBenchTaskLoader(root)
    task_filter = TaskFilter(
        categories=request.categories,
        max_tasks=request.max_tasks,
    )
    tasks = loader.discover_tasks(task_filter=task_filter)
    categories = loader.list_categories()

    summaries = [
        TaskSummary(
            task_id=t.task_id,
            category=t.category,
            instruction_preview=t.instruction[:200] if t.instruction else "",
            has_skills=t.skills_dir is not None,
        )
        for t in tasks
    ]

    return {
        "total": len(summaries),
        "categories": categories,
        "tasks": summaries,
    }


@router.get("/skillsbench/runs", response_model=list[RunSummaryResponse])
async def list_benchmark_runs(
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List recent SkillsBench benchmark runs."""
    result: list[dict[str, Any]] = []
    for run_id in reversed(_run_order):
        run = _runs.get(run_id)
        if run is None:
            continue
        result.append(
            {
                "run_id": run.run_id,
                "status": run.status,
                "total_tasks": run.total_tasks,
                "total_trials": run.total_trials,
                "passed_trials": run.passed_trials,
                "pass_rate": run.pass_rate,
                "total_duration_ms": run.total_duration_ms,
            }
        )
        if len(result) >= limit:
            break
    return result


@router.get("/skillsbench/runs/{run_id}")
async def get_benchmark_run(run_id: str) -> dict[str, Any]:
    """Get detailed results for a specific benchmark run."""
    run = _runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return run.model_dump()
