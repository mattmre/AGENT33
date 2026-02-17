"""Fact-check criteria hooks for explanation scaffolding."""

from __future__ import annotations

import structlog

from agent33.explanation.models import ExplanationMetadata, FactCheckStatus

logger = structlog.get_logger()


async def run_fact_check_hooks(explanation: ExplanationMetadata) -> FactCheckStatus:
    """Run stage-1 fact-check hooks and return the aggregate status.

    Stage 1 is scaffold-only; hooks are intentionally non-blocking until
    validator strategies are wired in future phase slices.
    """
    logger.info(
        "fact_check_hook_invoked",
        explanation_id=explanation.id,
        entity_type=explanation.entity_type,
        entity_id=explanation.entity_id,
    )
    return FactCheckStatus.SKIPPED

