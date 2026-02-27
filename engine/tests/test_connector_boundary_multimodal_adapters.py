"""Connector boundary governance coverage for multimodal adapters."""

from __future__ import annotations

import base64

import pytest
from pydantic import SecretStr

from agent33.multimodal.adapters import STTAdapter, TTSAdapter, VisionAdapter
from agent33.multimodal.models import ModalityType, MultimodalRequest


def _stt_request() -> MultimodalRequest:
    return MultimodalRequest(
        modality=ModalityType.SPEECH_TO_TEXT,
        input_artifact_base64=base64.b64encode(b"audio").decode("utf-8"),
        requested_timeout_seconds=5,
    )


def _tts_request() -> MultimodalRequest:
    return MultimodalRequest(
        modality=ModalityType.TEXT_TO_SPEECH,
        input_text="hello multimodal",
        requested_timeout_seconds=5,
    )


def _vision_request() -> MultimodalRequest:
    return MultimodalRequest(
        modality=ModalityType.VISION,
        input_artifact_base64=base64.b64encode(b"image").decode("utf-8"),
        requested_timeout_seconds=5,
    )


@pytest.mark.parametrize(
    ("adapter", "request_factory", "connector"),
    [
        (STTAdapter(), _stt_request, "multimodal:speech_to_text"),
        (TTSAdapter(), _tts_request, "multimodal:text_to_speech"),
        (VisionAdapter(), _vision_request, "multimodal:vision_analysis"),
    ],
)
@pytest.mark.asyncio
async def test_adapter_governance_blocked_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
    adapter: STTAdapter | TTSAdapter | VisionAdapter,
    request_factory,
    connector: str,
) -> None:
    monkeypatch.setattr("agent33.config.settings.connector_boundary_enabled", True)
    monkeypatch.setattr("agent33.config.settings.connector_policy_pack", "default")
    monkeypatch.setattr(
        "agent33.config.settings.connector_governance_blocked_connectors",
        connector,
    )
    monkeypatch.setattr("agent33.config.settings.connector_governance_blocked_operations", "")
    monkeypatch.setattr("agent33.config.settings.openai_api_key", SecretStr(""))
    monkeypatch.setattr("agent33.config.settings.elevenlabs_api_key", SecretStr(""))

    with pytest.raises(RuntimeError) as excinfo:
        await adapter.run_async(request_factory())
    assert str(excinfo.value) == (
        f"Connector governance blocked {connector}/run: connector blocked by policy: {connector}"
    )


@pytest.mark.asyncio
async def test_boundary_disabled_mock_paths_preserve_response_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("agent33.config.settings.connector_boundary_enabled", False)
    monkeypatch.setattr("agent33.config.settings.connector_governance_blocked_connectors", "")
    monkeypatch.setattr("agent33.config.settings.connector_governance_blocked_operations", "")
    monkeypatch.setattr("agent33.config.settings.openai_api_key", SecretStr(""))
    monkeypatch.setattr("agent33.config.settings.elevenlabs_api_key", SecretStr(""))

    stt_response = await STTAdapter().run_async(_stt_request())
    assert stt_response["output_artifact_id"] == ""
    assert stt_response["output_data"] == {
        "modality": ModalityType.SPEECH_TO_TEXT.value,
        "mock": True,
    }

    tts_request = _tts_request()
    tts_response = await TTSAdapter().run_async(tts_request)
    assert tts_response["output_text"] == ""
    assert tts_response["output_artifact_id"] == f"artifact-tts-{tts_request.id}"
    assert tts_response["output_data"] == {
        "modality": ModalityType.TEXT_TO_SPEECH.value,
        "mock": True,
        "chars": len(tts_request.input_text),
    }

    vision_request = _vision_request()
    vision_response = await VisionAdapter().run_async(vision_request)
    assert vision_response["output_text"] == "mock vision analysis complete (missing API key)"
    assert vision_response["output_artifact_id"] == ""
    assert vision_response["output_data"] == {
        "modality": ModalityType.VISION.value,
        "mock": True,
        "artifact_chars": len(vision_request.input_artifact_base64),
    }


@pytest.mark.parametrize(
    ("adapter", "request_factory", "connector"),
    [
        (STTAdapter(), _stt_request, "multimodal:speech_to_text"),
        (TTSAdapter(), _tts_request, "multimodal:text_to_speech"),
        (VisionAdapter(), _vision_request, "multimodal:vision_analysis"),
    ],
)
def test_sync_run_path_uses_async_boundary_governance(
    monkeypatch: pytest.MonkeyPatch,
    adapter: STTAdapter | TTSAdapter | VisionAdapter,
    request_factory,
    connector: str,
) -> None:
    monkeypatch.setattr("agent33.config.settings.connector_boundary_enabled", True)
    monkeypatch.setattr("agent33.config.settings.connector_policy_pack", "default")
    monkeypatch.setattr(
        "agent33.config.settings.connector_governance_blocked_connectors",
        connector,
    )
    monkeypatch.setattr("agent33.config.settings.connector_governance_blocked_operations", "")
    monkeypatch.setattr("agent33.config.settings.openai_api_key", SecretStr(""))
    monkeypatch.setattr("agent33.config.settings.elevenlabs_api_key", SecretStr(""))

    with pytest.raises(RuntimeError) as excinfo:
        adapter.run(request_factory())
    assert str(excinfo.value) == (
        f"Connector governance blocked {connector}/run: connector blocked by policy: {connector}"
    )


@pytest.mark.parametrize(
    ("adapter", "request_factory", "modality"),
    [
        (STTAdapter(), _stt_request, ModalityType.SPEECH_TO_TEXT.value),
        (TTSAdapter(), _tts_request, ModalityType.TEXT_TO_SPEECH.value),
        (VisionAdapter(), _vision_request, ModalityType.VISION.value),
    ],
)
def test_sync_run_wrapper_delegates_to_async_path(
    adapter: STTAdapter | TTSAdapter | VisionAdapter,
    request_factory,
    modality: str,
) -> None:
    request = request_factory()
    seen: dict[str, object] = {}
    expected = {
        "output_text": "",
        "output_artifact_id": "artifact-sync-wrapper",
        "output_data": {"modality": modality, "wrapped": True},
    }

    async def _fake_run_async(received_request: MultimodalRequest) -> dict[str, object]:
        seen["request"] = received_request
        return expected

    adapter.run_async = _fake_run_async  # type: ignore[method-assign]
    response = adapter.run(request)
    assert seen["request"] is request
    assert response == expected


@pytest.mark.parametrize(
    ("adapter", "request_factory"),
    [
        (STTAdapter(), _stt_request),
        (TTSAdapter(), _tts_request),
        (VisionAdapter(), _vision_request),
    ],
)
@pytest.mark.asyncio
async def test_sync_run_path_rejected_inside_active_event_loop(
    adapter: STTAdapter | TTSAdapter | VisionAdapter,
    request_factory,
) -> None:
    with pytest.raises(
        RuntimeError,
        match=(
            r"Synchronous adapter.run\(\) is not supported in an active event loop; "
            r"use await adapter.run_async\(\.\.\.\)\."
        ),
    ):
        adapter.run(request_factory())


@pytest.mark.parametrize(
    ("adapter", "request_factory", "connector", "modality"),
    [
        (STTAdapter(), _stt_request, "multimodal:speech_to_text", ModalityType.SPEECH_TO_TEXT),
        (TTSAdapter(), _tts_request, "multimodal:text_to_speech", ModalityType.TEXT_TO_SPEECH),
        (VisionAdapter(), _vision_request, "multimodal:vision_analysis", ModalityType.VISION),
    ],
)
@pytest.mark.asyncio
async def test_run_async_uses_boundary_connector_and_operation_contract(
    monkeypatch: pytest.MonkeyPatch,
    adapter: STTAdapter | TTSAdapter | VisionAdapter,
    request_factory,
    connector: str,
    modality: ModalityType,
) -> None:
    monkeypatch.setattr("agent33.config.settings.connector_boundary_enabled", False)
    monkeypatch.setattr("agent33.config.settings.openai_api_key", SecretStr(""))
    monkeypatch.setattr("agent33.config.settings.elevenlabs_api_key", SecretStr(""))

    captured: dict[str, object] = {}

    async def _fake_boundary_call(**kwargs):
        captured.update(kwargs)
        return {
            "output_text": "",
            "output_artifact_id": "",
            "output_data": {"modality": modality.value, "via": "boundary"},
        }

    monkeypatch.setattr(
        "agent33.multimodal.adapters.execute_multimodal_boundary_call", _fake_boundary_call
    )

    request = request_factory()
    response = await adapter.run_async(request)

    assert response["output_data"] == {"modality": modality.value, "via": "boundary"}
    assert captured["connector"] == connector
    assert captured["operation"] == "run"
    assert captured["payload"] == {"request_id": request.id, "modality": modality.value}
    assert captured["metadata"] == {}
    assert captured["timeout_seconds"] == float(request.requested_timeout_seconds)
