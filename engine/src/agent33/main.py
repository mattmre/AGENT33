"""FastAPI application entry point with full integration wiring."""

from __future__ import annotations

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
    benchmarks,
    chat,
    comparative,
    component_security,
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
    multimodal,
    operations_hub,
    operator,
    outcomes,
    packs,
    reasoning,
    releases,
    reviews,
    sessions,
    synthetic_envs,
    tool_approvals,
    traces,
    training,
    visualizations,
    webhooks,
    workflow_sse,
    workflow_templates,
    workflow_ws,
    workflows,
)
from agent33.api.routes import (
    discovery as discovery_routes,
)
from agent33.api.routes import (
    plugins as plugins_routes,
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
    from agent33.tools.governance import ToolGovernance
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
    logger.info("tool_registry_initialized", tool_count=len(tool_registry.list_all()))

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

    # -- Pack registry (optional) ------------------------------------------
    from agent33.packs.marketplace import LocalPackMarketplace
    from agent33.packs.registry import PackRegistry

    packs_dir = Path(settings.pack_definitions_dir)
    pack_marketplace = LocalPackMarketplace(Path(settings.pack_marketplace_dir))
    pack_registry = PackRegistry(
        packs_dir=packs_dir,
        skill_registry=skill_registry,
        marketplace=pack_marketplace,
    )
    if packs_dir.is_dir():
        pack_count = pack_registry.discover()
        logger.info("pack_registry_loaded", count=pack_count, path=str(packs_dir))
    else:
        logger.debug("pack_definitions_dir_not_found", path=str(packs_dir))
    app.state.pack_registry = pack_registry
    app.state.pack_marketplace = pack_marketplace

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
        from agent33.hooks.script_discovery import ScriptHookDiscovery

        project_hooks = (
            Path(settings.script_hooks_project_dir)
            if settings.script_hooks_project_dir.strip()
            else Path.cwd() / ".claude" / "hooks"
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

    # -- WebSocket manager for workflow events ------------------------------
    from agent33.workflows.ws_manager import WorkflowWSManager

    ws_manager = WorkflowWSManager()
    app.state.ws_manager = ws_manager
    workflows.set_ws_manager(ws_manager)
    logger.info("workflow_ws_manager_initialized")

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

    mcp_bridge = MCPServiceBridge(
        agent_registry=agent_registry,
        tool_registry=tool_registry,
        model_router=model_router,
        rag_pipeline=rag_pipeline,
        skill_registry=skill_registry,
        workflow_registry=workflows.get_workflow_registry(),
        proxy_manager=proxy_manager,
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
    from agent33.plugins.context import PluginContext
    from agent33.plugins.registry import PluginRegistry
    from agent33.plugins.scoped import (
        ReadOnlySettingsProxy,
        ScopedSkillRegistry,
        ScopedToolRegistry,
    )

    plugin_registry = PluginRegistry()
    plugins_dir = Path(settings.plugin_definitions_dir)

    def _plugin_context_factory(manifest: Any, plugin_dir: Path) -> PluginContext:
        """Build a scoped context for a plugin."""
        grants = CapabilityGrant(
            manifest_permissions=[p.value for p in manifest.permissions],
        )
        return PluginContext(
            plugin_name=manifest.name,
            plugin_dir=plugin_dir,
            granted_permissions=grants.effective_permissions,
            skill_registry=ScopedSkillRegistry(skill_registry, grants),
            tool_registry=ScopedToolRegistry(tool_registry, grants),
            agent_registry=agent_registry,
            hook_registry=getattr(app.state, "hook_registry", None),
            plugin_config={},
            settings_reader=(
                ReadOnlySettingsProxy(settings) if grants.check("config:read") else None
            ),
        )

    app.state.plugin_context_factory = _plugin_context_factory

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
    configured_multimodal_service.configure_voice_runtime(
        enabled=settings.voice_daemon_enabled,
        transport=settings.voice_daemon_transport,
        url=settings.voice_daemon_url,
        api_key=settings.voice_daemon_api_key.get_secret_value(),
        api_secret=settings.voice_daemon_api_secret.get_secret_value(),
        room_prefix=settings.voice_daemon_room_prefix,
        max_sessions=settings.voice_daemon_max_sessions,
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
        runtime = AgentRuntime(
            definition=definition,
            router=model_router,
            model=model,
            skill_injector=skill_injector,
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
# Execution order: CORS -> Auth -> SizeLimit -> HookMiddleware -> Router
# HookMiddleware added first so it runs last (after auth resolves tenant_id)
app.add_middleware(HookMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
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
app.include_router(sessions.router)
app.include_router(operator.router)
app.include_router(workflow_sse.router)
app.include_router(workflow_templates.router)
app.include_router(workflow_ws.router)
app.include_router(tool_catalog_routes.router)
