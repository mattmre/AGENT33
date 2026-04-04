"""Agent management and invocation endpoints."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from agent33.agents.capabilities import get_catalog_by_category
from agent33.agents.definition import (
    AgentDefinition,
    AgentRole,
    AgentStatus,
    CapabilityCategory,
    SpecCapability,
)
from agent33.agents.effort import AgentEffort, AgentEffortRouter
from agent33.agents.registry import AgentRegistry
from agent33.agents.runtime import AgentRuntime
from agent33.config import settings
from agent33.llm.ollama import OllamaProvider
from agent33.llm.router import ModelRouter
from agent33.observability.effort_telemetry import (
    EffortTelemetryExporter,
    EffortTelemetryExportError,
    NoopEffortTelemetryExporter,
)
from agent33.observability.metrics import MetricsCollector
from agent33.security.injection import scan_inputs_recursive
from agent33.security.permissions import _get_token_payload, require_scope

router = APIRouter(prefix="/v1/agents", tags=["agents"])
logger = logging.getLogger(__name__)

# -- singletons ----------------------------------------------------------


def _llamacpp_enabled() -> bool:
    """Return True when the local orchestration engine is llama.cpp."""
    return settings.local_orchestration_engine.lower() in ("llama.cpp", "llamacpp")


def _default_agent_model() -> str:
    """Return the default model name for agent invocations."""
    if _llamacpp_enabled():
        return settings.local_orchestration_model
    return settings.ollama_default_model


_model_router = ModelRouter(default_provider="llamacpp" if _llamacpp_enabled() else "ollama")
_model_router.register(
    "ollama",
    OllamaProvider(
        base_url=settings.ollama_base_url,
        default_model=settings.ollama_default_model,
    ),
)

if _llamacpp_enabled():
    from agent33.llm.openai import OpenAIProvider as _LlamaCppProvider

    _model_router.register(
        "llamacpp",
        _LlamaCppProvider(
            api_key="local",
            base_url=settings.local_orchestration_base_url,
            default_model=settings.local_orchestration_model,
        ),
    )

if settings.openai_api_key.get_secret_value():
    from agent33.llm.openai import OpenAIProvider

    _openai_kwargs: dict[str, Any] = {"api_key": settings.openai_api_key.get_secret_value()}
    if settings.openai_base_url:
        _openai_kwargs["base_url"] = settings.openai_base_url
    _model_router.register("openai", OpenAIProvider(**_openai_kwargs))


def _parse_effort_policy(raw: str) -> dict[str, str]:
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Effort policy config must be valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("Effort policy config must be a JSON object")
    parsed: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, str):
            parsed[key] = value
    return parsed


def _resolve_domain_context(request: Request, body_domain: str | None) -> str:
    if body_domain and body_domain.strip():
        return body_domain.strip().lower()
    header_domain = request.headers.get("x-agent-domain", "")
    if header_domain.strip():
        return header_domain.strip().lower()
    host = request.headers.get("host", "")
    return host.split(":", 1)[0].strip().lower() if host else ""


def _resolve_runtime_session_id(request: Request) -> str:
    for candidate in (
        request.headers.get("x-agent-session-id", ""),
        request.headers.get("x-session-id", ""),
        getattr(request.state, "session_id", ""),
    ):
        normalized = str(candidate).strip()
        if normalized:
            return normalized
    return ""


def _build_skill_match_query(definition: AgentDefinition, inputs: dict[str, Any]) -> str:
    """Build a compact query for skill matching from agent + request context."""
    user_payload = json.dumps(inputs, ensure_ascii=False)
    return f"{definition.description}\n\nUser request:\n{user_payload}"


async def _resolve_active_skills(
    *,
    request: Request,
    definition: AgentDefinition,
    model_router: ModelRouter,
    inputs: dict[str, Any],
) -> list[str]:
    """Resolve active skills for an invocation with feature-flagged matching."""
    configured_skills = list(definition.skills)
    if not configured_skills:
        return []
    if not settings.skillsbench_skill_matcher_enabled:
        return configured_skills

    skill_matcher = getattr(request.app.state, "skill_matcher", None)
    if skill_matcher is None:
        skill_registry = getattr(request.app.state, "skill_registry", None)
        if skill_registry is None:
            return configured_skills
        from agent33.skills.matching import SkillMatcher

        skill_matcher = SkillMatcher(
            registry=skill_registry,
            router=model_router,
            model=settings.skillsbench_skill_matcher_model or settings.ollama_default_model,
            top_k=settings.skillsbench_skill_matcher_top_k,
            skip_llm_below=settings.skillsbench_skill_matcher_skip_llm_below,
        )
        request.app.state.skill_matcher = skill_matcher

    allowed = set(configured_skills)
    try:
        match_result = await skill_matcher.match(
            _build_skill_match_query(definition, inputs),
        )
    except Exception:
        logger.warning("skill_match_failed agent=%s", definition.name, exc_info=True)
        return configured_skills

    matched = [skill.name for skill in match_result.skills if skill.name in allowed]
    return matched or configured_skills


_effort_router = AgentEffortRouter(
    enabled=settings.agent_effort_routing_enabled,
    default_effort=settings.agent_effort_default,
    low_model=settings.agent_effort_low_model or None,
    medium_model=settings.agent_effort_medium_model or None,
    high_model=settings.agent_effort_high_model or None,
    low_token_multiplier=settings.agent_effort_low_token_multiplier,
    medium_token_multiplier=settings.agent_effort_medium_token_multiplier,
    high_token_multiplier=settings.agent_effort_high_token_multiplier,
    heuristic_enabled=settings.agent_effort_heuristic_enabled,
    tenant_policies=_parse_effort_policy(settings.agent_effort_policy_tenant),
    domain_policies=_parse_effort_policy(settings.agent_effort_policy_domain),
    tenant_domain_policies=_parse_effort_policy(settings.agent_effort_policy_tenant_domain),
    cost_per_1k_tokens=settings.agent_effort_cost_per_1k_tokens,
    heuristic_low_score_threshold=settings.agent_effort_heuristic_low_score_threshold,
    heuristic_high_score_threshold=settings.agent_effort_heuristic_high_score_threshold,
    heuristic_medium_payload_chars=settings.agent_effort_heuristic_medium_payload_chars,
    heuristic_large_payload_chars=settings.agent_effort_heuristic_large_payload_chars,
    heuristic_many_input_fields_threshold=(
        settings.agent_effort_heuristic_many_input_fields_threshold
    ),
    heuristic_high_iteration_threshold=settings.agent_effort_heuristic_high_iteration_threshold,
    heuristic_simple_max_chars=settings.heuristic_simple_max_chars,
    heuristic_simple_max_words=settings.heuristic_simple_max_words,
)
_metrics = MetricsCollector()
_effort_exporter: EffortTelemetryExporter = NoopEffortTelemetryExporter()


def set_metrics(collector: MetricsCollector) -> None:
    """Swap the global metrics collector (called during app init)."""
    global _metrics
    _metrics = collector


def set_effort_telemetry_exporter(exporter: EffortTelemetryExporter) -> None:
    """Swap the global effort telemetry exporter (called during app init)."""
    global _effort_exporter
    _effort_exporter = exporter


def _record_effort_routing_metrics(routing: dict[str, Any] | None) -> None:
    if not routing:
        return
    effort = str(routing.get("effort") or "unknown")
    source = str(routing.get("source") or routing.get("effort_source") or "unknown")
    labels = {"effort": effort, "source": source}
    _metrics.increment("effort_routing_decisions_total", labels=labels)

    if effort == AgentEffort.HIGH.value:
        _metrics.increment("effort_routing_high_effort_total")

    estimated_token_budget = routing.get("estimated_token_budget")
    if isinstance(estimated_token_budget, int | float):
        _metrics.observe(
            "effort_routing_estimated_token_budget",
            float(estimated_token_budget),
            labels=labels,
        )
        _metrics.observe(
            "effort_routing_estimated_token_budget",
            float(estimated_token_budget),
        )

    estimated_cost = routing.get("estimated_cost")
    if isinstance(estimated_cost, int | float):
        _metrics.observe(
            "effort_routing_estimated_cost_usd",
            float(estimated_cost),
            labels=labels,
        )
        _metrics.observe(
            "effort_routing_estimated_cost_usd",
            float(estimated_cost),
        )

    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "routing": routing,
    }
    try:
        _effort_exporter.export(event)
    except EffortTelemetryExportError:
        _metrics.increment("effort_routing_export_failures_total")
        logger.warning("effort_routing_telemetry_export_failed", exc_info=True)
        if settings.observability_effort_export_fail_closed:
            raise HTTPException(status_code=503, detail="Effort telemetry export failed") from None


# -- dependency injection -------------------------------------------------


def get_registry(request: Request) -> AgentRegistry:
    """Return the shared registry from app state, or a fresh empty one."""
    registry = getattr(request.app.state, "agent_registry", None)
    if registry is None:
        registry = AgentRegistry()
    return registry


# -- request / response models -------------------------------------------


class InvokeRequest(BaseModel):
    """Body for the invoke endpoint."""

    inputs: dict[str, Any] = Field(default_factory=dict)
    model: str | None = None
    temperature: float = 0.7
    effort: AgentEffort | None = None
    domain: str | None = None


class InvokeResponse(BaseModel):
    """Response from the invoke endpoint."""

    agent: str
    output: dict[str, Any]
    tokens_used: int
    model: str
    routing: dict[str, Any] | None = None


class InvokeIterativeRequest(BaseModel):
    """Body for the iterative invoke endpoint."""

    inputs: dict[str, Any] = Field(default_factory=dict)
    model: str | None = None
    temperature: float = 0.7
    effort: AgentEffort | None = None
    domain: str | None = None
    max_iterations: int = 20
    max_tool_calls_per_iteration: int = 5
    enable_double_confirmation: bool = True
    loop_detection_threshold: int = 3
    autonomy_level: int | None = Field(
        default=None,
        ge=0,
        le=3,
        description="P67 autonomy level (0=supervised, 1=default, 2=auto, 3=full). "
        "When set, overrides the constructor-injected RuntimeEnforcer with a "
        "level-derived AutonomyBudget.",
    )


class InvokeIterativeResponse(BaseModel):
    """Response from the iterative invoke endpoint."""

    agent: str
    output: dict[str, Any]
    tokens_used: int
    model: str
    iterations: int
    tool_calls_made: int
    tools_used: list[str]
    termination_reason: str
    routing: dict[str, Any] | None = None


# -- routes ---------------------------------------------------------------


@router.get("/capabilities/catalog")
async def capabilities_catalog() -> dict[str, list[dict[str, str]]]:
    """Return the full spec capability taxonomy grouped by category."""
    return get_catalog_by_category()


@router.get("/search", dependencies=[require_scope("agents:read")])
async def search_agents(
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
    role: str | None = Query(default=None, description="Filter by role"),
    spec_capability: str | None = Query(
        default=None,
        description="Filter by spec capability ID",
    ),
    category: str | None = Query(
        default=None,
        description="Filter by capability category",
    ),
    status: str | None = Query(
        default=None,
        description="Filter by lifecycle status",
    ),
) -> list[dict[str, Any]]:
    """Search agents with multi-criteria AND filtering."""
    try:
        parsed_role = AgentRole(role) if role else None
        parsed_cap = SpecCapability(spec_capability) if spec_capability else None
        parsed_cat = CapabilityCategory(category) if category else None
        parsed_status = AgentStatus(status) if status else None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    results = registry.search(
        role=parsed_role,
        spec_capability=parsed_cap,
        category=parsed_cat,
        status=parsed_status,
    )
    return [_agent_summary(d) for d in results]


@router.get("/by-id/{agent_id}", dependencies=[require_scope("agents:read")])
async def get_agent_by_id(
    agent_id: str,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> dict[str, Any]:
    """Look up an agent by its spec ID (e.g. AGT-001)."""
    definition = registry.get_by_agent_id(agent_id)
    if definition is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent with ID '{agent_id}' not found",
        )
    return definition.model_dump(mode="json")


@router.get("/tool-loop/scores", dependencies=[require_scope("agents:read")])
async def get_tool_loop_scores(
    request: Request,
) -> dict[str, Any]:
    """Return current tool loop scoring data.

    If a ``ToolLoopScorer`` has been installed on ``app.state``,
    this endpoint returns its summary.  Otherwise it returns a minimal
    empty-state response.
    """
    empty: dict[str, Any] = {
        "total_iterations": 0,
        "total_tool_calls": 0,
        "unique_tools": 0,
        "overall_success_rate": 0.0,
        "convergence_detected": False,
        "tool_scores": [],
        "iterations": [],
    }
    scorer = getattr(request.app.state, "tool_loop_scorer", None)
    if scorer is None:
        return empty
    try:
        summary = scorer.get_loop_summary()
        result: dict[str, Any] = summary.model_dump(mode="json")
        return result
    except Exception:
        logger.debug("tool_loop_scorer.get_loop_summary() failed", exc_info=True)
        return empty


# -- profiling endpoints ---------------------------------------------------


@router.get("/profiling/summaries", dependencies=[require_scope("agents:read")])
async def profiling_summaries(
    request: Request,
) -> list[dict[str, Any]]:
    """Return performance summaries for all profiled agents."""
    profiler = getattr(request.app.state, "agent_profiler", None)
    if profiler is None:
        return []
    summaries = profiler.get_all_summaries()
    return [s.model_dump(mode="json") for s in summaries]


@router.get("/profiling/bottlenecks", dependencies=[require_scope("agents:read")])
async def profiling_bottlenecks(
    request: Request,
) -> list[dict[str, Any]]:
    """Detect agents with performance bottlenecks (one phase > 60% of duration)."""
    profiler = getattr(request.app.state, "agent_profiler", None)
    if profiler is None:
        return []
    result: list[dict[str, Any]] = profiler.detect_bottlenecks()
    return result


@router.get("/profiling/hot-paths", dependencies=[require_scope("agents:read")])
async def profiling_hot_paths(
    request: Request,
) -> list[dict[str, Any]]:
    """Identify the slowest agent/model combinations."""
    profiler = getattr(request.app.state, "agent_profiler", None)
    if profiler is None:
        return []
    result: list[dict[str, Any]] = profiler.get_hot_paths()
    return result


@router.get("/profiling/profiles", dependencies=[require_scope("agents:read")])
async def profiling_profiles(
    request: Request,
    agent_name: str | None = Query(default=None, description="Filter by agent name"),
    limit: int = Query(default=50, ge=1, le=500, description="Max profiles to return"),
) -> list[dict[str, Any]]:
    """Return raw invocation profiles, newest first."""
    profiler = getattr(request.app.state, "agent_profiler", None)
    if profiler is None:
        return []
    profiles = profiler.get_profiles(agent_name=agent_name, limit=limit)
    return [p.model_dump(mode="json") for p in profiles]


@router.get("/profiling/{agent_name}", dependencies=[require_scope("agents:read")])
async def profiling_agent_summary(
    agent_name: str,
    request: Request,
) -> dict[str, Any]:
    """Return the performance summary for a single agent."""
    profiler = getattr(request.app.state, "agent_profiler", None)
    if profiler is None:
        raise HTTPException(status_code=404, detail="Profiler not initialized")
    try:
        summary = profiler.get_agent_summary(agent_name)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"No profiles for agent '{agent_name}'",
        ) from None
    result: dict[str, Any] = summary.model_dump(mode="json")
    return result


@router.get("/", dependencies=[require_scope("agents:read")])
async def list_agents(
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> list[dict[str, Any]]:
    """List all registered agent definitions."""
    return [_agent_summary(d) for d in registry.list_all()]


@router.get("/{name}", dependencies=[require_scope("agents:read")])
async def get_agent(
    name: str,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> dict[str, Any]:
    """Return the full definition for a single agent."""
    definition = registry.get(name)
    if definition is None:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return definition.model_dump(mode="json")


@router.post("/", status_code=201, dependencies=[require_scope("agents:write")])
async def register_agent(
    definition: AgentDefinition,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> dict[str, str]:
    """Register a new agent definition."""
    registry.register(definition)
    return {"status": "registered", "name": definition.name}


@router.post("/{name}/invoke", dependencies=[require_scope("agents:invoke")])
async def invoke_agent(
    name: str,
    body: InvokeRequest,
    request: Request,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> InvokeResponse:
    """Invoke a registered agent with the given inputs."""
    definition = registry.get(name)
    if definition is None:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    # Scan inputs for prompt injection (recursive to catch nested payloads)
    scan = scan_inputs_recursive(body.inputs)
    if not scan.is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Input rejected: {', '.join(scan.threats)}",
        )

    # Pull subsystems from app state for agent runtime, falling back to
    # module-level singleton for backward compatibility.
    model_router = getattr(request.app.state, "model_router", _model_router)
    effort_router = getattr(request.app.state, "effort_router", _effort_router)
    skill_injector = getattr(request.app.state, "skill_injector", None)
    progressive_recall = getattr(request.app.state, "progressive_recall", None)
    token_payload = _get_token_payload(request)
    tenant_id = token_payload.tenant_id or ""
    domain = _resolve_domain_context(request, body.domain)
    active_skills = await _resolve_active_skills(
        request=request,
        definition=definition,
        model_router=model_router,
        inputs=body.inputs,
    )

    hook_registry = getattr(request.app.state, "hook_registry", None)
    cost_tracker = getattr(request.app.state, "cost_tracker", None)
    metrics_collector = getattr(request.app.state, "metrics_collector", None)

    runtime = AgentRuntime(
        definition=definition,
        router=model_router,
        model=body.model or _default_agent_model(),
        temperature=body.temperature,
        session_id=_resolve_runtime_session_id(request),
        invocation_mode="invoke",
        effort=body.effort,
        effort_router=effort_router,
        routing_metrics_emitter=_record_effort_routing_metrics,
        skill_injector=skill_injector,
        active_skills=active_skills,
        progressive_recall=progressive_recall,
        tenant_id=tenant_id,
        domain=domain,
        hook_registry=hook_registry,
        cost_tracker=cost_tracker,
        metrics_collector=metrics_collector,
    )

    try:
        result = await runtime.invoke(body.inputs)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        # Handle HookAbortError without hard import dependency
        if type(exc).__name__ == "HookAbortError":
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        raise

    return InvokeResponse(
        agent=name,
        output=result.output,
        tokens_used=result.tokens_used,
        model=result.model,
        routing=result.routing_decision,
    )


@router.post(
    "/{name}/invoke-iterative",
    dependencies=[require_scope("agents:invoke")],
)
async def invoke_agent_iterative(
    name: str,
    body: InvokeIterativeRequest,
    request: Request,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> InvokeIterativeResponse:
    """Invoke a registered agent with the iterative tool-use loop.

    Unlike the standard invoke, this endpoint repeatedly calls the LLM,
    parsing and executing tool calls until the task is complete or a
    limit is reached.
    """
    definition = registry.get(name)
    if definition is None:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    scan = scan_inputs_recursive(body.inputs)
    if not scan.is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Input rejected: {', '.join(scan.threats)}",
        )

    # Pull subsystems from app state
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(
            status_code=503,
            detail="Model router not initialized",
        )
    tool_registry = getattr(request.app.state, "tool_registry", None)
    if tool_registry is None:
        raise HTTPException(
            status_code=503,
            detail="Tool registry not initialized",
        )
    tool_governance = getattr(request.app.state, "tool_governance", None)
    effort_router = getattr(request.app.state, "effort_router", _effort_router)
    skill_injector = getattr(request.app.state, "skill_injector", None)
    progressive_recall = getattr(request.app.state, "progressive_recall", None)

    # Build ToolContext from authenticated user and definition governance
    from agent33.tools.base import ToolContext

    token_payload = _get_token_payload(request)
    user_scopes = token_payload.scopes
    domain = _resolve_domain_context(request, body.domain)
    session_id = _resolve_runtime_session_id(request)
    active_skills = await _resolve_active_skills(
        request=request,
        definition=definition,
        model_router=model_router,
        inputs=body.inputs,
    )

    # Extract tool_policies from definition governance
    tool_policies = definition.governance.tool_policies if definition.governance else {}

    tool_context = ToolContext(
        user_scopes=user_scopes,
        tool_policies=tool_policies,
        requested_by=token_payload.sub,
        tenant_id=token_payload.tenant_id or "",
        session_id=session_id,
    )

    from agent33.agents.tool_loop import ToolLoopConfig

    loop_config = ToolLoopConfig(
        max_iterations=body.max_iterations,
        max_tool_calls_per_iteration=body.max_tool_calls_per_iteration,
        enable_double_confirmation=body.enable_double_confirmation,
        loop_detection_threshold=body.loop_detection_threshold,
    )
    context_compressor = getattr(request.app.state, "context_compressor", None)
    context_manager = getattr(request.app.state, "context_manager", None)
    if context_manager is None and settings.skillsbench_context_manager_enabled:
        from agent33.agents.context_manager import ContextManager, budget_for_model

        selected_model = body.model or settings.ollama_default_model
        context_manager = ContextManager(
            budget=budget_for_model(selected_model),
            router=model_router,
            summarize_model=selected_model,
            skip_summarization=context_compressor is not None,
        )

    hook_registry = getattr(request.app.state, "hook_registry", None)
    tool_activation_manager = getattr(request.app.state, "tool_activation_manager", None)
    cost_tracker = getattr(request.app.state, "cost_tracker", None)
    metrics_collector_iter = getattr(request.app.state, "metrics_collector", None)

    runtime = AgentRuntime(
        definition=definition,
        router=model_router,
        model=body.model or _default_agent_model(),
        temperature=body.temperature,
        session_id=session_id,
        invocation_mode="iterative",
        effort=body.effort,
        effort_router=effort_router,
        routing_metrics_emitter=_record_effort_routing_metrics,
        skill_injector=skill_injector,
        active_skills=active_skills,
        progressive_recall=progressive_recall,
        tool_registry=tool_registry,
        tool_governance=tool_governance,
        tool_context=tool_context,
        tool_activation_manager=tool_activation_manager,
        tool_discovery_mode=settings.tool_discovery_mode,
        context_manager=context_manager,
        tenant_id=token_payload.tenant_id or "",
        domain=domain,
        hook_registry=hook_registry,
        context_compressor=context_compressor,
        cost_tracker=cost_tracker,
        metrics_collector=metrics_collector_iter,
    )

    try:
        result = await runtime.invoke_iterative(
            body.inputs,
            config=loop_config,
            autonomy_level=body.autonomy_level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return InvokeIterativeResponse(
        agent=name,
        output=result.output,
        tokens_used=result.tokens_used,
        model=result.model,
        iterations=result.iterations,
        tool_calls_made=result.tool_calls_made,
        tools_used=result.tools_used,
        termination_reason=result.termination_reason,
        routing=result.routing_decision,
    )


@router.post(
    "/{name}/invoke-iterative/stream",
    dependencies=[require_scope("agents:invoke")],
)
async def invoke_agent_iterative_stream(
    name: str,
    body: InvokeIterativeRequest,
    request: Request,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> StreamingResponse:
    """Stream agent iterative execution via SSE."""
    import asyncio
    import time

    definition = registry.get(name)
    if definition is None:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    scan = scan_inputs_recursive(body.inputs)
    if not scan.is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Input rejected: {', '.join(scan.threats)}",
        )

    # Pull subsystems from app state
    model_router = getattr(request.app.state, "model_router", None)
    if model_router is None:
        raise HTTPException(status_code=503, detail="Model router not initialized")

    tool_registry = getattr(request.app.state, "tool_registry", None)
    if tool_registry is None:
        raise HTTPException(status_code=503, detail="Tool registry not initialized")

    tool_governance = getattr(request.app.state, "tool_governance", None)
    effort_router = getattr(request.app.state, "effort_router", _effort_router)
    skill_injector = getattr(request.app.state, "skill_injector", None)
    progressive_recall = getattr(request.app.state, "progressive_recall", None)
    observation_capture = getattr(request.app.state, "observation_capture", None)
    context_manager = getattr(request.app.state, "context_manager", None)
    context_compressor = getattr(request.app.state, "context_compressor", None)
    hook_registry = getattr(request.app.state, "hook_registry", None)
    token_payload = _get_token_payload(request)
    domain = _resolve_domain_context(request, body.domain)
    session_id = _resolve_runtime_session_id(request)
    active_skills = await _resolve_active_skills(
        request=request,
        definition=definition,
        model_router=model_router,
        inputs=body.inputs,
    )

    from agent33.tools.base import ToolContext

    tool_context = ToolContext(
        user_scopes=token_payload.scopes,
        tool_policies=definition.governance.tool_policies if definition.governance else {},
        requested_by=token_payload.sub,
        tenant_id=token_payload.tenant_id or "",
        session_id=session_id,
    )

    from agent33.agents.tool_loop import ToolLoopConfig

    loop_config = ToolLoopConfig(
        max_iterations=body.max_iterations,
        max_tool_calls_per_iteration=body.max_tool_calls_per_iteration,
        enable_double_confirmation=body.enable_double_confirmation,
        loop_detection_threshold=body.loop_detection_threshold,
    )

    cost_tracker_stream = getattr(request.app.state, "cost_tracker", None)
    metrics_collector_stream = getattr(request.app.state, "metrics_collector", None)

    runtime = AgentRuntime(
        definition=definition,
        router=model_router,
        model=body.model or _default_agent_model(),
        temperature=body.temperature,
        observation_capture=observation_capture,
        session_id=session_id,
        invocation_mode="iterative_stream",
        effort=body.effort,
        effort_router=effort_router,
        routing_metrics_emitter=_record_effort_routing_metrics,
        skill_injector=skill_injector,
        active_skills=active_skills,
        progressive_recall=progressive_recall,
        tool_registry=tool_registry,
        tool_governance=tool_governance,
        tool_context=tool_context,
        tool_activation_manager=getattr(request.app.state, "tool_activation_manager", None),
        tool_discovery_mode=settings.tool_discovery_mode,
        context_manager=context_manager,
        tenant_id=token_payload.tenant_id or "",
        domain=domain,
        hook_registry=hook_registry,
        context_compressor=context_compressor,
        cost_tracker=cost_tracker_stream,
        metrics_collector=metrics_collector_stream,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for event in runtime.invoke_iterative_stream(body.inputs, config=loop_config):
                if await request.is_disconnected():
                    break
                if event.event_type == "completed":
                    try:
                        _record_effort_routing_metrics(runtime.routing_decision_metadata)
                    except HTTPException as exc:
                        error_payload = {
                            "event_type": "error",
                            "iteration": event.iteration,
                            "timestamp": time.time(),
                            "data": {"error": exc.detail, "phase": "telemetry_export"},
                        }
                        yield f"data: {json.dumps(error_payload)}\n\n"
                        return
                yield event.to_sse()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            error_payload = {
                "event_type": "error",
                "iteration": 0,
                "timestamp": time.time(),
                "data": {"error": str(exc), "phase": "endpoint"},
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get(
    "/{name}/context-budget",
    dependencies=[require_scope("agents:read")],
)
async def get_context_budget(
    name: str,
    request: Request,
    registry: AgentRegistry = Depends(get_registry),  # noqa: B008
) -> dict[str, Any]:
    """Return an estimated context budget for the agent's current configuration.

    Builds the system prompt, collects skill instructions, and estimates
    how many tokens each component consumes relative to the model's
    context window.
    """
    from agent33.agents.context_window import ContextWindowManager
    from agent33.agents.runtime import _build_system_prompt

    definition = registry.get(name)
    if definition is None:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")

    # Build system prompt the same way AgentRuntime does
    system_prompt = _build_system_prompt(definition)

    # Collect skill instruction blocks if injector is available
    skill_injector = getattr(request.app.state, "skill_injector", None)
    skill_texts: list[str] = []
    if skill_injector is not None and definition.skills:
        skill_texts.append(skill_injector.build_skill_metadata_block(definition.skills))
        for skill_name in definition.skills:
            skill_texts.append(skill_injector.build_skill_instructions_block(skill_name))

    cwm = getattr(request.app.state, "context_window_manager", None)
    if cwm is None:
        cwm = ContextWindowManager(default_max_tokens=settings.agent_default_context_window)

    budget = cwm.create_budget(
        system_prompt=system_prompt,
        skills=skill_texts if skill_texts else None,
    )
    report = cwm.get_utilization_report(budget)
    report["agent"] = name
    return report


# -- helpers --------------------------------------------------------------


def _agent_summary(d: AgentDefinition) -> dict[str, Any]:
    return {
        "name": d.name,
        "version": d.version,
        "role": d.role.value,
        "description": d.description,
        "agent_id": d.agent_id,
        "spec_capabilities": [c.value for c in d.spec_capabilities],
        "status": d.status.value,
    }
