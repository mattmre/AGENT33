import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn()
}));

vi.mock("../../lib/api", () => ({
  apiRequest: apiRequestMock
}));

import { WorkflowStarterPanel } from "./WorkflowStarterPanel";

function renderPanel(overrides: Partial<React.ComponentProps<typeof WorkflowStarterPanel>> = {}) {
  return render(
    <WorkflowStarterPanel
      token="token"
      apiKey=""
      onOpenSetup={vi.fn()}
      onOpenSpawner={vi.fn()}
      onOpenOperations={vi.fn()}
      onResult={vi.fn()}
      {...overrides}
    />
  );
}

describe("WorkflowStarterPanel", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("prompts for credentials before creating workflows", () => {
    renderPanel({ token: "", apiKey: "" });

    expect(screen.getByText("Connect to the engine first")).toBeInTheDocument();
    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("recommends and creates a workflow from a plain-language goal", async () => {
    apiRequestMock
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        data: {
          query: "research",
          matches: [
            {
              name: "research-template",
              description: "Research template",
              score: 0.8,
              source: "template",
              version: "1.0.0",
              tags: ["research"],
              source_path: "core/workflows/research.yaml",
              pack: null
            }
          ]
        }
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        data: {
          query: "research",
          matches: [
            {
              name: "web-research",
              description: "Search and summarize sources",
              score: 0.7,
              version: "1.0.0",
              tags: ["research"],
              pack: null
            }
          ]
        }
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        data: {
          name: "weekly-agent-market-scan",
          version: "1.0.0",
          step_count: 4,
          created: true
        }
      });

    renderPanel();

    await userEvent.type(screen.getByLabelText("Workflow name"), "weekly-agent-market-scan");
    await userEvent.type(
      screen.getByLabelText("Goal"),
      "Track agent OS and MCP changes weekly."
    );
    await userEvent.click(screen.getByRole("button", { name: "Recommend plan" }));

    expect(await screen.findByText("research-template")).toBeInTheDocument();
    expect(screen.getByText("web-research")).toBeInTheDocument();
    expect(screen.getByText("weekly-agent-market-scan")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Create workflow" }));

    await waitFor(() => {
      expect(apiRequestMock).toHaveBeenCalledWith(
        expect.objectContaining({
          method: "POST",
          path: "/v1/workflows/",
          token: "token",
          apiKey: ""
        })
      );
    });
    expect(await screen.findByText("weekly-agent-market-scan created with 4 steps.")).toBeInTheDocument();
  });

  it("preserves outcome pack context in created workflow metadata and activity labels", async () => {
    const onResult = vi.fn();
    apiRequestMock.mockResolvedValueOnce({
      ok: true,
      status: 201,
      data: {
        name: "founder-mvp-builder",
        version: "1.0.0",
        step_count: 3,
        created: true
      }
    });

    renderPanel({
      onResult,
      initialDraft: {
        id: "outcome-founder-mvp-builder",
        name: "founder-mvp-builder",
        goal: "Create the first MVP plan.",
        kind: "automation-loop",
        output: "MVP brief; First sprint plan",
        author: "AGENT-33",
        sourceLabel: "Outcome pack: Founder MVP Builder",
        sourcePack: "official-outcome-packs",
        sourcePackVersion: "1.0.0",
        sourceOutcomeId: "founder-mvp-builder"
      }
    });

    expect(screen.getByText("Loaded starter: Outcome pack: Founder MVP Builder")).toBeInTheDocument();
    expect(screen.getByText("Pack: official-outcome-packs v1.0.0")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Create workflow" }));

    await waitFor(() => {
      expect(apiRequestMock).toHaveBeenCalledWith(
        expect.objectContaining({
          method: "POST",
          path: "/v1/workflows/"
        })
      );
    });

    const body = JSON.parse(apiRequestMock.mock.calls[0][0].body as string) as {
      metadata: { tags: string[] };
    };
    expect(body.metadata.tags).toEqual(
      expect.arrayContaining([
        "pack:official-outcome-packs",
        "pack-version:1.0.0",
        "outcome:founder-mvp-builder"
      ])
    );
    expect(onResult).toHaveBeenCalledWith(
      "Workflow Starter - Create Workflow from official-outcome-packs",
      expect.objectContaining({ status: 201 })
    );
  });
});
