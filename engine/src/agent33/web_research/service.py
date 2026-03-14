"""Provider-aware web research service layer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from urllib.parse import urlparse

if TYPE_CHECKING:
    from collections.abc import Sequence

import httpx

from agent33.config import settings
from agent33.connectors.boundary import (
    build_connector_boundary_executor,
    map_connector_exception,
)
from agent33.connectors.models import ConnectorRequest
from agent33.web_research.models import (
    ProviderAuthState,
    ResearchProviderKind,
    ResearchProviderStatus,
    ResearchSearchResponse,
    ResearchTrustLevel,
    WebFetchArtifact,
    WebResearchCitation,
    WebResearchResult,
)

_SEARCH_TIMEOUT_SECONDS = 15.0
_FETCH_TIMEOUT_SECONDS = 30.0
_MAX_FETCH_BYTES = 5 * 1024 * 1024


class SearchProvider(Protocol):
    """Protocol for search-capable research providers."""

    provider_id: str

    def diagnostics(self) -> ResearchProviderStatus:
        """Return operator-visible provider diagnostics."""

    async def search(
        self,
        query: str,
        *,
        limit: int,
        categories: str,
    ) -> list[WebResearchResult]:
        """Execute a search query and return structured results."""


class FetchProvider(Protocol):
    """Protocol for fetch-capable research providers."""

    provider_id: str

    def diagnostics(self) -> ResearchProviderStatus:
        """Return operator-visible provider diagnostics."""

    async def fetch(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: str | None,
        method: str,
        timeout: int,
        allowed_domains: Sequence[str],
    ) -> WebFetchArtifact:
        """Fetch a URL and return a structured artifact."""


def _display_url(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    path = parsed.path.rstrip("/")
    if path:
        return f"{domain}{path}"
    return domain or url


def _domain(url: str) -> str:
    return urlparse(url).hostname or ""


def _search_citation(title: str, url: str, provider_id: str) -> WebResearchCitation:
    return WebResearchCitation(
        title=title,
        url=url,
        display_url=_display_url(url),
        domain=_domain(url),
        provider_id=provider_id,
        trust_level=ResearchTrustLevel.SEARCH_INDEXED,
        trust_reason=(
            f"Indexed by {provider_id}; AGENT-33 has not fetched this source directly yet."
        ),
    )


class SearXNGSearchProvider:
    """Default search provider backed by SearXNG."""

    provider_id = "searxng"

    def diagnostics(self) -> ResearchProviderStatus:
        configured = bool(settings.searxng_url.strip())
        return ResearchProviderStatus(
            provider_id=self.provider_id,
            display_name="SearXNG",
            kind=ResearchProviderKind.SEARCH,
            status="ok" if configured else "unconfigured",
            auth_state=ProviderAuthState.NOT_REQUIRED,
            configured=configured,
            capabilities=["search", "snippets"],
            is_default=True,
            detail=(
                f"Base URL: {settings.searxng_url}"
                if configured
                else "Set `SEARXNG_URL` to enable grounded search."
            ),
        )

    async def search(
        self,
        query: str,
        *,
        limit: int,
        categories: str,
    ) -> list[WebResearchResult]:
        if not settings.searxng_url.strip():
            raise ValueError("SearXNG provider is not configured")

        url = f"{settings.searxng_url}/search"
        request_params: dict[str, str | int] = {
            "q": query,
            "format": "json",
            "pageno": 1,
            "categories": categories,
        }

        async def _perform_search(_request: ConnectorRequest) -> httpx.Response:
            async with httpx.AsyncClient(timeout=_SEARCH_TIMEOUT_SECONDS) as client:
                return await client.get(url, params=request_params)

        boundary_executor = build_connector_boundary_executor(
            default_timeout_seconds=_SEARCH_TIMEOUT_SECONDS,
            retry_attempts=1,
        )
        try:
            if boundary_executor is None:
                response = await _perform_search(
                    ConnectorRequest(connector="search:searxng", operation="GET")
                )
            else:
                req = ConnectorRequest(
                    connector="search:searxng",
                    operation="GET",
                    payload={"url": url, "params": request_params},
                    metadata={"timeout_seconds": _SEARCH_TIMEOUT_SECONDS},
                )
                response = await boundary_executor.execute(req, _perform_search)
            response.raise_for_status()
        except Exception as exc:
            if boundary_executor is not None:
                mapped = map_connector_exception(exc, "search:searxng", "GET")
                raise ValueError(str(mapped)) from exc
            if isinstance(exc, httpx.ConnectError):
                raise ValueError(
                    f"Could not connect to SearXNG at {settings.searxng_url}."
                ) from exc
            if isinstance(exc, httpx.TimeoutException):
                raise ValueError("SearXNG request timed out.") from exc
            if isinstance(exc, httpx.HTTPStatusError):
                raise ValueError(
                    f"SearXNG returned HTTP {exc.response.status_code}: {exc.response.text[:500]}"
                ) from exc
            if isinstance(exc, httpx.RequestError):
                raise ValueError(f"SearXNG request error: {exc}") from exc
            raise ValueError(f"SearXNG request error: {exc}") from exc

        payload = response.json()
        raw_results = payload.get("results", [])[:limit]
        results: list[WebResearchResult] = []
        for index, item in enumerate(raw_results, start=1):
            title = str(item.get("title") or "Untitled")
            result_url = str(item.get("url") or "")
            citation = _search_citation(title, result_url, self.provider_id)
            results.append(
                WebResearchResult(
                    title=title,
                    url=result_url,
                    snippet=str(item.get("content") or "").strip(),
                    provider_id=self.provider_id,
                    rank=index,
                    domain=citation.domain,
                    display_url=citation.display_url,
                    trust_level=citation.trust_level,
                    trust_reason=citation.trust_reason,
                    citation=citation,
                )
            )
        return results


class GovernedFetchProvider:
    """Fetch provider that wraps governed HTTP retrieval."""

    provider_id = "web_fetch"

    def diagnostics(self) -> ResearchProviderStatus:
        return ResearchProviderStatus(
            provider_id=self.provider_id,
            display_name="Governed HTTP Fetch",
            kind=ResearchProviderKind.FETCH,
            status="ok",
            auth_state=ProviderAuthState.NOT_REQUIRED,
            configured=True,
            capabilities=["fetch", "allowlist-enforced"],
            detail="Uses connector-boundary execution with explicit domain allowlists.",
        )

    async def fetch(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: str | None,
        method: str,
        timeout: int,
        allowed_domains: Sequence[str],
    ) -> WebFetchArtifact:
        domain = _domain(url)
        if not allowed_domains:
            raise ValueError("Domain allowlist not configured — all requests denied by default")
        if not any(
            domain == allowed or domain.endswith(f".{allowed}") for allowed in allowed_domains
        ):
            raise ValueError(f"Domain '{domain}' is not in the allowlist: {list(allowed_domains)}")

        async def _perform_fetch(_request: ConnectorRequest) -> httpx.Response:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                if method == "GET":
                    return await client.get(url, headers=headers)
                return await client.post(url, headers=headers, content=body)

        boundary_executor = build_connector_boundary_executor(
            default_timeout_seconds=float(timeout),
            retry_attempts=1,
        )
        try:
            if boundary_executor is None:
                response = await _perform_fetch(
                    ConnectorRequest(connector="tool:web_fetch", operation=method)
                )
            else:
                req = ConnectorRequest(
                    connector="tool:web_fetch",
                    operation=method,
                    payload={"url": url, "headers": headers, "body": body},
                    metadata={"timeout_seconds": float(timeout)},
                )
                response = await boundary_executor.execute(req, _perform_fetch)
            response.raise_for_status()
            if 300 <= response.status_code < 400:
                raise ValueError("Redirect responses are blocked by policy")
            if len(response.content) > _MAX_FETCH_BYTES:
                raise ValueError(
                    f"Response too large ({len(response.content)} bytes, limit {_MAX_FETCH_BYTES})"
                )
        except Exception as exc:
            if boundary_executor is not None and not isinstance(exc, ValueError):
                mapped = map_connector_exception(exc, "tool:web_fetch", method)
                raise ValueError(str(mapped)) from exc
            if isinstance(exc, ValueError):
                raise
            if isinstance(exc, httpx.TimeoutException):
                raise ValueError(f"Request timed out after {timeout}s") from exc
            if isinstance(exc, httpx.HTTPStatusError):
                raise ValueError(
                    f"HTTP {exc.response.status_code}: {exc.response.text[:500]}"
                ) from exc
            if isinstance(exc, httpx.RequestError):
                raise ValueError(f"Request error: {exc}") from exc
            raise ValueError(f"Request error: {exc}") from exc

        citation = WebResearchCitation(
            title=_display_url(url),
            url=url,
            display_url=_display_url(url),
            domain=domain,
            provider_id=self.provider_id,
            trust_level=ResearchTrustLevel.FETCH_VERIFIED,
            trust_reason="Fetched directly by AGENT-33 through the governed web_fetch provider.",
        )
        content = response.text
        return WebFetchArtifact(
            url=url,
            provider_id=self.provider_id,
            status_code=response.status_code,
            content=content,
            content_preview=content[:2000],
            trust_level=ResearchTrustLevel.FETCH_VERIFIED,
            trust_reason=citation.trust_reason,
            citation=citation,
        )


class WebResearchService:
    """Unified service for grounded search/fetch providers."""

    def __init__(
        self,
        *,
        search_providers: Sequence[SearchProvider],
        fetch_providers: Sequence[FetchProvider],
        default_search_provider: str,
        default_fetch_provider: str,
    ) -> None:
        self._search_providers = {provider.provider_id: provider for provider in search_providers}
        self._fetch_providers = {provider.provider_id: provider for provider in fetch_providers}
        self._default_search_provider = default_search_provider
        self._default_fetch_provider = default_fetch_provider

    def list_providers(self) -> list[ResearchProviderStatus]:
        providers = [provider.diagnostics() for provider in self._search_providers.values()]
        providers.extend(provider.diagnostics() for provider in self._fetch_providers.values())
        return providers

    async def search(
        self,
        query: str,
        *,
        provider_id: str | None = None,
        limit: int = 10,
        categories: str = "general",
    ) -> ResearchSearchResponse:
        resolved_provider_id = provider_id or self._default_search_provider
        provider = self._search_providers.get(resolved_provider_id)
        if provider is None:
            raise ValueError(f"Unknown research search provider '{resolved_provider_id}'")
        results = await provider.search(query, limit=limit, categories=categories)
        return ResearchSearchResponse(
            query=query,
            provider_id=resolved_provider_id,
            results=results,
        )

    async def fetch(
        self,
        url: str,
        *,
        allowed_domains: Sequence[str],
        provider_id: str | None = None,
        headers: dict[str, str] | None = None,
        body: str | None = None,
        method: str = "GET",
        timeout: int = int(_FETCH_TIMEOUT_SECONDS),
    ) -> WebFetchArtifact:
        resolved_provider_id = provider_id or self._default_fetch_provider
        provider = self._fetch_providers.get(resolved_provider_id)
        if provider is None:
            raise ValueError(f"Unknown research fetch provider '{resolved_provider_id}'")
        return await provider.fetch(
            url,
            headers=headers or {},
            body=body,
            method=method,
            timeout=timeout,
            allowed_domains=allowed_domains,
        )


def create_default_web_research_service() -> WebResearchService:
    """Create the default Track 7 research service graph."""

    return WebResearchService(
        search_providers=[SearXNGSearchProvider()],
        fetch_providers=[GovernedFetchProvider()],
        default_search_provider="searxng",
        default_fetch_provider="web_fetch",
    )
