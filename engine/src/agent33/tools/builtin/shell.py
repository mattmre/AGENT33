"""Shell command execution tool."""

from __future__ import annotations

import asyncio
import shlex
from typing import Any

from agent33.tools.base import ToolContext, ToolResult

_DEFAULT_TIMEOUT = 30


class ShellTool:
    """Execute shell commands with allowlist enforcement and timeout."""

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Run a shell command and capture its output."

    async def execute(self, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Run a shell command.

        Parameters
        ----------
        params:
            command : str  - The command string to execute.
            timeout : int  - Max seconds to wait (default 30).
        context:
            command_allowlist and working_dir are respected.
        """
        command: str = params.get("command", "").strip()
        if not command:
            return ToolResult.fail("No command provided")

        timeout: int = params.get("timeout", _DEFAULT_TIMEOUT)

        # Parse the executable name for allowlist checking
        try:
            parts = shlex.split(command)
        except ValueError as exc:
            return ToolResult.fail(f"Invalid command syntax: {exc}")

        executable = parts[0]
        if context.command_allowlist and executable not in context.command_allowlist:
            return ToolResult.fail(
                f"Command '{executable}' is not in the allowlist. "
                f"Allowed: {', '.join(context.command_allowlist)}"
            )

        try:
            proc = await asyncio.create_subprocess_exec(
                *parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(context.working_dir),
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()  # type: ignore[union-attr]
            return ToolResult.fail(f"Command timed out after {timeout}s")
        except FileNotFoundError:
            return ToolResult.fail(f"Command not found: {executable}")
        except OSError as exc:
            return ToolResult.fail(f"OS error: {exc}")

        stdout_text = stdout.decode(errors="replace")
        stderr_text = stderr.decode(errors="replace")

        if proc.returncode != 0:
            return ToolResult(
                success=False,
                output=stdout_text,
                error=f"Exit code {proc.returncode}: {stderr_text}",
            )
        return ToolResult.ok(stdout_text + stderr_text)
