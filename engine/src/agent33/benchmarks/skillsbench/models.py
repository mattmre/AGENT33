"""Pydantic models for SkillsBench benchmark runs and trial results."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TrialOutcome(StrEnum):
    """Outcome of a single SkillsBench trial."""

    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class BenchmarkRunStatus(StrEnum):
    """Status of a full benchmark run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrialRecord(BaseModel):
    """Record of a single trial execution."""

    task_id: str = Field(..., description="SkillsBench task ID (category/task_name).")
    trial_number: int = Field(..., ge=1, description="Trial number within this task.")
    outcome: TrialOutcome = Field(..., description="Trial outcome.")
    duration_ms: float = Field(default=0.0, ge=0.0, description="Wall-clock time in ms.")
    tokens_used: int = Field(default=0, ge=0, description="Total tokens consumed.")
    agent: str = Field(default="", description="Agent name used for the trial.")
    model: str = Field(default="", description="LLM model used for the trial.")
    skills_enabled: bool = Field(default=False, description="Whether skills were enabled.")
    iterations: int = Field(default=0, ge=0, description="Iterative loop iterations.")
    tool_calls_made: int = Field(default=0, ge=0, description="Number of tool calls made.")
    termination_reason: str = Field(default="", description="Why the agent stopped.")
    pytest_returncode: int = Field(default=-1, description="Raw pytest return code.")
    error_message: str = Field(default="", description="Error details if outcome is ERROR.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra metadata.")

    @property
    def passed(self) -> bool:
        """Whether this trial passed."""
        return self.outcome == TrialOutcome.PASSED


class TaskFilter(BaseModel):
    """Filter criteria for selecting SkillsBench tasks."""

    categories: list[str] = Field(
        default_factory=list,
        description="Include only these categories. Empty means all.",
    )
    exclude_categories: list[str] = Field(
        default_factory=list,
        description="Exclude these categories.",
    )
    task_ids: list[str] = Field(
        default_factory=list,
        description="Include only specific task IDs. Empty means all.",
    )
    max_tasks: int = Field(
        default=0,
        ge=0,
        description="Maximum number of tasks to include. 0 means unlimited.",
    )


class BenchmarkRunResult(BaseModel):
    """Aggregated result of a complete SkillsBench benchmark run."""

    run_id: str = Field(default="", description="Unique run identifier.")
    status: BenchmarkRunStatus = Field(default=BenchmarkRunStatus.PENDING)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)
    config_summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration snapshot for this run.",
    )
    trials: list[TrialRecord] = Field(default_factory=list)
    total_tasks: int = Field(default=0, ge=0)
    total_trials: int = Field(default=0, ge=0)
    passed_trials: int = Field(default=0, ge=0)
    failed_trials: int = Field(default=0, ge=0)
    error_trials: int = Field(default=0, ge=0)
    pass_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    total_tokens_used: int = Field(default=0, ge=0)
    total_duration_ms: float = Field(default=0.0, ge=0.0)

    def compute_aggregates(self) -> None:
        """Recompute aggregate fields from the trials list."""
        self.total_trials = len(self.trials)
        self.passed_trials = sum(1 for t in self.trials if t.outcome == TrialOutcome.PASSED)
        self.failed_trials = sum(1 for t in self.trials if t.outcome == TrialOutcome.FAILED)
        self.error_trials = sum(1 for t in self.trials if t.outcome == TrialOutcome.ERROR)
        self.total_tokens_used = sum(t.tokens_used for t in self.trials)
        self.total_duration_ms = sum(t.duration_ms for t in self.trials)
        self.pass_rate = self.passed_trials / self.total_trials if self.total_trials > 0 else 0.0
        task_ids = {t.task_id for t in self.trials}
        self.total_tasks = len(task_ids)
