# Phase 58: Mixture-of-Agents (MoA) Workflow Template -- Scope Doc

**Session**: 109
**Branch**: `feat/phase58-moa-workflow`
**Base**: `origin/main` (`2f4b272`)

## Included Work

1. **MoA workflow template** (`engine/src/agent33/workflows/templates/mixture_of_agents.py`)
   - `build_moa_workflow()` function that produces a `WorkflowDefinition`
   - N parallel reference-model steps (invoke-agent action, no dependencies)
   - 1 aggregator step (invoke-agent) depending on all reference steps
   - Aggregator system prompt from the MoA paper (arXiv:2406.04692)
   - Step ID sanitization for arbitrary model names
   - Duplicate model name handling with numeric suffixes
   - `format_moa_result()` helper to extract aggregated response

2. **MoA tool** (`engine/src/agent33/tools/builtin/moa.py`)
   - `MoATool` implementing `Tool` and `SchemaAwareTool` protocols
   - Accepts query, optional reference_models/aggregator/temperatures
   - Builds workflow, executes via `WorkflowExecutor`, returns `ToolResult`
   - Proper error handling for missing models, workflow failures, exceptions

3. **Config** (`engine/src/agent33/config.py`)
   - `moa_reference_models: str = ""` (comma-separated)
   - `moa_aggregator_model: str = ""`
   - `moa_reference_temperature: float = 0.6`
   - `moa_aggregator_temperature: float = 0.4`

4. **Tests** (`engine/tests/test_moa_workflow.py`)
   - DAG structure validation (step count, dependencies, parallel groups)
   - Aggregator prompt content verification
   - Temperature propagation
   - Step ID sanitization edge cases
   - Config default and custom value tests
   - MoATool: error paths, mock execution, param overrides

5. **Workflow templates package** (`engine/src/agent33/workflows/templates/__init__.py`)

## Explicit Non-Goals

- **Multi-layer MoA**: The paper describes iterative layers; this implements
  the single-layer variant. Multi-layer can be a follow-up.
- **Automatic model discovery**: Reference models are explicitly configured,
  not discovered from the model router at runtime.
- **Cost tracking integration**: Phase 49 pricing catalog exists but wiring
  MoA to per-invocation cost tracking is deferred.
- **API route**: No `/v1/moa` endpoint is added. The tool is accessible via
  the standard tool execution interface.
- **Lifespan wiring**: The MoATool is not registered in `main.py` lifespan
  during this phase. Registration is a follow-up.

## Implementation Notes

- The workflow uses `ExecutionMode.DEPENDENCY_AWARE` so the DAG engine
  automatically runs all reference steps in parallel, then the aggregator.
- Step IDs are sanitized from model names (e.g., "GPT-4o" -> "ref-gpt-4o")
  to satisfy the `^[a-z][a-z0-9-]*$` pattern requirement.
- The aggregator prompt uses Jinja2 expressions (`{{ step_id.result }}`) that
  the `ExpressionEvaluator` resolves at runtime from workflow state.
- Config uses a CSV string for reference models (matching existing patterns
  like `cors_allowed_origins`) rather than a native list type.

## Validation Plan

1. `ruff check src/ tests/` -- lint clean
2. `ruff format --check src/ tests/` -- format clean
3. `mypy src --config-file pyproject.toml` -- type-check clean
4. `pytest tests/test_moa_workflow.py -x -q` -- all tests pass
5. `pytest tests/ -x -q` -- full suite still green
