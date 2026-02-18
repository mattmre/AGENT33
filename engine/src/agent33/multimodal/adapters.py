"""Adapter contracts and deterministic Stage 1 mock implementations."""

from __future__ import annotations

from typing import Any, Protocol

from agent33.multimodal.models import ModalityType, MultimodalRequest


class MultimodalAdapter(Protocol):
    """Contract for a modality-specific adapter."""

    def run(self, request: MultimodalRequest) -> dict[str, Any]:
        """Execute multimodal processing for a request."""


class STTAdapter:
    """Deterministic speech-to-text mock adapter."""

    def run(self, request: MultimodalRequest) -> dict[str, Any]:
        if not request.input_artifact_base64:
            raise ValueError("speech_to_text requires input_artifact_base64")
        return {
            "output_text": f"[mock-stt] decoded {len(request.input_artifact_base64)} chars",
            "output_artifact_id": "",
            "output_data": {"modality": ModalityType.SPEECH_TO_TEXT.value},
        }


class TTSAdapter:
    """Deterministic text-to-speech mock adapter."""

    def run(self, request: MultimodalRequest) -> dict[str, Any]:
        if not request.input_text:
            raise ValueError("text_to_speech requires input_text")
        return {
            "output_text": "",
            "output_artifact_id": f"artifact-tts-{request.id}",
            "output_data": {
                "modality": ModalityType.TEXT_TO_SPEECH.value,
                "chars": len(request.input_text),
            },
        }


class VisionAdapter:
    """Deterministic vision-analysis mock adapter."""

    def run(self, request: MultimodalRequest) -> dict[str, Any]:
        if not request.input_artifact_base64:
            raise ValueError("vision_analysis requires input_artifact_base64")
        return {
            "output_text": "mock vision analysis complete",
            "output_artifact_id": "",
            "output_data": {
                "modality": ModalityType.VISION.value,
                "artifact_chars": len(request.input_artifact_base64),
            },
        }
