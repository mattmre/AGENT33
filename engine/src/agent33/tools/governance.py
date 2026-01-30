"""Tool governance: permission checks and audit logging."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from agent33.security.permissions import check_permission
from agent33.tools.base import ToolContext, ToolResult

logger = logging.getLogger(__name__)

# Structured audit log
_audit_logger = logging.getLogger("agent33.tools.audit")


class ToolGovernance:
    """Pre-execution permission checks and post-execution audit logging."""

    # Map of tool names to the scope required to invoke them.
    # Tools not listed here default to ``tools:execute``.
    TOOL_SCOPE_MAP: dict[str, str] = {}

    def pre_execute_check(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: ToolContext,
    ) -> bool:
        """Return ``True`` if the current context is allowed to run the tool.

        Checks:
        1. The user has the required scope (``tools:execute`` by default).
        2. For the shell tool, the command is in the command allowlist.
        3. For file operations, the path is within the path allowlist.
        4. For web fetch, the domain is in the domain allowlist.
        """
        required_scope = self.TOOL_SCOPE_MAP.get(tool_name, "tools:execute")
        if not check_permission(required_scope, context.user_scopes):
            logger.warning(
                "Permission denied: tool=%s scope=%s user_scopes=%s",
                tool_name,
                required_scope,
                context.user_scopes,
            )
            return False

        if tool_name == "shell" and context.command_allowlist:
            command = params.get("command", "")
            executable = command.split()[0] if command else ""
            if executable not in context.command_allowlist:
                logger.warning(
                    "Command not in allowlist: %s (allowed: %s)",
                    executable,
                    context.command_allowlist,
                )
                return False

        if tool_name == "file_ops" and context.path_allowlist:
            path = params.get("path", "")
            if not any(path.startswith(allowed) for allowed in context.path_allowlist):
                logger.warning(
                    "Path not in allowlist: %s (allowed: %s)",
                    path,
                    context.path_allowlist,
                )
                return False

        if tool_name == "web_fetch" and context.domain_allowlist:
            url = params.get("url", "")
            from urllib.parse import urlparse

            domain = urlparse(url).hostname or ""
            if not any(
                domain == allowed or domain.endswith(f".{allowed}")
                for allowed in context.domain_allowlist
            ):
                logger.warning(
                    "Domain not in allowlist: %s (allowed: %s)",
                    domain,
                    context.domain_allowlist,
                )
                return False

        return True

    def log_execution(
        self,
        tool_name: str,
        params: dict[str, Any],
        result: ToolResult,
    ) -> None:
        """Write a structured audit log entry for a tool execution."""
        _audit_logger.info(
            "tool_execution",
            extra={
                "tool": tool_name,
                "params": params,
                "success": result.success,
                "error": result.error or None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
