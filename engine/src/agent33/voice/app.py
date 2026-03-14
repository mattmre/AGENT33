"""FastAPI app factory for the standalone voice sidecar."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel, Field

from agent33.voice.service import VoiceSidecarService


class StartVoiceSidecarSessionRequest(BaseModel):
    """Request body for starting a sidecar session."""

    room_name: str
    requested_by: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    persona_id: str = "default"


def create_voice_sidecar_app(service: VoiceSidecarService | None = None) -> FastAPI:
    """Create a standalone FastAPI voice sidecar app."""
    resolved_service = service or VoiceSidecarService(
        voices_path=Path("config/voice/voices.json"),
        artifacts_dir=Path("var/voice-sidecar"),
        playback_backend="noop",
    )

    @asynccontextmanager
    async def _lifespan(app: FastAPI):  # noqa: ARG001
        yield
        await resolved_service.shutdown()

    app = FastAPI(title="AGENT-33 Voice Sidecar", version="0.1.0", lifespan=_lifespan)
    app.state.voice_sidecar_service = resolved_service

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

    return app
