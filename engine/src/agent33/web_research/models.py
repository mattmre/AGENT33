"""Structured models for provider-aware web research."""

from __future__ import annotations

from datetime import datetime  # noqa: TCH003 — Pydantic needs runtime access
from enum import StrEnum

from pydantic import BaseModel, Field


class ResearchTrustLevel(StrEnum):
    """Explicit trust semantics for research artifacts."""

    SEARCH_INDEXED = "search-indexed"
    FETCH_VERIFIED = "fetch-verified"
    BLOCKED = "blocked"


class ResearchProviderKind(StrEnum):
    """Kinds of web research providers."""

    SEARCH = "search"
    FETCH = "fetch"


class ProviderAuthState(StrEnum):
    """Configuration/auth state for a research provider."""

    NOT_REQUIRED = "not_required"
    CONFIGURED = "configured"
    MISSING = "missing"


class WebResearchCitation(BaseModel):
    """Citation metadata suitable for direct frontend rendering."""

    title: str
    url: str
    display_url: str
    domain: str
    provider_id: str
    trust_level: ResearchTrustLevel
    trust_reason: str


class WebResearchResult(BaseModel):
    """A structured web search result."""

    title: str
    url: str
    snippet: str = ""
    provider_id: str
    rank: int = 1
    domain: str = ""
    display_url: str = ""
    trust_level: ResearchTrustLevel
    trust_reason: str
    citation: WebResearchCitation


class ResearchProviderStatus(BaseModel):
    """Operator-visible diagnostics for a research provider."""

    provider_id: str
    display_name: str
    kind: ResearchProviderKind
    status: str
    auth_state: ProviderAuthState
    configured: bool
    capabilities: list[str] = Field(default_factory=list)
    is_default: bool = False
    detail: str = ""


class ProviderStatusInfo(BaseModel):
    """Dashboard-facing provider health summary with call metrics."""

    name: str
    enabled: bool
    status: str
    last_check: datetime | None = None
    total_calls: int = 0
    success_rate: float = 1.0


class ResearchSearchRequest(BaseModel):
    """Search request body for grounded web research."""

    query: str = Field(min_length=1)
    provider: str | None = None
    limit: int = Field(default=10, ge=1, le=25)
    categories: str = "general"


class ResearchSearchResponse(BaseModel):
    """Structured search response for the web research API."""

    query: str
    provider_id: str
    results: list[WebResearchResult] = Field(default_factory=list)


class ResearchFetchRequest(BaseModel):
    """Fetch request body for governed web retrieval."""

    url: str = Field(min_length=1)
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | None = None
    timeout: int = Field(default=30, ge=1, le=300)
    allowed_domains: list[str] = Field(default_factory=list)


class WebFetchArtifact(BaseModel):
    """Structured representation of a fetched page."""

    url: str
    provider_id: str
    status_code: int
    content: str
    content_preview: str
    trust_level: ResearchTrustLevel
    trust_reason: str
    citation: WebResearchCitation
