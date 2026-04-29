"""API tests for unified local model health routes."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from agent33.config import Settings
from agent33.main import app
from agent33.security.auth import create_access_token
from agent33.services.lm_studio_readiness import (
    LMStudioReadinessService,
    _LMStudioFetchResult,
)
from agent33.services.ollama_readiness import (
    OllamaReadinessService,
    _OllamaFetchResult,
)


class _OllamaSequenceFetcher:
    def __init__(self, responses: list[_OllamaFetchResult]) -> None:
        self._responses = responses
        self.calls: list[str] = []

    async def __call__(self, url: str) -> _OllamaFetchResult:
        self.calls.append(url)
        if not self._responses:
            raise AssertionError("No more Ollama responses configured")
        return self._responses.pop(0)


class _LMStudioSequenceFetcher:
    def __init__(self, responses: list[_LMStudioFetchResult]) -> None:
        self._responses = responses
        self.calls: list[str] = []

    async def __call__(self, url: str) -> _LMStudioFetchResult:
        self.calls.append(url)
        if not self._responses:
            raise AssertionError("No more LM Studio responses configured")
        return self._responses.pop(0)


@pytest.fixture()
def operator_read_client() -> TestClient:
    token = create_access_token("op-reader", scopes=["operator:read"], tenant_id="test-tenant")
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture()
def no_auth_client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _restore_readiness_services() -> Any:
    original_ollama = getattr(app.state, "ollama_readiness_service", None)
    original_lm_studio = getattr(app.state, "lm_studio_readiness_service", None)
    if "ollama_readiness_service" in app.state._state:
        del app.state.ollama_readiness_service
    if "lm_studio_readiness_service" in app.state._state:
        del app.state.lm_studio_readiness_service
    yield
    if original_ollama is not None:
        app.state.ollama_readiness_service = original_ollama
    elif "ollama_readiness_service" in app.state._state:
        del app.state.ollama_readiness_service
    if original_lm_studio is not None:
        app.state.lm_studio_readiness_service = original_lm_studio
    elif "lm_studio_readiness_service" in app.state._state:
        del app.state.lm_studio_readiness_service


def _ollama_tags_payload() -> dict[str, Any]:
    return {
        "models": [
            {
                "name": "qwen2.5-coder:7b",
                "size": 4_700_000_000,
                "details": {"parameter_size": "7B", "quantization_level": "Q4_K_M"},
            }
        ]
    }


def _lm_studio_models_payload() -> dict[str, Any]:
    return {
        "data": [
            {
                "id": "qwen2.5-coder-7b-instruct",
                "owned_by": "lmstudio",
                "context_length": 32_768,
            },
            {
                "id": "mistral-nemo-instruct",
                "owned_by": "lmstudio",
                "context_length": 128_000,
            },
        ]
    }


def _install_services(
    *,
    ollama_responses: list[_OllamaFetchResult],
    lm_studio_responses: list[_LMStudioFetchResult],
) -> tuple[_OllamaSequenceFetcher, _LMStudioSequenceFetcher]:
    ollama_fetcher = _OllamaSequenceFetcher(ollama_responses)
    lm_studio_fetcher = _LMStudioSequenceFetcher(lm_studio_responses)
    app.state.ollama_readiness_service = OllamaReadinessService(
        Settings(),
        fetcher=ollama_fetcher,
    )
    app.state.lm_studio_readiness_service = LMStudioReadinessService(
        Settings(),
        fetcher=lm_studio_fetcher,
    )
    return ollama_fetcher, lm_studio_fetcher


class TestModelHealthRoute:
    def test_requires_auth(self, no_auth_client: TestClient) -> None:
        resp = no_auth_client.get("/v1/model-health")
        assert resp.status_code == 401

    def test_summarizes_ready_local_runtimes(self, operator_read_client: TestClient) -> None:
        ollama_fetcher, lm_studio_fetcher = _install_services(
            ollama_responses=[_OllamaFetchResult(status_code=200, payload=_ollama_tags_payload())],
            lm_studio_responses=[
                _LMStudioFetchResult(status_code=200, payload=_lm_studio_models_payload())
            ],
        )

        resp = operator_read_client.get("/v1/model-health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_state"] == "ready"
        assert data["provider_count"] == 2
        assert data["ready_provider_count"] == 2
        assert data["total_model_count"] == 3
        assert data["providers"][0]["provider"] == "ollama"
        assert data["providers"][0]["model_count"] == 1
        assert data["providers"][1]["provider"] == "lm-studio"
        assert data["providers"][1]["model_count"] == 2
        assert ollama_fetcher.calls == ["http://ollama:11434/api/tags"]
        assert lm_studio_fetcher.calls == ["http://localhost:1234/v1/models"]

    def test_reports_attention_when_runtime_has_no_models(
        self,
        operator_read_client: TestClient,
    ) -> None:
        _install_services(
            ollama_responses=[_OllamaFetchResult(status_code=200, payload={"models": []})],
            lm_studio_responses=[_LMStudioFetchResult(status_code=None, error="offline")],
        )

        resp = operator_read_client.get("/v1/model-health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_state"] == "needs_attention"
        assert data["ready_provider_count"] == 0
        assert data["attention_provider_count"] == 1
        assert data["total_model_count"] == 0

    def test_applies_safe_provider_specific_overrides(
        self,
        operator_read_client: TestClient,
    ) -> None:
        ollama_fetcher, lm_studio_fetcher = _install_services(
            ollama_responses=[_OllamaFetchResult(status_code=200, payload=_ollama_tags_payload())],
            lm_studio_responses=[
                _LMStudioFetchResult(status_code=200, payload=_lm_studio_models_payload())
            ],
        )

        resp = operator_read_client.get(
            "/v1/model-health",
            params={
                "ollama_base_url": "http://localhost:11434/v1",
                "lm_studio_base_url": "http://127.0.0.1:1234",
            },
        )

        assert resp.status_code == 200
        assert resp.json()["overall_state"] == "ready"
        assert ollama_fetcher.calls == ["http://localhost:11434/api/tags"]
        assert lm_studio_fetcher.calls == ["http://127.0.0.1:1234/v1/models"]

    def test_unsafe_override_is_reported_without_fetching_provider(
        self,
        operator_read_client: TestClient,
    ) -> None:
        ollama_fetcher, lm_studio_fetcher = _install_services(
            ollama_responses=[_OllamaFetchResult(status_code=200, payload=_ollama_tags_payload())],
            lm_studio_responses=[
                _LMStudioFetchResult(status_code=200, payload=_lm_studio_models_payload())
            ],
        )

        resp = operator_read_client.get(
            "/v1/model-health",
            params={
                "ollama_base_url": "http://metadata.google.internal/computeMetadata/v1",
                "lm_studio_base_url": "http://localhost:1234/v1",
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_state"] == "ready"
        assert data["providers"][0]["state"] == "error"
        assert "base URL overrides" in data["providers"][0]["message"]
        assert ollama_fetcher.calls == []
        assert lm_studio_fetcher.calls == ["http://localhost:1234/v1/models"]
