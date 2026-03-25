"""In-memory metrics collection."""

from __future__ import annotations

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _Observation:
    values: list[float] = field(default_factory=list)


class MetricsCollector:
    """Tracks counters and observations for key metrics."""

    _PROMETHEUS_COUNTER_ALLOWLIST = frozenset(
        {
            "effort_routing_decisions_total",
            "effort_routing_high_effort_total",
            "effort_routing_export_failures_total",
            "http_requests_total",
        }
    )
    _PROMETHEUS_OBSERVATION_ALLOWLIST = frozenset(
        {
            "effort_routing_estimated_cost_usd",
            "effort_routing_estimated_token_budget",
            "db_query_duration_seconds",
            "http_request_duration_seconds",
            "health_check_result",
        }
    )

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

    @staticmethod
    def _parse_label_key(label_key: str) -> dict[str, str]:
        labels: dict[str, str] = {}
        if not label_key:
            return labels
        for item in label_key.split(","):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            labels[key] = value
        return labels

    @staticmethod
    def _escape_label_value(value: str) -> str:
        return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')

    @classmethod
    def _render_prometheus_labels(cls, label_key: str) -> str:
        labels = cls._parse_label_key(label_key)
        if not labels:
            return ""
        rendered = ",".join(
            f'{key}="{cls._escape_label_value(value)}"' for key, value in sorted(labels.items())
        )
        return f"{{{rendered}}}"

    @staticmethod
    def _sanitize_metric_name(name: str) -> str:
        sanitized = re.sub(r"[^a-zA-Z0-9_:]", "_", name)
        if sanitized and sanitized[0].isdigit():
            return f"_{sanitized}"
        return sanitized or "agent33_metric"

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

    def render_prometheus(self) -> str:
        """Render a low-cardinality Prometheus exposition payload."""
        lines: list[str] = []

        for name in sorted(self._PROMETHEUS_COUNTER_ALLOWLIST):
            label_map = self._counters.get(name)
            if not label_map:
                continue
            metric_name = self._sanitize_metric_name(name)
            lines.append(f"# TYPE {metric_name} counter")
            for label_key, value in sorted(label_map.items()):
                lines.append(f"{metric_name}{self._render_prometheus_labels(label_key)} {value}")

        for name in sorted(self._PROMETHEUS_OBSERVATION_ALLOWLIST):
            obs_map = self._observations.get(name)
            if not obs_map:
                continue
            metric_name = self._sanitize_metric_name(name)
            lines.extend(
                [
                    f"# TYPE {metric_name}_count gauge",
                    f"# TYPE {metric_name}_sum gauge",
                    f"# TYPE {metric_name}_avg gauge",
                    f"# TYPE {metric_name}_min gauge",
                    f"# TYPE {metric_name}_max gauge",
                ]
            )
            for label_key, observation in sorted(obs_map.items()):
                values = observation.values
                if not values:
                    continue
                labels = self._render_prometheus_labels(label_key)
                total = sum(values)
                count = len(values)
                minimum = min(values)
                maximum = max(values)
                average = total / count
                lines.extend(
                    [
                        f"{metric_name}_count{labels} {count}",
                        f"{metric_name}_sum{labels} {total}",
                        f"{metric_name}_avg{labels} {average}",
                        f"{metric_name}_min{labels} {minimum}",
                        f"{metric_name}_max{labels} {maximum}",
                    ]
                )

        return "\n".join(lines) + ("\n" if lines else "# no metrics collected\n")


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
