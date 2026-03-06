from __future__ import annotations

from pathlib import Path

import pytest

from agent33.workflows.definition import WorkflowDefinition
from agent33.workflows.executor import WorkflowExecutor

WORKTREE_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = WORKTREE_ROOT / "core" / "workflows" / "improvement-cycle"


@pytest.mark.parametrize(
    ("filename", "workflow_name", "required_input", "expected_source"),
    [
        (
            "retrospective.workflow.yaml",
            "improvement-cycle-retrospective",
            "session_id",
            "session-end",
        ),
        (
            "metrics-review.workflow.yaml",
            "improvement-cycle-metrics-review",
            "review_period",
            "weekly",
        ),
    ],
)
def test_improvement_cycle_templates_load_with_expected_shape(
    filename: str,
    workflow_name: str,
    required_input: str,
    expected_source: str,
) -> None:
    definition = WorkflowDefinition.load_from_file(TEMPLATE_DIR / filename)

    assert definition.name == workflow_name
    assert definition.version == "1.0.0"
    assert definition.execution.mode.value == "dependency-aware"
    assert [step.id for step in definition.steps] == ["validate", "collect", "summarize"]
    assert [step.action.value for step in definition.steps] == [
        "validate",
        "transform",
        "transform",
    ]
    assert definition.inputs[required_input].required is True
    assert "result" in definition.outputs

    if filename == "retrospective.workflow.yaml":
        assert "session-end" in [event.value for event in definition.triggers.on_event]
    else:
        assert definition.triggers.schedule == expected_source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filename", "inputs", "expected_summary", "markdown_heading"),
    [
        (
            "retrospective.workflow.yaml",
            {
                "session_id": "session-57",
                "scope": "frontend",
                "participants": ["implementer", "reviewer"],
                "wins": ["Live graph refresh shipped."],
                "improvement_areas": ["Tighten workflow preset drift checks."],
            },
            "Retrospective scaffold prepared for session-57",
            "## Retrospective: session-57",
        ),
        (
            "metrics-review.workflow.yaml",
            {
                "review_period": "2026-03-01 to 2026-03-07",
                "focus_areas": ["build-health", "api-alignment"],
                "metrics_snapshot": {"build_pass_rate": "98%", "api_mismatches": 0},
            },
            "Metrics review scaffold prepared for 2026-03-01 to 2026-03-07",
            "## Metrics Review: 2026-03-01 to 2026-03-07",
        ),
    ],
)
async def test_improvement_cycle_templates_execute_deterministically(
    filename: str,
    inputs: dict[str, object],
    expected_summary: str,
    markdown_heading: str,
) -> None:
    definition = WorkflowDefinition.load_from_file(TEMPLATE_DIR / filename)

    result = await WorkflowExecutor(definition).execute(inputs=inputs)

    assert result.status.value == "success"
    assert result.steps_executed == ["validate", "collect", "summarize"]
    scaffold = result.outputs["result"]
    assert scaffold["summary"] == expected_summary
    assert scaffold["status"] == "ready"
    assert markdown_heading in str(scaffold["report_markdown"])

    prompts_key = (
        "action_items"
        if filename == "retrospective.workflow.yaml"
        else "recommendation_prompts"
    )
    prompts = scaffold[prompts_key]
    assert isinstance(prompts, list)
    assert len(prompts) == 2
