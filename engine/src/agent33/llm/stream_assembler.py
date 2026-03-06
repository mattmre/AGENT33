"""Reassemble ToolCall objects from streaming ToolCallDelta fragments."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent33.llm.base import ToolCall, ToolCallDelta


@dataclasses.dataclass
class ToolCallAssembler:
    """Accumulates streaming tool call deltas and produces complete ToolCall objects."""

    _pending: dict[int, dict[str, str | list[str]]] = dataclasses.field(
        default_factory=dict,
    )

    def feed(self, deltas: list[ToolCallDelta]) -> None:
        """Process a batch of ToolCallDelta fragments."""
        for d in deltas:
            if d.index not in self._pending:
                self._pending[d.index] = {"id": "", "name": "", "args_parts": []}
            entry = self._pending[d.index]
            if d.id:
                entry["id"] = d.id
            if d.function_name:
                entry["name"] = d.function_name
            if d.arguments_delta:
                args_parts = entry["args_parts"]
                assert isinstance(args_parts, list)
                args_parts.append(d.arguments_delta)

    def finalize(self) -> list[ToolCall]:
        """Build complete ToolCall objects from accumulated deltas."""
        from agent33.llm.base import ToolCall, ToolCallFunction

        result: list[ToolCall] = []
        for idx in sorted(self._pending):
            entry = self._pending[idx]
            args_parts = entry["args_parts"]
            assert isinstance(args_parts, list)
            result.append(
                ToolCall(
                    id=str(entry["id"]),
                    function=ToolCallFunction(
                        name=str(entry["name"]),
                        arguments="".join(args_parts),
                    ),
                )
            )
        self._pending.clear()
        return result

    @property
    def has_pending(self) -> bool:
        """Return True if there are accumulated deltas waiting to be finalized."""
        return bool(self._pending)

    def reset(self) -> None:
        """Discard all accumulated deltas."""
        self._pending.clear()
