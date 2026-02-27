"""Action that invokes an agent by name from a registry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from agent33.agents.registry import AgentRegistry

logger = structlog.get_logger()

# Simple in-process agent registry. External modules register callables here.
_agent_registry: dict[str, Any] = {}

# Optional bridge to the main AgentRegistry (set during app startup).
_definition_registry: AgentRegistry | None = None


def set_definition_registry(registry: AgentRegistry) -> None:
    """Wire the main AgentRegistry so workflow steps can look up agents."""
    global _definition_registry  # noqa: PLW0603
    _definition_registry = registry


def register_agent(name: str, handler: Any) -> None:
    """Register an agent handler callable.

    Args:
        name: Agent name used in workflow step definitions.
        handler: An async callable accepting (inputs: dict) -> dict.
    """
    _agent_registry[name] = handler


def get_agent(name: str) -> Any:
    """Retrieve a registered agent handler by name.

    Falls back to the definition registry if no explicit handler exists.

    Raises:
        KeyError: If the agent is not registered anywhere.
    """
    if name in _agent_registry:
        return _agent_registry[name]

    if _definition_registry is not None:
        defn = _definition_registry.get(name)
        if defn is not None:
            return defn

    raise KeyError(f"Agent '{name}' is not registered in the workflow agent registry")


async def execute(
    agent: str | None,
    inputs: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """Invoke a named agent with the given inputs.

    Args:
        agent: Name of the agent to invoke.
        inputs: Input data to pass to the agent.
        dry_run: If True, log but skip actual execution.

    Returns:
        A dict containing the agent's output.

    Raises:
        ValueError: If agent name is not provided.
        KeyError: If the agent is not found in the registry.
    """
    if not agent:
        raise ValueError("invoke-agent action requires an 'agent' field")

    logger.info("invoke_agent", agent=agent, dry_run=dry_run)

    if dry_run:
        return {"dry_run": True, "agent": agent, "inputs": inputs}

    handler = get_agent(agent)
    result = await handler(inputs)

    if not isinstance(result, dict):
        result = {"result": result}

    logger.info("invoke_agent_complete", agent=agent, output_keys=list(result.keys()))
    return result
