"""SQLite persistence for the P-PACK v3 A/B harness."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from agent33.evaluation.ppack_ab_models import PPackABAssignment, PPackABReport


class PPackABPersistence:
    """Persist A/B assignments and generated reports."""

    def __init__(self, db_path: str | Path) -> None:
        path_text = str(db_path)
        if path_text != ":memory:":
            Path(path_text).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path_text, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._configure_connection(path_text)
        self._create_schema()

    def close(self) -> None:
        self._conn.close()

    def _configure_connection(self, path_text: str) -> None:
        self._conn.execute("PRAGMA busy_timeout = 5000")
        if path_text != ":memory:":
            self._conn.execute("PRAGMA journal_mode = WAL")

    def _create_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ppack_ab_assignments (
                assignment_id TEXT PRIMARY KEY,
                experiment_key TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                variant TEXT NOT NULL,
                assignment_hash TEXT NOT NULL,
                assigned_at TEXT NOT NULL,
                UNIQUE(experiment_key, tenant_id, session_id)
            );

            CREATE INDEX IF NOT EXISTS idx_ppack_ab_assignments_tenant
            ON ppack_ab_assignments (tenant_id, experiment_key, assigned_at DESC);

            CREATE TABLE IF NOT EXISTS ppack_ab_reports (
                report_id TEXT PRIMARY KEY,
                experiment_key TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                markdown TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_ppack_ab_reports_tenant
            ON ppack_ab_reports (tenant_id, experiment_key, generated_at DESC);
            """
        )
        self._conn.commit()

    def save_assignment(self, assignment: PPackABAssignment) -> PPackABAssignment:
        self._conn.execute(
            """
            INSERT INTO ppack_ab_assignments (
                assignment_id,
                experiment_key,
                tenant_id,
                session_id,
                variant,
                assignment_hash,
                assigned_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(experiment_key, tenant_id, session_id) DO UPDATE SET
                variant = excluded.variant,
                assignment_hash = excluded.assignment_hash,
                assigned_at = excluded.assigned_at
            """,
            (
                assignment.assignment_id,
                assignment.experiment_key,
                assignment.tenant_id,
                assignment.session_id,
                assignment.variant.value,
                assignment.assignment_hash,
                assignment.assigned_at.isoformat(),
            ),
        )
        self._conn.commit()
        stored = self.get_assignment(
            tenant_id=assignment.tenant_id,
            session_id=assignment.session_id,
            experiment_key=assignment.experiment_key,
        )
        if stored is None:
            raise RuntimeError("Failed to persist P-PACK A/B assignment")
        return stored

    def get_assignment(
        self, *, tenant_id: str, session_id: str, experiment_key: str
    ) -> PPackABAssignment | None:
        row = self._conn.execute(
            """
            SELECT assignment_id, experiment_key, tenant_id, session_id, variant,
                   assignment_hash, assigned_at
            FROM ppack_ab_assignments
            WHERE experiment_key = ? AND tenant_id = ? AND session_id = ?
            """,
            (experiment_key, tenant_id, session_id),
        ).fetchone()
        return self._hydrate_assignment(row) if row else None

    def list_assignments(self, *, tenant_id: str, experiment_key: str) -> list[PPackABAssignment]:
        rows = self._conn.execute(
            """
            SELECT assignment_id, experiment_key, tenant_id, session_id, variant,
                   assignment_hash, assigned_at
            FROM ppack_ab_assignments
            WHERE tenant_id = ? AND experiment_key = ?
            ORDER BY assigned_at DESC
            """,
            (tenant_id, experiment_key),
        ).fetchall()
        return [self._hydrate_assignment(row) for row in rows]

    def save_report(self, report: PPackABReport) -> PPackABReport:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO ppack_ab_reports (
                report_id,
                experiment_key,
                tenant_id,
                domain,
                generated_at,
                payload_json,
                markdown
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report.report_id,
                report.experiment_key,
                report.tenant_id,
                report.domain,
                report.generated_at.isoformat(),
                report.model_dump_json(),
                report.markdown,
            ),
        )
        self._conn.commit()
        stored = self.get_report(report.report_id)
        if stored is None:
            raise RuntimeError("Failed to persist P-PACK A/B report")
        return stored

    def get_report(self, report_id: str) -> PPackABReport | None:
        row = self._conn.execute(
            """
            SELECT payload_json
            FROM ppack_ab_reports
            WHERE report_id = ?
            """,
            (report_id,),
        ).fetchone()
        if row is None:
            return None
        return PPackABReport.model_validate(json.loads(row["payload_json"]))

    def _hydrate_assignment(self, row: sqlite3.Row) -> PPackABAssignment:
        return PPackABAssignment.model_validate(dict(row))
