"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI

from agent33.api.routes import agents, auth, chat, dashboard, health, webhooks, workflows

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown."""
    logger.info("agent33_starting")
    yield
    logger.info("agent33_stopping")


app = FastAPI(
    title="AGENT-33",
    description="Autonomous AI agent orchestration engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(auth.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
