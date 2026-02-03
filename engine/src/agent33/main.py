"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from fastapi import FastAPI

from agent33.api.routes import (
    activity,
    agents,
    auth,
    chat,
    dashboard,
    health,
    memory_search,
    observatory,
    sources,
    training,
    webhooks,
    workflows,
)
from agent33.config import settings

if TYPE_CHECKING:
    from agent33.ingestion.base import IngestResult

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown."""
    logger.info("agent33_starting")

    # --- Database initialization ---
    try:
        from agent33.db.session import init_db
        await init_db()
        logger.info("database_initialized")
    except Exception:
        logger.warning("database_init_failed", exc_info=True)

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

    # --- Observatory services ---
    try:
        from agent33.db.session import get_session_factory
        from agent33.memory.embeddings import EmbeddingProvider
        from agent33.observatory.knowledge import IngestedContentCreate, KnowledgeService
        from agent33.observatory.stats import StatsService

        session_factory = get_session_factory()

        # Create embedding provider
        embedding_provider = EmbeddingProvider(
            base_url=settings.ollama_base_url,
            model="nomic-embed-text",
        )

        # Optionally create LLM provider for fact extraction
        llm_provider = None
        try:
            from agent33.llm.ollama import OllamaProvider
            llm_provider = OllamaProvider(
                base_url=settings.ollama_base_url,
                default_model="llama3.2",
            )
        except Exception:
            logger.debug("llm_provider_not_available_for_knowledge_service")

        # Initialize KnowledgeService
        knowledge_service = KnowledgeService(
            session_factory=session_factory,
            embedding_provider=embedding_provider,
            llm_provider=llm_provider,
            llm_model="llama3.2",
        )
        app.state.knowledge_service = knowledge_service
        logger.info("knowledge_service_initialized")

        # Initialize StatsService
        stats_service = StatsService(session_factory=session_factory)
        app.state.stats_service = stats_service
        logger.info("stats_service_initialized")

    except Exception:
        logger.warning("observatory_services_init_failed", exc_info=True)

    # --- Ingestion coordinator ---
    ingestion_coordinator = None
    try:
        from uuid import uuid4

        from agent33.db.models import ActivityLog, ActivityType
        from agent33.db.session import get_session_factory
        from agent33.ingestion.coordinator import IngestionCoordinator

        session_factory = get_session_factory()

        # Define callbacks for the coordinator
        async def emit_activity(activity_type: str, message: str, metadata: dict[str, Any]) -> None:
            """Emit an activity log entry."""
            try:
                async with session_factory() as session:
                    activity = ActivityLog(
                        id=str(uuid4()),
                        tenant_id=metadata.get("tenant_id", "default"),
                        activity_type=ActivityType.INGESTED if activity_type == "ingested" else ActivityType.SYSTEM,
                        title=message[:200],
                        description=message,
                        metadata_=metadata,
                        source_id=metadata.get("source_id"),
                        is_public=True,
                    )
                    session.add(activity)
                    await session.commit()
            except Exception as e:
                logger.warning("emit_activity_failed", error=str(e))

        async def store_content(source_id: UUID, result: IngestResult) -> bool:
            """Store ingested content via KnowledgeService."""
            try:
                knowledge_svc = getattr(app.state, "knowledge_service", None)
                if knowledge_svc is None:
                    logger.warning("knowledge_service_not_available_for_ingestion")
                    return False

                # Look up tenant_id from the source
                from sqlalchemy import select

                from agent33.db.models import Source

                tenant_id = "default"
                async with session_factory() as session:
                    stmt = select(Source.tenant_id).where(Source.id == str(source_id))
                    db_result = await session.execute(stmt)
                    row = db_result.scalar_one_or_none()
                    if row:
                        tenant_id = row

                content = IngestedContentCreate(
                    tenant_id=tenant_id,
                    source_id=str(source_id),
                    title=result.title,
                    content=result.content,
                    source_url=result.source_url,
                    published_at=result.published_at,
                    metadata=result.metadata or {},
                )
                await knowledge_svc.store_content(content)
                return True
            except Exception as e:
                logger.warning("store_content_failed", source_id=str(source_id), error=str(e))
                return False

        async def update_source_cursor(source_id: UUID, timestamp: datetime) -> None:
            """Update source's last fetched timestamp."""
            try:
                knowledge_svc = getattr(app.state, "knowledge_service", None)
                if knowledge_svc is not None:
                    await knowledge_svc.update_source_cursor(source_id, timestamp.isoformat())
            except Exception as e:
                logger.warning("update_source_cursor_failed", source_id=str(source_id), error=str(e))

        ingestion_coordinator = IngestionCoordinator(
            emit_activity=emit_activity,
            store_content=store_content,
            update_source_cursor=update_source_cursor,
        )
        app.state.ingestion_coordinator = ingestion_coordinator
        logger.info("ingestion_coordinator_initialized")

    except Exception:
        logger.warning("ingestion_coordinator_init_failed", exc_info=True)

    yield

    # --- Shutdown ingestion coordinator ---
    ingestion_coord = getattr(app.state, "ingestion_coordinator", None)
    if ingestion_coord is not None:
        try:
            await ingestion_coord.stop_all()
            logger.info("ingestion_coordinator_stopped")
        except Exception:
            logger.warning("ingestion_coordinator_stop_failed", exc_info=True)

    # --- Shutdown ---
    training_store = getattr(app.state, "training_store", None)
    if training_store is not None:
        await training_store.close()

    scheduler = getattr(app.state, "training_scheduler", None)
    if scheduler is not None:
        await scheduler.stop()

    logger.info("agent33_stopping")


app = FastAPI(
    title="AGENT-33",
    description="Autonomous AI agent orchestration engine",
    version="0.1.0",
    lifespan=lifespan,
)

# --- Add TenantMiddleware for multi-tenant support ---
try:
    from agent33.tenancy.middleware import TenantMiddleware
    app.add_middleware(TenantMiddleware)
    logger.info("tenant_middleware_added")
except Exception:
    logger.warning("tenant_middleware_add_failed", exc_info=True)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(auth.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(memory_search.router)
app.include_router(observatory.router)
app.include_router(training.router)
app.include_router(activity.router)
app.include_router(sources.router)
