"""SkillsBench smoke benchmark tests.

Fast, deterministic smoke tests that validate core evaluation service functionality.
Tests use existing EvaluationService and CTRF reporting infrastructure.

These benchmarks are non-blocking in CI and generate CTRF reports for artifact upload.
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from agent33.evaluation.ctrf import CTRFGenerator
from agent33.evaluation.models import GateType
from agent33.evaluation.multi_trial import (
    ExperimentConfig,
    MultiTrialResult,
    MultiTrialRun,
    TrialResult,
)
from agent33.evaluation.service import EvaluationService

pytestmark = [pytest.mark.benchmark, pytest.mark.smoke]


def write_benchmark_ctrf(
    test_results: list[dict[str, Any]],
    output_path: Path | None = None,
    tool_name: str = "agent33-benchmark-smoke",
) -> None:
    """Write pytest benchmark results as CTRF report.

    Args:
        test_results: List of test dicts with name, status, duration_ms
        output_path: Path to write CTRF JSON (from env or default)
        tool_name: Tool identifier for report
    """
    if output_path is None:
        env_path = os.environ.get("AGENT33_SMOKE_CTRF_PATH")
        output_path = Path(env_path) if env_path else Path("test-results/ctrf-smoke-report.json")

    # Calculate summary statistics
    total = len(test_results)
    passed = sum(1 for t in test_results if t["status"] == "passed")
    failed = sum(1 for t in test_results if t["status"] == "failed")
    skipped = sum(1 for t in test_results if t["status"] == "skipped")

    # Get timing bounds
    start_time = min((t.get("start_ms", 0) for t in test_results), default=0)
    stop_time = max((t.get("stop_ms", 0) for t in test_results), default=0)

    # Build CTRF-compliant report
    report = {
        "results": {
            "tool": {
                "name": tool_name,
                "version": "1.0.0",
            },
            "summary": {
                "tests": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pending": 0,
                "other": 0,
                "start": start_time,
                "stop": stop_time,
            },
            "tests": [
                {
                    "name": t["name"],
                    "status": t["status"],
                    "duration": t["duration_ms"],
                }
                for t in test_results
            ],
        },
    }

    # Write report to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2))


class TestSkillsBenchSmoke:
    """Smoke tests for SkillsBench evaluation harness.

    These tests validate core functionality of the evaluation service,
    CTRF reporting, and integration touchpoints. All tests are designed
    to be fast (<100ms each) and deterministic.
    """

    def test_service_initialization(self) -> None:
        """Verify EvaluationService initializes without errors.

        Tests:
        - Service creation
        - Component wiring (calculator, enforcer, detector)
        - Internal registries initialization
        """
        start = time.perf_counter()

        service = EvaluationService()

        # Verify service instance
        assert service is not None
        assert hasattr(service, "recorder")

        # Verify internal components exist
        assert service._calculator is not None
        assert service._enforcer is not None
        assert service._detector is not None
        assert service._recorder is not None
        assert service._ctrf is not None

        # Verify registries are initialized
        assert isinstance(service._runs, dict)
        assert isinstance(service._baselines, dict)
        assert isinstance(service._multi_trial_runs, dict)

        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"Service init took {elapsed:.3f}s, expected <100ms"

    def test_golden_tasks_registry(self) -> None:
        """Verify golden task registry is accessible and populated.

        Tests:
        - list_golden_tasks() returns non-empty list
        - Task schema is valid (has required fields)
        - list_golden_cases() is accessible
        """
        start = time.perf_counter()

        service = EvaluationService()

        # Test golden tasks
        tasks = service.list_golden_tasks()
        assert tasks is not None
        assert isinstance(tasks, list)
        assert len(tasks) > 0, "Golden task registry should not be empty"

        # Verify task structure
        first_task = tasks[0]
        assert "task_id" in first_task
        assert isinstance(first_task["task_id"], str)

        # Test golden cases
        cases = service.list_golden_cases()
        assert cases is not None
        assert isinstance(cases, list)

        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"Registry access took {elapsed:.3f}s, expected <100ms"

    def test_ctrf_report_generation(self) -> None:
        """Verify CTRF report can be generated from test run.

        Tests:
        - CTRFGenerator integration
        - Schema compliance (required fields)
        - MultiTrialRun → CTRF conversion
        """
        start = time.perf_counter()

        # Create a minimal MultiTrialRun
        trial = TrialResult(trial_number=1, score=1, duration_ms=50)
        result = MultiTrialResult(
            task_id="test-task",
            agent="test-agent",
            model="test-model",
            skills_enabled=True,
            trials=[trial],
            total_tokens=100,
            total_duration_ms=50,
        )
        run = MultiTrialRun(
            run_id="test-run-id",
            config=ExperimentConfig(
                tasks=["test-task"],
                agents=["test-agent"],
                models=["test-model"],
            ),
            results=[result],
            started_at=datetime.now(UTC),
        )

        # Generate CTRF report
        generator = CTRFGenerator()
        report = generator.generate_report(run)

        # Verify CTRF schema compliance
        assert "results" in report
        assert "tool" in report["results"]
        assert "summary" in report["results"]
        assert "tests" in report["results"]

        # Verify tool info
        assert report["results"]["tool"]["name"] == "agent33-eval"
        assert "version" in report["results"]["tool"]

        # Verify summary
        summary = report["results"]["summary"]
        assert summary["tests"] == 1
        assert summary["passed"] + summary["failed"] == 1
        assert "start" in summary
        assert "stop" in summary

        # Verify test entries
        tests = report["results"]["tests"]
        assert len(tests) == 1
        assert tests[0]["name"] == "test-task [test-agent/test-model] +skills"
        assert tests[0]["status"] in ["passed", "failed"]
        assert "duration" in tests[0]

        elapsed = time.perf_counter() - start
        assert elapsed < 0.15, f"CTRF generation took {elapsed:.3f}s, expected <150ms"

    def test_gate_type_enumeration(self) -> None:
        """Verify gate types are defined and queryable.

        Tests:
        - GateType enum is accessible
        - get_tasks_for_gate() returns task lists
        - Known gates have defined task mappings
        """
        start = time.perf_counter()

        service = EvaluationService()

        # Test GateType enum
        assert hasattr(GateType, "G_PR")
        assert hasattr(GateType, "G_MRG")
        assert hasattr(GateType, "G_REL")
        assert hasattr(GateType, "G_MON")

        # Test get_tasks_for_gate for each gate type
        for gate in [GateType.G_PR, GateType.G_MRG, GateType.G_REL, GateType.G_MON]:
            tasks = service.get_tasks_for_gate(gate)
            assert tasks is not None
            assert isinstance(tasks, list)
            # Smoke gate should have at least one task
            if gate == GateType.G_PR:
                assert len(tasks) > 0, "G-PR gate should have smoke tasks"

        elapsed = time.perf_counter() - start
        assert elapsed < 0.1, f"Gate enumeration took {elapsed:.3f}s, expected <100ms"

    @pytest.mark.asyncio
    async def test_multi_trial_executes_three_golden_tasks(self) -> None:
        """Run a minimal 3-task multi-trial smoke experiment."""
        service = EvaluationService()
        config = ExperimentConfig(
            tasks=["GT-01", "GT-04", "GT-06"],
            agents=["smoke-agent"],
            models=["smoke-model"],
            trials_per_combination=1,
            skills_modes=[True, False],
            timeout_per_trial_seconds=15,
            parallel_trials=1,
        )
        run = await service.start_multi_trial_run(config)

        assert run.status == "completed"
        assert len(run.results) == 6  # 3 tasks x 1 agent x 1 model x 2 skills modes
        assert len(run.skills_impacts) == 3
        assert all(result.pass_rate == 1.0 for result in run.results)

    @pytest.mark.asyncio
    async def test_multi_trial_ctrf_export_contains_expected_counts(self) -> None:
        """Ensure CTRF export reflects smoke multi-trial execution."""
        service = EvaluationService()
        run = await service.start_multi_trial_run(
            ExperimentConfig(
                tasks=["GT-01", "GT-02", "GT-03"],
                agents=["smoke-agent"],
                models=["smoke-model"],
                trials_per_combination=1,
                skills_modes=[True],
                timeout_per_trial_seconds=15,
                parallel_trials=1,
            )
        )

        report = service.export_ctrf(run.run_id)
        assert report is not None
        assert report["results"]["summary"]["tests"] == 3
        assert report["results"]["summary"]["failed"] == 0

        # Write to CI artifact path if env var is set
        ctrf_path = os.environ.get("AGENT33_SMOKE_CTRF_PATH")
        if ctrf_path:
            output_path = Path(ctrf_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2))


def test_write_ctrf_helper(tmp_path: Path) -> None:
    """Test that CTRF helper writes valid reports.

    This test validates the write_benchmark_ctrf helper function
    using a temporary directory to avoid overwriting CI artifacts.
    """
    # Sample test results
    test_results = [
        {
            "name": "test_example_pass",
            "status": "passed",
            "duration_ms": 42,
            "start_ms": 1700000000000,
            "stop_ms": 1700000000042,
        },
        {
            "name": "test_example_fail",
            "status": "failed",
            "duration_ms": 15,
            "start_ms": 1700000000100,
            "stop_ms": 1700000000115,
        },
    ]

    # Write to temporary path instead of CI artifact path
    output_path = tmp_path / "ctrf-helper-test.json"

    # Write the report
    write_benchmark_ctrf(test_results, output_path)

    # Verify the file was created and is valid JSON
    assert output_path.exists(), f"CTRF report not created at {output_path}"

    # Parse and validate schema
    with open(output_path) as f:
        report = json.load(f)

    # Verify CTRF structure
    assert "results" in report
    assert "tool" in report["results"]
    assert "summary" in report["results"]
    assert "tests" in report["results"]

    # Verify summary counts
    summary = report["results"]["summary"]
    assert summary["tests"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1

    # Verify test entries
    tests = report["results"]["tests"]
    assert len(tests) == 2
    assert tests[0]["name"] == "test_example_pass"
    assert tests[0]["status"] == "passed"
