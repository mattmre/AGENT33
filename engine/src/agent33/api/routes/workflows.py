"""FastAPI router for workflow management and execution."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent33.security.injection import scan_inputs_recursive
from agent33.workflows.definition import WorkflowDefinition
from agent33.workflows.executor import WorkflowExecutor, WorkflowResult

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/workflows", tags=["workflows"])

# In-memory workflow registry
_registry: dict[str, WorkflowDefinition] = {}


class WorkflowCreateRequest(BaseModel):
    """Request body for creating a workflow."""

    name: str
    version: str
    description: str | None = None
    triggers: dict[str, Any] = {}
    inputs: dict[str, Any] = {}
    outputs: dict[str, Any] = {}
    steps: list[dict[str, Any]]
    execution: dict[str, Any] = {}
    metadata: dict[str, Any] = {}


class WorkflowExecuteRequest(BaseModel):
    """Request body for executing a workflow."""

    inputs: dict[str, Any] = {}
    dry_run: bool = False


class WorkflowSummary(BaseModel):
    """Summary of a registered workflow."""

    name: str
    version: str
    description: str | None = None
    step_count: int
    triggers: dict[str, Any] = {}


@router.get("/")
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


@router.get("/{name}")
async def get_workflow(name: str) -> dict[str, Any]:
    """Get a workflow definition by name."""
    workflow = _registry.get(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")
    return workflow.model_dump()


@router.post("/", status_code=201)
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


@router.post("/{name}/execute")
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

    # Optionally override dry_run
    if request.dry_run:
        workflow = workflow.model_copy(
            update={"execution": workflow.execution.model_copy(update={"dry_run": True})}
        )

    executor = WorkflowExecutor(workflow)

    try:
        result: WorkflowResult = await executor.execute(request.inputs)
    except Exception as exc:
        logger.error("workflow_execution_failed", name=name, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    logger.info(
        "workflow_executed",
        name=name,
        status=result.status.value,
        duration_ms=result.duration_ms,
    )

    return result.model_dump()
