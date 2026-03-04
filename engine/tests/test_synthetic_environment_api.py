"""API tests for synthetic environment generation routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agent33.api.routes import synthetic_envs
from agent33.evaluation.synthetic_envs.service import SyntheticEnvironmentService
from agent33.main import app
from agent33.security.auth import create_access_token


def _client(scopes: list[str]) -> TestClient:
    root = Path(__file__).resolve().parents[1]
    synthetic_envs.set_synthetic_environment_service(
        SyntheticEnvironmentService(
            workflow_dir=root / "workflow-definitions",
            tool_dir=root / "tool-definitions",
        )
    )
    token = create_access_token("synthetic-env-user", scopes=scopes)
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


def test_list_synthetic_workflows_requires_read_scope() -> None:
    client = _client(scopes=[])

    response = client.get("/v1/evaluation/synthetic-environments/workflows")

    assert response.status_code == 403


def test_list_synthetic_workflows_returns_catalog() -> None:
    client = _client(scopes=["workflows:read"])

    response = client.get("/v1/evaluation/synthetic-environments/workflows")

    assert response.status_code == 200
    payload = response.json()
    assert any(item["workflow_name"] == "code-review-pipeline" for item in payload)


def test_generate_and_fetch_synthetic_bundle() -> None:
    client = _client(scopes=["workflows:read", "tools:execute"])

    create_response = client.post(
        "/v1/evaluation/synthetic-environments/bundles",
        json={
            "workflow_names": ["incident-triage-loop"],
            "variations_per_workflow": 2,
        },
    )

    assert create_response.status_code == 201
    bundle = create_response.json()
    assert bundle["source_workflows"] == ["incident-triage-loop"]
    assert len(bundle["environments"]) == 2

    fetch_response = client.get(
        f"/v1/evaluation/synthetic-environments/bundles/{bundle['bundle_id']}"
    )

    assert fetch_response.status_code == 200
    fetched = fetch_response.json()
    assert fetched["bundle_id"] == bundle["bundle_id"]
