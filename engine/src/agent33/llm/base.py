"""Base LLM provider protocol and shared types."""

from __future__ import annotations

import dataclasses
from typing import Any, Protocol, runtime_checkable


@dataclasses.dataclass(frozen=True, slots=True)
class ToolCallFunction:
    """Function details within a tool call."""

    name: str
    arguments: str  # JSON string of arguments


@dataclasses.dataclass(frozen=True, slots=True)
class ToolCall:
    """A tool call from an LLM response."""

    id: str
    function: ToolCallFunction


@dataclasses.dataclass(frozen=True, slots=True)
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    tool_calls: list[ToolCall] | None = None
    finish_reason: str = "stop"

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def has_tool_calls(self) -> bool:
        """Return True if the response contains tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0


@dataclasses.dataclass(frozen=True, slots=True)
class ChatMessage:
    """A single message in a conversation."""

    role: str
    content: str
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str = ""
    name: str = ""


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol that all LLM providers must implement."""

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate a completion from the given messages."""
        ...

    async def list_models(self) -> list[str]:
        """Return available model identifiers."""
        ...
