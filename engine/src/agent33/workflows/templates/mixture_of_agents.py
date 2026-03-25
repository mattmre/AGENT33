"""Mixture-of-Agents (MoA) workflow template builder.

Implements the MoA methodology (arXiv:2406.04692) as a native AGENT-33 DAG
workflow.  Multiple reference models answer the same query in parallel, then
an aggregator model synthesizes their responses into a single high-quality
answer.

The builder produces a ``WorkflowDefinition`` that the standard
``WorkflowExecutor`` can execute without any engine changes.
"""

from __future__ import annotations

import re
from typing import Any

from agent33.workflows.definition import (
    ExecutionMode,
    StepAction,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowMetadata,
    WorkflowStep,
)

# ---------------------------------------------------------------------------
# Aggregator system prompt -- derived from the MoA paper (arXiv:2406.04692)
# ---------------------------------------------------------------------------

MOA_AGGREGATOR_SYSTEM_PROMPT: str = (
    "You have been provided with a set of responses from various open-source "
    "AI models to the latest user query. Your task is to synthesize these "
    "responses into a single, high-quality response. It is crucial to "
    "critically evaluate the information provided in these responses, "
    "recognizing that some of it may be biased or incorrect. Your response "
    "should not simply replicate the given answers but should offer a refined, "
    "accurate, and comprehensive reply to the instruction. Ensure your "
    "response is well-structured, coherent, and adheres to the highest "
    "standards of accuracy and reliability.\n\n"
    "Responses from models:"
)


def _sanitize_step_id(raw: str) -> str:
    """Convert an arbitrary model name into a valid WorkflowStep id.

    Step IDs must match ``^[a-z][a-z0-9-]*$``.  This helper lower-cases the
    name, replaces non-alphanumeric characters with hyphens, collapses
    consecutive hyphens, and ensures the result starts with a letter.
    """
    lowered = raw.lower().strip()
    # Replace any character that is not a-z or 0-9 with a hyphen
    sanitized = re.sub(r"[^a-z0-9]", "-", lowered)
    # Collapse consecutive hyphens
    sanitized = re.sub(r"-+", "-", sanitized)
    # Strip leading/trailing hyphens
    sanitized = sanitized.strip("-")
    # Ensure it starts with a letter
    if not sanitized or not sanitized[0].isalpha():
        sanitized = f"m-{sanitized}" if sanitized else "model"
    return sanitized


def _make_unique_ids(models: list[str]) -> list[tuple[str, str]]:
    """Return (step_id, model_name) pairs with unique step IDs.

    If two models would produce the same sanitized ID, a numeric suffix is
    appended.
    """
    seen: dict[str, int] = {}
    pairs: list[tuple[str, str]] = []
    for model in models:
        base = f"ref-{_sanitize_step_id(model)}"
        count = seen.get(base, 0)
        step_id = f"{base}-{count}" if count > 0 else base
        seen[base] = count + 1
        pairs.append((step_id, model))
    return pairs


def _build_reference_prompt(query: str) -> str:
    """Build the prompt sent to each reference model."""
    return query


def _build_aggregator_user_prompt(
    query: str,
    reference_step_ids: list[str],
) -> str:
    """Build the user prompt for the aggregator step.

    Uses Jinja2-style expression references so the ``ExpressionEvaluator``
    inside ``WorkflowExecutor`` can substitute actual reference outputs at
    runtime.
    """
    lines: list[str] = [f"Original query: {query}", "", "Reference responses:"]
    for idx, step_id in enumerate(reference_step_ids, 1):
        # Reference the "result" key that invoke_agent.execute() returns
        lines.append(f"{idx}. {{{{ {step_id}.result | default('(no response)') }}}}")
    return "\n".join(lines)


def build_moa_workflow(
    query: str,
    reference_models: list[str],
    aggregator_model: str,
    reference_temperature: float = 0.6,
    aggregator_temperature: float = 0.4,
) -> WorkflowDefinition:
    """Build a Mixture-of-Agents DAG workflow.

    Creates *N* parallel reference-model steps followed by a single aggregator
    step that depends on all of them.  The aggregator receives every reference
    output and synthesizes a unified answer.

    Args:
        query: The user question / instruction to answer.
        reference_models: List of model identifiers to query in parallel.
        aggregator_model: Model identifier for the synthesis step.
        reference_temperature: Sampling temperature for reference models.
        aggregator_temperature: Sampling temperature for the aggregator.

    Returns:
        A fully-formed ``WorkflowDefinition`` ready for ``WorkflowExecutor``.

    Raises:
        ValueError: If ``reference_models`` is empty.
    """
    if not reference_models:
        raise ValueError("At least one reference model is required")

    id_model_pairs = _make_unique_ids(reference_models)
    reference_step_ids = [sid for sid, _ in id_model_pairs]

    # -- Reference steps (all independent, will be run in parallel by DAG) --
    reference_steps: list[WorkflowStep] = []
    for step_id, model_name in id_model_pairs:
        reference_steps.append(
            WorkflowStep(
                id=step_id,
                name=f"Reference: {model_name}",
                action=StepAction.INVOKE_AGENT,
                agent=model_name,
                inputs={
                    "prompt": _build_reference_prompt(query),
                    "temperature": reference_temperature,
                    "model": model_name,
                },
            )
        )

    # -- Aggregator step (depends on all reference steps) --
    aggregator_step = WorkflowStep(
        id="moa-aggregator",
        name=f"MoA Aggregator: {aggregator_model}",
        action=StepAction.INVOKE_AGENT,
        agent=aggregator_model,
        depends_on=reference_step_ids,
        inputs={
            "system_prompt": MOA_AGGREGATOR_SYSTEM_PROMPT,
            "prompt": _build_aggregator_user_prompt(query, reference_step_ids),
            "temperature": aggregator_temperature,
            "model": aggregator_model,
        },
    )

    all_steps = [*reference_steps, aggregator_step]

    return WorkflowDefinition(
        name="moa-workflow",
        version="1.0.0",
        description=(
            "Mixture-of-Agents workflow: parallel reference models "
            "followed by aggregator synthesis (arXiv:2406.04692)."
        ),
        steps=all_steps,
        execution=WorkflowExecution(
            mode=ExecutionMode.DEPENDENCY_AWARE,
            parallel_limit=len(reference_models),
        ),
        metadata=WorkflowMetadata(
            tags=["moa", "multi-model", "ensemble"],
        ),
    )


def format_moa_result(workflow_outputs: dict[str, Any]) -> str:
    """Extract the aggregated response from a MoA workflow result.

    Args:
        workflow_outputs: The ``outputs`` dict from ``WorkflowResult``.

    Returns:
        The aggregated text response, or a fallback message.
    """
    # The aggregator step writes its output under "result" key
    result = workflow_outputs.get("result")
    if isinstance(result, str):
        return result
    # Fallback: return stringified outputs
    return str(workflow_outputs) if workflow_outputs else "(no aggregated response)"
