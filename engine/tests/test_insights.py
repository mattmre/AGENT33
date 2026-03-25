"""Tests for the Session Analytics & Insights Engine (Phase 57)."""

from __future__ import annotations

import time
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from agent33.api.routes.insights import set_insights_dependencies
from agent33.observability.insights import InsightsEngine, InsightsReport
from agent33.observability.metrics import CostTracker, MetricsCollector

if TYPE_CHECKING:
    from starlette.testclient import TestClient


# ---------------------------------------------------------------------------
# Unit tests: InsightsEngine
# ---------------------------------------------------------------------------


class TestInsightsEngineAggregation:
    """Verify the engine computes correct aggregate values."""

    def test_basic_aggregation_with_cost_tracker(self) -> None:
        """Engine sums tokens and cost from CostTracker records."""
        mc = MetricsCollector()
        ct = CostTracker(pricing={"gpt-4": {"input": 0.03, "output": 0.06}})

        # Record two invocations
        ct.record_usage("gpt-4", tokens_in=1000, tokens_out=500, scope="global")
        ct.record_usage("gpt-4", tokens_in=2000, tokens_out=1000, scope="global")

        engine = InsightsEngine(mc, ct)
        report = engine.generate(days=1)

        assert isinstance(report, InsightsReport)
        assert report.total_tokens == 4500  # 1000+500+2000+1000
        assert report.total_cost_usd > Decimal("0")
        assert report.period_days == 1
        assert report.generated_at != ""

    def test_model_usage_breakdown(self) -> None:
        """Engine produces per-model usage data with correct structure."""
        mc = MetricsCollector()
        ct = CostTracker(
            pricing={
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            }
        )

        ct.record_usage("gpt-4", tokens_in=1000, tokens_out=500, scope="global")
        ct.record_usage("gpt-3.5-turbo", tokens_in=5000, tokens_out=3000, scope="global")

        engine = InsightsEngine(mc, ct)
        report = engine.generate(days=1)

        assert "gpt-4" in report.model_usage
        assert "gpt-3.5-turbo" in report.model_usage

        gpt4 = report.model_usage["gpt-4"]
        assert gpt4["tokens"] == 1500
        assert gpt4["input_tokens"] == 1000
        assert gpt4["output_tokens"] == 500
        assert gpt4["invocations"] == 1
        assert gpt4["cost_usd"] > 0

        gpt35 = report.model_usage["gpt-3.5-turbo"]
        assert gpt35["tokens"] == 8000
        assert gpt35["invocations"] == 1

    def test_cost_computation_accuracy(self) -> None:
        """Verify dollar cost matches expected value from pricing table."""
        mc = MetricsCollector()
        ct = CostTracker(pricing={"test-model": {"input": 0.01, "output": 0.02}})

        # 2000 input tokens at $0.01/1K = $0.02
        # 1000 output tokens at $0.02/1K = $0.02
        # Total = $0.04
        ct.record_usage("test-model", tokens_in=2000, tokens_out=1000, scope="global")

        engine = InsightsEngine(mc, ct)
        report = engine.generate(days=1)

        assert report.total_cost_usd == Decimal("0.04")

    def test_sessions_from_http_counter(self) -> None:
        """Engine derives total_sessions from http_requests_total counter."""
        mc = MetricsCollector()
        mc.increment("http_requests_total")
        mc.increment("http_requests_total")
        mc.increment("http_requests_total")

        engine = InsightsEngine(mc)
        report = engine.generate(days=1)

        assert report.total_sessions == 3

    def test_sessions_from_labeled_http_counter(self) -> None:
        """Engine sums labeled http_requests_total counters."""
        mc = MetricsCollector()
        mc.increment("http_requests_total", {"method": "GET"})
        mc.increment("http_requests_total", {"method": "GET"})
        mc.increment("http_requests_total", {"method": "POST"})

        engine = InsightsEngine(mc)
        report = engine.generate(days=1)

        assert report.total_sessions == 3

    def test_avg_duration_from_latency_observation(self) -> None:
        """Engine derives avg_session_duration from request latency observations."""
        mc = MetricsCollector()
        mc.observe("http_request_duration_seconds", 0.5)
        mc.observe("http_request_duration_seconds", 1.5)

        engine = InsightsEngine(mc)
        report = engine.generate(days=1)

        assert report.avg_session_duration_seconds == pytest.approx(1.0, abs=0.01)


class TestInsightsEngineTimeWindow:
    """Verify time-window filtering."""

    def test_excludes_old_records(self) -> None:
        """Records older than the window are excluded from token/cost totals."""
        mc = MetricsCollector()
        ct = CostTracker(pricing={"test-model": {"input": 0.01, "output": 0.02}})

        # Record a usage event, then manually backdate it
        ct.record_usage("test-model", tokens_in=1000, tokens_out=500, scope="global")
        # Backdate the record to 10 days ago
        ct._records[-1] = ct._records[-1].__class__(
            model="test-model",
            tokens_in=1000,
            tokens_out=500,
            cost=ct._records[-1].cost,
            timestamp=time.time() - (10 * 86400),
            scope="global",
        )

        # Record a recent usage event
        ct.record_usage("test-model", tokens_in=2000, tokens_out=1000, scope="global")

        engine = InsightsEngine(mc, ct)

        # 1-day window should only include the recent record
        report_1d = engine.generate(days=1)
        assert report_1d.total_tokens == 3000  # only 2000+1000

        # 30-day window should include both records
        report_30d = engine.generate(days=30)
        assert report_30d.total_tokens == 4500  # 1000+500+2000+1000

    def test_daily_activity_fills_gaps(self) -> None:
        """Daily activity includes entries for days with no activity."""
        mc = MetricsCollector()
        ct = CostTracker(pricing={"test-model": {"input": 0.01, "output": 0.02}})
        ct.record_usage("test-model", tokens_in=100, tokens_out=50, scope="global")

        engine = InsightsEngine(mc, ct)
        report = engine.generate(days=3)

        # Should have entries for each day in the 3-day window
        assert len(report.daily_activity) >= 3
        # Today's entry should have activity
        today_entry = report.daily_activity[-1]
        assert today_entry["tokens"] == 150
        assert today_entry["sessions"] == 1

    def test_minimum_days_clamped_to_1(self) -> None:
        """Days parameter below 1 is clamped to 1."""
        mc = MetricsCollector()
        engine = InsightsEngine(mc)
        report = engine.generate(days=0)
        assert report.period_days == 1

        report_neg = engine.generate(days=-5)
        assert report_neg.period_days == 1


class TestInsightsEngineTenantIsolation:
    """Verify per-tenant filtering."""

    def test_tenant_filter_includes_matching_records(self) -> None:
        """Only records matching the tenant scope are included."""
        mc = MetricsCollector()
        ct = CostTracker(pricing={"test-model": {"input": 0.01, "output": 0.02}})

        ct.record_usage("test-model", tokens_in=1000, tokens_out=500, scope="tenant:acme")
        ct.record_usage("test-model", tokens_in=2000, tokens_out=1000, scope="tenant:globex")
        ct.record_usage(
            "test-model", tokens_in=500, tokens_out=250, scope="tenant:acme:workflow:build"
        )

        engine = InsightsEngine(mc, ct)
        report = engine.generate(days=1, tenant_id="acme")

        # Should include tenant:acme (1000+500) + tenant:acme:workflow:build (500+250)
        assert report.total_tokens == 2250

    def test_tenant_filter_excludes_other_tenants(self) -> None:
        """Records from other tenants are excluded."""
        mc = MetricsCollector()
        ct = CostTracker(pricing={"test-model": {"input": 0.01, "output": 0.02}})

        ct.record_usage("test-model", tokens_in=1000, tokens_out=500, scope="tenant:acme")
        ct.record_usage("test-model", tokens_in=2000, tokens_out=1000, scope="tenant:globex")

        engine = InsightsEngine(mc, ct)
        report = engine.generate(days=1, tenant_id="globex")

        assert report.total_tokens == 3000  # only globex tokens

    def test_no_tenant_filter_includes_all(self) -> None:
        """Without tenant_id, all records are included."""
        mc = MetricsCollector()
        ct = CostTracker(pricing={"test-model": {"input": 0.01, "output": 0.02}})

        ct.record_usage("test-model", tokens_in=1000, tokens_out=500, scope="tenant:acme")
        ct.record_usage("test-model", tokens_in=2000, tokens_out=1000, scope="tenant:globex")

        engine = InsightsEngine(mc, ct)
        report = engine.generate(days=1, tenant_id=None)

        assert report.total_tokens == 4500  # all tenants


class TestInsightsEngineEdgeCases:
    """Edge cases and empty-data scenarios."""

    def test_empty_metrics_produces_zero_report(self) -> None:
        """Engine returns a valid report with zero values when no data exists."""
        mc = MetricsCollector()
        engine = InsightsEngine(mc)
        report = engine.generate(days=30)

        assert report.total_sessions == 0
        assert report.total_tokens == 0
        assert report.total_cost_usd == Decimal("0")
        assert report.avg_session_duration_seconds == 0.0
        assert report.tool_usage == {}
        assert report.model_usage == {}
        assert report.daily_activity == []
        assert report.period_days == 30

    def test_no_cost_tracker_still_reports_sessions(self) -> None:
        """Without CostTracker, session count from MetricsCollector is reported."""
        mc = MetricsCollector()
        mc.increment("http_requests_total")
        mc.increment("http_requests_total")

        engine = InsightsEngine(mc, cost_tracker=None)
        report = engine.generate(days=1)

        assert report.total_sessions == 2
        assert report.total_tokens == 0
        assert report.total_cost_usd == Decimal("0")

    def test_tool_usage_from_effort_routing(self) -> None:
        """When no tool-specific counters exist, effort routing is reported."""
        mc = MetricsCollector()
        mc.increment("effort_routing_decisions_total")
        mc.increment("effort_routing_decisions_total")

        engine = InsightsEngine(mc)
        report = engine.generate(days=1)

        assert "effort_routing" in report.tool_usage
        assert report.tool_usage["effort_routing"] == 2


# ---------------------------------------------------------------------------
# API route integration tests
# ---------------------------------------------------------------------------


class TestInsightsRoute:
    """Test the GET /v1/insights endpoint."""

    @pytest.fixture(autouse=True)
    def _setup(self, client: TestClient) -> None:
        self.client = client
        # Wire a fresh MetricsCollector + CostTracker for the route
        self.mc = MetricsCollector()
        self.ct = CostTracker(pricing={"gpt-4": {"input": 0.03, "output": 0.06}})
        self.mc.increment("http_requests_total")
        self.ct.record_usage("gpt-4", tokens_in=1000, tokens_out=500, scope="global")
        set_insights_dependencies(self.mc, self.ct)

    def test_default_response_shape(self) -> None:
        """GET /v1/insights returns all expected keys with correct types."""
        resp = self.client.get("/v1/insights")
        assert resp.status_code == 200

        data = resp.json()
        assert "total_sessions" in data
        assert "total_tokens" in data
        assert "total_cost_usd" in data
        assert "avg_session_duration_seconds" in data
        assert "tool_usage" in data
        assert "model_usage" in data
        assert "daily_activity" in data
        assert "period_days" in data
        assert "generated_at" in data

        assert isinstance(data["total_sessions"], int)
        assert isinstance(data["total_tokens"], int)
        assert isinstance(data["total_cost_usd"], float)
        assert isinstance(data["period_days"], int)
        assert isinstance(data["tool_usage"], dict)
        assert isinstance(data["model_usage"], dict)
        assert isinstance(data["daily_activity"], list)

    def test_response_values_match_seeded_data(self) -> None:
        """Returned values reflect the seeded MetricsCollector and CostTracker data."""
        resp = self.client.get("/v1/insights")
        data = resp.json()

        assert data["total_sessions"] == 1
        assert data["total_tokens"] == 1500  # 1000 + 500
        assert data["total_cost_usd"] > 0
        assert data["period_days"] == 30

        assert "gpt-4" in data["model_usage"]
        assert data["model_usage"]["gpt-4"]["invocations"] == 1

    def test_days_query_param(self) -> None:
        """The days query parameter controls the lookback period."""
        resp = self.client.get("/v1/insights?days=7")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period_days"] == 7

    def test_days_validation_rejects_zero(self) -> None:
        """Days < 1 is rejected by the query param validator."""
        resp = self.client.get("/v1/insights?days=0")
        assert resp.status_code == 422  # FastAPI validation error

    def test_days_validation_rejects_too_large(self) -> None:
        """Days > 365 is rejected by the query param validator."""
        resp = self.client.get("/v1/insights?days=999")
        assert resp.status_code == 422

    def test_tenant_id_filter(self) -> None:
        """The tenant_id query parameter filters cost data."""
        # Seed tenant-specific data
        self.ct.record_usage("gpt-4", tokens_in=500, tokens_out=200, scope="tenant:acme")
        set_insights_dependencies(self.mc, self.ct)

        resp = self.client.get("/v1/insights?tenant_id=acme")
        assert resp.status_code == 200
        data = resp.json()

        # Only the tenant:acme record should be included
        assert data["total_tokens"] == 700  # 500 + 200

    def test_unauthenticated_returns_401(self) -> None:
        """Request without auth token gets 401."""
        from starlette.testclient import TestClient

        from agent33.main import app

        anon_client = TestClient(app)
        resp = anon_client.get("/v1/insights")
        assert resp.status_code == 401

    def test_daily_activity_shape(self) -> None:
        """Each entry in daily_activity has date, sessions, tokens, cost_usd."""
        resp = self.client.get("/v1/insights?days=3")
        data = resp.json()

        assert len(data["daily_activity"]) >= 3
        for entry in data["daily_activity"]:
            assert "date" in entry
            assert "sessions" in entry
            assert "tokens" in entry
            assert "cost_usd" in entry
