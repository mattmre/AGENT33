"""Tests for lightweight repo-ingestion task artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from agent33.improvement.ingestion_artifacts import (
    IngestionTaskArtifact,
    IngestionTaskStatus,
    build_repo_ingestion_task_artifact,
)
from agent33.improvement.repo_ingestion import RepoHarvestRecord


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_ingestion_task_artifact_round_trips_markdown() -> None:
    artifact = IngestionTaskArtifact(
        task_id="ING-abc123def456",
        title="Ingest example/repo",
        owner="codex",
        status=IngestionTaskStatus.IN_PROGRESS,
        target="example/repo",
        summary="Track one repo-ingestion effort without creating a ticket system.",
        acceptance_criteria=["Keep the artifact small and auditable."],
        evidence=["docs/research/example.md"],
        planning_refs=["task_plan.md", "findings.md", "progress.md"],
        research_refs=["docs/phases/ROADMAP-REBASE-2026-03-26.md"],
        body="# Outcome\n\nStill running.",
    )

    parsed = IngestionTaskArtifact.from_markdown(artifact.to_markdown())

    assert parsed == artifact


def test_ingestion_task_artifact_write_and_load(tmp_path: Path) -> None:
    artifact = IngestionTaskArtifact(
        task_id="ING-feedfacecafe",
        title="Remediate example/repo",
        owner="codex",
        target="example/repo",
        planning_refs=["task_plan.md"],
    )
    path = tmp_path / artifact.suggested_filename()

    artifact.write(path)
    loaded = IngestionTaskArtifact.load(path)

    assert path.name == "ing-feedfacecafe-example-repo.md"
    assert loaded.task_id == artifact.task_id
    assert loaded.target == "example/repo"


def test_build_repo_ingestion_task_artifact_sets_minimal_defaults() -> None:
    record = RepoHarvestRecord(
        rank=2,
        full_name="org/project",
        url="https://github.com/org/project",
        stars=100,
        source_query="agent runtime",
    )

    artifact = build_repo_ingestion_task_artifact(record, owner="codex")

    assert artifact.title == "Ingest org/project"
    assert artifact.owner == "codex"
    assert artifact.target == "org/project"
    assert artifact.evidence == ["https://github.com/org/project"]
    assert artifact.planning_refs == ["task_plan.md", "findings.md", "progress.md"]
    assert len(artifact.acceptance_criteria) == 3


def test_ingestion_task_artifact_rejects_blank_required_fields() -> None:
    with pytest.raises(ValidationError):
        IngestionTaskArtifact(
            task_id="ING-blankowner",
            title="Valid title",
            owner="",
            target="example/repo",
        )


def test_ingestion_template_documents_required_fields() -> None:
    template_path = _repo_root() / "docs" / "research" / "templates" / "INGESTION_TASK_TEMPLATE.md"
    template = template_path.read_text(encoding="utf-8")

    for field in (
        "task_id:",
        "owner:",
        "status:",
        "acceptance_criteria:",
        "evidence:",
        "planning_refs:",
    ):
        assert field in template
    assert "task_plan.md" in template
    assert "findings.md" in template
    assert "progress.md" in template


def test_example_ingestion_task_is_parseable_and_linked_to_planning_files() -> None:
    artifact_path = (
        _repo_root() / "docs" / "research" / "codex-autorunner-ingestion-task-2026-03-28.md"
    )
    artifact = IngestionTaskArtifact.load(artifact_path)

    assert artifact.status is IngestionTaskStatus.COMPLETED
    assert artifact.target == "Git-on-my-level/codex-autorunner"
    assert "task_plan.md" in artifact.planning_refs
    assert "findings.md" in artifact.planning_refs
    assert "progress.md" in artifact.planning_refs
    assert "docs/research/codex-autorunner-adaptive-ingestion-2026-03-28.md" in artifact.evidence
