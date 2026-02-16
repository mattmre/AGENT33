"""CTRF (Common Test Report Format) report generator.

Produces CTRF-compliant JSON reports from multi-trial evaluation runs.
See https://ctrf.io/ for the specification.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from agent33.evaluation.multi_trial import MultiTrialRun

logger = logging.getLogger(__name__)


class CTRFGenerator:
    """Generates CTRF-compliant test result reports."""

    TOOL_NAME = "agent33-eval"
    TOOL_VERSION = "1.0.0"

    def __init__(self, pass_threshold: float = 0.6) -> None:
        self._pass_threshold = pass_threshold

    def generate_report(self, run: MultiTrialRun) -> dict[str, Any]:
        """Generate a full CTRF report from a MultiTrialRun."""
        tests: list[dict[str, Any]] = []
        total_passed = 0
        total_failed = 0
        total_skipped = 0

        for result in run.results:
            status = (
                "passed"
                if result.pass_rate >= self._pass_threshold
                else "failed"
            )
            if status == "passed":
                total_passed += 1
            else:
                total_failed += 1

            skills_label = " +skills" if result.skills_enabled else " -skills"
            tests.append({
                "name": (
                    f"{result.task_id} [{result.agent}/{result.model}]"
                    + skills_label
                ),
                "status": status,
                "duration": result.total_duration_ms,
                "extra": {
                    "trials": len(result.trials),
                    "pass_rate": result.pass_rate,
                    "variance": result.variance,
                    "skills_enabled": result.skills_enabled,
                    "agent": result.agent,
                    "model": result.model,
                    "tokens_used": result.total_tokens,
                    "trial_results": [t.score for t in result.trials],
                },
            })

        start_ms = int(run.started_at.timestamp() * 1000)
        stop_ms = (
            int(run.completed_at.timestamp() * 1000)
            if run.completed_at
            else start_ms
        )

        return {
            "results": {
                "tool": {
                    "name": self.TOOL_NAME,
                    "version": self.TOOL_VERSION,
                },
                "summary": {
                    "tests": len(tests),
                    "passed": total_passed,
                    "failed": total_failed,
                    "skipped": total_skipped,
                    "pending": 0,
                    "other": 0,
                    "start": start_ms,
                    "stop": stop_ms,
                },
                "tests": tests,
            },
        }

    def generate_summary(self, run: MultiTrialRun) -> dict[str, Any]:
        """Generate summary statistics for a run."""
        if not run.results:
            return {"total_combinations": 0, "avg_pass_rate": 0.0}
        avg_pass = sum(r.pass_rate for r in run.results) / len(run.results)
        avg_var = sum(r.variance for r in run.results) / len(run.results)
        return {
            "total_combinations": len(run.results),
            "avg_pass_rate": round(avg_pass, 4),
            "avg_variance": round(avg_var, 4),
            "consistency": round(1 - avg_var, 4),
            "skills_impacts_count": len(run.skills_impacts),
        }

    def write_report(self, run: MultiTrialRun, path: Path) -> None:
        """Write CTRF JSON report to disk."""
        report = self.generate_report(run)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2))
        logger.info("ctrf_report_written path=%s", path)
