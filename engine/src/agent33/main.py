"""FastAPI application entry point with full integration wiring."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from agent33.llm.router import ModelRouter

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from agent33.api.routes import (
    agents,
    auth,
    autonomy,
    chat,
    dashboard,
    evaluations,
    health,
    improvements,
    memory_search,
    releases,
    reviews,
    traces,
    training,
    webhooks,
    workflows,
)
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

    # Warn about insecure defaults
    secret_warnings = settings.check_production_secrets()
    for warning in secret_warnings:
        logger.warning("SECURITY: %s — override via environment variable", warning)

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
        logger.info("redis_connected", url=_redact_url(settings.redis_url))
    except Exception as exc:
        logger.warning("redis_init_failed", error=str(exc))
    app.state.redis = redis_conn

    # -- NATS message bus --------------------------------------------------
    nats_bus = NATSMessageBus(settings.nats_url)
    try:
        await nats_bus.connect()
        logger.info("nats_connected", url=_redact_url(settings.nats_url))
    except Exception as exc:
        logger.warning("nats_init_failed", error=str(exc))
    app.state.nats_bus = nats_bus

    # -- Agent registry ----------------------------------------------------
    from pathlib import Path

    from agent33.agents.registry import AgentRegistry

    agent_registry = AgentRegistry()
    defs_dir = Path(settings.agent_definitions_dir)
    if defs_dir.is_dir():
        count = agent_registry.discover(defs_dir)
        logger.info("agent_registry_loaded", count=count, path=str(defs_dir))
    else:
        logger.warning("agent_definitions_dir_not_found", path=str(defs_dir))
    app.state.agent_registry = agent_registry

    # -- Agent runtime / workflow integration ------------------------------
    from agent33.llm.router import ModelRouter
    from agent33.workflows.actions.invoke_agent import (
        register_agent,
        set_definition_registry,
    )

    set_definition_registry(agent_registry)

    # -- Code execution layer ------------------------------------------
    from agent33.execution.executor import CodeExecutor
    from agent33.workflows.actions import execute_code

    code_executor = CodeExecutor(tool_registry=None)
    app.state.code_executor = code_executor
    execute_code.set_executor(code_executor)
    logger.info("code_executor_initialized")

    model_router = ModelRouter()
    app.state.model_router = model_router

    _register_agent_runtime_bridge(model_router, register_agent, registry=agent_registry)
    logger.info("agent_workflow_bridge_registered")

    # --- AirLLM provider (optional) ---
    if settings.airllm_enabled and settings.airllm_model_path:
        try:
            from agent33.llm.airllm_provider import AirLLMProvider

            airllm = AirLLMProvider(
                model_path=settings.airllm_model_path,
                device=settings.airllm_device,
                compression=settings.airllm_compression,
                max_seq_len=settings.airllm_max_seq_len,
                prefetch=settings.airllm_prefetch,
            )
            app.state.airllm_provider = airllm
            logger.info("airllm_provider_registered", model=settings.airllm_model_path)
        except ImportError:
            logger.warning("airllm_not_available", reason="airllm package not installed")

    # --- Memory subsystem ---
    try:
        from agent33.memory.observation import ObservationCapture
        from agent33.memory.summarizer import SessionSummarizer

        capture = ObservationCapture()
        app.state.observation_capture = capture
        logger.info("observation_capture_initialized")

        # Summarizer needs a router - will be available after agents routes init
        app.state.session_summarizer_class = SessionSummarizer
    except Exception:
        logger.debug("memory_subsystem_init_skipped", exc_info=True)

    # --- Training subsystem (optional) ---
    if settings.training_enabled:
        try:
            from agent33.training.store import TrainingStore

            training_store = TrainingStore(settings.database_url)
            await training_store.initialize()
            app.state.training_store = training_store
            logger.info("training_store_initialized")
        except Exception:
            logger.warning("training_store_init_failed", exc_info=True)

    yield

    # -- Shutdown ----------------------------------------------------------
    logger.info("agent33_stopping")

    training_store = getattr(app.state, "training_store", None)
    if training_store is not None:
        await training_store.close()

    scheduler = getattr(app.state, "training_scheduler", None)
    if scheduler is not None:
        await scheduler.stop()

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
    model_router: ModelRouter,
    register_fn: Callable[..., object],
    registry: Any = None,
) -> None:
    """Create a bridge so workflow invoke-agent steps can run AgentRuntime.

    The bridge intercepts calls from the workflow executor's invoke-agent
    action.  It first looks up the agent in the registry to use the real
    definition (with governance, ownership, safety rules).  Falls back to
    a lightweight throwaway definition only when the name is not registered.
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

        # Try to look up actual registered definition first
        definition = None
        if registry is not None:
            definition = registry.get(agent_name)

        if definition is None:
            # Fall back to throwaway definition for unknown agents
            definition = AgentDefinition(
                name=agent_name,
                version="0.1.0",
                role=AgentRole.WORKER,
                description=f"Dynamically invoked agent '{agent_name}'",
                inputs={
                    k: AgentParameter(type="string", description="Workflow input")
                    for k in inputs
                    if k.isidentifier()
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


# -- Request size limit middleware ----------------------------------------------


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the configured limit."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size_bytes:
            return Response(
                content='{"detail":"Request body too large"}',
                status_code=413,
                media_type="application/json",
            )
        return await call_next(request)


# -- Application factory ------------------------------------------------------

app = FastAPI(
    title="AGENT-33",
    description="Autonomous AI agent orchestration engine",
    version="0.1.0",
    lifespan=lifespan,
)

# -- Middleware (order matters: last added = first executed) --------------------

_cors_origins = (
    settings.cors_allowed_origins.split(",") if settings.cors_allowed_origins else []
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(AuthMiddleware)

# -- Routers -------------------------------------------------------------------

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(auth.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(memory_search.router)
app.include_router(reviews.router)
app.include_router(traces.router)
app.include_router(evaluations.router)
app.include_router(autonomy.router)
app.include_router(releases.router)
app.include_router(improvements.router)
app.include_router(training.router)
