"""Base tool protocol and shared types."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclasses.dataclass(frozen=True, slots=True)
class ToolContext:
    """Execution context passed to every tool invocation."""

    user_scopes: list[str] = dataclasses.field(default_factory=list)
    command_allowlist: list[str] = dataclasses.field(default_factory=list)
    path_allowlist: list[str] = dataclasses.field(default_factory=list)
    domain_allowlist: list[str] = dataclasses.field(default_factory=list)
    working_dir: Path = dataclasses.field(default_factory=Path.cwd)


@dataclasses.dataclass(frozen=True, slots=True)
class ToolResult:
    """Result returned from a tool execution."""

    success: bool
    output: str = ""
    error: str = ""

    @staticmethod
    def ok(output: str = "") -> ToolResult:
        return ToolResult(success=True, output=output)

    @staticmethod
    def fail(error: str) -> ToolResult:
        return ToolResult(success=False, error=error)


@runtime_checkable
class Tool(Protocol):
    """Protocol that all tools must implement."""

    @property
    def name(self) -> str:
        """Unique tool identifier."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what this tool does."""
        ...

    async def execute(self, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Run the tool with the given parameters and context."""
        ...
