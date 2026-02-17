# Phase 26 Readiness Research: Visual Review Capabilities (2026-02-17)

## Executive Summary

This document captures concrete design decisions and readiness assessments for Phase 26 (Visual Explainer Decision and Review Pages). Phase 26 builds on Phase 25's workflow graph foundation to deliver visual explanation pages for diff reviews, plan reviews, project recaps, and fact-checked outputs within AGENT-33 workflows.

**Status**: Planning complete; ready for API contract design and implementation kickoff after Phase 25 Stage 1 delivery.

---

## Context

Phase 25 Stage 1 delivered workflow DAG visualization with interactive drill-down. Phase 26 extends visual explainer capabilities into structured review-style HTML outputs that operators can generate, view, and validate within the AGENT-33 platform.

### Upstream Inspiration

The visual-explainer patterns (https://github.com/nicobailon/visual-explainer) demonstrate effective approaches for rendering agent reasoning, code diffs, and project context in consumable HTML formats. Phase 26 adapts these patterns for AGENT-33's autonomous workflow context while ensuring security, auditability, and integration with existing trace/review infrastructure.

---

## API Contract Direction

### Proposed Endpoint Structure

```
POST   /v1/explanations/diff-review      # Generate visual diff review page
POST   /v1/explanations/plan-review      # Generate visual plan review page
POST   /v1/explanations/project-recap    # Generate project recap/context page
POST   /v1/explanations/fact-check       # Generate fact-checked validation page

GET    /v1/explanations/{explanation_id} # Retrieve generated explanation artifact
GET    /v1/explanations/                 # List recent explanations (filtered by type/source)
DELETE /v1/explanations/{explanation_id} # Delete explanation artifact
```

### Request Schema (Unified)

All generation endpoints accept a common structure with type-specific parameters:

```json
{
  "source_refs": {
    "branch": "feat/phase-25-graphs",
    "base_ref": "main",
    "commit_hash": "abc123",
    "plan_path": "docs/phases/PHASE-25-VISUAL-EXPLAINER-INTEGRATION.md",
    "trace_ids": ["trace-301", "trace-302"]
  },
  "options": {
    "include_context": true,
    "max_diff_lines": 500,
    "enable_fact_check": true,
    "confidence_threshold": 0.7
  },
  "metadata": {
    "requested_by": "operator-id",
    "session_id": "session-123"
  }
}
```

### Response Schema

```json
{
  "explanation_id": "exp-12345",
  "type": "diff-review",
  "status": "completed",
  "artifact_url": "/v1/explanations/exp-12345",
  "source_refs": { ... },
  "confidence_score": 0.85,
  "fact_check_results": {
    "claims_validated": 12,
    "claims_flagged": 2,
    "flagged_claims": [
      {
        "claim": "All tests pass in current branch",
        "reason": "Test suite shows 3 failures in test_visualizations.py",
        "confidence": 0.95
      }
    ]
  },
  "metadata": {
    "generated_at": "2026-02-17T12:34:56Z",
    "generation_time_ms": 1850,
    "model_used": "llama3.2",
    "render_size_bytes": 45600
  }
}
```

---

## Artifact Metadata Model

### Core Schema

```python
class VisualExplanation(BaseModel):
    """Metadata and tracking for generated visual explanation artifacts."""
    
    id: str  # exp-{uuid}
    type: Literal["diff-review", "plan-review", "project-recap", "fact-check"]
    status: Literal["pending", "generating", "completed", "failed"]
    
    # Source context
    source_refs: SourceRefs
    requested_by: str
    session_id: Optional[str]
    
    # Generation metadata
    generated_at: datetime
    generation_time_ms: int
    model_used: str
    
    # Artifact storage
    artifact_path: str  # File path or blob key
    artifact_size_bytes: int
    artifact_format: Literal["html", "json", "markdown"]
    
    # Quality signals
    confidence_score: float  # 0.0-1.0
    fact_check_enabled: bool
    fact_check_results: Optional[FactCheckResults]
    
    # Lifecycle
    accessed_count: int = 0
    last_accessed_at: Optional[datetime]
    expires_at: Optional[datetime]  # TTL for cleanup
```

### Storage Lifecycle

**Storage strategy**:
- **Transient storage**: Explanation artifacts stored in `engine/data/explanations/{type}/{id}.html`
- **TTL policy**: 30-day default expiration; extendable via API
- **Cleanup**: Background task removes expired artifacts based on `expires_at` timestamp
- **Metadata persistence**: SQLite database tracks metadata even after artifact deletion (audit trail)

**Access control**:
- Explanations inherit auth scope from source refs (e.g., diff-review requires `workflows:read` or `git:read`)
- Operators can only retrieve explanations they generated or have explicit access to
- No unauthenticated sharing links in Phase 26 MVP (defer to future phases)

---

## Fact-Check Confidence Criteria

### Problem Statement

Generated explanation pages may include LLM-generated summaries, code analysis, or execution insights that could be inaccurate. Fact-check mode validates claims against ground truth (repository state, test results, trace logs) before marking an explanation as high-confidence.

### Validation Approach

**Fact-check pipeline**:
1. Extract claims from generated explanation text (e.g., "All tests pass", "No security issues found")
2. Map claims to validation strategies:
   - **Test results**: Query pytest output or evaluation run results
   - **Code changes**: Verify diff contents against git refs
   - **Execution traces**: Check trace logs for step statuses
   - **Policy compliance**: Run policy checks from Phase 14 security rules
3. Assign confidence scores per claim (0.0-1.0)
4. Flag low-confidence claims with reasons and recommended corrections
5. Compute overall confidence score as weighted average

**Confidence thresholds**:
- **High confidence (≥0.85)**: All critical claims validated, no major inconsistencies
- **Medium confidence (0.60-0.84)**: Most claims validated, minor issues flagged
- **Low confidence (<0.60)**: Multiple claims unverified or contradicted by ground truth

**User experience**:
- Explanations with confidence <0.70 show warning banner with flagged claims
- Operators can regenerate with corrected prompts or disable fact-check for exploratory outputs
- Fact-check results are persisted in metadata for audit trail

### Example Validation Rules

| Claim Type | Validation Strategy | Confidence Signal |
|------------|---------------------|-------------------|
| "Tests pass" | Query `pytest` exit code or evaluation run status | 1.0 if all pass, 0.0 if any fail |
| "No security issues" | Run `ruff check` security rules or query Phase 14 policy results | 0.9 if clean, 0.3 if warnings, 0.0 if errors |
| "Branch merged" | Query git log for merge commit | 1.0 if found, 0.0 if not |
| "Workflow executed successfully" | Query workflow execution history | 1.0 if status="success", 0.0 if failed |
| "Performance improved" | Compare metrics from evaluation runs (baseline vs current) | 0.8 if metrics improved, 0.2 if degraded |

---

## Phase 26 Deliverable Checklist

### Backend API (Priority 1)
- [ ] Create `visual_explanations.py` route with generation endpoints
- [ ] Implement `VisualExplanation` model and SQLite persistence
- [ ] Build rendering service with HTML sanitization (prevent XSS)
- [ ] Implement fact-check pipeline with validation rule registry
- [ ] Add artifact storage with TTL-based cleanup task
- [ ] Write unit tests for all generation paths and fact-check logic

### Frontend UI (Priority 2)
- [ ] Add Explanations domain to sidebar navigation
- [ ] Create explanation generation form (type selection + source refs)
- [ ] Build explanation list view with filters (type, date, status)
- [ ] Implement explanation viewer with embedded HTML iframe (sandboxed)
- [ ] Add fact-check results display with flagged claims UI
- [ ] Write component tests for explanation workflows

### Integration & Validation (Priority 3)
- [ ] Wire explanations domain to backend API operations
- [ ] Test diff-review generation against real git branches
- [ ] Test plan-review generation with Phase 25 spec document
- [ ] Test project-recap with recent session logs and traces
- [ ] Validate fact-check accuracy with known-good and known-bad inputs
- [ ] Measure generation latency for median and large inputs (<5s target)

### Documentation (Priority 4)
- [ ] Update `docs/walkthroughs.md` with explanation generation examples
- [ ] Document fact-check criteria and confidence interpretation
- [ ] Create operator troubleshooting guide for low-confidence outputs
- [ ] Capture validation evidence in `docs/progress/phase-26-visual-review-log.md`

---

## Risks and Open Questions

### Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Generated HTML includes unsanitized user input (XSS) | High | Use server-side templating with auto-escaping; sandbox iframe rendering |
| Fact-check validation rules incomplete or inaccurate | Medium | Start with conservative rule set; iterate based on operator feedback |
| Large diff/plan inputs exceed generation timeout | Medium | Implement pagination or summarization for inputs >500 lines |
| Artifact storage grows unbounded | Low | Enforce 30-day TTL with background cleanup; alert on disk usage thresholds |
| Operators misinterpret low-confidence outputs as ground truth | Medium | Prominent warning banners; require explicit confidence acknowledgment |

### Open Questions

1. **Template engine**: Use Jinja2, Mako, or custom HTML builder? (Recommend Jinja2 for maturity and auto-escaping)
2. **Artifact format**: HTML only, or support Markdown/JSON alternatives? (Start with HTML; add Markdown in future iteration)
3. **Model selection**: Use same model as workflow execution or dedicated review model? (Use workflow model for consistency; allow override in future)
4. **Export options**: Allow PDF export or static archive of explanations? (Defer to post-MVP; focus on interactive HTML first)
5. **Diff visualization**: Inline diff rendering or side-by-side? (Side-by-side for clarity; inline as future option)

---

## Phase 26 Implementation Sequence

1. **API Design & Contracts** (Week 1)
   - Finalize request/response schemas
   - Implement metadata model and storage layer
   - Write API route stubs with schema validation

2. **Generation Service** (Week 1-2)
   - Build diff-review generator (integrate with git CLI or libgit2)
   - Build plan-review generator (parse markdown, extract structure)
   - Build project-recap generator (query traces + session logs)
   - Implement HTML rendering with Jinja2 templates

3. **Fact-Check Pipeline** (Week 2)
   - Define validation rule registry
   - Implement claim extraction from generated text
   - Build validation executors (pytest, ruff, git, trace queries)
   - Add confidence scoring and result aggregation

4. **Frontend Integration** (Week 2-3)
   - Create explanation domain operations
   - Build generation form and list views
   - Implement sandboxed HTML viewer
   - Add fact-check results UI components

5. **Testing & Validation** (Week 3)
   - Write unit tests for backend generation logic
   - Write integration tests for end-to-end flows
   - Validate fact-check accuracy with test cases
   - Measure performance against acceptance criteria

6. **Documentation & Handoff** (Week 3)
   - Update walkthroughs and operator guides
   - Document known limitations and future enhancements
   - Capture progress evidence and validation results
   - Review and merge Phase 26 implementation PR

---

## Success Criteria (Phase 26 MVP)

- [ ] Operators can generate diff-review pages for branch comparisons
- [ ] Operators can generate plan-review pages from phase spec documents
- [ ] Operators can generate project-recap pages from recent activity
- [ ] Fact-check pipeline validates at least 5 claim types with ≥80% accuracy
- [ ] Explanations render in <5s for median inputs (100-line diffs, 1000-word plans)
- [ ] HTML sanitization prevents all common XSS vectors (tested with OWASP samples)
- [ ] All Phase 26 backend and frontend tests pass
- [ ] Documentation includes concrete examples and troubleshooting guidance

---

## References

- Phase 25 spec: `docs/phases/PHASE-25-VISUAL-EXPLAINER-INTEGRATION.md`
- Phase 26 spec: `docs/phases/PHASE-26-VISUAL-EXPLAINER-DECISION-AND-REVIEW-PAGES.md`
- Visual explainer analysis: `docs/research/visual-explainer-integration-analysis-2026-02-17.md`
- Phase 14 security patterns: `docs/phases/PHASE-14-SECURITY-HARDENING-AND-PROMPT-INJECTION-DEFENSE.md`
- Phase 16 trace schema: `docs/phases/PHASE-16-OBSERVABILITY-AND-TRACE-PIPELINE.md`
- Visual-explainer upstream: https://github.com/nicobailon/visual-explainer
