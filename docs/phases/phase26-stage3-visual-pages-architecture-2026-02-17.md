# Phase 26 Stage 3: Visual Pages Architecture (2026-02-17)

## Overview

This document defines the implementation plan for Stage 3 visual page generation. Stage 3 builds on Stage 2's fact-check infrastructure to deliver rich HTML rendering for explanation modes.

---

## Architecture Components

### 1. Template System

**File**: `engine/src/agent33/explanation/renderer.py`

**Responsibilities**:
- Initialize Jinja2 environment with auto-escaping
- Load templates from `engine/src/agent33/explanation/templates/`
- Prepare context data (explanations, claims, metadata)
- Render HTML with syntax highlighting for code blocks
- Sanitize output with `bleach` library

**Key methods**:
```python
def render_visual_page(explanation: ExplanationMetadata, mode: ExplanationMode) -> str:
    """Render explanation as HTML page based on mode."""

def sanitize_html(html: str) -> str:
    """Remove potentially dangerous HTML tags/attributes."""

def highlight_code(code: str, language: str) -> str:
    """Apply syntax highlighting to code blocks."""
```

### 2. Template Files

**Base template** (`templates/base.html.j2`):
- Common layout with CSS styles
- Navigation header with explanation metadata
- Fact-check status indicator
- Footer with timestamp and model info

**Mode templates**:
- `templates/diff_review.html.j2`: Side-by-side diff display with line numbers
- `templates/plan_review.html.j2`: Collapsible sections for phase spec content
- `templates/project_recap.html.j2`: Timeline view with trace event cards

### 3. API Routes

**File**: `engine/src/agent33/api/routes/explanations.py` (extend existing)

**New endpoints**:

```python
@router.get("/{explanation_id}/visual")
async def get_visual_page(explanation_id: str, auth: AuthContext = Depends(require_auth)):
    """Serve rendered HTML page for explanation."""
    # 1. Fetch explanation metadata
    # 2. Load artifact from storage or generate if missing
    # 3. Return HTML with content-type: text/html
    # 4. Log access for audit

@router.post("/{explanation_id}/regenerate")
async def regenerate_visual(explanation_id: str, auth: AuthContext = Depends(require_auth)):
    """Regenerate visual page with updated template/data."""
    # 1. Validate ownership/permissions
    # 2. Delete existing artifact
    # 3. Render new HTML page
    # 4. Store artifact and update metadata
    # 5. Return updated ExplanationMetadata
```

### 4. Storage Layer

**File**: `engine/src/agent33/explanation/storage.py` (new)

**Schema addition** (extend `ExplanationMetadata`):
```python
class ExplanationMetadata(BaseModel):
    # ... existing fields ...
    artifact_path: str | None = None  # Path to rendered HTML file
    artifact_size_bytes: int = 0
    expires_at: datetime | None = None  # TTL for cleanup
```

**Storage operations**:
```python
def store_artifact(explanation_id: str, html_content: str) -> str:
    """Save rendered HTML to disk, return file path."""

def load_artifact(explanation_id: str) -> str | None:
    """Load HTML content from disk if exists."""

def cleanup_expired_artifacts() -> int:
    """Delete artifacts past expiration, return count removed."""
```

### 5. Frontend Viewer

**File**: `frontend/src/components/ExplanationView.tsx` (extend existing)

**UI additions**:
```tsx
// Add button to toggle visual view
<button onClick={() => setShowVisual(!showVisual)}>
  {showVisual ? "Show Text" : "Show Visual Page"}
</button>

// Render iframe when visual mode active
{showVisual && (
  <iframe
    src={`/v1/explanations/${explanation.id}/visual`}
    sandbox="allow-scripts allow-same-origin"
    className="visual-page-viewer"
    title="Visual Explanation"
  />
)}
```

**File**: `frontend/src/data/domains/explanations.ts` (extend existing)

**New operations**:
```typescript
getVisualPage: {
  type: "get" as const,
  path: (id: string) => `/explanations/${id}/visual`,
  requiresAuth: true,
},

regenerateVisual: {
  type: "post" as const,
  path: (id: string) => `/explanations/${id}/regenerate`,
  requiresAuth: true,
},
```

---

## Target Files for Implementation

### Backend (Priority 1)
1. `engine/src/agent33/explanation/renderer.py` (create)
2. `engine/src/agent33/explanation/storage.py` (create)
3. `engine/src/agent33/explanation/templates/base.html.j2` (create)
4. `engine/src/agent33/explanation/templates/diff_review.html.j2` (create)
5. `engine/src/agent33/explanation/templates/plan_review.html.j2` (create)
6. `engine/src/agent33/explanation/templates/project_recap.html.j2` (create)
7. `engine/src/agent33/explanation/models.py` (extend with artifact fields)
8. `engine/src/agent33/api/routes/explanations.py` (add visual endpoints)

### Frontend (Priority 2)
9. `frontend/src/components/ExplanationView.tsx` (add iframe viewer)
10. `frontend/src/data/domains/explanations.ts` (add visual operations)

### Testing (Priority 3)
11. `engine/tests/test_visual_rendering.py` (create - unit tests for renderer)
12. `engine/tests/test_explanations_api.py` (extend with visual endpoint tests)
13. `frontend/src/components/ExplanationView.test.ts` (extend with visual mode tests)

### Documentation (Priority 4)
14. `docs/walkthroughs.md` (add visual page generation example)
15. `docs/progress/phase-26-stage3-validation-log.md` (create - capture evidence)

---

## Acceptance Criteria

### Functional Requirements
- [ ] Visual pages render for `diff_review`, `plan_review`, `project_recap` modes
- [ ] Fact-check claims visible in visual output with color-coded badges
- [ ] Syntax highlighting applied to all code blocks
- [ ] Side-by-side diff view with line numbers and change indicators
- [ ] Phase plan sections collapsible with TOC navigation
- [ ] Artifacts stored with 30-day TTL and cleanup task

### Non-Functional Requirements
- [ ] Visual page generation completes in <2s for median inputs
- [ ] HTML sanitization blocks all OWASP XSS test vectors
- [ ] Iframe viewer loads without console errors or CSP violations
- [ ] Mobile responsiveness: pages readable on 375px viewport
- [ ] Accessibility: WCAG 2.1 AA compliance for templates

### Testing Requirements
- [ ] Unit tests for renderer cover all template modes
- [ ] Integration tests verify end-to-end visual generation
- [ ] Security tests validate XSS prevention
- [ ] Performance tests measure render time for various input sizes
- [ ] Manual browser testing in Chrome, Firefox, Safari

### Documentation Requirements
- [ ] Walkthrough includes visual page generation example
- [ ] API docs updated with new endpoints and schemas
- [ ] Template customization guide for future enhancements
- [ ] Validation log captures test evidence and screenshots

---

## Dependencies

**Python packages** (add to `engine/pyproject.toml`):
- `jinja2>=3.1.0` - Template rendering
- `bleach>=6.0.0` - HTML sanitization
- `pygments>=2.17.0` - Syntax highlighting

**Configuration**:
- Add `EXPLANATION_ARTIFACT_DIR` to settings (default: `engine/data/explanations`)
- Add `EXPLANATION_TTL_DAYS` to settings (default: 30)

---

## Implementation Sequence

1. **Template infrastructure** (2-3 hours)
   - Create renderer.py with Jinja2 setup
   - Implement base template with styles
   - Add sanitization and highlighting utilities

2. **Mode templates** (3-4 hours)
   - Build diff_review template with side-by-side layout
   - Build plan_review template with section collapse
   - Build project_recap template with timeline cards

3. **Storage layer** (1-2 hours)
   - Create storage.py with artifact save/load
   - Extend models with artifact fields
   - Implement TTL cleanup background task

4. **API endpoints** (2-3 hours)
   - Add GET /visual endpoint with artifact serving
   - Add POST /regenerate endpoint with re-render logic
   - Wire to renderer and storage modules

5. **Frontend viewer** (2-3 hours)
   - Add visual toggle to ExplanationView
   - Implement sandboxed iframe rendering
   - Add domain operations for new endpoints

6. **Testing** (3-4 hours)
   - Write unit tests for renderer and templates
   - Write integration tests for visual endpoints
   - Add security tests for XSS prevention
   - Extend frontend tests for viewer

7. **Documentation** (1-2 hours)
   - Update API docs and walkthroughs
   - Create validation log with test evidence
   - Document template customization

---

## Rollout Strategy

1. **Merge criteria**: All tests pass, documentation complete, manual validation done
2. **Feature flag**: None required (new endpoints, backward compatible)
3. **Monitoring**: Track visual generation time and artifact storage growth
4. **Rollback plan**: Endpoints can be disabled if issues arise; text mode remains available

