"""Models for explanation artifact metadata and API contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FactCheckStatus(StrEnum):
    """Status of fact-check validation."""

    PENDING = "pending"
    VERIFIED = "verified"
    FLAGGED = "flagged"
    SKIPPED = "skipped"


class ExplanationRequest(BaseModel):
    """Request to generate an explanation."""

    entity_type: str = Field(..., min_length=1, description="Type of entity to explain")
    entity_id: str = Field(..., min_length=1, description="ID of the entity")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for generation",
    )


class ExplanationMetadata(BaseModel):
    """Metadata for a generated explanation artifact."""

    id: str = Field(..., description="Unique explanation identifier")
    entity_type: str = Field(..., description="Type of entity (workflow, agent, etc.)")
    entity_id: str = Field(..., description="ID of the entity being explained")
    content: str = Field(..., description="Explanation text content")
    fact_check_status: FactCheckStatus = Field(
        default=FactCheckStatus.PENDING,
        description="Current fact-check validation status",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when explanation was generated",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (model used, confidence, etc.)",
    )

