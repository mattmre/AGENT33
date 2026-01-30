"""Agent management and invocation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent33.agents.definition import AgentDefinition
from agent33.agents.registry import AgentRegistry
from agent33.agents.runtime import AgentRuntime
from agent33.config import settings
from agent33.llm.ollama import OllamaProvider
from agent33.llm.router import ModelRouter

router = APIRouter(prefix="/v1/agents", tags=["agents"])

# -- singletons ----------------------------------------------------------

_registry = AgentRegistry()

_model_router = ModelRouter()
_model_router.register("ollama", OllamaProvider(
    base_url=settings.ollama_base_url,
    default_model=settings.ollama_default_model,
))

if settings.openai_api_key:
    from agent33.llm.openai import OpenAIProvider

    _openai_kwargs: dict[str, Any] = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        _openai_kwargs["base_url"] = settings.openai_base_url
    _model_router.register("openai", OpenAIProvider(**_openai_kwargs))

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


@router.get("/")
async def list_agents() -> list[dict[str, Any]]:
    """List all registered agent definitions."""
    return [
        {
            "name": d.name,
            "version": d.version,
            "role": d.role.value,
            "description": d.description,
        }
        for d in _registry.list_all()
    ]


@router.get("/{name}")
async def get_agent(name: str) -> dict[str, Any]:
    """Return the full definition for a single agent."""
    definition = _registry.get(name)
    if definition is None:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return definition.model_dump(mode="json")


@router.post("/", status_code=201)
async def register_agent(definition: AgentDefinition) -> dict[str, str]:
    """Register a new agent definition."""
    _registry.register(definition)
    return {"status": "registered", "name": definition.name}


@router.post("/{name}/invoke")
async def invoke_agent(name: str, body: InvokeRequest) -> InvokeResponse:
    """Invoke a registered agent with the given inputs."""
    definition = _registry.get(name)
    if definition is None:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    runtime = AgentRuntime(
        definition=definition,
        router=_model_router,
        model=body.model,
        temperature=body.temperature,
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
