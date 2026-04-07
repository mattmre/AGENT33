# AGENT-33 Benchmarks

This directory contains benchmark run metadata for the `main` branch.

## SkillsBench Results

Full SkillsBench results are stored on the [`benchmarks`](https://github.com/mattmre/AGENT33/tree/benchmarks) branch to avoid polluting `main` git history with large JSON files.

### Viewing Results

```bash
# List available runs
git fetch origin benchmarks
git show origin/benchmarks:README.md

# Get the latest baseline
git show origin/benchmarks:baselines/ctrf-baseline-latest.json | agent33 bench report -
```

### Running Benchmarks

```bash
# Full run (requires SkillsBench checkout + live LLM)
agent33 bench run --skillsbench-root ./skillsbench --output ctrf-report.json --model llama3.2

# Quick smoke suite (deterministic, no LLM required)
agent33 bench smoke --output ctrf-smoke.json

# Compare against baseline
agent33 bench report ctrf-report.json --baseline ctrf-baseline.json
```

### CI Integration

- **Smoke suite**: Runs on every PR via `benchmark-smoke` CI job (`continue-on-error: true`)
- **Full run**: Runs weekly via scheduled workflow; results committed to `benchmarks` branch
- **Regression alert**: GitHub issue opened automatically if any category drops >5% vs baseline

### Baseline Files

| File | Description |
|---|---|
| `baselines/ctrf-baseline-latest.json` | Latest committed baseline (from most recent full run) |
| `baselines/ctrf-baseline-YYYY-MM-DD.json` | Historical baselines by date |
