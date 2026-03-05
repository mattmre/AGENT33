# Periodic Metrics Review Workflow Template

> **Intended location**: `core/workflows/improvement-cycle/template-metrics-review.md`
> Move this file once the `improvement-cycle/` directory is created.

## Purpose

Structured template for reviewing quantitative metrics at regular intervals. Surfaces trends, regressions, and improvements across build health, test coverage, API alignment, and operational performance.

## Invocation

Run this workflow on a periodic basis (weekly, per-phase, or per-release).

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| review_period | Yes | Time range being reviewed (e.g., "2026-03-01 to 2026-03-07") |
| baseline_period | No | Comparison period for trend analysis |
| focus_areas | No | Comma-separated list of metric categories to prioritize |

## Workflow

### 1. Collect Metrics

Gather data from the following sources:

| Category | Source | Key Metrics |
|----------|--------|-------------|
| Build Health | CI pipeline | Pass rate, avg duration, flake rate |
| Test Coverage | Coverage reports | Line %, branch %, delta from baseline |
| API Alignment | Domain configs vs. backend routes | Mismatched endpoints, missing operations |
| Operations Hub | `/v1/operations/hub` | Active process count, control action success rate |
| Code Quality | Linter / type-checker output | Error count, warning count, delta |
| PR Velocity | Git / issue tracker | PRs merged, avg review time, rework rate |

### 2. Trend Analysis

Compare current period against baseline:

| Metric | Baseline | Current | Delta | Trend |
|--------|----------|---------|-------|-------|
| [metric name] | [value] | [value] | [+/-] | ↑ / ↓ / → |

Flag any metric with:
- **Regression**: Current is worse than baseline by more than 10%
- **Improvement**: Current is better than baseline by more than 10%
- **Plateau**: No meaningful change across 3+ review periods

### 3. Anomaly Detection

Identify outliers or unexpected values:
- [ ] Build failures on previously stable components
- [ ] Sudden coverage drops in specific modules
- [ ] Spike in API 4xx/5xx error rates
- [ ] Stale domain configs pointing to removed endpoints

### 4. Impact Assessment

For each regression or anomaly:

| Issue | Impact | Affected Area | Urgency |
|-------|--------|---------------|---------|
| [description] | [user/developer/ops impact] | [module/feature] | P0/P1/P2 |

### 5. Recommendations

Produce prioritized recommendations:

| Recommendation | Category | Expected Outcome | Effort |
|---------------|----------|-------------------|--------|
| [action] | [build/test/api/ops] | [what improves] | Low/Medium/High |

### 6. Record Results

Document the review for historical tracking:

```markdown
## Metrics Review: [review_period]

### Summary
- **Overall health**: [Green/Yellow/Red]
- **Key improvement**: [description]
- **Key regression**: [description]

### Action Items
1. [action with owner]
2. [action with owner]
```

## Outputs

| Output | Destination | Action |
|--------|-------------|--------|
| Metrics summary | `docs/progress/` | Create period review doc |
| Regression tickets | Issue tracker / `TASKS.md` | Create with priority |
| Trend dashboard data | `docs/self-improvement/` | Append to tracking |

## Completion Criteria

- All metric categories collected with actual values (no placeholders)
- Trend analysis completed with baseline comparison
- At least one recommendation per regression found
- Results recorded in the appropriate docs directory

## Related Documents

- `core/workflows/improvement-cycle-retrospective.md` — Qualitative retrospective
- `core/workflows/commands/status.md` — Status tracking
- `docs/self-improvement/` — Historical improvement tracking
