"""Tests for comparative evaluation API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agent33.api.routes.comparative import set_comparative_service
from agent33.evaluation.comparative.models import AgentScore
from agent33.evaluation.comparative.service import ComparativeEvaluationService

if TYPE_CHECKING:
    from starlette.testclient import TestClient


def _init_service_with_data() -> ComparativeEvaluationService:
    """Create and populate a test service."""
    svc = ComparativeEvaluationService()
    svc.record_scores(
        [
            AgentScore(agent_name="alpha", metric_name="M-01", value=90.0),
            AgentScore(agent_name="beta", metric_name="M-01", value=70.0),
            AgentScore(agent_name="gamma", metric_name="M-01", value=50.0),
        ]
    )
    set_comparative_service(svc)
    return svc


class TestLeaderboardRoute:
    @pytest.fixture(autouse=True)
    def _setup(self, client: TestClient) -> None:
        self.client = client
        _init_service_with_data()

    def test_get_leaderboard(self) -> None:
        resp = self.client.get("/v1/evaluation/comparative/leaderboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "population_size" in data


class TestAgentProfileRoute:
    @pytest.fixture(autouse=True)
    def _setup(self, client: TestClient) -> None:
        self.client = client
        _init_service_with_data()

    def test_get_profile(self) -> None:
        resp = self.client.get("/v1/evaluation/comparative/agents/alpha/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_name"] == "alpha"
        assert "metric_percentiles" in data

    def test_profile_not_found(self) -> None:
        resp = self.client.get("/v1/evaluation/comparative/agents/nonexistent/profile")
        assert resp.status_code == 404


class TestEvaluateRoute:
    @pytest.fixture(autouse=True)
    def _setup(self, client: TestClient) -> None:
        self.client = client
        _init_service_with_data()

    def test_trigger_evaluation(self) -> None:
        resp = self.client.post(
            "/v1/evaluation/comparative/evaluate",
            json={"metric_name": "M-01"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["comparisons"] == 3  # 3 agents -> 3 pairs
        assert data["population_size"] == 3


class TestRecordScoresRoute:
    @pytest.fixture(autouse=True)
    def _setup(self, client: TestClient) -> None:
        self.client = client
        svc = ComparativeEvaluationService()
        set_comparative_service(svc)

    def test_record_scores(self) -> None:
        resp = self.client.post(
            "/v1/evaluation/comparative/scores",
            json={
                "scores": [
                    {"agent_name": "x", "metric_name": "M-01", "value": 80.0},
                    {"agent_name": "y", "metric_name": "M-01", "value": 60.0},
                ]
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["recorded"] == 2
        assert data["population_size"] == 2

    def test_empty_scores_rejected(self) -> None:
        resp = self.client.post(
            "/v1/evaluation/comparative/scores",
            json={"scores": []},
        )
        assert resp.status_code == 422  # Validation error


class TestPairwiseCompareRoute:
    @pytest.fixture(autouse=True)
    def _setup(self, client: TestClient) -> None:
        self.client = client
        _init_service_with_data()

    def test_compare_success(self) -> None:
        resp = self.client.post(
            "/v1/evaluation/comparative/compare",
            json={"agent_a": "alpha", "agent_b": "beta", "metric_name": "M-01"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["outcome"] == "win"
        assert data["agent_a"] == "alpha"

    def test_compare_missing_data(self) -> None:
        resp = self.client.post(
            "/v1/evaluation/comparative/compare",
            json={"agent_a": "alpha", "agent_b": "nobody", "metric_name": "M-01"},
        )
        assert resp.status_code == 404


class TestHistoryRoute:
    @pytest.fixture(autouse=True)
    def _setup(self, client: TestClient) -> None:
        self.client = client
        svc = _init_service_with_data()
        # Run a round-robin to generate history
        svc.run_round_robin("M-01")

    def test_history_for_agent(self) -> None:
        resp = self.client.get(
            "/v1/evaluation/comparative/history",
            params={"agent_name": "alpha"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_name"] == "alpha"
        assert len(data["history"]) > 1

    def test_history_all_snapshots(self) -> None:
        resp = self.client.get("/v1/evaluation/comparative/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "snapshots" in data

    def test_history_unknown_agent(self) -> None:
        resp = self.client.get(
            "/v1/evaluation/comparative/history",
            params={"agent_name": "ghost"},
        )
        assert resp.status_code == 404
