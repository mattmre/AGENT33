"""Activity feed API endpoints for the Observatory."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent33.db.models import ActivityLog, ActivityType, Fact, Source
from agent33.db.session import get_session

logger = structlog.get_logger()
router = APIRouter(prefix="/api", tags=["activity"])


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class ActivityItem(BaseModel):
    """A single activity item in the feed."""

    id: str
    activity_type: str
    title: str
    description: str | None
    metadata: dict[str, Any]
    source_name: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityFeedResponse(BaseModel):
    """Paginated activity feed response."""

    items: list[ActivityItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class StatsResponse(BaseModel):
    """Observatory statistics."""

    facts_count: int
    sources_count: int
    activities_today: int
    last_activity_at: datetime | None


class AskRequest(BaseModel):
    """Request body for asking the agent."""

    question: str


class AskResponse(BaseModel):
    """Response from asking the agent."""

    answer: str
    sources: list[dict[str, Any]]
    confidence: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/activity", response_model=ActivityFeedResponse)
async def get_activity_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    activity_type: ActivityType | None = None,
    session: AsyncSession = Depends(get_session),
) -> ActivityFeedResponse:
    """Get paginated activity feed.

    Returns the most recent activities, optionally filtered by type.
    """
    # Build query
    stmt = (
        select(ActivityLog)
        .where(ActivityLog.is_public == True)  # noqa: E712
        .order_by(ActivityLog.created_at.desc())
    )

    if activity_type:
        stmt = stmt.where(ActivityLog.activity_type == activity_type)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await session.execute(stmt)
    activities = result.scalars().all()

    # Load source names
    items = []
    for activity in activities:
        source_name = None
        if activity.source_id:
            source = await session.get(Source, activity.source_id)
            source_name = source.name if source else None

        items.append(
            ActivityItem(
                id=activity.id,
                activity_type=activity.activity_type.value,
                title=activity.title,
                description=activity.description,
                metadata=activity.metadata_ or {},
                source_name=source_name,
                created_at=activity.created_at,
            )
        )

    return ActivityFeedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=offset + len(items) < total,
    )


@router.get("/activity/stream")
async def stream_activity(
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Server-Sent Events stream for real-time activity updates.

    Clients should connect and receive events as they happen.
    Format: `data: {json}\n\n`
    """

    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events for new activities."""
        last_id: str | None = None

        # Send initial heartbeat
        yield f"event: connected\ndata: {{}}\n\n"

        while True:
            try:
                # Check for new activities
                stmt = (
                    select(ActivityLog)
                    .where(ActivityLog.is_public == True)  # noqa: E712
                    .order_by(ActivityLog.created_at.desc())
                    .limit(1)
                )
                result = await session.execute(stmt)
                latest = result.scalar_one_or_none()

                if latest and latest.id != last_id:
                    last_id = latest.id

                    # Load source name
                    source_name = None
                    if latest.source_id:
                        source = await session.get(Source, latest.source_id)
                        source_name = source.name if source else None

                    event_data = {
                        "id": latest.id,
                        "activity_type": latest.activity_type.value,
                        "title": latest.title,
                        "description": latest.description,
                        "metadata": latest.metadata_ or {},
                        "source_name": source_name,
                        "created_at": latest.created_at.isoformat(),
                    }

                    import json
                    yield f"event: activity\ndata: {json.dumps(event_data)}\n\n"

                # Send heartbeat every 30 seconds
                yield f"event: heartbeat\ndata: {{}}\n\n"

                # Poll interval
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("sse_error", error=str(e))
                yield f"event: error\ndata: {{\"error\": \"{str(e)}\"}}\n\n"
                await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    session: AsyncSession = Depends(get_session),
) -> StatsResponse:
    """Get Observatory statistics."""
    # Count facts
    facts_result = await session.execute(select(func.count(Fact.id)))
    facts_count = facts_result.scalar() or 0

    # Count active sources
    sources_result = await session.execute(
        select(func.count(Source.id)).where(Source.is_active == True)  # noqa: E712
    )
    sources_count = sources_result.scalar() or 0

    # Count activities today
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    activities_result = await session.execute(
        select(func.count(ActivityLog.id)).where(
            ActivityLog.created_at >= today_start,
            ActivityLog.is_public == True,  # noqa: E712
        )
    )
    activities_today = activities_result.scalar() or 0

    # Get last activity timestamp
    last_activity_result = await session.execute(
        select(ActivityLog.created_at)
        .where(ActivityLog.is_public == True)  # noqa: E712
        .order_by(ActivityLog.created_at.desc())
        .limit(1)
    )
    last_activity_at = last_activity_result.scalar()

    return StatsResponse(
        facts_count=facts_count,
        sources_count=sources_count,
        activities_today=activities_today,
        last_activity_at=last_activity_at,
    )


@router.post("/ask", response_model=AskResponse)
async def ask_agent(
    request: AskRequest,
    session: AsyncSession = Depends(get_session),
) -> AskResponse:
    """Ask the agent a question using RAG over stored facts.

    The agent will search through learned facts and provide an answer
    with source citations.
    """
    from agent33.memory.long_term import LongTermMemory
    from agent33.memory.embeddings import get_embedding
    from agent33.llm.router import ModelRouter
    from agent33.config import settings

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Log the query activity
    activity = ActivityLog(
        tenant_id="default",  # TODO: get from auth context
        activity_type=ActivityType.QUERIED,
        title=f"Question: {question[:100]}",
        description=question,
        metadata_={"question_length": len(question)},
        is_public=True,
    )
    session.add(activity)

    try:
        # Get embedding for the question
        question_embedding = await get_embedding(question)

        # Search for relevant facts
        memory = LongTermMemory(settings.database_url)
        await memory.initialize()

        results = await memory.search(question_embedding, top_k=5)
        await memory.close()

        # Build context from search results
        context_parts = []
        sources = []
        for i, result in enumerate(results):
            context_parts.append(f"[{i+1}] {result.text}")
            sources.append({
                "index": i + 1,
                "text": result.text[:200],
                "score": result.score,
                "metadata": result.metadata,
            })

        context = "\n\n".join(context_parts) if context_parts else "No relevant information found."

        # Generate answer using LLM
        router = ModelRouter()
        prompt = f"""Based on the following information, answer the user's question.
If the information doesn't contain the answer, say so clearly.
Cite your sources using [1], [2], etc.

Information:
{context}

Question: {question}

Answer:"""

        response = await router.complete(
            messages=[{"role": "user", "content": prompt}],
            model="default",
        )

        answer = response.get("content", "I couldn't generate an answer.")

        # Log the response
        response_activity = ActivityLog(
            tenant_id="default",
            activity_type=ActivityType.RESPONDED,
            title=f"Answered: {question[:50]}...",
            description=answer[:500],
            metadata_={
                "sources_used": len(sources),
                "confidence": results[0].score if results else 0,
            },
            is_public=True,
        )
        session.add(response_activity)

        return AskResponse(
            answer=answer,
            sources=sources,
            confidence=results[0].score if results else 0.0,
        )

    except Exception as e:
        logger.error("ask_failed", error=str(e), question=question[:100])
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")


@router.get("/knowledge")
async def get_knowledge_graph(
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get knowledge graph data for visualization.

    Returns nodes (facts, sources) and edges (relationships).
    """
    # Get recent facts
    facts_stmt = (
        select(Fact)
        .order_by(Fact.created_at.desc())
        .limit(limit)
    )
    facts_result = await session.execute(facts_stmt)
    facts = facts_result.scalars().all()

    # Get sources
    sources_stmt = select(Source).where(Source.is_active == True)  # noqa: E712
    sources_result = await session.execute(sources_stmt)
    sources = sources_result.scalars().all()

    # Build nodes
    nodes = []
    edges = []

    # Add source nodes
    for source in sources:
        nodes.append({
            "id": f"source_{source.id}",
            "type": "source",
            "label": source.name,
            "data": {
                "source_type": source.source_type.value,
                "items_fetched": source.items_fetched,
            },
        })

    # Add fact nodes and edges to sources
    for fact in facts:
        nodes.append({
            "id": f"fact_{fact.id}",
            "type": "fact",
            "label": (fact.metadata_.get("title", fact.content[:50]) if fact.metadata_ else fact.content[:50]),
            "data": {
                "content": fact.content[:200],
                "confidence": fact.confidence,
                "created_at": fact.created_at.isoformat(),
            },
        })

        # Edge from source to fact
        if fact.source_id:
            edges.append({
                "source": f"source_{fact.source_id}",
                "target": f"fact_{fact.id}",
                "type": "produced",
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_facts": len(facts),
            "total_sources": len(sources),
        },
    }
