"""FastAPI app factory for the standalone voice sidecar."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel, Field

from agent33.voice.elevenlabs import (
    ElevenLabsArtifactStore,
    ElevenLabsConfig,
    ElevenLabsTransport,
    ElevenLabsTransportError,
)
from agent33.voice.livekit_transport import (
    LiveKitConfig,
    LiveKitTransport,
    LiveKitTransportError,
)
from agent33.voice.service import VoiceSidecarService

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)


class StartVoiceSidecarSessionRequest(BaseModel):
    """Request body for starting a sidecar session."""

    room_name: str
    requested_by: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    persona_id: str = "default"


class SynthesizeRequest(BaseModel):
    """Request body for ElevenLabs text-to-speech synthesis."""

    text: str
    voice_id: str = ""
    session_id: str = ""


class CreateLiveKitRoomRequest(BaseModel):
    """Request body for creating a LiveKit room."""

    name: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenerateLiveKitTokenRequest(BaseModel):
    """Request body for generating a LiveKit access token."""

    room_name: str
    identity: str
    ttl: int | None = None


def create_voice_sidecar_app(
    service: VoiceSidecarService | None = None,
    *,
    elevenlabs_config: ElevenLabsConfig | None = None,
    elevenlabs_artifact_store: ElevenLabsArtifactStore | None = None,
    livekit_config: LiveKitConfig | None = None,
) -> FastAPI:
    """Create a standalone FastAPI voice sidecar app."""
    resolved_service = service or VoiceSidecarService(
        voices_path=Path("config/voice/voices.json"),
        artifacts_dir=Path("var/voice-sidecar"),
        playback_backend="noop",
    )

    el_config = elevenlabs_config or ElevenLabsConfig()
    el_transport = ElevenLabsTransport(el_config) if el_config.api_key else None
    el_store = elevenlabs_artifact_store or ElevenLabsArtifactStore(
        storage_dir=resolved_service.artifacts_dir / "elevenlabs",
    )

    lk_config = livekit_config or LiveKitConfig()
    lk_transport = LiveKitTransport(lk_config) if lk_config.is_configured else None

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
        yield
        await resolved_service.shutdown()

    app = FastAPI(title="AGENT-33 Voice Sidecar", version="0.1.0", lifespan=_lifespan)
    app.state.voice_sidecar_service = resolved_service
    app.state.elevenlabs_transport = el_transport
    app.state.elevenlabs_artifact_store = el_store
    app.state.livekit_transport = lk_transport
    app.state.livekit_config = lk_config

    # ------------------------------------------------------------------
    # Core sidecar endpoints
    # ------------------------------------------------------------------

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return resolved_service.health_snapshot().model_dump(mode="json")

    @app.get("/v1/voice/personas")
    async def list_personas() -> list[dict[str, Any]]:
        return [persona.model_dump(mode="json") for persona in resolved_service.list_personas()]

    @app.get("/v1/voice/sessions")
    async def list_sessions() -> list[dict[str, Any]]:
        return [session.model_dump(mode="json") for session in resolved_service.list_sessions()]

    @app.post("/v1/voice/sessions", status_code=201)
    async def start_session(body: StartVoiceSidecarSessionRequest) -> dict[str, Any]:
        session = resolved_service.start_session(
            room_name=body.room_name,
            requested_by=body.requested_by,
            metadata=body.metadata,
            persona_id=body.persona_id,
        )
        return session.model_dump(mode="json")

    @app.get("/v1/voice/sessions/{session_id}")
    async def get_session(session_id: str) -> dict[str, Any]:
        session = resolved_service.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Voice sidecar session not found")
        return session.model_dump(mode="json")

    @app.post("/v1/voice/sessions/{session_id}/stop")
    async def stop_session(session_id: str) -> dict[str, Any]:
        try:
            session = resolved_service.stop_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return session.model_dump(mode="json")

    @app.websocket("/ws/voice/{session_id}")
    async def voice_stream(websocket: WebSocket, session_id: str) -> None:
        try:
            await resolved_service.handle_websocket(session_id, websocket)
        except KeyError:
            await websocket.close(code=1008, reason="voice session not found")

    # ------------------------------------------------------------------
    # ElevenLabs endpoints
    # ------------------------------------------------------------------

    @app.post("/v1/voice/synthesize")
    async def synthesize(body: SynthesizeRequest) -> dict[str, Any]:
        """Synthesize text to audio using ElevenLabs TTS."""
        if el_transport is None:
            raise HTTPException(
                status_code=503,
                detail="ElevenLabs transport is not configured (missing API key)",
            )
        try:
            audio_data = await el_transport.synthesize(
                body.text,
                voice_id=body.voice_id or None,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ElevenLabsTransportError as exc:
            raise HTTPException(
                status_code=exc.status_code or 502,
                detail=exc.detail or str(exc),
            ) from exc

        # Persist artifact if a session_id was provided
        file_path = ""
        if body.session_id:
            file_path = el_store.save_audio(
                session_id=body.session_id,
                text=body.text,
                audio_data=audio_data,
                audio_format=el_config.output_format.split("_")[0],
            )

        return {
            "status": "ok",
            "size_bytes": len(audio_data),
            "format": el_config.output_format,
            "artifact_path": file_path,
        }

    @app.get("/v1/voice/voices")
    async def list_voices() -> dict[str, Any]:
        """List available ElevenLabs voices."""
        if el_transport is None:
            raise HTTPException(
                status_code=503,
                detail="ElevenLabs transport is not configured (missing API key)",
            )
        try:
            voices = await el_transport.list_voices()
        except ElevenLabsTransportError as exc:
            raise HTTPException(
                status_code=exc.status_code or 502,
                detail=exc.detail or str(exc),
            ) from exc
        return {"voices": voices}

    @app.get("/v1/voice/health/elevenlabs")
    async def elevenlabs_health() -> dict[str, Any]:
        """Check ElevenLabs API connectivity."""
        if el_transport is None:
            return {
                "status": "unconfigured",
                "detail": "ElevenLabs API key is not set",
            }
        healthy = await el_transport.health_check()
        return {
            "status": "ok" if healthy else "unavailable",
            "model_id": el_config.model_id,
            "voice_id": el_config.voice_id,
        }

    # ------------------------------------------------------------------
    # LiveKit endpoints (S32)
    # ------------------------------------------------------------------

    @app.post("/v1/voice/livekit/rooms", status_code=201)
    async def create_livekit_room(body: CreateLiveKitRoomRequest) -> dict[str, Any]:
        """Create a LiveKit room in the sidecar."""
        if lk_transport is None:
            raise HTTPException(
                status_code=503,
                detail="LiveKit transport is not configured",
            )
        try:
            room = lk_transport.create_room(body.name, metadata=body.metadata)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except LiveKitTransportError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return room.to_dict()

    @app.get("/v1/voice/livekit/rooms")
    async def list_livekit_rooms() -> list[dict[str, Any]]:
        """List active LiveKit rooms."""
        if lk_transport is None:
            raise HTTPException(
                status_code=503,
                detail="LiveKit transport is not configured",
            )
        return [room.to_dict() for room in lk_transport.list_rooms()]

    @app.delete("/v1/voice/livekit/rooms/{name}")
    async def delete_livekit_room(name: str) -> dict[str, Any]:
        """Delete a LiveKit room."""
        if lk_transport is None:
            raise HTTPException(
                status_code=503,
                detail="LiveKit transport is not configured",
            )
        deleted = lk_transport.delete_room(name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Room '{name}' not found")
        return {"status": "deleted", "room_name": name}

    @app.post("/v1/voice/livekit/token")
    async def generate_livekit_token(body: GenerateLiveKitTokenRequest) -> dict[str, Any]:
        """Generate a LiveKit access token."""
        if lk_transport is None:
            raise HTTPException(
                status_code=503,
                detail="LiveKit transport is not configured",
            )
        try:
            token = lk_transport.generate_token(
                body.room_name,
                body.identity,
                ttl=body.ttl,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except LiveKitTransportError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {"token": token, "room_name": body.room_name, "identity": body.identity}

    @app.get("/v1/voice/livekit/rooms/{name}/participants")
    async def list_livekit_participants(name: str) -> list[dict[str, Any]]:
        """List participants in a LiveKit room."""
        if lk_transport is None:
            raise HTTPException(
                status_code=503,
                detail="LiveKit transport is not configured",
            )
        try:
            participants = lk_transport.get_participants(name)
        except LiveKitTransportError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return [p.to_dict() for p in participants]

    @app.get("/v1/voice/health/livekit")
    async def livekit_health() -> dict[str, Any]:
        """Check LiveKit transport configuration and connectivity."""
        if lk_transport is None:
            return {
                "status": "unconfigured",
                "detail": "LiveKit transport is not configured",
            }
        healthy = lk_transport.health_check()
        snap = lk_transport.snapshot()
        return {
            "status": "ok" if healthy else "unavailable",
            "ws_url": lk_config.ws_url,
            "default_codec": lk_config.default_codec,
            "active_rooms": snap["active_rooms"],
            "total_participants": snap["total_participants"],
        }

    return app
