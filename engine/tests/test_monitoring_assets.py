"""Validation for checked-in monitoring assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GRAFANA_DASHBOARD_PATH = (
    _REPO_ROOT / "deploy" / "monitoring" / "grafana" / "agent33-production-overview.dashboard.json"
)
_PROMETHEUS_RULES_PATH = (
    _REPO_ROOT / "deploy" / "monitoring" / "prometheus" / "agent33-alerts.rules.yaml"
)
_EXPECTED_METRICS = {
    "effort_routing_decisions_total",
    "effort_routing_high_effort_total",
    "effort_routing_export_failures_total",
    "effort_routing_estimated_cost_usd_avg",
    "effort_routing_estimated_token_budget_avg",
}


def _walk_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, list):
        for item in value:
            strings.extend(_walk_strings(item))
    elif isinstance(value, dict):
        for item in value.values():
            strings.extend(_walk_strings(item))
    return strings


def test_grafana_dashboard_is_parseable_and_references_expected_metrics() -> None:
    dashboard = json.loads(_GRAFANA_DASHBOARD_PATH.read_text(encoding="utf-8"))

    assert dashboard["title"] == "AGENT-33 Production Overview"
    assert dashboard["uid"] == "agent33-production-overview"
    assert dashboard["schemaVersion"] >= 39
    assert len(dashboard["panels"]) >= 5

    strings = _walk_strings(dashboard)
    for metric in _EXPECTED_METRICS:
        assert any(metric in item for item in strings), metric


def test_prometheus_rules_are_parseable_and_reference_expected_metrics() -> None:
    payload = yaml.safe_load(_PROMETHEUS_RULES_PATH.read_text(encoding="utf-8"))

    assert isinstance(payload, dict)
    groups = payload.get("groups")
    assert isinstance(groups, list) and groups
    assert groups[0]["name"] == "agent33-observability"

    rules = groups[0].get("rules")
    assert isinstance(rules, list) and len(rules) == 3

    expressions = [rule["expr"] for rule in rules]
    assert any("effort_routing_export_failures_total" in expr for expr in expressions)
    assert any("effort_routing_high_effort_total" in expr for expr in expressions)
    assert any("effort_routing_decisions_total" in expr for expr in expressions)
    assert any("effort_routing_estimated_cost_usd_avg" in expr for expr in expressions)
