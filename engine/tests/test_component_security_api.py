"""Phase 28 Stage 1 tests for component security backend surfaces."""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from agent33.api.routes.component_security import _service
from agent33.component_security.models import (
    FindingCategory,
    FindingSeverity,
    FindingsSummary,
    RunStatus,
    ScanTarget,
    SecurityFinding,
    SecurityProfile,
    SecurityRun,
)
from agent33.main import app
from agent33.security.auth import create_access_token
from agent33.services.pentagi_integration import PentAGIService

if TYPE_CHECKING:
    from pathlib import Path


def _fake_completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def _default_command_runner(
    command: list[str], _timeout_seconds: int
) -> subprocess.CompletedProcess[str]:
    if "bandit" in " ".join(command):
        return _fake_completed('{"results": []}')
    if command and command[0] == "gitleaks":
        return _fake_completed("[]")
    return _fake_completed("")


@pytest.fixture(autouse=True)
def reset_component_security_service() -> None:
    _service._runs.clear()
    _service._findings.clear()
    _service._command_runner = _default_command_runner
    yield
    _service._runs.clear()
    _service._findings.clear()
    _service._command_runner = _default_command_runner


@pytest.fixture
def writer_client() -> TestClient:
    token = create_access_token(
        "component-security-writer",
        scopes=["component-security:read", "component-security:write"],
    )
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def reader_client() -> TestClient:
    token = create_access_token("component-security-reader", scopes=["component-security:read"])
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def no_scope_client() -> TestClient:
    token = create_access_token("component-security-none", scopes=[])
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


class TestComponentSecurityModels:
    def test_run_defaults(self) -> None:
        run = SecurityRun(
            profile=SecurityProfile.QUICK,
            target=ScanTarget(repository_path="."),
        )
        assert run.id.startswith("secrun-")
        assert run.status == RunStatus.PENDING
        assert run.findings_count == 0
        assert run.duration_seconds == 0

    def test_findings_summary_aggregation(self) -> None:
        findings = [
            SecurityFinding(
                run_id="secrun-1",
                severity=FindingSeverity.HIGH,
                category=FindingCategory.CODE_QUALITY,
                title="a",
                description="a",
                tool="bandit",
            ),
            SecurityFinding(
                run_id="secrun-1",
                severity=FindingSeverity.LOW,
                category=FindingCategory.SECRETS_EXPOSURE,
                title="b",
                description="b",
                tool="gitleaks",
            ),
        ]
        summary = FindingsSummary.from_findings(findings)
        assert summary.high == 1
        assert summary.low == 1
        assert summary.total == 2


class TestPentAGIService:
    def test_launch_quick_scan_collects_findings(self, tmp_path: Path) -> None:
        def command_runner(
            command: list[str], _timeout_seconds: int
        ) -> subprocess.CompletedProcess[str]:
            if "bandit" in " ".join(command):
                return _fake_completed(
                    json.dumps(
                        {
                            "results": [
                                {
                                    "issue_severity": "HIGH",
                                    "issue_text": "Use of subprocess with shell=True",
                                    "filename": "app.py",
                                    "line_number": 12,
                                    "issue_cwe": {"id": "78"},
                                }
                            ]
                        }
                    ),
                    returncode=1,
                )
            return _fake_completed(
                json.dumps(
                    [
                        {
                            "RuleID": "generic-api-key",
                            "Description": "Detected a Generic API Key",
                            "File": "config.py",
                            "StartLine": 10,
                        }
                    ]
                )
            )

        service = PentAGIService(command_runner=command_runner)
        run = service.create_run(
            target=ScanTarget(repository_path=str(tmp_path)),
            profile=SecurityProfile.QUICK,
        )
        completed = service.launch_scan(run.id)

        assert completed.status == RunStatus.COMPLETED
        assert completed.findings_count == 2
        assert completed.findings_summary.high == 2
        findings = service.fetch_findings(run.id)
        assert len(findings) == 2
        assert {finding.tool for finding in findings} == {"bandit", "gitleaks"}

    def test_launch_scan_fails_for_missing_target(self) -> None:
        service = PentAGIService(command_runner=_default_command_runner)
        run = service.create_run(
            target=ScanTarget(repository_path="D:\\missing-target"),
            profile=SecurityProfile.QUICK,
        )
        failed = service.launch_scan(run.id)
        assert failed.status == RunStatus.FAILED
        assert "does not exist" in failed.error_message

    def test_non_quick_profile_rejected(self, tmp_path: Path) -> None:
        service = PentAGIService(command_runner=_default_command_runner)
        run = service.create_run(
            target=ScanTarget(repository_path=str(tmp_path)),
            profile=SecurityProfile.STANDARD,
        )
        with pytest.raises(Exception, match="not available in Stage 1"):
            service.launch_scan(run.id)


class TestComponentSecurityApi:
    def test_create_run_pending_when_execute_now_false(
        self, writer_client: TestClient, tmp_path: Path
    ) -> None:
        response = writer_client.post(
            "/v1/component-security/runs",
            json={
                "target": {"repository_path": str(tmp_path)},
                "profile": "quick",
                "execute_now": False,
            },
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["status"] == "pending"
        assert payload["findings_count"] == 0

    def test_create_run_executes_quick_profile(
        self, writer_client: TestClient, tmp_path: Path
    ) -> None:
        response = writer_client.post(
            "/v1/component-security/runs",
            json={"target": {"repository_path": str(tmp_path)}, "profile": "quick"},
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["status"] == "completed"
        assert payload["metadata"]["tools_executed"] == ["bandit", "gitleaks"]

    def test_list_get_and_status_endpoints(
        self, writer_client: TestClient, reader_client: TestClient, tmp_path: Path
    ) -> None:
        create_response = writer_client.post(
            "/v1/component-security/runs",
            json={"target": {"repository_path": str(tmp_path)}, "execute_now": False},
        )
        run_id = create_response.json()["id"]

        list_response = reader_client.get("/v1/component-security/runs")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

        get_response = reader_client.get(f"/v1/component-security/runs/{run_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == run_id

        status_response = reader_client.get(f"/v1/component-security/runs/{run_id}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "pending"

    def test_findings_endpoint_with_filter(
        self, writer_client: TestClient, reader_client: TestClient, tmp_path: Path
    ) -> None:
        create_response = writer_client.post(
            "/v1/component-security/runs",
            json={"target": {"repository_path": str(tmp_path)}, "profile": "quick"},
        )
        run_id = create_response.json()["id"]

        findings_response = reader_client.get(
            f"/v1/component-security/runs/{run_id}/findings?min_severity=high"
        )
        assert findings_response.status_code == 200
        payload = findings_response.json()
        assert payload["total_count"] == 0
        assert payload["findings"] == []

    def test_cancel_terminal_run_returns_409(
        self, writer_client: TestClient, tmp_path: Path
    ) -> None:
        create_response = writer_client.post(
            "/v1/component-security/runs",
            json={"target": {"repository_path": str(tmp_path)}, "profile": "quick"},
        )
        run_id = create_response.json()["id"]

        cancel_response = writer_client.post(f"/v1/component-security/runs/{run_id}/cancel")
        assert cancel_response.status_code == 409

    def test_delete_run_then_get_returns_404(
        self, writer_client: TestClient, reader_client: TestClient, tmp_path: Path
    ) -> None:
        create_response = writer_client.post(
            "/v1/component-security/runs",
            json={"target": {"repository_path": str(tmp_path)}, "execute_now": False},
        )
        run_id = create_response.json()["id"]

        delete_response = writer_client.delete(f"/v1/component-security/runs/{run_id}")
        assert delete_response.status_code == 200

        get_response = reader_client.get(f"/v1/component-security/runs/{run_id}")
        assert get_response.status_code == 404

    def test_scope_enforcement_for_missing_permissions(
        self, no_scope_client: TestClient, tmp_path: Path
    ) -> None:
        create_response = no_scope_client.post(
            "/v1/component-security/runs",
            json={"target": {"repository_path": str(tmp_path)}, "profile": "quick"},
        )
        assert create_response.status_code == 403

        list_response = no_scope_client.get("/v1/component-security/runs")
        assert list_response.status_code == 403
