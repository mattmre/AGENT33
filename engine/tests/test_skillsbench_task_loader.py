"""Tests for SkillsBench task loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent33.benchmarks.skillsbench.models import TaskFilter
from agent33.benchmarks.skillsbench.task_loader import SkillsBenchTask, SkillsBenchTaskLoader


# ---------------------------------------------------------------------------
# Helpers to build task directory structures on disk
# ---------------------------------------------------------------------------


def _create_task(
    root: Path,
    category: str,
    task_name: str,
    instruction: str = "Do the task.",
    *,
    with_skills: bool = False,
) -> Path:
    """Create a minimal SkillsBench task directory structure."""
    task_dir = root / "tasks" / category / task_name
    task_dir.mkdir(parents=True, exist_ok=True)

    # instruction.md
    (task_dir / "instruction.md").write_text(instruction, encoding="utf-8")

    # tests/test_outputs.py
    tests_dir = task_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_outputs.py").write_text(
        "def test_output():\n    assert True\n", encoding="utf-8"
    )

    # Optional skills directory
    if with_skills:
        skills_dir = task_dir / "environment" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / "example.yaml").write_text(
            "name: example-skill\ndescription: Test skill\n", encoding="utf-8"
        )

    return task_dir


# ---------------------------------------------------------------------------
# SkillsBenchTask
# ---------------------------------------------------------------------------


class TestSkillsBenchTask:
    def test_equality_by_task_id(self) -> None:
        task_a = SkillsBenchTask(
            task_id="math/add",
            category="math",
            instruction="Add numbers",
            skills_dir=None,
            tests_path=Path("/x/tests/test_outputs.py"),
        )
        task_b = SkillsBenchTask(
            task_id="math/add",
            category="math",
            instruction="Different instruction",
            skills_dir=None,
            tests_path=Path("/y/tests/test_outputs.py"),
        )
        assert task_a == task_b

    def test_inequality(self) -> None:
        task_a = SkillsBenchTask(
            task_id="math/add", category="math", instruction="",
            skills_dir=None, tests_path=Path("/x"),
        )
        task_b = SkillsBenchTask(
            task_id="math/subtract", category="math", instruction="",
            skills_dir=None, tests_path=Path("/x"),
        )
        assert task_a != task_b

    def test_hash_consistency(self) -> None:
        task = SkillsBenchTask(
            task_id="science/chem", category="science", instruction="",
            skills_dir=None, tests_path=Path("/x"),
        )
        # Same task_id should produce the same hash
        task2 = SkillsBenchTask(
            task_id="science/chem", category="science", instruction="other",
            skills_dir=None, tests_path=Path("/y"),
        )
        assert hash(task) == hash(task2)

    def test_repr(self) -> None:
        task = SkillsBenchTask(
            task_id="cat/name", category="cat", instruction="",
            skills_dir=None, tests_path=Path("/x"),
        )
        r = repr(task)
        assert "cat/name" in r
        assert "SkillsBenchTask" in r


# ---------------------------------------------------------------------------
# SkillsBenchTaskLoader -- discover_tasks
# ---------------------------------------------------------------------------


class TestSkillsBenchTaskLoaderDiscovery:
    def test_discover_empty_root(self, tmp_path: Path) -> None:
        loader = SkillsBenchTaskLoader(tmp_path)
        tasks = loader.discover_tasks()
        assert tasks == []

    def test_discover_missing_tasks_dir(self, tmp_path: Path) -> None:
        """No tasks/ subdirectory -- should return empty, not crash."""
        loader = SkillsBenchTaskLoader(tmp_path)
        assert loader.discover_tasks() == []

    def test_discover_single_task(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "math", "addition", "Add two numbers.")
        loader = SkillsBenchTaskLoader(tmp_path)
        tasks = loader.discover_tasks()
        assert len(tasks) == 1
        assert tasks[0].task_id == "math/addition"
        assert tasks[0].category == "math"
        assert tasks[0].instruction == "Add two numbers."

    def test_discover_multiple_categories(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "math", "add")
        _create_task(tmp_path, "science", "chem")
        _create_task(tmp_path, "security", "vuln")
        loader = SkillsBenchTaskLoader(tmp_path)
        tasks = loader.discover_tasks()
        assert len(tasks) == 3
        # Should be sorted by category then task name
        cats = [t.category for t in tasks]
        assert cats == sorted(cats)

    def test_discover_multiple_tasks_in_category(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "math", "subtract")
        _create_task(tmp_path, "math", "add")
        _create_task(tmp_path, "math", "multiply")
        loader = SkillsBenchTaskLoader(tmp_path)
        tasks = loader.discover_tasks()
        assert len(tasks) == 3
        # Within a category, tasks should be sorted by name
        names = [t.metadata["task_name"] for t in tasks]
        assert names == sorted(names)

    def test_discover_with_skills_dir(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "cat", "task_with_skills", with_skills=True)
        loader = SkillsBenchTaskLoader(tmp_path)
        tasks = loader.discover_tasks()
        assert len(tasks) == 1
        assert tasks[0].skills_dir is not None
        assert tasks[0].skills_dir.is_dir()

    def test_discover_without_skills_dir(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "cat", "task_no_skills", with_skills=False)
        loader = SkillsBenchTaskLoader(tmp_path)
        tasks = loader.discover_tasks()
        assert len(tasks) == 1
        assert tasks[0].skills_dir is None

    def test_discover_skips_files_in_tasks_dir(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "math", "add")
        # Add a stray file in tasks/
        (tmp_path / "tasks" / "README.md").write_text("ignore me", encoding="utf-8")
        loader = SkillsBenchTaskLoader(tmp_path)
        tasks = loader.discover_tasks()
        assert len(tasks) == 1

    def test_discover_skips_invalid_task(self, tmp_path: Path) -> None:
        """A task directory missing instruction.md should be skipped."""
        task_dir = tmp_path / "tasks" / "math" / "broken"
        task_dir.mkdir(parents=True)
        # No instruction.md -- should be skipped silently
        _create_task(tmp_path, "math", "valid")
        loader = SkillsBenchTaskLoader(tmp_path)
        tasks = loader.discover_tasks()
        assert len(tasks) == 1
        assert tasks[0].task_id == "math/valid"


# ---------------------------------------------------------------------------
# SkillsBenchTaskLoader -- discover_tasks with TaskFilter
# ---------------------------------------------------------------------------


class TestSkillsBenchTaskLoaderFilter:
    def test_filter_by_category(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "math", "add")
        _create_task(tmp_path, "science", "chem")
        _create_task(tmp_path, "security", "vuln")
        loader = SkillsBenchTaskLoader(tmp_path)
        f = TaskFilter(categories=["math"])
        tasks = loader.discover_tasks(task_filter=f)
        assert len(tasks) == 1
        assert tasks[0].category == "math"

    def test_filter_exclude_category(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "math", "add")
        _create_task(tmp_path, "science", "chem")
        loader = SkillsBenchTaskLoader(tmp_path)
        f = TaskFilter(exclude_categories=["science"])
        tasks = loader.discover_tasks(task_filter=f)
        assert len(tasks) == 1
        assert tasks[0].category == "math"

    def test_filter_by_task_id(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "math", "add")
        _create_task(tmp_path, "math", "subtract")
        _create_task(tmp_path, "science", "chem")
        loader = SkillsBenchTaskLoader(tmp_path)
        f = TaskFilter(task_ids=["math/subtract", "science/chem"])
        tasks = loader.discover_tasks(task_filter=f)
        assert len(tasks) == 2
        ids = {t.task_id for t in tasks}
        assert ids == {"math/subtract", "science/chem"}

    def test_filter_max_tasks(self, tmp_path: Path) -> None:
        for i in range(10):
            _create_task(tmp_path, "math", f"task_{i:02d}")
        loader = SkillsBenchTaskLoader(tmp_path)
        f = TaskFilter(max_tasks=3)
        tasks = loader.discover_tasks(task_filter=f)
        assert len(tasks) == 3


# ---------------------------------------------------------------------------
# SkillsBenchTaskLoader -- load_task
# ---------------------------------------------------------------------------


class TestSkillsBenchTaskLoaderLoadTask:
    def test_load_specific_task(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "math", "addition", "Add numbers.")
        loader = SkillsBenchTaskLoader(tmp_path)
        task = loader.load_task("math/addition")
        assert task.task_id == "math/addition"
        assert task.instruction == "Add numbers."

    def test_load_task_not_found(self, tmp_path: Path) -> None:
        (tmp_path / "tasks").mkdir(parents=True)
        loader = SkillsBenchTaskLoader(tmp_path)
        with pytest.raises(FileNotFoundError, match="Task directory not found"):
            loader.load_task("nonexistent/task")

    def test_load_task_invalid_format(self, tmp_path: Path) -> None:
        loader = SkillsBenchTaskLoader(tmp_path)
        with pytest.raises(ValueError, match="category/task_name"):
            loader.load_task("no-slash")

    def test_load_task_missing_instruction(self, tmp_path: Path) -> None:
        """Task directory exists but has no instruction.md."""
        task_dir = tmp_path / "tasks" / "math" / "broken"
        task_dir.mkdir(parents=True)
        tests_dir = task_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_outputs.py").write_text("pass", encoding="utf-8")
        loader = SkillsBenchTaskLoader(tmp_path)
        with pytest.raises(FileNotFoundError, match="instruction.md"):
            loader.load_task("math/broken")

    def test_load_task_missing_test_file(self, tmp_path: Path) -> None:
        """Task directory exists with instruction but no tests/test_outputs.py."""
        task_dir = tmp_path / "tasks" / "math" / "broken"
        task_dir.mkdir(parents=True)
        (task_dir / "instruction.md").write_text("Do something", encoding="utf-8")
        loader = SkillsBenchTaskLoader(tmp_path)
        with pytest.raises(FileNotFoundError, match="test_outputs.py"):
            loader.load_task("math/broken")


# ---------------------------------------------------------------------------
# SkillsBenchTaskLoader -- list_categories
# ---------------------------------------------------------------------------


class TestSkillsBenchTaskLoaderCategories:
    def test_list_categories_empty(self, tmp_path: Path) -> None:
        loader = SkillsBenchTaskLoader(tmp_path)
        assert loader.list_categories() == []

    def test_list_categories(self, tmp_path: Path) -> None:
        _create_task(tmp_path, "math", "add")
        _create_task(tmp_path, "science", "chem")
        _create_task(tmp_path, "security", "vuln")
        loader = SkillsBenchTaskLoader(tmp_path)
        cats = loader.list_categories()
        assert cats == ["math", "science", "security"]

    def test_tasks_dir_property(self, tmp_path: Path) -> None:
        loader = SkillsBenchTaskLoader(tmp_path)
        assert loader.tasks_dir == tmp_path / "tasks"

    def test_root_property(self, tmp_path: Path) -> None:
        loader = SkillsBenchTaskLoader(tmp_path)
        assert loader.root == tmp_path
