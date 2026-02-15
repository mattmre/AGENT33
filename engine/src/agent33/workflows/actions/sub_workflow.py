"""Action that executes a sub-workflow inline."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


async def execute(
    workflow_definition: dict[str, Any] | None = None,
    inputs: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute a nested workflow defined inline.

    The sub-workflow is parsed into a
    :class:`~agent33.workflows.definition.WorkflowDefinition` and
    executed via a fresh
    :class:`~agent33.workflows.executor.WorkflowExecutor`.

    Args:
        workflow_definition: A dict matching the WorkflowDefinition
            schema (must include ``name``, ``version``, ``steps``).
        inputs: Input data forwarded to the sub-workflow.
        dry_run: If True, log but skip actual execution.

    Returns:
        A dict with ``status``, ``outputs``, ``steps_executed``,
        and ``duration_ms``.

    Raises:
        ValueError: If *workflow_definition* is not provided.
    """
    if not workflow_definition:
        raise ValueError("sub-workflow action requires a 'workflow_definition'")

    step_count = len(workflow_definition.get("steps", []))
    logger.info("sub_workflow", step_count=step_count, dry_run=dry_run)

    if dry_run:
        return {"dry_run": True, "step_count": step_count}

    from agent33.workflows.definition import WorkflowDefinition
    from agent33.workflows.executor import WorkflowExecutor

    sub_def = WorkflowDefinition(**workflow_definition)
    executor = WorkflowExecutor(sub_def)
    result = await executor.execute(inputs or {})

    return {
        "status": result.status.value,
        "outputs": result.outputs,
        "steps_executed": result.steps_executed,
        "duration_ms": result.duration_ms,
    }
