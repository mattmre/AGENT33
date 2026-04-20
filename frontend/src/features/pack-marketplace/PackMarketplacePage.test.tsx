import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { PackMarketplacePage } from "./PackMarketplacePage";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

describe("PackMarketplacePage", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    window.__AGENT33_CONFIG__ = { API_BASE_URL: "http://localhost:8000" };
  });

  afterEach(() => {
    delete window.__AGENT33_CONFIG__;
    fetchMock.mockReset();
    vi.unstubAllGlobals();
  });

  it("uses the API key for marketplace loading and shows pack state badges", async () => {
    fetchMock.mockImplementation(async (input, init) => {
      const url = String(input);

      if (url === "http://localhost:8000/v1/marketplace/packs") {
        expect(init).toEqual(
          expect.objectContaining({
            headers: expect.objectContaining({
              Accept: "application/json",
              "X-API-Key": "market-key"
            })
          })
        );
        return jsonResponse({
          packs: [
            {
              name: "analytics-pack",
              description: "Adds analytics workflows",
              author: "AGENT-33",
              tags: ["analytics", "metrics"],
              category: "analytics",
              latest_version: "2.0.0",
              versions_count: 2,
              sources: ["core"]
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/categories") {
        return jsonResponse({
          categories: [
            {
              slug: "analytics",
              label: "Analytics",
              description: "Analytics packs",
              parent_slug: ""
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/featured") {
        return jsonResponse({
          records: [
            {
              pack_name: "analytics-pack",
              version: "2.0.0",
              status: "featured",
              quality: { overall_score: 0.9, label: "high", passed: true },
              badges: ["featured"],
              featured: true,
              verified: true,
              reviewer_id: "ops",
              review_notes: "",
              deprecation_reason: "",
              submitted_at: null,
              reviewed_at: null,
              listed_at: null,
              download_count: 24
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/curation") {
        return jsonResponse({
          records: [
            {
              pack_name: "analytics-pack",
              version: "2.0.0",
              status: "featured",
              quality: { overall_score: 0.9, label: "high", passed: true },
              badges: ["featured"],
              featured: true,
              verified: true,
              reviewer_id: "ops",
              review_notes: "",
              deprecation_reason: "",
              submitted_at: null,
              reviewed_at: null,
              listed_at: null,
              download_count: 24
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/packs") {
        return jsonResponse({
          packs: [
            {
              name: "analytics-pack",
              version: "2.0.0",
              description: "Adds analytics workflows",
              author: "AGENT-33",
              tags: ["analytics", "metrics"],
              category: "analytics",
              skills_count: 4,
              status: "installed"
            }
          ],
          count: 1
        });
      }

      throw new Error(`Unhandled fetch: ${url}`);
    });

    render(<PackMarketplacePage token={null} apiKey="market-key" />);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));
    expect(screen.getAllByRole("button", { name: /open details for analytics-pack/i })).toHaveLength(2);
    expect(screen.getAllByText("Featured").length).toBeGreaterThan(0);
    expect(screen.getByText("Installed")).toBeInTheDocument();
  });

  it("installs a selected marketplace version with bearer auth", async () => {
    fetchMock.mockImplementation(async (input, init) => {
      const url = String(input);

      if (url === "http://localhost:8000/v1/marketplace/packs") {
        return jsonResponse({
          packs: [
            {
              name: "alpha-pack",
              description: "Alpha workflow pack",
              author: "AGENT-33",
              tags: ["alpha"],
              category: "automation",
              latest_version: "1.4.0",
              versions_count: 2,
              sources: ["community"]
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/categories") {
        return jsonResponse({ categories: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/marketplace/featured") {
        return jsonResponse({ records: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/marketplace/curation") {
        return jsonResponse({ records: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/packs") {
        return jsonResponse({ packs: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/marketplace/packs/alpha-pack") {
        return jsonResponse({
          name: "alpha-pack",
          description: "Alpha workflow pack",
          author: "AGENT-33",
          tags: ["alpha"],
          category: "automation",
          latest_version: "1.4.0",
          sources: ["community"],
          versions: [
            {
              version: "1.4.0",
              description: "Latest release",
              author: "AGENT-33",
              tags: ["alpha"],
              category: "automation",
              skills_count: 3,
              source_name: "community",
              source_type: "registry",
              trust_level: "verified"
            },
            {
              version: "1.3.0",
              description: "Previous release",
              author: "AGENT-33",
              tags: ["alpha"],
              category: "automation",
              skills_count: 2,
              source_name: "community",
              source_type: "registry",
              trust_level: "medium"
            }
          ]
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/install") {
        expect(init).toEqual(
          expect.objectContaining({
            method: "POST",
            headers: expect.objectContaining({
              Accept: "application/json",
              Authorization: "Bearer session-token",
              "Content-Type": "application/json"
            }),
            body: JSON.stringify({ name: "alpha-pack", version: "1.4.0" })
          })
        );
        return jsonResponse(
          {
            success: true,
            pack_name: "alpha-pack",
            version: "1.4.0",
            skills_loaded: 3,
            errors: [],
            warnings: []
          },
          201
        );
      }

      if (url === "http://localhost:8000/v1/packs/alpha-pack") {
        return jsonResponse({
          name: "alpha-pack",
          version: "1.4.0",
          description: "Alpha workflow pack",
          author: "AGENT-33",
          tags: ["alpha"],
          category: "automation",
          skills_count: 3,
          status: "installed",
          license: "MIT",
          loaded_skill_names: ["one", "two", "three"],
          engine_min_version: "0.1.0",
          installed_at: null,
          source: "marketplace",
          source_reference: "community",
          checksum: "abc123",
          enabled_for_tenant: true
        });
      }

      if (url === "http://localhost:8000/v1/packs/alpha-pack/trust") {
        return jsonResponse({
          pack_name: "alpha-pack",
          installed_version: "1.4.0",
          source: "marketplace",
          source_reference: "community",
          allowed: true,
          reason: "",
          policy: { require_signature: false, min_trust_level: "medium", allowed_signers: [] }
        });
      }

      throw new Error(`Unhandled fetch: ${url}`);
    });

    const user = userEvent.setup();
    render(<PackMarketplacePage token="session-token" apiKey={null} />);

    await user.click(await screen.findByRole("button", { name: /open details for alpha-pack/i }));
    await user.click(await screen.findByRole("button", { name: /install selected version/i }));

    expect(await screen.findByText("Installed alpha-pack 1.4.0")).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/v1/marketplace/install",
      expect.objectContaining({ method: "POST" })
    ));
  });

  it("submits an installed pack for community curation and shows the updated status", async () => {
    fetchMock.mockImplementation(async (input, init) => {
      const url = String(input);

      if (url === "http://localhost:8000/v1/marketplace/packs") {
        return jsonResponse({
          packs: [
            {
              name: "community-pack",
              description: "Community-ready automation pack",
              author: "AGENT-33",
              tags: ["community", "automation"],
              category: "automation",
              latest_version: "1.2.0",
              versions_count: 1,
              sources: ["community"]
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/categories") {
        return jsonResponse({ categories: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/marketplace/featured") {
        return jsonResponse({ records: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/marketplace/curation") {
        return jsonResponse({ records: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/packs") {
        return jsonResponse({
          packs: [
            {
              name: "community-pack",
              version: "1.2.0",
              description: "Community-ready automation pack",
              author: "AGENT-33",
              tags: ["community", "automation"],
              category: "automation",
              skills_count: 2,
              status: "installed"
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/packs/community-pack") {
        return jsonResponse({
          name: "community-pack",
          description: "Community-ready automation pack",
          author: "AGENT-33",
          tags: ["community", "automation"],
          category: "automation",
          latest_version: "1.2.0",
          sources: ["community"],
          versions: [
            {
              version: "1.2.0",
              description: "Current release",
              author: "AGENT-33",
              tags: ["community", "automation"],
              category: "automation",
              skills_count: 2,
              source_name: "community",
              source_type: "registry",
              trust_level: "verified"
            }
          ]
        });
      }

      if (url === "http://localhost:8000/v1/packs/community-pack") {
        return jsonResponse({
          name: "community-pack",
          version: "1.2.0",
          description: "Community-ready automation pack",
          author: "AGENT-33",
          tags: ["community", "automation"],
          category: "automation",
          skills_count: 2,
          status: "installed",
          license: "MIT",
          loaded_skill_names: ["workflow-builder", "ops-helper"],
          engine_min_version: "0.1.0",
          installed_at: null,
          source: "marketplace",
          source_reference: "community",
          checksum: "checksum",
          enabled_for_tenant: true
        });
      }

      if (url === "http://localhost:8000/v1/packs/community-pack/trust") {
        return jsonResponse({
          pack_name: "community-pack",
          installed_version: "1.2.0",
          source: "marketplace",
          source_reference: "community",
          allowed: true,
          reason: "",
          policy: { require_signature: false, min_trust_level: "medium", allowed_signers: [] }
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/quality/community-pack") {
        return jsonResponse({
          overall_score: 0.92,
          label: "high",
          passed: true,
          checks: [
            {
              name: "description_quality",
              passed: true,
              score: 1,
              reason: "description length: 74 chars"
            }
          ]
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/curation/submit") {
        expect(init).toEqual(
          expect.objectContaining({
            method: "POST",
            headers: expect.objectContaining({
              Accept: "application/json",
              Authorization: "Bearer session-token",
              "Content-Type": "application/json"
            }),
            body: JSON.stringify({ pack_name: "community-pack", version: "1.2.0" })
          })
        );

        return jsonResponse(
          {
            pack_name: "community-pack",
            version: "1.2.0",
            status: "submitted",
            quality: {
              overall_score: 0.92,
              label: "high",
              passed: true,
              checks: [
                {
                  name: "description_quality",
                  passed: true,
                  score: 1,
                  reason: "description length: 74 chars"
                }
              ]
            },
            badges: [],
            featured: false,
            verified: false,
            reviewer_id: "",
            review_notes: "",
            deprecation_reason: "",
            submitted_at: null,
            reviewed_at: null,
            listed_at: null,
            download_count: 0
          },
          201
        );
      }

      throw new Error(`Unhandled fetch: ${url}`);
    });

    const user = userEvent.setup();
    render(<PackMarketplacePage token="session-token" apiKey={null} />);

    await user.click(await screen.findByRole("button", { name: /open details for community-pack/i }));
    expect(await screen.findByText(/quality preview:/i)).toBeInTheDocument();

    await user.click(await screen.findByRole("button", { name: /submit for curation/i }));

    expect(
      await screen.findByText("Submitted community-pack for marketplace curation.")
    ).toBeInTheDocument();
    expect(screen.getAllByText("submitted").length).toBeGreaterThan(0);
  });

  it("keeps submission available when installed detail fetch fails", async () => {
    fetchMock.mockImplementation(async (input) => {
      const url = String(input);

      if (url === "http://localhost:8000/v1/marketplace/packs") {
        return jsonResponse({
          packs: [
            {
              name: "community-pack",
              description: "Community-ready automation pack",
              author: "AGENT-33",
              tags: ["community", "automation"],
              category: "automation",
              latest_version: "1.2.0",
              versions_count: 1,
              sources: ["community"]
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/categories") {
        return jsonResponse({ categories: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/marketplace/featured") {
        return jsonResponse({ records: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/marketplace/curation") {
        return jsonResponse({ records: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/packs") {
        return jsonResponse({
          packs: [
            {
              name: "community-pack",
              version: "1.2.0",
              description: "Community-ready automation pack",
              author: "AGENT-33",
              tags: ["community", "automation"],
              category: "automation",
              skills_count: 2,
              status: "installed"
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/packs/community-pack") {
        return jsonResponse({
          name: "community-pack",
          description: "Community-ready automation pack",
          author: "AGENT-33",
          tags: ["community", "automation"],
          category: "automation",
          latest_version: "1.2.0",
          sources: ["community"],
          versions: [
            {
              version: "1.2.0",
              description: "Current release",
              author: "AGENT-33",
              tags: ["community", "automation"],
              category: "automation",
              skills_count: 2,
              source_name: "community",
              source_type: "registry",
              trust_level: "verified"
            }
          ]
        });
      }

      if (url === "http://localhost:8000/v1/packs/community-pack") {
        return jsonResponse({ detail: "detail unavailable" }, 500);
      }

      if (url === "http://localhost:8000/v1/packs/community-pack/trust") {
        return jsonResponse({
          pack_name: "community-pack",
          installed_version: "1.2.0",
          source: "marketplace",
          source_reference: "community",
          allowed: true,
          reason: "",
          policy: { require_signature: false, min_trust_level: "medium", allowed_signers: [] }
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/quality/community-pack") {
        return jsonResponse({
          overall_score: 0.92,
          label: "high",
          passed: true,
          checks: []
        });
      }

      throw new Error(`Unhandled fetch: ${url}`);
    });

    const user = userEvent.setup();
    render(<PackMarketplacePage token="session-token" apiKey={null} />);

    await user.click(await screen.findByRole("button", { name: /open details for community-pack/i }));

    expect(
      await screen.findByText("Installed pack detail failed: detail unavailable")
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /submit for curation/i })).toBeInTheDocument();
    expect(
      screen.queryByText(/install this pack before submitting it for marketplace curation/i)
    ).not.toBeInTheDocument();
  });

  it("treats draft curation records as submittable", async () => {
    fetchMock.mockImplementation(async (input) => {
      const url = String(input);

      if (url === "http://localhost:8000/v1/marketplace/packs") {
        return jsonResponse({
          packs: [
            {
              name: "draft-pack",
              description: "Drafted community pack",
              author: "AGENT-33",
              tags: ["community"],
              category: "automation",
              latest_version: "0.4.0",
              versions_count: 1,
              sources: ["community"]
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/categories") {
        return jsonResponse({ categories: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/marketplace/featured") {
        return jsonResponse({ records: [], count: 0 });
      }

      if (url === "http://localhost:8000/v1/marketplace/curation") {
        return jsonResponse({
          records: [
            {
              pack_name: "draft-pack",
              version: "0.4.0",
              status: "draft",
              quality: null,
              badges: [],
              featured: false,
              verified: false,
              reviewer_id: "",
              review_notes: "",
              deprecation_reason: "",
              submitted_at: null,
              reviewed_at: null,
              listed_at: null,
              download_count: 0
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/packs") {
        return jsonResponse({
          packs: [
            {
              name: "draft-pack",
              version: "0.4.0",
              description: "Drafted community pack",
              author: "AGENT-33",
              tags: ["community"],
              category: "automation",
              skills_count: 1,
              status: "installed"
            }
          ],
          count: 1
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/packs/draft-pack") {
        return jsonResponse({
          name: "draft-pack",
          description: "Drafted community pack",
          author: "AGENT-33",
          tags: ["community"],
          category: "automation",
          latest_version: "0.4.0",
          sources: ["community"],
          versions: [
            {
              version: "0.4.0",
              description: "Current release",
              author: "AGENT-33",
              tags: ["community"],
              category: "automation",
              skills_count: 1,
              source_name: "community",
              source_type: "registry",
              trust_level: "verified"
            }
          ]
        });
      }

      if (url === "http://localhost:8000/v1/packs/draft-pack") {
        return jsonResponse({
          name: "draft-pack",
          version: "0.4.0",
          description: "Drafted community pack",
          author: "AGENT-33",
          tags: ["community"],
          category: "automation",
          skills_count: 1,
          status: "installed",
          license: "MIT",
          loaded_skill_names: ["workflow-builder"],
          engine_min_version: "0.1.0",
          installed_at: null,
          source: "marketplace",
          source_reference: "community",
          checksum: "checksum",
          enabled_for_tenant: true
        });
      }

      if (url === "http://localhost:8000/v1/packs/draft-pack/trust") {
        return jsonResponse({
          pack_name: "draft-pack",
          installed_version: "0.4.0",
          source: "marketplace",
          source_reference: "community",
          allowed: true,
          reason: "",
          policy: { require_signature: false, min_trust_level: "medium", allowed_signers: [] }
        });
      }

      if (url === "http://localhost:8000/v1/marketplace/quality/draft-pack") {
        return jsonResponse({
          overall_score: 0.65,
          label: "medium",
          passed: true,
          checks: []
        });
      }

      throw new Error(`Unhandled fetch: ${url}`);
    });

    const user = userEvent.setup();
    render(<PackMarketplacePage token="session-token" apiKey={null} />);

    await user.click(await screen.findByRole("button", { name: /open details for draft-pack/i }));

    expect(await screen.findByRole("button", { name: /submit for curation/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /resubmit for curation/i })).not.toBeInTheDocument();
  });
});
