"""Pack signing, provenance verification, and trust policy enforcement.

Provides HMAC-SHA256 signing of pack manifests, signature verification,
and trust policy evaluation to ensure packs are from trusted sources.

Uses only stdlib ``hmac`` and ``hashlib`` -- no external crypto deps.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from enum import StrEnum

import structlog
from pydantic import BaseModel, Field

from agent33.packs.manifest import PackManifest, manifest_to_dict

logger = structlog.get_logger()


class TrustLevel(StrEnum):
    """Trust classification for a pack's provenance."""

    UNTRUSTED = "untrusted"
    COMMUNITY = "community"
    VERIFIED = "verified"
    OFFICIAL = "official"


# Ordered for comparison: higher index = more trusted
_TRUST_ORDER: list[TrustLevel] = [
    TrustLevel.UNTRUSTED,
    TrustLevel.COMMUNITY,
    TrustLevel.VERIFIED,
    TrustLevel.OFFICIAL,
]


def _trust_rank(level: TrustLevel) -> int:
    """Return numeric rank for a trust level (higher = more trusted)."""
    return _TRUST_ORDER.index(level)


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
    signed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of when the pack was signed",
    )
    algorithm: str = Field(
        default="sha256",
        description="Hash algorithm used for signing (currently only sha256)",
    )
    trust_level: TrustLevel = Field(
        default=TrustLevel.COMMUNITY,
        description="Trust classification assigned by the signer",
    )


class PackTrustPolicy(BaseModel):
    """Policy governing which packs are trusted for installation."""

    require_signature: bool = Field(
        default=False,
        description="If True, packs without provenance metadata are rejected",
    )
    min_trust_level: TrustLevel = Field(
        default=TrustLevel.UNTRUSTED,
        description="Minimum trust level required for installation",
    )
    allowed_signers: list[str] = Field(
        default_factory=list,
        description="If non-empty, only these signer IDs are accepted",
    )


class TrustDecision(BaseModel):
    """Result of evaluating provenance against a trust policy."""

    allowed: bool
    reason: str = ""


def _canonical_manifest_bytes(manifest: PackManifest) -> bytes:
    """Serialize a manifest to canonical JSON bytes for signing.

    Uses sorted keys and no extra whitespace to ensure deterministic output
    regardless of field insertion order.
    """
    data = manifest_to_dict(manifest)
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_pack(
    manifest: PackManifest,
    signing_key: str,
    *,
    signer_id: str = "default",
    trust_level: TrustLevel = TrustLevel.COMMUNITY,
) -> PackProvenance:
    """Sign a pack manifest with HMAC-SHA256.

    Args:
        manifest: The pack manifest to sign.
        signing_key: Shared secret key for HMAC computation.
        signer_id: Identifier for the signing entity.
        trust_level: Trust classification to embed in provenance.

    Returns:
        A ``PackProvenance`` containing the hex signature and metadata.
    """
    payload = _canonical_manifest_bytes(manifest)
    sig = hmac.new(
        signing_key.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    provenance = PackProvenance(
        signer_id=signer_id,
        signature=sig,
        signed_at=datetime.now(UTC),
        algorithm="sha256",
        trust_level=trust_level,
    )

    logger.info(
        "pack_signed",
        pack=manifest.name,
        signer=signer_id,
        trust_level=trust_level,
    )
    return provenance


def verify_pack(
    manifest: PackManifest,
    provenance: PackProvenance,
    verification_key: str,
) -> bool:
    """Verify a pack manifest's signature against its provenance.

    Args:
        manifest: The pack manifest to verify.
        provenance: The provenance metadata containing the signature.
        verification_key: The shared secret key for HMAC verification.

    Returns:
        ``True`` if the signature is valid, ``False`` otherwise.
    """
    if provenance.algorithm != "sha256":
        logger.warning(
            "pack_verify_unsupported_algorithm",
            algorithm=provenance.algorithm,
        )
        return False

    payload = _canonical_manifest_bytes(manifest)
    expected_sig = hmac.new(
        verification_key.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    valid = hmac.compare_digest(expected_sig, provenance.signature)

    logger.info(
        "pack_verified",
        pack=manifest.name,
        signer=provenance.signer_id,
        valid=valid,
    )
    return valid


def evaluate_trust(provenance: PackProvenance | None, policy: PackTrustPolicy) -> TrustDecision:
    """Evaluate provenance metadata against a trust policy.

    Args:
        provenance: The provenance to evaluate (may be ``None`` for unsigned packs).
        policy: The trust policy to check against.

    Returns:
        A ``TrustDecision`` indicating whether the pack should be allowed.
    """
    # No provenance at all
    if provenance is None:
        if policy.require_signature:
            return TrustDecision(
                allowed=False,
                reason="Pack has no provenance metadata but policy requires a signature",
            )
        # No signature required, no provenance — allow by default
        return TrustDecision(
            allowed=True,
            reason="No provenance metadata; policy does not require signature",
        )

    # Check signer allowlist
    if policy.allowed_signers and provenance.signer_id not in policy.allowed_signers:
        return TrustDecision(
            allowed=False,
            reason=(
                f"Signer '{provenance.signer_id}' is not in the allowed signers list: "
                f"{policy.allowed_signers}"
            ),
        )

    # Check minimum trust level
    if _trust_rank(provenance.trust_level) < _trust_rank(policy.min_trust_level):
        return TrustDecision(
            allowed=False,
            reason=(
                f"Pack trust level '{provenance.trust_level}' is below the required "
                f"minimum '{policy.min_trust_level}'"
            ),
        )

    return TrustDecision(
        allowed=True,
        reason=(
            f"Pack signed by '{provenance.signer_id}' with trust level "
            f"'{provenance.trust_level}' meets policy requirements"
        ),
    )
