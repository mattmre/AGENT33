"""Tool governance: permission checks, autonomy enforcement, rate limiting, and audit logging."""

from __future__ import annotations

import fnmatch
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
        0. Tool-specific governance policies (from context.tool_policies).
        1. Rate limiting (per-subject sliding window).
        2. Autonomy level enforcement.
        3. The user has the required scope (``tools:execute`` by default).
        4. For the shell tool, the command passes multi-segment validation.
        5. For file operations, the path is within the path allowlist.
        6. For web fetch, the domain is in the domain allowlist.
        """
        # --- Tool-specific governance policies ---
        if context.tool_policies:
            policy_result = self._check_tool_policy(tool_name, params, context)
            if policy_result is not None:
                # Policy explicitly allowed, denied, or asked
                if policy_result == "deny":
                    logger.warning("Tool policy denied: tool=%s", tool_name)
                    return False
                if policy_result == "ask":
                    logger.info(
                        "Tool policy requires approval: tool=%s (blocking for now)",
                        tool_name,
                    )
                    return False
                # "allow" continues to normal checks

        # --- Rate limiting ---
        subject = context.user_scopes[0] if context.user_scopes else "__anon__"
        if not self._rate_limiter.check(subject):
            logger.warning("Rate limit exceeded for subject=%s", subject)
            return False

        # --- Autonomy level enforcement ---
        if autonomy_level is not None:
            from agent33.agents.definition import AutonomyLevel

            if autonomy_level == AutonomyLevel.READ_ONLY and tool_name in _WRITE_TOOLS:
                logger.warning("Autonomy denied: tool=%s blocked in read-only mode", tool_name)
                return False
            if autonomy_level == AutonomyLevel.SUPERVISED and tool_name in _DESTRUCTIVE_PARAMS:
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

    def _check_tool_policy(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: ToolContext,
    ) -> str | None:
        """Evaluate tool_policies for this tool invocation.

        Returns:
            "allow" if explicitly allowed
            "deny" if explicitly denied
            "ask" if requires approval
            None if no matching policy (continue to normal checks)

        Policy keys support:
        - Exact tool name: "shell"
        - Wildcard tool pattern: "file_*", "*"
        - Tool with operation suffix: "file_ops:write", "file_ops:*"

        Precedence (most specific to least):
        1. Exact operation match: "file_ops:write"
        2. Exact tool match: "file_ops"
        3. Wildcard operation match: "file_*:write"
        4. Wildcard tool match: "file_*"
        5. Global wildcard: "*"
        """
        policies = context.tool_policies
        if not policies:
            return None

        operation = params.get("operation")

        # 1. Check exact operation match first (most specific)
        if operation:
            exact_op_key = f"{tool_name}:{operation}"
            if exact_op_key in policies:
                return policies[exact_op_key].lower()

            exact_wildcard_op_key = f"{tool_name}:*"
            if exact_wildcard_op_key in policies:
                return policies[exact_wildcard_op_key].lower()

        # 2. Check exact tool name match
        if tool_name in policies:
            return policies[tool_name].lower()

        # 3. Check wildcard operation patterns (sorted by length for specificity)
        if operation:
            wildcard_op_keys = [
                k for k in policies if ":" in k and ("*" in k or "?" in k or "[" in k)
            ]
            wildcard_op_keys.sort(key=len, reverse=True)

            for pattern_key in wildcard_op_keys:
                parts = pattern_key.split(":", 1)
                if len(parts) == 2:
                    tool_pattern, op_pattern = parts
                    if fnmatch.fnmatch(tool_name, tool_pattern) and (
                        op_pattern == "*" or fnmatch.fnmatch(operation, op_pattern)
                    ):
                        return policies[pattern_key].lower()

        # 4. Check wildcard tool patterns (sorted by length for specificity)
        wildcard_tool_keys = [
            k for k in policies if ":" not in k and ("*" in k or "?" in k or "[" in k) and k != "*"
        ]
        wildcard_tool_keys.sort(key=len, reverse=True)

        for pattern in wildcard_tool_keys:
            if fnmatch.fnmatch(tool_name, pattern):
                return policies[pattern].lower()

        # 5. Check global wildcard (least specific)
        if "*" in policies:
            return policies["*"].lower()

        return None

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
