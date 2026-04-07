# AGENT-33 SkillsBench Results

This branch stores SkillsBench benchmark results to avoid cluttering `main` git history.

## Latest Baseline

See `ctrf-baseline-latest.json`.

## How Results Are Added

Automated weekly runs commit here via the `benchmarks-weekly` GitHub Actions workflow.
Each run creates `ctrf-baseline-YYYY-MM-DD.json` and updates `ctrf-baseline-latest.json`.

## Manual Run

```bash
git clone --branch benchmarks https://github.com/mattmre/AGENT33 agent33-benchmarks
```
