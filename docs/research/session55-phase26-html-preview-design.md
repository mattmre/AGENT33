# Session 55 – Phase 26: HTML Preview Design

**Date:** 2026-03-08  
**Scope:** Explanation domain operations + HTML preview rendering  
**Branch:** `feat/session55-phase26-explanation-ops`

---

## 1. Problem Statement

The Explanations domain previously supported only a generic `POST /v1/explanations/` endpoint and read operations. Phase 26 introduces three specialised explanation endpoints (`diff-review`, `plan-review`, `project-recap`) whose responses return **HTML-formatted content**. The frontend needs to:

1. Expose these operations in the Operations Hub via domain config.
2. Render HTML responses inline without breaking the existing plain-text display.
3. Maintain security: untrusted HTML must not execute scripts or navigate the parent frame.

## 2. Design Decisions

### 2.1 Domain Config – Three New Operations

Each new operation maps 1:1 to a backend endpoint and Pydantic request model:

| Operation ID | Backend Endpoint | Request Model |
|---|---|---|
| `explanations-diff-review` | `POST /v1/explanations/diff-review` | `DiffReviewRequest` |
| `explanations-plan-review` | `POST /v1/explanations/plan-review` | `PlanReviewRequest` |
| `explanations-project-recap` | `POST /v1/explanations/project-recap` | `ProjectRecapRequest` |

Default request bodies are derived from the Pydantic models in `engine/src/agent33/explanation/models.py` to ensure field names, required fields, and types match.

All three operations carry `uxHint: "explanation-html"`, which signals `OperationCard` to render the response through `ExplanationView` instead of the raw JSON `<pre>` block.

### 2.2 HTML Content Detection

Rather than relying on a response header or backend metadata flag, detection is performed client-side on `explanation.content`:

```ts
function isHtmlContent(content: string): boolean {
  const trimmed = content.trimStart().toLowerCase();
  return (
    trimmed.startsWith("<!doctype") ||
    trimmed.startsWith("<html") ||
    trimmed.startsWith("<div")
  );
}
```

**Why these three prefixes?**
- `<!DOCTYPE html>` – standard full HTML documents returned by the renderer.
- `<html` – documents without a doctype preamble.
- `<div` – HTML fragments that the renderer wraps in a container `<div>`.

This covers all outputs produced by `engine/src/agent33/explanation/renderer.py`.

**Alternative considered:** A `content_type` field on `ExplanationMetadata`. Rejected because it would require a backend schema migration and this heuristic is sufficient and zero-cost.

### 2.3 Sandboxed Iframe Rendering

HTML content is rendered using:

```tsx
<iframe
  srcDoc={explanation.content}
  sandbox="allow-same-origin"
  style={{ width: "100%", minHeight: "400px", border: "1px solid #e5e7eb" }}
  title="Explanation content"
/>
```

**Security properties of `sandbox="allow-same-origin"`:**
- **No script execution** – `allow-scripts` is intentionally omitted.
- **No form submission** – forms inside the iframe cannot submit.
- **No navigation** – the iframe cannot navigate the parent or open popups.
- `allow-same-origin` is included so that the iframe can inherit styles from the parent origin if needed, but since scripts are blocked, this does not create an XSS vector.

**Alternative considered:** `dangerouslySetInnerHTML`. Rejected because it introduces direct DOM injection risks and does not provide the isolation boundary that an iframe offers.

### 2.4 UxHint Wiring in OperationCard

The existing `OperationCard` component uses a flag-per-hint pattern:

```ts
const isExplanationHtml = operation.uxHint === "explanation-html";
```

The `OperationUxHint` union type is extended with `"explanation-html"`.

Result rendering follows the same conditional pattern as other hints: when `isExplanationHtml && result.ok`, the `ExplanationView` component is rendered instead of the default JSON `<pre>` block.

### 2.5 Plain Text Backward Compatibility

When `isHtmlContent()` returns `false`, the component renders the original `<p>{explanation.content}</p>` markup. All existing tests continue to pass unmodified; new tests validate the HTML → iframe path.

## 3. Files Modified

| File | Change |
|---|---|
| `frontend/src/types/index.ts` | Added `"explanation-html"` to `OperationUxHint` |
| `frontend/src/data/domains/explanations.ts` | Added 3 operations with `uxHint` and default bodies |
| `frontend/src/components/ExplanationView.tsx` | HTML detection + iframe rendering |
| `frontend/src/components/OperationCard.tsx` | Import `ExplanationView`, wire `isExplanationHtml` flag |
| `frontend/src/components/ExplanationView.test.ts` | Added tests for HTML/iframe, plain text, and claims |

## 4. Testing Strategy

Tests use `renderToStaticMarkup` (server-side rendering) which is already established in the test suite. This validates:

- Plain text content produces `<p>` tags, not `<iframe>`.
- HTML content (all three prefix variants) produces `<iframe>` with correct sandbox and title attributes.
- Claims list renders when present, is omitted when empty.
- Metadata section renders conditionally.

## 5. Future Considerations

- **Auto-resize iframe:** Currently uses a fixed `minHeight: 400px`. A `ResizeObserver`-based approach could dynamically match the iframe's content height.
- **Content-type metadata:** If the backend adds a `content_type` field to `ExplanationMetadata`, the client-side heuristic can be replaced with a direct check.
- **Dark mode:** The iframe content is isolated from parent CSS. A future enhancement could inject a theme stylesheet into the `srcDoc`.
