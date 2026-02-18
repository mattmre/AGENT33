"""Domain models for multimodal request/response lifecycle."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class ModalityType(StrEnum):
    """Supported multimodal operations."""

    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    VISION = "vision_analysis"


class RequestState(StrEnum):
    """Lifecycle state for multimodal requests."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MultimodalPolicy(BaseModel):
    """Per-tenant multimodal policy limits."""

    max_text_chars: int = Field(default=5000, ge=0)
    max_artifact_bytes: int = Field(default=5_000_000, ge=0)
    max_timeout_seconds: int = Field(default=300, ge=1)
    allowed_modalities: set[ModalityType] = Field(
        default_factory=lambda: {
            ModalityType.SPEECH_TO_TEXT,
            ModalityType.TEXT_TO_SPEECH,
            ModalityType.VISION,
        }
    )


class MultimodalRequest(BaseModel):
    """Request record for multimodal processing."""

    id: str = Field(default_factory=lambda: _id("mmreq"))
    tenant_id: str = ""
    modality: ModalityType
    input_text: str = ""
    input_artifact_id: str = ""
    input_artifact_base64: str = ""
    requested_timeout_seconds: int = 60
    requested_by: str = ""
    state: RequestState = RequestState.PENDING
    result_id: str = ""
    error_message: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MultimodalResult(BaseModel):
    """Execution result for a multimodal request."""

    id: str = Field(default_factory=lambda: _id("mmres"))
    request_id: str
    state: RequestState
    output_text: str = ""
    output_artifact_id: str = ""
    output_data: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
