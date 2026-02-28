"""FastAPI router for comparative evaluation (AWM Tier 2 group-relative scoring)."""

# NOTE: no ``from __future__ import annotations`` — Pydantic needs these
# types at runtime for request-body validation.

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent33.evaluation.comparative.service import ComparativeEvaluationService
from agent33.security.permissions import require_scope

logger = structlog.get_logger()

router = APIRouter(
    prefix="/v1/evaluation/comparative",
    tags=["comparative-evaluation"],
)

# Module-level service instance (set during lifespan init)
_service: ComparativeEvaluationService | None = None


def set_comparative_service(service: ComparativeEvaluationService) -> None:
    """Inject the comparative evaluation service (called from lifespan)."""
    global _service  # noqa: PLW0603
    _service = service


def get_comparative_service() -> ComparativeEvaluationService:
    """Return the service singleton, raising 503 if not initialized."""
    if _service is None:
        raise HTTPException(
            status_code=503,
            detail="Comparative evaluation service not initialized",
        )
    return _service


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ScoreInput(BaseModel):
    agent_name: str
    metric_name: str
    value: float
    task_id: str | None = None


class RecordScoresRequest(BaseModel):
    scores: list[ScoreInput] = Field(min_length=1, max_length=500)


class EvaluateRequest(BaseModel):
    metric_name: str


class PairwiseRequest(BaseModel):
    agent_a: str
    agent_b: str
    metric_name: str


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------


@router.get(
    "/leaderboard",
    dependencies=[require_scope("workflows:read")],
)
async def get_leaderboard() -> dict[str, Any]:
    """Get the current agent leaderboard."""
    svc = get_comparative_service()
    snapshot = svc.get_latest_leaderboard()
    if snapshot is None:
        # Generate a fresh one
        snapshot = svc.generate_leaderboard()
    return snapshot.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Agent profile
# ---------------------------------------------------------------------------


@router.get(
    "/agents/{name}/profile",
    dependencies=[require_scope("workflows:read")],
)
async def get_agent_profile(name: str) -> dict[str, Any]:
    """Get an agent's comparative profile."""
    svc = get_comparative_service()
    profile = svc.get_agent_profile(name)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {name}")
    return profile.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Evaluate (trigger round-robin)
# ---------------------------------------------------------------------------


@router.post(
    "/evaluate",
    status_code=201,
    dependencies=[require_scope("tools:execute")],
)
async def trigger_evaluation(body: EvaluateRequest) -> dict[str, Any]:
    """Trigger a round-robin comparative evaluation on a metric."""
    svc = get_comparative_service()
    results = svc.run_round_robin(body.metric_name)
    leaderboard = svc.generate_leaderboard()
    return {
        "comparisons": len(results),
        "population_size": leaderboard.population_size,
        "leaderboard_id": leaderboard.snapshot_id,
    }


# ---------------------------------------------------------------------------
# Record scores
# ---------------------------------------------------------------------------


@router.post(
    "/scores",
    status_code=201,
    dependencies=[require_scope("tools:execute")],
)
async def record_scores(body: RecordScoresRequest) -> dict[str, Any]:
    """Record agent scores into the population tracker."""
    from agent33.evaluation.comparative.models import AgentScore

    svc = get_comparative_service()
    scores = [
        AgentScore(
            agent_name=s.agent_name,
            metric_name=s.metric_name,
            value=s.value,
            task_id=s.task_id,
        )
        for s in body.scores
    ]
    svc.record_scores(scores)
    return {"recorded": len(scores), "population_size": svc.population_tracker.population_size}


# ---------------------------------------------------------------------------
# Pairwise comparison
# ---------------------------------------------------------------------------


@router.post(
    "/compare",
    dependencies=[require_scope("workflows:read")],
)
async def pairwise_compare(body: PairwiseRequest) -> dict[str, Any]:
    """Run a pairwise comparison between two agents."""
    svc = get_comparative_service()
    result = svc.run_pairwise_evaluation(body.agent_a, body.agent_b, body.metric_name)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Insufficient data for comparison: {body.agent_a} vs {body.agent_b}",
        )
    return result.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Rating history
# ---------------------------------------------------------------------------


@router.get(
    "/history",
    dependencies=[require_scope("workflows:read")],
)
async def get_rating_history(agent_name: str | None = None) -> dict[str, Any]:
    """Get rating history. If agent_name is given, return that agent's history."""
    svc = get_comparative_service()
    if agent_name:
        history = svc.get_rating_history(agent_name)
        if not history:
            raise HTTPException(status_code=404, detail=f"No history for agent: {agent_name}")
        return {"agent_name": agent_name, "history": history}
    # Return all snapshots
    snapshots = svc.list_leaderboard_history(limit=50)
    return {
        "snapshots": [s.model_dump(mode="json") for s in snapshots],
        "count": len(snapshots),
    }
