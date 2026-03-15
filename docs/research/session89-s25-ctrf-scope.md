# S25: SkillsBench CTRF Reporting Integration

## Status: Implemented (Session 89)

## Scope

Add standardized CTRF (Common Test Report Format) reporting to the AGENT-33
evaluation subsystem (Phase 17). This enables interoperability with
SkillsBench and any tooling that consumes CTRF JSON.

## Background

CTRF (https://ctrf.io/) is a standardized JSON format for test results.
AGENT-33's evaluation subsystem already had golden tasks, metrics, gate
enforcement, and multi-trial experiments with a legacy dict-based CTRF
generator. This slice adds:

1. **Typed Pydantic models** for the full CTRF spec (CTRFReport,
   CTRFResults, CTRFSummary, CTRFTest, CTRFToolInfo, CTRFEnvironment,
   CTRFTestState).

2. **CTRFReportGenerator** class with three conversion paths:
   - `from_evaluation_run()` -- standard evaluation run TaskRunResult data
   - `from_gate_results()` -- regression gate GateCheckResult data
   - `from_golden_tasks()` -- golden task execution results
   - `to_json()` and `to_file()` serialization helpers

3. **API endpoints**:
   - `GET /v1/evaluations/ctrf/latest` (agents:read scope) -- latest
     completed evaluation run as CTRF JSON
   - `POST /v1/evaluations/ctrf/generate` (admin scope) -- generate CTRF
     from a specific run or the latest, with selectable report type
     (evaluation, gate, golden-task)

4. **Config**: `evaluation_ctrf_output_dir` setting for file-based report
   storage.

5. **Service methods**: `generate_ctrf_for_run()`,
   `generate_ctrf_for_gate()`, `generate_ctrf_for_golden_tasks()`,
   `get_latest_ctrf()` on EvaluationService.

## Backward Compatibility

The existing `CTRFGenerator` class (dict-based, used by the multi-trial
pipeline and `export_ctrf()` service method) is fully preserved. The new
`CTRFReportGenerator` coexists alongside it and is used by the new
endpoints and service methods.

## Files Modified

- `engine/src/agent33/evaluation/ctrf.py` -- CTRF models + generators
- `engine/src/agent33/evaluation/service.py` -- typed CTRF service methods
- `engine/src/agent33/api/routes/evaluations.py` -- CTRF API endpoints
- `engine/src/agent33/config.py` -- `evaluation_ctrf_output_dir` setting
- `engine/tests/test_evaluation_ctrf.py` -- comprehensive test suite
- `docs/research/session89-s25-ctrf-scope.md` -- this document

## Test Coverage

Tests verify:
- All CTRF model fields and defaults
- Status mapping from AGENT-33 TaskResult to CTRFTestState
- Summary count accuracy across all result combinations
- JSON round-trip serialization
- File output with directory creation
- Empty input handling
- Service integration (completed/incomplete/nonexistent runs)
- API endpoints (GET latest, POST generate with all report types)
- CTRF spec structure compliance

## Relation to SkillsBench

SkillsBench uses CTRF as its native reporting format. This integration
enables AGENT-33 to produce CTRF-compliant reports that can be consumed
by SkillsBench tooling, CI dashboards, and cross-benchmark comparison
pipelines without any format translation layer.
