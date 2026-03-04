# Session 53 Research: Confidence Gate Baseline Alignment

Date: 2026-03-04
Scope: Priority #1 (`main` confidence gate) preflight hardening

## Problem

Running local gate commands with mixed environments surfaced inconsistent mypy results for optional dependencies. The same source tree produced:

- missing-import errors when optional packages were absent
- unused-ignore errors when optional packages were present

This made confidence-gate runs noisy and environment-sensitive.

## Root Cause

`engine/pyproject.toml` mypy override list did not include all optional dependency modules imported conditionally in runtime code:

- `playwright.*`
- `transformers.*`
- `PIL.*`

At the same time, several source files had import-level `type: ignore[import-not-found]` comments that became stale once the package was installed, tripping strict `unused-ignore`.

## Implemented Hardening

1. Added optional module families to mypy `ignore_missing_imports` overrides:
   - `playwright`, `playwright.*`
   - `transformers`, `transformers.*`
   - `PIL`, `PIL.*`
2. Removed local import-level `type: ignore` comments in:
   - `engine/src/agent33/tools/builtin/browser.py`
   - `engine/src/agent33/llm/airllm_provider.py`
   - `engine/src/agent33/memory/ingestion.py`

## Validation Evidence

Executed in the feature worktree using CI-aligned Python 3.11:

- `uv run --python 3.11 --extra dev ruff check src tests`
- `uv run --python 3.11 --extra dev ruff format --check src tests`
- `uv run --python 3.11 --extra dev mypy src --config-file pyproject.toml`
- `uv run --python 3.11 --extra dev pytest tests/ -q`

Results:

- Ruff check: pass
- Ruff format check: pass
- Mypy strict: pass (`no issues found in 297 source files`)
- Full tests: pass (`2586 passed`, coverage threshold satisfied)

## Notes

- A Python 3.12 full-suite run showed one plugin-base mismatch; the same suite on Python 3.11 passed cleanly.
- CI is pinned to Python 3.11, so confidence gates should use that interpreter for reproducible parity.
