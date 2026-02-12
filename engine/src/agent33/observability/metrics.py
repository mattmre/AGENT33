"""In-memory metrics collection."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _Observation:
    values: list[float] = field(default_factory=list)


class MetricsCollector:
    """Tracks counters and observations for key metrics."""

    def __init__(self) -> None:
        self._counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._observations: dict[str, dict[str, _Observation]] = defaultdict(
            lambda: defaultdict(_Observation)
        )

    @staticmethod
    def _label_key(labels: dict[str, str] | None) -> str:
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def increment(self, name: str, labels: dict[str, str] | None = None) -> None:
        """Increment a counter by 1."""
        key = self._label_key(labels)
        self._counters[name][key] += 1

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record an observed value (e.g. latency)."""
        key = self._label_key(labels)
        self._observations[name][key].values.append(value)

    def get_summary(self) -> dict[str, Any]:
        """Return a summary of all metrics."""
        summary: dict[str, Any] = {}

        # Counters
        for name, label_map in self._counters.items():
            if len(label_map) == 1 and "" in label_map:
                summary[name] = label_map[""]
            else:
                summary[name] = dict(label_map)

        # Observations
        for name, obs_map in self._observations.items():
            for label_key, obs in obs_map.items():
                display = f"{name}({label_key})" if label_key else name
                vals = obs.values
                if vals:
                    summary[display] = {
                        "count": len(vals),
                        "sum": sum(vals),
                        "avg": sum(vals) / len(vals),
                        "min": min(vals),
                        "max": max(vals),
                    }

        return summary


# ---------------------------------------------------------------------------
# CA-060: Dollar-Cost Attribution
# ---------------------------------------------------------------------------

# Default pricing per 1K tokens (USD)
DEFAULT_MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
}


@dataclass
class CostReport:
    """Summary of costs for a given scope and period."""

    scope: str
    total_cost: float
    input_tokens: int
    output_tokens: int
    invocations: int
    breakdown: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class _UsageRecord:
    model: str
    tokens_in: int
    tokens_out: int
    cost: float
    timestamp: float
    scope: str  # e.g. "workflow:my-wf" or "user:alice"


class CostTracker:
    """Tracks dollar costs per agent invocation, workflow run, and org.

    Pricing tables are configurable at init time.
    """

    def __init__(
        self,
        pricing: dict[str, dict[str, float]] | None = None,
    ) -> None:
        self._pricing = pricing or dict(DEFAULT_MODEL_PRICING)
        self._records: list[_UsageRecord] = []

    def set_pricing(self, model: str, input_per_1k: float, output_per_1k: float) -> None:
        """Set or update pricing for a model."""
        self._pricing[model] = {"input": input_per_1k, "output": output_per_1k}

    def record_usage(
        self,
        model: str,
        tokens_in: int,
        tokens_out: int,
        scope: str = "global",
    ) -> float:
        """Record a usage event and return the computed cost.

        Parameters
        ----------
        model:
            Model identifier (must be in pricing table).
        tokens_in:
            Number of input tokens.
        tokens_out:
            Number of output tokens.
        scope:
            Attribution scope (e.g. ``"workflow:build"``, ``"user:alice"``).

        Returns
        -------
        float
            Dollar cost of this invocation.
        """
        prices = self._pricing.get(model, {"input": 0.0, "output": 0.0})
        cost = (tokens_in / 1000.0) * prices["input"] + (tokens_out / 1000.0) * prices["output"]
        self._records.append(
            _UsageRecord(
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost=cost,
                timestamp=time.time(),
                scope=scope,
            )
        )
        return cost

    def get_cost(
        self,
        scope: str | None = None,
        period: tuple[float, float] | None = None,
    ) -> CostReport:
        """Get a cost report for the given scope and time period.

        Parameters
        ----------
        scope:
            Filter by scope prefix. ``None`` means all scopes.
        period:
            ``(start_timestamp, end_timestamp)`` filter. ``None`` means all time.

        Returns
        -------
        CostReport
        """
        filtered = self._records
        report_scope = scope or "global"

        if scope is not None:
            filtered = [r for r in filtered if r.scope == scope or r.scope.startswith(scope + ":")]

        if period is not None:
            start, end = period
            filtered = [r for r in filtered if start <= r.timestamp <= end]

        total_cost = sum(r.cost for r in filtered)
        total_in = sum(r.tokens_in for r in filtered)
        total_out = sum(r.tokens_out for r in filtered)

        # Build breakdown by model
        by_model: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"cost": 0.0, "tokens_in": 0, "tokens_out": 0, "count": 0}
        )
        for r in filtered:
            entry = by_model[r.model]
            entry["cost"] += r.cost
            entry["tokens_in"] += r.tokens_in
            entry["tokens_out"] += r.tokens_out
            entry["count"] += 1

        breakdown = [{"model": m, **v} for m, v in by_model.items()]

        return CostReport(
            scope=report_scope,
            total_cost=round(total_cost, 6),
            input_tokens=total_in,
            output_tokens=total_out,
            invocations=len(filtered),
            breakdown=breakdown,
        )
