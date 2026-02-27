"""Adaptive effort-based model/token routing for agent execution."""

from __future__ import annotations

import dataclasses
import json
from enum import StrEnum
from typing import Any


class AgentEffort(StrEnum):
    """Execution effort level for adaptive routing."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EffortSelectionSource(StrEnum):
    """Source that selected the final effort value."""

    REQUEST = "request"
    POLICY = "policy"
    HEURISTIC = "heuristic"
    DEFAULT = "default"


@dataclasses.dataclass(frozen=True, slots=True)
class EffortRoutingDecision:
    """Resolved model/token parameters for a single invocation."""

    effort: AgentEffort
    effort_source: EffortSelectionSource
    model: str
    max_tokens: int
    token_multiplier: float
    estimated_token_budget: int
    estimated_cost: float | None
    tenant_id: str | None = None
    domain: str | None = None
    policy_key: str | None = None
    heuristic_confidence: float | None = None
    heuristic_reasons: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True, slots=True)
class EffortHeuristicDecision:
    """Deterministic heuristic output for effort selection."""

    effort: AgentEffort
    confidence: float
    reasons: tuple[str, ...]


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
        heuristic_enabled: bool = True,
        tenant_policies: dict[str, AgentEffort | str] | None = None,
        domain_policies: dict[str, AgentEffort | str] | None = None,
        tenant_domain_policies: dict[str, AgentEffort | str] | None = None,
        cost_per_1k_tokens: float = 0.0,
    ) -> None:
        self._enabled = enabled
        self._heuristic_enabled = heuristic_enabled
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
        self._cost_per_1k_tokens = max(0.0, cost_per_1k_tokens)
        self._tenant_policies = self._coerce_policy_map(tenant_policies or {})
        self._domain_policies = self._coerce_policy_map(domain_policies or {}, lower_keys=True)
        self._tenant_domain_policies = self._coerce_policy_map(
            tenant_domain_policies or {}, lower_keys=True
        )

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

    @staticmethod
    def _coerce_policy_map(
        policies: dict[str, AgentEffort | str],
        *,
        lower_keys: bool = False,
    ) -> dict[str, AgentEffort]:
        resolved: dict[str, AgentEffort] = {}
        for key, value in policies.items():
            normalized_key = key.strip()
            if not normalized_key:
                continue
            if lower_keys:
                normalized_key = normalized_key.lower()
            try:
                resolved_value = (
                    value if isinstance(value, AgentEffort) else AgentEffort(value.strip().lower())
                )
            except ValueError:
                continue
            resolved[normalized_key] = resolved_value
        return resolved

    @staticmethod
    def _normalize_tenant(tenant_id: str | None) -> str:
        return (tenant_id or "").strip()

    @staticmethod
    def _normalize_domain(domain: str | None) -> str:
        return (domain or "").strip().lower()

    def _resolve_policy_effort(
        self,
        *,
        tenant_id: str,
        domain: str,
    ) -> tuple[AgentEffort | None, str | None]:
        if tenant_id and domain:
            composite_key = f"{tenant_id}|{domain}"
            if composite_key in self._tenant_domain_policies:
                return self._tenant_domain_policies[composite_key], composite_key
        if tenant_id and tenant_id in self._tenant_policies:
            return self._tenant_policies[tenant_id], tenant_id
        if domain and domain in self._domain_policies:
            return self._domain_policies[domain], domain
        return None, None

    def classify_effort(
        self,
        *,
        inputs: dict[str, Any] | None,
        iterative: bool = False,
        max_iterations: int | None = None,
    ) -> EffortHeuristicDecision:
        """Deterministically classify effort from request shape."""
        if not inputs:
            return EffortHeuristicDecision(
                effort=AgentEffort.LOW,
                confidence=0.8,
                reasons=("empty_or_missing_inputs",),
            )

        payload = json.dumps(inputs, sort_keys=True, ensure_ascii=False)
        payload_len = len(payload)
        top_level_keys = len(inputs)
        lowered = payload.lower()

        score = 0
        reasons: list[str] = []

        if iterative:
            score += 2
            reasons.append("iterative_mode")
        if max_iterations is not None and max_iterations >= 15:
            score += 1
            reasons.append("high_iteration_budget")
        if payload_len >= 2000:
            score += 2
            reasons.append("large_payload")
        elif payload_len >= 800:
            score += 1
            reasons.append("medium_payload")
        if top_level_keys >= 10:
            score += 1
            reasons.append("many_input_fields")
        if any(
            keyword in lowered
            for keyword in (
                "analyze",
                "architecture",
                "optimize",
                "security",
                "root cause",
                "postmortem",
            )
        ):
            score += 1
            reasons.append("complex_task_keywords")

        if score >= 4:
            effort = AgentEffort.HIGH
            confidence = 0.8
        elif score <= 1:
            effort = AgentEffort.LOW
            confidence = 0.72
        else:
            effort = AgentEffort.MEDIUM
            confidence = 0.68
        return EffortHeuristicDecision(
            effort=effort,
            confidence=confidence,
            reasons=tuple(reasons) if reasons else ("balanced_request",),
        )

    def resolve(
        self,
        *,
        requested_model: str | None,
        default_model: str,
        max_tokens: int,
        effort: AgentEffort | str | None = None,
        tenant_id: str | None = None,
        domain: str | None = None,
        inputs: dict[str, Any] | None = None,
        iterative: bool = False,
        max_iterations: int | None = None,
    ) -> EffortRoutingDecision:
        """Resolve effective model + max_tokens for this execution."""
        normalized_tenant = self._normalize_tenant(tenant_id)
        normalized_domain = self._normalize_domain(domain)

        explicit_effort: AgentEffort | None = None
        if effort is not None:
            explicit_effort = self._coerce_effort(effort, self._default_effort)

        policy_effort: AgentEffort | None = None
        policy_key: str | None = None
        if explicit_effort is None:
            policy_effort, policy_key = self._resolve_policy_effort(
                tenant_id=normalized_tenant,
                domain=normalized_domain,
            )

        heuristic_decision: EffortHeuristicDecision | None = None
        if explicit_effort is not None:
            resolved_effort = explicit_effort
            effort_source = EffortSelectionSource.REQUEST
        elif policy_effort is not None:
            resolved_effort = policy_effort
            effort_source = EffortSelectionSource.POLICY
        elif self._heuristic_enabled:
            heuristic_decision = self.classify_effort(
                inputs=inputs,
                iterative=iterative,
                max_iterations=max_iterations,
            )
            resolved_effort = heuristic_decision.effort
            effort_source = EffortSelectionSource.HEURISTIC
        else:
            resolved_effort = self._default_effort
            effort_source = EffortSelectionSource.DEFAULT

        if not self._enabled:
            return EffortRoutingDecision(
                effort=resolved_effort,
                effort_source=effort_source,
                model=requested_model or default_model,
                max_tokens=max_tokens,
                token_multiplier=1.0,
                estimated_token_budget=max_tokens,
                estimated_cost=(
                    round((max_tokens / 1000.0) * self._cost_per_1k_tokens, 6)
                    if self._cost_per_1k_tokens > 0
                    else None
                ),
                tenant_id=normalized_tenant or None,
                domain=normalized_domain or None,
                policy_key=policy_key,
                heuristic_confidence=(
                    heuristic_decision.confidence if heuristic_decision is not None else None
                ),
                heuristic_reasons=(
                    heuristic_decision.reasons if heuristic_decision is not None else ()
                ),
            )

        selected_model = requested_model or self._models[resolved_effort] or default_model
        multiplier = self._token_multipliers[resolved_effort]
        routed_max_tokens = max(1, int(max_tokens * multiplier))
        estimated_cost = (
            round((routed_max_tokens / 1000.0) * self._cost_per_1k_tokens, 6)
            if self._cost_per_1k_tokens > 0
            else None
        )
        return EffortRoutingDecision(
            effort=resolved_effort,
            effort_source=effort_source,
            model=selected_model,
            max_tokens=routed_max_tokens,
            token_multiplier=multiplier,
            estimated_token_budget=routed_max_tokens,
            estimated_cost=estimated_cost,
            tenant_id=normalized_tenant or None,
            domain=normalized_domain or None,
            policy_key=policy_key,
            heuristic_confidence=heuristic_decision.confidence if heuristic_decision else None,
            heuristic_reasons=heuristic_decision.reasons if heuristic_decision else (),
        )
