"""Shared pack provenance data models with no manifest dependencies."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TrustLevel(StrEnum):
    """Trust classification for a pack's provenance."""

    UNTRUSTED = "untrusted"
    COMMUNITY = "community"
    VERIFIED = "verified"
    OFFICIAL = "official"


class PackProvenance(BaseModel):
    """Provenance metadata attached to a signed pack."""

    signer_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the entity that signed the pack",
    )
    signature: str = Field(
        ...,
        min_length=1,
        description="Hex-encoded HMAC-SHA256 signature of the manifest",
    )
    signed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    algorithm: str = Field(default="sha256")
    trust_level: TrustLevel = Field(default=TrustLevel.COMMUNITY)


class PackTrustPolicy(BaseModel):
    """Policy governing which packs are trusted for installation."""

    require_signature: bool = False
    min_trust_level: TrustLevel = TrustLevel.UNTRUSTED
    allowed_signers: list[str] = Field(default_factory=list)


class TrustDecision(BaseModel):
    """Result of evaluating provenance against a trust policy."""

    allowed: bool
    reason: str = ""
