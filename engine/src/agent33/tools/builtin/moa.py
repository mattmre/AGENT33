"""Mixture-of-Agents (MoA) tool.

Wraps the MoA workflow template as a standard AGENT-33 tool so agents can
invoke multi-model ensemble reasoning through the normal tool interface.
"""

from __future__ import annotations

from typing import Any

import structlog

from agent33.tools.base import ToolContext, ToolResult
from agent33.workflows.executor import WorkflowExecutor
from agent33.workflows.templates.mixture_of_agents import (
    build_moa_workflow,
    format_moa_result,
)

logger = structlog.get_logger()


class MoATool:
    """Execute a Mixture-of-Agents workflow via the standard tool protocol.

    Parameters accepted in ``params``:
        query (str, required): The question or instruction to answer.
        reference_models (list[str], optional): Model IDs for the parallel
            reference layer.  Falls back to ``default_reference_models``.
        aggregator (str, optional): Model ID for the aggregator step.
            Falls back to ``default_aggregator_model``.
        reference_temperature (float, optional): Temperature for reference
            models.  Defaults to ``default_reference_temperature``.
        aggregator_temperature (float, optional): Temperature for the
            aggregator.  Defaults to ``default_aggregator_temperature``.
    """

    def __init__(
        self,
        default_reference_models: list[str] | None = None,
        default_aggregator_model: str = "",
        default_reference_temperature: float = 0.6,
        default_aggregator_temperature: float = 0.4,
    ) -> None:
        self._default_reference_models = default_reference_models or []
        self._default_aggregator_model = default_aggregator_model
        self._default_reference_temperature = default_reference_temperature
        self._default_aggregator_temperature = default_aggregator_temperature

    @property
    def name(self) -> str:
        return "mixture_of_agents"

    @property
    def description(self) -> str:
        return (
            "Run a Mixture-of-Agents ensemble: query multiple models in "
            "parallel and synthesize their responses through an aggregator."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or instruction to answer.",
                },
                "reference_models": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Model identifiers for the parallel reference layer.",
                },
                "aggregator": {
                    "type": "string",
                    "description": "Model identifier for the aggregator step.",
                },
                "reference_temperature": {
                    "type": "number",
                    "description": "Sampling temperature for reference models.",
                },
                "aggregator_temperature": {
                    "type": "number",
                    "description": "Sampling temperature for the aggregator.",
                },
            },
            "required": ["query"],
        }

    async def execute(self, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Build and run a MoA workflow, returning the aggregated answer."""
        query: str = params.get("query", "").strip()
        if not query:
            return ToolResult.fail("No query provided")

        reference_models: list[str] = params.get(
            "reference_models", self._default_reference_models
        )
        if not reference_models:
            return ToolResult.fail(
                "No reference models provided and no defaults configured. "
                "Set MOA_REFERENCE_MODELS or pass reference_models."
            )

        aggregator: str = params.get("aggregator", self._default_aggregator_model)
        if not aggregator:
            return ToolResult.fail(
                "No aggregator model provided and no default configured. "
                "Set MOA_AGGREGATOR_MODEL or pass aggregator."
            )

        ref_temp: float = params.get("reference_temperature", self._default_reference_temperature)
        agg_temp: float = params.get(
            "aggregator_temperature", self._default_aggregator_temperature
        )

        logger.info(
            "moa_tool_invoked",
            query_len=len(query),
            reference_models=reference_models,
            aggregator=aggregator,
        )

        try:
            workflow = build_moa_workflow(
                query=query,
                reference_models=reference_models,
                aggregator_model=aggregator,
                reference_temperature=ref_temp,
                aggregator_temperature=agg_temp,
            )
        except ValueError as exc:
            return ToolResult.fail(f"Failed to build MoA workflow: {exc}")

        executor = WorkflowExecutor(
            definition=workflow,
            tenant_id=context.tenant_id,
        )

        try:
            result = await executor.execute()
        except Exception as exc:
            logger.error("moa_workflow_execution_error", error=str(exc))
            return ToolResult.fail(f"MoA workflow execution failed: {exc}")

        if result.status.value == "failed":
            error_msgs = [sr.error for sr in result.step_results if sr.error]
            return ToolResult.fail(
                f"MoA workflow failed: {'; '.join(error_msgs) or 'unknown error'}"
            )

        aggregated = format_moa_result(result.outputs)
        logger.info(
            "moa_tool_complete",
            status=result.status.value,
            steps_executed=len(result.steps_executed),
            duration_ms=result.duration_ms,
        )
        return ToolResult.ok(aggregated)
