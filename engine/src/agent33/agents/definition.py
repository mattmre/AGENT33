"""Pydantic models matching the AGENT-33 agent schema."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Allowed agent roles."""

    ORCHESTRATOR = "orchestrator"
    DIRECTOR = "director"
    WORKER = "worker"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
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
    RESEARCH = "research"
    REFINEMENT = "refinement"


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


class AgentDefinition(BaseModel):
    """Full agent definition matching agent.schema.json."""

    name: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z][a-z0-9-]*$")
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
