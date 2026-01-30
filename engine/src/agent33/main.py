"""FastAPI application entry point with full integration wiring."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent33.api.routes import agents, auth, chat, dashboard, health, webhooks, workflows
from agent33.config import settings
from agent33.memory.long_term import LongTermMemory
from agent33.messaging.bus import NATSMessageBus
from agent33.security.middleware import AuthMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown.

    Startup initialises:
    - PostgreSQL connection pool (via LongTermMemory / SQLAlchemy async engine)
    - Redis async connection
    - NATS message bus
    - Agent runtime wiring into the workflow executor

    All resources are stored on ``app.state`` for access by route handlers.
    """
    logger.info("agent33_starting")

    # -- Database (PostgreSQL + pgvector) ----------------------------------
    long_term_memory = LongTermMemory(settings.database_url)
    try:
        await long_term_memory.initialize()
        logger.info("database_connected", url=_redact_url(settings.database_url))
    except Exception as exc:
        logger.warning("database_init_failed", error=str(exc))
    app.state.long_term_memory = long_term_memory

    # -- Redis -------------------------------------------------------------
    redis_conn = None
    try:
        import redis.asyncio as aioredis

        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await _redis_client.ping()
        redis_conn = _redis_client
        logger.info("redis_connected", url=settings.redis_url)
    except Exception as exc:
        logger.warning("redis_init_failed", error=str(exc))
    app.state.redis = redis_conn

    # -- NATS message bus --------------------------------------------------
    nats_bus = NATSMessageBus(settings.nats_url)
    try:
        await nats_bus.connect()
        logger.info("nats_connected", url=settings.nats_url)
    except Exception as exc:
        logger.warning("nats_init_failed", error=str(exc))
    app.state.nats_bus = nats_bus

    # -- Agent runtime / workflow integration ------------------------------
    from agent33.llm.router import ModelRouter
    from agent33.workflows.actions.invoke_agent import register_agent

    model_router = ModelRouter()
    app.state.model_router = model_router

    _register_agent_runtime_bridge(model_router, register_agent)
    logger.info("agent_workflow_bridge_registered")

    yield

    # -- Shutdown ----------------------------------------------------------
    logger.info("agent33_stopping")

    if nats_bus.is_connected:
        await nats_bus.close()
        logger.info("nats_closed")

    if redis_conn is not None:
        await redis_conn.aclose()
        logger.info("redis_closed")

    await long_term_memory.close()
    logger.info("database_closed")


def _redact_url(url: str) -> str:
    """Return the host portion of a database URL to avoid logging credentials."""
    if "@" in url:
        return url.split("@", 1)[-1]
    return url


def _register_agent_runtime_bridge(
    model_router: object,
    register_fn: object,
) -> None:
    """Create a bridge so workflow invoke-agent steps can run AgentRuntime.

    The bridge intercepts calls from the workflow executor's invoke-agent
    action.  It builds a lightweight AgentDefinition on the fly and delegates
    to AgentRuntime.invoke so that real LLM calls happen.
    """
    from agent33.agents.definition import (
        AgentConstraints,
        AgentDefinition,
        AgentParameter,
        AgentRole,
    )
    from agent33.agents.runtime import AgentRuntime

    async def _bridge(inputs: dict) -> dict:
        agent_name = inputs.pop("agent_name", "workflow-agent")
        model = inputs.pop("model", settings.ollama_default_model)

        definition = AgentDefinition(
            name=agent_name,
            version="0.1.0",
            role=AgentRole.WORKER,
            description=f"Dynamically invoked agent '{agent_name}'",
            inputs={
                k: AgentParameter(type="string", description=k)
                for k in inputs
            },
            outputs={
                "result": AgentParameter(type="string", description="result"),
            },
            constraints=AgentConstraints(),
        )
        runtime = AgentRuntime(definition=definition, router=model_router, model=model)
        result = await runtime.invoke(inputs)
        return result.output

    register_fn("__default__", _bridge)


# -- Application factory ------------------------------------------------------

app = FastAPI(
    title="AGENT-33",
    description="Autonomous AI agent orchestration engine",
    version="0.1.0",
    lifespan=lifespan,
)

# -- Middleware (order matters: last added = first executed) --------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)

# -- Routers -------------------------------------------------------------------

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(auth.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
