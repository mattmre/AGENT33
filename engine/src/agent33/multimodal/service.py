"""In-memory multimodal orchestration service."""

from __future__ import annotations

import base64
import binascii
import time
from datetime import UTC, datetime

from agent33.config import settings
from agent33.multimodal.adapters import MultimodalAdapter, build_adapters
from agent33.multimodal.models import (
    ModalityType,
    MultimodalPolicy,
    MultimodalRequest,
    MultimodalResult,
    RequestState,
)


class PolicyViolationError(Exception):
    """Raised when a request violates tenant multimodal policy."""


class RequestNotFoundError(Exception):
    """Raised when a multimodal request is not found."""


class InvalidStateTransitionError(Exception):
    """Raised when a request lifecycle transition is invalid."""


class MultimodalService:
    """Manage multimodal requests, execution, and policy enforcement."""

    def __init__(
        self,
        *,
        adapters: dict[ModalityType, MultimodalAdapter] | None = None,
        retry_attempts: int | None = None,
        retry_base_delay_ms: int | None = None,
        provider_config: dict[str, str] | None = None,
        openai_api_key: str | None = None,
        openai_base_url: str | None = None,
    ) -> None:
        self._requests: dict[str, MultimodalRequest] = {}
        self._results: dict[str, MultimodalResult] = {}
        self._policies: dict[str, MultimodalPolicy] = {}
        self._provider_config = provider_config or {
            "stt": settings.multimodal_stt_provider,
            "tts": settings.multimodal_tts_provider,
            "vision": settings.multimodal_vision_provider,
        }
        self._openai_api_key = (
            openai_api_key
            if openai_api_key is not None
            else settings.openai_api_key.get_secret_value()
        )
        self._openai_base_url = openai_base_url or settings.multimodal_openai_base_url
        self._retry_attempts = max(
            1, retry_attempts if retry_attempts is not None else settings.multimodal_retry_attempts
        )
        self._retry_base_delay_ms = max(
            0,
            retry_base_delay_ms
            if retry_base_delay_ms is not None
            else settings.multimodal_retry_base_delay_ms,
        )
        self._adapters = adapters if adapters is not None else self._build_adapters()

    def set_policy(self, tenant_id: str, policy: MultimodalPolicy) -> None:
        self._policies[tenant_id] = policy

    def get_policy(self, tenant_id: str) -> MultimodalPolicy:
        return self._policies.get(tenant_id, MultimodalPolicy())

    def configure_providers(
        self,
        *,
        stt_provider: str | None = None,
        tts_provider: str | None = None,
        vision_provider: str | None = None,
    ) -> dict[str, object]:
        """Update runtime provider configuration and return validation health."""
        next_config = dict(self._provider_config)
        if stt_provider is not None:
            next_config["stt"] = stt_provider
        if tts_provider is not None:
            next_config["tts"] = tts_provider
        if vision_provider is not None:
            next_config["vision"] = vision_provider

        adapters = build_adapters(
            stt_provider=next_config["stt"],
            tts_provider=next_config["tts"],
            vision_provider=next_config["vision"],
            openai_api_key=self._openai_api_key,
            openai_base_url=self._openai_base_url,
        )
        self._provider_config = next_config
        self._adapters = adapters
        return self.provider_health()

    def provider_health(self) -> dict[str, object]:
        """Return runtime provider configuration and key validation status."""
        providers = {
            "stt": self._provider_config["stt"],
            "tts": self._provider_config["tts"],
            "vision": self._provider_config["vision"],
        }
        openai_required = any(name.startswith("openai") for name in providers.values())
        openai_key_configured = bool(self._openai_api_key)

        checks = {
            "openai": {
                "required": openai_required,
                "configured": openai_key_configured,
                "status": "healthy"
                if (not openai_required or openai_key_configured)
                else "unhealthy",
            }
        }

        return {
            "providers": providers,
            "checks": checks,
            "status": checks["openai"]["status"],
        }

    def provider_metrics(self) -> dict[str, object]:
        """Aggregate provider execution metrics from completed results."""
        aggregates: dict[str, dict[str, float | int]] = {}
        for result in self._results.values():
            provider = str(result.metadata.get("provider", "unknown"))
            duration_ms = int(result.metadata.get("duration_ms", 0))
            entry = aggregates.setdefault(
                provider,
                {"count": 0, "failures": 0, "total_duration_ms": 0},
            )
            entry["count"] = int(entry["count"]) + 1
            entry["total_duration_ms"] = int(entry["total_duration_ms"]) + duration_ms
            if result.state == RequestState.FAILED:
                entry["failures"] = int(entry["failures"]) + 1

        providers = {}
        for provider, entry in aggregates.items():
            count = int(entry["count"])
            failures = int(entry["failures"])
            total_duration = int(entry["total_duration_ms"])
            providers[provider] = {
                "count": count,
                "failures": failures,
                "failure_rate": (failures / count) if count else 0.0,
                "avg_duration_ms": (total_duration / count) if count else 0.0,
            }
        return {"providers": providers}

    def create_request(
        self,
        *,
        tenant_id: str,
        modality: ModalityType,
        input_text: str = "",
        input_artifact_id: str = "",
        input_artifact_base64: str = "",
        requested_timeout_seconds: int = 60,
        requested_by: str = "",
    ) -> MultimodalRequest:
        policy = self.get_policy(tenant_id)
        self._validate_policy(
            policy=policy,
            modality=modality,
            input_text=input_text,
            input_artifact_base64=input_artifact_base64,
            requested_timeout_seconds=requested_timeout_seconds,
        )
        request = MultimodalRequest(
            tenant_id=tenant_id,
            modality=modality,
            input_text=input_text,
            input_artifact_id=input_artifact_id,
            input_artifact_base64=input_artifact_base64,
            requested_timeout_seconds=requested_timeout_seconds,
            requested_by=requested_by,
        )
        self._requests[request.id] = request
        return request

    def list_requests(
        self,
        *,
        tenant_id: str | None = None,
        modality: ModalityType | None = None,
        state: RequestState | None = None,
        limit: int = 50,
    ) -> list[MultimodalRequest]:
        requests = list(self._requests.values())
        if tenant_id is not None:
            requests = [req for req in requests if req.tenant_id == tenant_id]
        if modality is not None:
            requests = [req for req in requests if req.modality == modality]
        if state is not None:
            requests = [req for req in requests if req.state == state]
        requests.sort(key=lambda req: req.created_at, reverse=True)
        return requests[:limit]

    def get_request(self, request_id: str, *, tenant_id: str | None = None) -> MultimodalRequest:
        request = self._requests.get(request_id)
        if request is None:
            raise RequestNotFoundError(f"Request not found: {request_id}")
        if tenant_id is not None and request.tenant_id != tenant_id:
            raise RequestNotFoundError(f"Request not found: {request_id}")
        return request

    def execute_request(
        self, request_id: str, *, tenant_id: str | None = None
    ) -> MultimodalRequest:
        request = self.get_request(request_id, tenant_id=tenant_id)
        if request.state in (RequestState.COMPLETED, RequestState.CANCELLED):
            raise InvalidStateTransitionError(
                f"Cannot execute request in state '{request.state.value}'"
            )
        request.state = RequestState.PROCESSING
        request.updated_at = datetime.now(UTC)
        started_at = request.updated_at
        perf_started = time.perf_counter()

        adapter = self._adapters[request.modality]
        output: dict[str, object] | None = None
        failure: Exception | None = None
        attempts = 0
        while attempts < self._retry_attempts:
            attempts += 1
            try:
                output = adapter.run(
                    request,
                    timeout_seconds=request.requested_timeout_seconds,
                )
                failure = None
                break
            except Exception as exc:  # noqa: BLE001 - surface final failure below
                failure = exc
                if attempts >= self._retry_attempts:
                    break
                if self._retry_base_delay_ms > 0:
                    delay_ms = self._retry_base_delay_ms * (2 ** (attempts - 1))
                    time.sleep(delay_ms / 1000)

        duration_ms = int((time.perf_counter() - perf_started) * 1000)
        provider_name = getattr(adapter, "provider_name", "unknown")
        if failure is not None or output is None:
            message = str(failure) if failure is not None else "execution failed"
            request.state = RequestState.FAILED
            request.error_message = message
            request.updated_at = datetime.now(UTC)
            result = MultimodalResult(
                request_id=request.id,
                state=RequestState.FAILED,
                started_at=started_at,
                completed_at=request.updated_at,
                metadata={
                    "error": message,
                    "provider": provider_name,
                    "attempts": attempts,
                    "duration_ms": duration_ms,
                },
            )
            self._results[result.id] = result
            request.result_id = result.id
            return request

        request.state = RequestState.COMPLETED
        request.updated_at = datetime.now(UTC)
        result = MultimodalResult(
            request_id=request.id,
            state=RequestState.COMPLETED,
            output_text=str(output.get("output_text", "")),
            output_artifact_id=str(output.get("output_artifact_id", "")),
            output_data=dict(output.get("output_data", {}))
            if isinstance(output.get("output_data", {}), dict)
            else {},
            started_at=started_at,
            completed_at=request.updated_at,
            metadata={
                "provider": provider_name,
                "attempts": attempts,
                "duration_ms": duration_ms,
            },
        )
        self._results[result.id] = result
        request.result_id = result.id
        request.error_message = ""
        return request

    def get_result(self, request_id: str, *, tenant_id: str | None = None) -> MultimodalResult:
        request = self.get_request(request_id, tenant_id=tenant_id)
        if not request.result_id:
            raise RequestNotFoundError(f"Result not available for request: {request_id}")
        result = self._results.get(request.result_id)
        if result is None:
            raise RequestNotFoundError(f"Result not available for request: {request_id}")
        return result

    def cancel_request(
        self, request_id: str, *, tenant_id: str | None = None
    ) -> MultimodalRequest:
        request = self.get_request(request_id, tenant_id=tenant_id)
        if request.state in (RequestState.COMPLETED, RequestState.FAILED):
            raise InvalidStateTransitionError(
                f"Cannot cancel request in state '{request.state.value}'"
            )
        request.state = RequestState.CANCELLED
        request.error_message = "Cancelled by operator"
        request.updated_at = datetime.now(UTC)
        return request

    def _build_adapters(self) -> dict[ModalityType, MultimodalAdapter]:
        return build_adapters(
            stt_provider=self._provider_config["stt"],
            tts_provider=self._provider_config["tts"],
            vision_provider=self._provider_config["vision"],
            openai_api_key=self._openai_api_key,
            openai_base_url=self._openai_base_url,
        )

    def _validate_policy(
        self,
        *,
        policy: MultimodalPolicy,
        modality: ModalityType,
        input_text: str,
        input_artifact_base64: str,
        requested_timeout_seconds: int,
    ) -> None:
        if modality not in policy.allowed_modalities:
            raise PolicyViolationError(f"Modality '{modality.value}' is not allowed")
        if len(input_text) > policy.max_text_chars:
            raise PolicyViolationError("input_text exceeds tenant max_text_chars policy")
        if requested_timeout_seconds > policy.max_timeout_seconds:
            raise PolicyViolationError("requested_timeout_seconds exceeds tenant timeout policy")

        artifact_bytes = self._artifact_size(input_artifact_base64)
        if artifact_bytes > policy.max_artifact_bytes:
            raise PolicyViolationError("input artifact exceeds tenant max_artifact_bytes policy")

    @staticmethod
    def _artifact_size(input_artifact_base64: str) -> int:
        if not input_artifact_base64:
            return 0
        try:
            decoded = base64.b64decode(input_artifact_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise PolicyViolationError("input_artifact_base64 is invalid base64") from exc
        return len(decoded)
