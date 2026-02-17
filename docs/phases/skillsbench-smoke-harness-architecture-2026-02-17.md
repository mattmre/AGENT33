# SkillsBench Smoke Harness Architecture
**Date**: 2026-02-17  
**Agent**: Architect  
**Status**: Complete  
**Implements**: Research findings from skillsbench-smoke-harness-research-2026-02-17.md

## Architecture Overview

Minimal smoke benchmark infrastructure that validates SkillsBench evaluation framework integration. Uses existing CTRF schema and pytest framework, adds non-blocking CI job with artifact reporting.

```
┌─────────────────────────────────────────────────────────┐
│               CI Workflow (.github/workflows/ci.yml)    │
├─────────────┬─────────────┬─────────────┬──────────────┤
│    lint     │    test     │    build    │ benchmark-   │
│             │             │             │    smoke     │
│  (blocking) │  (blocking) │  (blocking) │(non-blocking)│
└─────────────┴─────────────┴─────────────┴──────┬───────┘
                                                   │
                                                   ▼
                              ┌────────────────────────────────┐
                              │ engine/tests/benchmarks/       │
                              │   test_skills_smoke.py         │
                              │                                │
                              │ • validate_service_init()      │
                              │ • validate_golden_tasks()      │
                              │ • validate_ctrf_generation()   │
                              │ • validate_baseline_access()   │
                              └────────┬───────────────────────┘
                                       │
                                       │ uses
                                       ▼
              ┌────────────────────────────────────────────────┐
              │ agent33.evaluation.service.EvaluationService   │
              │ agent33.evaluation.ctrf.CTRFGenerator          │
              └────────┬───────────────────────────────────────┘
                       │
                       │ generates
                       ▼
              ┌────────────────────────────────┐
              │ engine/benchmark-results/      │
              │   smoke-report.ctrf.json       │
              │                                │
              │ CTRF v1.0 Schema:              │
              │ • results.tool                 │
              │ • results.summary              │
              │ • results.tests[]              │
              └────────┬───────────────────────┘
                       │
                       │ uploaded as
                       ▼
              ┌────────────────────────────────┐
              │  GitHub Actions Artifact       │
              │  Name: benchmark-smoke-results │
              │  Retention: 30 days            │
              └────────────────────────────────┘
```

## Component Design

### 1. Benchmark Test Module

**File**: `engine/tests/benchmarks/test_skills_smoke.py`

**Purpose**: Validate core evaluation service functionality with fast, deterministic tests.

**Test Cases**:

```python
class TestSkillsBenchSmoke:
    """Smoke tests for SkillsBench evaluation harness."""
    
    def test_service_initialization(self):
        """Verify EvaluationService initializes without errors."""
        # Tests: service creation, component wiring
        # Assertions: instance checks, no exceptions
        # Runtime: <50ms
    
    def test_golden_tasks_registry(self):
        """Verify golden task registry is accessible and populated."""
        # Tests: list_golden_tasks(), basic registry structure
        # Assertions: non-empty list, valid task schema
        # Runtime: <50ms
    
    def test_ctrf_report_generation(self):
        """Verify CTRF report can be generated from test run."""
        # Tests: CTRFGenerator integration, schema compliance
        # Assertions: valid JSON structure, required fields present
        # Runtime: <100ms
    
    def test_gate_type_enumeration(self):
        """Verify gate types are defined and queryable."""
        # Tests: GateType enum, get_tasks_for_gate()
        # Assertions: known gates return task lists
        # Runtime: <50ms
```

**Dependencies**:
```python
from agent33.evaluation.service import EvaluationService
from agent33.evaluation.ctrf import CTRFGenerator
from agent33.evaluation.models import GateType
import json
from pathlib import Path
```

### 2. CTRF Report Helper

**Strategy**: Inline helper function within test module (avoids new module for MVP).

**Function Signature**:
```python
def write_benchmark_ctrf(
    test_results: list[dict],
    output_path: Path,
    tool_name: str = "agent33-benchmark-smoke",
) -> None:
    """Write pytest benchmark results as CTRF report.
    
    Args:
        test_results: List of test dicts with name, status, duration
        output_path: Path to write CTRF JSON
        tool_name: Tool identifier for report
    """
```

**Schema Mapping**:
```python
{
    "results": {
        "tool": {
            "name": "agent33-benchmark-smoke",
            "version": "1.0.0"
        },
        "summary": {
            "tests": <count>,
            "passed": <count>,
            "failed": <count>,
            "skipped": 0,
            "pending": 0,
            "other": 0,
            "start": <epoch_ms>,
            "stop": <epoch_ms>
        },
        "tests": [
            {
                "name": "test_service_initialization",
                "status": "passed",  # or "failed"
                "duration": <ms>
            }
        ]
    }
}
```

**Implementation Note**: Reuse CTRFGenerator structure but simplified for pytest output format.

### 3. CI Job Integration

**File**: `.github/workflows/ci.yml`

**New Job Definition**:
```yaml
  benchmark-smoke:
    runs-on: ubuntu-latest
    continue-on-error: true  # Non-blocking
    defaults:
      run:
        working-directory: engine
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Run smoke benchmarks
        run: |
          pytest tests/benchmarks/test_skills_smoke.py -v \
            --tb=short \
            --junit-xml=benchmark-results/junit.xml
      
      - name: Generate CTRF report
        if: always()
        run: |
          python -c "
          import json
          from pathlib import Path
          # Parse junit.xml or pytest output to CTRF
          # Write to benchmark-results/smoke-report.ctrf.json
          "
      
      - name: Upload benchmark artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-smoke-results
          path: engine/benchmark-results/
          retention-days: 30
```

**Job Characteristics**:
- **Parallelism**: Runs in parallel with lint/test/build
- **Blocking**: Non-blocking via `continue-on-error: true`
- **Duration**: ~30 seconds (Python setup 20s, tests 5s, upload 5s)
- **Artifact**: Results preserved for 30 days

## Data Flow

```
┌──────────────┐
│   CI Trigger │ (push/PR)
└──────┬───────┘
       │
       ├──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼
   ┌───────┐    ┌────────┐    ┌───────┐    ┌──────────────┐
   │ lint  │    │  test  │    │ build │    │ benchmark-   │
   │       │    │        │    │       │    │    smoke     │
   └───────┘    └────────┘    └───────┘    └──────┬───────┘
                                                   │
                                                   ▼
                                        ┌─────────────────────┐
                                        │ pytest executes     │
                                        │ test_skills_smoke.py│
                                        └──────┬──────────────┘
                                               │
                                               ├─ calls EvaluationService
                                               ├─ calls CTRFGenerator
                                               └─ measures timing
                                               │
                                               ▼
                                        ┌─────────────────────┐
                                        │ Test results        │
                                        │ collected           │
                                        └──────┬──────────────┘
                                               │
                                               ▼
                                        ┌─────────────────────┐
                                        │ write_benchmark_ctrf│
                                        │ formats CTRF JSON   │
                                        └──────┬──────────────┘
                                               │
                                               ▼
                                        ┌─────────────────────┐
                                        │ smoke-report.ctrf.  │
                                        │ json written        │
                                        └──────┬──────────────┘
                                               │
                                               ▼
                                        ┌─────────────────────┐
                                        │ GitHub artifact     │
                                        │ uploaded            │
                                        └─────────────────────┘
```

## File Structure

```
AGENT33/
├── .github/
│   └── workflows/
│       └── ci.yml                           # MODIFIED: +benchmark-smoke job
├── engine/
│   ├── src/
│   │   └── agent33/
│   │       └── evaluation/
│   │           ├── ctrf.py                  # UNCHANGED: existing schema
│   │           └── service.py               # UNCHANGED: existing service
│   ├── tests/
│   │   └── benchmarks/
│   │       ├── __init__.py                  # UNCHANGED: existing
│   │       ├── test_dag_performance.py      # UNCHANGED: existing
│   │       └── test_skills_smoke.py         # NEW: smoke benchmark tests
│   └── benchmark-results/                   # NEW: created by tests
│       └── smoke-report.ctrf.json           # GENERATED: CTRF output
└── docs/
    ├── research/
    │   └── skillsbench-smoke-harness-*      # THIS FILE'S COMPANION
    └── phases/
        └── skillsbench-smoke-harness-*      # THIS FILE
```

## Implementation Checklist

### Phase 1: Test Module (Implementer)
- [ ] Create `engine/tests/benchmarks/test_skills_smoke.py`
- [ ] Implement 4 smoke test cases
- [ ] Add `write_benchmark_ctrf()` helper function
- [ ] Verify local pytest execution: `pytest tests/benchmarks/test_skills_smoke.py -v`
- [ ] Confirm CTRF JSON generated in `benchmark-results/`

### Phase 2: CI Integration (Implementer)
- [ ] Update `.github/workflows/ci.yml`
- [ ] Add `benchmark-smoke` job definition
- [ ] Configure artifact upload step
- [ ] Push to feature branch
- [ ] Verify job runs in Actions UI
- [ ] Verify artifact downloadable from Actions

### Phase 3: Validation (Reviewer/Tester)
- [ ] Lint existing jobs still pass
- [ ] Test existing jobs still pass
- [ ] Build existing jobs still pass
- [ ] Benchmark job runs (success or failure OK)
- [ ] Artifact contains valid CTRF JSON
- [ ] JSON schema validates against CTRF 1.0 spec

## Non-Goals (Explicitly Out of Scope)

- ❌ Comprehensive skill coverage tests
- ❌ Performance regression detection logic
- ❌ Historical trend database
- ❌ Multi-agent comparison matrices
- ❌ External benchmark suite integration
- ❌ Benchmark result visualization
- ❌ Automated performance alerts
- ❌ Benchmark parameterization/configuration

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test execution time | <5 seconds | CI job logs |
| CI setup overhead | <30 seconds | GitHub Actions timing |
| Job success rate | >95% | Non-flaky tests |
| CTRF schema compliance | 100% | JSON schema validator |
| Artifact generation | 100% | GitHub Actions artifacts |
| PR blocking rate | 0% | continue-on-error=true |

## Migration & Rollback

**Rollback Strategy**: Remove new job from `.github/workflows/ci.yml`, delete test file.

**Risk**: Minimal - no existing functionality modified, only additive changes.

**Deployment**: 
1. Merge PR with changes
2. Verify on main branch CI run
3. Monitor for 1 week for flakiness

## Future Enhancements (Post-MVP)

1. **Phase 2 - Performance Regression Detection**
   - Store historical benchmark results
   - Compare against baseline thresholds
   - Alert on significant degradation

2. **Phase 3 - Skill Coverage Expansion**
   - Add tests for each SkillsBench skill
   - Multi-agent comparison matrices
   - Skills impact analysis

3. **Phase 4 - Reporting Dashboard**
   - Visualization of benchmark trends
   - CI badge integration
   - Public benchmark leaderboard

## Architecture Decisions

### ADR-001: Use Inline CTRF Helper vs Shared Module
**Decision**: Inline helper function in test module  
**Rationale**: MVP scope doesn't justify new module overhead, <50 LOC  
**Trade-off**: Code duplication if multiple benchmark modules added later

### ADR-002: Non-Blocking CI Job
**Decision**: `continue-on-error: true` for benchmark job  
**Rationale**: Avoid blocking PRs during infrastructure stabilization  
**Trade-off**: May mask real issues, requires manual monitoring

### ADR-003: Artifact Retention 30 Days
**Decision**: 30-day retention policy  
**Rationale**: Balance storage costs with debugging needs  
**Trade-off**: Historical data not available beyond 30 days

### ADR-004: Reuse Existing CTRF Schema
**Decision**: Follow CTRFGenerator patterns from ctrf.py  
**Rationale**: Maintain consistency, enable future tooling reuse  
**Trade-off**: Simpler schema could be more readable

## Appendix: CTRF Schema Reference

**Specification**: https://ctrf.io/

**Required Fields**:
```json
{
  "results": {
    "tool": { "name": "string" },
    "summary": {
      "tests": number,
      "passed": number,
      "failed": number,
      "skipped": number,
      "pending": number,
      "other": number,
      "start": number,
      "stop": number
    },
    "tests": [
      {
        "name": "string",
        "status": "passed" | "failed" | "skipped" | "pending" | "other",
        "duration": number
      }
    ]
  }
}
```

**Optional Fields**: `message`, `trace`, `extra` (object for custom metadata)

---

**Architect Sign-Off**: Design approved for implementation. Proceed to Implementer phase.
