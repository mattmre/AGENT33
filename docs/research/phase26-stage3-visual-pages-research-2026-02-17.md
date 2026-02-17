# Phase 26 Stage 3: Visual Pages Research (2026-02-17)

## Executive Summary

Stage 3 extends Phase 26 explanations with **visual HTML page generation** using template-based rendering. While Stage 1-2 delivered text-based explanations with fact-check claims, Stage 3 adds rich visual pages for diff-review, plan-review, and project-recap modes using Jinja2 templates.

**Status**: Ready for implementation after Stage 2 completion.

---

## Current State (Stage 2 Baseline)

### Existing Capabilities
- ✅ Explanation API with generic text content generation
- ✅ Fact-check pipeline with deterministic claim validation
- ✅ Frontend rendering of claims and metadata
- ✅ Modes: `generic`, `diff_review`, `plan_review`, `project_recap`

### Gaps for Stage 3
- ❌ No HTML artifact generation (explanations are plain text)
- ❌ No template rendering system
- ❌ No visual diff display or syntax highlighting
- ❌ No structured sections for review modes
- ❌ No artifact storage/serving infrastructure
- ❌ No sandboxed iframe viewer in frontend

---

## Proposed Stage 3 Enhancements

### 1. Template Pack System

**Template structure**:
```
engine/src/agent33/explanation/templates/
├── base.html.j2          # Base layout with styles and navigation
├── diff_review.html.j2   # Diff visualization template
├── plan_review.html.j2   # Phase plan breakdown template
└── project_recap.html.j2 # Timeline/activity template
```

**Rendering service** (`engine/src/agent33/explanation/renderer.py`):
- Jinja2 environment with auto-escaping (XSS protection)
- Template selection based on explanation mode
- Context data preparation (diffs, metadata, claims)
- Syntax highlighting for code blocks (Pygments)
- Output sanitization with `bleach` library

### 2. Visual Page Endpoints

**New routes**:
```
GET /v1/explanations/{explanation_id}/visual    # Serve rendered HTML page
POST /v1/explanations/{explanation_id}/regenerate  # Regenerate visual with updated params
```

**Storage strategy**:
- Rendered HTML stored in `engine/data/explanations/{id}.html`
- 30-day TTL with background cleanup task
- Metadata tracks artifact path and size

### 3. Frontend Viewer

**Component enhancements** (`frontend/src/components/ExplanationView.tsx`):
- Add "View Visual Page" button for supported modes
- Sandboxed iframe for HTML rendering (`sandbox="allow-scripts allow-same-origin"`)
- Download option for offline viewing
- Toggle between text and visual views

---

## Security Strategy

### XSS Prevention
1. **Server-side**: Jinja2 auto-escaping + `bleach.clean()` on all dynamic content
2. **Client-side**: Sandboxed iframe with restricted permissions
3. **Testing**: OWASP XSS test vectors in integration tests

### Auth Enforcement
- Visual pages inherit access control from parent explanation
- No unauthenticated sharing (deferred to future phase)
- Audit logging for all visual artifact generations

---

## Testing Strategy

### Unit Tests
- Template rendering with mock data
- Claim embedding in visual output
- Sanitization of malicious input
- Error handling for missing templates

### Integration Tests
- End-to-end visual generation for each mode
- Artifact storage and retrieval lifecycle
- Frontend iframe rendering and isolation
- Performance benchmarks (<2s render time for typical inputs)

### Manual Validation
- Visual inspection of generated pages in multiple browsers
- Accessibility checks (WCAG 2.1 AA compliance)
- Mobile responsiveness testing

---

## Success Criteria

- [ ] Diff-review pages show side-by-side code diffs with syntax highlighting
- [ ] Plan-review pages render phase sections with TOC navigation
- [ ] Project-recap pages display timeline with trace event summaries
- [ ] All visual pages load in <2s for median inputs
- [ ] XSS vectors blocked in OWASP test suite
- [ ] Frontend viewer renders pages without console errors
- [ ] Fact-check claims visible in visual output with status badges

---

## Implementation Sizing

**Estimated effort**: 3-4 days
- **Day 1**: Template pack creation + renderer implementation
- **Day 2**: Visual endpoint implementation + storage layer
- **Day 3**: Frontend viewer + iframe sandboxing
- **Day 4**: Testing, validation, documentation

