"""Phase 30 MVP tests for adaptive effort routing."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from agent33.agents.definition import (
    AgentConstraints,
    AgentDefinition,
    AgentParameter,
    AgentRole,
)
from agent33.agents.effort import AgentEffort, AgentEffortRouter, EffortSelectionSource
from agent33.agents.runtime import AgentRuntime
from agent33.agents.tool_loop import ToolLoopConfig
from agent33.llm.base import LLMResponse


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


class TestAgentRuntimeEffortRouting:
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
