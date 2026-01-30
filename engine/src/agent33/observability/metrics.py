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
