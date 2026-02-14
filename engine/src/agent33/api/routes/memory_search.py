"""Memory search and observation API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent33.security.permissions import require_scope

router = APIRouter(prefix="/v1/memory", tags=["memory"])


class MemorySearchRequest(BaseModel):
    query: str
    level: str = "index"  # index | timeline | full
    top_k: int = 10


class MemorySearchResponse(BaseModel):
    results: list[dict[str, Any]]


class SummarizeResponse(BaseModel):
    summary: str
    key_facts: list[str]
    tags: list[str]


@router.post(
    "/search",
    response_model=MemorySearchResponse,
    dependencies=[require_scope("agents:read")],
)
async def search_memory(req: MemorySearchRequest) -> MemorySearchResponse:
    """Search memory with progressive recall at specified detail level."""
    # Progressive recall is wired via app.state in main.py
    from agent33.main import app

    recall = getattr(app.state, "progressive_recall", None)
    if recall is None:
        raise HTTPException(503, "Memory system not initialized")

    results = await recall.search(req.query, level=req.level, top_k=req.top_k)
    return MemorySearchResponse(
        results=[
            {
                "level": r.level,
                "content": r.content,
                "citations": r.citations,
                "token_estimate": r.token_estimate,
            }
            for r in results
        ]
    )


@router.get("/sessions/{session_id}/observations", dependencies=[require_scope("agents:read")])
async def list_observations(session_id: str) -> dict[str, Any]:
    """List observations for a session."""
    from agent33.main import app

    capture = getattr(app.state, "observation_capture", None)
    if capture is None:
        raise HTTPException(503, "Observation capture not initialized")

    # Return buffered observations matching session_id
    observations = [
        {
            "id": o.id,
            "session_id": o.session_id,
            "agent_name": o.agent_name,
            "event_type": o.event_type,
            "content": o.content[:500],
            "tags": o.tags,
            "timestamp": o.timestamp.isoformat(),
        }
        for o in capture._buffer
        if o.session_id == session_id
    ]
    return {"session_id": session_id, "observations": observations}


@router.post(
    "/sessions/{session_id}/summarize",
    response_model=SummarizeResponse,
    dependencies=[require_scope("agents:write")],
)
async def summarize_session(session_id: str) -> SummarizeResponse:
    """Trigger summarization for a session's observations."""
    from agent33.main import app

    capture = getattr(app.state, "observation_capture", None)
    summarizer = getattr(app.state, "session_summarizer", None)
    if capture is None or summarizer is None:
        raise HTTPException(503, "Memory system not initialized")

    observations = [o for o in capture._buffer if o.session_id == session_id]
    if not observations:
        raise HTTPException(404, f"No observations for session {session_id}")

    result = await summarizer.auto_summarize(session_id, observations)
    return SummarizeResponse(
        summary=result.get("summary", ""),
        key_facts=result.get("key_facts", []),
        tags=result.get("tags", []),
    )
