"""Load SkillsBench-format tasks from a local directory.

SkillsBench organises tasks as::

    tasks/
      {category}/
        {task_name}/
          instruction.md          # Task instruction for the agent
          tests/
            test_outputs.py       # Binary reward pytest file
          environment/            # Optional
            skills/               # Optional bundled skills dir

This module discovers and loads those tasks so AGENT-33's evaluation
pipeline can run them.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from agent33.benchmarks.skillsbench.models import TaskFilter

logger = logging.getLogger(__name__)


class SkillsBenchTask:
    """Metadata for a single SkillsBench task.

    Attributes
    ----------
    task_id:
        Canonical identifier: ``{category}/{task_name}``.
    category:
        Top-level category directory name (e.g. ``"scientific_computing"``).
    instruction:
        Full text of ``instruction.md``.
    skills_dir:
        Path to ``environment/skills/`` if it exists, else ``None``.
    tests_path:
        Absolute path to ``tests/test_outputs.py``.
    metadata:
        Any extra key-value pairs extracted from the task directory.
    """

    __slots__ = ("task_id", "category", "instruction", "skills_dir", "tests_path", "metadata")

    def __init__(
        self,
        *,
        task_id: str,
        category: str,
        instruction: str,
        skills_dir: Path | None,
        tests_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.task_id = task_id
        self.category = category
        self.instruction = instruction
        self.skills_dir = skills_dir
        self.tests_path = tests_path
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"SkillsBenchTask(task_id={self.task_id!r}, category={self.category!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SkillsBenchTask):
            return NotImplemented
        return self.task_id == other.task_id

    def __hash__(self) -> int:
        return hash(self.task_id)


class SkillsBenchTaskLoader:
    """Discovers and loads tasks from a SkillsBench repository checkout.

    Parameters
    ----------
    root:
        Root of the SkillsBench repository (the directory that contains
        the ``tasks/`` subdirectory).
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    @property
    def root(self) -> Path:
        """Return the SkillsBench repository root."""
        return self._root

    @property
    def tasks_dir(self) -> Path:
        """Return the ``tasks/`` subdirectory."""
        return self._root / "tasks"

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover_tasks(
        self,
        task_filter: TaskFilter | None = None,
    ) -> list[SkillsBenchTask]:
        """Walk ``tasks/{category}/{task_name}/`` directories.

        Returns tasks in sorted order (category then task_name) for
        deterministic discovery.

        Parameters
        ----------
        task_filter:
            Optional filter to select a subset of tasks. If ``None``,
            all valid tasks are returned.
        """
        tasks_dir = self.tasks_dir
        if not tasks_dir.is_dir():
            logger.warning("SkillsBench tasks directory not found: %s", tasks_dir)
            return []

        found: list[SkillsBenchTask] = []
        for category_dir in sorted(tasks_dir.iterdir()):
            if not category_dir.is_dir():
                continue

            category = category_dir.name

            # Apply category filter
            if task_filter is not None:
                if task_filter.exclude_categories and category in task_filter.exclude_categories:
                    continue
                if task_filter.categories and category not in task_filter.categories:
                    continue

            for task_dir in sorted(category_dir.iterdir()):
                if not task_dir.is_dir():
                    continue

                task_id = f"{category}/{task_dir.name}"

                # Apply task ID filter
                if (
                    task_filter is not None
                    and task_filter.task_ids
                    and task_id not in task_filter.task_ids
                ):
                    continue

                try:
                    task = self._load_from_dir(category=category, task_dir=task_dir)
                    found.append(task)
                except Exception:
                    logger.warning("Failed to load task from %s", task_dir, exc_info=True)

                # Apply max_tasks limit
                if (
                    task_filter is not None
                    and task_filter.max_tasks > 0
                    and len(found) >= task_filter.max_tasks
                ):
                    break

            # Check max_tasks at category level too
            if (
                task_filter is not None
                and task_filter.max_tasks > 0
                and len(found) >= task_filter.max_tasks
            ):
                break

        logger.info("Discovered %d SkillsBench tasks under %s", len(found), tasks_dir)
        return found

    def load_task(self, task_id: str) -> SkillsBenchTask:
        """Load a specific task by ID (``category/task_name`` format).

        Raises
        ------
        FileNotFoundError
            If the task directory does not exist.
        ValueError
            If ``task_id`` is not in ``category/task_name`` format.
        """
        parts = task_id.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"task_id must be in 'category/task_name' format, got: {task_id!r}")
        category, task_name = parts
        task_dir = self.tasks_dir / category / task_name
        if not task_dir.is_dir():
            raise FileNotFoundError(f"Task directory not found: {task_dir}")
        return self._load_from_dir(category=category, task_dir=task_dir)

    def list_categories(self) -> list[str]:
        """List all category directory names in sorted order."""
        tasks_dir = self.tasks_dir
        if not tasks_dir.is_dir():
            return []
        return sorted(d.name for d in tasks_dir.iterdir() if d.is_dir())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_from_dir(self, category: str, task_dir: Path) -> SkillsBenchTask:
        """Load a single task from a task directory."""
        task_name = task_dir.name
        task_id = f"{category}/{task_name}"

        # Load instruction
        instruction_path = task_dir / "instruction.md"
        if not instruction_path.is_file():
            raise FileNotFoundError(f"instruction.md not found in {task_dir}")
        instruction = instruction_path.read_text(encoding="utf-8").strip()

        # Locate tests/test_outputs.py
        tests_path = task_dir / "tests" / "test_outputs.py"
        if not tests_path.is_file():
            raise FileNotFoundError(f"tests/test_outputs.py not found in {task_dir}")

        # Optional skills dir
        candidate_skills_dir = task_dir / "environment" / "skills"
        skills_dir: Path | None = candidate_skills_dir if candidate_skills_dir.is_dir() else None

        metadata: dict[str, Any] = {
            "task_dir": str(task_dir),
            "task_name": task_name,
        }

        return SkillsBenchTask(
            task_id=task_id,
            category=category,
            instruction=instruction,
            skills_dir=skills_dir,
            tests_path=tests_path,
            metadata=metadata,
        )
