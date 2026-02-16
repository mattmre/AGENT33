import { describe, expect, it } from "vitest";

import { buildUrl, interpolatePath } from "./api";

describe("interpolatePath", () => {
  it("replaces path params", () => {
    expect(interpolatePath("/v1/reviews/{review_id}", { review_id: "abc-123" })).toBe(
      "/v1/reviews/abc-123"
    );
  });

  it("url-encodes path params", () => {
    expect(interpolatePath("/v1/files/{name}", { name: "a b.txt" })).toBe("/v1/files/a%20b.txt");
  });
});

describe("buildUrl", () => {
  it("builds full url with query", () => {
    const url = buildUrl(
      "http://localhost:8000",
      "/v1/agents/search",
      {},
      { role: "orchestrator", q: "alpha beta" }
    );
    expect(url).toBe("http://localhost:8000/v1/agents/search?role=orchestrator&q=alpha+beta");
  });

  it("omits blank query values", () => {
    const url = buildUrl("http://localhost:8000", "/health", {}, { q: "" });
    expect(url).toBe("http://localhost:8000/health");
  });
});
