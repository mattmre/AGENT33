"""Unified model health setup UX routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from agent33.api.routes.lm_studio import get_lm_studio_readiness_service
from agent33.api.routes.ollama import get_ollama_readiness_service
from agent33.security.permissions import require_scope
from agent33.services.model_health import (
    ModelHealthService,
    UnifiedModelHealthResponse,
)

router = APIRouter(prefix="/v1/model-health", tags=["model-health"])


def get_model_health_service(
    ollama_service: Annotated[
        Any,
        Depends(get_ollama_readiness_service),
    ],
    lm_studio_service: Annotated[
        Any,
        Depends(get_lm_studio_readiness_service),
    ],
) -> ModelHealthService:
    """Return a request-local aggregate over shared readiness services."""

    return ModelHealthService(
        ollama_service=ollama_service,
        lm_studio_service=lm_studio_service,
    )


ModelHealthDependency = Annotated[
    ModelHealthService,
    Depends(get_model_health_service),
]


@router.get(
    "",
    response_model=UnifiedModelHealthResponse,
    dependencies=[require_scope("operator:read")],
)
async def local_model_health(
    svc: ModelHealthDependency,
    ollama_base_url: str | None = Query(default=None),
    lm_studio_base_url: str | None = Query(default=None),
) -> UnifiedModelHealthResponse:
    """Return combined Ollama and LM Studio readiness for setup UI."""

    return await svc.status(
        ollama_base_url=ollama_base_url,
        lm_studio_base_url=lm_studio_base_url,
    )
