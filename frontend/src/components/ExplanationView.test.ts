import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ExplanationView, type ExplanationData } from "./ExplanationView";

describe("ExplanationView", () => {
  const mockExplanation: ExplanationData = {
    id: "expl-abc123",
    entity_type: "workflow",
    entity_id: "hello-flow",
    content: "This workflow processes greetings and generates responses.",
    fact_check_status: "verified",
    created_at: "2024-01-16T12:00:00Z",
    metadata: {
      model: "llama3.1"
    }
  };

  it("renders core explanation fields", () => {
    const html = renderToStaticMarkup(
      createElement(ExplanationView, { explanation: mockExplanation })
    );
    expect(html).toContain("expl-abc123");
    expect(html).toContain("workflow / hello-flow");
    expect(html).toContain("This workflow processes greetings and generates responses.");
    expect(html).toContain("verified");
  });

  it("renders metadata section when metadata exists", () => {
    const html = renderToStaticMarkup(
      createElement(ExplanationView, { explanation: mockExplanation })
    );
    expect(html).toContain("Metadata");
    expect(html).toContain("llama3.1");
  });

  it("hides metadata section when metadata is absent", () => {
    const withoutMetadata: ExplanationData = {
      id: "expl-no-meta",
      entity_type: "workflow",
      entity_id: "flow",
      content: "test",
      fact_check_status: "pending",
      created_at: "2024-01-16T12:00:00Z"
    };
    const html = renderToStaticMarkup(
      createElement(ExplanationView, { explanation: withoutMetadata })
    );
    expect(html).not.toContain("Metadata");
  });
});
