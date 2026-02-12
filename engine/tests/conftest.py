"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agent33.main import app
from agent33.security.auth import create_access_token


@pytest.fixture
def auth_token() -> str:
    return create_access_token("test-user", scopes=["admin"])


@pytest.fixture
def client(auth_token: str) -> TestClient:
    return TestClient(app, headers={"Authorization": f"Bearer {auth_token}"})
