"""Shared connector boundary models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ConnectorRequest:
    """Envelope passed through connector middleware chains."""

    connector: str
    operation: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
