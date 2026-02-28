"""Iterative tool-use loop for agent execution.

Implements the core loop that allows an agent to call tools repeatedly
until the task is complete, a budget is exceeded, or an error threshold
is reached.  This is the P0 capability gap identified in the SkillsBench
analysis.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import re
from typing import TYPE_CHECKING, Any

from agent33.llm.base import ChatMessage, LLMResponse
from agent33.tools.base import ToolResult
from agent33.tools.schema import generate_tool_description

if TYPE_CHECKING:
    from collections.abc import Callable

    from agent33.agents.context_manager import ContextManager
    from agent33.autonomy.enforcement import RuntimeEnforcer
    from agent33.llm.router import ModelRouter
    from agent33.memory.observation import ObservationCapture
    from agent33.tools.base import ToolContext
    from agent33.tools.governance import ToolGovernance
    from agent33.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

CONFIRMATION_PROMPT = (
    "You indicated you have completed the task. Please respond with "
    "exactly one of the following formats:\n\n"
    "COMPLETED: [your final answer]\n"
    "CONTINUE: [what you still need to do]\n\n"
    "If the task is not fully complete, use CONTINUE and keep working. "
    "If it is complete, use COMPLETED and restate your final answer."
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True, slots=True)
class ToolLoopConfig:
    """Immutable configuration for a tool-use loop."""

    max_iterations: int = 20
    max_tool_calls_per_iteration: int = 5
    error_threshold: int = 3
    enable_double_confirmation: bool = True
    loop_detection_threshold: int = 0  # 0 disables loop detection by default


@dataclasses.dataclass(slots=True)
class ToolLoopState:
    """Mutable state tracked across loop iterations."""

    iteration: int = 0
    total_tokens: int = 0
    tool_calls_made: int = 0
    tools_used: list[str] = dataclasses.field(default_factory=list)
    consecutive_errors: int = 0
    confirmation_pending: bool = False
    call_history: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True, slots=True)
class ToolLoopResult:
    """Immutable result returned when the loop terminates."""

    output: dict[str, Any]
    raw_response: str
    tokens_used: int
    model: str
    iterations: int
    tool_calls_made: int
    tools_used: list[str]
    termination_reason: str  # "completed", "max_iterations", "error", "budget_exceeded"


# ---------------------------------------------------------------------------
# ToolLoop
# ---------------------------------------------------------------------------


class ToolLoop:
    """Iterative tool-use loop for agent execution.

    Sends messages to an LLM via *router*, inspects the response for tool
    calls, executes them through *tool_registry* (with governance and
    autonomy checks), appends the results back to the conversation, and
    repeats until the LLM signals completion or a limit is reached.
    """

    def __init__(
        self,
        router: ModelRouter,
        tool_registry: ToolRegistry,
        tool_governance: ToolGovernance | None = None,
        tool_context: ToolContext | None = None,
        observation_capture: ObservationCapture | None = None,
        runtime_enforcer: RuntimeEnforcer | None = None,
        config: ToolLoopConfig | None = None,
        agent_name: str = "",
        session_id: str = "",
        context_manager: ContextManager | None = None,
        leakage_detector: Callable[[str], bool] | None = None,
        hook_registry: Any | None = None,
        tenant_id: str = "",
    ) -> None:
        self._router = router
        self._tool_registry = tool_registry
        self._tool_governance = tool_governance
        self._tool_context = tool_context
        self._observation_capture = observation_capture
        self._runtime_enforcer = runtime_enforcer
        self._config = config or ToolLoopConfig()
        self._agent_name = agent_name
        self._session_id = session_id
        self._context_manager = context_manager
        self._leakage_detector = leakage_detector
        self._hook_registry = hook_registry
        self._tenant_id = tenant_id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ToolLoopResult:
        """Execute the iterative tool-use loop.

        Parameters
        ----------
        messages:
            Initial conversation messages (system + user at minimum).
        model:
            Model identifier to pass to the router.
        temperature:
            Sampling temperature.
        max_tokens:
            Optional max-tokens cap per LLM call.

        Returns
        -------
        ToolLoopResult
            Contains the final output, token usage, iteration count,
            tool-call stats, and termination reason.
        """
        state = ToolLoopState()
        tool_descriptions = self._collect_tool_descriptions()

        last_raw = ""
        last_model = model

        while state.iteration < self._config.max_iterations:
            state.iteration += 1  # 1-based iteration count

            # --- Call the LLM -------------------------------------------------
            try:
                response = await self._router.complete(
                    messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tool_descriptions if tool_descriptions else None,
                )
            except Exception:
                state.consecutive_errors += 1
                logger.warning(
                    "LLM call failed (attempt %d, consecutive_errors=%d)",
                    state.iteration,
                    state.consecutive_errors,
                    exc_info=True,
                )
                if state.consecutive_errors >= self._config.error_threshold:
                    return self._build_result(state, last_raw, last_model, "error")
                continue

            # --- Track tokens -------------------------------------------------
            state.total_tokens += response.prompt_tokens + response.completion_tokens
            last_raw = response.content
            last_model = response.model

            # --- Record observation for LLM response --------------------------
            await self._record_observation(
                event_type="llm_response",
                content=response.content[:2000],
                metadata={
                    "model": response.model,
                    "tokens": response.total_tokens,
                    "has_tool_calls": response.has_tool_calls,
                    "iteration": state.iteration,
                },
            )

            # --- Handle tool calls --------------------------------------------
            if response.has_tool_calls:
                state.consecutive_errors = 0
                state.confirmation_pending = False

                # --- Doom-loop detection ---
                if self._config.loop_detection_threshold > 0:
                    loop_detected = self._check_doom_loop(response, state)
                    if loop_detected:
                        logger.warning(
                            "Doom-loop detected: identical tool call repeated %d times",
                            self._config.loop_detection_threshold,
                        )
                        return self._build_result(state, last_raw, last_model, "loop_detected")

                tool_results = await self._execute_tool_calls(response, state)

                # Check if budget enforcer blocked during tool execution
                if self._runtime_enforcer is not None and any(
                    tr.error == "__budget_blocked__" for tr in tool_results
                ):
                    return self._build_result(state, last_raw, last_model, "budget_exceeded")

                # Only include tool_calls that were actually processed in
                # the assistant message.  OpenAI-style APIs require every
                # tool_call id to have a matching role="tool" result; if
                # we cap at max_tool_calls_per_iteration the rest must
                # not appear in the conversation.
                assert response.tool_calls is not None  # guarded by has_tool_calls
                processed_tool_calls = response.tool_calls[: len(tool_results)]

                messages.append(
                    ChatMessage(
                        role="assistant",
                        content=response.content,
                        tool_calls=processed_tool_calls,
                    )
                )

                # Append tool result messages
                for i, tool_result in enumerate(tool_results):
                    tc = processed_tool_calls[i] if i < len(processed_tool_calls) else None
                    tc_id = tc.id if tc else ""
                    tc_name = tc.function.name if tc else ""
                    # Truncate raw tool output before adding to LLM context
                    from agent33.agents.context_manager import truncate_tool_output

                    content = (
                        truncate_tool_output(tool_result.output)
                        if tool_result.success
                        else f"Error: {truncate_tool_output(tool_result.error)}"
                    )
                    messages.append(
                        ChatMessage(
                            role="tool",
                            content=content,
                            tool_call_id=tc_id,
                            name=tc_name,
                        )
                    )

                # --- PHASE 34: Segmented Context Wipe (Handoff Interceptor) ---
                for tc, result in zip(processed_tool_calls, tool_results, strict=False):
                    if tc.function.name == "handoff" and result.success:
                        logger.info("PHASE 34: Intercepting Handoff -> Triggering Context Wipe.")
                        from agent33.workflows.actions.handoff import StateLedger, execute_handoff

                        try:
                            # Re-parse args, the registry already validated them
                            parsed_args = json.loads(tc.function.arguments)
                            ledger = StateLedger(**parsed_args.get("ledger_data", {}))
                            # Wipe and reset the entire conversation array
                            messages.clear()
                            wiped_messages = execute_handoff(
                                ledger,
                                [
                                    ChatMessage(
                                        role="system",
                                        content=messages[0].content if messages else "",
                                    )
                                ],
                            )
                            messages.extend(wiped_messages)

                            # Log to ui/observation for user visibility
                            obj = ledger.objective
                            await self._record_observation(
                                event_type="handoff_context_wipe",
                                content=f"Agent memory wiped. Fresh context + Objective: {obj}",
                                metadata={
                                    "source": ledger.source_agent,
                                    "target": ledger.target_agent,
                                },
                            )
                        except Exception as e:
                            logger.error(f"Handoff wipe failed unexpectedly: {e}")
            else:
                # --- Text-only response (no tool calls) -----------------------
                if not self._config.enable_double_confirmation:
                    output = self._parse_output(response.content)
                    return ToolLoopResult(
                        output=output,
                        raw_response=response.content,
                        tokens_used=state.total_tokens,
                        model=response.model,
                        iterations=state.iteration,
                        tool_calls_made=state.tool_calls_made,
                        tools_used=list(state.tools_used),
                        termination_reason="completed",
                    )

                if not state.confirmation_pending:
                    state.confirmation_pending = True
                    messages.append(ChatMessage(role="assistant", content=response.content))
                    messages.append(ChatMessage(role="user", content=CONFIRMATION_PROMPT))
                else:
                    # Parse structured confirmation response
                    final_text = response.content
                    confirmed = _parse_confirmation(final_text)

                    if confirmed is False:
                        # LLM said CONTINUE — keep going
                        state.confirmation_pending = False
                        messages.append(ChatMessage(role="assistant", content=response.content))
                        continue

                    if confirmed is None:
                        # Ambiguous response format; ask again for explicit confirmation.
                        messages.append(ChatMessage(role="assistant", content=response.content))
                        messages.append(ChatMessage(role="user", content=CONFIRMATION_PROMPT))
                        state.confirmation_pending = True
                        continue

                    # confirmed is True
                    final_text = _strip_completion_prefix(final_text)

                    output = self._parse_output(final_text)
                    return ToolLoopResult(
                        output=output,
                        raw_response=response.content,
                        tokens_used=state.total_tokens,
                        model=response.model,
                        iterations=state.iteration,
                        tool_calls_made=state.tool_calls_made,
                        tools_used=list(state.tools_used),
                        termination_reason="completed",
                    )

            # --- Context management after message changes ---------------------
            if self._context_manager is not None:
                messages = await self._context_manager.manage(messages)

            # --- Check termination conditions ---------------------------------
            if state.consecutive_errors >= self._config.error_threshold:
                return self._build_result(state, last_raw, last_model, "error")

            if self._runtime_enforcer is not None:
                from agent33.autonomy.models import EnforcementResult

                iter_result = self._runtime_enforcer.record_iteration()
                if iter_result == EnforcementResult.BLOCKED:
                    return self._build_result(state, last_raw, last_model, "budget_exceeded")

                dur_result = self._runtime_enforcer.check_duration()
                if dur_result == EnforcementResult.BLOCKED:
                    return self._build_result(state, last_raw, last_model, "budget_exceeded")

        # --- Max iterations exhausted -----------------------------------------
        return self._build_result(state, last_raw, last_model, "max_iterations")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect_tool_descriptions(self) -> list[dict[str, Any]]:
        """Build OpenAI-style tool descriptions from the registry."""
        descriptions: list[dict[str, Any]] = []
        for tool in self._tool_registry.list_all():
            entry = self._tool_registry.get_entry(tool.name)
            descriptions.append(generate_tool_description(tool, entry))
        return descriptions

    def _check_doom_loop(
        self,
        response: LLMResponse,
        state: ToolLoopState,
    ) -> bool:
        """Check if the same tool call is being repeated consecutively.

        Returns True if the most recent tool call signature has been repeated
        threshold times in a row.
        """
        if not response.tool_calls:
            return False

        # Build canonical signature for the first tool call
        # (agent typically repeats the same call, not multiple different ones)
        tc = response.tool_calls[0]
        # Sort arguments to create a stable signature
        try:
            import json

            args_dict = json.loads(tc.function.arguments)
            sorted_args = json.dumps(args_dict, sort_keys=True)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug("Tool call JSON parse fallback: %s", e)
            sorted_args = tc.function.arguments

        signature = f"{tc.function.name}:{sorted_args}"

        # Add to history
        state.call_history.append(signature)

        # Check if the last N calls are identical
        threshold = self._config.loop_detection_threshold
        if len(state.call_history) < threshold:
            return False

        recent_calls = state.call_history[-threshold:]
        return len(set(recent_calls)) == 1

    async def _execute_tool_calls(
        self,
        response: LLMResponse,
        state: ToolLoopState,
    ) -> list[ToolResult]:
        """Execute tool calls from an LLM response, respecting caps."""
        results: list[ToolResult] = []
        assert response.tool_calls is not None

        calls_to_process = response.tool_calls[: self._config.max_tool_calls_per_iteration]

        for tool_call in calls_to_process:
            tool_name = tool_call.function.name
            call_id = tool_call.id

            # --- Parse arguments ---
            try:
                parsed_args = json.loads(tool_call.function.arguments)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "Malformed tool call arguments for %s (call_id=%s)",
                    tool_name,
                    call_id,
                )
                state.consecutive_errors += 1
                result = ToolResult.fail(f"Invalid JSON arguments for tool '{tool_name}'")
                results.append(result)
                await self._record_observation(
                    event_type="tool_call",
                    content=f"Error parsing arguments for {tool_name}",
                    metadata={
                        "tool": tool_name,
                        "call_id": call_id,
                        "success": False,
                        "error": "malformed_arguments",
                    },
                )
                continue

            # --- Governance check ---
            if self._tool_governance is not None:
                gov_context = self._tool_context or self._default_context()
                allowed = self._tool_governance.pre_execute_check(
                    tool_name, parsed_args, gov_context
                )
                if not allowed:
                    logger.info("Governance denied tool call: %s", tool_name)
                    result = ToolResult.fail(f"Tool '{tool_name}' blocked by governance policy")
                    results.append(result)
                    await self._record_observation(
                        event_type="tool_call",
                        content=f"Governance blocked {tool_name}",
                        metadata={
                            "tool": tool_name,
                            "call_id": call_id,
                            "success": False,
                            "error": "governance_blocked",
                        },
                    )
                    continue

            # --- Autonomy enforcement check ---
            if self._runtime_enforcer is not None:
                from agent33.autonomy.models import EnforcementResult

                # Dispatch enforcement by tool type so the enforcer
                # checks the actual resource (command string, file path,
                # URL) rather than the tool name.
                enforce_result = EnforcementResult.ALLOWED
                if tool_name == "shell" and "command" in parsed_args:
                    enforce_result = self._runtime_enforcer.check_command(parsed_args["command"])
                elif tool_name in ("file_read", "file_write", "file_ops"):
                    path = parsed_args.get("path", parsed_args.get("file", ""))
                    if tool_name == "file_read":
                        enforce_result = self._runtime_enforcer.check_file_read(path)
                    else:
                        enforce_result = self._runtime_enforcer.check_file_write(path)
                elif tool_name == "web_fetch":
                    url = parsed_args.get("url", "")
                    enforce_result = self._runtime_enforcer.check_network(url)
                else:
                    enforce_result = self._runtime_enforcer.check_command(tool_name)
                if enforce_result == EnforcementResult.BLOCKED:
                    logger.info("Autonomy enforcer blocked tool call: %s", tool_name)
                    result = ToolResult(
                        success=False,
                        error="__budget_blocked__",
                    )
                    results.append(result)
                    return results  # Stop processing further calls

            # --- Hook: tool.execute.pre ---
            if self._hook_registry is not None:
                from agent33.hooks.models import HookEventType, ToolHookContext

                pre_runner = self._hook_registry.get_chain_runner(
                    HookEventType.TOOL_EXECUTE_PRE, self._tenant_id
                )
                tool_hook_ctx = ToolHookContext(
                    event_type=HookEventType.TOOL_EXECUTE_PRE,
                    tenant_id=self._tenant_id,
                    metadata={},
                    tool_name=tool_name,
                    arguments=parsed_args,
                    tool_context=self._tool_context,
                )
                tool_hook_ctx = await pre_runner.run(tool_hook_ctx)
                if tool_hook_ctx.abort:
                    result = ToolResult.fail(
                        f"Hook aborted: {tool_hook_ctx.abort_reason}"
                    )
                    results.append(result)
                    continue
                # Allow hooks to modify arguments
                parsed_args = tool_hook_ctx.arguments

            # --- Execute tool ---
            context = self._tool_context or self._default_context()
            try:
                result = await self._tool_registry.validated_execute(
                    tool_name, parsed_args, context
                )
            except Exception as exc:
                logger.warning(
                    "Tool execution failed: %s (call_id=%s): %s",
                    tool_name,
                    call_id,
                    exc,
                )
                state.consecutive_errors += 1
                result = ToolResult.fail(f"Tool '{tool_name}' raised: {exc}")

            # --- Hook: tool.execute.post ---
            if self._hook_registry is not None:
                from agent33.hooks.models import HookEventType, ToolHookContext

                post_runner = self._hook_registry.get_chain_runner(
                    HookEventType.TOOL_EXECUTE_POST, self._tenant_id
                )
                tool_hook_ctx = ToolHookContext(
                    event_type=HookEventType.TOOL_EXECUTE_POST,
                    tenant_id=self._tenant_id,
                    metadata={},
                    tool_name=tool_name,
                    arguments=parsed_args,
                    tool_context=self._tool_context,
                    result=result,
                )
                tool_hook_ctx = await post_runner.run(tool_hook_ctx)

            # --- Governance audit ---
            if self._tool_governance is not None:
                self._tool_governance.log_execution(tool_name, parsed_args, result)

            # --- Check for answer leakage in tool output ---
            if (
                self._leakage_detector is not None
                and result.success
                and result.output
                and self._leakage_detector(result.output)
            ):
                logger.info("Leakage detected in tool output for %s", tool_name)
                result = ToolResult.ok("[Tool output filtered: potential answer leakage detected]")
                await self._record_observation(
                    event_type="leakage_detected",
                    content=f"Answer leakage filtered from {tool_name} output",
                    metadata={"tool": tool_name, "call_id": call_id},
                )

            # --- Record observation ---
            await self._record_observation(
                event_type="tool_call",
                content=(
                    f"{tool_name}: {result.output[:500] if result.success else result.error[:500]}"
                ),
                metadata={
                    "tool": tool_name,
                    "call_id": call_id,
                    "success": result.success,
                    "arguments": parsed_args,
                },
            )

            # --- Track stats ---
            state.tool_calls_made += 1
            if tool_name not in state.tools_used:
                state.tools_used.append(tool_name)

            results.append(result)

        return results

    async def _record_observation(
        self,
        event_type: str,
        content: str,
        metadata: dict[str, Any],
    ) -> None:
        """Record an observation if capture is configured."""
        if self._observation_capture is None:
            return
        try:
            from agent33.memory.observation import Observation

            obs = Observation(
                session_id=self._session_id,
                agent_name=self._agent_name,
                event_type=event_type,
                content=content,
                metadata=metadata,
            )
            await self._observation_capture.record(obs)
        except Exception:
            logger.debug("Failed to record observation", exc_info=True)

    @staticmethod
    def _parse_output(raw: str) -> dict[str, Any]:
        """Try to parse the LLM's final text as JSON.

        Falls back to wrapping the raw text in a ``{"response": ...}`` dict.
        """
        stripped = raw.strip()

        # Try direct JSON parse
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug("Tool call JSON parse fallback: %s", e)

        # Strip markdown code fences and retry
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            inner_lines: list[str] = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```") and not in_block:
                    in_block = True
                    continue
                if line.strip() == "```" and in_block:
                    break
                if in_block:
                    inner_lines.append(line)
            inner = "\n".join(inner_lines).strip()
            try:
                parsed = json.loads(inner)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError) as e:
                logger.debug("Tool call JSON parse fallback: %s", e)

        return {"response": raw}

    @staticmethod
    def _default_context() -> ToolContext:
        """Create a minimal ToolContext when none is provided."""
        from agent33.tools.base import ToolContext

        return ToolContext(user_scopes=["tools:execute"])

    def _build_result(
        self,
        state: ToolLoopState,
        raw: str,
        model: str,
        reason: str,
    ) -> ToolLoopResult:
        """Build a ToolLoopResult from current state."""
        return ToolLoopResult(
            output=self._parse_output(raw),
            raw_response=raw,
            tokens_used=state.total_tokens,
            model=model,
            iterations=state.iteration,
            tool_calls_made=state.tool_calls_made,
            tools_used=list(state.tools_used),
            termination_reason=reason,
        )


# ---------------------------------------------------------------------------
# Structured confirmation parsing (Gap 4 Stage 1)
# ---------------------------------------------------------------------------


def _parse_confirmation(text: str) -> bool | None:
    """Parse a structured COMPLETED/CONTINUE response.

    Returns
    -------
    True  — LLM confirmed completion ("COMPLETED: ...")
    False — LLM wants to continue ("CONTINUE: ...")
    None  — Ambiguous (no structured prefix found)
    """
    stripped = text.strip()
    upper = stripped.upper()

    if re.match(r"^CONTINUE(?:\b|[:\-\s])", upper):
        return False
    if re.match(r"^COMPLETED(?:\b|[:\-\s])", upper):
        return True
    return None


def _strip_completion_prefix(text: str) -> str:
    """Remove the ``COMPLETED:`` prefix from a confirmation response."""
    stripped = text.strip()
    return re.sub(r"^COMPLETED(?:[:\-\s]+)?", "", stripped, flags=re.IGNORECASE).strip()
