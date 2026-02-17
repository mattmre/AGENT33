# Phase 26: Visual Explainer Decision and Review Pages

## Status: Planned

## Overview
- **Phase**: 26 of 26+
- **Category**: Product / Explainability UX
- **Primary Goal**: Add first-class visual review and decision-intelligence pages so AGENT-33 can render diffs, plans, and execution reasoning in website-friendly HTML outputs inspired by visual-explainer workflows.

## Objectives
- Deliver structured visual explanation pages for:
  - diff reviews
  - plan reviews
  - project recap/context reload
  - fact-check validation against repository state
- Reuse Phase 25 graph artifacts and existing AGENT-33 traces/evaluation outputs.
- Provide operator workflows in the AGENT-33 frontend that generate and view these pages without manual prompt engineering.
- Ensure safe rendering (sanitization + auth-aware access) and measurable usefulness.

## Scope

### In Scope
- New backend explanation endpoints for review-style page generation.
- HTML template orchestration for visual explanation page types.
- Frontend controls to request, list, and open generated explanation pages.
- Metadata tracking (source refs, confidence markers, generation time, model/tool context).
- Documentation and test coverage for new visual explanation flows.

### Out of Scope
- Free-form WYSIWYG page editor.
- Public unauthenticated sharing links.
- External CDN dependency requirements for core rendering.
- Non-technical marketing page generation.

## Deliverables

| # | Deliverable | Target Path | Description |
|---|-------------|-------------|-------------|
| 1 | Visual explanation API routes | `engine/src/agent33/api/routes/visual_explanations.py` | Endpoints for diff/plan/recap/fact-check generation and retrieval |
| 2 | Explanation orchestration service | `engine/src/agent33/services/visual_explanations.py` | Normalizes inputs, renders templates, stores artifacts metadata |
| 3 | Render template pack | `engine/src/agent33/templates/visual_explainer/` | Internal templates for review page types |
| 4 | Frontend explanation workspace | `frontend/src/features/explanations/` | UI module to generate and open explanation pages |
| 5 | Domain wiring | `frontend/src/data/domains/` | New domain operations for visual explanation endpoints |
| 6 | Artifact metadata model | `engine/src/agent33/models/` | Track explanation runs, source refs, and confidence signals |
| 7 | Backend tests | `engine/tests/test_visual_explanations_api.py` | API and service behavior tests |
| 8 | Frontend tests | `frontend/src/features/explanations/*.test.tsx` | Interaction and rendering flow tests |
| 9 | Operator documentation | `docs/walkthroughs.md` | How to run diff/plan/recap/fact-check visual pages |
| 10 | Progress evidence log | `docs/progress/phase-26-visual-review-log.md` | Validation runs, screenshots, known issues, fixes |

## Acceptance Criteria
- [ ] Operators can generate a visual diff review from a branch/ref comparison.
- [ ] Operators can generate a plan-review page against a provided plan path.
- [ ] Operators can generate a project recap page from recent repo activity + traces.
- [ ] Operators can run fact-check mode that flags unsupported claims in generated pages.
- [ ] Generated pages are persisted with metadata and retrievable via authenticated API.
- [ ] Rendering pipeline sanitizes dynamic content and prevents script injection.
- [ ] Backend and frontend tests pass for all new explanation flows.
- [ ] Explanation generation is documented with examples and troubleshooting guidance.
- [ ] Generated page latency is acceptable for interactive use (<5s for median input size).
- [ ] UX review confirms pages are easier to consume than terminal-only outputs.

## Dependencies
- Phase 14 (security hardening patterns for sanitization and auth boundaries)
- Phase 16 (trace and observability artifacts used in recap/fact-check pages)
- Phase 22 (frontend platform and domain operation UX)
- Phase 25 (workflow graph foundation and visualization primitives)

## Blocks
- Phase 27+ advanced collaboration/sharing workflows, if introduced.

## Orchestration Guidance
1. **Design contracts first**:
   - Define request/response schemas for each page type.
   - Define metadata schema and storage lifecycle.
2. **Build backend generation service**:
   - Normalize input sources (git refs, plan files, trace IDs).
   - Create deterministic generation prompts/templates.
3. **Integrate frontend controls**:
   - Add explanation generation panel and recent artifacts list.
   - Wire page preview/open flows.
4. **Harden safety and quality checks**:
   - Enforce sanitization and auth scope checks.
   - Add fact-check mode before page promotion.
5. **Validate with realistic workflows**:
   - Compare outputs for large diffs and long plan docs.
   - Measure latency and operator usefulness.

## Review Checklist
- [ ] API and metadata schemas reviewed for backward compatibility.
- [ ] Security review completed for HTML sanitization and artifact access control.
- [ ] QA review covers diff/plan/recap/fact-check paths end-to-end.
- [ ] UX review confirms readability and operator navigation quality.
- [ ] Documentation includes concrete command/UI examples and recovery steps.

## References
- Phase 25 spec: `docs/phases/PHASE-25-VISUAL-EXPLAINER-INTEGRATION.md`
- Visual explainer integration research: `docs/research/visual-explainer-integration-analysis-2026-02-17.md`
- Visual-explainer upstream repo: https://github.com/nicobailon/visual-explainer
