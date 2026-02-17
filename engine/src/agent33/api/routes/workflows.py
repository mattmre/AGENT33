"""FastAPI router for workflow management and execution."""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent33.automation.scheduler import WorkflowScheduler
from agent33.security.injection import scan_inputs_recursive
from agent33.security.permissions import require_scope
from agent33.workflows.definition import WorkflowDefinition
from agent33.workflows.executor import WorkflowExecutor, WorkflowResult

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/workflows", tags=["workflows"])

# In-memory workflow registry
_registry: dict[str, WorkflowDefinition] = {}

# In-memory execution history
_MAX_EXECUTION_HISTORY = 1000
_execution_history: deque[dict[str, Any]] = deque(maxlen=_MAX_EXECUTION_HISTORY)

# Workflow scheduler instance
_scheduler: WorkflowScheduler | None = None


def get_workflow_registry() -> dict[str, WorkflowDefinition]:
    """Expose the workflow registry for internal route composition."""
    return _registry


def get_execution_history() -> deque[dict[str, Any]]:
    """Expose workflow execution history for internal route composition."""
    return _execution_history


class WorkflowCreateRequest(BaseModel):
    """Request body for creating a workflow."""

    name: str
    version: str
    description: str | None = None
    triggers: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    steps: list[dict[str, Any]]
    execution: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecuteRequest(BaseModel):
    """Request body for executing a workflow."""

    inputs: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    # Repeat/autonomous execution controls (safe defaults)
    repeat_count: int | None = Field(default=None, ge=1, le=100)
    repeat_interval_seconds: int | None = Field(default=None, ge=0, le=3600)
    autonomous: bool = False  # If True, returns execution metadata instead of result


class WorkflowSummary(BaseModel):
    """Summary of a registered workflow."""

    name: str
    version: str
    description: str | None = None
    step_count: int
    triggers: dict[str, Any] = Field(default_factory=dict)


class WorkflowScheduleRequest(BaseModel):
    """Request body for scheduling a workflow."""

    cron_expr: str | None = None  # Cron expression (5-field format)
    interval_seconds: int | None = Field(default=None, ge=1, le=86_400)
    inputs: dict[str, Any] = Field(default_factory=dict)  # Optional workflow inputs


class WorkflowScheduleResponse(BaseModel):
    """Response for scheduled workflow."""

    job_id: str
    workflow_name: str
    schedule_type: str
    schedule_expr: str
    inputs: dict[str, Any]


class WorkflowHistoryEntry(BaseModel):
    """Entry in workflow execution history."""

    workflow_name: str
    trigger_type: str  # "manual" or "scheduled"
    status: str
    duration_ms: float
    timestamp: float
    error: str | None = None
    job_id: str | None = None  # Present for scheduled executions
    step_statuses: dict[str, str] | None = None  # Optional step-level status map


@router.get("/", dependencies=[require_scope("workflows:read")])
async def list_workflows() -> list[WorkflowSummary]:
    """List all registered workflows."""
    return [
        WorkflowSummary(
            name=w.name,
            version=w.version,
            description=w.description,
            step_count=len(w.steps),
            triggers=w.triggers.model_dump(),
        )
        for w in _registry.values()
    ]


# -- Scheduling endpoints (must be before /{name} to avoid route conflicts) ----


@router.get("/schedules", dependencies=[require_scope("workflows:read")])
async def list_schedules() -> list[WorkflowScheduleResponse]:
    """List all scheduled workflow jobs."""
    if _scheduler is None:
        return []
    jobs = _scheduler.list_jobs()

    return [
        WorkflowScheduleResponse(
            job_id=job.job_id,
            workflow_name=job.workflow_name,
            schedule_type=job.schedule_type,
            schedule_expr=job.schedule_expr,
            inputs=job.inputs,
        )
        for job in jobs
    ]


@router.delete("/schedules/{job_id}", dependencies=[require_scope("workflows:execute")])
async def delete_schedule(job_id: str) -> dict[str, Any]:
    """Remove a scheduled workflow job."""
    removed = False
    if _scheduler is not None:
        removed = _scheduler.remove(job_id)

    if not removed:
        raise HTTPException(status_code=404, detail=f"Schedule '{job_id}' not found")

    logger.info("workflow_schedule_removed", job_id=job_id)

    return {"job_id": job_id, "removed": True}


# -- Dynamic workflow routes (must be after static routes like /schedules) -----


@router.get("/{name}", dependencies=[require_scope("workflows:read")])
async def get_workflow(name: str) -> dict[str, Any]:
    """Get a workflow definition by name."""
    workflow = _registry.get(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")
    return workflow.model_dump()


@router.post("/", status_code=201, dependencies=[require_scope("workflows:write")])
async def create_workflow(request: WorkflowCreateRequest) -> dict[str, Any]:
    """Register a new workflow definition."""
    try:
        definition = WorkflowDefinition.model_validate(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if definition.name in _registry:
        raise HTTPException(
            status_code=409,
            detail=f"Workflow '{definition.name}' already exists",
        )

    _registry[definition.name] = definition
    logger.info("workflow_created", name=definition.name, version=definition.version)

    return {
        "name": definition.name,
        "version": definition.version,
        "step_count": len(definition.steps),
        "created": True,
    }


@router.post("/{name}/schedule", dependencies=[require_scope("workflows:execute")])
async def schedule_workflow(
    name: str, request: WorkflowScheduleRequest
) -> WorkflowScheduleResponse:
    """Schedule a workflow to run on a cron expression or interval."""
    workflow = _registry.get(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")

    scan = scan_inputs_recursive(request.inputs)
    if not scan.is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Input rejected: {', '.join(scan.threats)}",
        )

    # Validate that exactly one schedule type is provided
    if request.cron_expr and request.interval_seconds:
        raise HTTPException(
            status_code=400,
            detail="Provide either cron_expr or interval_seconds, not both",
        )
    if not request.cron_expr and not request.interval_seconds:
        raise HTTPException(
            status_code=400,
            detail="Must provide either cron_expr or interval_seconds",
        )

    scheduler = _get_scheduler()

    try:
        if request.cron_expr:
            job_id = scheduler.schedule_cron(
                workflow_name=name,
                cron_expr=request.cron_expr,
                inputs=request.inputs,
            )
            schedule_type = "cron"
            schedule_expr = request.cron_expr
        else:
            job_id = scheduler.schedule_interval(
                workflow_name=name,
                seconds=request.interval_seconds,
                inputs=request.inputs,
            )
            schedule_type = "interval"
            schedule_expr = f"{request.interval_seconds}s"
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info(
        "workflow_scheduled",
        workflow_name=name,
        job_id=job_id,
        schedule_type=schedule_type,
    )

    return WorkflowScheduleResponse(
        job_id=job_id,
        workflow_name=name,
        schedule_type=schedule_type,
        schedule_expr=schedule_expr,
        inputs=request.inputs,
    )


@router.get("/{name}/history", dependencies=[require_scope("workflows:read")])
async def get_workflow_history(name: str) -> list[WorkflowHistoryEntry]:
    """Get execution history for a specific workflow."""
    history = [
        WorkflowHistoryEntry(**entry)
        for entry in _execution_history
        if entry["workflow_name"] == name
    ]

    # Return most recent first
    return sorted(history, key=lambda x: x.timestamp, reverse=True)


@router.post("/{name}/execute", dependencies=[require_scope("workflows:execute")])
async def execute_workflow(
    name: str, request: WorkflowExecuteRequest
) -> dict[str, Any]:
    """Execute a registered workflow."""
    workflow = _registry.get(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")

    # Scan inputs for prompt injection (recursive to catch nested payloads)
    scan = scan_inputs_recursive(request.inputs)
    if not scan.is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Input rejected: {', '.join(scan.threats)}",
        )

    # Handle repeat/autonomous execution
    if request.repeat_count or request.autonomous:
        return await _execute_repeated_or_autonomous(
            workflow, name, request
        )

    # Standard single execution (backward compatible)
    return await _execute_single(workflow, name, request, trigger_type="manual")


async def _execute_single(
    workflow: WorkflowDefinition,
    name: str,
    request: WorkflowExecuteRequest,
    trigger_type: str = "manual",
    job_id: str | None = None,
) -> dict[str, Any]:
    """Execute a workflow once and return the result."""
    # Optionally override dry_run
    if request.dry_run:
        workflow = workflow.model_copy(
            update={"execution": workflow.execution.model_copy(update={"dry_run": True})}
        )

    executor = WorkflowExecutor(workflow)
    start_ts = time.time()
    start_monotonic = time.monotonic()

    try:
        result: WorkflowResult = await executor.execute(request.inputs)
        error = None
    except Exception as exc:
        logger.error("workflow_execution_failed", name=name, error=str(exc))
        # Record failure in history
        _execution_history.append({
            "workflow_name": name,
            "trigger_type": trigger_type,
            "status": "failed",
            "duration_ms": (time.monotonic() - start_monotonic) * 1000,
            "timestamp": start_ts,
            "error": str(exc),
            "job_id": job_id,
            "step_statuses": None,
        })
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Extract step statuses from result
    step_statuses = {sr.step_id: sr.status for sr in result.step_results}

    # Record success in history
    _execution_history.append({
        "workflow_name": name,
        "trigger_type": trigger_type,
        "status": result.status.value,
        "duration_ms": result.duration_ms,
        "timestamp": start_ts,
        "error": error,
        "job_id": job_id,
        "step_statuses": step_statuses,
    })

    logger.info(
        "workflow_executed",
        name=name,
        status=result.status.value,
        duration_ms=result.duration_ms,
        trigger_type=trigger_type,
    )

    return result.model_dump()


async def _execute_repeated_or_autonomous(
    workflow: WorkflowDefinition,
    name: str,
    request: WorkflowExecuteRequest,
) -> dict[str, Any]:
    """Execute a workflow multiple times or autonomously."""
    import asyncio

    repeat_count = request.repeat_count or 1
    interval = request.repeat_interval_seconds or 0
    results = []

    for i in range(repeat_count):
        if i > 0 and interval > 0:
            await asyncio.sleep(interval)

        result_dict = await _execute_single(workflow, name, request, trigger_type="manual")
        results.append(result_dict)

    # If autonomous mode, return execution metadata instead of full results
    if request.autonomous:
        return {
            "executions": repeat_count,
            "workflow_name": name,
            "status": "completed",
            "results_summary": [
                {
                    "status": r["status"],
                    "duration_ms": r["duration_ms"],
                    "steps_executed": len(r["steps_executed"]),
                }
                for r in results
            ],
        }

    # Otherwise return last result (backward compatible for repeat_count=1)
    return results[-1] if results else {}


# -- Scheduling support functions ---------------------------------------------


def _get_scheduler() -> WorkflowScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = WorkflowScheduler(on_trigger=_scheduled_execution_callback)
        _scheduler.start()
        logger.info("workflow_scheduler_initialized")
    return _scheduler


async def _scheduled_execution_callback(
    job_id: str,
    workflow_name: str,
    inputs: dict[str, Any],
) -> None:
    """Callback invoked when a scheduled job triggers."""
    logger.info("scheduled_workflow_triggered", workflow_name=workflow_name, job_id=job_id)
    workflow = _registry.get(workflow_name)
    if workflow is None:
        logger.error("scheduled_workflow_not_found", workflow_name=workflow_name, job_id=job_id)
        return

    scan = scan_inputs_recursive(inputs)
    if not scan.is_safe:
        logger.warning(
            "scheduled_workflow_input_rejected",
            workflow_name=workflow_name,
            job_id=job_id,
            threats=scan.threats,
        )
        return

    request = WorkflowExecuteRequest(inputs=inputs)
    try:
        await _execute_single(
            workflow,
            workflow_name,
            request,
            trigger_type="scheduled",
            job_id=job_id,
        )
    except Exception as exc:
        logger.error(
            "scheduled_workflow_execution_failed",
            workflow_name=workflow_name,
            job_id=job_id,
            error=str(exc),
        )
