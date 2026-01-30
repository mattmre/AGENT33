"""Base LLM provider protocol and shared types."""

from __future__ import annotations

import dataclasses
from typing import Protocol, runtime_checkable


@dataclasses.dataclass(frozen=True, slots=True)
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclasses.dataclass(frozen=True, slots=True)
class ChatMessage:
    """A single message in a conversation."""

    role: str
    content: str


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
    ) -> LLMResponse:
        """Generate a completion from the given messages."""
        ...

    async def list_models(self) -> list[str]:
        """Return available model identifiers."""
        ...
