"""SQLite-backed persistence for outcome events (P72)."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from agent33.outcomes.models import OutcomeEvent, OutcomeMetricType

if TYPE_CHECKING:
    from pathlib import Path

logger = structlog.get_logger()

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS outcome_events (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    event_type TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    value REAL NOT NULL,
    occurred_at TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_tenant_occurred
    ON outcome_events(tenant_id, occurred_at);
"""


class OutcomePersistence:
    """SQLite-backed persistence for outcome events."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Create outcomes table if not exists."""
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()

    def save_event(self, event: OutcomeEvent) -> None:
        """Persist a single outcome event."""
        self._conn.execute(
            """INSERT OR REPLACE INTO outcome_events
               (id, tenant_id, domain, event_type, metric_type, value, occurred_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event.id,
                event.tenant_id,
                event.domain,
                event.event_type,
                event.metric_type.value,
                event.value,
                event.occurred_at.isoformat(),
                json.dumps(event.metadata),
            ),
        )
        self._conn.commit()

    def load_events(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        limit: int = 1000,
    ) -> list[OutcomeEvent]:
        """Load events from SQLite, optionally filtered by tenant and date."""
        if since is not None:
            cursor = self._conn.execute(
                """SELECT id, tenant_id, domain, event_type, metric_type,
                          value, occurred_at, metadata
                   FROM outcome_events
                   WHERE tenant_id = ? AND occurred_at >= ?
                   ORDER BY occurred_at DESC
                   LIMIT ?""",
                (tenant_id, since.isoformat(), limit),
            )
        else:
            cursor = self._conn.execute(
                """SELECT id, tenant_id, domain, event_type, metric_type,
                          value, occurred_at, metadata
                   FROM outcome_events
                   WHERE tenant_id = ?
                   ORDER BY occurred_at DESC
                   LIMIT ?""",
                (tenant_id, limit),
            )
        rows = cursor.fetchall()
        return [self._row_to_event(row) for row in rows]

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> OutcomeEvent:
        """Convert a database row to an OutcomeEvent."""
        occurred_at_str: str = row["occurred_at"]
        # Handle both timezone-aware and naive ISO formats
        if occurred_at_str.endswith("+00:00") or occurred_at_str.endswith("Z"):
            occurred_at = datetime.fromisoformat(occurred_at_str.replace("Z", "+00:00"))
        else:
            occurred_at = datetime.fromisoformat(occurred_at_str).replace(tzinfo=UTC)
        return OutcomeEvent(
            id=row["id"],
            tenant_id=row["tenant_id"],
            domain=row["domain"],
            event_type=row["event_type"],
            metric_type=OutcomeMetricType(row["metric_type"]),
            value=row["value"],
            occurred_at=occurred_at,
            metadata=json.loads(row["metadata"]),
        )

    def close(self) -> None:
        """Close the SQLite connection."""
        try:
            self._conn.close()
        except Exception:
            logger.warning("outcome_persistence_close_error", exc_info=True)
