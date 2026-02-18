"""Operations hub aggregation and lifecycle controls."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from agent33.api.routes.autonomy import get_autonomy_service
from agent33.api.routes.improvements import get_improvement_service
from agent33.api.routes.traces import get_trace_collector
from agent33.api.routes.workflows import get_execution_history
from agent33.autonomy.models import BudgetState
from agent33.autonomy.service import BudgetNotFoundError
from agent33.improvement.models import IntakeStatus
from agent33.observability.trace_collector import TraceNotFoundError
from agent33.observability.trace_models import TraceStatus

_DEFAULT_INCLUDE = frozenset({"traces", "budgets", "improvements", "workflows"})
_MAX_LIMIT = 100


class ProcessNotFoundError(Exception):
    """Raised when an operations process cannot be found."""


class UnsupportedControlError(Exception):
    """Raised when a lifecycle action is unsupported for a process type."""


class OperationsHubService:
    """Aggregate operations data and execute lifecycle controls."""

    def get_hub(
        self,
        *,
        tenant_id: str = "",
        include: set[str] | None = None,
        since: datetime | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Return normalized operations processes across subsystems."""
        now = datetime.now(UTC)
        since_dt = since or (now - timedelta(hours=24))
        include_set = include if include is not None else set(_DEFAULT_INCLUDE)
        capped_limit = max(1, min(limit, _MAX_LIMIT))

        processes: list[dict[str, Any]] = []
        if "traces" in include_set:
            processes.extend(
                self._trace_processes(
                    tenant_id=tenant_id,
                    since=since_dt,
                    status=status,
                    limit=capped_limit,
                )
            )
        if "budgets" in include_set and not tenant_id:
            processes.extend(
                self._budget_processes(
                    since=since_dt,
                    status=status,
                    limit=capped_limit,
                )
            )
        if "improvements" in include_set and not tenant_id:
            processes.extend(
                self._improvement_processes(since=since_dt, status=status, limit=capped_limit)
            )
        if "workflows" in include_set and not tenant_id:
            processes.extend(
                self._workflow_processes(
                    since=since_dt,
                    status=status,
                    limit=capped_limit,
                )
            )

        if status is not None:
            processes = [item for item in processes if item["status"] == status]

        processes.sort(key=lambda item: item["_started_at"], reverse=True)
        processes = processes[:capped_limit]
        for item in processes:
            item.pop("_started_at", None)

        return {
            "timestamp": now.isoformat(),
            "active_count": len(processes),
            "processes": processes,
        }

    def get_process(self, process_id: str, *, tenant_id: str = "") -> dict[str, Any]:
        """Return process detail for trace, budget, improvement, or workflow IDs."""
        if process_id.startswith("workflow:"):
            if tenant_id:
                raise ProcessNotFoundError(process_id)
            return self._workflow_detail(process_id)

        trace_collector = get_trace_collector()
        try:
            trace = trace_collector.get_trace(process_id)
            if tenant_id and trace.tenant_id != tenant_id:
                raise ProcessNotFoundError(process_id)
            return self._trace_detail(trace)
        except TraceNotFoundError:
            pass

        if not tenant_id:
            autonomy_service = get_autonomy_service()
            try:
                budget = autonomy_service.get_budget(process_id)
                return self._budget_detail(budget)
            except BudgetNotFoundError:
                pass

            improvement = get_improvement_service().get_intake(process_id)
            if improvement is not None:
                return self._improvement_detail(improvement)

        raise ProcessNotFoundError(process_id)

    def control_process(
        self, process_id: str, action: str, *, tenant_id: str = ""
    ) -> dict[str, Any]:
        """Control supported process lifecycles for traces and budgets."""
        trace_collector = get_trace_collector()
        try:
            trace = trace_collector.get_trace(process_id)
            if tenant_id and trace.tenant_id != tenant_id:
                raise ProcessNotFoundError(process_id)
            if action != "cancel":
                raise UnsupportedControlError(
                    f"Action '{action}' is unsupported for trace process"
                )
            trace_collector.complete_trace(
                process_id,
                status=TraceStatus.CANCELLED,
                failure_code="F-CAN",
                failure_message="Cancelled via operations hub",
            )
            return self.get_process(process_id, tenant_id=tenant_id)
        except TraceNotFoundError:
            pass

        if tenant_id:
            raise ProcessNotFoundError(process_id)

        autonomy_service = get_autonomy_service()
        try:
            _budget = autonomy_service.get_budget(process_id)
        except BudgetNotFoundError as exc:
            if process_id.startswith("workflow:"):
                raise UnsupportedControlError(
                    "Lifecycle control is not supported for workflow history records"
                ) from exc
            if get_improvement_service().get_intake(process_id) is not None:
                raise UnsupportedControlError(
                    "Lifecycle control is not supported for improvement intake records"
                ) from exc
            raise ProcessNotFoundError(process_id) from exc

        if action == "pause":
            autonomy_service.suspend(process_id)
        elif action == "resume":
            autonomy_service.activate(process_id)
        elif action == "cancel":
            # Prefer EXPIRED for cancellation semantics, fall back to COMPLETED if needed.
            try:
                autonomy_service.transition(process_id, BudgetState.EXPIRED)
            except Exception:
                autonomy_service.complete(process_id)
        else:
            raise UnsupportedControlError(f"Action '{action}' is unsupported for budget process")
        return self.get_process(process_id)

    def _trace_processes(
        self, *, tenant_id: str, since: datetime, status: str | None, limit: int
    ) -> list[dict[str, Any]]:
        collector = get_trace_collector()
        trace_status = TraceStatus.RUNNING if status is None else None
        traces = collector.list_traces(
            tenant_id=tenant_id or None,
            status=trace_status,
            limit=limit,
        )

        processes: list[dict[str, Any]] = []
        for trace in traces:
            if trace.started_at < since:
                continue
            processes.append(
                {
                    "id": trace.trace_id,
                    "type": "trace",
                    "status": trace.outcome.status.value,
                    "started_at": trace.started_at.isoformat(),
                    "name": trace.task_id or trace.trace_id,
                    "metadata": {
                        "tenant_id": trace.tenant_id,
                        "agent_id": trace.context.agent_id,
                        "session_id": trace.session_id,
                        "run_id": trace.run_id,
                    },
                    "_started_at": trace.started_at,
                }
            )
        return processes

    def _budget_processes(
        self, *, since: datetime, status: str | None, limit: int
    ) -> list[dict[str, Any]]:
        autonomy_service = get_autonomy_service()
        state_filter = BudgetState.ACTIVE if status is None else None
        budgets = autonomy_service.list_budgets(state=state_filter, limit=limit)

        processes: list[dict[str, Any]] = []
        for budget in budgets:
            if budget.created_at < since:
                continue
            processes.append(
                {
                    "id": budget.budget_id,
                    "type": "autonomy_budget",
                    "status": budget.state.value,
                    "started_at": budget.created_at.isoformat(),
                    "name": budget.task_id or budget.budget_id,
                    "metadata": {
                        "agent_id": budget.agent_id,
                    },
                    "_started_at": budget.created_at,
                }
            )
        return processes

    def _improvement_processes(
        self, *, since: datetime, status: str | None, limit: int
    ) -> list[dict[str, Any]]:
        service = get_improvement_service()
        intake_status = IntakeStatus.ANALYZING if status is None else None
        intakes = service.list_intakes(status=intake_status)

        processes: list[dict[str, Any]] = []
        for intake in intakes:
            if intake.submitted_at < since:
                continue
            processes.append(
                {
                    "id": intake.intake_id,
                    "type": "improvement_intake",
                    "status": intake.disposition.status.value,
                    "started_at": intake.submitted_at.isoformat(),
                    "name": intake.content.title,
                    "metadata": {
                        "research_type": intake.classification.research_type.value,
                        "urgency": intake.classification.urgency.value,
                    },
                    "_started_at": intake.submitted_at,
                }
            )
        processes.sort(key=lambda item: item["_started_at"], reverse=True)
        return processes[:limit]

    def _workflow_processes(
        self, *, since: datetime, status: str | None, limit: int
    ) -> list[dict[str, Any]]:
        history = list(get_execution_history())
        processes: list[dict[str, Any]] = []
        for entry in reversed(history):
            timestamp = float(entry.get("timestamp", 0))
            started_at = datetime.fromtimestamp(timestamp, UTC)
            if started_at < since:
                continue
            workflow_name = entry.get("workflow_name", "")
            processes.append(
                {
                    "id": f"workflow:{workflow_name}:{int(timestamp)}",
                    "type": "workflow",
                    "status": str(entry.get("status", "unknown")),
                    "started_at": started_at.isoformat(),
                    "name": workflow_name or "workflow",
                    "metadata": {
                        "trigger_type": entry.get("trigger_type"),
                        "duration_ms": entry.get("duration_ms"),
                        "error": entry.get("error"),
                        "job_id": entry.get("job_id"),
                    },
                    "_started_at": started_at,
                }
            )
            if len(processes) >= limit:
                break
        return processes

    def _trace_detail(self, trace: Any) -> dict[str, Any]:
        return {
            "id": trace.trace_id,
            "type": "trace",
            "status": trace.outcome.status.value,
            "started_at": trace.started_at.isoformat(),
            "name": trace.task_id or trace.trace_id,
            "metadata": {
                "tenant_id": trace.tenant_id,
                "agent_id": trace.context.agent_id,
                "session_id": trace.session_id,
                "run_id": trace.run_id,
            },
            "actions": [
                {
                    "step_id": step.step_id,
                    "action_count": len(step.actions),
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                }
                for step in trace.execution
            ],
        }

    def _budget_detail(self, budget: Any) -> dict[str, Any]:
        return {
            "id": budget.budget_id,
            "type": "autonomy_budget",
            "status": budget.state.value,
            "started_at": budget.created_at.isoformat(),
            "name": budget.task_id or budget.budget_id,
            "metadata": {
                "agent_id": budget.agent_id,
                "approved_by": budget.approved_by,
            },
        }

    def _improvement_detail(self, intake: Any) -> dict[str, Any]:
        return {
            "id": intake.intake_id,
            "type": "improvement_intake",
            "status": intake.disposition.status.value,
            "started_at": intake.submitted_at.isoformat(),
            "name": intake.content.title,
            "metadata": {
                "research_type": intake.classification.research_type.value,
                "urgency": intake.classification.urgency.value,
            },
        }

    def _workflow_detail(self, process_id: str) -> dict[str, Any]:
        parts = process_id.split(":", 2)
        if len(parts) != 3:
            raise ProcessNotFoundError(process_id)
        workflow_name = parts[1]
        target_ts = int(parts[2])

        for entry in get_execution_history():
            timestamp = int(float(entry.get("timestamp", 0)))
            if entry.get("workflow_name") == workflow_name and timestamp == target_ts:
                started_at = datetime.fromtimestamp(timestamp, UTC)
                return {
                    "id": process_id,
                    "type": "workflow",
                    "status": str(entry.get("status", "unknown")),
                    "started_at": started_at.isoformat(),
                    "name": workflow_name or "workflow",
                    "metadata": {
                        "trigger_type": entry.get("trigger_type"),
                        "duration_ms": entry.get("duration_ms"),
                        "error": entry.get("error"),
                        "job_id": entry.get("job_id"),
                    },
                }
        raise ProcessNotFoundError(process_id)
