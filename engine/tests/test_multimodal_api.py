"""Phase 29 Stage 1 tests for multimodal backend contracts."""

from __future__ import annotations

import asyncio
import base64

import pytest
from fastapi.testclient import TestClient

from agent33.api.routes.multimodal import _service
from agent33.main import app
from agent33.multimodal.models import ModalityType, MultimodalPolicy, RequestState
from agent33.security.auth import create_access_token


@pytest.fixture(autouse=True)
def reset_multimodal_service() -> None:
    _service._requests.clear()
    _service._results.clear()
    _service._policies.clear()
    yield
    _service._requests.clear()
    _service._results.clear()
    _service._policies.clear()


def _client(scopes: list[str], *, tenant_id: str = "tenant-a") -> TestClient:
    token = create_access_token("multimodal-user", scopes=scopes, tenant_id=tenant_id)
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def writer_client() -> TestClient:
    return _client(["multimodal:read", "multimodal:write"])


@pytest.fixture
def reader_client() -> TestClient:
    return _client(["multimodal:read"])


@pytest.fixture
def no_scope_client() -> TestClient:
    return _client([])


@pytest.fixture
def tenant_b_writer() -> TestClient:
    return _client(["multimodal:read", "multimodal:write"], tenant_id="tenant-b")


def test_create_request_with_execute_now_false(writer_client: TestClient) -> None:
    response = writer_client.post(
        "/v1/multimodal/requests",
        json={
            "modality": "text_to_speech",
            "input_text": "hello",
            "execute_now": False,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["state"] == "pending"
    assert payload["result_id"] == ""


def test_create_request_execute_now_true_completes(writer_client: TestClient) -> None:
    response = writer_client.post(
        "/v1/multimodal/requests",
        json={
            "modality": "text_to_speech",
            "input_text": "hello world",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["state"] == "completed"
    assert payload["result_id"] != ""


def test_create_request_requires_write_scope(reader_client: TestClient) -> None:
    response = reader_client.post(
        "/v1/multimodal/requests",
        json={"modality": "text_to_speech", "input_text": "blocked"},
    )
    assert response.status_code == 403
    assert "multimodal:write" in response.json()["detail"]


def test_read_requests_require_read_scope(no_scope_client: TestClient) -> None:
    response = no_scope_client.get("/v1/multimodal/requests")
    assert response.status_code == 403
    assert "multimodal:read" in response.json()["detail"]


def test_policy_blocks_over_limit_text(writer_client: TestClient) -> None:
    writer_client.post(
        "/v1/multimodal/tenants/tenant-a/policy",
        json={"max_text_chars": 4},
    )
    response = writer_client.post(
        "/v1/multimodal/requests",
        json={
            "modality": "text_to_speech",
            "input_text": "this is too long",
            "execute_now": False,
        },
    )
    assert response.status_code == 400
    assert "max_text_chars" in response.json()["detail"]


def test_policy_blocks_over_limit_artifact(writer_client: TestClient) -> None:
    writer_client.post(
        "/v1/multimodal/tenants/tenant-a/policy",
        json={"max_artifact_bytes": 2},
    )
    encoded = base64.b64encode(b"abcdef").decode("utf-8")
    response = writer_client.post(
        "/v1/multimodal/requests",
        json={
            "modality": "vision_analysis",
            "input_artifact_base64": encoded,
            "execute_now": False,
        },
    )
    assert response.status_code == 400
    assert "max_artifact_bytes" in response.json()["detail"]


def test_policy_blocks_disallowed_modality(writer_client: TestClient) -> None:
    writer_client.post(
        "/v1/multimodal/tenants/tenant-a/policy",
        json={"allowed_modalities": ["vision_analysis"]},
    )
    response = writer_client.post(
        "/v1/multimodal/requests",
        json={
            "modality": "text_to_speech",
            "input_text": "should fail",
            "execute_now": False,
        },
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


def test_list_requests_is_tenant_scoped(
    writer_client: TestClient, tenant_b_writer: TestClient
) -> None:
    writer_client.post(
        "/v1/multimodal/requests",
        json={"modality": "text_to_speech", "input_text": "tenant-a", "execute_now": False},
    )
    tenant_b_writer.post(
        "/v1/multimodal/requests",
        json={"modality": "text_to_speech", "input_text": "tenant-b", "execute_now": False},
    )

    tenant_a_items = writer_client.get("/v1/multimodal/requests").json()
    tenant_b_items = tenant_b_writer.get("/v1/multimodal/requests").json()

    assert len(tenant_a_items) == 1
    assert len(tenant_b_items) == 1
    assert tenant_a_items[0]["tenant_id"] == "tenant-a"
    assert tenant_b_items[0]["tenant_id"] == "tenant-b"


def test_get_request_is_tenant_scoped(
    writer_client: TestClient, tenant_b_writer: TestClient
) -> None:
    create_response = writer_client.post(
        "/v1/multimodal/requests",
        json={"modality": "text_to_speech", "input_text": "tenant-a", "execute_now": False},
    )
    request_id = create_response.json()["id"]

    allowed = writer_client.get(f"/v1/multimodal/requests/{request_id}")
    denied = tenant_b_writer.get(f"/v1/multimodal/requests/{request_id}")
    assert allowed.status_code == 200
    assert denied.status_code == 404


def test_execute_request_transitions_state(writer_client: TestClient) -> None:
    create_response = writer_client.post(
        "/v1/multimodal/requests",
        json={"modality": "text_to_speech", "input_text": "run", "execute_now": False},
    )
    request_id = create_response.json()["id"]

    execute_response = writer_client.post(f"/v1/multimodal/requests/{request_id}/execute")
    assert execute_response.status_code == 200
    assert execute_response.json()["state"] == "completed"


def test_execute_request_requires_write_scope(
    writer_client: TestClient, reader_client: TestClient
) -> None:
    create_response = writer_client.post(
        "/v1/multimodal/requests",
        json={"modality": "text_to_speech", "input_text": "run", "execute_now": False},
    )
    request_id = create_response.json()["id"]
    response = reader_client.post(f"/v1/multimodal/requests/{request_id}/execute")
    assert response.status_code == 403


def test_get_result_returns_404_when_not_available(writer_client: TestClient) -> None:
    create_response = writer_client.post(
        "/v1/multimodal/requests",
        json={"modality": "text_to_speech", "input_text": "pending", "execute_now": False},
    )
    request_id = create_response.json()["id"]
    response = writer_client.get(f"/v1/multimodal/requests/{request_id}/result")
    assert response.status_code == 404


def test_get_result_after_execution(writer_client: TestClient) -> None:
    create_response = writer_client.post(
        "/v1/multimodal/requests",
        json={
            "modality": "vision_analysis",
            "input_artifact_base64": base64.b64encode(b"x").decode(),
        },
    )
    request_id = create_response.json()["id"]

    response = writer_client.get(f"/v1/multimodal/requests/{request_id}/result")
    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"] == request_id
    assert payload["state"] == "completed"


def test_cancel_pending_request(writer_client: TestClient) -> None:
    create_response = writer_client.post(
        "/v1/multimodal/requests",
        json={"modality": "text_to_speech", "input_text": "cancel", "execute_now": False},
    )
    request_id = create_response.json()["id"]

    cancel_response = writer_client.post(f"/v1/multimodal/requests/{request_id}/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["state"] == "cancelled"


def test_cancel_completed_request_returns_409(writer_client: TestClient) -> None:
    create_response = writer_client.post(
        "/v1/multimodal/requests",
        json={"modality": "text_to_speech", "input_text": "already-complete"},
    )
    request_id = create_response.json()["id"]
    cancel_response = writer_client.post(f"/v1/multimodal/requests/{request_id}/cancel")
    assert cancel_response.status_code == 409


def test_service_policy_and_lifecycle_contracts() -> None:
    _service.set_policy(
        "tenant-a",
        MultimodalPolicy(allowed_modalities={ModalityType.TEXT_TO_SPEECH}, max_text_chars=10),
    )
    request = _service.create_request(
        tenant_id="tenant-a",
        modality=ModalityType.TEXT_TO_SPEECH,
        input_text="short",
        requested_timeout_seconds=5,
    )
    assert request.state == RequestState.PENDING
    request = asyncio.run(_service.execute_request(request.id, tenant_id="tenant-a"))
    assert request.state == RequestState.COMPLETED
