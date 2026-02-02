"""Agent runtime -- executes an agent definition against an LLM."""

from __future__ import annotations

import dataclasses
import json
import logging
from typing import Any

from agent33.agents.definition import AgentDefinition
from agent33.llm.base import ChatMessage, LLMResponse
from agent33.llm.router import ModelRouter

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, slots=True)
class AgentResult:
    """Result of invoking an agent."""

    output: dict[str, Any]
    raw_response: str
    tokens_used: int
    model: str


def _build_system_prompt(definition: AgentDefinition) -> str:
    """Construct a system prompt from the agent definition."""
    parts: list[str] = []

    parts.append(f"You are '{definition.name}', an AI agent with role '{definition.role.value}'.")
    if definition.description:
        parts.append(f"Purpose: {definition.description}")

    if definition.capabilities:
        caps = ", ".join(c.value for c in definition.capabilities)
        parts.append(f"Capabilities: {caps}")

    if definition.inputs:
        input_desc = "; ".join(
            f"{name} ({p.type}): {p.description}" if p.description else f"{name} ({p.type})"
            for name, p in definition.inputs.items()
        )
        parts.append(f"Expected inputs: {input_desc}")

    if definition.outputs:
        output_desc = "; ".join(
            f"{name} ({p.type}): {p.description}" if p.description else f"{name} ({p.type})"
            for name, p in definition.outputs.items()
        )
        parts.append(f"You must produce outputs: {output_desc}")

    if definition.constraints:
        parts.append(
            f"Constraints: max_tokens={definition.constraints.max_tokens}, "
            f"timeout={definition.constraints.timeout_seconds}s, "
            f"max_retries={definition.constraints.max_retries}"
        )

    parts.append("Respond with valid JSON containing the output fields.")
    return "\n".join(parts)


def _parse_output(raw: str, definition: AgentDefinition) -> dict[str, Any]:
    """Try to parse the LLM response as JSON; fall back to wrapping in a dict."""
    stripped = raw.strip()
    # Handle markdown code fences
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        # Remove first and last fence lines
        inner_lines = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```") and not in_block:
                in_block = True
                continue
            if line.strip() == "```" and in_block:
                break
            if in_block:
                inner_lines.append(line)
        stripped = "\n".join(inner_lines).strip()

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
        return {"result": parsed}
    except json.JSONDecodeError:
        # If the definition has a single output, use that key
        output_keys = list(definition.outputs.keys())
        if len(output_keys) == 1:
            return {output_keys[0]: raw}
        return {"result": raw}


class AgentRuntime:
    """Executes an agent definition by calling the LLM via the model router."""

    def __init__(
        self,
        definition: AgentDefinition,
        router: ModelRouter,
        model: str | None = None,
        temperature: float = 0.7,
        observation_capture: Any | None = None,
        trace_emitter: Any | None = None,
        session_id: str = "",
    ) -> None:
        self._definition = definition
        self._router = router
        self._model = model or "llama3.2"
        self._temperature = temperature
        self._observation_capture = observation_capture
        self._trace_emitter = trace_emitter
        self._session_id = session_id

    @property
    def definition(self) -> AgentDefinition:
        return self._definition

    async def invoke(self, inputs: dict[str, Any]) -> AgentResult:
        """Run the agent with the given inputs and return a result."""
        system_prompt = _build_system_prompt(self._definition)

        # Validate required inputs
        for name, param in self._definition.inputs.items():
            if param.required and name not in inputs:
                raise ValueError(f"Missing required input: {name}")

        user_content = json.dumps(inputs, indent=2)

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_content),
        ]

        max_tokens = self._definition.constraints.max_tokens
        max_retries = self._definition.constraints.max_retries

        last_exc: Exception | None = None
        response: LLMResponse | None = None

        for attempt in range(max_retries + 1):
            try:
                response = await self._router.complete(
                    messages,
                    model=self._model,
                    temperature=self._temperature,
                    max_tokens=max_tokens,
                )
                break
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "agent %s invoke attempt %d/%d failed: %s",
                    self._definition.name,
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )

        if response is None:
            raise RuntimeError(
                f"Agent '{self._definition.name}' failed after {max_retries + 1} attempts"
            ) from last_exc

        output = _parse_output(response.content, self._definition)

        result = AgentResult(
            output=output,
            raw_response=response.content,
            tokens_used=response.total_tokens,
            model=response.model,
        )

        # Record observation if capture is available
        if self._observation_capture is not None:
            try:
                from agent33.memory.observation import Observation

                obs = Observation(
                    session_id=self._session_id,
                    agent_name=self._definition.name,
                    event_type="llm_response",
                    content=response.content[:2000],
                    metadata={"model": response.model, "tokens": response.total_tokens},
                    tags=[],
                )
                await self._observation_capture.record(obs)
            except Exception:
                logger.debug("failed to record observation", exc_info=True)

        # Emit trace spans if emitter is available
        if self._trace_emitter is not None:
            try:
                self._trace_emitter.emit_prompt(
                    self._definition.name,
                    [{"role": m.role, "content": m.content} for m in messages],
                )
                self._trace_emitter.emit_result(
                    self._definition.name, response.content
                )
            except Exception:
                logger.debug("failed to emit trace", exc_info=True)

        return result
