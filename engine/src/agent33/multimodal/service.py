"""In-memory multimodal orchestration service."""

from __future__ import annotations

import base64
import binascii
from datetime import UTC, datetime

from agent33.multimodal.adapters import MultimodalAdapter, STTAdapter, TTSAdapter, VisionAdapter
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

    def __init__(self) -> None:
        self._requests: dict[str, MultimodalRequest] = {}
        self._results: dict[str, MultimodalResult] = {}
        self._policies: dict[str, MultimodalPolicy] = {}
        self._adapters: dict[ModalityType, MultimodalAdapter] = {
            ModalityType.SPEECH_TO_TEXT: STTAdapter(),
            ModalityType.TEXT_TO_SPEECH: TTSAdapter(),
            ModalityType.VISION: VisionAdapter(),
        }

    def set_policy(self, tenant_id: str, policy: MultimodalPolicy) -> None:
        self._policies[tenant_id] = policy

    def get_policy(self, tenant_id: str) -> MultimodalPolicy:
        return self._policies.get(tenant_id, MultimodalPolicy())

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

    async def execute_request(
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

        adapter = self._adapters[request.modality]
        try:
            output = await adapter.run(request)
        except Exception as exc:
            request.state = RequestState.FAILED
            request.error_message = str(exc)
            request.updated_at = datetime.now(UTC)
            result = MultimodalResult(
                request_id=request.id,
                state=RequestState.FAILED,
                started_at=started_at,
                completed_at=request.updated_at,
                metadata={"error": str(exc)},
            )
            self._results[result.id] = result
            request.result_id = result.id
            return request

        request.state = RequestState.COMPLETED
        request.updated_at = datetime.now(UTC)
        result = MultimodalResult(
            request_id=request.id,
            state=RequestState.COMPLETED,
            output_text=output.get("output_text", ""),
            output_artifact_id=output.get("output_artifact_id", ""),
            output_data=output.get("output_data", {}),
            started_at=started_at,
            completed_at=request.updated_at,
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
