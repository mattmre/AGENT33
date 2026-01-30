"""File operations tool with path allowlist enforcement."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from agent33.tools.base import ToolContext, ToolResult


class FileOpsTool:
    """Read, write, and list files within allowed paths."""

    @property
    def name(self) -> str:
        return "file_ops"

    @property
    def description(self) -> str:
        return "Read, write, or list files on the local filesystem."

    async def execute(self, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Run a file operation.

        Parameters
        ----------
        params:
            operation : str  - One of 'read', 'write', 'list'.
            path      : str  - Target file or directory path.
            content   : str  - Content to write (for 'write' operation).
        """
        operation: str = params.get("operation", "").strip()
        raw_path: str = params.get("path", "").strip()

        if not operation:
            return ToolResult.fail("No operation specified (read, write, list)")
        if not raw_path:
            return ToolResult.fail("No path specified")

        resolved = Path(raw_path).resolve()

        if not self._path_allowed(resolved, context):
            return ToolResult.fail(
                f"Path '{resolved}' is outside the allowed directories: "
                f"{context.path_allowlist}"
            )

        if operation == "read":
            return await self._read(resolved)
        if operation == "write":
            content: str = params.get("content", "")
            return await self._write(resolved, content)
        if operation == "list":
            return await self._list(resolved)
        return ToolResult.fail(f"Unknown operation: {operation}")

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    async def _read(self, path: Path) -> ToolResult:
        try:
            text = path.read_text(encoding="utf-8")
            return ToolResult.ok(text)
        except FileNotFoundError:
            return ToolResult.fail(f"File not found: {path}")
        except OSError as exc:
            return ToolResult.fail(f"Read error: {exc}")

    async def _write(self, path: Path, content: str) -> ToolResult:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return ToolResult.ok(f"Wrote {len(content)} bytes to {path}")
        except OSError as exc:
            return ToolResult.fail(f"Write error: {exc}")

    async def _list(self, path: Path) -> ToolResult:
        try:
            if path.is_file():
                stat = path.stat()
                return ToolResult.ok(
                    f"{path.name}  ({stat.st_size} bytes, modified {stat.st_mtime})"
                )
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            lines = []
            for entry in entries:
                kind = "dir" if entry.is_dir() else "file"
                lines.append(f"{kind}  {entry.name}")
            return ToolResult.ok("\n".join(lines) if lines else "(empty directory)")
        except FileNotFoundError:
            return ToolResult.fail(f"Path not found: {path}")
        except OSError as exc:
            return ToolResult.fail(f"List error: {exc}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _path_allowed(resolved: Path, context: ToolContext) -> bool:
        """Check that *resolved* falls within one of the allowed paths."""
        if not context.path_allowlist:
            return True
        resolved_str = str(resolved)
        return any(
            resolved_str.startswith(str(Path(allowed).resolve()))
            for allowed in context.path_allowlist
        )
