# P4.17 Plugin SDK Real-World Validation -- Scope

**Session**: 109
**Branch**: `feat/p417-plugin-sdk-validation`
**Date**: 2026-03-25

## Included Work

1. **`engine/src/agent33/skills/plugin_validator.py`** -- Standalone validation utility
   - `validate_plugin(path) -> ValidationResult`
   - Checks: manifest schema valid, dependencies resolvable, entry point module exists,
     entry point class importable and extends `PluginBase`, version format valid
   - Returns a structured `ValidationResult` with pass/fail per check and messages

2. **`engine/tests/test_plugin_sdk_validation.py`** -- Validation harness
   - Tests loading and registering real example plugins (word-count)
   - Tests full plugin lifecycle (init, on_load, execute, on_disable, on_unload)
   - Tests tenant boundary isolation (plugin discovered by tenant A is invisible to tenant B)
   - Tests plugin error handling and crash recovery (on_load raises, on_enable raises)
   - Tests manifest schema validation (name pattern, semver, field constraints)
   - Tests the `validate_plugin()` utility against valid/invalid plugin directories

## Explicit Non-Goals

- **No new API routes** -- validation is a library/CLI utility, not an HTTP endpoint
- **No changes to existing PluginRegistry** -- we test what already exists
- **No changes to PluginBase** -- the existing lifecycle contract is the target
- **No new plugin examples** -- we test the existing word-count example and synthetic ones
- **No CI pipeline changes** -- tests run in the standard pytest suite

## Implementation Notes

- The validation utility lives in `engine/src/agent33/skills/plugin_validator.py`
  because it validates both skill-level and plugin-level concepts. The `plugins/`
  package already has `doctor.py` for runtime diagnostics; the validator is for
  pre-deployment static checks before a plugin enters the registry.
- All tests create plugin directories via `tmp_path` fixtures to avoid filesystem
  side effects.
- Tenant isolation tests use the `PluginRegistry(tenant_id=...)` parameter on
  `discover_plugin()`, `get()`, `list_all()`, and lifecycle methods.

## Validation Plan

1. `ruff check src/ tests/` -- 0 errors
2. `ruff format --check src/ tests/` -- 0 drift
3. `mypy src --config-file pyproject.toml` -- 0 errors
4. `pytest tests/test_plugin_sdk_validation.py -v` -- all pass
5. `pytest tests/ -q` -- full suite green (no regressions)
