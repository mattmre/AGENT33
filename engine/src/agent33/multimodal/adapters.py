"""Adapter contracts and real API implementations for multimodal tasks."""

from __future__ import annotations

import asyncio
import base64
from typing import Any, Protocol

import httpx

from agent33.config import settings
from agent33.multimodal.boundary import execute_multimodal_boundary_call
from agent33.multimodal.models import ModalityType, MultimodalRequest


class MultimodalAdapter(Protocol):
    """Contract for a modality-specific adapter."""

    def run(self, request: MultimodalRequest) -> dict[str, Any]:
        """Execute multimodal processing for a request."""

    async def run_async(self, request: MultimodalRequest) -> dict[str, Any]:
        """Execute multimodal processing asynchronously for a request."""


class STTAdapter:
    """OpenAI Whisper speech-to-text adapter."""

    def run(self, request: MultimodalRequest) -> dict[str, Any]:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run_async(request))
        raise RuntimeError(
            "Synchronous adapter.run() is not supported in an active event loop; "
            "use await adapter.run_async(...)."
        )

    async def run_async(self, request: MultimodalRequest) -> dict[str, Any]:
        self._validate_request(request)
        connector = "multimodal:speech_to_text"
        operation = "run"

        async def _perform_run(_request: object) -> dict[str, Any]:
            return await asyncio.to_thread(self._run_impl, request)

        return await execute_multimodal_boundary_call(
            connector=connector,
            operation=operation,
            payload={"request_id": request.id, "modality": request.modality.value},
            metadata={},
            call=_perform_run,
            timeout_seconds=float(request.requested_timeout_seconds),
        )

    @staticmethod
    def _validate_request(request: MultimodalRequest) -> None:
        if not request.input_artifact_base64:
            raise ValueError("speech_to_text requires input_artifact_base64")

    def _run_impl(self, request: MultimodalRequest) -> dict[str, Any]:
        api_key = settings.openai_api_key.get_secret_value()
        if not api_key:
            return {
                "output_text": (
                    f"[mock-stt] decoded {len(request.input_artifact_base64)} "
                    "chars (missing API key)"
                ),
                "output_artifact_id": "",
                "output_data": {"modality": ModalityType.SPEECH_TO_TEXT.value, "mock": True},
            }

        audio_bytes = base64.b64decode(request.input_artifact_base64)

        url = f"{settings.openai_base_url.rstrip('/') or 'https://api.openai.com/v1'}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}

        with httpx.Client(timeout=request.requested_timeout_seconds) as client:
            files = {"file": ("audio.webm", audio_bytes, "audio/webm")}
            data = {"model": "whisper-1"}
            resp = client.post(url, headers=headers, data=data, files=files)
            resp.raise_for_status()
            result = resp.json()

        return {
            "output_text": result.get("text", ""),
            "output_artifact_id": "",
            "output_data": {"modality": ModalityType.SPEECH_TO_TEXT.value, "provider": "openai"},
        }


class TTSAdapter:
    """ElevenLabs or OpenAI text-to-speech adapter."""

    def run(self, request: MultimodalRequest) -> dict[str, Any]:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run_async(request))
        raise RuntimeError(
            "Synchronous adapter.run() is not supported in an active event loop; "
            "use await adapter.run_async(...)."
        )

    async def run_async(self, request: MultimodalRequest) -> dict[str, Any]:
        self._validate_request(request)
        connector = "multimodal:text_to_speech"
        operation = "run"

        async def _perform_run(_request: object) -> dict[str, Any]:
            return await asyncio.to_thread(self._run_impl, request)

        return await execute_multimodal_boundary_call(
            connector=connector,
            operation=operation,
            payload={"request_id": request.id, "modality": request.modality.value},
            metadata={},
            call=_perform_run,
            timeout_seconds=float(request.requested_timeout_seconds),
        )

    @staticmethod
    def _validate_request(request: MultimodalRequest) -> None:
        if not request.input_text:
            raise ValueError("text_to_speech requires input_text")

    def _run_impl(self, request: MultimodalRequest) -> dict[str, Any]:
        eleven_key = settings.elevenlabs_api_key.get_secret_value()
        openai_key = settings.openai_api_key.get_secret_value()

        if eleven_key:
            # ElevenLabs TTS
            url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
            headers = {"xi-api-key": eleven_key, "Content-Type": "application/json"}
            payload = {
                "text": request.input_text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
            }
            with httpx.Client(timeout=request.requested_timeout_seconds) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                audio_b64 = base64.b64encode(resp.content).decode("utf-8")

            return {
                "output_text": "",
                "output_artifact_id": f"artifact-tts-{request.id}",
                "output_data": {
                    "modality": ModalityType.TEXT_TO_SPEECH.value,
                    "provider": "elevenlabs",
                    "audio_base64": audio_b64,
                },
            }
        elif openai_key:
            # OpenAI TTS
            url = f"{settings.openai_base_url.rstrip('/') or 'https://api.openai.com/v1'}/audio/speech"
            headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            payload = {"model": "tts-1", "input": request.input_text, "voice": "alloy"}
            with httpx.Client(timeout=request.requested_timeout_seconds) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                audio_b64 = base64.b64encode(resp.content).decode("utf-8")

            return {
                "output_text": "",
                "output_artifact_id": f"artifact-tts-{request.id}",
                "output_data": {
                    "modality": ModalityType.TEXT_TO_SPEECH.value,
                    "provider": "openai",
                    "audio_base64": audio_b64,
                },
            }
        else:
            return {
                "output_text": "",
                "output_artifact_id": f"artifact-tts-{request.id}",
                "output_data": {
                    "modality": ModalityType.TEXT_TO_SPEECH.value,
                    "mock": True,
                    "chars": len(request.input_text),
                },
            }


class VisionAdapter:
    """OpenAI GPT-4 Vision analysis adapter."""

    def run(self, request: MultimodalRequest) -> dict[str, Any]:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run_async(request))
        raise RuntimeError(
            "Synchronous adapter.run() is not supported in an active event loop; "
            "use await adapter.run_async(...)."
        )

    async def run_async(self, request: MultimodalRequest) -> dict[str, Any]:
        self._validate_request(request)
        connector = "multimodal:vision_analysis"
        operation = "run"

        async def _perform_run(_request: object) -> dict[str, Any]:
            return await asyncio.to_thread(self._run_impl, request)

        return await execute_multimodal_boundary_call(
            connector=connector,
            operation=operation,
            payload={"request_id": request.id, "modality": request.modality.value},
            metadata={},
            call=_perform_run,
            timeout_seconds=float(request.requested_timeout_seconds),
        )

    @staticmethod
    def _validate_request(request: MultimodalRequest) -> None:
        if not request.input_artifact_base64:
            raise ValueError("vision_analysis requires input_artifact_base64")

    def _run_impl(self, request: MultimodalRequest) -> dict[str, Any]:
        api_key = settings.openai_api_key.get_secret_value()
        if not api_key:
            return {
                "output_text": "mock vision analysis complete (missing API key)",
                "output_artifact_id": "",
                "output_data": {
                    "modality": ModalityType.VISION.value,
                    "mock": True,
                    "artifact_chars": len(request.input_artifact_base64),
                },
            }

        url = f"{settings.openai_base_url.rstrip('/') or 'https://api.openai.com/v1'}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        prompt = request.input_text or "Please describe this image in detail."

        # Detect mime type roughly from base64 if needed, but assuming jpeg for API
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{request.input_artifact_base64}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 1000,
        }

        with httpx.Client(timeout=request.requested_timeout_seconds) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            result = resp.json()
            text_resp = result["choices"][0]["message"]["content"]

        return {
            "output_text": text_resp,
            "output_artifact_id": "",
            "output_data": {
                "modality": ModalityType.VISION.value,
                "provider": "openai",
                "usage": result.get("usage", {}),
            },
        }
