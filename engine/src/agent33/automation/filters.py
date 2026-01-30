"""CA-013: Artifact Filtering Module."""

from __future__ import annotations

import fnmatch
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Artifact:
    """Represents a filterable artifact."""

    id: str
    name: str
    artifact_type: str = ""
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class ArtifactFilter:
    """Composable artifact filter supporting glob, regex, and predicate-based filtering.

    Filters are accumulated and applied in order via ``apply()``.
    """

    def __init__(self) -> None:
        self._include_patterns: list[str] = []
        self._exclude_patterns: list[str] = []
        self._type_filter: list[str] = []
        self._max_age: float | None = None
        self._predicates: list[Callable[[Artifact], bool]] = []

    def include(self, patterns: list[str]) -> ArtifactFilter:
        """Add glob include patterns (matched against artifact name).

        Parameters
        ----------
        patterns:
            Glob patterns like ``["*.py", "build-*"]``.
        """
        self._include_patterns.extend(patterns)
        return self

    def exclude(self, patterns: list[str]) -> ArtifactFilter:
        """Add glob exclude patterns.

        Parameters
        ----------
        patterns:
            Glob patterns to exclude.
        """
        self._exclude_patterns.extend(patterns)
        return self

    def by_type(self, types: list[str]) -> ArtifactFilter:
        """Filter to only artifacts of the given types.

        Parameters
        ----------
        types:
            Allowed artifact type strings.
        """
        self._type_filter.extend(types)
        return self

    def by_age(self, max_age: float) -> ArtifactFilter:
        """Filter to artifacts created within ``max_age`` seconds.

        Parameters
        ----------
        max_age:
            Maximum age in seconds.
        """
        self._max_age = max_age
        return self

    def by_regex(self, pattern: str) -> ArtifactFilter:
        """Filter by regex pattern matched against artifact name.

        Parameters
        ----------
        pattern:
            Regular expression string.
        """
        compiled = re.compile(pattern)
        self._predicates.append(lambda a: compiled.search(a.name) is not None)
        return self

    def by_predicate(self, predicate: Callable[[Artifact], bool]) -> ArtifactFilter:
        """Add a custom predicate filter.

        Parameters
        ----------
        predicate:
            Callable that returns True for artifacts to keep.
        """
        self._predicates.append(predicate)
        return self

    def apply(self, artifacts: list[Artifact]) -> list[Artifact]:
        """Apply all configured filters and return matching artifacts.

        Parameters
        ----------
        artifacts:
            Input list of artifacts.

        Returns
        -------
        list[Artifact]
            Filtered artifacts.
        """
        result = list(artifacts)

        # Include filter
        if self._include_patterns:
            result = [
                a for a in result
                if any(fnmatch.fnmatch(a.name, p) for p in self._include_patterns)
            ]

        # Exclude filter
        if self._exclude_patterns:
            result = [
                a for a in result
                if not any(fnmatch.fnmatch(a.name, p) for p in self._exclude_patterns)
            ]

        # Type filter
        if self._type_filter:
            result = [a for a in result if a.artifact_type in self._type_filter]

        # Age filter
        if self._max_age is not None:
            cutoff = time.time() - self._max_age
            result = [a for a in result if a.created_at >= cutoff]

        # Predicate filters (including regex)
        for pred in self._predicates:
            result = [a for a in result if pred(a)]

        return result
