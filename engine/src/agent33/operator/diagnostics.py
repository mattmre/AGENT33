"""Diagnostic checks for the operator doctor endpoint."""

from __future__ import annotations

import logging
from typing import Any

from agent33.operator.models import CheckStatus, DiagnosticCheck

logger = logging.getLogger(__name__)


async def check_database(app_state: Any) -> DiagnosticCheck:
    """DOC-01: PostgreSQL connectivity."""
    try:
        ltm = getattr(app_state, "long_term_memory", None)
        if ltm is None:
            return DiagnosticCheck(
                id="DOC-01",
                category="database",
                status=CheckStatus.ERROR,
                message="LongTermMemory not initialized",
                remediation="Verify DATABASE_URL is set and PostgreSQL is reachable",
            )
        # Attempt a lightweight probe
        engine = getattr(ltm, "_engine", None)
        if engine is not None:
            from sqlalchemy import text

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return DiagnosticCheck(
                id="DOC-01",
                category="database",
                status=CheckStatus.OK,
                message="PostgreSQL connected",
            )
        # Engine not available but LTM exists -- partial
        return DiagnosticCheck(
            id="DOC-01",
            category="database",
            status=CheckStatus.WARNING,
            message="LongTermMemory exists but engine not inspectable",
            remediation="Check database connection pool health",
        )
    except Exception as exc:
        logger.debug("DOC-01 failed: %s", exc)
        return DiagnosticCheck(
            id="DOC-01",
            category="database",
            status=CheckStatus.ERROR,
            message=f"PostgreSQL check failed: {exc}",
            remediation="Verify DATABASE_URL and ensure PostgreSQL is running",
        )


async def check_redis(app_state: Any) -> DiagnosticCheck:
    """DOC-02: Redis connectivity."""
    try:
        redis_conn = getattr(app_state, "redis", None)
        if redis_conn is None:
            return DiagnosticCheck(
                id="DOC-02",
                category="redis",
                status=CheckStatus.WARNING,
                message="Redis not initialized",
                remediation="Set REDIS_URL and ensure Redis is running",
            )
        await redis_conn.ping()
        return DiagnosticCheck(
            id="DOC-02",
            category="redis",
            status=CheckStatus.OK,
            message="Redis connected",
        )
    except Exception as exc:
        logger.debug("DOC-02 failed: %s", exc)
        return DiagnosticCheck(
            id="DOC-02",
            category="redis",
            status=CheckStatus.ERROR,
            message=f"Redis check failed: {exc}",
            remediation="Verify REDIS_URL and ensure Redis is running",
        )


async def check_nats(app_state: Any) -> DiagnosticCheck:
    """DOC-03: NATS connectivity."""
    try:
        nats_bus = getattr(app_state, "nats_bus", None)
        if nats_bus is None:
            return DiagnosticCheck(
                id="DOC-03",
                category="nats",
                status=CheckStatus.WARNING,
                message="NATS bus not initialized",
                remediation="Set NATS_URL and ensure NATS server is running",
            )
        if nats_bus.is_connected:
            return DiagnosticCheck(
                id="DOC-03",
                category="nats",
                status=CheckStatus.OK,
                message="NATS connected",
            )
        return DiagnosticCheck(
            id="DOC-03",
            category="nats",
            status=CheckStatus.ERROR,
            message="NATS bus exists but not connected",
            remediation="Check NATS_URL and verify NATS server is reachable",
        )
    except Exception as exc:
        logger.debug("DOC-03 failed: %s", exc)
        return DiagnosticCheck(
            id="DOC-03",
            category="nats",
            status=CheckStatus.ERROR,
            message=f"NATS check failed: {exc}",
            remediation="Verify NATS_URL and ensure NATS is running",
        )


async def check_llm(app_state: Any) -> DiagnosticCheck:
    """DOC-04: LLM provider reachability."""
    try:
        model_router = getattr(app_state, "model_router", None)
        if model_router is None:
            return DiagnosticCheck(
                id="DOC-04",
                category="llm",
                status=CheckStatus.WARNING,
                message="Model router not initialized",
                remediation="Verify OLLAMA_BASE_URL or OPENAI_API_KEY is configured",
            )
        providers = getattr(model_router, "_providers", {})
        if not providers:
            return DiagnosticCheck(
                id="DOC-04",
                category="llm",
                status=CheckStatus.WARNING,
                message="No LLM providers registered",
                remediation="Configure at least one LLM provider (Ollama or OpenAI)",
            )
        return DiagnosticCheck(
            id="DOC-04",
            category="llm",
            status=CheckStatus.OK,
            message=f"{len(providers)} LLM provider(s) registered",
        )
    except Exception as exc:
        logger.debug("DOC-04 failed: %s", exc)
        return DiagnosticCheck(
            id="DOC-04",
            category="llm",
            status=CheckStatus.ERROR,
            message=f"LLM check failed: {exc}",
            remediation="Check LLM provider configuration",
        )


async def check_agents(app_state: Any) -> DiagnosticCheck:
    """DOC-05: Agent definitions directory and loaded agents."""
    try:
        registry = getattr(app_state, "agent_registry", None)
        if registry is None:
            return DiagnosticCheck(
                id="DOC-05",
                category="agents",
                status=CheckStatus.ERROR,
                message="Agent registry not initialized",
                remediation="Ensure AGENT_DEFINITIONS_DIR is set and contains JSON definitions",
            )
        count = len(registry.list_all())
        if count == 0:
            return DiagnosticCheck(
                id="DOC-05",
                category="agents",
                status=CheckStatus.WARNING,
                message="Agent registry is empty (0 definitions loaded)",
                remediation="Add agent JSON definitions to AGENT_DEFINITIONS_DIR",
            )
        return DiagnosticCheck(
            id="DOC-05",
            category="agents",
            status=CheckStatus.OK,
            message=f"{count} agent definition(s) loaded",
        )
    except Exception as exc:
        logger.debug("DOC-05 failed: %s", exc)
        return DiagnosticCheck(
            id="DOC-05",
            category="agents",
            status=CheckStatus.ERROR,
            message=f"Agent check failed: {exc}",
            remediation="Check AGENT_DEFINITIONS_DIR path and JSON validity",
        )


async def check_skills(app_state: Any) -> DiagnosticCheck:
    """DOC-06: Skills directory and loaded skills."""
    try:
        registry = getattr(app_state, "skill_registry", None)
        if registry is None:
            return DiagnosticCheck(
                id="DOC-06",
                category="skills",
                status=CheckStatus.WARNING,
                message="Skill registry not initialized",
                remediation="Ensure SKILL_DEFINITIONS_DIR is set",
            )
        count = len(registry.list_all())
        return DiagnosticCheck(
            id="DOC-06",
            category="skills",
            status=CheckStatus.OK if count > 0 else CheckStatus.WARNING,
            message=f"{count} skill(s) loaded",
            remediation="Add SKILL.md files to SKILL_DEFINITIONS_DIR" if count == 0 else None,
        )
    except Exception as exc:
        logger.debug("DOC-06 failed: %s", exc)
        return DiagnosticCheck(
            id="DOC-06",
            category="skills",
            status=CheckStatus.ERROR,
            message=f"Skill check failed: {exc}",
            remediation="Check SKILL_DEFINITIONS_DIR path and SKILL.md validity",
        )


async def check_plugins(app_state: Any) -> DiagnosticCheck:
    """DOC-07: Plugin directory and plugin states."""
    try:
        registry = getattr(app_state, "plugin_registry", None)
        if registry is None:
            return DiagnosticCheck(
                id="DOC-07",
                category="plugins",
                status=CheckStatus.WARNING,
                message="Plugin registry not initialized",
                remediation="Ensure PLUGIN_DEFINITIONS_DIR is set",
            )
        all_plugins = registry.list_all()
        count = len(all_plugins)
        error_count = 0
        for manifest in all_plugins:
            state = registry.get_state(manifest.name)
            if state is not None and state.value == "error":
                error_count += 1
        if error_count > 0:
            return DiagnosticCheck(
                id="DOC-07",
                category="plugins",
                status=CheckStatus.WARNING,
                message=f"{count} plugin(s), {error_count} in error state",
                remediation="Check plugin logs for load/enable failures",
            )
        return DiagnosticCheck(
            id="DOC-07",
            category="plugins",
            status=CheckStatus.OK,
            message=f"{count} plugin(s) loaded",
        )
    except Exception as exc:
        logger.debug("DOC-07 failed: %s", exc)
        return DiagnosticCheck(
            id="DOC-07",
            category="plugins",
            status=CheckStatus.ERROR,
            message=f"Plugin check failed: {exc}",
            remediation="Check plugin directory and manifests",
        )


async def check_packs(app_state: Any) -> DiagnosticCheck:
    """DOC-08: Pack directory and loadability."""
    try:
        registry = getattr(app_state, "pack_registry", None)
        if registry is None:
            return DiagnosticCheck(
                id="DOC-08",
                category="packs",
                status=CheckStatus.WARNING,
                message="Pack registry not initialized",
                remediation="Ensure PACK_DEFINITIONS_DIR is set",
            )
        all_packs = registry.list_all()
        count = len(all_packs)
        return DiagnosticCheck(
            id="DOC-08",
            category="packs",
            status=CheckStatus.OK,
            message=f"{count} pack(s) loaded",
        )
    except Exception as exc:
        logger.debug("DOC-08 failed: %s", exc)
        return DiagnosticCheck(
            id="DOC-08",
            category="packs",
            status=CheckStatus.ERROR,
            message=f"Pack check failed: {exc}",
            remediation="Check pack directory and PACK.yaml validity",
        )


async def check_security(app_state: Any) -> DiagnosticCheck:
    """DOC-09: Security configuration (JWT secret, DB credentials)."""
    from agent33.config import settings

    issues: list[str] = []
    remediations: list[str] = []

    if settings.jwt_secret.get_secret_value() == "change-me-in-production":
        issues.append("JWT secret is using default value")
        remediations.append(
            "Set JWT_SECRET environment variable to a cryptographically random value"
        )

    if "agent33:agent33@" in settings.database_url:
        issues.append("Database credentials are using defaults")
        remediations.append("Set DATABASE_URL with rotated credentials")

    if settings.api_secret_key.get_secret_value() == "change-me-in-production":
        issues.append("API secret key is using default value")
        remediations.append("Set API_SECRET_KEY to a strong random value")

    if issues:
        return DiagnosticCheck(
            id="DOC-09",
            category="security",
            status=CheckStatus.WARNING,
            message="; ".join(issues),
            remediation="; ".join(remediations),
        )
    return DiagnosticCheck(
        id="DOC-09",
        category="security",
        status=CheckStatus.OK,
        message="Security configuration looks good",
    )


async def check_config(app_state: Any) -> DiagnosticCheck:
    """DOC-10: General config validation (deprecated/conflicting values)."""
    from agent33.config import settings

    issues: list[str] = []

    # Check for potentially conflicting settings
    if settings.training_enabled and not settings.database_url:
        issues.append("training_enabled=True but no DATABASE_URL configured")

    if settings.embedding_cache_enabled and settings.embedding_cache_max_size < 1:
        issues.append("embedding_cache_enabled but max_size < 1")

    if issues:
        return DiagnosticCheck(
            id="DOC-10",
            category="config",
            status=CheckStatus.WARNING,
            message="; ".join(issues),
            remediation="Review configuration for consistency",
        )
    return DiagnosticCheck(
        id="DOC-10",
        category="config",
        status=CheckStatus.OK,
        message="No configuration issues detected",
    )


ALL_CHECKS = [
    check_database,
    check_redis,
    check_nats,
    check_llm,
    check_agents,
    check_skills,
    check_plugins,
    check_packs,
    check_security,
    check_config,
]


async def run_all_checks(app_state: Any) -> list[DiagnosticCheck]:
    """Run every diagnostic check and return results."""
    results: list[DiagnosticCheck] = []
    for check_fn in ALL_CHECKS:
        try:
            result = await check_fn(app_state)
            results.append(result)
        except Exception as exc:
            logger.exception("Diagnostic check %s raised unexpectedly", check_fn.__name__)
            results.append(
                DiagnosticCheck(
                    id=check_fn.__doc__.split(":")[0] if check_fn.__doc__ else "UNKNOWN",
                    category="internal",
                    status=CheckStatus.ERROR,
                    message=f"Check raised unexpectedly: {exc}",
                )
            )
    return results
