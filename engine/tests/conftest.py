"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agent33.main import app
from agent33.security.auth import create_access_token


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Disable rate limiting for every test.

    The RateLimiter is a module-level singleton whose token-bucket counters
    persist across the entire pytest process.  Without this reset, tests that
    make many requests (e.g. seed helpers that POST 15+ signals) exhaust the
    burst allowance and subsequent requests receive 429s.

    Setting the default tier to UNLIMITED ensures the middleware never rejects
    a request.  The dedicated ``test_rate_limiter.py`` tests create their own
    RateLimiter instances and are unaffected.
    """
    from agent33.security.rate_limiter import RateLimitTier

    rate_limiter = getattr(app.state, "rate_limiter", None)
    if rate_limiter is not None:
        rate_limiter.reset_all()
        rate_limiter.default_tier = RateLimitTier.UNLIMITED


@pytest.fixture
def auth_token() -> str:
    return create_access_token("test-user", scopes=["admin"])


@pytest.fixture
def client(auth_token: str) -> TestClient:
    return TestClient(app, headers={"Authorization": f"Bearer {auth_token}"})
