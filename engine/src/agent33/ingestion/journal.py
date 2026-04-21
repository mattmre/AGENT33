"""Append-only transition journal for the candidate asset ingestion lifecycle.

Every lifecycle state transition is written to both an in-memory list and a
SQLite table (``ingestion_journal``), giving operators a durable, ordered audit
trail of all status changes with actor attribution.

CLEAN-ROOM RESTRICTION
=======================
No code in this file may originate from the EvoMap/Evolver project.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from agent33.ingestion.models import CandidateAsset, CandidateStatus

logger = structlog.get_logger()

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS ingestion_journal (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id    TEXT    NOT NULL,
    tenant_id   TEXT    NOT NULL,
    from_status TEXT    NOT NULL,
    to_status   TEXT    NOT NULL,
    operator    TEXT    NOT NULL,
    reason      TEXT    NOT NULL,
    occurred_at TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_journal_asset_id
    ON ingestion_journal(asset_id);
CREATE INDEX IF NOT EXISTS idx_journal_tenant_id
    ON ingestion_journal(tenant_id, occurred_at);
"""


class TransitionJournal:
    """Append-only log of every CandidateAsset lifecycle transition.

    Entries are stored both in-memory (for fast reads without hitting SQLite)
    and persisted to the ``ingestion_journal`` table so they survive process
    restarts.
    """

    def __init__(self, db_path: str) -> None:
        import os

        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._entries: list[dict[str, Any]] = []
        self._init_schema()
        self._hydrate()

    def _init_schema(self) -> None:
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()

    def _hydrate(self) -> None:
        """Load existing journal entries from SQLite into the in-memory list."""
        try:
            cursor = self._conn.execute("SELECT * FROM ingestion_journal ORDER BY occurred_at ASC")
            rows = cursor.fetchall()
            self._entries = [self._row_to_dict(row) for row in rows]
            logger.info("ingestion_journal_hydrated", count=len(self._entries))
        except sqlite3.ProgrammingError:
            logger.debug("ingestion_journal_hydrate_skipped", reason="connection_closed")

    def record(
        self,
        asset: CandidateAsset,
        from_status: CandidateStatus,
        *,
        operator: str,
        reason: str,
    ) -> None:
        """Append one transition entry.

        ``asset.status`` at the time of this call is used as ``to_status``.
        The entry is written to SQLite and appended to the in-memory list.
        """
        occurred_at = datetime.now(UTC).isoformat()
        entry: dict[str, Any] = {
            "asset_id": asset.id,
            "tenant_id": asset.tenant_id,
            "from_status": from_status.value,
            "to_status": asset.status.value,
            "operator": operator,
            "reason": reason,
            "occurred_at": occurred_at,
        }
        try:
            self._conn.execute(
                """INSERT INTO ingestion_journal
                   (asset_id, tenant_id, from_status, to_status, operator, reason, occurred_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry["asset_id"],
                    entry["tenant_id"],
                    entry["from_status"],
                    entry["to_status"],
                    entry["operator"],
                    entry["reason"],
                    entry["occurred_at"],
                ),
            )
            self._conn.commit()
        except sqlite3.ProgrammingError:
            logger.debug("ingestion_journal_write_skipped", reason="connection_closed")
        self._entries.append(entry)
        logger.info(
            "ingestion_journal_recorded",
            asset_id=asset.id,
            from_status=from_status.value,
            to_status=asset.status.value,
            operator=operator,
        )

    def entries_for(self, asset_id: str) -> list[dict[str, Any]]:
        """Return all journal entries for the given asset, ascending by occurred_at."""
        return [e for e in self._entries if e["asset_id"] == asset_id]

    def entries_for_tenant(self, tenant_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        """Return the most-recent ``limit`` entries for the given tenant, descending."""
        tenant_entries = [e for e in self._entries if e["tenant_id"] == tenant_id]
        # Sort descending and take the last `limit` items
        sorted_entries = sorted(tenant_entries, key=lambda e: e["occurred_at"], reverse=True)
        return sorted_entries[:limit]

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        try:
            self._conn.close()
        except Exception:
            logger.warning("ingestion_journal_close_error", exc_info=True)

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "asset_id": row["asset_id"],
            "tenant_id": row["tenant_id"],
            "from_status": row["from_status"],
            "to_status": row["to_status"],
            "operator": row["operator"],
            "reason": row["reason"],
            "occurred_at": row["occurred_at"],
        }
