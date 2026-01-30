"""Dashboard API routes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from agent33.observability.lineage import ExecutionLineage
from agent33.observability.metrics import MetricsCollector

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])

# Module-level singletons; replaced at app startup if needed.
_metrics = MetricsCollector()
_lineage = ExecutionLineage()

_TEMPLATE_PATH = Path(__file__).resolve().parents[4] / "templates" / "dashboard.html"


def set_metrics(collector: MetricsCollector) -> None:
    """Swap the global metrics collector (called during app init)."""
    global _metrics
    _metrics = collector


def set_lineage(lineage: ExecutionLineage) -> None:
    """Swap the global lineage tracker (called during app init)."""
    global _lineage
    _lineage = lineage


@router.get("/", response_class=HTMLResponse)
async def dashboard_page() -> HTMLResponse:
    """Serve the HTML dashboard."""
    if _TEMPLATE_PATH.exists():
        content = _TEMPLATE_PATH.read_text(encoding="utf-8")
    else:
        content = "<html><body><h1>AGENT-33 Dashboard</h1><p>Template not found.</p></body></html>"
    return HTMLResponse(content=content)


@router.get("/metrics")
async def dashboard_metrics() -> dict[str, Any]:
    """Return current metrics summary as JSON."""
    return _metrics.get_summary()


@router.get("/lineage/{workflow_id}")
async def dashboard_lineage(workflow_id: str) -> list[dict[str, Any]]:
    """Return lineage records for a workflow."""
    records = _lineage.query(workflow_id)
    return [
        {
            "workflow_id": r.workflow_id,
            "step_id": r.step_id,
            "action": r.action,
            "inputs_hash": r.inputs_hash,
            "outputs_hash": r.outputs_hash,
            "parent_id": r.parent_id,
            "timestamp": r.timestamp,
        }
        for r in records
    ]
