"""Phase 30 MVP tests for adaptive effort routing."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from agent33.agents.definition import (
    AgentConstraints,
    AgentDefinition,
    AgentParameter,
    AgentRole,
)
from agent33.agents.effort import AgentEffort, AgentEffortRouter, EffortSelectionSource
from agent33.agents.runtime import AgentResult, AgentRuntime
from agent33.agents.tool_loop import ToolLoopConfig
from agent33.config import Settings
from agent33.llm.base import LLMResponse
from agent33.observability.alerts import AlertManager
from agent33.observability.metrics import MetricsCollector


def _make_definition(max_tokens: int = 100) -> AgentDefinition:
    return AgentDefinition(
        name="phase30-agent",
        version="1.0.0",
        role=AgentRole.IMPLEMENTER,
        inputs={"task": AgentParameter(type="string", required=False)},
        outputs={"result": AgentParameter(type="string")},
        constraints=AgentConstraints(max_tokens=max_tokens),
    )


def _text_response(
    content: str = '{"result": "ok"}',
    model: str = "base-model",
) -> LLMResponse:
    return LLMResponse(
        content=content,
        model=model,
        prompt_tokens=10,
        completion_tokens=5,
    )


class TestAgentEffortRouter:
    @pytest.mark.parametrize(
        (
            "resolve_kwargs",
            "expected_effort",
            "expected_source",
            "expected_model",
            "expected_tokens",
        ),
        [
            (
                {
                    "effort": AgentEffort.HIGH,
                    "tenant_id": "tenant-a",
                    "domain": "finance",
                    "inputs": {"task": "brief"},
                },
                AgentEffort.HIGH,
                EffortSelectionSource.REQUEST,
                "high-model",
                180,
            ),
            (
                {
                    "effort": None,
                    "tenant_id": "tenant-a",
                    "domain": "finance",
                    "inputs": {"task": "brief"},
                },
                AgentEffort.HIGH,
                EffortSelectionSource.POLICY,
                "high-model",
                180,
            ),
            (
                {
                    "effort": None,
                    "tenant_id": "tenant-z",
                    "domain": "ops",
                    "inputs": {"task": "brief"},
                },
                AgentEffort.LOW,
                EffortSelectionSource.HEURISTIC,
                "low-model",
                90,
            ),
            (
                {
                    "effort": None,
                    "tenant_id": "tenant-z",
                    "domain": "ops",
                    "inputs": {
                        "task": (
                            "Analyze architecture tradeoffs for routing strategy and "
                            + ("context " * 180)
                        )
                    },
                },
                AgentEffort.MEDIUM,
                EffortSelectionSource.HEURISTIC,
                "medium-model",
                120,
            ),
            (
                {
                    "effort": None,
                    "tenant_id": "tenant-z",
                    "domain": "ops",
                    "inputs": {"task": "security review " + ("details " * 500)},
                    "iterative": True,
                    "max_iterations": 20,
                },
                AgentEffort.HIGH,
                EffortSelectionSource.HEURISTIC,
                "high-model",
                180,
            ),
        ],
    )
    def test_acceptance_matrix_routing_outcomes(
        self,
        resolve_kwargs: dict[str, object],
        expected_effort: AgentEffort,
        expected_source: EffortSelectionSource,
        expected_model: str,
        expected_tokens: int,
    ) -> None:
        router = AgentEffortRouter(
            enabled=True,
            default_effort=AgentEffort.MEDIUM,
            low_model="low-model",
            medium_model="medium-model",
            high_model="high-model",
            low_token_multiplier=0.75,
            medium_token_multiplier=1.0,
            high_token_multiplier=1.5,
            heuristic_enabled=True,
            tenant_domain_policies={"tenant-a|finance": "high"},
        )

        decision = router.resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=120,
            **resolve_kwargs,
        )

        assert decision.effort == expected_effort
        assert decision.effort_source == expected_source
        assert decision.model == expected_model
        assert decision.max_tokens == expected_tokens
        assert decision.estimated_token_budget == expected_tokens

        if decision.effort_source == EffortSelectionSource.HEURISTIC:
            assert decision.heuristic_confidence is not None
            assert decision.heuristic_reasons
        else:
            assert decision.heuristic_confidence is None
            assert decision.heuristic_reasons == ()

    def test_resolve_uses_default_effort_model_and_multiplier(self) -> None:
        router = AgentEffortRouter(
            enabled=True,
            default_effort=AgentEffort.MEDIUM,
            medium_model="medium-model",
            medium_token_multiplier=1.5,
            heuristic_enabled=False,
        )

        decision = router.resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=100,
            effort=None,
        )

        assert decision.effort == AgentEffort.MEDIUM
        assert decision.model == "medium-model"
        assert decision.max_tokens == 150
        assert decision.effort_source == EffortSelectionSource.DEFAULT

    def test_resolve_requested_model_takes_precedence(self) -> None:
        router = AgentEffortRouter(
            enabled=True,
            high_model="high-model",
            high_token_multiplier=2.0,
        )

        decision = router.resolve(
            requested_model="user-model",
            default_model="fallback-model",
            max_tokens=100,
            effort=AgentEffort.HIGH,
        )

        assert decision.model == "user-model"
        assert decision.max_tokens == 200
        assert decision.effort_source == EffortSelectionSource.REQUEST

    def test_resolve_disabled_keeps_behavior_unchanged(self) -> None:
        router = AgentEffortRouter(
            enabled=False,
            high_model="high-model",
            high_token_multiplier=2.0,
        )

        decision = router.resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=123,
            effort=AgentEffort.HIGH,
        )

        assert decision.model == "fallback-model"
        assert decision.max_tokens == 123

    def test_precedence_explicit_over_policy_classifier_and_default(self) -> None:
        router = AgentEffortRouter(
            enabled=True,
            default_effort=AgentEffort.LOW,
            heuristic_enabled=True,
            tenant_policies={"tenant-a": "medium"},
            high_model="high-model",
        )
        decision = router.resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=100,
            effort=AgentEffort.HIGH,
            tenant_id="tenant-a",
            inputs={"task": "small"},
        )
        assert decision.effort == AgentEffort.HIGH
        assert decision.effort_source == EffortSelectionSource.REQUEST
        assert decision.policy_key is None

    def test_precedence_policy_over_heuristic_and_default(self) -> None:
        router = AgentEffortRouter(
            enabled=True,
            default_effort=AgentEffort.LOW,
            heuristic_enabled=True,
            tenant_policies={"tenant-a": "high"},
        )
        decision = router.resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=100,
            effort=None,
            tenant_id="tenant-a",
            inputs={"task": "small and simple"},
        )
        assert decision.effort == AgentEffort.HIGH
        assert decision.effort_source == EffortSelectionSource.POLICY
        assert decision.policy_key == "tenant-a"

    def test_precedence_heuristic_over_default_when_no_explicit_or_policy(self) -> None:
        router = AgentEffortRouter(
            enabled=True,
            default_effort=AgentEffort.HIGH,
            heuristic_enabled=True,
        )
        decision = router.resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=100,
            effort=None,
            inputs={"task": "brief"},
        )
        assert decision.effort == AgentEffort.LOW
        assert decision.effort_source == EffortSelectionSource.HEURISTIC

    def test_default_used_when_heuristic_disabled_and_no_policy(self) -> None:
        router = AgentEffortRouter(
            enabled=True,
            default_effort=AgentEffort.MEDIUM,
            heuristic_enabled=False,
        )
        decision = router.resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=100,
            effort=None,
            inputs={"task": "brief"},
        )
        assert decision.effort == AgentEffort.MEDIUM
        assert decision.effort_source == EffortSelectionSource.DEFAULT

    def test_resolve_tenant_domain_policy_resolution(self) -> None:
        router = AgentEffortRouter(
            enabled=True,
            heuristic_enabled=False,
            tenant_policies={"tenant-a": "medium"},
            domain_policies={"security": "high"},
            tenant_domain_policies={"tenant-a|security": "low"},
        )
        decision = router.resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=100,
            tenant_id="tenant-a",
            domain="SECURITY",
        )
        assert decision.effort == AgentEffort.LOW
        assert decision.effort_source == EffortSelectionSource.POLICY
        assert decision.policy_key == "tenant-a|security"

    def test_resolve_cost_telemetry_fields_present(self) -> None:
        router = AgentEffortRouter(
            enabled=True,
            heuristic_enabled=False,
            default_effort=AgentEffort.HIGH,
            high_token_multiplier=1.5,
            cost_per_1k_tokens=0.25,
        )
        decision = router.resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=200,
            effort=None,
        )
        assert decision.token_multiplier == 1.5
        assert decision.estimated_token_budget == 300
        assert decision.estimated_cost is not None
        assert decision.estimated_cost > 0.0

    def test_heuristic_score_thresholds_are_configurable(self) -> None:
        payload = {"task": "analyze architecture tradeoffs"}
        baseline = AgentEffortRouter(
            enabled=True,
            heuristic_enabled=True,
        ).resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=100,
            inputs=payload,
        )
        assert baseline.effort == AgentEffort.LOW
        assert baseline.heuristic_score == 1
        assert baseline.heuristic_low_threshold == 1
        assert baseline.heuristic_high_threshold == 4

        tuned = AgentEffortRouter(
            enabled=True,
            heuristic_enabled=True,
            heuristic_low_score_threshold=0,
            heuristic_high_score_threshold=1,
        ).resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=100,
            inputs=payload,
        )
        assert tuned.effort == AgentEffort.HIGH
        assert tuned.heuristic_score == 1
        assert tuned.heuristic_low_threshold == 0
        assert tuned.heuristic_high_threshold == 1

    def test_payload_thresholds_are_configurable(self) -> None:
        decision = AgentEffortRouter(
            enabled=True,
            heuristic_enabled=True,
            heuristic_low_score_threshold=0,
            heuristic_high_score_threshold=2,
            heuristic_medium_payload_chars=20,
            heuristic_large_payload_chars=30,
        ).resolve(
            requested_model=None,
            default_model="fallback-model",
            max_tokens=100,
            inputs={"task": "x" * 40},
        )
        assert decision.effort == AgentEffort.HIGH
        assert decision.heuristic_score == 2
        assert "large_payload" in decision.heuristic_reasons


class TestAgentRuntimeEffortRouting:
    async def test_invoke_acceptance_matrix_includes_heuristic_metadata(self) -> None:
        definition = _make_definition(max_tokens=120)
        model_router = MagicMock()

        async def _complete(*_args, **kwargs):
            return _text_response(model=str(kwargs["model"]))

        model_router.complete = AsyncMock(side_effect=_complete)
        effort_router = AgentEffortRouter(
            enabled=True,
            low_model="low-model",
            medium_model="medium-model",
            high_model="high-model",
            low_token_multiplier=0.75,
            medium_token_multiplier=1.0,
            high_token_multiplier=1.5,
            heuristic_enabled=True,
        )
        runtime = AgentRuntime(
            definition=definition,
            router=model_router,
            effort=None,
            effort_router=effort_router,
        )

        result = await runtime.invoke(
            {
                "task": (
                    "Analyze architecture tradeoffs for routing strategy and " + ("context " * 180)
                )
            }
        )

        assert result.model == "medium-model"
        assert result.routing_decision is not None
        assert result.routing_decision["effort"] == AgentEffort.MEDIUM.value
        assert result.routing_decision["effort_source"] == EffortSelectionSource.HEURISTIC.value
        assert result.routing_decision["heuristic_reasons"]
        assert result.routing_decision["routed_max_tokens"] == 120
        assert result.routing_decision["agent_name"] == "phase30-agent"
        assert result.routing_decision["invocation_mode"] == "invoke"
        assert result.routing_decision["completion_status"] == "completed"
        assert result.routing_decision["tokens_used"] == 15
        assert result.routing_decision["input_field_count"] == 1
        assert result.routing_decision["input_char_count"] > 0
        assert result.routing_decision["invocation_id"]

    async def test_invoke_uses_routed_model_and_max_tokens(self) -> None:
        definition = _make_definition(max_tokens=100)
        model_router = MagicMock()
        model_router.complete = AsyncMock(return_value=_text_response(model="routed-model"))
        effort_router = AgentEffortRouter(
            enabled=True,
            high_model="routed-model",
            high_token_multiplier=2.0,
        )

        runtime = AgentRuntime(
            definition=definition,
            router=model_router,
            effort=AgentEffort.HIGH,
            effort_router=effort_router,
        )
        result = await runtime.invoke({"task": "route me"})

        call_kwargs = model_router.complete.call_args.kwargs
        assert call_kwargs["model"] == "routed-model"
        assert call_kwargs["max_tokens"] == 200
        assert result.routing_decision is not None
        assert result.routing_decision["effort_source"] == EffortSelectionSource.REQUEST.value

    async def test_invoke_uses_tenant_domain_policy_context(self) -> None:
        definition = _make_definition(max_tokens=100)
        model_router = MagicMock()
        model_router.complete = AsyncMock(return_value=_text_response(model="policy-model"))
        effort_router = AgentEffortRouter(
            enabled=True,
            heuristic_enabled=False,
            tenant_domain_policies={"tenant-x|finance": "high"},
            high_model="policy-model",
            high_token_multiplier=2.0,
        )
        runtime = AgentRuntime(
            definition=definition,
            router=model_router,
            effort=None,
            effort_router=effort_router,
            tenant_id="tenant-x",
            domain="finance",
        )
        result = await runtime.invoke({"task": "route by policy"})
        call_kwargs = model_router.complete.call_args.kwargs
        assert call_kwargs["model"] == "policy-model"
        assert call_kwargs["max_tokens"] == 200
        assert result.routing_decision is not None
        assert result.routing_decision["effort_source"] == EffortSelectionSource.POLICY.value
        assert result.routing_decision["policy_key"] == "tenant-x|finance"

    async def test_invoke_iterative_uses_routed_model_and_max_tokens(self) -> None:
        definition = _make_definition(max_tokens=120)
        model_router = MagicMock()
        model_router.complete = AsyncMock(return_value=_text_response(model="iter-model"))
        tool_registry = MagicMock()
        tool_registry.list_all.return_value = []
        effort_router = AgentEffortRouter(
            enabled=True,
            high_model="iter-model",
            high_token_multiplier=1.5,
        )

        runtime = AgentRuntime(
            definition=definition,
            router=model_router,
            effort=AgentEffort.HIGH,
            effort_router=effort_router,
            tool_registry=tool_registry,
        )
        result = await runtime.invoke_iterative(
            {"task": "iterative route"},
            config=ToolLoopConfig(enable_double_confirmation=False),
        )

        call_kwargs = model_router.complete.call_args.kwargs
        assert call_kwargs["model"] == "iter-model"
        assert call_kwargs["max_tokens"] == 180
        assert result.routing_decision is not None
        assert result.routing_decision["estimated_token_budget"] == 180

    async def test_invoke_includes_heuristic_calibration_metadata(self) -> None:
        definition = _make_definition(max_tokens=100)
        model_router = MagicMock()
        model_router.complete = AsyncMock(return_value=_text_response(model="heuristic-model"))
        effort_router = AgentEffortRouter(
            enabled=True,
            heuristic_enabled=True,
            heuristic_low_score_threshold=0,
            heuristic_high_score_threshold=1,
        )

        runtime = AgentRuntime(
            definition=definition,
            router=model_router,
            effort=None,
            effort_router=effort_router,
        )
        result = await runtime.invoke({"task": "analyze architecture tradeoffs"})

        assert result.routing_decision is not None
        assert result.routing_decision["heuristic_score"] == 1
        assert result.routing_decision["heuristic_low_threshold"] == 0
        assert result.routing_decision["heuristic_high_threshold"] == 1

    async def test_invoke_iterative_stream_tracks_completion_metadata(self) -> None:
        from agent33.agents.events import ToolLoopEvent

        definition = _make_definition(max_tokens=100)
        effort_router = AgentEffortRouter(
            enabled=True,
            heuristic_enabled=False,
            default_effort=AgentEffort.HIGH,
            high_model="stream-model",
            high_token_multiplier=1.5,
        )
        runtime = AgentRuntime(
            definition=definition,
            router=MagicMock(),
            effort_router=effort_router,
            tool_registry=MagicMock(),
            tenant_id="tenant-stream",
            domain="ops",
            session_id="session-stream",
            invocation_mode="iterative_stream",
        )

        async def _fake_run_stream(self, messages, model, temperature=0.7, max_tokens=None):
            del self, messages, model, temperature, max_tokens
            yield ToolLoopEvent(
                event_type="completed",
                iteration=2,
                data={
                    "termination_reason": "natural",
                    "total_tokens": 33,
                    "tool_calls_made": 1,
                    "tools_used": ["shell"],
                    "output": {"result": "ok"},
                },
            )

        with patch("agent33.agents.tool_loop.ToolLoop.run_stream", new=_fake_run_stream):
            events = [
                event
                async for event in runtime.invoke_iterative_stream(
                    {"task": "stream telemetry"},
                    config=ToolLoopConfig(enable_double_confirmation=False),
                )
            ]

        assert [event.event_type for event in events] == ["completed"]
        assert runtime.routing_decision_metadata is not None
        assert runtime.routing_decision_metadata["agent_name"] == "phase30-agent"
        assert runtime.routing_decision_metadata["invocation_mode"] == "iterative_stream"
        assert runtime.routing_decision_metadata["session_id"] == "session-stream"
        assert runtime.routing_decision_metadata["tenant_id"] == "tenant-stream"
        assert runtime.routing_decision_metadata["domain"] == "ops"
        assert runtime.routing_decision_metadata["tokens_used"] == 33
        assert runtime.routing_decision_metadata["iterations"] == 2
        assert runtime.routing_decision_metadata["tool_calls_made"] == 1
        assert runtime.routing_decision_metadata["termination_reason"] == "natural"


class TestEffortRoutingObservabilityAPI:
    def test_invoke_exports_effort_routing_metrics_to_dashboard(self, client) -> None:
        from agent33.agents.registry import AgentRegistry
        from agent33.agents.runtime import AgentResult
        from agent33.api.routes import agents as agents_route
        from agent33.api.routes import dashboard as dashboard_route
        from agent33.main import app

        metrics = MetricsCollector()
        agents_route.set_metrics(metrics)
        dashboard_route.set_metrics(metrics)

        definition = _make_definition()
        definition.name = "phase30-observability-agent"
        app.state.agent_registry = AgentRegistry()
        app.state.agent_registry.register(definition)

        mock_result = AgentResult(
            output={"result": "ok"},
            raw_response='{"result":"ok"}',
            tokens_used=42,
            model="routed-model",
            routing_decision={
                "effort": "high",
                "effort_source": "policy",
                "estimated_token_budget": 1600,
                "estimated_cost": 0.8,
            },
        )
        with patch("agent33.api.routes.agents.AgentRuntime", autospec=True) as mock_runtime_cls:
            mock_instance = MagicMock()

            async def _invoke(*_args, **_kwargs):
                mock_runtime_cls.call_args.kwargs["routing_metrics_emitter"](
                    mock_result.routing_decision
                )
                return mock_result

            mock_instance.invoke = AsyncMock(side_effect=_invoke)
            mock_runtime_cls.return_value = mock_instance

            response = client.post(
                "/v1/agents/phase30-observability-agent/invoke",
                json={"inputs": {"task": "route and export"}},
            )
        assert response.status_code == 200

        metrics_response = client.get("/v1/dashboard/metrics")
        assert metrics_response.status_code == 200
        payload = metrics_response.json()
        assert payload["effort_routing_decisions_total"]["effort=high,source=policy"] == 1
        assert payload["effort_routing_high_effort_total"] == 1
        assert (
            payload["effort_routing_estimated_token_budget(effort=high,source=policy)"]["max"]
            == 1600.0
        )
        assert (
            payload["effort_routing_estimated_cost_usd(effort=high,source=policy)"]["max"] == 0.8
        )

    def test_dashboard_alerts_endpoint_returns_triggered_effort_alerts(self, client) -> None:
        from agent33.api.routes import dashboard as dashboard_route

        metrics = MetricsCollector()
        alert_manager = AlertManager(metrics)
        alert_manager.add_rule(
            name="test_high_cost_effort",
            metric="effort_routing_estimated_cost_usd(effort=high,source=policy)",
            threshold=0.5,
            comparator="gt",
            statistic="max",
        )
        dashboard_route.set_metrics(metrics)
        dashboard_route.set_alert_manager(alert_manager)
        metrics.observe(
            "effort_routing_estimated_cost_usd",
            0.75,
            labels={"effort": "high", "source": "policy"},
        )

        response = client.get("/v1/dashboard/alerts")
        assert response.status_code == 200
        alerts = response.json()
        assert len(alerts) == 1
        assert alerts[0]["rule_name"] == "test_high_cost_effort"

    async def test_workflow_bridge_emits_effort_routing_metrics(self) -> None:
        from agent33.agents.registry import AgentRegistry
        from agent33.api.routes import agents as agents_route
        from agent33.main import _register_agent_runtime_bridge
        from agent33.workflows.actions.invoke_agent import get_agent, register_agent

        metrics = MetricsCollector()
        agents_route.set_metrics(metrics)

        definition = _make_definition()
        definition.name = "phase30-workflow-bridge-agent"
        registry = AgentRegistry()
        registry.register(definition)

        model_router = MagicMock()
        model_router.complete = AsyncMock(return_value=_text_response(model="bridge-model"))
        effort_router = AgentEffortRouter(
            enabled=True,
            default_effort=AgentEffort.HIGH,
            high_model="bridge-model",
            high_token_multiplier=1.0,
            heuristic_enabled=False,
        )
        _register_agent_runtime_bridge(
            model_router,
            register_agent,
            registry=registry,
            effort_router=effort_router,
            routing_metrics_emitter=agents_route._record_effort_routing_metrics,
        )
        bridge_handler = get_agent("__default__")
        result = await bridge_handler(
            {"agent_name": "phase30-workflow-bridge-agent", "task": "route me"}
        )
        assert "result" in result
        call_kwargs = model_router.complete.call_args.kwargs
        assert call_kwargs["model"] == "bridge-model"

        summary = metrics.get_summary()
        assert summary["effort_routing_decisions_total"]["effort=high,source=default"] == 1


class TestEffortAlertManager:
    def test_alert_manager_supports_statistic_thresholds(self) -> None:
        metrics = MetricsCollector()
        alerts = AlertManager(metrics)
        alerts.add_rule(
            name="max_cost",
            metric="effort_routing_estimated_cost_usd",
            threshold=1.0,
            comparator="gt",
            statistic="max",
        )
        metrics.observe("effort_routing_estimated_cost_usd", 1.25)

        triggered = alerts.check_all()
        assert len(triggered) == 1
        assert triggered[0].rule_name == "max_cost"


class TestEffortAPIRouting:
    """API-level integration tests that verify effort routing through the invoke endpoint."""

    def _setup_agent(self, name: str = "effort-api-agent") -> None:
        from agent33.agents.registry import AgentRegistry
        from agent33.main import app

        definition = _make_definition()
        definition.name = name
        app.state.agent_registry = AgentRegistry()
        app.state.agent_registry.register(definition)

    def test_invoke_with_explicit_effort_routes_through_effort_router(self, client) -> None:
        """POST /v1/agents/{id}/invoke with effort=high routes via effort router."""
        self._setup_agent("effort-explicit-agent")
        mock_result = AgentResult(
            output={"result": "routed"},
            raw_response='{"result":"routed"}',
            tokens_used=30,
            model="high-model",
            routing_decision={
                "effort": "high",
                "effort_source": "request",
                "model": "high-model",
                "routed_max_tokens": 150,
                "estimated_token_budget": 150,
                "estimated_cost": 0.0375,
            },
        )
        with patch("agent33.api.routes.agents.AgentRuntime", autospec=True) as mock_cls:
            mock_instance = MagicMock()
            mock_instance.invoke = AsyncMock(return_value=mock_result)
            mock_cls.return_value = mock_instance

            response = client.post(
                "/v1/agents/effort-explicit-agent/invoke",
                json={"inputs": {"task": "go"}, "effort": "high"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["routing"]["effort"] == "high"
        assert data["routing"]["effort_source"] == "request"

        # Verify the runtime was constructed with the effort param from the request
        construct_kwargs = mock_cls.call_args.kwargs
        assert construct_kwargs["effort"] == AgentEffort.HIGH

    def test_invoke_with_low_effort_routes_correctly(self, client) -> None:
        """POST /v1/agents/{id}/invoke with effort=low gets low routing."""
        self._setup_agent("effort-low-agent")
        mock_result = AgentResult(
            output={"result": "quick"},
            raw_response='{"result":"quick"}',
            tokens_used=10,
            model="low-model",
            routing_decision={
                "effort": "low",
                "effort_source": "request",
                "model": "low-model",
                "routed_max_tokens": 75,
                "estimated_token_budget": 75,
                "estimated_cost": None,
            },
        )
        with patch("agent33.api.routes.agents.AgentRuntime", autospec=True) as mock_cls:
            mock_instance = MagicMock()
            mock_instance.invoke = AsyncMock(return_value=mock_result)
            mock_cls.return_value = mock_instance

            response = client.post(
                "/v1/agents/effort-low-agent/invoke",
                json={"inputs": {"task": "tiny"}, "effort": "low"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["routing"]["effort"] == "low"
        assert data["routing"]["effort_source"] == "request"
        construct_kwargs = mock_cls.call_args.kwargs
        assert construct_kwargs["effort"] == AgentEffort.LOW

    def test_invoke_without_effort_falls_through_to_heuristic(self, client) -> None:
        """POST /v1/agents/{id}/invoke without effort param uses heuristic routing."""
        self._setup_agent("effort-heuristic-agent")
        mock_result = AgentResult(
            output={"result": "classified"},
            raw_response='{"result":"classified"}',
            tokens_used=20,
            model="medium-model",
            routing_decision={
                "effort": "medium",
                "effort_source": "heuristic",
                "model": "medium-model",
                "routed_max_tokens": 100,
                "estimated_token_budget": 100,
                "estimated_cost": None,
                "heuristic_score": 2,
                "heuristic_reasons": ["medium_payload", "complex_task_keywords"],
            },
        )
        with patch("agent33.api.routes.agents.AgentRuntime", autospec=True) as mock_cls:
            mock_instance = MagicMock()
            mock_instance.invoke = AsyncMock(return_value=mock_result)
            mock_cls.return_value = mock_instance

            response = client.post(
                "/v1/agents/effort-heuristic-agent/invoke",
                json={"inputs": {"task": "analyze the architecture"}},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["routing"]["effort_source"] == "heuristic"
        # Runtime constructed without explicit effort
        construct_kwargs = mock_cls.call_args.kwargs
        assert construct_kwargs["effort"] is None

    def test_invoke_tenant_policy_fixture_routes_via_policy(self, client) -> None:
        """Tenant-level effort policy overrides heuristic at the API layer."""
        self._setup_agent("effort-tenant-policy-agent")
        mock_result = AgentResult(
            output={"result": "policy-driven"},
            raw_response='{"result":"policy-driven"}',
            tokens_used=25,
            model="policy-model",
            routing_decision={
                "effort": "high",
                "effort_source": "policy",
                "policy_key": "tenant-alpha",
                "model": "policy-model",
                "routed_max_tokens": 200,
                "estimated_token_budget": 200,
                "estimated_cost": 0.05,
            },
        )
        with patch("agent33.api.routes.agents.AgentRuntime", autospec=True) as mock_cls:
            mock_instance = MagicMock()
            mock_instance.invoke = AsyncMock(return_value=mock_result)
            mock_cls.return_value = mock_instance

            response = client.post(
                "/v1/agents/effort-tenant-policy-agent/invoke",
                json={"inputs": {"task": "run with policy"}},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["routing"]["effort_source"] == "policy"
        assert data["routing"]["policy_key"] == "tenant-alpha"

    def test_invoke_domain_policy_fixture_routes_via_domain(self, client) -> None:
        """Domain-level effort policy surfaces in response routing metadata."""
        self._setup_agent("effort-domain-policy-agent")
        mock_result = AgentResult(
            output={"result": "domain-routed"},
            raw_response='{"result":"domain-routed"}',
            tokens_used=30,
            model="domain-model",
            routing_decision={
                "effort": "high",
                "effort_source": "policy",
                "policy_key": "security",
                "model": "domain-model",
                "routed_max_tokens": 200,
                "estimated_token_budget": 200,
                "estimated_cost": 0.05,
            },
        )
        with patch("agent33.api.routes.agents.AgentRuntime", autospec=True) as mock_cls:
            mock_instance = MagicMock()
            mock_instance.invoke = AsyncMock(return_value=mock_result)
            mock_cls.return_value = mock_instance

            response = client.post(
                "/v1/agents/effort-domain-policy-agent/invoke",
                json={
                    "inputs": {"task": "security review"},
                    "domain": "security",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["routing"]["effort_source"] == "policy"
        assert data["routing"]["policy_key"] == "security"
        # Domain is forwarded to the runtime constructor
        construct_kwargs = mock_cls.call_args.kwargs
        assert construct_kwargs["domain"] == "security"

    def test_invoke_response_contains_calibration_metadata(self, client) -> None:
        """Calibration metadata (heuristic thresholds and score) is emitted in response."""
        self._setup_agent("effort-calibration-agent")
        mock_result = AgentResult(
            output={"result": "calibrated"},
            raw_response='{"result":"calibrated"}',
            tokens_used=15,
            model="heuristic-model",
            routing_decision={
                "effort": "high",
                "effort_source": "heuristic",
                "model": "heuristic-model",
                "routed_max_tokens": 150,
                "estimated_token_budget": 150,
                "estimated_cost": None,
                "heuristic_score": 5,
                "heuristic_low_threshold": 1,
                "heuristic_high_threshold": 4,
                "heuristic_confidence": 0.8,
                "heuristic_reasons": [
                    "iterative_mode",
                    "large_payload",
                    "complex_task_keywords",
                ],
            },
        )
        with patch("agent33.api.routes.agents.AgentRuntime", autospec=True) as mock_cls:
            mock_instance = MagicMock()
            mock_instance.invoke = AsyncMock(return_value=mock_result)
            mock_cls.return_value = mock_instance

            response = client.post(
                "/v1/agents/effort-calibration-agent/invoke",
                json={"inputs": {"task": "calibrate"}},
            )

        assert response.status_code == 200
        routing = response.json()["routing"]
        assert "heuristic_score" in routing
        assert "heuristic_low_threshold" in routing
        assert "heuristic_high_threshold" in routing
        assert "heuristic_confidence" in routing
        assert "heuristic_reasons" in routing
        assert routing["heuristic_score"] == 5
        assert routing["heuristic_low_threshold"] == 1
        assert routing["heuristic_high_threshold"] == 4
        assert routing["heuristic_confidence"] == 0.8
        assert isinstance(routing["heuristic_reasons"], list)
        assert len(routing["heuristic_reasons"]) >= 1

    def test_invoke_with_medium_effort_populates_routing_in_response(self, client) -> None:
        """Routing dict is always present when effort routing is active."""
        self._setup_agent("effort-medium-agent")
        mock_result = AgentResult(
            output={"result": "ok"},
            raw_response='{"result":"ok"}',
            tokens_used=20,
            model="medium-model",
            routing_decision={
                "effort": "medium",
                "effort_source": "request",
                "model": "medium-model",
                "routed_max_tokens": 100,
                "estimated_token_budget": 100,
                "estimated_cost": None,
            },
        )
        with patch("agent33.api.routes.agents.AgentRuntime", autospec=True) as mock_cls:
            mock_instance = MagicMock()
            mock_instance.invoke = AsyncMock(return_value=mock_result)
            mock_cls.return_value = mock_instance

            response = client.post(
                "/v1/agents/effort-medium-agent/invoke",
                json={"inputs": {"task": "something"}, "effort": "medium"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["routing"] is not None
        assert data["routing"]["effort"] == "medium"
        assert data["routing"]["effort_source"] == "request"
        assert "estimated_token_budget" in data["routing"]

    def test_iterative_stream_passes_context_and_exports_metrics(self, client) -> None:
        from agent33.agents.events import ToolLoopEvent
        from agent33.agents.registry import AgentRegistry
        from agent33.api.routes import agents as agents_route
        from agent33.main import app

        metrics = MetricsCollector()
        agents_route.set_metrics(metrics)

        definition = _make_definition()
        definition.name = "effort-stream-agent"
        app.state.agent_registry = AgentRegistry()
        app.state.agent_registry.register(definition)
        app.state.model_router = MagicMock()
        app.state.tool_registry = MagicMock()

        async def _stream(*_args, **_kwargs):
            yield ToolLoopEvent(
                event_type="completed",
                iteration=1,
                data={
                    "termination_reason": "natural",
                    "total_tokens": 12,
                    "tool_calls_made": 0,
                    "tools_used": [],
                    "output": {"result": "ok"},
                },
            )

        with patch("agent33.api.routes.agents.AgentRuntime", autospec=True) as mock_cls:
            mock_instance = MagicMock()
            mock_instance.invoke_iterative_stream = _stream
            mock_instance.routing_decision_metadata = {
                "effort": "high",
                "effort_source": "policy",
                "estimated_token_budget": 200,
                "estimated_cost": 0.5,
                "agent_name": "effort-stream-agent",
                "invocation_mode": "iterative_stream",
                "session_id": "session-123",
            }
            mock_cls.return_value = mock_instance

            response = client.post(
                "/v1/agents/effort-stream-agent/invoke-iterative/stream",
                json={"inputs": {"task": "stream it"}},
                headers={
                    "x-agent-session-id": "session-123",
                    "x-agent-domain": "security",
                },
            )

        assert response.status_code == 200
        construct_kwargs = mock_cls.call_args.kwargs
        assert construct_kwargs["invocation_mode"] == "iterative_stream"
        assert construct_kwargs["session_id"] == "session-123"
        assert construct_kwargs["domain"] == "security"
        assert construct_kwargs["routing_metrics_emitter"] is not None

        summary = metrics.get_summary()
        assert summary["effort_routing_decisions_total"]["effort=high,source=policy"] == 1


class TestEffortConfigValidation:
    def test_score_threshold_order_is_validated(self) -> None:
        with pytest.raises(
            ValidationError,
            match="agent_effort_heuristic_high_score_threshold must be greater than",
        ):
            Settings(
                agent_effort_heuristic_low_score_threshold=2,
                agent_effort_heuristic_high_score_threshold=2,
            )

    def test_payload_threshold_order_is_validated(self) -> None:
        with pytest.raises(
            ValidationError,
            match="agent_effort_heuristic_large_payload_chars must be greater than",
        ):
            Settings(
                agent_effort_heuristic_medium_payload_chars=1000,
                agent_effort_heuristic_large_payload_chars=1000,
            )
