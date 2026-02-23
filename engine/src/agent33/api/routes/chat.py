"""Chat completions proxy to Ollama."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent33.config import settings
from agent33.security.injection import scan_input

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False


from fastapi import Request, Response


@router.post("/chat/completions")
async def chat_completions(request: Request) -> Response:
    """Proxy chat completions to the locally configured orchestration engine."""
    payload = await request.json()
    model = payload.get("model") or settings.local_orchestration_model
    payload["model"] = model

    # Scan for prompt injection
    for msg in payload.get("messages", []):
        content = msg.get("content", "")
        if content:
            scan = scan_input(content)
            if not scan.is_safe:
                raise HTTPException(
                    status_code=400,
                    detail=f"Input rejected: {', '.join(scan.threats)}",
                )

    engine = settings.local_orchestration_engine.lower()
    if engine in ("llama.cpp", "llamacpp"):
        base_url = "http://host.docker.internal:8033/v1"
    else:
        # Ollama's OpenAI compatibility layer
        base_url = f"{settings.ollama_base_url}/v1"

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # We explicitly pass the headers and yield the raw response so that streaming (SSE)
            # and exact OpenAI chunk formats are perfectly preserved back to the frontend.
            req = client.build_request("POST", f"{base_url}/chat/completions", json=payload)
            r = await client.send(req, stream=True)

            # Read the response and return it exactly as the provider formatted it
            await r.aread()
            return Response(
                content=r.content,
                status_code=r.status_code,
                media_type=r.headers.get("content-type", "application/json")
            )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=503, detail=f"{engine} unavailable: {type(e).__name__} - {e}") from e
