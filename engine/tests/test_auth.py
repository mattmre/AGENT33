"""Tests for authentication module."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from agent33.security.auth import (
    TokenPayload,
    _hash_key,
    clear_api_key_cache,
    create_access_token,
    generate_api_key,
    revoke_api_key,
    validate_api_key,
    verify_token,
)


class TestTokenPayload:
    """Tests for TokenPayload model."""

    def test_token_payload_defaults(self):
        """Test that TokenPayload has correct defaults."""
        payload = TokenPayload(sub="user123")
        assert payload.sub == "user123"
        assert payload.tenant_id is None
        assert payload.scopes == []
        assert payload.exp == 0

    def test_token_payload_with_all_fields(self):
        """Test TokenPayload with all fields set."""
        payload = TokenPayload(
            sub="user123",
            tenant_id="tenant456",
            scopes=["read", "write"],
            exp=1234567890,
        )
        assert payload.sub == "user123"
        assert payload.tenant_id == "tenant456"
        assert payload.scopes == ["read", "write"]
        assert payload.exp == 1234567890


class TestJWTFunctions:
    """Tests for JWT helper functions."""

    def test_create_access_token_basic(self):
        """Test basic token creation."""
        token = create_access_token(subject="user123")
        assert token
        assert isinstance(token, str)
        # Should have 3 parts separated by dots
        assert len(token.split(".")) == 3

    def test_create_access_token_with_scopes(self):
        """Test token creation with scopes."""
        token = create_access_token(
            subject="user123",
            scopes=["read", "write"],
        )
        # Decode without verification to check payload
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["scopes"] == ["read", "write"]

    def test_create_access_token_with_tenant_id(self):
        """Test token creation with tenant_id."""
        token = create_access_token(
            subject="user123",
            tenant_id="tenant456",
        )
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["tenant_id"] == "tenant456"

    def test_create_access_token_includes_timestamps(self):
        """Test that token includes iat and exp timestamps."""
        before = int(time.time())
        token = create_access_token(subject="user123")
        after = int(time.time())

        payload = jwt.decode(token, options={"verify_signature": False})
        assert before <= payload["iat"] <= after
        assert payload["exp"] > payload["iat"]

    def test_verify_token_success(self):
        """Test successful token verification."""
        token = create_access_token(
            subject="user123",
            scopes=["read"],
            tenant_id="tenant456",
        )
        payload = verify_token(token)
        assert payload.sub == "user123"
        assert payload.scopes == ["read"]
        assert payload.tenant_id == "tenant456"

    def test_verify_token_invalid(self):
        """Test that invalid token raises error."""
        with pytest.raises(jwt.InvalidTokenError):
            verify_token("invalid.token.here")

    def test_verify_token_tampered(self):
        """Test that tampered token raises error."""
        token = create_access_token(subject="user123")
        # Tamper with the token
        parts = token.split(".")
        parts[1] = parts[1][:-1] + "X"  # Modify payload
        tampered = ".".join(parts)

        with pytest.raises(jwt.InvalidTokenError):
            verify_token(tampered)


class TestAPIKeyFunctions:
    """Tests for API key management functions."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_api_key_cache()

    def test_hash_key_deterministic(self):
        """Test that same key produces same hash."""
        key = "test_key_12345"
        hash1 = _hash_key(key)
        hash2 = _hash_key(key)
        assert hash1 == hash2

    def test_hash_key_different_for_different_keys(self):
        """Test that different keys produce different hashes."""
        hash1 = _hash_key("key1")
        hash2 = _hash_key("key2")
        assert hash1 != hash2

    def test_hash_key_sha256_length(self):
        """Test that hash is SHA-256 (64 hex chars)."""
        hash_val = _hash_key("test")
        assert len(hash_val) == 64

    def test_generate_api_key_format(self):
        """Test that generated key has correct format."""
        result = generate_api_key(subject="user123")
        assert result["key"].startswith("a33_")
        assert len(result["key_id"]) == 16  # hex(8) = 16 chars
        assert result["subject"] == "user123"

    def test_generate_api_key_with_scopes(self):
        """Test generating key with scopes."""
        result = generate_api_key(
            subject="user123",
            scopes=["read", "write"],
        )
        assert result["scopes"] == ["read", "write"]

    def test_generate_api_key_with_tenant_id(self):
        """Test generating key with tenant_id."""
        result = generate_api_key(
            subject="user123",
            tenant_id="tenant456",
        )
        assert result["tenant_id"] == "tenant456"

    def test_generate_api_key_unique(self):
        """Test that each generated key is unique."""
        key1 = generate_api_key(subject="user")
        key2 = generate_api_key(subject="user")
        assert key1["key"] != key2["key"]
        assert key1["key_id"] != key2["key_id"]

    def test_validate_api_key_success(self):
        """Test successful API key validation."""
        result = generate_api_key(
            subject="user123",
            scopes=["read"],
            tenant_id="tenant456",
        )
        payload = validate_api_key(result["key"])
        assert payload is not None
        assert payload.sub == "user123"
        assert payload.scopes == ["read"]
        assert payload.tenant_id == "tenant456"

    def test_validate_api_key_invalid(self):
        """Test that invalid key returns None."""
        payload = validate_api_key("invalid_key")
        assert payload is None

    def test_revoke_api_key_success(self):
        """Test successful key revocation."""
        result = generate_api_key(subject="user123")
        key_id = result["key_id"]
        raw_key = result["key"]

        # Key should be valid before revocation
        assert validate_api_key(raw_key) is not None

        # Revoke the key
        assert revoke_api_key(key_id) is True

        # Key should be invalid after revocation
        assert validate_api_key(raw_key) is None

    def test_revoke_api_key_not_found(self):
        """Test revoking non-existent key."""
        assert revoke_api_key("nonexistent_key_id") is False

    def test_clear_api_key_cache(self):
        """Test clearing the API key cache."""
        # Generate a key
        result = generate_api_key(subject="user123")
        raw_key = result["key"]

        # Should be valid
        assert validate_api_key(raw_key) is not None

        # Clear cache
        clear_api_key_cache()

        # Should now be invalid (not in cache)
        assert validate_api_key(raw_key) is None


class TestAsyncAPIKeyFunctions:
    """Tests for async API key functions."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_generate_api_key_async_creates_db_record(self, mock_session):
        """Test that async generation creates database record."""
        from agent33.security.auth import generate_api_key_async

        # Mock the ApiKey model
        with patch("agent33.security.auth.ApiKey") as mock_api_key:
            mock_instance = MagicMock()
            mock_instance.id = "db_id_123"
            mock_api_key.return_value = mock_instance

            result = await generate_api_key_async(
                session=mock_session,
                tenant_id="tenant123",
                subject="user123",
                name="Test Key",
                scopes=["read"],
            )

            assert result["key"].startswith("a33_")
            assert result["tenant_id"] == "tenant123"
            mock_session.add.assert_called_once()
            mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_api_key_async_checks_cache_first(self, mock_session):
        """Test that async validation checks cache before database."""
        from agent33.security.auth import validate_api_key_async

        clear_api_key_cache()

        # Add key to cache
        result = generate_api_key(
            subject="user123",
            tenant_id="tenant456",
        )

        # Validate should hit cache, not database
        payload = await validate_api_key_async(mock_session, result["key"])
        assert payload is not None
        assert payload.sub == "user123"

        # Session should not have been queried
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_revoke_api_key_async_deactivates_record(self, mock_session):
        """Test that async revocation deactivates database record."""
        from agent33.security.auth import revoke_api_key_async

        # Mock finding the key
        mock_api_key = MagicMock()
        mock_api_key.key_id = "key123"
        mock_api_key.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_session.execute.return_value = mock_result

        result = await revoke_api_key_async(
            session=mock_session,
            key_id="key123",
            tenant_id="tenant456",
        )

        assert result is True
        assert mock_api_key.is_active is False
