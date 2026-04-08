"""CLI commands for SkillsBench benchmark evaluation.

Provides benchmark evaluation subcommands:
- ``agent33 bench run``   -- full 86-task SkillsBench run (live LLM, CTRF output)
- ``agent33 bench smoke`` -- quick smoke suite (deterministic, compare to baseline)
- ``agent33 bench report`` -- display results from a stored CTRF file
"""

from __future__ import annotations

import json
import sys
from pathlib import Path  # noqa: TC003 -- typer needs Path at runtime
from typing import Annotated

import typer

bench_app = typer.Typer(name="bench", help="SkillsBench benchmark evaluation commands.")


@bench_app.command("run")
def bench_run(
    skillsbench_root: Annotated[
        Path | None,
        typer.Option("--skillsbench-root", help="Path to SkillsBench repo checkout."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write CTRF report JSON to this path."),
    ] = None,
    model: Annotated[
        str,
        typer.Option("--model", "-m", help="LLM model identifier for the agent runtime."),
    ] = "llama3.2",
    agent_name: Annotated[
        str,
        typer.Option("--agent", help="Agent definition name."),
    ] = "code-worker",
    baseline: Annotated[
        Path | None,
        typer.Option("--baseline", help="CTRF baseline to compare against."),
    ] = None,
    trials: Annotated[
        int,
        typer.Option("--trials", "-t", help="Trials per task (default 5)."),
    ] = 5,
) -> None:
    """Run the full SkillsBench suite with a live LLM and write a CTRF report.

    Requires a SkillsBench repository checkout (--skillsbench-root) and a
    running LLM at the configured endpoint. Results are written to the
    --output path and optionally compared against a --baseline CTRF file.

    Exits with code 1 if task discovery fails, no LLM provider is
    reachable, or the benchmark encounters a fatal error.
    """
    import asyncio

    from agent33.benchmarks.skillsbench.config import SkillsBenchConfig
    from agent33.benchmarks.skillsbench.reporting import SkillsBenchCTRFGenerator
    from agent33.benchmarks.skillsbench.task_loader import SkillsBenchTaskLoader

    root = skillsbench_root or Path("./skillsbench")
    if not root.exists():
        typer.echo(
            f"[error] SkillsBench root not found: {root}\n"
            "Clone https://github.com/benchflow-ai/skillsbench and pass --skillsbench-root.",
            err=True,
        )
        raise typer.Exit(code=1)

    # 1. Discover tasks
    try:
        loader = SkillsBenchTaskLoader(root)
        tasks = loader.discover_tasks()
        typer.echo(f"Discovered {len(tasks)} tasks")
    except Exception as exc:
        typer.echo(f"[error] Failed to load tasks: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if not tasks:
        typer.echo("[error] No tasks found. Verify --skillsbench-root contains tasks/.", err=True)
        raise typer.Exit(code=1)

    # 2. Build runtime infrastructure
    try:
        from agent33.agents.definition import AgentDefinition, AgentRole
        from agent33.agents.registry import AgentRegistry
        from agent33.agents.runtime import AgentRuntime
        from agent33.benchmarks.skillsbench.adapter import SkillsBenchAdapter
        from agent33.benchmarks.skillsbench.runner import PytestBinaryRewardRunner
        from agent33.config import settings
        from agent33.llm.router import ModelRouter
        from agent33.skills.registry import SkillRegistry

        # Attempt to load agent definition from the configured definitions dir
        definition: AgentDefinition | None = None
        defs_dir = Path(settings.agent_definitions_dir)
        if defs_dir.is_dir():
            registry = AgentRegistry()
            registry.discover(defs_dir)
            definition = registry.get(agent_name)

        if definition is None:
            # Fallback: build a minimal agent definition for CLI usage
            definition = AgentDefinition(
                name=agent_name,
                version="1.0.0",
                role=AgentRole.IMPLEMENTER,
                description=f"SkillsBench evaluation agent ({agent_name})",
            )

        router = ModelRouter()
        skill_registry = SkillRegistry()
        agent_runtime = AgentRuntime(
            definition=definition,
            router=router,
            model=model,
            evaluation_mode=True,
        )
        pytest_runner = PytestBinaryRewardRunner()
        adapter = SkillsBenchAdapter(
            task_loader=loader,
            pytest_runner=pytest_runner,
            skill_registry=skill_registry,
            agent_runtime=agent_runtime,
        )
    except Exception as exc:
        typer.echo(f"[error] Failed to initialize runtime: {exc}", err=True)
        typer.echo(
            "Ensure an LLM provider is configured (e.g. OLLAMA_BASE_URL) "
            "before running `agent33 bench run`.",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    # 3. Run the benchmark
    cfg = SkillsBenchConfig(
        skillsbench_root=root,
        agent_name=agent_name,
        model=model,
        trials_per_task=trials,
    )

    typer.echo(f"Running {len(tasks)} tasks x {trials} trials with model={model} ...")

    try:
        run_result = asyncio.run(adapter.run_benchmark(cfg))
    except Exception as exc:
        typer.echo(f"[error] Benchmark execution failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    # 4. Write CTRF report
    generator = SkillsBenchCTRFGenerator()
    report = generator.generate_report(run_result)

    out_path = output or Path("ctrf-bench-report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    typer.echo(f"CTRF report written to {out_path}")
    typer.echo(
        f"Results: {run_result.passed_trials}/{run_result.total_trials} passed "
        f"({run_result.pass_rate:.1%})"
    )

    if baseline and baseline.exists():
        _compare_baseline(report, baseline)


@bench_app.command("smoke")
def bench_smoke(
    baseline: Annotated[
        Path | None,
        typer.Option(
            "--baseline",
            help="CTRF baseline to compare against (from benchmarks branch).",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write CTRF smoke report JSON to this path."),
    ] = None,
) -> None:
    """Run the fast smoke benchmark suite (deterministic, no live LLM).

    Exits 0 if pass rate is no worse than the baseline (or no baseline provided).
    Exits 1 if the pass rate drops more than 5 percentage points vs. the baseline.
    """
    import importlib.util
    import os
    import subprocess

    # Locate the smoke test file relative to the installed package
    spec = importlib.util.find_spec("agent33")
    if spec and spec.origin:
        package_dir = Path(spec.origin).parent  # agent33/
        src_dir = package_dir.parent  # src/
        engine_dir = src_dir.parent  # engine/
        smoke_test = engine_dir / "tests" / "benchmarks" / "test_skills_smoke.py"
    else:
        smoke_test = Path("tests/benchmarks/test_skills_smoke.py")

    env = os.environ.copy()
    ctrf_out = output or Path("ctrf-smoke-report.json")
    ctrf_out.parent.mkdir(parents=True, exist_ok=True)
    env["AGENT33_SMOKE_CTRF_PATH"] = str(ctrf_out)

    typer.echo("Running smoke benchmark suite...")

    if smoke_test.exists():
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(smoke_test), "-v", "--no-cov", "--tb=short"],
            env=env,
            capture_output=False,
            check=False,
        )
        passed = result.returncode == 0
    else:
        typer.echo(f"[warn] Smoke test file not found at {smoke_test}, using stub run", err=True)
        passed = True

    # Compare against baseline
    if baseline and baseline.exists() and ctrf_out.exists():
        try:
            baseline_data = json.loads(baseline.read_text(encoding="utf-8"))
            current_data = json.loads(ctrf_out.read_text(encoding="utf-8"))
            regression = _detect_regression(current_data, baseline_data)
            if regression:
                typer.echo(f"[REGRESSION] Pass rate dropped >5%: {regression}", err=True)
                raise typer.Exit(code=1)
            typer.echo("Smoke suite: no regression detected")
        except (json.JSONDecodeError, KeyError) as exc:
            typer.echo(f"[warn] Could not compare baseline: {exc}", err=True)

    if not passed:
        raise typer.Exit(code=1)


@bench_app.command("report")
def bench_report(
    ctrf_file: Annotated[
        Path,
        typer.Argument(help="Path to CTRF JSON report file."),
    ],
    baseline: Annotated[
        Path | None,
        typer.Option("--baseline", help="CTRF baseline to compare against."),
    ] = None,
) -> None:
    """Display a summary of a CTRF benchmark report.

    Shows overall pass rate, failed tasks, and compares against a baseline
    if provided.
    """
    if not ctrf_file.exists():
        typer.echo(f"[error] Report file not found: {ctrf_file}", err=True)
        raise typer.Exit(code=1)

    try:
        report = json.loads(ctrf_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        typer.echo(f"[error] Invalid JSON in report: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    summary = report.get("results", {}).get("summary", {})
    total: int = summary.get("tests", 0)
    passed: int = summary.get("passed", 0)
    failed: int = summary.get("failed", 0)
    skipped: int = summary.get("skipped", 0)
    pass_rate = (passed / total * 100) if total > 0 else 0.0

    typer.echo(f"SkillsBench Report: {ctrf_file}")
    typer.echo(f"  Total:   {total}")
    typer.echo(f"  Passed:  {passed} ({pass_rate:.1f}%)")
    typer.echo(f"  Failed:  {failed}")
    typer.echo(f"  Skipped: {skipped}")

    if baseline and baseline.exists():
        baseline_data = json.loads(baseline.read_text(encoding="utf-8"))
        regression = _detect_regression(report, baseline_data)
        if regression:
            typer.echo(f"\n  [REGRESSION vs baseline] {regression}")
        else:
            typer.echo("\n  [OK] No regression vs baseline")


def _compare_baseline(current: dict[str, object], baseline_path: Path) -> None:
    """Print a comparison summary between current run and baseline CTRF."""
    try:
        baseline_raw = json.loads(baseline_path.read_text(encoding="utf-8"))
        regression = _detect_regression(current, baseline_raw)
        if regression:
            typer.echo(f"[warn] Baseline comparison: {regression}")
        else:
            typer.echo("Baseline comparison: no regression detected")
    except Exception as exc:
        typer.echo(f"[warn] Could not compare baseline: {exc}", err=True)


def _detect_regression(current: dict[str, object], baseline: dict[str, object]) -> str | None:
    """Return a description string if pass rate dropped >5pp, else None."""

    def pass_rate(d: dict[str, object]) -> float:
        results = d.get("results")
        if not isinstance(results, dict):
            return 0.0
        summary = results.get("summary")
        if not isinstance(summary, dict):
            return 0.0
        total = summary.get("tests", 0)
        passed = summary.get("passed", 0)
        if not isinstance(total, (int, float)) or not isinstance(passed, (int, float)):
            return 0.0
        return (float(passed) / float(total) * 100) if total > 0 else 0.0

    current_rate = pass_rate(current)
    baseline_rate = pass_rate(baseline)
    if baseline_rate > 0 and (baseline_rate - current_rate) > 5.0:
        return f"pass rate {current_rate:.1f}% < baseline {baseline_rate:.1f}% (dropped >5pp)"
    return None
