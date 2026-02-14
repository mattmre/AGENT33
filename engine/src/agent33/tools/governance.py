"""Tool governance: permission checks, autonomy enforcement, rate limiting, and audit logging."""

from __future__ import annotations

import logging
import re
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from agent33.config import settings
from agent33.security.permissions import check_permission

if TYPE_CHECKING:
    from agent33.agents.definition import AutonomyLevel
    from agent33.tools.base import ToolContext, ToolResult

logger = logging.getLogger(__name__)

# Structured audit log
_audit_logger = logging.getLogger("agent33.tools.audit")

# Patterns that indicate command chaining / subshell injection
_CHAIN_OPERATORS = re.compile(r"[|;&]|&&|\|\|")
_SUBSHELL_PATTERNS = re.compile(r"\$\(|`")

# Tools that perform write/execute operations (blocked in read-only mode)
_WRITE_TOOLS: frozenset[str] = frozenset({"shell", "file_ops", "browser"})
_DESTRUCTIVE_PARAMS: dict[str, set[str]] = {
    "file_ops": {"write"},  # operation=write is destructive
}


class _RateLimiter:
    """Sliding-window rate limiter keyed by subject."""

    def __init__(self, per_minute: int, burst: int) -> None:
        self._per_minute = per_minute
        self._burst = burst
        # subject -> list of timestamps
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, subject: str) -> bool:
        """Return ``True`` if the request is within rate limits."""
        now = time.monotonic()
        window = self._windows[subject]
        # Purge entries older than 60s
        cutoff = now - 60.0
        self._windows[subject] = window = [t for t in window if t > cutoff]

        if len(window) >= self._per_minute:
            return False

        # Burst check: no more than `burst` requests in the last 1 second
        one_sec_ago = now - 1.0
        recent = sum(1 for t in window if t > one_sec_ago)
        if recent >= self._burst:
            return False

        window.append(now)
        return True


class ToolGovernance:
    """Pre-execution permission checks, autonomy enforcement, rate limiting,
    and post-execution audit logging."""

    # Map of tool names to the scope required to invoke them.
    # Tools not listed here default to ``tools:execute``.
    TOOL_SCOPE_MAP: dict[str, str] = {}

    def __init__(self) -> None:
        self._rate_limiter = _RateLimiter(
            per_minute=settings.rate_limit_per_minute,
            burst=settings.rate_limit_burst,
        )

    def pre_execute_check(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: ToolContext,
        autonomy_level: AutonomyLevel | None = None,
    ) -> bool:
        """Return ``True`` if the current context is allowed to run the tool.

        Checks (in order):
        1. Rate limiting (per-subject sliding window).
        2. Autonomy level enforcement.
        3. The user has the required scope (``tools:execute`` by default).
        4. For the shell tool, the command passes multi-segment validation.
        5. For file operations, the path is within the path allowlist.
        6. For web fetch, the domain is in the domain allowlist.
        """
        # --- Rate limiting ---
        subject = context.user_scopes[0] if context.user_scopes else "__anon__"
        if not self._rate_limiter.check(subject):
            logger.warning("Rate limit exceeded for subject=%s", subject)
            return False

        # --- Autonomy level enforcement ---
        if autonomy_level is not None:
            from agent33.agents.definition import AutonomyLevel

            if autonomy_level == AutonomyLevel.READ_ONLY and tool_name in _WRITE_TOOLS:
                logger.warning(
                    "Autonomy denied: tool=%s blocked in read-only mode", tool_name
                )
                return False
            if (
                autonomy_level == AutonomyLevel.SUPERVISED
                and tool_name in _DESTRUCTIVE_PARAMS
            ):
                op = params.get("operation", "")
                if op in _DESTRUCTIVE_PARAMS[tool_name]:
                    logger.info(
                        "Supervised mode: tool=%s operation=%s requires approval",
                        tool_name,
                        op,
                    )
                    # For now, supervised mode logs but allows — full approval
                    # gates are Phase 18 (Autonomy Enforcement).

        # --- Scope check ---
        required_scope = self.TOOL_SCOPE_MAP.get(tool_name, "tools:execute")
        if not check_permission(required_scope, context.user_scopes):
            logger.warning(
                "Permission denied: tool=%s scope=%s user_scopes=%s",
                tool_name,
                required_scope,
                context.user_scopes,
            )
            return False

        # --- Shell: multi-segment command validation ---
        if tool_name == "shell":
            command = params.get("command", "")
            if not self._validate_command(command, context):
                return False

        # --- File ops: path allowlist ---
        if tool_name == "file_ops" and context.path_allowlist:
            path = params.get("path", "")
            if not any(path.startswith(allowed) for allowed in context.path_allowlist):
                logger.warning(
                    "Path not in allowlist: %s (allowed: %s)",
                    path,
                    context.path_allowlist,
                )
                return False

        # --- Web fetch: domain allowlist ---
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

    def _validate_command(self, command: str, context: ToolContext) -> bool:
        """Validate a shell command, checking all segments against the allowlist.

        Multi-segment validation (inspired by ZeroClaw ``security/policy.rs``):
        1. Reject subshell patterns: ``$(...)`` and backticks.
        2. Split on chain operators: ``|``, ``&&``, ``||``, ``;``.
        3. Validate every segment's executable against the allowlist.
        """
        if not command:
            return True

        # Block subshell injection
        if _SUBSHELL_PATTERNS.search(command):
            logger.warning("Subshell injection blocked: %s", command[:100])
            return False

        if not context.command_allowlist:
            # No allowlist configured — allow (governance is opt-in per-agent)
            return True

        # Split on chain operators and validate each segment
        segments = _CHAIN_OPERATORS.split(command)
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            executable = segment.split()[0] if segment.split() else ""
            if executable and executable not in context.command_allowlist:
                logger.warning(
                    "Command not in allowlist: %s (segment of: %s, allowed: %s)",
                    executable,
                    command[:100],
                    context.command_allowlist,
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
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
