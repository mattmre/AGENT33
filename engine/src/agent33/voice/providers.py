"""Provider abstraction for TTS and STT backends.

Phase 35 delivers a provider-agnostic interface so the voice sidecar can swap
between local (Piper, Whisper) and cloud (ElevenLabs, OpenAI) backends without
touching orchestration code.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Audio format / metadata
# ------------------------------------------------------------------


class AudioEncoding(StrEnum):
    """Supported audio encodings for voice pipeline I/O."""

    PCM_S16LE = "pcm_s16le"
    MP3 = "mp3"
    OGG_OPUS = "ogg_opus"
    WAV = "wav"
    FLAC = "flac"


@dataclass(frozen=True)
class AudioFormat:
    """Describes the audio wire format for a voice session."""

    encoding: AudioEncoding = AudioEncoding.PCM_S16LE
    sample_rate: int = 16000
    channels: int = 1
    bit_depth: int = 16

    def __post_init__(self) -> None:
        if self.sample_rate < 8000 or self.sample_rate > 48000:
            raise ValueError(f"sample_rate must be 8000..48000, got {self.sample_rate}")
        if self.channels < 1 or self.channels > 2:
            raise ValueError(f"channels must be 1 or 2, got {self.channels}")
        if self.bit_depth not in {8, 16, 24, 32}:
            raise ValueError(f"bit_depth must be 8/16/24/32, got {self.bit_depth}")


@dataclass
class TTSResult:
    """Output from a TTS synthesis call."""

    audio_data: bytes
    audio_format: AudioFormat
    duration_ms: float = 0.0
    provider: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class STTResult:
    """Output from an STT transcription call."""

    text: str
    confidence: float = 0.0
    language: str = ""
    duration_ms: float = 0.0
    provider: str = ""
    is_partial: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# Provider protocols
# ------------------------------------------------------------------


@runtime_checkable
class TTSProvider(Protocol):
    """Protocol for text-to-speech providers.

    Implementations must provide ``synthesize`` and ``provider_name``.
    The voice sidecar dispatches to whichever TTSProvider is configured
    at startup, allowing hot-swap between local and cloud backends.
    """

    @property
    def provider_name(self) -> str: ...

    async def synthesize(
        self,
        text: str,
        *,
        voice_id: str = "",
        audio_format: AudioFormat | None = None,
    ) -> TTSResult:
        """Convert *text* to audio bytes."""
        ...

    async def list_voices(self) -> list[dict[str, Any]]:
        """Return available voice identifiers for this provider."""
        ...

    async def health_check(self) -> bool:
        """Return True if the provider is reachable and ready."""
        ...


@runtime_checkable
class STTProvider(Protocol):
    """Protocol for speech-to-text providers.

    Implementations must provide ``transcribe`` and ``provider_name``.
    """

    @property
    def provider_name(self) -> str: ...

    async def transcribe(
        self,
        audio_data: bytes,
        *,
        audio_format: AudioFormat | None = None,
        language: str = "",
    ) -> STTResult:
        """Transcribe *audio_data* to text."""
        ...

    async def health_check(self) -> bool:
        """Return True if the provider is reachable and ready."""
        ...


# ------------------------------------------------------------------
# Base implementations (ABC for subclass convenience)
# ------------------------------------------------------------------


class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers with shared helpers."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        *,
        voice_id: str = "",
        audio_format: AudioFormat | None = None,
    ) -> TTSResult: ...

    async def list_voices(self) -> list[dict[str, Any]]:
        """Default: no discoverable voices."""
        return []

    async def health_check(self) -> bool:
        """Default: always healthy if constructed."""
        return True


class BaseSTTProvider(ABC):
    """Abstract base class for STT providers with shared helpers."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        *,
        audio_format: AudioFormat | None = None,
        language: str = "",
    ) -> STTResult: ...

    async def health_check(self) -> bool:
        """Default: always healthy if constructed."""
        return True


# ------------------------------------------------------------------
# Stub / local providers
# ------------------------------------------------------------------


class StubTTSProvider(BaseTTSProvider):
    """No-op TTS provider for testing and development.

    Returns a deterministic zero-filled audio buffer so callers can
    exercise the full pipeline without a real TTS backend.
    """

    @property
    def provider_name(self) -> str:
        return "stub"

    async def synthesize(
        self,
        text: str,
        *,
        voice_id: str = "",
        audio_format: AudioFormat | None = None,
    ) -> TTSResult:
        if not text:
            raise ValueError("text must not be empty")
        fmt = audio_format or AudioFormat()
        # Generate a deterministic silence buffer: ~100ms of audio at the
        # requested sample rate.
        sample_bytes = fmt.bit_depth // 8
        num_samples = int(fmt.sample_rate * 0.1) * fmt.channels
        audio_data = b"\x00" * (num_samples * sample_bytes)
        return TTSResult(
            audio_data=audio_data,
            audio_format=fmt,
            duration_ms=100.0,
            provider=self.provider_name,
            metadata={"voice_id": voice_id or "stub-default", "text_length": len(text)},
        )

    async def list_voices(self) -> list[dict[str, Any]]:
        return [
            {"voice_id": "stub-default", "name": "Stub Default", "provider": "stub"},
            {"voice_id": "stub-alt", "name": "Stub Alternate", "provider": "stub"},
        ]


class StubSTTProvider(BaseSTTProvider):
    """No-op STT provider for testing and development.

    Returns a fixed transcription string so callers can exercise
    the full pipeline without a real STT backend.
    """

    @property
    def provider_name(self) -> str:
        return "stub"

    async def transcribe(
        self,
        audio_data: bytes,
        *,
        audio_format: AudioFormat | None = None,
        language: str = "",
    ) -> STTResult:
        if not audio_data:
            raise ValueError("audio_data must not be empty")
        return STTResult(
            text="[stub transcription]",
            confidence=1.0,
            language=language or "en",
            duration_ms=0.0,
            provider=self.provider_name,
            metadata={"audio_bytes": len(audio_data)},
        )


# ------------------------------------------------------------------
# Local provider stubs (Piper TTS / Whisper STT)
# ------------------------------------------------------------------


class PiperTTSProvider(BaseTTSProvider):
    """Local Piper TTS provider stub.

    Piper (https://github.com/rhasspy/piper) is a fast, local neural TTS
    engine. This stub implements the provider interface so the sidecar
    configuration layer can reference it; actual Piper binary invocation
    is deferred until the ``piper-phonemize`` dependency is wired.
    """

    def __init__(self, *, model_path: str = "", voice_id: str = "en_US-lessac-medium") -> None:
        self._model_path = model_path
        self._default_voice_id = voice_id

    @property
    def provider_name(self) -> str:
        return "piper"

    async def synthesize(
        self,
        text: str,
        *,
        voice_id: str = "",
        audio_format: AudioFormat | None = None,
    ) -> TTSResult:
        if not text:
            raise ValueError("text must not be empty")
        fmt = audio_format or AudioFormat(encoding=AudioEncoding.WAV, sample_rate=22050)
        # Stub: generate silence. Real implementation would invoke piper binary.
        sample_bytes = fmt.bit_depth // 8
        num_samples = int(fmt.sample_rate * 0.1) * fmt.channels
        audio_data = b"\x00" * (num_samples * sample_bytes)
        logger.debug(
            "piper.synthesize_stub text_length=%d voice_id=%s",
            len(text),
            voice_id or self._default_voice_id,
        )
        return TTSResult(
            audio_data=audio_data,
            audio_format=fmt,
            duration_ms=100.0,
            provider=self.provider_name,
            metadata={
                "voice_id": voice_id or self._default_voice_id,
                "model_path": self._model_path,
                "stub": True,
            },
        )

    async def list_voices(self) -> list[dict[str, Any]]:
        return [
            {
                "voice_id": self._default_voice_id,
                "name": "Piper Lessac Medium",
                "provider": "piper",
            },
        ]

    async def health_check(self) -> bool:
        # Real implementation would verify piper binary is accessible
        return True


class WhisperSTTProvider(BaseSTTProvider):
    """Local Whisper STT provider stub.

    OpenAI Whisper (https://github.com/openai/whisper) runs locally for
    transcription. This stub implements the provider interface; actual
    Whisper model loading is deferred until the ``openai-whisper``
    dependency is wired.
    """

    def __init__(self, *, model_size: str = "base", device: str = "cpu") -> None:
        self._model_size = model_size
        self._device = device

    @property
    def provider_name(self) -> str:
        return "whisper"

    async def transcribe(
        self,
        audio_data: bytes,
        *,
        audio_format: AudioFormat | None = None,
        language: str = "",
    ) -> STTResult:
        if not audio_data:
            raise ValueError("audio_data must not be empty")
        logger.debug(
            "whisper.transcribe_stub audio_bytes=%d model_size=%s",
            len(audio_data),
            self._model_size,
        )
        # Stub: return placeholder. Real implementation would run whisper model.
        return STTResult(
            text="[whisper transcription placeholder]",
            confidence=0.95,
            language=language or "en",
            duration_ms=0.0,
            provider=self.provider_name,
            metadata={
                "model_size": self._model_size,
                "device": self._device,
                "stub": True,
            },
        )

    async def health_check(self) -> bool:
        # Real implementation would verify whisper model is loaded
        return True


# ------------------------------------------------------------------
# Cloud provider stubs
# ------------------------------------------------------------------


class OpenAIWhisperSTTProvider(BaseSTTProvider):
    """Cloud OpenAI Whisper API provider stub.

    Wraps the ``POST /v1/audio/transcriptions`` endpoint. The actual HTTP
    call is deferred; this stub demonstrates the provider shape.
    """

    def __init__(self, *, api_key: str = "", model: str = "whisper-1") -> None:
        self._api_key = api_key
        self._model = model

    @property
    def provider_name(self) -> str:
        return "openai_whisper"

    async def transcribe(
        self,
        audio_data: bytes,
        *,
        audio_format: AudioFormat | None = None,
        language: str = "",
    ) -> STTResult:
        if not audio_data:
            raise ValueError("audio_data must not be empty")
        if not self._api_key:
            raise RuntimeError("OpenAI API key is not configured")
        # Stub: real implementation would POST to OpenAI /v1/audio/transcriptions
        logger.debug(
            "openai_whisper.transcribe_stub audio_bytes=%d model=%s",
            len(audio_data),
            self._model,
        )
        return STTResult(
            text="[openai whisper transcription placeholder]",
            confidence=0.9,
            language=language or "en",
            duration_ms=0.0,
            provider=self.provider_name,
            metadata={"model": self._model, "stub": True},
        )

    async def health_check(self) -> bool:
        return bool(self._api_key)


class ElevenLabsTTSProviderAdapter(BaseTTSProvider):
    """Adapter wrapping the existing ElevenLabsTransport as a TTSProvider.

    This bridges the pre-existing ``ElevenLabsTransport`` class (which
    predates the provider abstraction) into the Phase 35 protocol so
    existing ElevenLabs configuration continues to work.
    """

    def __init__(self, transport: Any) -> None:
        self._transport = transport

    @property
    def provider_name(self) -> str:
        return "elevenlabs"

    async def synthesize(
        self,
        text: str,
        *,
        voice_id: str = "",
        audio_format: AudioFormat | None = None,
    ) -> TTSResult:
        if not text:
            raise ValueError("text must not be empty")
        audio_data: bytes = await self._transport.synthesize(text, voice_id=voice_id or None)
        fmt = audio_format or AudioFormat(encoding=AudioEncoding.MP3, sample_rate=44100)
        return TTSResult(
            audio_data=audio_data,
            audio_format=fmt,
            provider=self.provider_name,
            metadata={"voice_id": voice_id, "size_bytes": len(audio_data)},
        )

    async def list_voices(self) -> list[dict[str, Any]]:
        voices: list[dict[str, Any]] = await self._transport.list_voices()
        return voices

    async def health_check(self) -> bool:
        result: bool = await self._transport.health_check()
        return result
