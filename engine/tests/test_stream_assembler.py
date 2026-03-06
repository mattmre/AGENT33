"""Tests for ToolCallAssembler — streaming tool call fragment reassembly."""

from __future__ import annotations

from agent33.llm.base import ToolCallDelta
from agent33.llm.stream_assembler import ToolCallAssembler


class TestToolCallAssembler:
    def test_single_tool_call_assembly(self) -> None:
        assembler = ToolCallAssembler()
        assembler.feed([
            ToolCallDelta(index=0, id="call_1", function_name="shell"),
            ToolCallDelta(index=0, arguments_delta='{"com'),
            ToolCallDelta(index=0, arguments_delta='mand": "ls"}'),
        ])
        result = assembler.finalize()
        assert len(result) == 1
        assert result[0].id == "call_1"
        assert result[0].function.name == "shell"
        assert result[0].function.arguments == '{"command": "ls"}'

    def test_multiple_tool_calls(self) -> None:
        assembler = ToolCallAssembler()
        assembler.feed([
            ToolCallDelta(index=0, id="call_1", function_name="read_file"),
            ToolCallDelta(index=1, id="call_2", function_name="write_file"),
        ])
        assembler.feed([
            ToolCallDelta(index=0, arguments_delta='{"path": "a.txt"}'),
            ToolCallDelta(index=1, arguments_delta='{"path": "b.txt"}'),
        ])
        result = assembler.finalize()
        assert len(result) == 2
        assert result[0].id == "call_1"
        assert result[0].function.name == "read_file"
        assert result[1].id == "call_2"
        assert result[1].function.name == "write_file"

    def test_interleaved_deltas(self) -> None:
        assembler = ToolCallAssembler()
        assembler.feed([ToolCallDelta(index=0, id="c0", function_name="foo")])
        assembler.feed([ToolCallDelta(index=1, id="c1", function_name="bar")])
        assembler.feed([ToolCallDelta(index=0, arguments_delta='{"a":')])
        assembler.feed([ToolCallDelta(index=1, arguments_delta='{"b":')])
        assembler.feed([ToolCallDelta(index=0, arguments_delta=' 1}')])
        assembler.feed([ToolCallDelta(index=1, arguments_delta=' 2}')])
        result = assembler.finalize()
        assert len(result) == 2
        assert result[0].function.arguments == '{"a": 1}'
        assert result[1].function.arguments == '{"b": 2}'

    def test_empty_arguments(self) -> None:
        assembler = ToolCallAssembler()
        assembler.feed([
            ToolCallDelta(index=0, id="call_1", function_name="noop"),
        ])
        result = assembler.finalize()
        assert result[0].function.arguments == ""

    def test_finalize_clears_state(self) -> None:
        assembler = ToolCallAssembler()
        assembler.feed([ToolCallDelta(index=0, id="c1", function_name="f")])
        assert assembler.has_pending
        assembler.finalize()
        assert not assembler.has_pending

    def test_has_pending(self) -> None:
        assembler = ToolCallAssembler()
        assert not assembler.has_pending
        assembler.feed([ToolCallDelta(index=0, id="c1")])
        assert assembler.has_pending

    def test_reset(self) -> None:
        assembler = ToolCallAssembler()
        assembler.feed([ToolCallDelta(index=0, id="c1", function_name="x")])
        assembler.reset()
        assert not assembler.has_pending
        result = assembler.finalize()
        assert result == []

    def test_id_only_in_first_delta(self) -> None:
        """The id is typically only in the first delta for a given index."""
        assembler = ToolCallAssembler()
        assembler.feed([ToolCallDelta(index=0, id="call_42", function_name="tool")])
        assembler.feed([ToolCallDelta(index=0, arguments_delta='{"x": 1}')])
        result = assembler.finalize()
        assert result[0].id == "call_42"

    def test_name_only_in_first_delta(self) -> None:
        """The function name is typically only in the first delta."""
        assembler = ToolCallAssembler()
        assembler.feed([ToolCallDelta(index=0, id="c1", function_name="my_tool")])
        assembler.feed([ToolCallDelta(index=0, arguments_delta="{}")])
        result = assembler.finalize()
        assert result[0].function.name == "my_tool"

    def test_arguments_concatenation(self) -> None:
        assembler = ToolCallAssembler()
        parts = ['{"ke', 'y": ', '"val', 'ue"}']
        for part in parts:
            assembler.feed([ToolCallDelta(index=0, arguments_delta=part)])
        # Also need id/name
        assembler.feed([ToolCallDelta(index=0, id="c1", function_name="t")])
        result = assembler.finalize()
        assert result[0].function.arguments == '{"key": "value"}'

    def test_multiple_finalize_calls(self) -> None:
        """Calling finalize twice returns empty on second call."""
        assembler = ToolCallAssembler()
        assembler.feed([ToolCallDelta(index=0, id="c1", function_name="f")])
        first = assembler.finalize()
        assert len(first) == 1
        second = assembler.finalize()
        assert second == []

    def test_feed_empty_list(self) -> None:
        assembler = ToolCallAssembler()
        assembler.feed([])
        assert not assembler.has_pending

    def test_complex_json_arguments(self) -> None:
        assembler = ToolCallAssembler()
        complex_json = '{"nested": {"a": [1, 2, 3]}, "flag": true, "name": null}'
        assembler.feed([
            ToolCallDelta(index=0, id="call_x", function_name="complex_tool"),
        ])
        # Stream it in small chunks
        chunk_size = 5
        for i in range(0, len(complex_json), chunk_size):
            assembler.feed([
                ToolCallDelta(index=0, arguments_delta=complex_json[i : i + chunk_size]),
            ])
        result = assembler.finalize()
        assert result[0].function.arguments == complex_json

    def test_sorted_index_order(self) -> None:
        """Results are returned sorted by index."""
        assembler = ToolCallAssembler()
        assembler.feed([ToolCallDelta(index=2, id="c2", function_name="third")])
        assembler.feed([ToolCallDelta(index=0, id="c0", function_name="first")])
        assembler.feed([ToolCallDelta(index=1, id="c1", function_name="second")])
        result = assembler.finalize()
        assert [r.function.name for r in result] == ["first", "second", "third"]

    def test_id_overwritten_by_later_delta(self) -> None:
        """If a later delta for the same index has an id, it overwrites."""
        assembler = ToolCallAssembler()
        assembler.feed([ToolCallDelta(index=0, id="old_id")])
        assembler.feed([ToolCallDelta(index=0, id="new_id")])
        result = assembler.finalize()
        assert result[0].id == "new_id"

    def test_name_overwritten_by_later_delta(self) -> None:
        """If a later delta for the same index has a name, it overwrites."""
        assembler = ToolCallAssembler()
        assembler.feed([ToolCallDelta(index=0, function_name="old_name")])
        assembler.feed([ToolCallDelta(index=0, function_name="new_name")])
        result = assembler.finalize()
        assert result[0].function.name == "new_name"
