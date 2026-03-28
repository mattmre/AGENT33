"""Tests for canonical runtime durable state roots."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agent33.state_paths import RuntimeStatePaths, StatePathError, StateRootKind

if TYPE_CHECKING:
    from pathlib import Path


def test_resolve_repo_relative_var_path(tmp_path: Path) -> None:
    state_paths = RuntimeStatePaths.from_app_root(tmp_path, home_dir=tmp_path / "home")

    resolved = state_paths.resolve_approved("var/process-manager")

    assert resolved == (tmp_path / "var" / "process-manager").resolve()
    assert state_paths.classify(resolved) == StateRootKind.APP_VAR


def test_default_user_state_dir_uses_home_override(tmp_path: Path) -> None:
    state_paths = RuntimeStatePaths.from_app_root(tmp_path, home_dir=tmp_path / "home")

    assert (
        state_paths.default_user_state_dir("sessions")
        == (tmp_path / "home" / ".agent33" / "sessions").resolve()
    )


def test_resolve_repo_relative_trajectory_dir_is_approved(tmp_path: Path) -> None:
    state_paths = RuntimeStatePaths.from_app_root(tmp_path, home_dir=tmp_path / "home")

    resolved = state_paths.resolve_approved("trajectories")

    assert resolved == (tmp_path / "trajectories").resolve()
    assert state_paths.classify(resolved) == StateRootKind.APP_ROOT


def test_reject_path_outside_approved_roots(tmp_path: Path) -> None:
    outside_root = tmp_path.parent / "outside"
    state_paths = RuntimeStatePaths.from_app_root(tmp_path, home_dir=tmp_path / "home")

    with pytest.raises(StatePathError):
        state_paths.resolve_approved(outside_root / "escape.json")
