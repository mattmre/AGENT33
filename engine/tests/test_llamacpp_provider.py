"""Tests for llama.cpp provider wiring (local orchestration engine)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agent33.api.routes.agents import _default_agent_model, _llamacpp_enabled
from agent33.config import settings
from agent33.llm.openai import OpenAIProvider
from agent33.llm.router import ModelRouter


class TestLlamaCppEnabled:
    """Verify the _llamacpp_enabled() helper returns the correct boolean."""

    def test_llamacpp_enabled_when_engine_is_llamacpp(self) -> None:
        with patch.object(settings, "local_orchestration_engine", "llama.cpp"):
            assert _llamacpp_enabled() is True

    def test_llamacpp_enabled_when_engine_is_llamacpp_noslash(self) -> None:
        with patch.object(settings, "local_orchestration_engine", "llamacpp"):
            assert _llamacpp_enabled() is True

    def test_llamacpp_disabled_when_engine_is_ollama(self) -> None:
        with patch.object(settings, "local_orchestration_engine", "ollama"):
            assert _llamacpp_enabled() is False


class TestDefaultAgentModel:
    """Verify _default_agent_model() returns the right model name."""

    def test_default_model_returns_local_model_when_llamacpp(self) -> None:
        with (
            patch.object(settings, "local_orchestration_engine", "llama.cpp"),
            patch.object(settings, "local_orchestration_model", "test-local-model"),
        ):
            assert _default_agent_model() == "test-local-model"

    def test_default_model_returns_ollama_model_when_disabled(self) -> None:
        with (
            patch.object(settings, "local_orchestration_engine", "ollama"),
            patch.object(settings, "ollama_default_model", "llama3.2"),
        ):
            assert _default_agent_model() == "llama3.2"


class TestModelRouterRegistration:
    """Verify that llamacpp provider can be registered on a ModelRouter."""

    def test_model_router_registers_llamacpp_when_enabled(self) -> None:
        router = ModelRouter(default_provider="llamacpp")
        provider = OpenAIProvider(
            api_key="local",
            base_url="http://localhost:8033/v1",
            default_model="qwen3-coder-next",
        )
        router.register("llamacpp", provider)

        # Verify the provider is stored under the "llamacpp" key
        assert "llamacpp" in router._providers
        assert router._providers["llamacpp"] is provider
        assert router._default_provider == "llamacpp"

    @pytest.mark.parametrize(
        "engine_value",
        ["llama.cpp", "llamacpp"],
    )
    def test_model_router_default_provider_is_llamacpp_for_valid_engines(
        self, engine_value: str
    ) -> None:
        """Both 'llama.cpp' and 'llamacpp' should result in llamacpp as default."""
        with patch.object(settings, "local_orchestration_engine", engine_value):
            assert _llamacpp_enabled() is True
            router = ModelRouter(default_provider="llamacpp" if _llamacpp_enabled() else "ollama")
            assert router._default_provider == "llamacpp"
