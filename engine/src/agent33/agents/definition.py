"""Pydantic models matching the AGENT-33 agent schema."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator


class AgentRole(str, Enum):
    """Allowed agent roles."""

    ORCHESTRATOR = "orchestrator"
    DIRECTOR = "director"
    IMPLEMENTER = "implementer"
    QA = "qa"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    ARCHITECT = "architect"
    TEST_ENGINEER = "test-engineer"

    # Deprecated aliases -- kept for backward-compatible JSON loading.
    WORKER = "worker"
    VALIDATOR = "validator"


class AgentCapability(str, Enum):
    """Capabilities an agent may declare."""

    FILE_READ = "file-read"
    FILE_WRITE = "file-write"
    CODE_EXECUTION = "code-execution"
    WEB_SEARCH = "web-search"
    API_CALLS = "api-calls"
    ORCHESTRATION = "orchestration"
    VALIDATION = "validation"
    CODE_ANALYSIS = "code-analysis"
    RESEARCH = "research"
    REFINEMENT = "refinement"


class CapabilityCategory(str, Enum):
    """Top-level capability categories from the spec taxonomy."""

    PLANNING = "P"
    IMPLEMENTATION = "I"
    VERIFICATION = "V"
    REVIEW = "R"
    RESEARCH = "X"


class SpecCapability(str, Enum):
    """25-entry spec capability taxonomy (5 per category)."""

    # Planning
    P_01 = "P-01"
    P_02 = "P-02"
    P_03 = "P-03"
    P_04 = "P-04"
    P_05 = "P-05"

    # Implementation
    I_01 = "I-01"
    I_02 = "I-02"
    I_03 = "I-03"
    I_04 = "I-04"
    I_05 = "I-05"

    # Verification
    V_01 = "V-01"
    V_02 = "V-02"
    V_03 = "V-03"
    V_04 = "V-04"
    V_05 = "V-05"

    # Review
    R_01 = "R-01"
    R_02 = "R-02"
    R_03 = "R-03"
    R_04 = "R-04"
    R_05 = "R-05"

    # Research
    X_01 = "X-01"
    X_02 = "X-02"
    X_03 = "X-03"
    X_04 = "X-04"
    X_05 = "X-05"

    @property
    def category(self) -> CapabilityCategory:
        """Return the top-level category for this capability."""
        return CapabilityCategory(self.value[0])


class AgentStatus(str, Enum):
    """Lifecycle status for an agent definition."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class AgentParameter(BaseModel):
    """A single input or output parameter."""

    type: str = Field(..., description="Parameter type")
    description: str = ""
    required: bool = False
    default: Any = None
    enum: list[Any] | None = None


class AgentDependency(BaseModel):
    """A dependency on another agent."""

    agent: str
    optional: bool = False
    purpose: str = ""


class AgentPrompts(BaseModel):
    """Prompt template paths."""

    system: str = ""
    user: str = ""
    examples: list[str] = Field(default_factory=list)


class AgentConstraints(BaseModel):
    """Execution constraints."""

    max_tokens: int = Field(default=4096, ge=100, le=200000)
    timeout_seconds: int = Field(default=120, ge=10, le=3600)
    max_retries: int = Field(default=2, ge=0, le=10)
    parallel_allowed: bool = True


class AgentMetadata(BaseModel):
    """Optional metadata."""

    author: str = ""
    created: str = ""
    updated: str = ""
    tags: list[str] = Field(default_factory=list)


class GovernanceConstraints(BaseModel):
    """Governance rules from the spec. Enforcement is Phase 14."""

    scope: str = ""
    commands: str = ""
    network: str = ""
    approval_required: list[str] = Field(default_factory=list)


class AgentOwnership(BaseModel):
    """Ownership and escalation metadata."""

    owner: str = ""
    escalation_target: str = ""


class AgentDefinition(BaseModel):
    """Full agent definition matching agent.schema.json."""

    name: str = Field(
        ..., min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9-]*$"
    )
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    role: AgentRole
    description: str = Field(default="", max_length=500)
    capabilities: list[AgentCapability] = Field(default_factory=list)
    inputs: dict[str, AgentParameter] = Field(default_factory=dict)
    outputs: dict[str, AgentParameter] = Field(default_factory=dict)
    dependencies: list[AgentDependency] = Field(default_factory=list)
    prompts: AgentPrompts = Field(default_factory=AgentPrompts)
    constraints: AgentConstraints = Field(default_factory=AgentConstraints)
    metadata: AgentMetadata = Field(default_factory=AgentMetadata)

    # Phase 11 additions -- all optional so existing JSON still loads.
    agent_id: str | None = Field(
        default=None,
        pattern=r"^AGT-\d{3}$",
        description="Spec agent ID (e.g. AGT-001)",
    )
    spec_capabilities: list[SpecCapability] = Field(default_factory=list)
    governance: GovernanceConstraints = Field(
        default_factory=GovernanceConstraints,
    )
    ownership: AgentOwnership = Field(default_factory=AgentOwnership)
    status: AgentStatus = Field(default=AgentStatus.ACTIVE)

    @model_validator(mode="before")
    @classmethod
    def normalise_deprecated_roles(cls, data: Any) -> Any:
        """Map legacy 'worker' -> 'implementer', 'validator' -> 'qa'."""
        if isinstance(data, dict):
            role = data.get("role")
            if role == "worker":
                data = {**data, "role": "implementer"}
            elif role == "validator":
                data = {**data, "role": "qa"}
        return data

    @classmethod
    def load_from_file(cls, path: str | Path) -> AgentDefinition:
        """Load an agent definition from a JSON file."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Agent definition not found: {file_path}")
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        # Strip JSON-schema $schema key if present
        raw.pop("$schema", None)
        return cls.model_validate(raw)
