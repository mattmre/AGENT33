"""Tests for approval token REST API endpoints (Phase 45).

These tests verify the token issuance, validation, and revocation endpoints
that extend the existing tool_approvals router.
"""

from __future__ import annotations

import pytest

from agent33.security.approval_tokens import ApprovalTokenError, ApprovalTokenManager
from agent33.tools.approvals import (
    ApprovalReason,
    ApprovalStatus,
    ToolApprovalService,
)


class TestApprovalTokenManagerIntegration:
    """End-to-end: create approval, issue token, validate, revoke."""

    def test_full_lifecycle(self) -> None:
        """Create approval -> issue token -> validate -> consumed."""
        service = ToolApprovalService()
        mgr = ApprovalTokenManager(secret="test-secret")

        # 1. Create approval request
        req = service.request(
            reason=ApprovalReason.TOOL_POLICY_ASK,
            tool_name="shell",
            operation="execute",
            requested_by="user1",
            tenant_id="t-001",
        )
        assert req.status == ApprovalStatus.PENDING

        # 2. Approve it
        approved = service.decide(
            req.approval_id,
            approved=True,
            reviewed_by="admin1",
        )
        assert approved is not None
        assert approved.status == ApprovalStatus.APPROVED

        # 3. Issue token
        args = {"command": "ls -la"}
        token = mgr.issue(approved, arguments=args)
        assert isinstance(token, str)

        # 4. Validate token
        payload = mgr.validate(token, "shell", args, tenant_id="t-001")
        assert payload.tool == "shell"
        assert payload.jti == req.approval_id

        # 5. One-time token should be consumed
        with pytest.raises(ApprovalTokenError, match="already been consumed"):
            mgr.validate(token, "shell", args, tenant_id="t-001")

    def test_revocation_lifecycle(self) -> None:
        """Issue token -> revoke -> validation fails."""
        service = ToolApprovalService()
        mgr = ApprovalTokenManager(secret="test-secret")

        req = service.request(
            reason=ApprovalReason.TOOL_POLICY_ASK,
            tool_name="shell",
            requested_by="user1",
        )
        approved = service.decide(req.approval_id, approved=True, reviewed_by="admin")
        assert approved is not None
        args = {"command": "echo hello"}
        token = mgr.issue(approved, arguments=args)

        # Revoke
        mgr.revoke(req.approval_id)

        # Validation should fail
        with pytest.raises(ApprovalTokenError, match="revoked"):
            mgr.validate(token, "shell", args)

    def test_rejected_approval_cannot_issue_token(self) -> None:
        """Rejected approvals should not produce tokens."""
        service = ToolApprovalService()
        mgr = ApprovalTokenManager(secret="test-secret")

        req = service.request(
            reason=ApprovalReason.TOOL_POLICY_ASK,
            tool_name="shell",
            requested_by="user1",
        )
        rejected = service.decide(req.approval_id, approved=False, reviewed_by="admin")
        assert rejected is not None
        assert rejected.status == ApprovalStatus.REJECTED

        with pytest.raises(ApprovalTokenError, match="Cannot issue token"):
            mgr.issue(rejected, arguments={})

    def test_expired_approval_cannot_issue_token(self) -> None:
        """Expired approvals should not produce tokens."""
        service = ToolApprovalService(default_ttl_minutes=0)  # immediate expiry
        mgr = ApprovalTokenManager(secret="test-secret")

        req = service.request(
            reason=ApprovalReason.TOOL_POLICY_ASK,
            tool_name="shell",
            requested_by="user1",
        )
        # Force expiry
        from datetime import UTC, datetime

        req.expires_at = datetime(2020, 1, 1, tzinfo=UTC)
        service._expire_pending()

        with pytest.raises(ApprovalTokenError, match="Cannot issue token"):
            mgr.issue(req, arguments={})

    def test_token_validate_without_consuming(self) -> None:
        """Non-one-time tokens can be validated repeatedly."""
        service = ToolApprovalService()
        mgr = ApprovalTokenManager(secret="test-secret")

        req = service.request(
            reason=ApprovalReason.TOOL_POLICY_ASK,
            tool_name="file_ops",
            requested_by="user1",
        )
        approved = service.decide(req.approval_id, approved=True, reviewed_by="admin")
        assert approved is not None
        args = {"path": "/tmp/data.txt", "operation": "read"}
        token = mgr.issue(approved, arguments=args, one_time=False)

        # Multiple validations should succeed
        p1 = mgr.validate(token, "file_ops", args)
        p2 = mgr.validate(token, "file_ops", args)
        assert p1.jti == p2.jti
