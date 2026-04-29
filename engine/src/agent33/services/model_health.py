"""Unified local model health for beginner setup UX."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from agent33.services.lm_studio_readiness import (
        LMStudioReadinessService,
        LMStudioStatusResponse,
    )
    from agent33.services.ollama_readiness import (
        OllamaReadinessService,
        OllamaStatusResponse,
    )

LocalModelProvider = Literal["ollama", "lm-studio"]
LocalModelProviderState = Literal["available", "empty", "unavailable", "error"]
UnifiedModelHealthState = Literal["ready", "needs_attention", "unavailable"]


class LocalModelProviderHealth(BaseModel):
    """Provider-level model health safe for operator setup UI."""

    provider: LocalModelProvider
    label: str
    state: LocalModelProviderState
    ok: bool
    base_url: str
    default_model: str
    checked_at: datetime
    model_count: int = 0
    message: str
    action: str


class UnifiedModelHealthResponse(BaseModel):
    """Combined local runtime health across supported beginner providers."""

    provider_count: int = 0
    ready_provider_count: int = 0
    attention_provider_count: int = 0
    total_model_count: int = 0
    overall_state: UnifiedModelHealthState
    summary: str
    checked_at: datetime
    providers: list[LocalModelProviderHealth] = Field(default_factory=list)


class ModelHealthService:
    """Aggregate local model readiness without duplicating provider probes."""

    def __init__(
        self,
        *,
        ollama_service: OllamaReadinessService,
        lm_studio_service: LMStudioReadinessService,
    ) -> None:
        self._ollama_service = ollama_service
        self._lm_studio_service = lm_studio_service

    async def status(
        self,
        *,
        ollama_base_url: str | None = None,
        lm_studio_base_url: str | None = None,
    ) -> UnifiedModelHealthResponse:
        """Return a unified health summary for local model providers."""

        checked_at = datetime.now(UTC)
        results = await asyncio.gather(
            self._ollama_service.status(base_url=ollama_base_url),
            self._lm_studio_service.status(base_url=lm_studio_base_url),
            return_exceptions=True,
        )
        providers = [
            self._coerce_result(
                results[0],
                checked_at,
                provider="ollama",
                label="Ollama",
            ),
            self._coerce_result(
                results[1],
                checked_at,
                provider="lm-studio",
                label="LM Studio",
            ),
        ]
        ready_provider_count = sum(1 for provider in providers if provider.ok)
        attention_provider_count = sum(
            1 for provider in providers if provider.state in {"empty", "error"}
        )
        total_model_count = sum(provider.model_count for provider in providers)
        overall_state = self._overall_state(
            ready_provider_count=ready_provider_count,
            attention_provider_count=attention_provider_count,
        )

        return UnifiedModelHealthResponse(
            provider_count=len(providers),
            ready_provider_count=ready_provider_count,
            attention_provider_count=attention_provider_count,
            total_model_count=total_model_count,
            overall_state=overall_state,
            summary=self._summary(
                overall_state=overall_state,
                ready_provider_count=ready_provider_count,
                total_model_count=total_model_count,
            ),
            checked_at=checked_at,
            providers=providers,
        )

    @staticmethod
    def _overall_state(
        *,
        ready_provider_count: int,
        attention_provider_count: int,
    ) -> UnifiedModelHealthState:
        if ready_provider_count > 0:
            return "ready"
        if attention_provider_count > 0:
            return "needs_attention"
        return "unavailable"

    @staticmethod
    def _summary(
        *,
        overall_state: UnifiedModelHealthState,
        ready_provider_count: int,
        total_model_count: int,
    ) -> str:
        if overall_state == "ready":
            provider_label = "runtime" if ready_provider_count == 1 else "runtimes"
            model_label = "model" if total_model_count == 1 else "models"
            return (
                f"{ready_provider_count} local {provider_label} ready with "
                f"{total_model_count} detected {model_label}."
            )
        if overall_state == "needs_attention":
            return "Local runtimes responded, but a model still needs to be installed or loaded."
        return (
            "No local model runtime is reachable yet. Start Ollama or LM Studio "
            "to use local models."
        )

    @staticmethod
    def _coerce_result(
        result: OllamaStatusResponse | LMStudioStatusResponse | BaseException,
        checked_at: datetime,
        *,
        provider: LocalModelProvider,
        label: str,
    ) -> LocalModelProviderHealth:
        if isinstance(result, BaseException):
            return LocalModelProviderHealth(
                provider=provider,
                label=label,
                state="error",
                ok=False,
                base_url="",
                default_model="",
                checked_at=checked_at,
                message=f"Could not check {label}: {result}",
                action=f"Check the {label} runtime configuration.",
            )
        return LocalModelProviderHealth(
            provider=provider,
            label=label,
            state=result.state,
            ok=result.ok,
            base_url=result.base_url,
            default_model=result.default_model,
            checked_at=result.checked_at,
            model_count=result.count,
            message=result.message,
            action=ModelHealthService._action_for_state(label, result.state),
        )

    @staticmethod
    def _action_for_state(provider_label: str, state: LocalModelProviderState) -> str:
        if state == "available":
            return f"Choose a detected {provider_label} model for local workflows."
        if state == "empty":
            return f"Install or load a model in {provider_label}, then refresh health."
        if state == "unavailable":
            return f"Start {provider_label}, then refresh health."
        return f"Check the {provider_label} base URL and runtime settings."
