"""MCP Proxy Manager: aggregates multiple upstream MCP servers."""

from __future__ import annotations

import logging
from typing import Any

from agent33.mcp_server.proxy_child import ChildServerHandle, ChildServerState
from agent33.mcp_server.proxy_models import ProxyFleetConfig, ProxyServerConfig

logger = logging.getLogger(__name__)

# The separator between prefix and tool name in aggregated tool listings.
DEFAULT_TOOL_SEPARATOR = "__"


class ProxyManager:
    """Central coordinator for the proxy fleet of child MCP servers."""

    def __init__(
        self,
        config: ProxyFleetConfig | None = None,
        tool_separator: str = DEFAULT_TOOL_SEPARATOR,
    ) -> None:
        self._config = config or ProxyFleetConfig()
        self._tool_separator = tool_separator
        self._children: dict[str, ChildServerHandle] = {}
        # Native tool names that should never be shadowed by proxy tools
        self._native_tool_names: set[str] = set()

    # ------------------------------------------------------------------
    # Fleet lifecycle
    # ------------------------------------------------------------------

    async def start_all(self) -> None:
        """Create handles for configured servers and start all enabled ones."""
        for server_cfg in self._config.proxy_servers:
            if server_cfg.id in self._children:
                logger.warning("proxy_duplicate_id: id=%s (skipping)", server_cfg.id)
                continue
            handle = ChildServerHandle(config=server_cfg)
            self._children[server_cfg.id] = handle
            if server_cfg.enabled:
                await handle.start()

    async def stop_all(self) -> None:
        """Stop all child servers in reverse-registration order."""
        for handle in reversed(list(self._children.values())):
            if handle.state != ChildServerState.STOPPED:
                await handle.stop()

    # ------------------------------------------------------------------
    # Server management
    # ------------------------------------------------------------------

    async def add_server(self, config: ProxyServerConfig) -> ChildServerHandle:
        """Add and start a new child server at runtime."""
        if config.id in self._children:
            raise ValueError(f"Proxy server '{config.id}' already registered")

        # Check for tool name collisions before adding
        handle = ChildServerHandle(config=config)
        self._children[config.id] = handle
        if config.enabled:
            await handle.start()
        return handle

    async def remove_server(self, server_id: str) -> bool:
        """Stop and remove a child server.  Returns True if found."""
        handle = self._children.pop(server_id, None)
        if handle is None:
            return False
        if handle.state != ChildServerState.STOPPED:
            await handle.stop()
        return True

    def get_server(self, server_id: str) -> ChildServerHandle | None:
        """Return a specific child server handle."""
        return self._children.get(server_id)

    def list_servers(self) -> list[dict[str, Any]]:
        """Return status summaries for all child servers."""
        return [h.status_summary() for h in self._children.values()]

    # ------------------------------------------------------------------
    # Native tool registration (collision avoidance)
    # ------------------------------------------------------------------

    def set_native_tool_names(self, names: set[str]) -> None:
        """Register native AGENT-33 tool names to prevent proxy collisions."""
        self._native_tool_names = names

    # ------------------------------------------------------------------
    # Aggregated tool listing
    # ------------------------------------------------------------------

    def list_aggregated_tools(self) -> list[dict[str, Any]]:
        """Return all tools from all healthy children with prefixes applied."""
        tools: list[dict[str, Any]] = []
        for handle in self._children.values():
            if handle.state not in (ChildServerState.HEALTHY, ChildServerState.DEGRADED):
                continue
            prefix = handle.config.effective_prefix()
            for tool in handle.list_tools():
                prefixed_name = f"{prefix}{self._tool_separator}{tool.name}"
                tools.append(
                    {
                        "name": prefixed_name,
                        "description": f"[{prefix}] {tool.description}",
                        "inputSchema": tool.input_schema,
                        "proxy_server_id": handle.config.id,
                        "original_name": tool.name,
                    }
                )
        return tools

    def check_collisions(self) -> list[str]:
        """Check for tool name collisions across all children and native tools.

        Returns a list of collision descriptions (empty if clean).
        """
        collisions: list[str] = []
        seen: dict[str, str] = {}  # prefixed_name -> server_id

        for handle in self._children.values():
            prefix = handle.config.effective_prefix()
            for tool in handle.list_tools():
                prefixed_name = f"{prefix}{self._tool_separator}{tool.name}"
                if prefixed_name in self._native_tool_names:
                    collisions.append(
                        f"Proxy tool '{prefixed_name}' from server '{handle.config.id}' "
                        f"collides with native tool"
                    )
                elif prefixed_name in seen:
                    collisions.append(
                        f"Proxy tool '{prefixed_name}' from server '{handle.config.id}' "
                        f"collides with server '{seen[prefixed_name]}'"
                    )
                else:
                    seen[prefixed_name] = handle.config.id
        return collisions

    # ------------------------------------------------------------------
    # Tool routing
    # ------------------------------------------------------------------

    def resolve_server_for_tool(
        self, prefixed_tool_name: str
    ) -> tuple[ChildServerHandle, str] | None:
        """Map a prefixed tool name to (child, unprefixed_name).

        Returns None if no matching server is found.
        """
        for handle in self._children.values():
            if handle.state not in (ChildServerState.HEALTHY, ChildServerState.DEGRADED):
                continue
            prefix = handle.config.effective_prefix()
            expected_prefix = f"{prefix}{self._tool_separator}"
            if prefixed_tool_name.startswith(expected_prefix):
                unprefixed = prefixed_tool_name[len(expected_prefix) :]
                if unprefixed in handle.discovered_tools:
                    return handle, unprefixed
        return None

    async def call_proxy_tool(
        self,
        prefixed_tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Route a tool call to the correct child server."""
        resolved = self.resolve_server_for_tool(prefixed_tool_name)
        if resolved is None:
            raise ValueError(f"No proxy server found for tool '{prefixed_tool_name}'")
        handle, unprefixed_name = resolved
        return await handle.call_tool(unprefixed_name, arguments)

    # ------------------------------------------------------------------
    # Health summary
    # ------------------------------------------------------------------

    def health_summary(self) -> dict[str, Any]:
        """Return a fleet-level health summary."""
        total = len(self._children)
        healthy = sum(1 for h in self._children.values() if h.state == ChildServerState.HEALTHY)
        degraded = sum(1 for h in self._children.values() if h.state == ChildServerState.DEGRADED)
        unhealthy = sum(
            1
            for h in self._children.values()
            if h.state in (ChildServerState.UNHEALTHY, ChildServerState.COOLDOWN)
        )
        return {
            "total": total,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "stopped": total - healthy - degraded - unhealthy,
        }
