"""Pack manifest (PACK.yaml) parsing and validation.

A Skill Pack is a directory containing a PACK.yaml manifest and one or
more skill definitions.  The manifest is the pack's identity document.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from agent33.packs.models import (
    PackCompatibility,
    PackDependency,
    PackGovernance,
    PackSkillEntry,
)

if TYPE_CHECKING:
    from pathlib import Path

import structlog

logger = structlog.get_logger()

# Regex for valid pack name: lowercase letters, digits, hyphens; 1-64 chars
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$|^[a-z0-9]$")

# Regex for semver: MAJOR.MINOR.PATCH (no pre-release tags in v1)
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


class PackDependencies(BaseModel):
    """Dependencies section of a pack manifest."""

    packs: list[PackDependency] = Field(default_factory=list)
    engine: dict[str, str] = Field(
        default_factory=dict,
        description="Engine compatibility: {min_version: '0.1.0'}",
    )
    plugins: list[PackDependency] = Field(default_factory=list)


class PackManifest(BaseModel):
    """Parsed and validated PACK.yaml manifest.

    This model represents the on-disk manifest format.  After validation,
    it is converted to an ``InstalledPack`` for use in the registry.
    """

    schema_version: str = Field(
        default="1",
        description="Manifest format version (currently '1')",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Pack slug (lowercase, hyphens, 1-64 chars)",
    )
    version: str = Field(
        ...,
        min_length=1,
        description="Semver version (MAJOR.MINOR.PATCH)",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Short description",
    )
    author: str = Field(
        ...,
        min_length=1,
        description="Author or organization name",
    )
    license: str = ""
    homepage: str = ""
    repository: str = ""

    # Classification
    tags: list[str] = Field(default_factory=list)
    category: str = ""

    # Skills
    skills: list[PackSkillEntry] = Field(
        ...,
        min_length=1,
        description="Skills included in this pack (at least one required)",
    )

    # Dependencies
    dependencies: PackDependencies = Field(default_factory=PackDependencies)

    # Compatibility
    compatibility: PackCompatibility = Field(default_factory=PackCompatibility)

    # Governance
    governance: PackGovernance = Field(default_factory=PackGovernance)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        if not _NAME_RE.match(value):
            raise ValueError(
                f"Pack name '{value}' must be lowercase letters, digits, and hyphens "
                f"(1-64 chars, must start and end with letter or digit)"
            )
        return value

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        if not _SEMVER_RE.match(value):
            raise ValueError(
                f"Pack version '{value}' must be valid semver (MAJOR.MINOR.PATCH)"
            )
        return value

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        if value != "1":
            raise ValueError(
                f"Unsupported schema_version '{value}'. Only version '1' is supported."
            )
        return value

    @model_validator(mode="after")
    def _validate_skill_names_unique(self) -> PackManifest:
        """Ensure no duplicate skill names within a pack."""
        seen: set[str] = set()
        for skill in self.skills:
            if skill.name in seen:
                raise ValueError(f"Duplicate skill name '{skill.name}' in pack '{self.name}'")
            seen.add(skill.name)
        return self


def parse_pack_yaml(path: Path) -> PackManifest:
    """Parse a PACK.yaml file and return a validated PackManifest.

    Args:
        path: Path to the PACK.yaml file.

    Returns:
        A validated PackManifest instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the YAML is invalid or fails validation.
    """
    import yaml

    if not path.is_file():
        raise FileNotFoundError(f"PACK.yaml not found: {path}")

    content = path.read_text(encoding="utf-8")

    try:
        raw = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"PACK.yaml must be a YAML mapping, got {type(raw).__name__}")

    return PackManifest.model_validate(raw)


def manifest_to_dict(manifest: PackManifest) -> dict[str, Any]:
    """Serialize a manifest to a dictionary suitable for YAML output."""
    return manifest.model_dump(mode="json", exclude_defaults=True)
