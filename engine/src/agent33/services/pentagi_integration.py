"""Stage 1 PentAGI integration service (quick profile)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from agent33.component_security.models import (
    FindingCategory,
    FindingSeverity,
    FindingsSummary,
    RunStatus,
    ScanOptions,
    ScanTarget,
    SecurityFinding,
    SecurityProfile,
    SecurityRun,
)

logger = structlog.get_logger()

if TYPE_CHECKING:
    from collections.abc import Callable

_TERMINAL_STATES = frozenset({
    RunStatus.COMPLETED,
    RunStatus.FAILED,
    RunStatus.CANCELLED,
    RunStatus.TIMEOUT,
})
_SEVERITY_ORDER = {
    FindingSeverity.INFO: 0,
    FindingSeverity.LOW: 1,
    FindingSeverity.MEDIUM: 2,
    FindingSeverity.HIGH: 3,
    FindingSeverity.CRITICAL: 4,
}


class PentAGIServiceError(Exception):
    """Base service error for component security operations."""


class RunNotFoundError(PentAGIServiceError):
    """Raised when the requested run does not exist."""


class RunStateError(PentAGIServiceError):
    """Raised for invalid state transitions."""


class ToolExecutionError(PentAGIServiceError):
    """Raised when scanner command execution fails."""


class PentAGIService:
    """In-memory service for component security run lifecycle and quick profile scans."""

    def __init__(
        self,
        command_runner: Callable[[list[str], int], subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self._runs: dict[str, SecurityRun] = {}
        self._findings: dict[str, list[SecurityFinding]] = {}
        self._command_runner = command_runner or self._run_command

    def create_run(
        self,
        *,
        target: ScanTarget,
        profile: SecurityProfile,
        options: ScanOptions | None = None,
        tenant_id: str = "",
        requested_by: str = "",
        session_id: str = "",
        release_candidate_id: str = "",
    ) -> SecurityRun:
        """Create and store a new security run."""
        run = SecurityRun(
            tenant_id=tenant_id,
            profile=profile,
            target=target,
            options=options or ScanOptions(),
        )
        run.metadata.requested_by = requested_by
        run.metadata.session_id = session_id
        run.metadata.release_candidate_id = release_candidate_id
        self._runs[run.id] = run
        self._findings[run.id] = []
        logger.info("component_security_run_created", run_id=run.id, profile=profile.value)
        return run

    def list_runs(
        self,
        *,
        tenant_id: str | None = None,
        status: RunStatus | None = None,
        profile: SecurityProfile | None = None,
        limit: int = 50,
    ) -> list[SecurityRun]:
        """List runs with optional tenant/status/profile filters."""
        runs = list(self._runs.values())
        if tenant_id:
            runs = [run for run in runs if run.tenant_id == tenant_id]
        if status is not None:
            runs = [run for run in runs if run.status == status]
        if profile is not None:
            runs = [run for run in runs if run.profile == profile]
        runs.sort(key=lambda run: run.created_at, reverse=True)
        return runs[:limit]

    def get_run(self, run_id: str, *, tenant_id: str | None = None) -> SecurityRun:
        """Get a run by ID with optional tenant check."""
        run = self._runs.get(run_id)
        if run is None:
            raise RunNotFoundError(f"Component security run not found: {run_id}")
        if tenant_id and run.tenant_id != tenant_id:
            raise RunNotFoundError(f"Component security run not found: {run_id}")
        return run

    def launch_scan(self, run_id: str, *, tenant_id: str | None = None) -> SecurityRun:
        """Execute stage-1 quick profile scanners for the run."""
        run = self.get_run(run_id, tenant_id=tenant_id)
        if run.status != RunStatus.PENDING:
            raise RunStateError(f"Run {run.id} cannot start from state {run.status.value}")
        if run.profile != SecurityProfile.QUICK:
            raise PentAGIServiceError(
                f"Profile '{run.profile.value}' is not available in Stage 1; use 'quick'"
            )

        run.status = RunStatus.RUNNING
        run.touch()
        run.started_at = run.updated_at

        try:
            findings = self._execute_quick_profile(
                run_id=run.id,
                target_path=run.target.repository_path,
                timeout_seconds=run.options.timeout_seconds,
            )
            self._findings[run.id] = findings
            run.findings_count = len(findings)
            run.findings_summary = FindingsSummary.from_findings(findings)
            run.metadata.tools_executed = ["bandit", "gitleaks"]
            run.status = RunStatus.COMPLETED
            run.touch()
            run.completed_at = run.updated_at
        except subprocess.TimeoutExpired:
            run.status = RunStatus.TIMEOUT
            run.error_message = "Scan timed out while executing quick profile"
            run.touch()
            run.completed_at = run.updated_at
        except ToolExecutionError as exc:
            run.status = RunStatus.FAILED
            run.error_message = str(exc)
            run.touch()
            run.completed_at = run.updated_at
        return run

    def fetch_findings(
        self,
        run_id: str,
        *,
        tenant_id: str | None = None,
        min_severity: FindingSeverity | None = None,
    ) -> list[SecurityFinding]:
        """Return findings for a run with optional minimum severity filter."""
        run = self.get_run(run_id, tenant_id=tenant_id)
        if run.status != RunStatus.COMPLETED:
            return []
        findings = self._findings.get(run.id, [])
        if min_severity is None:
            return findings
        min_score = _SEVERITY_ORDER[min_severity]
        return [finding for finding in findings if _SEVERITY_ORDER[finding.severity] >= min_score]

    def cancel_run(self, run_id: str, *, tenant_id: str | None = None) -> SecurityRun:
        """Cancel a non-terminal run."""
        run = self.get_run(run_id, tenant_id=tenant_id)
        if run.status in _TERMINAL_STATES:
            raise RunStateError(f"Run {run.id} is already {run.status.value}")
        run.status = RunStatus.CANCELLED
        run.touch()
        run.completed_at = run.updated_at
        return run

    def delete_run(self, run_id: str, *, tenant_id: str | None = None) -> None:
        """Delete run and associated findings."""
        run = self.get_run(run_id, tenant_id=tenant_id)
        del self._runs[run.id]
        self._findings.pop(run.id, None)

    def _execute_quick_profile(
        self,
        *,
        run_id: str,
        target_path: str,
        timeout_seconds: int,
    ) -> list[SecurityFinding]:
        target = Path(target_path)
        if not target.exists():
            raise ToolExecutionError(f"Scan target does not exist: {target_path}")

        bandit_raw = self._run_bandit(target_path=target_path, timeout_seconds=timeout_seconds)
        gitleaks_raw = self._run_gitleaks(target_path=target_path, timeout_seconds=timeout_seconds)
        findings = self._parse_bandit_findings(run_id=run_id, raw_output=bandit_raw)
        findings.extend(self._parse_gitleaks_findings(run_id=run_id, raw_output=gitleaks_raw))
        return findings

    def _run_bandit(self, *, target_path: str, timeout_seconds: int) -> str:
        command = [sys.executable, "-m", "bandit", "-r", target_path, "-f", "json", "-q"]
        try:
            result = self._command_runner(command, timeout_seconds)
        except FileNotFoundError as exc:
            raise ToolExecutionError(
                "Bandit is not installed in the execution environment"
            ) from exc
        if result.returncode not in {0, 1}:
            error_text = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Bandit execution failed"
            )
            raise ToolExecutionError(error_text)
        return result.stdout

    def _run_gitleaks(self, *, target_path: str, timeout_seconds: int) -> str:
        command = [
            "gitleaks",
            "detect",
            "--source",
            target_path,
            "--report-format",
            "json",
            "--report-path",
            "-",
            "--no-banner",
            "--exit-code",
            "0",
        ]
        try:
            result = self._command_runner(command, timeout_seconds)
        except FileNotFoundError as exc:
            raise ToolExecutionError(
                "gitleaks is not installed in the execution environment"
            ) from exc
        if result.returncode != 0:
            error_text = (
                result.stderr.strip()
                or result.stdout.strip()
                or "gitleaks execution failed"
            )
            raise ToolExecutionError(error_text)
        return result.stdout

    def _run_command(
        self, command: list[str], timeout_seconds: int
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )

    def _parse_bandit_findings(self, *, run_id: str, raw_output: str) -> list[SecurityFinding]:
        if not raw_output.strip():
            return []
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ToolExecutionError("Bandit output was not valid JSON") from exc

        raw_findings = payload.get("results", [])
        findings: list[SecurityFinding] = []
        for issue in raw_findings:
            findings.append(
                SecurityFinding(
                    run_id=run_id,
                    severity=self._map_bandit_severity(issue.get("issue_severity", "")),
                    category=self._map_bandit_category(issue.get("issue_text", "")),
                    title=issue.get("issue_text", "Bandit finding"),
                    description=issue.get("issue_text", "Bandit finding"),
                    tool="bandit",
                    file_path=issue.get("filename", ""),
                    line_number=issue.get("line_number"),
                    remediation=issue.get("more_info", ""),
                    cwe_id=str(issue.get("issue_cwe", {}).get("id") or ""),
                )
            )
        return findings

    def _parse_gitleaks_findings(self, *, run_id: str, raw_output: str) -> list[SecurityFinding]:
        if not raw_output.strip():
            return []
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ToolExecutionError("gitleaks output was not valid JSON") from exc
        if not isinstance(payload, list):
            raise ToolExecutionError("gitleaks output must be a JSON array")

        findings: list[SecurityFinding] = []
        for leak in payload:
            findings.append(
                SecurityFinding(
                    run_id=run_id,
                    severity=FindingSeverity.HIGH,
                    category=FindingCategory.SECRETS_EXPOSURE,
                    title=leak.get("Description", leak.get("RuleID", "gitleaks finding")),
                    description=leak.get("Description", "Potential secret exposure"),
                    tool="gitleaks",
                    file_path=leak.get("File", ""),
                    line_number=leak.get("StartLine"),
                    remediation="Rotate exposed secret and remove it from repository history",
                )
            )
        return findings

    @staticmethod
    def _map_bandit_severity(raw_severity: str) -> FindingSeverity:
        normalized = raw_severity.lower()
        if normalized == "high":
            return FindingSeverity.HIGH
        if normalized == "medium":
            return FindingSeverity.MEDIUM
        if normalized == "low":
            return FindingSeverity.LOW
        return FindingSeverity.INFO

    @staticmethod
    def _map_bandit_category(issue_text: str) -> FindingCategory:
        lowered = issue_text.lower()
        if "inject" in lowered or "exec" in lowered or "subprocess" in lowered:
            return FindingCategory.INJECTION_RISK
        return FindingCategory.CODE_QUALITY
