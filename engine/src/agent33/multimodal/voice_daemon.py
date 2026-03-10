"""WebRTC Voice Daemon using LiveKit and OpenAI Realtime API.

This daemon connects to a LiveKit room to facilitate ultra-low-latency,
interruptible voice conversations natively inside the browser, serving as the
agent's ears and mouth for multimodal humanistic interaction.

Phase 35 status: scaffold with full lifecycle interface.  The actual LiveKit
SDK wiring is deferred until the dependency is added to the project.
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

logger = structlog.get_logger()


class LiveVoiceDaemon:
    """Orchestrates bi-directional voice streaming over LiveKit.

    Lifecycle
    ---------
    1. Construct with room/connection parameters.
    2. ``await start()`` — connects to the WebRTC room and begins streaming.
    3. Feed audio with ``await process_audio_chunk(chunk)`` (STT direction).
    4. Generate audio with ``await synthesize_speech(text)`` (TTS direction).
    5. ``await stop()`` — tears down the connection gracefully.

    Use ``health_check()`` at any point to query liveness.
    """

    def __init__(
        self,
        room_name: str,
        url: str,
        api_key: str,
        api_secret: str,
        *,
        transport: str = "stub",
    ) -> None:
        self._room_name = room_name
        self._url = url
        self._api_key = api_key
        self._api_secret = api_secret
        self._transport = transport
        self._active = False
        self._started_at: datetime | None = None
        self._stopped_at: datetime | None = None
        self._processed_chunks = 0
        self._synthesized_utterances = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Connect to the WebRTC room and instantiate the VoicePipelineAgent.

        # TODO: Wire LiveKit SDK when dependency is added
        """
        logger.info(
            "voice_daemon.starting",
            room=self._room_name,
            url=self._url,
            transport=self._transport,
        )
        if self._active:
            logger.debug("voice_daemon.start_skipped", room=self._room_name)
            return
        if self._transport == "livekit":
            raise RuntimeError(
                "LiveKit transport requires the livekit-agents runtime, which is not yet "
                "installed in this repository. Use the default stub transport until the "
                "dependency lands."
            )
        if self._transport != "stub":
            raise ValueError(f"Unsupported voice daemon transport: {self._transport}")
        self._active = True
        self._started_at = datetime.now(UTC)
        self._stopped_at = None
        logger.info("voice_daemon.started", room=self._room_name, transport=self._transport)

    async def stop(self) -> None:
        """Disconnect the daemon from the WebRTC session.

        # TODO: Wire LiveKit SDK when dependency is added
        """
        logger.info("voice_daemon.stopping", room=self._room_name)
        if not self._active:
            logger.debug("voice_daemon.stop_skipped", room=self._room_name)
            return
        self._active = False
        self._stopped_at = datetime.now(UTC)
        logger.info("voice_daemon.stopped", room=self._room_name)

    def health_check(self) -> bool:
        """Return ``True`` when the daemon is connected and streaming.

        # TODO: Wire LiveKit SDK when dependency is added
        """
        healthy = self._active
        logger.debug("voice_daemon.health_check", healthy=healthy, room=self._room_name)
        return healthy

    # ------------------------------------------------------------------
    # Audio processing stubs
    # ------------------------------------------------------------------

    async def process_audio_chunk(self, chunk: bytes) -> str | None:
        """Receive a raw audio chunk and return transcribed text, if any.

        In the full implementation this will feed the chunk into the LiveKit
        VoicePipelineAgent's STT pipeline and return partial/final
        transcriptions as they become available.

        Returns ``None`` while the stub is in place.

        # TODO: Wire LiveKit SDK when dependency is added
        """
        if not self._active:
            raise RuntimeError("Voice daemon is not active")
        self._processed_chunks += 1
        logger.debug(
            "voice_daemon.process_audio_chunk",
            chunk_bytes=len(chunk),
            room=self._room_name,
        )
        return None

    async def synthesize_speech(self, text: str) -> bytes | None:
        """Convert *text* to speech audio bytes.

        In the full implementation this will delegate to the LiveKit
        VoicePipelineAgent's TTS pipeline and return the synthesised audio
        payload.

        Returns ``None`` while the stub is in place.

        # TODO: Wire LiveKit SDK when dependency is added
        """
        if not self._active:
            raise RuntimeError("Voice daemon is not active")
        self._synthesized_utterances += 1
        logger.debug(
            "voice_daemon.synthesize_speech",
            text_length=len(text),
            room=self._room_name,
        )
        return None

    def snapshot(self) -> dict[str, object]:
        """Return deterministic daemon status for API/session management."""
        return {
            "room_name": self._room_name,
            "transport": self._transport,
            "active": self._active,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "stopped_at": self._stopped_at.isoformat() if self._stopped_at else None,
            "processed_chunks": self._processed_chunks,
            "synthesized_utterances": self._synthesized_utterances,
        }
