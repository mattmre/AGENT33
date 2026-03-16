"""FastAPI application entry point with full integration wiring."""

from __future__ import annotations

import json
import time
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
    backups,
    benchmarks,
    chat,
    comparative,
    component_security,
    connectors,
    context,
    cron,
    dashboard,
    evaluations,
    explanations,
    health,
    hooks,
    improvements,
    marketplace,
    mcp,
    mcp_proxy,
    mcp_sync,
    memory_search,
    migrations,
    multimodal,
    operations_hub,
    operator,
    outcomes,
    packs,
    processes,
    provenance,
    reasoning,
    releases,
    research,
    reviews,
    sessions,
    synthetic_envs,
    tool_approvals,
    tool_mutations,
    traces,
    training,
    visualizations,
    webhooks,
    workflow_marketplace,
    workflow_sse,
    workflow_templates,
    workflow_transport,
    workflow_ws,
    workflows,
)
from agent33.api.routes import (
    config as config_routes,
)
from agent33.api.routes import (
    discovery as discovery_routes,
)
from agent33.api.routes import (
    execution as execution_routes,
)
from agent33.api.routes import (
    plugins as plugins_routes,
)
from agent33.api.routes import (
    rate_limits as rate_limits_routes,
)
from agent33.api.routes import (
    skill_matching as skill_matching_routes,
)
from agent33.api.routes import (
    tool_catalog as tool_catalog_routes,
)
from agent33.config import settings
from agent33.hooks.middleware import HookMiddleware
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

    # Record startup time for uptime calculation
    _start_time = time.time()

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

    # -- Shared orchestration state -----------------------------------------
    orchestration_state_store = None
    if settings.orchestration_state_store_path.strip():
        from agent33.services.orchestration_state import OrchestrationStateStore

        orchestration_state_store = OrchestrationStateStore(
            settings.orchestration_state_store_path
        )
        logger.info(
            "orchestration_state_store_enabled",
            path=settings.orchestration_state_store_path,
        )
    app.state.orchestration_state_store = orchestration_state_store

    from agent33.autonomy.service import AutonomyService
    from agent33.backup.service import BackupService
    from agent33.observability.trace_collector import TraceCollector
    from agent33.release.service import ReleaseService

    autonomy_service = AutonomyService(state_store=orchestration_state_store)
    release_service = ReleaseService(state_store=orchestration_state_store)
    trace_collector = TraceCollector(state_store=orchestration_state_store)
    app.state.autonomy_service = autonomy_service
    app.state.release_service = release_service
    app.state.trace_collector = trace_collector
    autonomy.set_autonomy_service(autonomy_service)
    releases.set_release_service(release_service)
    traces.set_trace_collector(trace_collector)

    # -- Redis -------------------------------------------------------------
    redis_conn = None
    try:
        import redis.asyncio as aioredis

        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
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

    # -- Agent profiler (S40) ----------------------------------------------
    from agent33.agents.profiling import AgentProfiler

    agent_profiler = AgentProfiler(max_profiles=settings.agent_profiler_max_profiles)
    app.state.agent_profiler = agent_profiler
    logger.info(
        "agent_profiler_initialized",
        max_profiles=settings.agent_profiler_max_profiles,
    )

    # -- Observability metrics + alerts -------------------------------------
    from agent33.observability.alerts import AlertManager
    from agent33.observability.effort_telemetry import (
        FileEffortTelemetryExporter,
        NoopEffortTelemetryExporter,
    )
    from agent33.observability.metrics import MetricsCollector

    metrics_collector = MetricsCollector()
    app.state.metrics_collector = metrics_collector
    agents.set_metrics(metrics_collector)
    dashboard.set_metrics(metrics_collector)

    effort_telemetry_exporter = (
        FileEffortTelemetryExporter(settings.observability_effort_export_path)
        if settings.observability_effort_export_enabled
        else NoopEffortTelemetryExporter()
    )
    app.state.effort_telemetry_exporter = effort_telemetry_exporter
    agents.set_effort_telemetry_exporter(effort_telemetry_exporter)

    alert_manager = AlertManager(metrics_collector)
    if settings.observability_effort_alerts_enabled:
        alert_manager.add_rule(
            name="high_effort_routing_volume",
            metric="effort_routing_high_effort_total",
            threshold=float(settings.observability_effort_alert_high_effort_count_threshold),
            comparator="gt",
        )
        alert_manager.add_rule(
            name="high_effort_cost_spike",
            metric="effort_routing_estimated_cost_usd",
            threshold=settings.observability_effort_alert_high_cost_usd_threshold,
            comparator="gt",
            statistic="max",
        )
        alert_manager.add_rule(
            name="high_effort_token_budget_spike",
            metric="effort_routing_estimated_token_budget",
            threshold=float(settings.observability_effort_alert_high_token_budget_threshold),
            comparator="gt",
            statistic="max",
        )
    app.state.alert_manager = alert_manager
    dashboard.set_alert_manager(alert_manager)

    # -- Connector metrics collector (Phase 32 UX) -------------------------
    from agent33.connectors.monitoring import ConnectorMetricsCollector

    connector_metrics = ConnectorMetricsCollector()
    app.state.connector_metrics = connector_metrics
    logger.info("connector_metrics_collector_initialized")

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
    if settings.jupyter_kernel_enabled:
        from agent33.execution.adapters.jupyter import (
            JupyterAdapter,
            build_default_jupyter_definition,
        )

        try:
            jupyter_definition = build_default_jupyter_definition(
                adapter_id=settings.jupyter_kernel_adapter_id,
                tool_id=settings.jupyter_kernel_tool_id,
                kernel_name=settings.jupyter_kernel_name,
                max_sessions=settings.jupyter_kernel_max_sessions,
                idle_timeout_seconds=settings.jupyter_kernel_idle_timeout_seconds,
                startup_timeout_seconds=settings.jupyter_kernel_startup_timeout_seconds,
                execution_timeout_seconds=settings.jupyter_kernel_execution_timeout_seconds,
                docker_enabled=settings.jupyter_kernel_mode == "docker",
                docker_image=settings.jupyter_kernel_docker_image,
                docker_allowed_images=[
                    image.strip()
                    for image in settings.jupyter_kernel_allowed_images.split(",")
                    if image.strip()
                ],
                docker_network_enabled=settings.jupyter_kernel_network_enabled,
                docker_mount_working_directory=settings.jupyter_kernel_mount_workdir,
                docker_container_workdir=settings.jupyter_kernel_container_workdir,
            )
            code_executor.register_adapter(JupyterAdapter(jupyter_definition))
            logger.info(
                "jupyter_kernel_adapter_registered",
                adapter_id=settings.jupyter_kernel_adapter_id,
                tool_id=settings.jupyter_kernel_tool_id,
                mode=settings.jupyter_kernel_mode,
            )
        except Exception as exc:
            logger.warning("jupyter_kernel_adapter_failed", error=str(exc))
    app.state.code_executor = code_executor
    execute_code.set_executor(code_executor)
    logger.info("code_executor_initialized")

    # -- GPU Docker manager (S30) ------------------------------------------
    from agent33.execution.gpu import GPUDockerManager

    gpu_docker_manager = GPUDockerManager(
        default_image=settings.execution_default_docker_image,
    )
    app.state.gpu_docker_manager = gpu_docker_manager
    logger.info(
        "gpu_docker_manager_initialized",
        gpu_enabled=settings.execution_gpu_enabled,
        default_image=settings.execution_default_docker_image,
    )

    model_router = ModelRouter()

    # Register LLM providers on the shared model router
    from agent33.llm.ollama import OllamaProvider

    model_router.register(
        "ollama",
        OllamaProvider(
            base_url=settings.ollama_base_url,
            default_model=settings.ollama_default_model,
        ),
    )
    if settings.openai_api_key.get_secret_value():
        from agent33.llm.openai import OpenAIProvider

        _openai_kwargs: dict[str, Any] = {
            "api_key": settings.openai_api_key.get_secret_value(),
        }
        if settings.openai_base_url:
            _openai_kwargs["base_url"] = settings.openai_base_url
        model_router.register("openai", OpenAIProvider(**_openai_kwargs))

    app.state.model_router = model_router
    logger.info("model_router_initialized")

    # -- Tool registry + governance ----------------------------------------
    from agent33.security.approval_tokens import ApprovalTokenManager
    from agent33.tools.approvals import ToolApprovalService
    from agent33.tools.builtin.apply_patch import ApplyPatchTool
    from agent33.tools.governance import ToolGovernance
    from agent33.tools.mutation_audit import MutationAuditStore
    from agent33.tools.registry import ToolRegistry

    tool_registry = ToolRegistry()
    tool_registry.discover_from_entrypoints()
    app.state.tool_registry = tool_registry

    tool_approval_service = ToolApprovalService(state_store=orchestration_state_store)
    app.state.tool_approval_service = tool_approval_service
    tool_approvals.set_tool_approval_service(tool_approval_service)

    approval_token_manager = None
    if settings.approval_token_enabled:
        approval_token_manager = ApprovalTokenManager(
            secret=settings.jwt_secret.get_secret_value(),
            algorithm=settings.jwt_algorithm,
            default_ttl_seconds=settings.approval_token_ttl_seconds,
            default_one_time=settings.approval_token_one_time_default,
            state_store=orchestration_state_store,
        )
    app.state.approval_token_manager = approval_token_manager

    tool_governance = ToolGovernance(
        approval_service=tool_approval_service,
        approval_token_manager=approval_token_manager,
    )
    app.state.tool_governance = tool_governance
    mutation_audit_store = MutationAuditStore(state_store=orchestration_state_store)
    app.state.mutation_audit_store = mutation_audit_store
    tool_mutations.set_mutation_audit_store(mutation_audit_store)
    tool_registry.register(ApplyPatchTool(audit_store=mutation_audit_store))
    logger.info("tool_registry_initialized", tool_count=len(tool_registry.list_all()))

    from agent33.processes.service import ProcessManagerService

    process_manager_service = ProcessManagerService(
        workspace_root=Path.cwd(),
        log_dir=Path(settings.process_manager_log_dir),
        state_store=orchestration_state_store,
        max_processes=settings.process_manager_max_processes,
    )
    app.state.process_manager_service = process_manager_service
    logger.info(
        "process_manager_service_initialized",
        workspace_root=str(Path.cwd().resolve()),
        log_dir=str(Path(settings.process_manager_log_dir).resolve()),
        max_processes=settings.process_manager_max_processes,
    )

    backup_service = BackupService(
        backup_dir=Path(settings.backup_dir),
        settings=settings,
        app_root=Path.cwd(),
        workspace_dir=None,
    )
    app.state.backup_service = backup_service
    logger.info(
        "backup_service_initialized",
        backup_dir=str(Path(settings.backup_dir).resolve()),
    )

    # -- Embedding provider + cache ----------------------------------------
    from agent33.memory.embeddings import EmbeddingProvider

    embedding_provider = EmbeddingProvider(
        base_url=settings.ollama_base_url,
        max_connections=settings.http_max_connections,
        max_keepalive_connections=settings.http_max_keepalive,
    )
    app.state.embedding_provider = embedding_provider

    active_embedder: Any = embedding_provider
    if settings.embedding_cache_enabled:
        from agent33.memory.cache import EmbeddingCache

        embedding_cache = EmbeddingCache(
            provider=embedding_provider,
            max_size=settings.embedding_cache_max_size,
        )
        active_embedder = embedding_cache
        app.state.embedding_cache = embedding_cache

    logger.info("embedding_provider_initialized", cache=settings.embedding_cache_enabled)

    # -- BM25 + Hybrid + RAG ----------------------------------------------
    from agent33.memory.bm25 import BM25Index
    from agent33.memory.rag import RAGPipeline

    bm25_index = BM25Index()
    app.state.bm25_index = bm25_index

    # -- BM25 warm-up from existing records --
    if settings.bm25_warmup_enabled:
        from agent33.memory.warmup import warm_up_bm25

        try:
            warmup_count = await warm_up_bm25(
                long_term_memory=long_term_memory,
                bm25_index=bm25_index,
                page_size=settings.bm25_warmup_page_size,
                max_records=settings.bm25_warmup_max_records,
            )
            logger.info("bm25_warmup_done", records_loaded=warmup_count)
        except Exception as exc:
            logger.warning("bm25_warmup_failed", error=str(exc), exc_info=True)

    hybrid_searcher = None
    if settings.rag_hybrid_enabled:
        from agent33.memory.hybrid import HybridSearcher

        hybrid_searcher = HybridSearcher(
            long_term_memory=long_term_memory,
            embedding_provider=active_embedder,
            bm25_index=bm25_index,
            vector_weight=settings.rag_vector_weight,
            rrf_k=settings.rag_rrf_k,
        )
        app.state.hybrid_searcher = hybrid_searcher

    rag_pipeline = RAGPipeline(
        embedding_provider=active_embedder,
        long_term_memory=long_term_memory,
        top_k=settings.rag_top_k,
        similarity_threshold=settings.rag_similarity_threshold,
        hybrid_searcher=hybrid_searcher,
    )
    app.state.rag_pipeline = rag_pipeline
    logger.info(
        "rag_pipeline_initialized",
        hybrid=settings.rag_hybrid_enabled,
        top_k=settings.rag_top_k,
    )

    # -- Progressive recall ------------------------------------------------
    from agent33.memory.progressive_recall import ProgressiveRecall

    progressive_recall = ProgressiveRecall(
        long_term_memory=long_term_memory,
        embedding_provider=active_embedder,
    )
    app.state.progressive_recall = progressive_recall

    # -- Skill registry + injector -----------------------------------------
    from agent33.skills.injection import SkillInjector
    from agent33.skills.registry import SkillRegistry

    skill_registry = SkillRegistry()
    skills_dir = Path(settings.skill_definitions_dir)
    if skills_dir.is_dir():
        skill_count = skill_registry.discover(skills_dir)
        logger.info("skill_registry_loaded", count=skill_count, path=str(skills_dir))
    app.state.skill_registry = skill_registry

    skill_injector = SkillInjector(skill_registry)
    app.state.skill_injector = skill_injector
    logger.info("skill_injector_initialized")

    # -- Hybrid skill matcher (S29) ----------------------------------------
    from agent33.skills.calibration import HybridSkillMatcher, MatchThresholds

    hybrid_thresholds = MatchThresholds(
        fuzzy_threshold=settings.skill_match_fuzzy_threshold,
        semantic_threshold=settings.skill_match_semantic_threshold,
        contextual_threshold=settings.skill_match_contextual_threshold,
        max_candidates=settings.skill_match_max_candidates,
    )
    hybrid_skill_matcher = HybridSkillMatcher(
        skill_registry=skill_registry,
        thresholds=hybrid_thresholds,
    )
    app.state.hybrid_skill_matcher = hybrid_skill_matcher
    logger.info("hybrid_skill_matcher_initialized")

    # -- Pack registry (optional) ------------------------------------------
    from agent33.packs.marketplace import LocalPackMarketplace
    from agent33.packs.marketplace_aggregator import MarketplaceAggregator
    from agent33.packs.registry import PackRegistry
    from agent33.packs.remote_marketplace import RemoteMarketplaceConfig, RemotePackMarketplace
    from agent33.packs.rollback import PackRollbackManager
    from agent33.packs.trust_manager import TrustPolicyManager

    packs_dir = Path(settings.pack_definitions_dir)
    local_pack_marketplace = LocalPackMarketplace(Path(settings.pack_marketplace_dir))
    remote_marketplaces: list[RemotePackMarketplace] = []
    raw_remote_sources = settings.pack_marketplace_remote_sources.strip()
    if raw_remote_sources:
        try:
            parsed_sources = json.loads(raw_remote_sources)
        except json.JSONDecodeError:
            parsed_sources = []
            logger.warning("pack_marketplace_remote_sources_invalid")
        if isinstance(parsed_sources, list):
            for item in parsed_sources:
                if not isinstance(item, dict):
                    continue
                try:
                    config = RemoteMarketplaceConfig.model_validate(item)
                except Exception:
                    logger.warning(
                        "pack_marketplace_remote_source_invalid",
                        name=item.get("name"),
                        index_url=item.get("index_url"),
                    )
                    continue
                remote_marketplaces.append(
                    RemotePackMarketplace(
                        config,
                        cache_dir=Path(settings.pack_marketplace_cache_dir),
                        max_download_size_bytes=settings.pack_max_size_mb * 1024 * 1024,
                    )
                )
    pack_marketplace = MarketplaceAggregator([local_pack_marketplace, *remote_marketplaces])
    pack_trust_manager = TrustPolicyManager(orchestration_state_store)
    pack_registry = PackRegistry(
        packs_dir=packs_dir,
        skill_registry=skill_registry,
        marketplace=pack_marketplace,
        trust_policy_manager=pack_trust_manager,
    )
    pack_rollback_manager = PackRollbackManager(
        pack_registry,
        archive_dir=Path(settings.pack_rollback_archive_dir),
        state_store=orchestration_state_store,
    )
    if packs_dir.is_dir():
        pack_count = pack_registry.discover()
        logger.info("pack_registry_loaded", count=pack_count, path=str(packs_dir))
    else:
        logger.debug("pack_definitions_dir_not_found", path=str(packs_dir))
    app.state.pack_registry = pack_registry
    app.state.pack_marketplace = pack_marketplace
    app.state.pack_trust_manager = pack_trust_manager
    app.state.pack_rollback_manager = pack_rollback_manager

    # -- Marketplace curation (Phase 33) -----------------------------------
    from agent33.packs.categories import CategoryRegistry
    from agent33.packs.curation_service import CurationService

    category_registry = CategoryRegistry(
        orchestration_state_store, settings.pack_default_categories
    )
    curation_service = CurationService(
        pack_registry,
        category_registry,
        orchestration_state_store,
        settings.pack_min_quality_score,
        settings.pack_require_review_for_listing,
    )
    app.state.category_registry = category_registry
    app.state.curation_service = curation_service
    logger.info("marketplace_curation_initialized")

    # -- Trust analytics dashboard (Phase 33 / S23) ------------------------
    from agent33.packs.trust_analytics import TrustAnalyticsService

    trust_analytics = TrustAnalyticsService(
        pack_registry,
        pack_trust_manager,
        provenance_collector=None,  # wired later after provenance init
        curation_service=curation_service,
        verification_key=settings.pack_signing_key,
    )
    app.state.trust_analytics = trust_analytics
    logger.info("trust_analytics_initialized")

    # -- Pack audit service (Phase 33 / S24) -------------------------------
    from agent33.packs.audit import PackAuditService

    pack_audit = PackAuditService(
        pack_registry,
        trust_analytics=trust_analytics,
        curation_service=curation_service,
        provenance_collector=None,  # wired later after provenance init
    )
    app.state.pack_audit = pack_audit
    logger.info("pack_audit_service_initialized")

    # -- Hook registry -----------------------------------------------------
    hook_registry = None
    if settings.hooks_enabled:
        from agent33.hooks.registry import HookRegistry

        hook_registry = HookRegistry(max_per_event=settings.hooks_max_per_event)
        hook_registry.discover_builtins()
        app.state.hook_registry = hook_registry
        logger.info("hook_registry_initialized", hook_count=hook_registry.count())

    # -- Script hook discovery (Phase 44) ----------------------------------
    script_hook_discovery = None
    if settings.script_hooks_enabled and hook_registry is not None:
        from agent33.hooks.script_discovery import (
            ScriptHookDiscovery,
            resolve_project_hooks_dir,
        )

        project_hooks = (
            Path(settings.script_hooks_project_dir)
            if settings.script_hooks_project_dir.strip()
            else resolve_project_hooks_dir(Path.cwd())
        )
        user_hooks = (
            Path(settings.script_hooks_user_dir)
            if settings.script_hooks_user_dir.strip()
            else Path.home() / ".agent33" / "hooks"
        )
        script_hook_discovery = ScriptHookDiscovery(
            hook_registry=hook_registry,
            project_hooks_dir=project_hooks,
            user_hooks_dir=user_hooks,
            default_timeout_ms=settings.script_hooks_default_timeout_ms,
            max_timeout_ms=settings.script_hooks_max_timeout_ms,
        )
        discovered = script_hook_discovery.discover()
        app.state.script_hook_discovery = script_hook_discovery
        logger.info("script_hook_discovery_complete", count=discovered)

    # -- Operator session service (Phase 44) -------------------------------
    operator_session_service = None
    if settings.operator_session_enabled:
        from agent33.sessions.service import OperatorSessionService
        from agent33.sessions.storage import FileSessionStorage

        base_dir = (
            Path(settings.operator_session_base_dir)
            if settings.operator_session_base_dir.strip()
            else Path.home() / ".agent33" / "sessions"
        )
        session_storage = FileSessionStorage(
            base_dir=base_dir,
            max_replay_file_bytes=settings.operator_session_max_replay_file_mb * 1024 * 1024,
        )
        operator_session_service = OperatorSessionService(
            storage=session_storage,
            hook_registry=hook_registry,
            checkpoint_interval_seconds=settings.operator_session_checkpoint_interval_seconds,
            max_sessions_retained=settings.operator_session_max_retained,
        )
        app.state.operator_session_service = operator_session_service
        sessions.set_session_service(operator_session_service)

        # Crash detection on startup
        if settings.operator_session_crash_recovery_enabled:
            try:
                crashed = await operator_session_service.detect_incomplete_sessions()
                if crashed:
                    logger.warning(
                        "incomplete_sessions_found",
                        count=len(crashed),
                        session_ids=[s.session_id for s in crashed],
                    )
            except Exception:
                logger.warning("crash_detection_failed", exc_info=True)

        logger.info("operator_session_service_initialized", base_dir=str(base_dir))

    # -- Track 8: Session catalog, lineage, spawn, archive -----------------
    if operator_session_service is not None:
        from agent33.sessions.archive import SessionArchiveService
        from agent33.sessions.catalog import SessionCatalog
        from agent33.sessions.lineage import SessionLineageBuilder
        from agent33.sessions.spawn import SessionSpawnService

        session_catalog = SessionCatalog(operator_session_service)
        app.state.session_catalog = session_catalog
        sessions.set_session_catalog(session_catalog)

        session_lineage_builder = SessionLineageBuilder(operator_session_service)
        app.state.session_lineage_builder = session_lineage_builder
        sessions.set_session_lineage_builder(session_lineage_builder)

        session_spawn_service = SessionSpawnService(
            session_service=operator_session_service,
            templates_dir=settings.session_spawn_templates_dir,
        )
        app.state.session_spawn_service = session_spawn_service
        sessions.set_session_spawn_service(session_spawn_service)

        session_archive_service = SessionArchiveService(operator_session_service)
        app.state.session_archive_service = session_archive_service
        sessions.set_session_archive_service(session_archive_service)

        logger.info("track8_session_services_initialized")

    # -- Track 8: Context engine registry -----------------------------------
    from agent33.context.registry import ContextEngineRegistry

    context_engine_registry = ContextEngineRegistry(
        default_engine=settings.context_engine_default,
    )
    app.state.context_engine_registry = context_engine_registry
    context.set_context_engine_registry(context_engine_registry)
    logger.info(
        "context_engine_registry_initialized",
        default_engine=settings.context_engine_default,
    )

    # -- Web research service (Track 7) ------------------------------------
    from agent33.web_research.service import create_default_web_research_service

    web_research_service = create_default_web_research_service()
    app.state.web_research_service = web_research_service
    research.set_research_service(web_research_service)
    logger.info("web_research_service_initialized")

    # -- Voice sidecar probe / status-line services ------------------------
    voice_sidecar_probe = None
    if settings.voice_sidecar_url.strip() or settings.voice_daemon_transport == "sidecar":
        from agent33.voice.client import VoiceSidecarProbe

        sidecar_url = settings.voice_sidecar_url.strip() or settings.voice_daemon_url.strip()
        voice_sidecar_probe = VoiceSidecarProbe(
            base_url=sidecar_url,
            enabled=settings.voice_daemon_enabled,
            transport=settings.voice_daemon_transport,
            timeout_seconds=settings.voice_sidecar_probe_timeout_seconds,
        )
        app.state.voice_sidecar_probe = voice_sidecar_probe

    from agent33.operator.status_line import StatusLineService

    status_line_service = StatusLineService(
        app_state=app.state,
        workspace_root=Path.cwd(),
        voice_probe=voice_sidecar_probe,
    )
    app.state.status_line_service = status_line_service
    if operator_session_service is not None:
        operator_session_service.set_status_snapshot_builder(status_line_service.build_snapshot)

    # -- WebSocket manager for workflow events ------------------------------
    from agent33.workflows.ws_manager import WorkflowWSManager

    ws_manager = WorkflowWSManager()
    app.state.ws_manager = ws_manager
    workflows.set_ws_manager(ws_manager)
    logger.info("workflow_ws_manager_initialized")

    # -- Workflow transport manager (S33: WS-first / SSE fallback) ----------
    from agent33.workflows.transport import (
        TransportConfig,
        TransportType,
        WorkflowTransportManager,
    )

    _transport_config = TransportConfig(
        preferred=TransportType(settings.workflow_transport_preferred),
        ws_ping_interval=settings.workflow_ws_ping_interval,
        ws_ping_timeout=settings.workflow_ws_ping_timeout,
    )
    workflow_transport_manager = WorkflowTransportManager(
        config=_transport_config,
        ws_manager=ws_manager,
    )
    app.state.workflow_transport_manager = workflow_transport_manager
    logger.info(
        "workflow_transport_manager_initialized",
        preferred=settings.workflow_transport_preferred,
    )

    # -- MCP bridge / server / transport ------------------------------------
    from agent33.mcp_server.bridge import MCPServiceBridge
    from agent33.mcp_server.proxy_manager import ProxyManager
    from agent33.mcp_server.proxy_models import ProxyFleetConfig
    from agent33.mcp_server.server import create_mcp_server

    proxy_config = ProxyFleetConfig()
    if settings.mcp_proxy_config_path.strip():
        proxy_config_path = Path(settings.mcp_proxy_config_path)
        try:
            if proxy_config_path.exists():
                proxy_config = ProxyFleetConfig.model_validate_json(
                    proxy_config_path.read_text(encoding="utf-8")
                )
            else:
                logger.warning("mcp_proxy_config_not_found", path=str(proxy_config_path))
        except Exception as exc:
            logger.warning(
                "mcp_proxy_config_invalid",
                path=str(proxy_config_path),
                error=str(exc),
                exc_info=True,
            )

    proxy_manager = ProxyManager(
        config=proxy_config,
        tool_separator=settings.mcp_proxy_tool_separator,
        health_check_enabled=settings.mcp_proxy_health_check_enabled,
    )
    proxy_manager.set_native_tool_names({tool.name for tool in tool_registry.list_all()})
    if settings.mcp_proxy_enabled:
        await proxy_manager.start_all()
    app.state.proxy_manager = proxy_manager
    mcp_proxy.set_proxy_manager(proxy_manager)
    mcp_proxy.set_config_path(settings.mcp_proxy_config_path)

    mcp_bridge = MCPServiceBridge(
        agent_registry=agent_registry,
        tool_registry=tool_registry,
        model_router=model_router,
        rag_pipeline=rag_pipeline,
        skill_registry=skill_registry,
        workflow_registry=workflows.get_workflow_registry(),
        proxy_manager=proxy_manager,
        tool_governance=tool_governance,
    )
    mcp_server = create_mcp_server(mcp_bridge)
    mcp_transport = None
    if mcp_server is not None:
        try:
            from mcp.server.sse import SseServerTransport
        except ImportError as exc:
            logger.warning(
                "mcp_sse_transport_unavailable",
                error=str(exc),
                exc_info=True,
            )
        else:
            mcp_transport = SseServerTransport("/v1/mcp/messages")

    app.state.mcp_bridge = mcp_bridge
    app.state.mcp_server = mcp_server
    app.state.mcp_transport = mcp_transport
    logger.info(
        "mcp_services_initialized",
        server_enabled=mcp_server is not None,
        transport_enabled=mcp_transport is not None,
    )

    # -- Plugin registry (Phase 32.8 — Plugin SDK) -------------------------
    from agent33.plugins.capabilities import CapabilityGrant
    from agent33.plugins.config_store import PluginConfigStore
    from agent33.plugins.context import PluginContext
    from agent33.plugins.doctor import PluginDoctor
    from agent33.plugins.events import PluginEventStore
    from agent33.plugins.installer import PluginInstaller
    from agent33.plugins.registry import PluginRegistry
    from agent33.plugins.scoped import (
        ReadOnlySettingsProxy,
        ScopedSkillRegistry,
        ScopedToolRegistry,
    )
    from agent33.services.orchestration_state import OrchestrationStateStore

    plugin_state_store = OrchestrationStateStore(settings.plugin_state_store_path)
    plugin_event_store = PluginEventStore(plugin_state_store)
    plugin_config_store = PluginConfigStore(plugin_state_store)
    plugin_registry = PluginRegistry(event_store=plugin_event_store)
    plugins_dir = Path(settings.plugin_definitions_dir)

    def _plugin_context_factory(manifest: Any, plugin_dir: Path) -> PluginContext:
        """Build a scoped context for a plugin."""
        entry = plugin_registry.get(manifest.name)
        owner_tenant_id = entry.tenant_id if entry is not None else ""
        requested_permissions = [p.value for p in manifest.permissions]
        grants = CapabilityGrant(
            manifest_permissions=requested_permissions,
            tenant_grants=plugin_config_store.granted_permissions(
                manifest.name,
                tenant_id=owner_tenant_id,
                manifest_permissions=requested_permissions,
            ),
        )
        stored_config = plugin_config_store.get(manifest.name, tenant_id=owner_tenant_id)
        return PluginContext(
            plugin_name=manifest.name,
            plugin_dir=plugin_dir,
            granted_permissions=grants.effective_permissions,
            skill_registry=ScopedSkillRegistry(skill_registry, grants),
            tool_registry=ScopedToolRegistry(tool_registry, grants),
            agent_registry=agent_registry,
            hook_registry=getattr(app.state, "hook_registry", None),
            plugin_config=(
                dict(stored_config.config_overrides) if stored_config is not None else {}
            ),
            settings_reader=(
                ReadOnlySettingsProxy(settings) if grants.check("config:read") else None
            ),
        )

    app.state.plugin_context_factory = _plugin_context_factory
    app.state.plugin_state_store = plugin_state_store
    app.state.plugin_event_store = plugin_event_store
    app.state.plugin_config_store = plugin_config_store

    if plugins_dir.is_dir():
        plugin_count = plugin_registry.discover(plugins_dir)
        logger.info("plugin_registry_discovered", count=plugin_count, path=str(plugins_dir))
        if plugin_count > 0:
            loaded = await plugin_registry.load_all(_plugin_context_factory)
            logger.info("plugin_registry_loaded", loaded=loaded)
            if settings.plugin_auto_enable:
                for manifest in plugin_registry.list_all():
                    state = plugin_registry.get_state(manifest.name)
                    if state and state.value == "loaded":
                        try:
                            await plugin_registry.enable(manifest.name)
                        except Exception:
                            logger.warning(
                                "plugin_auto_enable_failed",
                                plugin=manifest.name,
                                exc_info=True,
                            )
    else:
        logger.debug("plugin_definitions_dir_not_found", path=str(plugins_dir))

    app.state.plugin_registry = plugin_registry
    app.state.plugin_installer = PluginInstaller(
        plugin_registry,
        plugins_dir=plugins_dir,
        context_factory=_plugin_context_factory,
        event_store=plugin_event_store,
        state_store=plugin_state_store,
        auto_enable=settings.plugin_auto_enable,
    )
    app.state.plugin_doctor = PluginDoctor(
        plugin_registry,
        config_store=plugin_config_store,
        installer=app.state.plugin_installer,
    )

    # -- Tool catalog service (aggregates all tool sources) -----------------
    from agent33.tools.catalog import ToolCatalogService

    tool_catalog_service = ToolCatalogService(
        tool_registry=tool_registry,
        skill_registry=skill_registry,
        plugin_registry=plugin_registry,
    )
    app.state.tool_catalog_service = tool_catalog_service
    tool_catalog_routes.set_catalog_service(tool_catalog_service)
    logger.info("tool_catalog_service_initialized")

    # -- Agent-workflow bridge (with subsystem injection) -------------------
    _register_agent_runtime_bridge(
        model_router,
        register_agent,
        registry=agent_registry,
        skill_injector=skill_injector,
        progressive_recall=progressive_recall,
        effort_router=getattr(agents, "_effort_router", None),
        routing_metrics_emitter=getattr(agents, "_record_effort_routing_metrics", None),
        hook_registry=hook_registry,
    )
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

        capture = ObservationCapture(nats_bus=nats_bus)
        app.state.observation_capture = capture
        logger.info("observation_capture_initialized")

        # Summarizer needs a router - will be available after agents routes init
        app.state.session_summarizer_class = SessionSummarizer
    except Exception:
        logger.debug("memory_subsystem_init_skipped", exc_info=True)

    # --- Comparative evaluation (AWM Tier 2 group-relative scoring) ---
    from agent33.evaluation.comparative.service import ComparativeEvaluationService

    comparative_service = ComparativeEvaluationService(
        elo_k_factor=settings.comparative_elo_k_factor,
        min_population_size=settings.comparative_min_population_size,
        confidence_level=settings.comparative_confidence_level,
    )
    app.state.comparative_service = comparative_service
    comparative.set_comparative_service(comparative_service)
    logger.info("comparative_evaluation_initialized")

    # --- Synthetic environment generation (AWM Tier 2 A5) ---
    from agent33.evaluation.synthetic_envs.service import SyntheticEnvironmentService

    synthetic_environment_service = SyntheticEnvironmentService(
        workflow_dir=Path(settings.synthetic_env_workflow_dir),
        tool_dir=Path(settings.synthetic_env_tool_dir),
        max_saved_bundles=settings.synthetic_env_bundle_retention,
        persistence_path=(
            Path(settings.synthetic_env_bundle_persistence_path)
            if settings.synthetic_env_bundle_persistence_path.strip()
            else None
        ),
    )
    app.state.synthetic_environment_service = synthetic_environment_service
    synthetic_envs.set_synthetic_environment_service(synthetic_environment_service)
    logger.info(
        "synthetic_environment_service_initialized",
        workflow_count=len(synthetic_environment_service.list_workflows()),
    )

    configured_multimodal_service = multimodal.get_multimodal_service()
    daemon_factory = None
    if settings.voice_daemon_transport == "sidecar":
        from agent33.voice.client import SidecarVoiceDaemon

        daemon_factory = SidecarVoiceDaemon
    configured_multimodal_service.configure_voice_runtime(
        enabled=settings.voice_daemon_enabled,
        transport=settings.voice_daemon_transport,
        url=settings.voice_sidecar_url.strip() or settings.voice_daemon_url,
        api_key=settings.voice_daemon_api_key.get_secret_value(),
        api_secret=settings.voice_daemon_api_secret.get_secret_value(),
        room_prefix=settings.voice_daemon_room_prefix,
        max_sessions=settings.voice_daemon_max_sessions,
        daemon_factory=daemon_factory,
    )
    app.state.multimodal_service = configured_multimodal_service
    logger.info(
        "voice_runtime_configured",
        enabled=settings.voice_daemon_enabled,
        transport=settings.voice_daemon_transport,
        room_prefix=settings.voice_daemon_room_prefix,
    )

    # --- Operator control plane ---
    from agent33.operator.service import OperatorService

    operator_service = OperatorService(
        app_state=app.state,
        settings=settings,
        start_time=_start_time,
    )
    app.state.operator_service = operator_service
    logger.info("operator_service_initialized")

    # --- Rate limiter (S42) ---
    # The RateLimiter instance is created eagerly at module scope (for middleware
    # registration). Store the reference on app.state for route DI access.
    if settings.rate_limit_enabled:
        app.state.rate_limiter = _boot_rate_limiter
        logger.info(
            "rate_limiter_initialized",
            default_tier=settings.rate_limit_default_tier,
        )

    # --- Cron CRUD and job history (Track 9) ---
    from agent33.automation.cron_models import JobDefinition, JobHistoryStore

    cron_job_store: dict[str, JobDefinition] = {}
    job_history_store = JobHistoryStore()
    app.state.cron_job_store = cron_job_store
    app.state.job_history_store = job_history_store
    logger.info("cron_job_store_initialized")

    # --- Config apply service (Track 9) ---
    from agent33.config_apply import ConfigApplyService

    config_apply_service = ConfigApplyService(settings_cls=type(settings))
    app.state.config_apply_service = config_apply_service
    logger.info("config_apply_service_initialized")

    # --- Onboarding service (Track 9) ---
    from agent33.operator.onboarding import OnboardingService

    onboarding_service = OnboardingService(app_state=app.state, settings=settings)
    app.state.onboarding_service = onboarding_service
    logger.info("onboarding_service_initialized")

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

    # -- Template catalog --------------------------------------------------
    from agent33.workflows.template_catalog import TemplateCatalog

    _template_dir = Path(settings.agent_definitions_dir).parent / "..core"
    # Resolve the core/workflows directory relative to the engine root
    _core_workflows_dir = Path(settings.agent_definitions_dir).parent.parent / "core" / "workflows"
    if not _core_workflows_dir.is_dir():
        # Fallback: try relative to CWD
        _core_workflows_dir = Path("core/workflows")
    template_catalog = TemplateCatalog(_core_workflows_dir)
    template_catalog.refresh()
    app.state.template_catalog = template_catalog
    workflow_templates.set_template_catalog(template_catalog)
    logger.info(
        "template_catalog_initialized",
        count=len(template_catalog.list_templates()),
        path=str(_core_workflows_dir),
    )

    # -- Workflow template marketplace (S41) --------------------------------
    if settings.workflow_marketplace_enabled:
        from agent33.workflows.marketplace import WorkflowMarketplace

        _wm_dir = settings.workflow_templates_dir
        wf_marketplace = WorkflowMarketplace(_wm_dir if _wm_dir else None)
        wf_marketplace.discover_builtin_templates()
        app.state.workflow_marketplace = wf_marketplace
        workflow_marketplace.set_workflow_marketplace(wf_marketplace)
        logger.info(
            "workflow_marketplace_initialized",
            count=wf_marketplace.count,
            path=_wm_dir,
        )

    # -- Discovery service (Phase 46A) --------------------------------------
    from agent33.discovery.service import DiscoveryService
    from agent33.tools.discovery_runtime import (
        DISCOVER_TOOLS_TOOL_NAME,
        DISCOVER_TOOLS_TOOL_VERSION,
        DiscoverToolsTool,
        ToolActivationManager,
    )
    from agent33.tools.registry_entry import ToolRegistryEntry

    discovery_service = DiscoveryService(
        tool_registry=tool_registry,
        skill_registry=skill_registry,
        pack_registry=pack_registry,
        workflow_registry=workflows.get_workflow_registry(),
        template_catalog=template_catalog,
    )
    tool_activation_manager = ToolActivationManager()
    discover_tools_tool = DiscoverToolsTool(
        discovery_service=discovery_service,
        activation_manager=tool_activation_manager,
        mode=settings.tool_discovery_mode,
    )
    tool_registry.register_with_entry(
        discover_tools_tool,
        ToolRegistryEntry(
            tool_id=DISCOVER_TOOLS_TOOL_NAME,
            name=DISCOVER_TOOLS_TOOL_NAME,
            version=DISCOVER_TOOLS_TOOL_VERSION,
            description=discover_tools_tool.description,
            owner="agent33",
            tags=["discovery", "meta"],
            parameters_schema=discover_tools_tool.parameters_schema,
        ),
    )
    app.state.discovery_service = discovery_service
    app.state.tool_activation_manager = tool_activation_manager
    discovery_routes.set_discovery_service(discovery_service)
    mcp_bridge.discovery_service = discovery_service
    mcp_bridge.tool_activation_manager = tool_activation_manager
    mcp_bridge.tool_discovery_mode = settings.tool_discovery_mode
    proxy_manager.set_native_tool_names({tool.name for tool in tool_registry.list_all()})
    logger.info("discovery_service_initialized")

    # -- Provenance & runtime version -----------------------------------------
    from agent33.provenance.audit_export import AuditExporter as _AuditExporter
    from agent33.provenance.collector import ProvenanceCollector as _ProvenanceCollector
    from agent33.provenance.timeline import AuditTimelineService as _AuditTimelineService
    from agent33.runtime.version import resolve_version as _resolve_version

    _provenance_collector = _ProvenanceCollector(
        max_receipts=settings.provenance_max_receipts,
    )
    _audit_timeline_service = _AuditTimelineService(_provenance_collector)
    _audit_exporter = _AuditExporter(_provenance_collector)
    app.state.provenance_collector = _provenance_collector
    app.state.audit_timeline_service = _audit_timeline_service
    app.state.audit_exporter = _audit_exporter

    # Back-wire provenance collector into trust analytics (initialized earlier)
    if hasattr(app.state, "trust_analytics"):
        app.state.trust_analytics._provenance_collector = _provenance_collector

    # Back-wire provenance collector into pack audit service (initialized earlier)
    if hasattr(app.state, "pack_audit"):
        app.state.pack_audit._provenance_collector = _provenance_collector

    _runtime_version_info = _resolve_version()
    app.state.runtime_version_info = _runtime_version_info
    logger.info(
        "provenance_and_runtime_initialized",
        version=_runtime_version_info.version,
        git_hash=_runtime_version_info.git_short_hash,
    )

    # -- Benchmark harness (S26) ----------------------------------------------
    from agent33.evaluation.benchmark import BenchmarkHarness
    from agent33.evaluation.benchmark_catalog import DEFAULT_BENCHMARK_CATALOG

    _benchmark_catalog = list(DEFAULT_BENCHMARK_CATALOG)
    if settings.evaluation_benchmark_catalog_path.strip():
        _custom_catalog_path = Path(settings.evaluation_benchmark_catalog_path)
        if _custom_catalog_path.exists():
            try:
                _benchmark_catalog = BenchmarkHarness.load_catalog_from_file(_custom_catalog_path)
                logger.info(
                    "benchmark_catalog_loaded_from_file",
                    path=str(_custom_catalog_path),
                    count=len(_benchmark_catalog),
                )
            except Exception as exc:
                logger.warning(
                    "benchmark_catalog_load_failed",
                    path=str(_custom_catalog_path),
                    error=str(exc),
                )
        else:
            logger.warning(
                "benchmark_catalog_path_not_found",
                path=str(_custom_catalog_path),
            )

    benchmark_harness = BenchmarkHarness(task_catalog=_benchmark_catalog)
    app.state.benchmark_harness = benchmark_harness
    evaluations.set_benchmark_harness(benchmark_harness)
    logger.info("benchmark_harness_initialized", tasks=len(_benchmark_catalog))

    # -- Tuning loop scheduler (Phase 31) ------------------------------------
    if settings.improvement_tuning_loop_enabled and settings.improvement_learning_enabled:
        try:
            from agent33.improvement.tuning import TuningLoopScheduler, TuningLoopService

            _improvement_svc = improvements.get_improvement_service()
            _config_apply_svc = getattr(app.state, "config_apply_service", None)
            _tuning_svc = TuningLoopService(_improvement_svc, _config_apply_svc, settings)
            _tuning_scheduler = TuningLoopScheduler(
                _tuning_svc, settings.improvement_tuning_loop_interval_hours
            )
            app.state.tuning_loop_scheduler = _tuning_scheduler
            await _tuning_scheduler.start()
            logger.info("tuning_loop_scheduler_started")
        except Exception:
            logger.warning("tuning_loop_scheduler_init_failed", exc_info=True)

    # -- Alembic migration checker (S34) ------------------------------------
    from agent33.migrations.checker import MigrationChecker as _MigrationChecker

    _migration_checker = _MigrationChecker(
        alembic_dir=str(Path(settings.alembic_config_path).parent / "alembic"),
        config_file=settings.alembic_config_path,
    )
    app.state.migration_checker = _migration_checker
    if settings.alembic_auto_check_on_startup:
        try:
            _mig_status = _migration_checker.get_status()
            if not _mig_status.chain_valid:
                logger.warning("alembic_chain_invalid", heads=_mig_status.heads)
            elif _mig_status.has_multiple_heads:
                logger.warning("alembic_multiple_heads", heads=_mig_status.heads)
            else:
                logger.info(
                    "alembic_chain_ok",
                    head=_mig_status.current_head,
                    revisions=len(_migration_checker.list_revisions()),
                )
        except Exception:
            logger.warning("alembic_auto_check_failed", exc_info=True)

    yield

    # -- Shutdown ----------------------------------------------------------
    logger.info("agent33_stopping")

    # Flush operator sessions before other subsystems shut down
    _session_svc: Any = getattr(app.state, "operator_session_service", None)
    if _session_svc is not None:
        try:
            await _session_svc.shutdown()
            logger.info("operator_session_service_shutdown")
        except Exception:
            logger.warning("operator_session_service_shutdown_failed", exc_info=True)

    _process_manager: Any = getattr(app.state, "process_manager_service", None)
    if _process_manager is not None:
        try:
            await _process_manager.shutdown()
            logger.info("process_manager_service_shutdown")
        except Exception:
            logger.warning("process_manager_service_shutdown_failed", exc_info=True)

    workflows.set_ws_manager(None)

    shutdown_multimodal_service: Any = getattr(app.state, "multimodal_service", None)
    if shutdown_multimodal_service is not None:
        await shutdown_multimodal_service.shutdown_voice_sessions()
        logger.info("voice_runtime_shutdown")

    _plugin_reg: Any = getattr(app.state, "plugin_registry", None)
    if _plugin_reg is not None:
        try:
            await _plugin_reg.unload_all()
            logger.info("plugin_registry_unloaded")
        except Exception:
            logger.warning("plugin_registry_unload_failed", exc_info=True)

    _training_store: Any = getattr(app.state, "training_store", None)
    if _training_store is not None:
        await _training_store.close()

    _proxy_manager: Any = getattr(app.state, "proxy_manager", None)
    if _proxy_manager is not None:
        await _proxy_manager.stop_all()
        logger.info("mcp_proxy_manager_stopped")

    scheduler = getattr(app.state, "training_scheduler", None)
    if scheduler is not None:
        await scheduler.stop()

    _tuning_loop_scheduler: Any = getattr(app.state, "tuning_loop_scheduler", None)
    if _tuning_loop_scheduler is not None:
        await _tuning_loop_scheduler.stop()
        logger.info("tuning_loop_scheduler_stopped")

    # Close embedding provider (cache.close() delegates to provider.close())
    _embedder = getattr(app.state, "embedding_cache", None) or getattr(
        app.state, "embedding_provider", None
    )
    if _embedder is not None:
        await _embedder.close()
        logger.info("embedding_provider_closed")

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
    skill_injector: Any = None,
    progressive_recall: Any = None,
    effort_router: Any = None,
    routing_metrics_emitter: Callable[[dict[str, Any] | None], None] | None = None,
    hook_registry: Any = None,
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

    async def _bridge(inputs: dict[str, Any]) -> dict[str, Any]:
        agent_name = inputs.pop("agent_name", "workflow-agent")
        model = inputs.pop("model", None)
        active_skills_raw = inputs.pop("active_skills", None)

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
        if active_skills_raw is None:
            active_skills = list(definition.skills)
        elif isinstance(active_skills_raw, list):
            active_skills = [
                str(skill).strip() for skill in active_skills_raw if str(skill).strip()
            ]
        else:
            normalized = str(active_skills_raw).strip()
            active_skills = [normalized] if normalized else list(definition.skills)

        runtime = AgentRuntime(
            definition=definition,
            router=model_router,
            model=model,
            skill_injector=skill_injector,
            active_skills=active_skills,
            progressive_recall=progressive_recall,
            effort_router=effort_router,
            routing_metrics_emitter=routing_metrics_emitter,
            hook_registry=hook_registry,
        )
        result = await runtime.invoke(inputs)
        return result.output

    register_fn("__default__", _bridge)


# -- Request size limit middleware ----------------------------------------------


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the configured limit."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size_bytes:
            return Response(
                content='{"detail":"Request body too large"}',
                status_code=413,
                media_type="application/json",
            )
        response: Response = await call_next(request)
        return response


# -- Application factory ------------------------------------------------------

app = FastAPI(
    title="AGENT-33",
    description="Autonomous AI agent orchestration engine",
    version="0.1.0",
    lifespan=lifespan,
)

# -- Middleware (order matters: last added = first executed) --------------------
# Execution order: CORS -> Auth -> RateLimit -> SizeLimit -> HookMiddleware -> Router
# HookMiddleware added first so it runs last (after auth resolves tenant_id)
app.add_middleware(HookMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)

# Rate limit middleware: runs after auth resolves tenant_id.
# The RateLimiter is a lightweight in-memory object, safe to create eagerly.
if settings.rate_limit_enabled:
    from agent33.security.rate_limiter import (
        RateLimiter as _BootRateLimiter,
    )
    from agent33.security.rate_limiter import (
        RateLimitMiddleware,
    )
    from agent33.security.rate_limiter import (
        RateLimitTier as _BootRateLimitTier,
    )

    _boot_rate_limiter = _BootRateLimiter(
        default_tier=_BootRateLimitTier(settings.rate_limit_default_tier),
    )
    # Store eagerly on app.state so tests can reset per-tenant state even
    # before the async lifespan runs (TestClient without context manager).
    app.state.rate_limiter = _boot_rate_limiter
    app.add_middleware(RateLimitMiddleware, rate_limiter=_boot_rate_limiter)

app.add_middleware(AuthMiddleware)

_cors_origins = settings.cors_allowed_origins.split(",") if settings.cors_allowed_origins else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


# -- Routers -------------------------------------------------------------------

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(visualizations.router)
app.include_router(explanations.router)
app.include_router(auth.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(memory_search.router)
app.include_router(discovery_routes.router)
app.include_router(reviews.router)
app.include_router(traces.router)
app.include_router(evaluations.router)
app.include_router(autonomy.router)
app.include_router(releases.router)
app.include_router(research.router)
app.include_router(improvements.router)
app.include_router(training.router)
app.include_router(benchmarks.router)
app.include_router(component_security.router)
app.include_router(outcomes.router)
app.include_router(multimodal.router)
app.include_router(operations_hub.router)
app.include_router(marketplace.router)
app.include_router(mcp.router)
app.include_router(mcp_proxy.router)
app.include_router(mcp_sync.router)
app.include_router(plugins_routes.router)
app.include_router(packs.router)
app.include_router(reasoning.router)
app.include_router(hooks.router)
app.include_router(comparative.router)
app.include_router(synthetic_envs.router)
app.include_router(tool_approvals.router)
app.include_router(tool_mutations.router)
app.include_router(processes.router)
app.include_router(backups.router)
app.include_router(sessions.router)
app.include_router(context.router)
app.include_router(operator.router)
app.include_router(cron.router)
app.include_router(config_routes.router)
app.include_router(workflow_sse.router)
app.include_router(workflow_templates.router)
app.include_router(workflow_marketplace.router)
app.include_router(workflow_transport.router)
app.include_router(workflow_ws.router)
app.include_router(tool_catalog_routes.router)
app.include_router(provenance.router)
app.include_router(connectors.router)
app.include_router(skill_matching_routes.router)
app.include_router(execution_routes.router)
app.include_router(migrations.router)
app.include_router(rate_limits_routes.router)
