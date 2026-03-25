"""Tests for Phase 59: Trajectory saver."""

from __future__ import annotations

import json
from pathlib import Path

from agent33.agents.trajectory import (
    _build_trajectory_record,
    _trajectory_filename,
    convert_scratchpad_to_think,
    get_trajectory_stats,
    save_trajectory,
)

# ---------------------------------------------------------------------------
# convert_scratchpad_to_think
# ---------------------------------------------------------------------------


class TestConvertScratchpadToThink:
    def test_basic_conversion(self) -> None:
        text = "<scratchpad>reasoning here</scratchpad>"
        assert convert_scratchpad_to_think(text) == "<think>reasoning here</think>"

    def test_case_insensitive(self) -> None:
        text = "<Scratchpad>reasoning</Scratchpad>"
        assert convert_scratchpad_to_think(text) == "<think>reasoning</think>"

    def test_multiline_content(self) -> None:
        text = "<scratchpad>\nstep 1\nstep 2\n</scratchpad>"
        result = convert_scratchpad_to_think(text)
        assert result == "<think>\nstep 1\nstep 2\n</think>"

    def test_multiple_blocks(self) -> None:
        text = "<scratchpad>first</scratchpad> then <scratchpad>second</scratchpad>"
        result = convert_scratchpad_to_think(text)
        assert result == "<think>first</think> then <think>second</think>"

    def test_no_scratchpad_unchanged(self) -> None:
        text = "Hello, this is a normal message."
        assert convert_scratchpad_to_think(text) == text

    def test_existing_think_tags_unchanged(self) -> None:
        text = "<think>already correct</think>"
        assert convert_scratchpad_to_think(text) == text

    def test_mixed_content(self) -> None:
        text = "Before <scratchpad>inside</scratchpad> after"
        assert convert_scratchpad_to_think(text) == "Before <think>inside</think> after"


# ---------------------------------------------------------------------------
# _trajectory_filename
# ---------------------------------------------------------------------------


class TestTrajectoryFilename:
    def test_success_filename(self) -> None:
        assert _trajectory_filename(True) == "trajectories_success.jsonl"

    def test_failure_filename(self) -> None:
        assert _trajectory_filename(False) == "trajectories_failed.jsonl"


# ---------------------------------------------------------------------------
# _build_trajectory_record
# ---------------------------------------------------------------------------


class TestBuildTrajectoryRecord:
    def test_basic_structure(self) -> None:
        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        record = _build_trajectory_record(conversation, "llama3.2", True)

        assert "conversations" in record
        assert "model" in record
        assert "completed" in record
        assert "timestamp" in record

        assert record["model"] == "llama3.2"
        assert record["completed"] is True

    def test_sharegpt_role_mapping(self) -> None:
        conversation = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "tool", "content": "result"},
        ]
        record = _build_trajectory_record(conversation, "test", True)
        turns = record["conversations"]

        assert turns[0]["from"] == "system"
        assert turns[1]["from"] == "human"
        assert turns[2]["from"] == "gpt"
        assert turns[3]["from"] == "tool"

    def test_scratchpad_normalised(self) -> None:
        conversation = [
            {"role": "assistant", "content": "<scratchpad>thinking</scratchpad> answer"},
        ]
        record = _build_trajectory_record(conversation, "test", True)
        assert "<think>thinking</think>" in record["conversations"][0]["value"]
        assert "<scratchpad>" not in record["conversations"][0]["value"]

    def test_secret_redaction_applied(self) -> None:
        conversation = [
            {"role": "user", "content": "My key is sk-abcdefghijklmnopqrstuvwxyz123456"},
        ]
        record = _build_trajectory_record(conversation, "test", True, redaction_enabled=True)
        value = record["conversations"][0]["value"]
        # The key should be redacted (not present in full).
        assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in value

    def test_secret_redaction_disabled(self) -> None:
        conversation = [
            {"role": "user", "content": "My key is sk-abcdefghijklmnopqrstuvwxyz123456"},
        ]
        record = _build_trajectory_record(conversation, "test", True, redaction_enabled=False)
        value = record["conversations"][0]["value"]
        assert "sk-abcdefghijklmnopqrstuvwxyz123456" in value

    def test_timestamp_is_iso_format(self) -> None:
        record = _build_trajectory_record([{"role": "user", "content": "hi"}], "test", True)
        # Should parse without error.
        from datetime import datetime

        datetime.fromisoformat(record["timestamp"])

    def test_failed_trajectory_flag(self) -> None:
        record = _build_trajectory_record([{"role": "user", "content": "hi"}], "test", False)
        assert record["completed"] is False


# ---------------------------------------------------------------------------
# save_trajectory (async, with filesystem)
# ---------------------------------------------------------------------------


class TestSaveTrajectory:
    async def test_creates_success_file(self, tmp_path: Path) -> None:
        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        await save_trajectory(conversation, "llama3.2", True, str(tmp_path))

        expected = tmp_path / "trajectories_success.jsonl"
        assert expected.exists()

        with open(expected, encoding="utf-8") as f:
            record = json.loads(f.readline())

        assert record["completed"] is True
        assert record["model"] == "llama3.2"
        assert len(record["conversations"]) == 2
        assert record["conversations"][0]["from"] == "human"
        assert record["conversations"][1]["from"] == "gpt"

    async def test_creates_failed_file(self, tmp_path: Path) -> None:
        conversation = [
            {"role": "user", "content": "Do something"},
            {"role": "assistant", "content": "Error occurred"},
        ]
        await save_trajectory(conversation, "llama3.2", False, str(tmp_path))

        expected = tmp_path / "trajectories_failed.jsonl"
        assert expected.exists()

        with open(expected, encoding="utf-8") as f:
            record = json.loads(f.readline())
        assert record["completed"] is False

    async def test_appends_to_existing_file(self, tmp_path: Path) -> None:
        conv1 = [{"role": "user", "content": "First"}]
        conv2 = [{"role": "user", "content": "Second"}]

        await save_trajectory(conv1, "model-a", True, str(tmp_path))
        await save_trajectory(conv2, "model-b", True, str(tmp_path))

        expected = tmp_path / "trajectories_success.jsonl"
        lines = expected.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

        r1 = json.loads(lines[0])
        r2 = json.loads(lines[1])
        assert r1["model"] == "model-a"
        assert r2["model"] == "model-b"

    async def test_custom_filename(self, tmp_path: Path) -> None:
        conversation = [{"role": "user", "content": "Hello"}]
        await save_trajectory(conversation, "test", True, str(tmp_path), filename="custom.jsonl")

        assert (tmp_path / "custom.jsonl").exists()

    async def test_creates_parent_directories(self, tmp_path: Path) -> None:
        nested_dir = str(tmp_path / "deep" / "nested" / "dir")
        conversation = [{"role": "user", "content": "Hello"}]
        await save_trajectory(conversation, "test", True, nested_dir)

        assert (Path(nested_dir) / "trajectories_success.jsonl").exists()

    async def test_empty_conversation_skipped(self, tmp_path: Path) -> None:
        await save_trajectory([], "test", True, str(tmp_path))
        # No file should be created.
        assert not (tmp_path / "trajectories_success.jsonl").exists()

    async def test_redaction_applied_in_saved_file(self, tmp_path: Path) -> None:
        conversation = [
            {"role": "user", "content": "Use key sk-abcdefghijklmnopqrstuvwxyz123456"},
        ]
        await save_trajectory(conversation, "test", True, str(tmp_path))

        with open(tmp_path / "trajectories_success.jsonl", encoding="utf-8") as f:
            record = json.loads(f.readline())

        value = record["conversations"][0]["value"]
        assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in value

    async def test_scratchpad_normalised_in_saved_file(self, tmp_path: Path) -> None:
        conversation = [
            {"role": "assistant", "content": "<scratchpad>reason</scratchpad> answer"},
        ]
        await save_trajectory(conversation, "test", True, str(tmp_path))

        with open(tmp_path / "trajectories_success.jsonl", encoding="utf-8") as f:
            record = json.loads(f.readline())

        assert "<think>reason</think>" in record["conversations"][0]["value"]

    async def test_separates_success_and_failure(self, tmp_path: Path) -> None:
        success_conv = [{"role": "user", "content": "Success"}]
        failure_conv = [{"role": "user", "content": "Failure"}]

        await save_trajectory(success_conv, "test", True, str(tmp_path))
        await save_trajectory(failure_conv, "test", False, str(tmp_path))

        success_path = tmp_path / "trajectories_success.jsonl"
        failure_path = tmp_path / "trajectories_failed.jsonl"
        assert success_path.exists()
        assert failure_path.exists()

        with open(success_path, encoding="utf-8") as f:
            assert json.loads(f.readline())["completed"] is True
        with open(failure_path, encoding="utf-8") as f:
            assert json.loads(f.readline())["completed"] is False


# ---------------------------------------------------------------------------
# get_trajectory_stats
# ---------------------------------------------------------------------------


class TestGetTrajectoryStats:
    async def test_empty_dir(self, tmp_path: Path) -> None:
        stats = get_trajectory_stats(str(tmp_path))
        assert stats["output_dir"] == str(tmp_path)
        assert stats["files"] == {}

    async def test_nonexistent_dir(self, tmp_path: Path) -> None:
        stats = get_trajectory_stats(str(tmp_path / "noexist"))
        assert stats["files"] == {}

    async def test_counts_records(self, tmp_path: Path) -> None:
        # Write 3 success records.
        for i in range(3):
            await save_trajectory(
                [{"role": "user", "content": f"msg{i}"}], "test", True, str(tmp_path)
            )
        # Write 1 failure record.
        await save_trajectory([{"role": "user", "content": "fail"}], "test", False, str(tmp_path))

        stats = get_trajectory_stats(str(tmp_path))
        assert stats["files"]["trajectories_success.jsonl"]["record_count"] == 3
        assert stats["files"]["trajectories_failed.jsonl"]["record_count"] == 1
        assert stats["files"]["trajectories_success.jsonl"]["size_bytes"] > 0
