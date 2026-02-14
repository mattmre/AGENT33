"""Agent management and invocation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from agent33.agents.capabilities import get_catalog_by_category
from agent33.agents.definition import (
    AgentDefinition,
    AgentRole,
    AgentStatus,
    CapabilityCategory,
    SpecCapability,
)
from agent33.agents.registry import AgentRegistry
from agent33.agents.runtime import AgentRuntime
from agent33.config import settings
from agent33.llm.ollama import OllamaProvider
from agent33.llm.router import ModelRouter
from agent33.security.injection import scan_inputs_recursive
from agent33.security.permissions import require_scope

router = APIRouter(prefix="/v1/agents", tags=["agents"])

# -- singletons ----------------------------------------------------------

_model_router = ModelRouter()
_model_router.register("ollama", OllamaProvider(
    base_url=settings.ollama_base_url,
    default_model=settings.ollama_default_model,
))

if settings.openai_api_key.get_secret_value():
    from agent33.llm.openai import OpenAIProvider

    _openai_kwargs: dict[str, Any] = {"api_key": settings.openai_api_key.get_secret_value()}
    if settings.openai_base_url:
        _openai_kwargs["base_url"] = settings.openai_base_url
    _model_router.register("openai", OpenAIProvider(**_openai_kwargs))


# -- dependency injection -------------------------------------------------


def get_registry(request: Request) -> AgentRegistry:
    """Return the shared registry from app state, or a fresh empty one."""
    registry = getattr(request.app.state, "agent_registry", None)
    if registry is None:
        registry = AgentRegistry()
    return registry


# -- request / response models -------------------------------------------


class InvokeRequest(BaseModel):
    """Body for the invoke endpoint."""

    inputs: dict[str, Any] = {}
    model: str | None = None
    temperature: float = 0.7


class InvokeResponse(BaseModel):
    """Response from the invoke endpoint."""

    agent: str
    output: dict[str, Any]
    tokens_used: int
    model: str


# -- routes ---------------------------------------------------------------


@router.get("/capabilities/catalog")
async def capabilities_catalog() -> dict[str, list[dict[str, str]]]:
    """Return the full spec capability taxonomy grouped by category."""
    return get_catalog_by_category()


@router.get("/search", dependencies=[require_scope("agents:read")])
async def search_agents(
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
    role: str | None = Query(default=None, description="Filter by role"),
    spec_capability: str | None = Query(
        default=None, description="Filter by spec capability ID",
    ),
    category: str | None = Query(
        default=None, description="Filter by capability category",
    ),
    status: str | None = Query(
        default=None, description="Filter by lifecycle status",
    ),
) -> list[dict[str, Any]]:
    """Search agents with multi-criteria AND filtering."""
    try:
        parsed_role = AgentRole(role) if role else None
        parsed_cap = SpecCapability(spec_capability) if spec_capability else None
        parsed_cat = CapabilityCategory(category) if category else None
        parsed_status = AgentStatus(status) if status else None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    results = registry.search(
        role=parsed_role,
        spec_capability=parsed_cap,
        category=parsed_cat,
        status=parsed_status,
    )
    return [_agent_summary(d) for d in results]


@router.get("/by-id/{agent_id}", dependencies=[require_scope("agents:read")])
async def get_agent_by_id(
    agent_id: str,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> dict[str, Any]:
    """Look up an agent by its spec ID (e.g. AGT-001)."""
    definition = registry.get_by_agent_id(agent_id)
    if definition is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent with ID '{agent_id}' not found",
        )
    return definition.model_dump(mode="json")


@router.get("/", dependencies=[require_scope("agents:read")])
async def list_agents(
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> list[dict[str, Any]]:
    """List all registered agent definitions."""
    return [_agent_summary(d) for d in registry.list_all()]


@router.get("/{name}", dependencies=[require_scope("agents:read")])
async def get_agent(
    name: str,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> dict[str, Any]:
    """Return the full definition for a single agent."""
    definition = registry.get(name)
    if definition is None:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return definition.model_dump(mode="json")


@router.post("/", status_code=201, dependencies=[require_scope("agents:write")])
async def register_agent(
    definition: AgentDefinition,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> dict[str, str]:
    """Register a new agent definition."""
    registry.register(definition)
    return {"status": "registered", "name": definition.name}


@router.post("/{name}/invoke", dependencies=[require_scope("agents:invoke")])
async def invoke_agent(
    name: str,
    body: InvokeRequest,
    request: Request,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> InvokeResponse:
    """Invoke a registered agent with the given inputs."""
    definition = registry.get(name)
    if definition is None:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    # Scan inputs for prompt injection (recursive to catch nested payloads)
    scan = scan_inputs_recursive(body.inputs)
    if not scan.is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Input rejected: {', '.join(scan.threats)}",
        )

    # Pull subsystems from app state for agent runtime
    skill_injector = getattr(request.app.state, "skill_injector", None)
    progressive_recall = getattr(request.app.state, "progressive_recall", None)

    runtime = AgentRuntime(
        definition=definition,
        router=_model_router,
        model=body.model,
        temperature=body.temperature,
        skill_injector=skill_injector,
        progressive_recall=progressive_recall,
    )

    try:
        result = await runtime.invoke(body.inputs)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return InvokeResponse(
        agent=name,
        output=result.output,
        tokens_used=result.tokens_used,
        model=result.model,
    )


# -- helpers --------------------------------------------------------------


def _agent_summary(d: AgentDefinition) -> dict[str, Any]:
    return {
        "name": d.name,
        "version": d.version,
        "role": d.role.value,
        "description": d.description,
        "agent_id": d.agent_id,
        "spec_capabilities": [c.value for c in d.spec_capabilities],
        "status": d.status.value,
    }
