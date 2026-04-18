# Session 128 R2 scope lock - P-ENV v2 and launch-doc reliability

## Goal

Make the P-ENV v2 bootstrap path internally consistent on merged `main` and fix
the operator-facing reliability/documentation issues left by PRs `#407` and
`#408`.

## Baseline

- Fresh worktree: `C:\GitHub\repos\AGENT33\worktrees\session128-s2-penv2-hardening`
- Branch: `session128-s2-penv2-hardening`
- Base commit: `0918881` (`Session 128: harden pack/session lifecycle cleanup (#409)`)
- R1 is merged and fresh-main verified.

## Confirmed issues on main

1. Runtime settings still load `.env`, while wizard/bootstrap write `.env.local`.
2. The canonical default Ollama model still drifts between runtime defaults,
   bootstrap/wizard output, and docs (`llama3.2` vs `llama3.2:3b`).
3. Bundled Ollama startup swallows useful `docker compose` stdout/stderr on
   failure.
4. Wizard env refresh still uses an overly broad `TypeError` fallback.
5. Ollama model pull timeout remains a hardcoded 900 seconds, which is short for
   the recommended larger models.
6. Setup docs still do not describe a reliable first-time bootstrap/start path.

## Tight implementation sequence

1. Align runtime env loading with `.env.local` first, falling back to `.env`.
2. Standardize the default Ollama model string to `llama3.2:3b` across runtime,
   bootstrap/wizard output, and docs.
3. Narrow or remove the broad `TypeError` fallback in wizard env refresh based
   on the current `detect_env()` signature.
4. Surface bundled `docker compose` diagnostics when Ollama startup fails.
5. Increase the default Ollama pull timeout to cover the recommended models.
6. Update setup docs with an explicit first-time path and corrected model
   examples.

## Likely code/doc surfaces

- `engine/src/agent33/config.py`
- `engine/src/agent33/env/detect.py`
- `engine/src/agent33/env/ollama_setup.py`
- `engine/src/agent33/cli/wizard.py`
- `engine/src/agent33/cli/bootstrap.py`
- `docs/setup-guide.md`
- potentially `docs/getting-started.md`, `docs/ONBOARDING.md`, `frontend/README.md`

## Validation target

- targeted pytest for config/env/wizard/bootstrap/diagnose surfaces
- `ruff check`
- `ruff format --check`
- `mypy` on touched Python files

## Scope guardrails

- Keep this slice limited to reliability and correctness fixes.
- Do not start the pack marketplace UI until this PR is merged and fresh-main
  verified.
