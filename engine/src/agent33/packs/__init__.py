"""Skill Packs: versioned, distributable bundles of related skills.

Packs are an organizational layer above individual skills. They provide
grouping, versioned dependency resolution, tenant-scoped enablement,
and external format compatibility (SkillsBench, MCP tools).

Existing standalone skills continue to work unchanged.
"""

from __future__ import annotations

from agent33.packs.conflicts import (
    ConflictKind,
    Resolution,
    ResolutionAction,
    VersionConflict,
    detect_conflicts,
    resolve_conflicts,
)
from agent33.packs.manifest import PackManifest
from agent33.packs.marketplace import (
    LocalPackMarketplace,
    MarketplacePackRecord,
    MarketplacePackVersion,
)
from agent33.packs.models import (
    InstalledPack,
    InstallResult,
    PackDependency,
    PackGovernance,
    PackSkillEntry,
    PackSource,
    PackStatus,
)
from agent33.packs.provenance import (
    evaluate_trust,
    sign_pack,
    verify_pack,
)
from agent33.packs.provenance_models import (
    PackProvenance,
    PackTrustPolicy,
    TrustDecision,
    TrustLevel,
)

__all__ = [
    "ConflictKind",
    "InstalledPack",
    "InstallResult",
    "LocalPackMarketplace",
    "PackDependency",
    "PackGovernance",
    "PackManifest",
    "PackProvenance",
    "MarketplacePackRecord",
    "MarketplacePackVersion",
    "PackSkillEntry",
    "PackSource",
    "PackStatus",
    "PackTrustPolicy",
    "Resolution",
    "ResolutionAction",
    "TrustDecision",
    "TrustLevel",
    "VersionConflict",
    "detect_conflicts",
    "evaluate_trust",
    "resolve_conflicts",
    "sign_pack",
    "verify_pack",
]
