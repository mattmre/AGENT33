"""Workflow executor that runs steps according to the DAG schedule."""

from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

from agent33.workflows.actions import (
    conditional,
    execute_code,
    http_request,
    invoke_agent,
    parallel_group,
    route,
    run_command,
    sub_workflow,
    transform,
    validate,
    wait,
)
from agent33.workflows.dag import DAGBuilder
from agent33.workflows.definition import (
    ExecutionMode,
    StepAction,
    WorkflowDefinition,
    WorkflowStep,
)
from agent33.workflows.expressions import ExpressionEvaluator

logger = structlog.get_logger()


class WorkflowStatus(str, Enum):
    """Terminal status of a workflow execution."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class StepResult(BaseModel):
    """Result of executing a single step."""

    step_id: str
    status: str
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0


class WorkflowResult(BaseModel):
    """Result of a complete workflow execution."""

    outputs: dict[str, Any] = Field(default_factory=dict)
    steps_executed: list[str] = Field(default_factory=list)
    step_results: list[StepResult] = Field(default_factory=list)
    duration_ms: float = 0.0
    status: WorkflowStatus = WorkflowStatus.SUCCESS


class WorkflowExecutor:
    """Executes a workflow definition by building a DAG and running steps.

    Supports sequential, parallel, and dependency-aware execution modes.
    Handles conditionals, retries, timeouts, and state passing between steps.
    """

    def __init__(self, definition: WorkflowDefinition) -> None:
        self._definition = definition
        self._evaluator = ExpressionEvaluator()
        self._steps: dict[str, WorkflowStep] = {s.id: s for s in definition.steps}

    async def execute(self, inputs: dict[str, Any] | None = None) -> WorkflowResult:
        """Execute the workflow with the given inputs.

        Args:
            inputs: Initial input data for the workflow.

        Returns:
            A WorkflowResult with outputs, executed steps, duration, and status.
        """
        start = time.monotonic()
        state: dict[str, Any] = dict(inputs or {})
        step_results: list[StepResult] = []
        steps_executed: list[str] = []
        execution = self._definition.execution
        failed = False

        try:
            if execution.mode == ExecutionMode.SEQUENTIAL:
                for step in self._definition.steps:
                    result = await self._execute_step(step, state, execution.dry_run)
                    step_results.append(result)
                    steps_executed.append(step.id)
                    state[step.id] = result.outputs

                    if result.status == "failed":
                        failed = True
                        if execution.fail_fast:
                            break
                        if not execution.continue_on_error:
                            break
            else:
                # dependency-aware or parallel: use DAG
                dag = DAGBuilder(self._definition.steps).build()
                groups = dag.parallel_groups()
                parallel_limit = execution.parallel_limit

                for group in groups:
                    if len(group) == 1 or execution.mode == ExecutionMode.SEQUENTIAL:
                        for sid in group:
                            result = await self._execute_step(
                                self._steps[sid], state, execution.dry_run
                            )
                            step_results.append(result)
                            steps_executed.append(sid)
                            state[sid] = result.outputs
                            if result.status == "failed":
                                failed = True
                                if execution.fail_fast:
                                    break
                        if failed and execution.fail_fast:
                            break
                    else:
                        # Run group in parallel with concurrency limit
                        _sem = asyncio.Semaphore(parallel_limit)

                        async def _run_limited(
                            sid: str,
                            semaphore: asyncio.Semaphore = _sem,
                        ) -> StepResult:
                            async with semaphore:
                                return await self._execute_step(
                                    self._steps[sid], state, execution.dry_run
                                )

                        tasks = [_run_limited(sid) for sid in group]
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        for sid, res in zip(group, results, strict=True):
                            if isinstance(res, BaseException):
                                sr = StepResult(
                                    step_id=sid,
                                    status="failed",
                                    error=str(res),
                                )
                                step_results.append(sr)
                                state[sid] = {}
                                failed = True
                            else:
                                step_results.append(res)
                                state[sid] = res.outputs
                                if res.status == "failed":
                                    failed = True
                            steps_executed.append(sid)

                        if failed and execution.fail_fast:
                            break

        except Exception as exc:
            logger.error("workflow_execution_error", error=str(exc))
            failed = True

        elapsed_ms = (time.monotonic() - start) * 1000

        # Determine overall status
        if failed:
            any_success = any(r.status == "success" for r in step_results)
            status = WorkflowStatus.PARTIAL if any_success else WorkflowStatus.FAILED
        else:
            status = WorkflowStatus.SUCCESS

        # Collect final outputs from the last executed steps
        final_outputs: dict[str, Any] = {}
        for sr in step_results:
            if sr.status == "success":
                final_outputs.update(sr.outputs)

        return WorkflowResult(
            outputs=final_outputs,
            steps_executed=steps_executed,
            step_results=step_results,
            duration_ms=round(elapsed_ms, 2),
            status=status,
        )

    async def _execute_step(
        self,
        step: WorkflowStep,
        state: dict[str, Any],
        dry_run: bool,
    ) -> StepResult:
        """Execute a single step with retry and timeout handling."""
        start = time.monotonic()

        # Evaluate condition
        if step.condition:
            try:
                should_run = self._evaluator.evaluate_condition(step.condition, state)
                if not should_run:
                    return StepResult(
                        step_id=step.id,
                        status="skipped",
                        outputs={"skipped": True, "reason": "condition_false"},
                    )
            except Exception as exc:
                return StepResult(
                    step_id=step.id,
                    status="failed",
                    error=f"Condition evaluation error: {exc}",
                )

        # Resolve inputs
        resolved_inputs = self._evaluator.resolve_inputs(step.inputs, state)

        max_attempts = step.retry.max_attempts
        delay = step.retry.delay_seconds
        last_error: str | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                coro = self._dispatch_action(step, resolved_inputs, state, dry_run)

                if step.timeout_seconds:
                    outputs = await asyncio.wait_for(coro, timeout=float(step.timeout_seconds))
                else:
                    outputs = await coro

                elapsed = (time.monotonic() - start) * 1000
                return StepResult(
                    step_id=step.id,
                    status="success",
                    outputs=outputs,
                    duration_ms=round(elapsed, 2),
                )

            except TimeoutError:
                last_error = f"Step timed out after {step.timeout_seconds}s"
                logger.warning("step_timeout", step_id=step.id, attempt=attempt)
            except Exception as exc:
                last_error = str(exc)
                logger.warning("step_error", step_id=step.id, attempt=attempt, error=last_error)

            if attempt < max_attempts:
                await asyncio.sleep(delay)

        elapsed = (time.monotonic() - start) * 1000
        return StepResult(
            step_id=step.id,
            status="failed",
            error=last_error,
            duration_ms=round(elapsed, 2),
        )

    async def _dispatch_action(
        self,
        step: WorkflowStep,
        resolved_inputs: dict[str, Any],
        state: dict[str, Any],
        dry_run: bool,
    ) -> dict[str, Any]:
        """Dispatch execution to the appropriate action handler."""
        action = step.action

        if action == StepAction.INVOKE_AGENT:
            return await invoke_agent.execute(
                agent=step.agent,
                inputs=resolved_inputs,
                dry_run=dry_run,
            )

        if action == StepAction.RUN_COMMAND:
            return await run_command.execute(
                command=step.command,
                inputs=resolved_inputs,
                timeout_seconds=step.timeout_seconds,
                dry_run=dry_run,
            )

        if action == StepAction.VALIDATE:
            return await validate.execute(
                inputs=resolved_inputs,
                dry_run=dry_run,
            )

        if action == StepAction.TRANSFORM:
            return await transform.execute(
                inputs=resolved_inputs,
                dry_run=dry_run,
            )

        if action == StepAction.CONDITIONAL:
            result = await conditional.execute(
                condition=step.condition,
                inputs={**state, **resolved_inputs},
                dry_run=dry_run,
            )
            # Execute the appropriate branch sub-steps
            branch = result.get("branch", "then")
            branch_steps = step.then_steps if branch == "then" else step.else_steps
            branch_outputs: dict[str, Any] = dict(result)
            for sub_step in branch_steps:
                sub_result = await self._execute_step(sub_step, state, dry_run)
                state[sub_step.id] = sub_result.outputs
                branch_outputs[sub_step.id] = sub_result.outputs
            return branch_outputs

        if action == StepAction.PARALLEL_GROUP:
            sub_ids = [s.id for s in step.steps]
            # Register sub-steps temporarily
            for s in step.steps:
                self._steps[s.id] = s

            async def _run_sub(sid: str) -> dict[str, Any]:
                sub_step = self._steps[sid]
                r = await self._execute_step(sub_step, state, dry_run)
                state[sid] = r.outputs
                return r.outputs

            return await parallel_group.execute(
                sub_step_ids=sub_ids,
                run_step=_run_sub,
                dry_run=dry_run,
            )

        if action == StepAction.WAIT:
            return await wait.execute(
                inputs={**state, **resolved_inputs},
                duration_seconds=step.duration_seconds,
                wait_condition=step.wait_condition,
                timeout_seconds=step.timeout_seconds,
                dry_run=dry_run,
            )

        if action == StepAction.EXECUTE_CODE:
            return await execute_code.execute(
                tool_id=step.tool_id,
                adapter_id=step.adapter_id,
                inputs=resolved_inputs,
                sandbox=step.sandbox,
                dry_run=dry_run,
            )

        if action == StepAction.HTTP_REQUEST:
            return await http_request.execute(
                url=step.url,
                method=step.http_method,
                headers=step.http_headers,
                body=step.http_body,
                timeout_seconds=step.timeout_seconds or 30,
                inputs=resolved_inputs,
                dry_run=dry_run,
            )

        if action == StepAction.SUB_WORKFLOW:
            return await sub_workflow.execute(
                workflow_definition=step.sub_workflow,
                inputs=resolved_inputs,
                dry_run=dry_run,
            )

        if action == StepAction.ROUTE:
            return await route.execute(
                query=step.query,
                candidates=step.route_candidates,
                model=step.route_model,
                inputs=resolved_inputs,
                dry_run=dry_run,
            )

        raise ValueError(f"Unknown action: {action}")


# ---------------------------------------------------------------------------
# CA-043: Backpressure Signaling
# ---------------------------------------------------------------------------


class BackpressureController:
    """Concurrency limiter that emits backpressure signals.

    Upstream producers can check ``is_pressured()`` or await
    ``wait_for_capacity()`` before submitting more work.
    """

    def __init__(self, max_tokens: int = 10) -> None:
        self._max_tokens = max_tokens
        self._tokens = max_tokens
        self._lock = asyncio.Lock()
        self._capacity_event = asyncio.Event()
        self._capacity_event.set()

    async def acquire(self) -> bool:
        """Acquire a token. Returns True if acquired, False if no capacity."""
        async with self._lock:
            if self._tokens > 0:
                self._tokens -= 1
                if self._tokens == 0:
                    self._capacity_event.clear()
                return True
            return False

    async def release(self) -> None:
        """Release a token back to the pool."""
        async with self._lock:
            if self._tokens < self._max_tokens:
                self._tokens += 1
                if self._tokens > 0:
                    self._capacity_event.set()

    def is_pressured(self) -> bool:
        """Return True if the system is under backpressure (no tokens)."""
        return self._tokens == 0

    async def wait_for_capacity(self) -> None:
        """Block until at least one token is available."""
        await self._capacity_event.wait()
