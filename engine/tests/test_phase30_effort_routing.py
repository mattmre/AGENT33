"""Phase 30 MVP tests for adaptive effort routing."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from agent33.agents.definition import (
    AgentConstraints,
    AgentDefinition,
    AgentParameter,
    AgentRole,
)
from agent33.agents.effort import AgentEffort, AgentEffortRouter
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
        await runtime.invoke({"task": "route me"})

        call_kwargs = model_router.complete.call_args.kwargs
        assert call_kwargs["model"] == "routed-model"
        assert call_kwargs["max_tokens"] == 200

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
        await runtime.invoke_iterative(
            {"task": "iterative route"},
            config=ToolLoopConfig(enable_double_confirmation=False),
        )

        call_kwargs = model_router.complete.call_args.kwargs
        assert call_kwargs["model"] == "iter-model"
        assert call_kwargs["max_tokens"] == 180
