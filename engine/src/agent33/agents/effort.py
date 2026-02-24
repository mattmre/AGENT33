"""Adaptive effort-based model/token routing for agent execution."""

from __future__ import annotations

import dataclasses
from enum import StrEnum


class AgentEffort(StrEnum):
    """Execution effort level for adaptive routing."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclasses.dataclass(frozen=True, slots=True)
class EffortRoutingDecision:
    """Resolved model/token parameters for a single invocation."""

    effort: AgentEffort
    model: str
    max_tokens: int


class AgentEffortRouter:
    """Resolves model and max_tokens based on effort and feature flags."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        default_effort: AgentEffort | str = AgentEffort.MEDIUM,
        low_model: str | None = None,
        medium_model: str | None = None,
        high_model: str | None = None,
        low_token_multiplier: float = 1.0,
        medium_token_multiplier: float = 1.0,
        high_token_multiplier: float = 1.0,
    ) -> None:
        self._enabled = enabled
        self._default_effort = self._coerce_effort(default_effort, AgentEffort.MEDIUM)
        self._models: dict[AgentEffort, str | None] = {
            AgentEffort.LOW: low_model or None,
            AgentEffort.MEDIUM: medium_model or None,
            AgentEffort.HIGH: high_model or None,
        }
        self._token_multipliers: dict[AgentEffort, float] = {
            AgentEffort.LOW: low_token_multiplier,
            AgentEffort.MEDIUM: medium_token_multiplier,
            AgentEffort.HIGH: high_token_multiplier,
        }

    @staticmethod
    def _coerce_effort(
        effort: AgentEffort | str | None,
        fallback: AgentEffort,
    ) -> AgentEffort:
        if effort is None:
            return fallback
        if isinstance(effort, AgentEffort):
            return effort
        try:
            return AgentEffort(effort)
        except ValueError:
            return fallback

    def resolve(
        self,
        *,
        requested_model: str | None,
        default_model: str,
        max_tokens: int,
        effort: AgentEffort | str | None = None,
    ) -> EffortRoutingDecision:
        """Resolve effective model + max_tokens for this execution."""
        resolved_effort = self._coerce_effort(effort, self._default_effort)
        if not self._enabled:
            return EffortRoutingDecision(
                effort=resolved_effort,
                model=requested_model or default_model,
                max_tokens=max_tokens,
            )

        selected_model = requested_model or self._models[resolved_effort] or default_model
        multiplier = self._token_multipliers[resolved_effort]
        routed_max_tokens = max(1, int(max_tokens * multiplier))
        return EffortRoutingDecision(
            effort=resolved_effort,
            model=selected_model,
            max_tokens=routed_max_tokens,
        )
