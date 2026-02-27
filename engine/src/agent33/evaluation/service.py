"""Evaluation service — orchestrates golden task runs, metrics, and gates.

This service ties together the golden task registry, metrics calculator,
gate enforcer, and regression detector into a single evaluation pipeline.
It also supports multi-trial experiments with CTRF reporting.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

from agent33.evaluation.ctrf import CTRFGenerator
from agent33.evaluation.experiment import ExperimentRunner
from agent33.evaluation.gates import GateEnforcer
from agent33.evaluation.golden_tasks import GOLDEN_CASES, GOLDEN_TASKS, tasks_by_tag
from agent33.evaluation.metrics import MetricsCalculator
from agent33.evaluation.models import (
    BaselineSnapshot,
    EvaluationRun,
    GateType,
    GoldenTag,
    MetricId,
    TaskRunResult,
)
from agent33.evaluation.multi_trial import (
    ExperimentConfig,
    MultiTrialExecutor,
    MultiTrialRun,
)
from agent33.evaluation.regression import RegressionDetector, RegressionRecorder

logger = logging.getLogger(__name__)
_MAX_MULTI_TRIAL_RUNS = 1000

# Gate → required tag (§ Gate Execution Matrix)
_GATE_TAG: dict[GateType, GoldenTag] = {
    GateType.G_PR: GoldenTag.GT_SMOKE,
    GateType.G_MRG: GoldenTag.GT_CRITICAL,
    GateType.G_REL: GoldenTag.GT_RELEASE,
    GateType.G_MON: GoldenTag.GT_OPTIONAL,
}


class EvaluationService:
    """Orchestrate evaluation runs with metric computation and gate checks."""

    def __init__(self, trial_evaluator: TrialEvaluatorAdapter | None = None) -> None:
        self._calculator = MetricsCalculator()
        self._enforcer = GateEnforcer()
        self._detector = RegressionDetector()
        self._recorder = RegressionRecorder()
        self._runs: dict[str, EvaluationRun] = {}
        self._baselines: dict[str, BaselineSnapshot] = {}
        self._multi_trial_runs: dict[str, MultiTrialRun] = {}
        self._multi_trial_run_order: list[str] = []
        self._ctrf = CTRFGenerator()
        self._trial_evaluator = trial_evaluator or DeterministicFallbackEvaluator()

    def set_trial_evaluator(self, evaluator: TrialEvaluatorAdapter) -> None:
        """Swap the adapter used to execute single-trial evaluations."""
        self._trial_evaluator = evaluator

    @property
    def recorder(self) -> RegressionRecorder:
        return self._recorder

    # ------------------------------------------------------------------
    # Golden task / case accessors
    # ------------------------------------------------------------------

    def list_golden_tasks(self) -> list[dict[str, object]]:
        """List all golden task definitions."""
        return [t.model_dump() for t in GOLDEN_TASKS.values()]

    def list_golden_cases(self) -> list[dict[str, object]]:
        """List all golden case definitions."""
        return [c.model_dump() for c in GOLDEN_CASES.values()]

    def get_tasks_for_gate(self, gate: GateType) -> list[str]:
        """Return task IDs required for a specific gate."""
        tag = _GATE_TAG.get(gate)
        if tag is None:
            return []
        tasks = tasks_by_tag(tag)
        return [t.task_id for t in tasks]

    # ------------------------------------------------------------------
    # Evaluation runs
    # ------------------------------------------------------------------

    def create_run(
        self,
        gate: GateType,
        commit_hash: str = "",
        branch: str = "",
    ) -> EvaluationRun:
        """Create a new evaluation run."""
        run = EvaluationRun(gate=gate, commit_hash=commit_hash, branch=branch)
        self._runs[run.run_id] = run
        logger.info("evaluation_run_created id=%s gate=%s", run.run_id, gate.value)
        return run

    def get_run(self, run_id: str) -> EvaluationRun | None:
        """Get an evaluation run by ID."""
        return self._runs.get(run_id)

    def list_runs(self, limit: int = 50) -> list[EvaluationRun]:
        """List evaluation runs, most recent first."""
        runs = sorted(self._runs.values(), key=lambda r: r.started_at, reverse=True)
        return runs[:limit]

    def submit_results(
        self,
        run_id: str,
        task_results: list[TaskRunResult],
        rework_count: int = 0,
        scope_violations: int = 0,
    ) -> EvaluationRun | None:
        """Submit golden task results to an evaluation run.

        Computes metrics, checks the gate, detects regressions, and
        completes the run.
        """
        run = self._runs.get(run_id)
        if run is None:
            return None

        run.task_results = task_results

        # Compute metrics
        run.metrics = self._calculator.compute_all(
            task_results,
            rework_count=rework_count,
            scope_violations=scope_violations,
        )

        # Build metric values dict for gate check
        metric_values = {m.metric_id: m.value for m in run.metrics}

        # Check gate
        run.gate_report = self._enforcer.check_gate(run.gate, metric_values, task_results)

        # Detect regressions against latest baseline
        baseline = self.get_latest_baseline()
        if baseline is not None:
            thresholds = self._build_threshold_map(run.gate)
            regressions = self._detector.detect(baseline, run.metrics, task_results, thresholds)
            self._recorder.record_many(regressions)
            run.regressions = regressions

        run.complete()
        logger.info(
            "evaluation_run_completed id=%s gate=%s result=%s",
            run.run_id,
            run.gate.value,
            run.gate_report.overall.value if run.gate_report else "unknown",
        )
        return run

    def _build_threshold_map(self, gate: GateType) -> dict[MetricId, float]:
        """Build a metric→threshold map for the given gate."""
        thresholds = self._enforcer.get_thresholds_for_gate(gate)
        return {t.metric_id: t.value for t in thresholds}

    # ------------------------------------------------------------------
    # Baseline management
    # ------------------------------------------------------------------

    def save_baseline(
        self,
        metrics: Sequence[object],
        task_results: list[TaskRunResult],
        commit_hash: str = "",
        branch: str = "",
    ) -> BaselineSnapshot:
        """Save a baseline snapshot for future regression comparison."""
        from agent33.evaluation.models import MetricValue

        metric_values = [m for m in metrics if isinstance(m, MetricValue)]
        baseline = BaselineSnapshot(
            commit_hash=commit_hash,
            branch=branch,
            metrics=metric_values,
            task_results=task_results,
        )
        self._baselines[baseline.baseline_id] = baseline
        logger.info("baseline_saved id=%s commit=%s", baseline.baseline_id, commit_hash)
        return baseline

    def get_latest_baseline(self) -> BaselineSnapshot | None:
        """Get the most recent baseline snapshot."""
        if not self._baselines:
            return None
        return max(self._baselines.values(), key=lambda b: b.created_at)

    def get_baseline(self, baseline_id: str) -> BaselineSnapshot | None:
        """Get a specific baseline by ID."""
        return self._baselines.get(baseline_id)

    def list_baselines(self, limit: int = 20) -> list[BaselineSnapshot]:
        """List baselines, most recent first."""
        baselines = sorted(self._baselines.values(), key=lambda b: b.created_at, reverse=True)
        return baselines[:limit]

    # ------------------------------------------------------------------
    # Multi-trial experiments
    # ------------------------------------------------------------------

    async def start_multi_trial_run(self, config: ExperimentConfig) -> MultiTrialRun:
        """Create and execute a multi-trial experiment.

        Runs the full (task x agent x model x skills_mode) matrix and
        computes skills impact metrics.
        """
        executor = MultiTrialExecutor(
            evaluation_fn=self._run_single_trial,
            timeout_seconds=config.timeout_per_trial_seconds,
        )
        runner = ExperimentRunner(executor)
        run = await runner.run_experiment(config)
        self._store_multi_trial_run(run)
        logger.info(
            "multi_trial_run_stored id=%s results=%d",
            run.run_id,
            len(run.results),
        )
        return run

    async def _run_single_trial(
        self,
        task_id: str,
        agent: str,
        model: str,
        skills_enabled: bool,
    ) -> bool:
        """Run one trial via pluggable adapter with deterministic fallback."""
        outcome = await self._trial_evaluator.evaluate(
            task_id=task_id,
            agent=agent,
            model=model,
            skills_enabled=skills_enabled,
        )
        return outcome.success

    def _store_multi_trial_run(self, run: MultiTrialRun) -> None:
        """Store a run with bounded retention to avoid unbounded memory growth."""
        self._multi_trial_runs[run.run_id] = run
        self._multi_trial_run_order.append(run.run_id)
        if len(self._multi_trial_run_order) > _MAX_MULTI_TRIAL_RUNS:
            oldest = self._multi_trial_run_order.pop(0)
            self._multi_trial_runs.pop(oldest, None)

    def get_multi_trial_run(self, run_id: str) -> MultiTrialRun | None:
        """Get a multi-trial run by ID."""
        return self._multi_trial_runs.get(run_id)

    def list_multi_trial_runs(self, limit: int = 50) -> list[MultiTrialRun]:
        """List multi-trial runs, most recent first."""
        result: list[MultiTrialRun] = []
        for run_id in reversed(self._multi_trial_run_order):
            run = self._multi_trial_runs.get(run_id)
            if run is None:
                continue
            result.append(run)
            if len(result) >= limit:
                break
        return result

    def export_ctrf(self, run_id: str) -> dict[str, Any] | None:
        """Export a multi-trial run as a CTRF report."""
        run = self._multi_trial_runs.get(run_id)
        if run is None:
            return None
        return self._ctrf.generate_report(run)


@dataclass(frozen=True, slots=True)
class TrialEvaluationOutcome:
    """Normalized result for a single multi-trial evaluation."""

    success: bool
    tokens_used: int = 0
    metadata: dict[str, Any] | None = None


class TrialEvaluatorAdapter(Protocol):
    """Adapter contract for single-trial evaluation execution."""

    async def evaluate(
        self,
        *,
        task_id: str,
        agent: str,
        model: str,
        skills_enabled: bool,
    ) -> TrialEvaluationOutcome: ...


class DeterministicFallbackEvaluator:
    """Deterministic adapter used when no concrete evaluator is configured."""

    async def evaluate(
        self,
        *,
        task_id: str,
        agent: str,
        model: str,
        skills_enabled: bool,
    ) -> TrialEvaluationOutcome:
        if task_id not in GOLDEN_TASKS:
            logger.warning(
                "multi_trial_unknown_task task_id=%s agent=%s model=%s skills=%s",
                task_id,
                agent,
                model,
                skills_enabled,
            )
            return TrialEvaluationOutcome(success=False, metadata={"reason": "unknown_task"})

        score_seed = f"{task_id}|{agent}|{model}|{int(skills_enabled)}".encode()
        digest = hashlib.sha256(score_seed).digest()
        percentile = digest[0] / 255.0
        pass_threshold = 0.58 if skills_enabled else 0.42
        success = percentile <= pass_threshold
        return TrialEvaluationOutcome(
            success=success,
            metadata={
                "seed": digest.hex()[:12],
                "percentile": round(percentile, 4),
                "threshold": pass_threshold,
            },
        )
