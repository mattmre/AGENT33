"""FastAPI router for explanation generation and management."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, HTTPException

from agent33.explanation.fact_check import run_fact_check_hooks
from agent33.explanation.models import ExplanationMetadata, ExplanationRequest
from agent33.security.permissions import require_scope

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/explanations", tags=["explanations"])
_explanations: dict[str, ExplanationMetadata] = {}


@router.post("/", dependencies=[require_scope("workflows:write")], status_code=201)
async def create_explanation(request: ExplanationRequest) -> ExplanationMetadata:
    """Generate a new explanation scaffold for an entity."""
    explanation_id = f"expl-{uuid.uuid4().hex[:12]}"
    explanation = ExplanationMetadata(
        id=explanation_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        content=f"Explanation for {request.entity_type} '{request.entity_id}'",
        metadata=request.metadata,
    )

    explanation.fact_check_status = await run_fact_check_hooks(explanation)
    _explanations[explanation_id] = explanation

    logger.info(
        "explanation_created",
        explanation_id=explanation_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        fact_check_status=explanation.fact_check_status,
    )
    return explanation


@router.get("/{explanation_id}", dependencies=[require_scope("workflows:read")])
async def get_explanation(explanation_id: str) -> ExplanationMetadata:
    """Retrieve an explanation by ID."""
    explanation = _explanations.get(explanation_id)
    if explanation is None:
        raise HTTPException(status_code=404, detail=f"Explanation '{explanation_id}' not found")

    logger.info("explanation_retrieved", explanation_id=explanation_id)
    return explanation


@router.get("/", dependencies=[require_scope("workflows:read")])
async def list_explanations(
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> list[ExplanationMetadata]:
    """List explanations, optionally filtered by entity."""
    results = list(_explanations.values())
    if entity_type:
        results = [
            explanation for explanation in results if explanation.entity_type == entity_type
        ]
    if entity_id:
        results = [explanation for explanation in results if explanation.entity_id == entity_id]

    logger.info(
        "explanations_listed",
        count=len(results),
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return results


@router.delete("/{explanation_id}", dependencies=[require_scope("workflows:write")])
async def delete_explanation(explanation_id: str) -> dict[str, str]:
    """Delete an explanation."""
    if explanation_id not in _explanations:
        raise HTTPException(status_code=404, detail=f"Explanation '{explanation_id}' not found")

    del _explanations[explanation_id]
    logger.info("explanation_deleted", explanation_id=explanation_id)
    return {"message": f"Explanation '{explanation_id}' deleted"}


def get_explanations_store() -> dict[str, ExplanationMetadata]:
    """Get in-memory explanation store for testing."""
    return _explanations
