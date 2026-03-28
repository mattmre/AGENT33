"""Approved durable state roots for repo-local and user-local runtime data."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class StateRootKind(StrEnum):
    """Canonical durable state roots used by the runtime."""

    APP_ROOT = "app_root"
    APP_VAR = "app_var"
    USER_STATE = "user_state"


class StatePathError(ValueError):
    """Raised when a path escapes the approved durable state roots."""


@dataclass(frozen=True, slots=True)
class RuntimeStatePaths:
    """Resolve and classify paths against the approved runtime roots."""

    app_root: Path
    app_var_dir: Path
    user_state_dir: Path

    @classmethod
    def from_app_root(
        cls,
        app_root: Path,
        *,
        home_dir: Path | None = None,
    ) -> RuntimeStatePaths:
        resolved_app_root = app_root.resolve()
        resolved_home = (home_dir or Path.home()).expanduser().resolve()
        return cls(
            app_root=resolved_app_root,
            app_var_dir=(resolved_app_root / "var").resolve(),
            user_state_dir=(resolved_home / ".agent33").resolve(),
        )

    @property
    def approved_roots(self) -> tuple[Path, Path, Path]:
        """Return approved durable roots from most-specific to least-specific."""
        return (self.app_var_dir, self.user_state_dir, self.app_root)

    def resolve(self, raw_path: str | Path) -> Path:
        """Resolve a candidate path relative to the repo root when needed."""
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = self.app_root / candidate
        return candidate.resolve()

    def classify(self, raw_path: str | Path) -> StateRootKind | None:
        """Classify a resolved path by its durable root."""
        resolved = self.resolve(raw_path)
        if resolved.is_relative_to(self.app_var_dir):
            return StateRootKind.APP_VAR
        if resolved.is_relative_to(self.user_state_dir):
            return StateRootKind.USER_STATE
        if resolved.is_relative_to(self.app_root):
            return StateRootKind.APP_ROOT
        return None

    def ensure_approved(self, raw_path: str | Path) -> Path:
        """Return the resolved path or raise when it escapes approved roots."""
        resolved = self.resolve(raw_path)
        if self.classify(resolved) is None:
            approved = ", ".join(str(root) for root in self.approved_roots)
            raise StatePathError(
                f"Path '{resolved}' is outside approved runtime roots: {approved}"
            )
        return resolved

    def resolve_approved(self, raw_path: str | Path) -> Path:
        """Resolve a candidate path and require it to stay inside approved roots."""
        return self.ensure_approved(raw_path)

    def default_user_state_dir(self, name: str) -> Path:
        """Return a directory under the canonical user-local state root."""
        resolved = (self.user_state_dir / name).resolve()
        if not resolved.is_relative_to(self.user_state_dir):
            raise StatePathError(
                f"User state path '{resolved}' escapes user_state_dir '{self.user_state_dir}'"
            )
        return resolved
