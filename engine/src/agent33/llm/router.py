"""Model router that dispatches to the correct LLM provider."""

from __future__ import annotations

import logging
from typing import Any

from agent33.llm.base import ChatMessage, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# Maps model-name prefixes to provider names. Checked in order; first match wins.
_DEFAULT_PREFIX_MAP: list[tuple[str, str]] = [
    ("gpt-", "openai"),
    ("o1", "openai"),
    ("o3", "openai"),
    ("claude-", "openai"),  # Anthropic via OpenAI-compat proxy
    ("ft:gpt-", "openai"),
    ("airllm-", "airllm"),
]

_DEFAULT_PROVIDER = "ollama"


class ModelRouter:
    """Routes completion requests to the appropriate LLM provider."""

    def __init__(
        self,
        providers: dict[str, Any] | None = None,
        prefix_map: list[tuple[str, str]] | None = None,
        default_provider: str = _DEFAULT_PROVIDER,
    ) -> None:
        self._providers: dict[str, LLMProvider] = dict(providers or {})
        self._prefix_map = prefix_map if prefix_map is not None else list(_DEFAULT_PREFIX_MAP)
        self._default_provider = default_provider

    # -- provider management ----------------------------------------------

    def register(self, name: str, provider: LLMProvider) -> None:
        """Register a provider under the given name."""
        self._providers[name] = provider
        logger.info("registered llm provider %s", name)

    def unregister(self, name: str) -> None:
        """Remove a registered provider."""
        self._providers.pop(name, None)

    @property
    def providers(self) -> dict[str, LLMProvider]:
        """Read-only view of registered providers."""
        return dict(self._providers)

    # -- routing ----------------------------------------------------------

    def route(self, model_name: str) -> LLMProvider:
        """Pick the right provider for *model_name* based on prefix rules."""
        for prefix, provider_name in self._prefix_map:
            if model_name.startswith(prefix):
                if provider_name in self._providers:
                    return self._providers[provider_name]
                raise ValueError(
                    f"Model '{model_name}' maps to provider '{provider_name}' "
                    f"which is not registered"
                )

        if self._default_provider in self._providers:
            return self._providers[self._default_provider]

        raise ValueError(
            f"No provider found for model '{model_name}' and default provider "
            f"'{self._default_provider}' is not registered"
        )

    # -- convenience ------------------------------------------------------

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Route to the correct provider and generate a completion."""
        provider = self.route(model)
        return await provider.complete(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
