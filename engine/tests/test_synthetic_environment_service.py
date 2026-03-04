"""Tests for the A5 synthetic environment generation service."""

from __future__ import annotations

from pathlib import Path

from agent33.evaluation.synthetic_envs.service import SyntheticEnvironmentService


def _service() -> SyntheticEnvironmentService:
    root = Path(__file__).resolve().parents[1]
    return SyntheticEnvironmentService(
        workflow_dir=root / "workflow-definitions",
        tool_dir=root / "tool-definitions",
    )


def test_workflow_catalog_discovers_synthetic_templates() -> None:
    service = _service()

    catalog = service.list_workflows()
    names = {entry.workflow_name for entry in catalog}

    assert "code-review-pipeline" in names
    assert "incident-triage-loop" in names
    assert "release-readiness-gate" in names


def test_generate_bundle_builds_requested_variants() -> None:
    service = _service()

    bundle = service.generate_bundle(
        workflow_names=["release-readiness-gate"],
        variations_per_workflow=2,
    )

    assert bundle.source_workflows == ["release-readiness-gate"]
    assert len(bundle.environments) == 2

    environment = bundle.environments[0]
    assert environment.workflow_name == "release-readiness-gate"
    assert environment.variant_index == 1
    assert "shell" in environment.inferred_tool_ids
    assert environment.tasks
    assert environment.verification_queries
    assert any(
        "CREATE TABLE workflow_context" in statement for statement in environment.initial_state_sql
    )


def test_generated_bundle_is_retrievable_from_service_store() -> None:
    service = _service()

    bundle = service.generate_bundle(
        workflow_names=["incident-triage-loop"],
        variations_per_workflow=1,
    )

    stored = service.get_bundle(bundle.bundle_id)
    assert stored is not None
    assert stored.bundle_id == bundle.bundle_id


def test_unknown_workflow_name_is_rejected() -> None:
    service = _service()

    try:
        service.generate_bundle(workflow_names=["does-not-exist"], variations_per_workflow=1)
    except ValueError as exc:
        assert "Unknown workflow templates" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown workflow")
