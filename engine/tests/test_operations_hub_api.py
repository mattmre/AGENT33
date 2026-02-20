"""Phase 27 Stage 1 tests for operations hub backend surfaces."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from agent33.api.routes.autonomy import get_autonomy_service
from agent33.api.routes.improvements import get_improvement_service
from agent33.api.routes.traces import get_trace_collector
from agent33.api.routes.workflows import get_execution_history
from agent33.autonomy.models import BudgetState
from agent33.improvement.models import IntakeContent, IntakeStatus, ResearchIntake
from agent33.main import app
from agent33.observability.trace_models import TraceStatus
from agent33.security.auth import create_access_token


def _client(scopes: list[str], *, tenant_id: str = "") -> TestClient:
    token = create_access_token("operations-user", scopes=scopes, tenant_id=tenant_id)
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture(autouse=True)
def reset_operations_sources() -> None:
    trace_collector = get_trace_collector()
    trace_collector._traces.clear()
    trace_collector._failures.clear()

    autonomy_service = get_autonomy_service()
    autonomy_service._budgets.clear()
    autonomy_service._enforcers.clear()
    autonomy_service._escalations.clear()

    improvement_service = get_improvement_service()
    improvement_service._intakes.clear()

    get_execution_history().clear()
    yield

    trace_collector._traces.clear()
    trace_collector._failures.clear()
    autonomy_service._budgets.clear()
    autonomy_service._enforcers.clear()
    autonomy_service._escalations.clear()
    improvement_service._intakes.clear()
    get_execution_history().clear()


@pytest.fixture
def anonymous_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def read_client() -> TestClient:
    return _client(["workflows:read"])


@pytest.fixture
def execute_client() -> TestClient:
    return _client(["workflows:execute"])


@pytest.fixture
def no_scope_client() -> TestClient:
    return _client([])


@pytest.fixture
def tenant_read_client() -> TestClient:
    return _client(["workflows:read"], tenant_id="tenant-alpha")


@pytest.fixture
def seeded_state() -> dict[str, str]:
    trace_collector = get_trace_collector()
    trace_alpha = trace_collector.start_trace(
        task_id="trace-alpha",
        tenant_id="tenant-alpha",
        agent_id="agent-alpha",
    )
    trace_beta = trace_collector.start_trace(
        task_id="trace-beta",
        tenant_id="tenant-beta",
        agent_id="agent-beta",
    )
    trace_collector.complete_trace(trace_beta.trace_id, status=TraceStatus.COMPLETED)

    autonomy_service = get_autonomy_service()
    active_budget = autonomy_service.create_budget(task_id="budget-active", agent_id="agent-a")
    autonomy_service.activate(active_budget.budget_id)
    draft_budget = autonomy_service.create_budget(task_id="budget-draft", agent_id="agent-b")

    improvements = get_improvement_service()
    intake = improvements.submit_intake(
        ResearchIntake(content=IntakeContent(title="Improve workflow latency"))
    )
    improvements.transition_intake(intake.intake_id, IntakeStatus.TRIAGED)
    improvements.transition_intake(intake.intake_id, IntakeStatus.ANALYZING)

    now_ts = datetime.now(UTC).timestamp()
    history = get_execution_history()
    history.append(
        {
            "workflow_name": "wf-recent",
            "trigger_type": "manual",
            "status": "completed",
            "duration_ms": 420,
            "timestamp": now_ts - 60,
            "error": None,
            "job_id": None,
        }
    )
    history.append(
        {
            "workflow_name": "wf-old",
            "trigger_type": "scheduled",
            "status": "failed",
            "duration_ms": 1200,
            "timestamp": now_ts - (30 * 3600),
            "error": "timeout",
            "job_id": "job-old",
        }
    )

    return {
        "trace_alpha_id": trace_alpha.trace_id,
        "trace_beta_id": trace_beta.trace_id,
        "active_budget_id": active_budget.budget_id,
        "draft_budget_id": draft_budget.budget_id,
        "intake_id": intake.intake_id,
    }


def test_hub_requires_auth(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/v1/operations/hub")
    assert response.status_code == 401


def test_hub_requires_workflows_read_scope(no_scope_client: TestClient) -> None:
    response = no_scope_client.get("/v1/operations/hub")
    assert response.status_code == 403
    assert "workflows:read" in response.json()["detail"]


def test_control_requires_workflows_execute_scope(
    read_client: TestClient, seeded_state: dict[str, str]
) -> None:
    response = read_client.post(
        f"/v1/operations/processes/{seeded_state['trace_alpha_id']}/control",
        json={"action": "cancel"},
    )
    assert response.status_code == 403
    assert "workflows:execute" in response.json()["detail"]


def test_hub_aggregates_expected_process_types(
    read_client: TestClient, seeded_state: dict[str, str]
) -> None:
    response = read_client.get("/v1/operations/hub")
    assert response.status_code == 200
    payload = response.json()
    process_types = {item["type"] for item in payload["processes"]}
    assert {"trace", "autonomy_budget", "improvement_intake", "workflow"} <= process_types


def test_hub_include_filter_limits_sources(
    read_client: TestClient, seeded_state: dict[str, str]
) -> None:
    response = read_client.get("/v1/operations/hub?include=traces,budgets")
    assert response.status_code == 200
    process_types = {item["type"] for item in response.json()["processes"]}
    assert process_types <= {"trace", "autonomy_budget"}


def test_hub_invalid_include_returns_400(read_client: TestClient) -> None:
    response = read_client.get("/v1/operations/hub?include=traces,invalid")
    assert response.status_code == 400
    assert "Invalid include values" in response.json()["detail"]


def test_hub_since_filter_excludes_old_workflows(
    read_client: TestClient, seeded_state: dict[str, str]
) -> None:
    since = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    response = read_client.get(
        "/v1/operations/hub",
        params={"include": "workflows", "since": since},
    )
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["processes"]}
    assert "wf-recent" in names
    assert "wf-old" not in names


def test_hub_status_filter_returns_running_only(
    read_client: TestClient, seeded_state: dict[str, str]
) -> None:
    response = read_client.get("/v1/operations/hub?status=running")
    assert response.status_code == 200
    processes = response.json()["processes"]
    assert processes
    assert all(item["status"] == "running" for item in processes)


def test_hub_tenant_filter_excludes_non_tenant_sources(
    tenant_read_client: TestClient, seeded_state: dict[str, str]
) -> None:
    response = tenant_read_client.get("/v1/operations/hub")
    assert response.status_code == 200
    processes = response.json()["processes"]
    assert processes
    assert all(item["type"] == "trace" for item in processes)
    assert all(item["metadata"]["tenant_id"] == "tenant-alpha" for item in processes)


def test_get_process_returns_trace_detail(
    read_client: TestClient, seeded_state: dict[str, str]
) -> None:
    response = read_client.get(f"/v1/operations/processes/{seeded_state['trace_alpha_id']}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "trace"
    assert payload["id"] == seeded_state["trace_alpha_id"]


def test_get_process_missing_returns_404(read_client: TestClient) -> None:
    response = read_client.get("/v1/operations/processes/missing-id")
    assert response.status_code == 404


def test_control_cancel_trace_marks_trace_cancelled(
    execute_client: TestClient, seeded_state: dict[str, str]
) -> None:
    trace_id = seeded_state["trace_alpha_id"]
    response = execute_client.post(
        f"/v1/operations/processes/{trace_id}/control",
        json={"action": "cancel"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    trace = get_trace_collector().get_trace(trace_id)
    assert trace.outcome.status == TraceStatus.CANCELLED


def test_control_budget_pause_resume_cancel(
    execute_client: TestClient, seeded_state: dict[str, str]
) -> None:
    budget_id = seeded_state["active_budget_id"]

    pause_response = execute_client.post(
        f"/v1/operations/processes/{budget_id}/control",
        json={"action": "pause"},
    )
    assert pause_response.status_code == 200
    assert pause_response.json()["status"] == "suspended"

    resume_response = execute_client.post(
        f"/v1/operations/processes/{budget_id}/control",
        json={"action": "resume"},
    )
    assert resume_response.status_code == 200
    assert resume_response.json()["status"] == "active"

    cancel_response = execute_client.post(
        f"/v1/operations/processes/{budget_id}/control",
        json={"action": "cancel"},
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] in {"expired", "completed"}

    budget = get_autonomy_service().get_budget(budget_id)
    assert budget.state in {BudgetState.EXPIRED, BudgetState.COMPLETED}


def test_control_improvement_returns_409(
    execute_client: TestClient, seeded_state: dict[str, str]
) -> None:
    response = execute_client.post(
        f"/v1/operations/processes/{seeded_state['intake_id']}/control",
        json={"action": "cancel"},
    )
    assert response.status_code == 409


def test_control_workflow_returns_409(
    execute_client: TestClient, read_client: TestClient, seeded_state: dict[str, str]
) -> None:
    hub = read_client.get("/v1/operations/hub?include=workflows").json()
    workflow_process = next(item for item in hub["processes"] if item["type"] == "workflow")
    response = execute_client.post(
        f"/v1/operations/processes/{workflow_process['id']}/control",
        json={"action": "cancel"},
    )
    assert response.status_code == 409


def test_control_missing_process_returns_404(execute_client: TestClient) -> None:
    response = execute_client.post(
        "/v1/operations/processes/missing-id/control",
        json={"action": "cancel"},
    )
    assert response.status_code == 404
