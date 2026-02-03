"""Observatory frontend and API routes."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel

router = APIRouter(tags=["observatory"])

# Path to observatory static files
_OBSERVATORY_PATH = Path(__file__).resolve().parents[4] / "observatory"


# --- Pydantic Models ---


class ActivityItem(BaseModel):
    """Single activity feed item."""

    id: str
    type: str  # query, ingest, workflow, error, chat, agent
    message: str
    timestamp: datetime
    agent: str | None = None
    metadata: dict[str, Any] | None = None


class ActivityResponse(BaseModel):
    """Paginated activity response."""

    items: list[ActivityItem]
    total: int
    page: int
    limit: int


class StatsResponse(BaseModel):
    """System statistics response."""

    facts_count: int
    sources_count: int
    queries_today: int
    uptime: str


class AskRequest(BaseModel):
    """Ask agent request."""

    question: str


class AskResponse(BaseModel):
    """Ask agent response."""

    answer: str
    sources: list[dict[str, str]]


# --- In-memory activity store (replace with database in production) ---

_activity_store: list[ActivityItem] = []
_activity_subscribers: list[asyncio.Queue] = []
_start_time = datetime.now(UTC)


def record_activity(
    activity_type: str,
    message: str,
    agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ActivityItem:
    """Record a new activity and notify subscribers."""
    activity = ActivityItem(
        id=f"act_{len(_activity_store) + 1}_{int(datetime.now(UTC).timestamp())}",
        type=activity_type,
        message=message,
        timestamp=datetime.now(UTC),
        agent=agent,
        metadata=metadata,
    )
    _activity_store.insert(0, activity)

    # Keep store bounded
    if len(_activity_store) > 1000:
        _activity_store.pop()

    # Notify all subscribers
    for queue in _activity_subscribers:
        try:
            queue.put_nowait(activity)
        except asyncio.QueueFull:
            pass

    return activity


# --- Static file routes ---


@router.get("/observatory", response_class=HTMLResponse, response_model=None)
async def observatory_index():
    """Serve the Observatory main page."""
    index_path = _OBSERVATORY_PATH / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    return HTMLResponse(
        content="<html><body><h1>Observatory not found</h1></body></html>",
        status_code=404,
    )


@router.get("/observatory/styles.css")
async def observatory_styles() -> FileResponse:
    """Serve Observatory CSS."""
    css_path = _OBSERVATORY_PATH / "styles.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return FileResponse(css_path)


@router.get("/observatory/app.js")
async def observatory_app_js() -> FileResponse:
    """Serve Observatory main JavaScript."""
    js_path = _OBSERVATORY_PATH / "app.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    return FileResponse(js_path)


@router.get("/observatory/api.js")
async def observatory_api_js() -> FileResponse:
    """Serve Observatory API client JavaScript."""
    js_path = _OBSERVATORY_PATH / "api.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    return FileResponse(js_path)


# --- API routes ---


@router.get("/api/activity", response_model=ActivityResponse)
async def get_activity(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> ActivityResponse:
    """Get paginated activity feed."""
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    items = _activity_store[start_idx:end_idx]

    return ActivityResponse(
        items=items,
        total=len(_activity_store),
        page=page,
        limit=limit,
    )


@router.get("/api/activity/stream")
async def activity_stream(request: Request) -> StreamingResponse:
    """Server-Sent Events stream for real-time activity updates."""

    async def event_generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[ActivityItem] = asyncio.Queue(maxsize=50)
        _activity_subscribers.append(queue)

        try:
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for activity with timeout for heartbeat
                    activity = await asyncio.wait_for(queue.get(), timeout=30.0)
                    data = activity.model_dump_json()
                    yield f"event: activity\ndata: {data}\n\n"
                except TimeoutError:
                    # Send heartbeat
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.now(UTC).isoformat()})}\n\n"

        finally:
            _activity_subscribers.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/stats", response_model=StatsResponse)
async def get_stats(request: Request) -> StatsResponse:
    """Get system statistics."""
    # Calculate uptime
    uptime_delta = datetime.now(UTC) - _start_time
    days = uptime_delta.days
    hours = uptime_delta.seconds // 3600
    minutes = (uptime_delta.seconds % 3600) // 60

    if days > 0:
        uptime_str = f"{days}d {hours}h"
    elif hours > 0:
        uptime_str = f"{hours}h {minutes}m"
    else:
        uptime_str = f"{minutes}m"

    # Get stats from app state if available
    app = request.app
    facts_count = 0
    sources_count = 0

    # Try to get real stats from memory/training stores
    if hasattr(app.state, "training_store"):
        try:
            # Placeholder for actual stats query
            pass
        except Exception:
            pass

    # Count today's queries from activity
    today = datetime.now(UTC).date()
    queries_today = sum(
        1
        for a in _activity_store
        if a.type == "query" and a.timestamp.date() == today
    )

    return StatsResponse(
        facts_count=facts_count,
        sources_count=sources_count,
        queries_today=queries_today,
        uptime=uptime_str,
    )


@router.post("/api/ask", response_model=AskResponse)
async def ask_agent(request: Request, body: AskRequest) -> AskResponse:
    """Ask a question to the agent."""
    # Record the query activity
    record_activity(
        activity_type="query",
        message=f'User asked: "{body.question[:100]}..."' if len(body.question) > 100 else f'User asked: "{body.question}"',
    )

    # Try to use the actual chat endpoint if available
    app = request.app

    try:
        # Import and use the RAG pipeline if available
        from agent33.memory.rag import RAGPipeline

        # Check if we have the necessary components
        if hasattr(app.state, "rag_pipeline"):
            rag: RAGPipeline = app.state.rag_pipeline
            result = await rag.query(body.question)
            return AskResponse(
                answer=result.get("answer", "No answer found."),
                sources=[
                    {"title": s.get("title", "Unknown"), "url": s.get("url", "#")}
                    for s in result.get("sources", [])
                ],
            )
    except ImportError:
        pass
    except Exception:
        # Log but don't fail
        pass

    # Fallback response
    return AskResponse(
        answer="The knowledge base is not yet configured. Please ensure the RAG pipeline is initialized with indexed documents.",
        sources=[],
    )


@router.get("/api/knowledge/graph")
async def get_knowledge_graph() -> dict[str, Any]:
    """Get knowledge graph data for visualization."""
    # Placeholder for future implementation
    return {
        "nodes": [],
        "edges": [],
        "metadata": {
            "message": "Knowledge graph visualization not yet implemented",
        },
    }
