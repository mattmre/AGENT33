"""FastAPI routes for multimodal request lifecycle."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agent33.multimodal.models import ModalityType, MultimodalPolicy, RequestState
from agent33.multimodal.service import (
    InvalidStateTransitionError,
    MultimodalService,
    PolicyViolationError,
    RequestNotFoundError,
)
from agent33.security.permissions import require_scope

router = APIRouter(prefix="/v1/multimodal", tags=["multimodal"])
_service = MultimodalService()


class CreateRequestBody(BaseModel):
    modality: ModalityType
    input_text: str = ""
    input_artifact_id: str = ""
    input_artifact_base64: str = ""
    requested_timeout_seconds: int = Field(default=60, ge=1)
    requested_by: str = ""
    execute_now: bool = True


def get_multimodal_service() -> MultimodalService:
    """Return singleton multimodal service."""
    return _service


def _tenant_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        return ""
    return getattr(user, "tenant_id", "")


@router.post("/requests", status_code=201, dependencies=[require_scope("multimodal:write")])
async def create_request(body: CreateRequestBody, request: Request) -> dict[str, Any]:
    tenant_id = _tenant_id(request)
    try:
        created = _service.create_request(
            tenant_id=tenant_id,
            modality=body.modality,
            input_text=body.input_text,
            input_artifact_id=body.input_artifact_id,
            input_artifact_base64=body.input_artifact_base64,
            requested_timeout_seconds=body.requested_timeout_seconds,
            requested_by=body.requested_by,
        )
        if body.execute_now:
            created = await _service.execute_request(created.id, tenant_id=tenant_id or None)
    except PolicyViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return created.model_dump(mode="json")


@router.get("/requests", dependencies=[require_scope("multimodal:read")])
async def list_requests(
    request: Request,
    modality: ModalityType | None = None,
    state: RequestState | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    tenant_id = _tenant_id(request)
    requests = _service.list_requests(
        tenant_id=tenant_id or None,
        modality=modality,
        state=state,
        limit=limit,
    )
    return [req.model_dump(mode="json") for req in requests]


@router.get("/requests/{request_id}", dependencies=[require_scope("multimodal:read")])
async def get_request(request_id: str, request: Request) -> dict[str, Any]:
    tenant_id = _tenant_id(request)
    try:
        record = _service.get_request(request_id, tenant_id=tenant_id or None)
    except RequestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return record.model_dump(mode="json")


@router.post(
    "/requests/{request_id}/execute",
    dependencies=[require_scope("multimodal:write")],
)
async def execute_request(request_id: str, request: Request) -> dict[str, Any]:
    tenant_id = _tenant_id(request)
    try:
        record = await _service.execute_request(request_id, tenant_id=tenant_id or None)
    except RequestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return record.model_dump(mode="json")


@router.get(
    "/requests/{request_id}/result",
    dependencies=[require_scope("multimodal:read")],
)
async def get_result(request_id: str, request: Request) -> dict[str, Any]:
    tenant_id = _tenant_id(request)
    try:
        result = _service.get_result(request_id, tenant_id=tenant_id or None)
    except RequestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@router.post(
    "/requests/{request_id}/cancel",
    dependencies=[require_scope("multimodal:write")],
)
async def cancel_request(request_id: str, request: Request) -> dict[str, Any]:
    tenant_id = _tenant_id(request)
    try:
        record = _service.cancel_request(request_id, tenant_id=tenant_id or None)
    except RequestNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return record.model_dump(mode="json")


@router.post(
    "/tenants/{tenant_id}/policy",
    dependencies=[require_scope("multimodal:write")],
)
async def set_tenant_policy(tenant_id: str, policy: MultimodalPolicy) -> dict[str, Any]:
    """Set policy guardrails for a tenant (Stage 1 helper endpoint)."""
    _service.set_policy(tenant_id, policy)
    return policy.model_dump(mode="json")
