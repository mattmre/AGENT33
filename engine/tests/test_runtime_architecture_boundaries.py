"""Tests for the Cluster 0.1 runtime import-boundary contract."""

from __future__ import annotations

from pathlib import Path

from agent33.testing.import_boundaries import (
    collect_allowlisted_importers,
    evaluate_runtime_boundaries,
    format_violations,
)


def test_runtime_import_boundaries_match_current_tree() -> None:
    package_root = Path(__file__).resolve().parents[1] / "src" / "agent33"
    violations = evaluate_runtime_boundaries(package_root)
    assert not violations, format_violations(violations)


def test_runtime_boundary_allowlist_stays_explicit_and_small() -> None:
    assert collect_allowlisted_importers() == {
        "agent33.api.routes.training",
        "agent33.services.operations_hub",
    }
