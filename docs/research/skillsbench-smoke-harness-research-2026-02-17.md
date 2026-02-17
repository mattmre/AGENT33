# SkillsBench Smoke Harness Research
**Date**: 2026-02-17  
**Agent**: Researcher  
**Status**: Complete

## Overview

Add a minimal smoke benchmark harness that validates the SkillsBench evaluation framework can execute and report results through CI. This MVP focuses on infrastructure validation, not comprehensive skill testing.

## Existing Infrastructure Analysis

### CTRF Support (engine/src/agent33/evaluation/ctrf.py)
- **CTRFGenerator** class already implemented
- Supports CTRF 1.0 schema compliance
- Methods:
  - `generate_report(run: MultiTrialRun)` → dict
  - `generate_summary(run: MultiTrialRun)` → dict  
  - `write_report(run: MultiTrialRun, path: Path)` → None
- Schema includes: tool metadata, summary stats, test results with extra fields
- Pass threshold configurable (default 0.6)

### EvaluationService (engine/src/agent33/evaluation/service.py)
- Orchestrates multi-trial experiment runs
- `export_ctrf(run_id: str)` method available
- Multi-trial runs stored with bounded retention (max 1000)
- Existing `_run_single_trial` placeholder currently returns True for known golden tasks

### Current CI Pipeline (.github/workflows/ci.yml)
- Jobs: `lint`, `test`, `build`
- All jobs run on `ubuntu-latest`, Python 3.11
- Working directory: `engine/`
- Uses pytest with coverage for testing
- Docker compose for build validation

### Existing Benchmarks (engine/tests/benchmarks/)
- `test_dag_performance.py` - DAG topological sort benchmarks
- Uses pytest framework
- Measures elapsed time with assertions on performance bounds
- Tests linear, wide, and diamond DAG structures (100 steps each)

## Research Findings

### 1. Benchmark Test Module Location
**Recommendation**: `engine/tests/benchmarks/test_skills_smoke.py`

**Rationale**:
- Consistent with existing `test_dag_performance.py` pattern
- pytest auto-discovery compatible
- Clear naming indicates smoke test scope
- Separates benchmarks from unit tests

### 2. CTRF Report Generation Strategy
**Recommendation**: Create helper function that wraps CTRFGenerator for benchmark use

**Approach**:
```python
# Reuse existing CTRFGenerator with synthetic MultiTrialRun
# OR create simplified BenchmarkCTRFWriter for direct test results
```

**Rationale**:
- Existing CTRFGenerator expects MultiTrialRun objects
- Benchmark smoke tests are simpler than full multi-trial experiments
- Need lightweight adapter that produces CTRF-compliant output
- Should maintain schema compatibility for report consumers

### 3. CI Integration Pattern
**Recommendation**: New non-blocking job with artifact upload

**Pattern**:
```yaml
benchmark-smoke:
  runs-on: ubuntu-latest
  continue-on-error: true  # Non-blocking
  steps:
    - Run benchmark suite
    - Generate CTRF report
    - Upload artifact
```

**Rationale**:
- `continue-on-error: true` prevents blocking PRs on benchmark failures
- Artifact upload enables historical tracking
- Isolated job keeps existing CI unchanged
- Enables future performance regression detection

## MVP Scope Definition

### In-Scope
1. **Single smoke benchmark module** (`test_skills_smoke.py`)
   - Validates evaluation service initialization
   - Tests basic golden task registry access
   - Verifies CTRF report generation
   - ~3-5 simple test cases
   - Total runtime target: <5 seconds

2. **CTRF report helper** (in benchmark module or shared util)
   - Converts pytest results to CTRF schema
   - Writes JSON artifact to `engine/benchmark-results/`
   - Reuses existing `ctrf.py` schema patterns
   - <50 lines of code

3. **CI job addition** (`.github/workflows/ci.yml`)
   - New `benchmark-smoke` job
   - Non-blocking (`continue-on-error: true`)
   - Runs pytest on benchmarks directory with marker filter
   - Uploads CTRF artifact with retention policy
   - Parallel execution with existing jobs

### Out-of-Scope (Future Enhancements)
- Full SkillsBench skill coverage tests
- Performance regression analysis
- Multi-agent comparison matrices
- Integration with external benchmark suites
- Historical trend visualization
- Benchmark result database storage

## Technical Constraints

### Dependencies
- No new Python package dependencies required
- Uses existing: pytest, agent33.evaluation modules
- Standard library: json, time, pathlib

### Performance Budget
- Smoke benchmark suite: <5 seconds total
- CI overhead: <30 seconds including setup
- No external service dependencies

### Compatibility
- Python 3.11+
- pytest 7.x+
- CTRF schema v1.0
- Ubuntu latest (CI runner)

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Benchmark flakiness | Medium | Use deterministic test data, avoid timing-sensitive assertions |
| CI overhead | Low | Keep suite minimal, use pytest markers for selective execution |
| False negatives | Low | Non-blocking job prevents PR disruption |
| Schema drift | Low | Reuse existing CTRFGenerator, unit test report structure |

## Success Criteria

1. ✅ Benchmark module executes successfully in CI
2. ✅ CTRF report artifact generated and uploaded
3. ✅ Existing CI jobs unchanged and passing
4. ✅ Smoke tests validate core evaluation service functionality
5. ✅ Total CI runtime increase <30 seconds
6. ✅ Non-blocking job doesn't prevent PR merges

## Next Steps → Architecture

**Implementer Ready**: After architecture phase approves design:
1. Create `engine/tests/benchmarks/test_skills_smoke.py`
2. Add CTRF helper function (inline or utility)
3. Update `.github/workflows/ci.yml` with new job
4. Verify local pytest execution
5. Test CI pipeline on feature branch
6. Update documentation with usage examples
