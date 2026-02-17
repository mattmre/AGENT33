"""Tests for explanations API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agent33.main import app
from agent33.security.auth import create_access_token


@pytest.fixture(autouse=True)
def clear_explanations_state():
    """Clear in-memory explanation store between tests."""
    from agent33.api.routes import explanations

    def _reset() -> None:
        explanations.get_explanations_store().clear()

    _reset()
    yield
    _reset()


@pytest.fixture
def reader_client() -> TestClient:
    """Client with read scope."""
    token = create_access_token("reader-user", scopes=["workflows:read"])
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def writer_client() -> TestClient:
    """Client with write scope."""
    token = create_access_token(
        "writer-user",
        scopes=["workflows:read", "workflows:write"],
    )
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def no_scope_client() -> TestClient:
    """Client with no scopes."""
    token = create_access_token("no-scope-user", scopes=[])
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


# -- Happy path tests --------------------------------------------------------


class TestExplanationCreation:
    """Tests for creating explanations."""

    def test_create_explanation_success(self, writer_client: TestClient) -> None:
        """Should create explanation with fact-check hook invoked."""
        resp = writer_client.post(
            "/v1/explanations/",
            json={
                "entity_type": "workflow",
                "entity_id": "hello-flow",
                "metadata": {"model": "llama3.1"},
            },
        )
        assert resp.status_code == 201

        data = resp.json()
        assert data["entity_type"] == "workflow"
        assert data["entity_id"] == "hello-flow"
        assert data["content"]  # Has generated content
        assert data["fact_check_status"] == "skipped"  # Hook returns SKIPPED
        assert "expl-" in data["id"]
        assert data["metadata"]["model"] == "llama3.1"

    def test_create_multiple_explanations(self, writer_client: TestClient) -> None:
        """Should create multiple explanations with unique IDs."""
        resp1 = writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "flow-1"},
        )
        resp2 = writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "agent", "entity_id": "agent-1"},
        )

        assert resp1.status_code == 201
        assert resp2.status_code == 201

        data1 = resp1.json()
        data2 = resp2.json()

        # Should have different IDs
        assert data1["id"] != data2["id"]


class TestExplanationRetrieval:
    """Tests for retrieving explanations."""

    def test_get_explanation_by_id(
        self, writer_client: TestClient, reader_client: TestClient
    ) -> None:
        """Should retrieve explanation by ID."""
        # Create explanation
        create_resp = writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "test-flow"},
        )
        explanation_id = create_resp.json()["id"]

        # Retrieve with read scope
        get_resp = reader_client.get(f"/v1/explanations/{explanation_id}")
        assert get_resp.status_code == 200

        data = get_resp.json()
        assert data["id"] == explanation_id
        assert data["entity_type"] == "workflow"
        assert data["entity_id"] == "test-flow"

    def test_get_nonexistent_explanation_returns_404(
        self, reader_client: TestClient
    ) -> None:
        """Should return 404 for nonexistent explanation."""
        resp = reader_client.get("/v1/explanations/expl-nonexistent")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_list_all_explanations(
        self, writer_client: TestClient, reader_client: TestClient
    ) -> None:
        """Should list all explanations."""
        # Create multiple explanations
        writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "flow-1"},
        )
        writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "agent", "entity_id": "agent-1"},
        )

        # List all
        resp = reader_client.get("/v1/explanations/")
        assert resp.status_code == 200

        data = resp.json()
        assert len(data) == 2

    def test_list_explanations_filtered_by_entity_type(
        self, writer_client: TestClient, reader_client: TestClient
    ) -> None:
        """Should filter explanations by entity_type."""
        # Create explanations of different types
        writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "flow-1"},
        )
        writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "agent", "entity_id": "agent-1"},
        )

        # Filter by workflow
        resp = reader_client.get("/v1/explanations/?entity_type=workflow")
        assert resp.status_code == 200

        data = resp.json()
        assert len(data) == 1
        assert data[0]["entity_type"] == "workflow"

    def test_list_explanations_filtered_by_entity_id(
        self, writer_client: TestClient, reader_client: TestClient
    ) -> None:
        """Should filter explanations by entity_id."""
        writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "flow-1"},
        )
        writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "flow-2"},
        )

        resp = reader_client.get("/v1/explanations/?entity_id=flow-1")
        assert resp.status_code == 200

        data = resp.json()
        assert len(data) == 1
        assert data[0]["entity_id"] == "flow-1"


class TestExplanationDeletion:
    """Tests for deleting explanations."""

    def test_delete_explanation_success(self, writer_client: TestClient) -> None:
        """Should delete explanation."""
        # Create
        create_resp = writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "test-flow"},
        )
        explanation_id = create_resp.json()["id"]

        # Delete
        delete_resp = writer_client.delete(f"/v1/explanations/{explanation_id}")
        assert delete_resp.status_code == 200
        assert "deleted" in delete_resp.json()["message"].lower()

        # Verify deleted
        get_resp = writer_client.get(f"/v1/explanations/{explanation_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_explanation_returns_404(
        self, writer_client: TestClient
    ) -> None:
        """Should return 404 when deleting nonexistent explanation."""
        resp = writer_client.delete("/v1/explanations/expl-nonexistent")
        assert resp.status_code == 404


# -- Authorization tests -----------------------------------------------------


class TestExplanationAuthorization:
    """Tests for scope enforcement."""

    def test_create_requires_write_scope(self, no_scope_client: TestClient) -> None:
        """Should require workflows:write scope to create."""
        resp = no_scope_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "test-flow"},
        )
        assert resp.status_code == 403
        assert "workflows:write" in resp.json()["detail"]

    def test_get_requires_read_scope(
        self, writer_client: TestClient, no_scope_client: TestClient
    ) -> None:
        """Should require workflows:read scope to retrieve."""
        # Create explanation
        create_resp = writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "test-flow"},
        )
        explanation_id = create_resp.json()["id"]

        # Try to get without scope
        resp = no_scope_client.get(f"/v1/explanations/{explanation_id}")
        assert resp.status_code == 403
        assert "workflows:read" in resp.json()["detail"]

    def test_list_requires_read_scope(self, no_scope_client: TestClient) -> None:
        """Should require workflows:read scope to list."""
        resp = no_scope_client.get("/v1/explanations/")
        assert resp.status_code == 403

    def test_delete_requires_write_scope(
        self, writer_client: TestClient, reader_client: TestClient
    ) -> None:
        """Should require workflows:write scope to delete."""
        # Create explanation
        create_resp = writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "test-flow"},
        )
        explanation_id = create_resp.json()["id"]

        # Try to delete with only read scope
        resp = reader_client.delete(f"/v1/explanations/{explanation_id}")
        assert resp.status_code == 403


# -- Fact-check hook tests ---------------------------------------------------


class TestFactCheckHook:
    """Tests for fact-check hook integration."""

    def test_fact_check_hook_invoked_on_creation(
        self, writer_client: TestClient
    ) -> None:
        """Fact-check hook should be invoked and set status."""
        resp = writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "test-flow"},
        )
        assert resp.status_code == 201

        data = resp.json()
        # Hook currently returns SKIPPED
        assert data["fact_check_status"] == "skipped"

    def test_fact_check_status_persisted(
        self, writer_client: TestClient, reader_client: TestClient
    ) -> None:
        """Fact-check status should persist on retrieval."""
        create_resp = writer_client.post(
            "/v1/explanations/",
            json={"entity_type": "workflow", "entity_id": "test-flow"},
        )
        explanation_id = create_resp.json()["id"]

        # Retrieve and verify status persisted
        get_resp = reader_client.get(f"/v1/explanations/{explanation_id}")
        assert get_resp.json()["fact_check_status"] == "skipped"
