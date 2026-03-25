# P4.11: Live LLM Evaluator Integration Testing -- Scope Doc

**Session**: 109
**Slice**: P4.11
**Status**: Implementation complete, validation in progress

## Included Work

### 1. Integration Test Module (`engine/tests/test_llm_evaluator_integration.py`)

52 tests across 9 test classes covering:

- **TestLLMEvaluatorWithRealisticProvider** (13 tests): Validates the evaluator with realistic LLM JSON responses (structured scores, detailed reasoning, multi-criteria feedback). Tests cover pass/fail/borderline verdicts, malformed responses, timeouts, connection errors, multi-criteria reasoning, and judge model config forwarding.

- **TestGateEnforcementWithRealisticScores** (5 tests): Validates gate enforcement (G-PR, G-MRG, G-REL) with computed metrics from realistic task results. Tests cover success rate thresholds, rework rate penalties, and scope adherence failures.

- **TestEvaluationServicePipelineIntegration** (5 tests): Full EvaluationService pipeline tests -- create run, submit results, compute metrics, check gates. Tests cover pass/fail flows, baseline+regression detection, run-not-found, and concurrent runs.

- **TestLLMEvaluatorToGatePipeline** (3 tests): End-to-end bridge between LLM evaluator verdicts and gate enforcement decisions. Tests convert EvaluationResult to TaskRunResult and verify gate pass/fail behavior.

- **TestConfigValidation** (7 tests): Validates evaluation_judge_model config behavior, LLMEvaluator construction validation, and ModelRouter routing for judge models.

- **TestEvaluationConfigValidation** (10 tests): Tests for the new `evaluation.validation` module (check_judge_model_configured, check_judge_model_available, validate_evaluation_config).

- **TestLLMEvaluatorRegistryWiring** (3 tests): Validates LLM/rule-based evaluator coexistence in the registry, default swapping, and result shape compatibility.

- **TestRealisticEndToEndFlow** (3 tests): Full end-to-end flow from LLM evaluation through EvaluationService to gate decisions, including mixed error scenarios.

- **TestLLMEvaluatorLiveProvider** (1 test, skipped without credentials): Live provider integration test gated behind AGENT33_LLM_LIVE_TESTS=1.

### 2. Evaluation Config Validation Module (`engine/src/agent33/evaluation/validation.py`)

New module providing:
- `check_judge_model_configured(settings)` -- checks if evaluation_judge_model is set
- `check_judge_model_available(settings, model_router)` -- checks if the model is routable
- `validate_evaluation_config(settings, model_router)` -- runs all checks, returns warnings

### 3. Realistic Response Fixtures

Defined in the test file:
- `REALISTIC_PASS_RESPONSE` (score 0.85, detailed reasoning)
- `REALISTIC_FAIL_RESPONSE` (score 0.35, explains what's wrong)
- `REALISTIC_PARTIAL_PASS_RESPONSE` (score 0.72, notes edge case gaps)
- `REALISTIC_HIGH_CONFIDENCE_PASS` (score 0.98, exact match)
- `REALISTIC_BORDERLINE_FAIL` (score 0.65, off-by-one bug)
- `MALFORMED_RESPONSES` (5 variants of invalid LLM output)

## Explicit Non-Goals

1. **Modifying existing test files** -- test_p22_llm_evaluator.py, test_llm_evaluator_live.py, and test_llm_evaluator_offline_extended.py are not modified.
2. **Wiring LLM evaluator into main.py lifespan** -- The LLM evaluator is not currently registered during app lifespan. This is a separate concern.
3. **Adding new config fields** -- The existing `evaluation_judge_model` field is sufficient.
4. **Multi-trial experiment integration** -- The existing multi-trial pipeline uses `TrialEvaluatorAdapter`, which is a different code path.

## Implementation Notes

- The existing `LLMEvaluator._parse_response()` is already well-tested in `test_llm_evaluator_offline_extended.py`. The new tests focus on the **pipeline integration** -- how parsed scores drive gate decisions.
- The realistic response fixtures produce scores that meaningfully exercise gate thresholds (80% G-PR, 90% G-MRG, 95% G-REL).
- All tests work without live LLM credentials. The live test class skips gracefully.
- The validation module uses `TYPE_CHECKING` imports to avoid circular dependencies.

## Validation Plan

1. `ruff check src/ tests/` -- 0 errors
2. `ruff format --check src/ tests/` -- 0 reformats needed
3. `mypy src --config-file pyproject.toml` -- 0 errors
4. `pytest tests/ -x -q` -- all tests pass
5. New test file: 52 passed, 1 skipped
