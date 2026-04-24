"""Shared runtime LLM configuration helpers."""

from __future__ import annotations

from urllib.parse import urlparse

from agent33.config import settings
from agent33.llm.default_models import (
    llamacpp_enabled as _llamacpp_enabled,
)
from agent33.llm.default_models import (
    resolve_default_model as _resolve_default_model,
)
from agent33.llm.ollama import OllamaProvider
from agent33.llm.openai import OpenAIProvider
from agent33.llm.router import ModelRouter


def llamacpp_enabled() -> bool:
    """Return True when the local orchestration engine is llama.cpp."""
    return _llamacpp_enabled()


def resolve_default_model() -> str:
    """Return the configured default chat/agent model."""
    return _resolve_default_model()


def _is_openrouter_base_url(base_url: str) -> bool:
    normalized = base_url.rstrip("/")
    parsed = urlparse(normalized)
    return parsed.netloc.lower() == "openrouter.ai" and parsed.path.endswith("/api/v1")


def _build_openrouter_headers() -> dict[str, str]:
    if not _is_openrouter_base_url(settings.openrouter_base_url):
        return {}

    headers: dict[str, str] = {}
    site_url = settings.openrouter_site_url.strip()
    app_name = settings.openrouter_app_name.strip()
    category = settings.openrouter_app_category.strip()

    if site_url:
        headers["HTTP-Referer"] = site_url
    if app_name:
        headers["X-OpenRouter-Title"] = app_name
    if category:
        headers["X-OpenRouter-Categories"] = category

    return headers


def build_model_router() -> ModelRouter:
    """Construct the shared runtime model router with configured providers."""
    router = ModelRouter(default_provider="llamacpp" if llamacpp_enabled() else "ollama")
    router.register(
        "ollama",
        OllamaProvider(
            base_url=settings.runtime_ollama_base_url,
            default_model=settings.ollama_default_model,
        ),
    )

    if llamacpp_enabled():
        router.register(
            "llamacpp",
            OpenAIProvider(
                api_key="local",
                base_url=settings.local_orchestration_base_url,
                default_model=settings.local_orchestration_model,
            ),
        )

    if settings.openai_api_key.get_secret_value():
        openai_kwargs: dict[str, str] = {
            "api_key": settings.openai_api_key.get_secret_value(),
        }
        if settings.openai_base_url:
            openai_kwargs["base_url"] = settings.openai_base_url
        router.register("openai", OpenAIProvider(**openai_kwargs))

    if settings.openrouter_api_key.get_secret_value():
        router.register(
            "openrouter",
            OpenAIProvider(
                api_key=settings.openrouter_api_key.get_secret_value(),
                base_url=settings.openrouter_base_url,
                default_model="openrouter/auto",
                extra_headers=_build_openrouter_headers(),
            ),
        )

    return router
