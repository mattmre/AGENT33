"""Tests for the 5-phase reasoning protocol."""

from __future__ import annotations

import dataclasses
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent33.agents.isc import GuardrailResult, ISCCriterion, ISCManager
from agent33.agents.reasoning import (
    ExecuteArtifact,
    LearnArtifact,
    NextAction,
    ObserveArtifact,
    PlanArtifact,
    ReasoningConfig,
    ReasoningPhase,
    ReasoningProtocol,
    ReasoningResult,
    ReasoningState,
    ReasoningStep,
    VerifyArtifact,
    _VALID_ACTIONS,
    _next_phase,
)
from agent33.agents.tool_loop import ToolLoopResult
from agent33.llm.base import LLMResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_llm_response(content: str = "test response") -> LLMResponse:
    return LLMResponse(
        content=content,
        model="test-model",
        prompt_tokens=10,
        completion_tokens=20,
    )


def _mock_tool_loop_result(output: str = "tool output") -> ToolLoopResult:
    return ToolLoopResult(
        output={"response": output},
        raw_response=output,
        tokens_used=100,
        model="test-model",
        iterations=3,
        tool_calls_made=5,
        tools_used=["shell", "file_read"],
        termination_reason="completed",
    )


def _make_router(content: str = "test response") -> AsyncMock:
    router = AsyncMock()
    router.complete = AsyncMock(return_value=_mock_llm_response(content))
    return router


def _make_tool_loop(output: str = "tool output") -> AsyncMock:
    loop = AsyncMock()
    loop.run = AsyncMock(return_value=_mock_tool_loop_result(output))
    return loop


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestNextAction:
    def test_values(self) -> None:
        assert NextAction.CONTINUE == "continue"
        assert NextAction.VALIDATE == "validate"
        assert NextAction.FINAL_ANSWER == "final_answer"
        assert NextAction.RESET == "reset"

    def test_str_inheritance(self) -> None:
        assert isinstance(NextAction.CONTINUE, str)


class TestReasoningPhase:
    def test_values(self) -> None:
        assert ReasoningPhase.OBSERVE == "observe"
        assert ReasoningPhase.PLAN == "plan"
        assert ReasoningPhase.EXECUTE == "execute"
        assert ReasoningPhase.VERIFY == "verify"
        assert ReasoningPhase.LEARN == "learn"

    def test_str_inheritance(self) -> None:
        assert isinstance(ReasoningPhase.OBSERVE, str)


# ---------------------------------------------------------------------------
# Config / State / Result
# ---------------------------------------------------------------------------


class TestReasoningConfig:
    def test_defaults(self) -> None:
        cfg = ReasoningConfig()
        assert cfg.max_steps == 25
        assert cfg.quality_gate_threshold == 0.7
        assert cfg.enable_anti_criteria is True
        assert len(cfg.phases_enabled) == 5

    def test_frozen(self) -> None:
        cfg = ReasoningConfig()
        with pytest.raises(dataclasses.FrozenInstanceError):
            cfg.max_steps = 10  # type: ignore[misc]

    def test_custom_phases(self) -> None:
        cfg = ReasoningConfig(
            phases_enabled=(ReasoningPhase.OBSERVE, ReasoningPhase.EXECUTE)
        )
        assert len(cfg.phases_enabled) == 2


class TestReasoningState:
    def test_defaults(self) -> None:
        s = ReasoningState()
        assert s.current_phase == ReasoningPhase.OBSERVE
        assert s.steps == []
        assert s.current_step_index == 0
        assert s.validated is False
        assert s.reset_count == 0

    def test_mutable(self) -> None:
        s = ReasoningState()
        s.current_phase = ReasoningPhase.PLAN
        s.validated = True
        assert s.current_phase == ReasoningPhase.PLAN
        assert s.validated is True


class TestReasoningResult:
    def test_frozen(self) -> None:
        r = ReasoningResult(
            steps=[], final_output="", phase_artifacts={},
            termination_reason="completed", total_steps=0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.total_steps = 5  # type: ignore[misc]

    def test_construction(self) -> None:
        r = ReasoningResult(
            steps=[ReasoningStep()],
            final_output="done",
            phase_artifacts={"a": 1},
            termination_reason="completed",
            total_steps=1,
        )
        assert r.final_output == "done"
        assert len(r.steps) == 1
        assert r.total_steps == 1


# ---------------------------------------------------------------------------
# ReasoningStep
# ---------------------------------------------------------------------------


class TestReasoningStep:
    def test_defaults(self) -> None:
        step = ReasoningStep()
        assert step.step_id.startswith("rs-")
        assert step.confidence == 0.5
        assert step.phase == "observe"

    def test_auto_id_unique(self) -> None:
        s1 = ReasoningStep()
        s2 = ReasoningStep()
        assert s1.step_id != s2.step_id


# ---------------------------------------------------------------------------
# Phase artifacts
# ---------------------------------------------------------------------------


class TestArtifacts:
    def test_observe_frozen(self) -> None:
        a = ObserveArtifact(observations=["x"], constraints=["y"], anti_criteria=[])
        with pytest.raises(dataclasses.FrozenInstanceError):
            a.observations = []  # type: ignore[misc]

    def test_plan_frozen(self) -> None:
        a = PlanArtifact(plan_steps=["step1"], approach="direct", estimated_steps=3)
        with pytest.raises(dataclasses.FrozenInstanceError):
            a.approach = "new"  # type: ignore[misc]

    def test_execute_frozen(self) -> None:
        a = ExecuteArtifact(tool_loop_result=None, raw_output="out")
        with pytest.raises(dataclasses.FrozenInstanceError):
            a.raw_output = "new"  # type: ignore[misc]

    def test_verify_frozen(self) -> None:
        a = VerifyArtifact(isc_results=[], all_passed=True, failed_criteria=[])
        with pytest.raises(dataclasses.FrozenInstanceError):
            a.all_passed = False  # type: ignore[misc]

    def test_learn_frozen(self) -> None:
        a = LearnArtifact(lessons=["l1"], recommendations=[], confidence_delta=0.1)
        with pytest.raises(dataclasses.FrozenInstanceError):
            a.confidence_delta = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FSM transition rules
# ---------------------------------------------------------------------------


class TestFSM:
    def test_valid_actions_observe(self) -> None:
        assert NextAction.CONTINUE in _VALID_ACTIONS[ReasoningPhase.OBSERVE]
        assert NextAction.RESET in _VALID_ACTIONS[ReasoningPhase.OBSERVE]
        assert NextAction.FINAL_ANSWER not in _VALID_ACTIONS[ReasoningPhase.OBSERVE]

    def test_valid_actions_plan(self) -> None:
        assert NextAction.CONTINUE in _VALID_ACTIONS[ReasoningPhase.PLAN]
        assert NextAction.RESET in _VALID_ACTIONS[ReasoningPhase.PLAN]

    def test_valid_actions_execute(self) -> None:
        assert NextAction.CONTINUE in _VALID_ACTIONS[ReasoningPhase.EXECUTE]
        assert NextAction.VALIDATE in _VALID_ACTIONS[ReasoningPhase.EXECUTE]
        assert NextAction.RESET in _VALID_ACTIONS[ReasoningPhase.EXECUTE]

    def test_valid_actions_verify(self) -> None:
        assert NextAction.VALIDATE in _VALID_ACTIONS[ReasoningPhase.VERIFY]
        assert NextAction.RESET in _VALID_ACTIONS[ReasoningPhase.VERIFY]
        assert NextAction.CONTINUE in _VALID_ACTIONS[ReasoningPhase.VERIFY]

    def test_valid_actions_learn(self) -> None:
        assert NextAction.FINAL_ANSWER in _VALID_ACTIONS[ReasoningPhase.LEARN]
        assert NextAction.RESET in _VALID_ACTIONS[ReasoningPhase.LEARN]

    def test_final_answer_only_from_learn(self) -> None:
        for phase in ReasoningPhase:
            if phase == ReasoningPhase.LEARN:
                assert NextAction.FINAL_ANSWER in _VALID_ACTIONS[phase]
            else:
                assert NextAction.FINAL_ANSWER not in _VALID_ACTIONS[phase]

    def test_reset_from_all_phases(self) -> None:
        for phase in ReasoningPhase:
            assert NextAction.RESET in _VALID_ACTIONS[phase]

    def test_next_phase_sequence(self) -> None:
        assert _next_phase(ReasoningPhase.OBSERVE) == ReasoningPhase.PLAN
        assert _next_phase(ReasoningPhase.PLAN) == ReasoningPhase.EXECUTE
        assert _next_phase(ReasoningPhase.EXECUTE) == ReasoningPhase.VERIFY
        assert _next_phase(ReasoningPhase.VERIFY) == ReasoningPhase.LEARN
        assert _next_phase(ReasoningPhase.LEARN) is None


# ---------------------------------------------------------------------------
# ReasoningProtocol
# ---------------------------------------------------------------------------


class TestReasoningProtocol:
    @pytest.mark.asyncio
    async def test_full_lifecycle(self) -> None:
        """Full 5-phase cycle: OBSERVE → PLAN → EXECUTE → VERIFY → LEARN."""
        router = _make_router("phase output")
        tool_loop = _make_tool_loop("executed result")

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=10),
        )

        result = await protocol.run(
            task_input="test task",
            tool_loop=tool_loop,
            model="test-model",
            router=router,
            system_prompt="system",
        )

        assert result.termination_reason == "completed"
        assert result.total_steps == 5
        assert result.final_output == "executed result"
        phases = [s.phase for s in result.steps]
        assert phases == ["observe", "plan", "execute", "verify", "learn"]

    @pytest.mark.asyncio
    async def test_validate_gate_blocks_without_verify(self) -> None:
        """FINAL_ANSWER blocked when state.validated is False."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        # Add ISC criteria that will fail → validated stays False
        isc = ISCManager()
        isc.add(ISCCriterion(
            name="must-fail", description="d",
            check_fn=lambda ctx: False,
        ))

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=50),
            isc_manager=isc,
        )

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        # Failing ISC triggers resets until max_resets exceeded
        assert result.termination_reason == "max_resets_exceeded"

    @pytest.mark.asyncio
    async def test_validate_gate_allows_after_verify(self) -> None:
        """FINAL_ANSWER succeeds when all ISC criteria pass."""
        router = _make_router()
        tool_loop = _make_tool_loop("final output")

        isc = ISCManager()
        isc.add(ISCCriterion(
            name="always-pass", description="d",
            check_fn=lambda ctx: True,
        ))

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=10),
            isc_manager=isc,
        )

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        assert result.termination_reason == "completed"
        assert result.final_output == "final output"

    @pytest.mark.asyncio
    async def test_reset_returns_to_observe(self) -> None:
        """RESET transitions back to OBSERVE phase."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        # Criteria that fail → triggers resets
        isc = ISCManager()
        isc.add(ISCCriterion(
            name="fail", description="d",
            check_fn=lambda ctx: False,
        ))

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=30),
            isc_manager=isc,
        )

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        # Should see multiple OBSERVE phases (from resets)
        observe_count = sum(1 for s in result.steps if s.phase == "observe")
        assert observe_count > 1

    @pytest.mark.asyncio
    async def test_max_resets_terminates(self) -> None:
        """Protocol terminates after exceeding max resets."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        isc = ISCManager()
        isc.add(ISCCriterion(
            name="always-fail", description="d",
            check_fn=lambda ctx: False,
        ))

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=50),
            isc_manager=isc,
        )

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        assert result.termination_reason == "max_resets_exceeded"

    @pytest.mark.asyncio
    async def test_max_steps_terminates(self) -> None:
        """Protocol terminates after hitting max_steps."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=2),
        )

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        assert result.termination_reason == "max_steps_exceeded"
        assert result.total_steps == 2

    @pytest.mark.asyncio
    async def test_quality_gate_triggers_reset(self) -> None:
        """Low confidence triggers a reset."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=20, quality_gate_threshold=0.99),
        )

        # With threshold 0.99, the default 0.8 confidence will trigger resets
        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        assert result.termination_reason == "max_resets_exceeded"

    @pytest.mark.asyncio
    async def test_invalid_action_defaults_to_continue(self) -> None:
        """Invalid action for a phase defaults to CONTINUE."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=10),
        )

        # Patch _phase_observe to return FINAL_ANSWER (invalid for OBSERVE)
        original_observe = protocol._phase_observe

        async def bad_observe(*args: Any, **kwargs: Any) -> tuple:
            step, _ = await original_observe(*args, **kwargs)
            # Force high confidence to avoid quality gate reset
            step = step.model_copy(update={"confidence": 0.99})
            return step, NextAction.FINAL_ANSWER

        protocol._phase_observe = bad_observe  # type: ignore[assignment]

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        # Should still complete (FINAL_ANSWER was treated as invalid → CONTINUE)
        assert result.termination_reason == "completed"

    @pytest.mark.asyncio
    async def test_disabled_phases_skipped(self) -> None:
        """Only enabled phases are executed."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        # Only OBSERVE and EXECUTE enabled
        protocol = ReasoningProtocol(
            config=ReasoningConfig(
                max_steps=10,
                phases_enabled=(
                    ReasoningPhase.OBSERVE,
                    ReasoningPhase.EXECUTE,
                    ReasoningPhase.VERIFY,
                    ReasoningPhase.LEARN,
                ),
            ),
        )

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        phases = [s.phase for s in result.steps]
        assert "plan" not in phases

    @pytest.mark.asyncio
    async def test_isc_integration_all_pass(self) -> None:
        """ISC criteria all pass → verification succeeds."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        isc = ISCManager()
        isc.add(ISCCriterion(name="c1", description="d", check_fn=lambda ctx: True))
        isc.add(ISCCriterion(name="c2", description="d", check_fn=lambda ctx: True))

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=10),
            isc_manager=isc,
        )

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        assert result.termination_reason == "completed"
        verify = result.phase_artifacts.get("verify")
        assert isinstance(verify, VerifyArtifact)
        assert verify.all_passed is True

    @pytest.mark.asyncio
    async def test_isc_integration_some_fail(self) -> None:
        """ISC criteria failing → RESET cascade."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        isc = ISCManager()
        isc.add(ISCCriterion(name="pass", description="d", check_fn=lambda ctx: True))
        isc.add(ISCCriterion(name="fail", description="d", check_fn=lambda ctx: False))

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=30),
            isc_manager=isc,
        )

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        assert result.termination_reason == "max_resets_exceeded"

    @pytest.mark.asyncio
    async def test_no_isc_manager_still_works(self) -> None:
        """Protocol works without ISC manager (auto-pass verification)."""
        router = _make_router()
        tool_loop = _make_tool_loop("output")

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=10),
        )

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        assert result.termination_reason == "completed"
        assert result.final_output == "output"

    @pytest.mark.asyncio
    async def test_execute_calls_tool_loop(self) -> None:
        """EXECUTE phase calls tool_loop.run()."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=10),
        )

        await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        tool_loop.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_observe_plan_learn_call_router(self) -> None:
        """OBSERVE, PLAN, and LEARN phases call router.complete()."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=10),
        )

        await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        # OBSERVE + PLAN + LEARN = 3 router.complete() calls
        assert router.complete.call_count == 3

    @pytest.mark.asyncio
    async def test_anti_criteria_in_verify(self) -> None:
        """Anti-criteria evaluated during VERIFY phase."""
        router = _make_router()
        tool_loop = _make_tool_loop()

        isc = ISCManager()
        # Anti-criterion: check_fn returns False → inverted → success=True
        isc.add(ISCCriterion(
            name="no-pii", description="d",
            check_fn=lambda ctx: False,
            is_anti=True,
        ))

        protocol = ReasoningProtocol(
            config=ReasoningConfig(max_steps=10, enable_anti_criteria=True),
            isc_manager=isc,
        )

        result = await protocol.run(
            task_input="test",
            tool_loop=tool_loop,
            model="m",
            router=router,
        )

        assert result.termination_reason == "completed"
        verify = result.phase_artifacts.get("verify")
        assert isinstance(verify, VerifyArtifact)
        assert verify.all_passed is True
