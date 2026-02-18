"""Adapter contracts, mock adapters, and provider-backed multimodal adapters."""

from __future__ import annotations

import base64
from typing import Any, Protocol

import httpx

from agent33.multimodal.models import ModalityType, MultimodalRequest


class MultimodalAdapter(Protocol):
    """Contract for modality-specific adapters."""

    provider_name: str

    def run(self, request: MultimodalRequest, *, timeout_seconds: int) -> dict[str, Any]:
        """Execute multimodal processing for a request."""


class STTAdapter:
    """Deterministic speech-to-text mock adapter."""

    provider_name = "mock"

    def run(self, request: MultimodalRequest, *, timeout_seconds: int) -> dict[str, Any]:
        del timeout_seconds
        if not request.input_artifact_base64:
            raise ValueError("speech_to_text requires input_artifact_base64")
        return {
            "output_text": f"[mock-stt] decoded {len(request.input_artifact_base64)} chars",
            "output_artifact_id": "",
            "output_data": {
                "modality": ModalityType.SPEECH_TO_TEXT.value,
                "provider": self.provider_name,
            },
        }


class TTSAdapter:
    """Deterministic text-to-speech mock adapter."""

    provider_name = "mock"

    def run(self, request: MultimodalRequest, *, timeout_seconds: int) -> dict[str, Any]:
        del timeout_seconds
        if not request.input_text:
            raise ValueError("text_to_speech requires input_text")
        return {
            "output_text": "",
            "output_artifact_id": f"artifact-tts-{request.id}",
            "output_data": {
                "modality": ModalityType.TEXT_TO_SPEECH.value,
                "chars": len(request.input_text),
                "provider": self.provider_name,
            },
        }


class VisionAdapter:
    """Deterministic vision-analysis mock adapter."""

    provider_name = "mock"

    def run(self, request: MultimodalRequest, *, timeout_seconds: int) -> dict[str, Any]:
        del timeout_seconds
        if not request.input_artifact_base64:
            raise ValueError("vision_analysis requires input_artifact_base64")
        return {
            "output_text": "mock vision analysis complete",
            "output_artifact_id": "",
            "output_data": {
                "modality": ModalityType.VISION.value,
                "artifact_chars": len(request.input_artifact_base64),
                "provider": self.provider_name,
            },
        }


class _OpenAIBaseAdapter:
    """Shared helper for OpenAI-backed adapters."""

    provider_name = "openai"

    def __init__(self, *, api_key: str, base_url: str) -> None:
        if not api_key:
            raise ValueError("OpenAI adapter requires a non-empty API key")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def _request(
        self,
        *,
        method: str,
        endpoint: str,
        timeout_seconds: int,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.request(
                method=method,
                url=f"{self._base_url}{endpoint}",
                headers=headers,
                json=json,
                data=data,
                files=files,
            )
        response.raise_for_status()
        return response


class OpenAIWhisperAdapter(_OpenAIBaseAdapter):
    """OpenAI Whisper speech-to-text adapter."""

    provider_name = "openai_whisper"

    def run(self, request: MultimodalRequest, *, timeout_seconds: int) -> dict[str, Any]:
        if not request.input_artifact_base64:
            raise ValueError("speech_to_text requires input_artifact_base64")
        audio_bytes = base64.b64decode(request.input_artifact_base64, validate=True)
        response = self._request(
            method="POST",
            endpoint="/audio/transcriptions",
            timeout_seconds=timeout_seconds,
            data={"model": "whisper-1"},
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
        )
        payload = response.json()
        text = str(payload.get("text", ""))
        return {
            "output_text": text,
            "output_artifact_id": "",
            "output_data": {"provider": self.provider_name, "model": "whisper-1"},
        }


class OpenAITTSAdapter(_OpenAIBaseAdapter):
    """OpenAI text-to-speech adapter."""

    provider_name = "openai_tts"

    def run(self, request: MultimodalRequest, *, timeout_seconds: int) -> dict[str, Any]:
        if not request.input_text:
            raise ValueError("text_to_speech requires input_text")
        response = self._request(
            method="POST",
            endpoint="/audio/speech",
            timeout_seconds=timeout_seconds,
            json={
                "model": "gpt-4o-mini-tts",
                "voice": "alloy",
                "input": request.input_text,
            },
        )
        audio_bytes = response.content
        return {
            "output_text": "",
            "output_artifact_id": f"artifact-tts-{request.id}",
            "output_data": {
                "provider": self.provider_name,
                "model": "gpt-4o-mini-tts",
                "audio_bytes": len(audio_bytes),
            },
        }


class OpenAIVisionAdapter(_OpenAIBaseAdapter):
    """OpenAI GPT-4o vision adapter."""

    provider_name = "openai_vision"

    def run(self, request: MultimodalRequest, *, timeout_seconds: int) -> dict[str, Any]:
        if not request.input_artifact_base64:
            raise ValueError("vision_analysis requires input_artifact_base64")
        response = self._request(
            method="POST",
            endpoint="/chat/completions",
            timeout_seconds=timeout_seconds,
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe the uploaded image."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{request.input_artifact_base64}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 300,
            },
        )
        payload = response.json()
        choices = payload.get("choices", [])
        if not choices:
            raise ValueError("vision provider returned no choices")
        message = choices[0].get("message", {})
        output_text = str(message.get("content", "")).strip()
        return {
            "output_text": output_text,
            "output_artifact_id": "",
            "output_data": {"provider": self.provider_name, "model": "gpt-4o-mini"},
        }


def build_adapters(
    *,
    stt_provider: str,
    tts_provider: str,
    vision_provider: str,
    openai_api_key: str,
    openai_base_url: str,
) -> dict[ModalityType, MultimodalAdapter]:
    """Build adapter map from provider configuration."""
    adapters: dict[ModalityType, MultimodalAdapter] = {}

    if stt_provider == "mock":
        adapters[ModalityType.SPEECH_TO_TEXT] = STTAdapter()
    elif stt_provider == "openai_whisper":
        adapters[ModalityType.SPEECH_TO_TEXT] = OpenAIWhisperAdapter(
            api_key=openai_api_key,
            base_url=openai_base_url,
        )
    else:
        raise ValueError(f"Unsupported STT provider: {stt_provider}")

    if tts_provider == "mock":
        adapters[ModalityType.TEXT_TO_SPEECH] = TTSAdapter()
    elif tts_provider == "openai_tts":
        adapters[ModalityType.TEXT_TO_SPEECH] = OpenAITTSAdapter(
            api_key=openai_api_key,
            base_url=openai_base_url,
        )
    else:
        raise ValueError(f"Unsupported TTS provider: {tts_provider}")

    if vision_provider == "mock":
        adapters[ModalityType.VISION] = VisionAdapter()
    elif vision_provider == "openai_vision":
        adapters[ModalityType.VISION] = OpenAIVisionAdapter(
            api_key=openai_api_key,
            base_url=openai_base_url,
        )
    else:
        raise ValueError(f"Unsupported vision provider: {vision_provider}")

    return adapters
