"""Core data models for skill packs.

Defines the status, dependency, governance, and installed-pack models
used throughout the pack subsystem.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path  # noqa: TC003 -- Pydantic needs Path at runtime

from pydantic import BaseModel, Field


class PackStatus(StrEnum):
    """Lifecycle status of an installed pack."""

    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PackSkillEntry(BaseModel):
    """A skill entry within a pack manifest."""

    name: str = Field(..., min_length=1, max_length=64)
    path: str = Field(..., min_length=1, description="Relative path to skill dir/file")
    description: str = ""
    required: bool = True


class PackDependency(BaseModel):
    """A dependency on another pack."""

    name: str = Field(..., min_length=1, max_length=64)
    version_constraint: str = Field(
        ...,
        min_length=1,
        description="Semver constraint string (e.g. ^1.0.0, >=2.0.0, <3.0.0)",
    )


class PackPythonDependency(BaseModel):
    """A Python package required at runtime."""

    name: str
    version: str = "*"


class PackCompatibility(BaseModel):
    """Compatibility requirements for a pack."""

    agent_roles: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    python_packages: list[PackPythonDependency] = Field(default_factory=list)


class PackGovernance(BaseModel):
    """Pack-level governance overrides."""

    min_autonomy_level: str = ""
    approval_required_for: list[str] = Field(default_factory=list)
    max_instructions_chars: int = 16000


class PackSource(BaseModel):
    """Describes where a pack comes from for installation."""

    source_type: str = Field(
        default="local",
        description="Source type: 'local' (directory path) or 'marketplace'",
    )
    path: str = Field(
        default="",
        description="Local filesystem path to pack directory",
    )
    name: str = Field(
        default="",
        description="Pack name for marketplace lookup",
    )
    version: str = Field(
        default="",
        description="Target version (empty = latest)",
    )


class InstalledPack(BaseModel):
    """Represents a pack that has been installed and validated."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = ""
    tags: list[str] = Field(default_factory=list)
    category: str = ""

    # Skills
    skills: list[PackSkillEntry] = Field(default_factory=list)
    loaded_skill_names: list[str] = Field(default_factory=list)

    # Dependencies
    pack_dependencies: list[PackDependency] = Field(default_factory=list)
    engine_min_version: str = ""

    # Compatibility
    compatibility: PackCompatibility = Field(default_factory=PackCompatibility)

    # Installation metadata
    installed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str = "local"
    checksum: str = ""
    pack_dir: Path

    # Governance
    governance: PackGovernance = Field(default_factory=PackGovernance)

    # Status
    status: PackStatus = PackStatus.INSTALLED

    model_config = {"arbitrary_types_allowed": True}


class InstallResult(BaseModel):
    """Result of a pack installation or upgrade operation."""

    success: bool
    pack_name: str
    version: str = ""
    skills_loaded: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
