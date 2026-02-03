"""Short-term conversation memory with token counting."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Message:
    """A single conversation message."""

    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


def _estimate_tokens(text: str) -> int:
    """Estimate token count using word-based heuristic (words * 1.3)."""
    words = len(text.split())
    return math.ceil(words * 1.3)


@dataclass
class ShortTermMemory:
    """Maintains conversation history with token-aware trimming."""

    messages: list[Message] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        """Append a message to the conversation history."""
        self.messages.append(Message(role=role, content=content))

    def token_count(self) -> int:
        """Return estimated total token count across all messages."""
        return sum(_estimate_tokens(m.content) for m in self.messages)

    def get_context(self, max_tokens: int) -> list[dict[str, str]]:
        """Return messages fitting within *max_tokens*, trimming oldest first."""
        result: list[Message] = []
        running = 0
        # Walk from newest to oldest so we keep recent context.
        for msg in reversed(self.messages):
            cost = _estimate_tokens(msg.content)
            if running + cost > max_tokens:
                break
            result.append(msg)
            running += cost
        # Restore chronological order.
        result.reverse()
        return [m.to_dict() for m in result]

    def clear(self) -> None:
        """Remove all messages."""
        self.messages.clear()
