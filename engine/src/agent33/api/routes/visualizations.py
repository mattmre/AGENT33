"""FastAPI router for workflow visualizations."""

from __future__ import annotations

import re
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request

from agent33.security.permissions import require_scope
from agent33.services.graph_generator import generate_workflow_graph
from agent33.workflows.dag import CycleDetectedError

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/visualizations", tags=["visualizations"])
_WORKFLOW_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


@router.get("/workflows/{workflow_id}/graph", dependencies=[require_scope("workflows:read")])
async def get_workflow_graph(
    workflow_id: str,
    request: Request,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Get visual graph representation of a workflow.

    Returns nodes with deterministic layered layout coordinates, edges,
    and overlays latest execution step statuses when available.

    Args:
        workflow_id: The workflow name/identifier.

    Returns:
        Graph structure with nodes, edges, layout metadata, and optional status overlay.

    Raises:
        HTTPException: 404 if workflow not found, 422 for cyclic workflows.
    """
    if not _WORKFLOW_ID_PATTERN.fullmatch(workflow_id):
        raise HTTPException(status_code=400, detail="Invalid workflow identifier format")

    # Import workflows route module to access route-level storage accessors.
    from agent33.api.routes import workflows

    workflow = workflows.get_workflow_registry().get(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Prefer the current live-run snapshot when a run_id is supplied.
    execution_status: dict[str, str] = {}
    used_live_overlay = False
    if run_id:
        manager = getattr(request.app.state, "ws_manager", None)
        if manager is not None:
            live_event = await manager.build_sync_event(run_id)
            if live_event is not None and live_event.workflow_name == workflow_id:
                execution_status = dict(live_event.data.get("step_statuses", {}))
                used_live_overlay = True

    if not used_live_overlay:
        execution_history = workflows.get_execution_history()
        if execution_history:
            recent_executions = [
                entry for entry in execution_history if entry["workflow_name"] == workflow_id
            ]
            if recent_executions:
                most_recent = max(recent_executions, key=lambda entry: entry.get("timestamp") or 0)
                step_statuses = most_recent.get("step_statuses")
                if step_statuses:
                    execution_status = step_statuses
                else:
                    workflow_status = most_recent.get("status")
                    if workflow_status == "success":
                        for step in workflow.steps:
                            execution_status[step.id] = "success"
                    elif workflow_status == "failed":
                        for step in workflow.steps:
                            execution_status[step.id] = "failed"

    # Generate graph with optional status overlay.
    try:
        graph = generate_workflow_graph(workflow, execution_status)
    except CycleDetectedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    logger.info(
        "workflow_graph_generated",
        workflow_id=workflow_id,
        run_id=run_id,
        node_count=len(graph.get("nodes", [])),
        edge_count=len(graph.get("edges", [])),
        has_status_overlay=bool(execution_status),
        used_live_overlay=used_live_overlay,
    )

    return graph
