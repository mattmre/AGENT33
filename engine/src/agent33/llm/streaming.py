"""Token-level LLM streaming utilities.

This module provides :class:`ToolCallAssembler` for reassembling streaming
tool-call deltas into complete :class:`~agent33.llm.base.ToolCall` objects.

The canonical implementation lives in :mod:`agent33.llm.stream_assembler`;
this module re-exports it under the ``streaming`` namespace so callers can
import from a single, semantically named location.
"""

from __future__ import annotations

from agent33.llm.stream_assembler import ToolCallAssembler

__all__ = ["ToolCallAssembler"]
