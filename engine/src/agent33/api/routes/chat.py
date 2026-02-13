"""Chat completions proxy to Ollama."""

from __future__ import annotations

from typing import Any

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


@router.post("/chat/completions")
async def chat_completions(request: ChatRequest) -> dict[str, Any]:
    """Proxy chat completions to Ollama."""
    model = request.model or settings.ollama_default_model
    payload = {
        "model": model,
        "messages": [m.model_dump() for m in request.messages],
        "stream": False,
        "options": {"temperature": request.temperature},
    }
    if request.max_tokens:
        payload["options"]["num_predict"] = request.max_tokens  # type: ignore[index]

    # Scan for prompt injection
    for msg in request.messages:
        scan = scan_input(msg.content)
        if not scan.is_safe:
            raise HTTPException(
                status_code=400,
                detail=f"Input rejected: {', '.join(scan.threats)}",
            )

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/chat", json=payload
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e)) from e
    except httpx.ConnectError as e:
        raise HTTPException(status_code=503, detail="Ollama unavailable") from e

    # Return OpenAI-compatible format
    return {
        "id": f"chatcmpl-{id(data)}",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": data.get("message", {}),
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0)
            + data.get("eval_count", 0),
        },
    }
