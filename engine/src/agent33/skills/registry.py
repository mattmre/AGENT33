"""Skill registry: discover, register, search, and retrieve skills."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from agent33.memory.bm25 import BM25Index
from agent33.skills.loader import (
    load_from_directory,
    load_from_skillmd,
    load_from_yaml,
)

if TYPE_CHECKING:
    from pathlib import Path

    from agent33.skills.definition import SkillDefinition

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Central registry for skill discovery, loading, and retrieval."""

    def __init__(self) -> None:
        self._skills: dict[str, SkillDefinition] = {}

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self, path: Path) -> int:
        """Scan a directory for skill definitions.

        Supports:
        - Single YAML files: ``skills/my-skill.yaml``
        - Directories with SKILL.md or skill.yaml: ``skills/my-skill/SKILL.md``

        Returns the number of skills loaded.
        """
        if not path.is_dir():
            logger.warning("Skill directory not found: %s", path)
            return 0

        return self._discover_path(path)

    def _discover_path(self, path: Path) -> int:
        """Recursively scan a directory tree for skill definitions."""
        loaded = 0
        if self._directory_contains_skill_definition(path):
            try:
                skill = load_from_directory(path)
                self.register(skill)
                return 1
            except Exception:
                logger.warning("Failed to load skill from %s", path, exc_info=True)
                return 0

        for entry in sorted(path.iterdir()):
            try:
                if entry.is_dir():
                    loaded += self._discover_path(entry)
                elif entry.suffix in (".yaml", ".yml"):
                    skill = load_from_yaml(entry)
                    self.register(skill)
                    loaded += 1
                elif entry.name == "SKILL.md":
                    skill = load_from_skillmd(entry)
                    self.register(skill)
                    loaded += 1
            except Exception:
                logger.warning("Failed to load skill from %s", entry, exc_info=True)

        return loaded

    @staticmethod
    def _directory_contains_skill_definition(path: Path) -> bool:
        """Return True when the directory itself is a skill root."""
        return any(
            (path / candidate).is_file() for candidate in ("SKILL.md", "skill.yaml", "skill.yml")
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def register(self, skill: SkillDefinition) -> None:
        """Register a skill definition."""
        if skill.name in self._skills:
            logger.info(
                "Replacing existing skill '%s' (version %s -> %s)",
                skill.name,
                self._skills[skill.name].version,
                skill.version,
            )
        self._skills[skill.name] = skill

    def get(self, name: str) -> SkillDefinition | None:
        """Look up a skill by name."""
        return self._skills.get(name)

    def remove(self, name: str) -> bool:
        """Remove a skill from the registry. Returns True if it existed."""
        return self._skills.pop(name, None) is not None

    def list_all(self) -> list[SkillDefinition]:
        """Return all registered skills sorted by name."""
        return sorted(self._skills.values(), key=lambda s: s.name)

    @property
    def count(self) -> int:
        """Number of registered skills."""
        return len(self._skills)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def find_by_tag(self, tag: str) -> list[SkillDefinition]:
        """Find skills that have a specific tag."""
        return [s for s in self._skills.values() if tag in s.tags]

    def find_by_tool(self, tool_name: str) -> list[SkillDefinition]:
        """Find skills that allow a specific tool."""
        return [s for s in self._skills.values() if tool_name in s.allowed_tools]

    def search(self, query: str) -> list[SkillDefinition]:
        """Simple text search across skill names, descriptions, and tags."""
        query_lower = query.lower()
        results: list[SkillDefinition] = []
        for skill in self._skills.values():
            if (
                query_lower in skill.name.lower()
                or query_lower in skill.description.lower()
                or query_lower in skill.category.lower()
                or query_lower in skill.provenance.lower()
                or any(query_lower in t.lower() for t in skill.tags)
            ):
                results.append(skill)
        return sorted(results, key=lambda s: s.name)

    def search_ranked(self, query: str, top_k: int = 3) -> list[tuple[SkillDefinition, float]]:
        """BM25-scored search across skill names, descriptions, and tags.

        Builds a transient ``BM25Index`` over the current registry contents,
        scores each skill against *query*, and returns the top *top_k* results
        as ``(SkillDefinition, score)`` tuples sorted by descending score.
        """
        if not self._skills:
            return []

        index = BM25Index()
        ordered_skills: list[SkillDefinition] = list(self._skills.values())

        for skill in ordered_skills:
            document = " ".join(
                part for part in (skill.name, skill.description, " ".join(skill.tags)) if part
            )
            index.add_document(document, metadata={"name": skill.name})

        results = index.search(query, top_k=top_k)
        return [(ordered_skills[r.doc_index], r.score) for r in results]

    # ------------------------------------------------------------------
    # Progressive Disclosure
    # ------------------------------------------------------------------

    def get_metadata_only(self, name: str) -> dict[str, str] | None:
        """L0: Return only name + description (for context budget)."""
        skill = self._skills.get(name)
        if skill is None:
            return None
        return {"name": skill.name, "description": skill.description}

    def get_full_instructions(self, name: str) -> str | None:
        """L1: Return full markdown instructions."""
        skill = self._skills.get(name)
        if skill is None:
            return None
        return skill.instructions

    def get_supporting_files(self, name: str) -> list[str]:
        """Return relative paths to supporting files under the skill directory.

        Scans for files inside conventional subdirectories:
        ``references/``, ``templates/``, ``scripts/``, ``assets/``.

        Returns an empty list if the skill is not found, has no
        ``base_path``, or has no matching subdirectories.
        """
        from pathlib import Path as _Path

        skill = self._skills.get(name)
        if skill is None or skill.base_path is None:
            return []

        supporting: list[str] = []
        for subdir_name in ("references", "templates", "scripts", "assets"):
            subdir = skill.base_path / subdir_name
            if not subdir.is_dir():
                continue
            for child in sorted(subdir.rglob("*")):
                if child.is_file():
                    rel = child.relative_to(skill.base_path)
                    supporting.append(str(_Path(rel).as_posix()))

        return supporting

    def get_resource(self, name: str, resource_path: str) -> str | None:
        """L2: Load a specific bundled resource on demand.

        Returns the file content or None if not found.
        """
        skill = self._skills.get(name)
        if skill is None or skill.base_path is None:
            return None

        target = (skill.base_path / resource_path).resolve()
        base = skill.base_path.resolve()

        # Path traversal check
        try:
            target.relative_to(base)
        except ValueError:
            logger.warning(
                "Skill resource path traversal blocked: %s (base: %s)",
                target,
                base,
            )
            return None

        if not target.is_file():
            return None

        try:
            return target.read_text(encoding="utf-8")
        except OSError:
            return None
