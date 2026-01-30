"""Alert rules and evaluation against metrics."""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from agent33.observability.metrics import MetricsCollector

_COMPARATORS: dict[str, Callable[[float, float], bool]] = {
    "gt": operator.gt,
    "lt": operator.lt,
    "eq": operator.eq,
}


@dataclass
class AlertRule:
    """Definition of an alert condition."""

    name: str
    metric: str
    threshold: float
    comparator: str  # "gt", "lt", or "eq"


@dataclass
class Alert:
    """A triggered alert."""

    rule_name: str
    metric: str
    current_value: float
    threshold: float
    triggered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AlertManager:
    """Evaluates alert rules against collected metrics."""

    def __init__(self, metrics: MetricsCollector) -> None:
        self._metrics = metrics
        self._rules: list[AlertRule] = []

    def add_rule(
        self,
        name: str,
        metric: str,
        threshold: float,
        comparator: str = "gt",
    ) -> None:
        """Register a new alert rule."""
        if comparator not in _COMPARATORS:
            raise ValueError(f"Unknown comparator: {comparator}. Use gt, lt, or eq.")
        self._rules.append(
            AlertRule(name=name, metric=metric, threshold=threshold, comparator=comparator)
        )

    def check_all(self) -> list[Alert]:
        """Evaluate all rules and return triggered alerts."""
        summary = self._metrics.get_summary()
        triggered: list[Alert] = []

        for rule in self._rules:
            value = summary.get(rule.metric)
            if value is None:
                continue
            # Handle both scalar values and dicts with a "count" key.
            if isinstance(value, dict):
                value = value.get("count", 0)
            compare_fn = _COMPARATORS[rule.comparator]
            if compare_fn(float(value), rule.threshold):
                triggered.append(
                    Alert(
                        rule_name=rule.name,
                        metric=rule.metric,
                        current_value=float(value),
                        threshold=rule.threshold,
                    )
                )

        return triggered
