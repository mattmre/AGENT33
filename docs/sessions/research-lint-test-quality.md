# Research: Lint & Test Quality Audit — 2026-02-12

## Ruff Configuration (`engine/pyproject.toml`)
```toml
[tool.ruff]
target-version = "py311"
line-length = 99
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "SIM", "TCH"]
```

## Lint Issues
- ~29 `# type: ignore` comments (mostly legitimate for external libraries)
- 7 `# noqa` comments (6 for FastAPI `Depends` pattern B008, 1 for global statement PLW0603)
- 100% `from __future__ import annotations` compliance ✅
- ~34 pre-existing errors expected from `ruff check` (per next-session.md)

## AsyncMock Warning
**Location**: `engine/tests/test_tools_reader.py:68`
```python
mock_resp.raise_for_status = AsyncMock()  # Should be MagicMock()
```
`raise_for_status` is synchronous — mocking as `AsyncMock` causes `RuntimeWarning: coroutine was never awaited`.

## Test Quality Assessment

| File | Quality | Notes |
|------|---------|-------|
| test_health.py | ⚠️ SHALLOW | Only checks status codes, not actual health values |
| test_chat.py | ✅ GOOD | Checks response structure + content |
| test_tools_reader.py | ✅ GOOD | Tests behavior, domain blocking, API modes |
| test_tools_search.py | ✅ GOOD | Tests results parsing, error handling |
| test_agent_registry.py | ⭐ EXCELLENT | 56 assertions, comprehensive coverage |
| test_session_memory.py | ⭐ EXCELLENT | Privacy tags, LTM storage, recall |
| test_training_system.py | ⭐ EXCELLENT | Traces, evaluation, algorithms |
| test_integration_wiring.py | ✅ GOOD | App lifecycle, middleware |
| test_airllm_provider.py | ✅ GOOD | Import handling, model routing |
| test_partial_features.py | ⭐ EXCELLENT | Comprehensive feature coverage |
| integration/test_workflow_execution.py | ⭐ EXCELLENT | End-to-end workflow |
| benchmarks/test_dag_performance.py | ✅ GOOD | Performance with thresholds |

## Auth Skip Pattern (6 occurrences in test_agent_registry.py)
```python
if resp.status_code == 401:
    pytest.skip("AuthMiddleware active — route wiring verified")
```
Tests skip on auth instead of using proper auth fixture.

## Fix Priorities
1. Fix AsyncMock → MagicMock in test_tools_reader.py:68
2. Enhance test_health.py with behavioral assertions
3. Run `ruff check` and fix all auto-fixable issues
4. Address auth skip pattern in test_agent_registry.py
