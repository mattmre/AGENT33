# Session 51 Baseline PR Stack Recovery Findings

Date: 2026-03-04

## Context

Session 50 produced a large PR stack (`#97`-`#105`) intended to land hooks, plugins, skill packs, SkillsBench integration, AWM comparative scoring, CI gate tightening, and refreshed handoff docs. Every open PR showed the same failing checks (`lint`, `test`, `build`, `benchmark-smoke`), which initially looked like branch-local breakage.

## Root Cause Summary

The failures are a mix of:

1. Shared baseline issues already present on `main`
2. Stack-order issues caused by PR dependencies not yet merged
3. Runner-tooling drift between local development environments and CI

## Findings

### 1. Frontend build failure was a baseline file hygiene issue

`frontend/src/styles.css` contained a stray merge marker:

```css
<<<<<<< HEAD
```

This caused Vite/PostCSS to fail during the Docker build with:

`Unknown word <<<<<<<`

The problem is not specific to any Session 50 branch; every PR inherits it from `main`.

### 2. `benchmark-smoke` was failing because repo-wide coverage thresholds applied to a smoke-only slice

`engine/pyproject.toml` defines global pytest addopts:

- `--cov=agent33`
- `--cov-report=term-missing`
- `--cov-fail-under=70`

The `benchmark-smoke` job runs only `tests/benchmarks/test_skills_smoke.py`, which is intentionally tiny. The tests themselves pass, but the job exits non-zero because overall coverage for that tiny subset is about 26%.

The correct fix is to opt the smoke benchmark invocation out of coverage with `--no-cov`.

### 3. Formatter drift on `main` was already failing the lint job

Before touching the Session 50 branches, `main` already failed:

```bash
python -m ruff format --check engine/src engine/tests
```

The drift was limited to:

- `engine/src/agent33/api/routes/webhooks.py`
- `engine/src/agent33/llm/airllm_provider.py`
- `engine/src/agent33/main.py`
- `engine/src/agent33/workflows/checkpoint.py`

This means feature PRs were inheriting a failing lint baseline even before their branch-specific formatting was considered.

### 4. CI Ruff was stricter than the local environment used for some earlier work

Representative CI logs showed `UP042` suggestions to replace `str, Enum` patterns with `StrEnum` in:

- `engine/src/agent33/agents/isc.py`
- `engine/src/agent33/agents/reasoning.py`
- `engine/src/agent33/api/routes/reasoning.py`
- `engine/src/agent33/connectors/circuit_breaker.py`

Those updates are safe on Python 3.11 and align the repo with the newer Ruff behavior used by CI.

### 5. PR `#99` is a prerequisite for the rest of the Session 50 test stack

Representative `test` job logs on PR `#98` still failed on the old multimodal `run_async` API assumption:

- `tests/test_connector_boundary_multimodal_adapters.py`

That is expected until PR `#99` is merged or rebased into later branches.

## Strategy Decision

The correct sequencing is:

1. Create and merge a fresh baseline repair PR from `main`
2. Rebase the Session 50 PR stack onto that repaired baseline
3. Merge the Session 50 stack in dependency order:
   - `#99`
   - `#97`
   - `#98`
   - `#100`
   - `#103`
   - `#102`
   - `#101`
   - `#104`
   - `#105`

This avoids repeating baseline fixes across every branch and makes later CI failures meaningful.

## Local Validation Used for Baseline Repair

- `python -m ruff check engine/src engine/tests`
- `python -m ruff format --check engine/src engine/tests`
- `python -m pytest engine/tests/benchmarks/test_skills_smoke.py -q --no-cov`
- `npx vite build` from `frontend/`

## Notes

- A local Windows `npm run build` invocation did not find `vite`, but `npx vite build` succeeded after `npm ci`. The Linux CI container already resolves `vite` correctly, so this appears to be a local shell/path quirk rather than a repo dependency defect.
