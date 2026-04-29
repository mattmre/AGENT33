import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../../lib/api";
import { ModelConnectionWizardPanel } from "./ModelConnectionWizardPanel";

vi.mock("../../lib/api", () => ({
  apiRequest: vi.fn()
}));

const apiRequestMock = vi.mocked(apiRequest);

function mockApiRequest(): void {
  apiRequestMock.mockImplementation(({ path }) => {
    if (path === "/v1/operator/config") {
      return Promise.resolve({
        ok: true,
        status: 200,
        durationMs: 5,
        url: "http://localhost/v1/operator/config",
        data: { groups: { llm: {}, ollama: {} } }
      });
    }
    if (path === "/v1/openrouter/models") {
      return Promise.resolve({
        ok: true,
        status: 200,
        durationMs: 5,
        url: "http://localhost/v1/openrouter/models",
        data: { data: [] }
      });
    }
    if (path === "/v1/ollama/status") {
      return Promise.resolve({
        ok: true,
        status: 200,
        durationMs: 5,
        url: "http://localhost/v1/ollama/status",
        data: {
          provider: "ollama",
          state: "available",
          ok: true,
          base_url: "http://localhost:11434",
          message: "Detected 2 local Ollama models.",
          models: [
            {
              name: "qwen2.5-coder:7b",
              size: 4_700_000_000,
              details: { parameter_size: "7B", quantization_level: "Q4_K_M" }
            },
            {
              name: "llama3.2:3b",
              size: 2_000_000_000,
              details: { parameter_size: "3B", quantization_level: "Q4_0" }
            }
          ]
        }
      });
    }
    return Promise.resolve({
      ok: true,
      status: 200,
      durationMs: 5,
      url: `http://localhost${path}`,
      data: {}
    });
  });
}

describe("ModelConnectionWizardPanel provider setup v2", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
    mockApiRequest();
  });

  it("renders provider paths before model settings", () => {
    render(
      <ModelConnectionWizardPanel
        token=""
        apiKey=""
        onOpenSetup={vi.fn()}
        onOpenWorkflowCatalog={vi.fn()}
        onResult={vi.fn()}
      />
    );

    expect(screen.getByRole("heading", { name: "Pick your model provider path" })).toBeInTheDocument();
    const providerPaths = within(screen.getByRole("group", { name: "Provider setup paths" }));
    expect(providerPaths.getByRole("button", { name: /OpenRouter/ })).toHaveAttribute("aria-pressed", "true");
    expect(providerPaths.getByRole("button", { name: /Ollama/ })).toBeInTheDocument();
    expect(providerPaths.getByRole("button", { name: /LM Studio/ })).toBeInTheDocument();
    expect(providerPaths.getByRole("button", { name: /OpenAI-compatible/ })).toBeInTheDocument();
  });

  it("applies a local preset to the existing form fields", async () => {
    const user = userEvent.setup();
    render(
      <ModelConnectionWizardPanel
        token=""
        apiKey=""
        onOpenSetup={vi.fn()}
        onOpenWorkflowCatalog={vi.fn()}
        onResult={vi.fn()}
      />
    );

    await user.click(screen.getByRole("button", { name: /Ollama/ }));

    const providerPaths = within(screen.getByRole("group", { name: "Provider setup paths" }));
    expect(providerPaths.getByRole("button", { name: /Ollama/ })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByLabelText("Base URL")).toHaveValue("http://localhost:11434");
    expect(screen.getByLabelText("Default model")).toHaveValue("ollama/qwen2.5-coder:7b");
    expect(screen.getByText("Local path can run without a key")).toBeInTheDocument();
  });

  it("shows detected Ollama models and lets users choose one", async () => {
    const user = userEvent.setup();
    render(
      <ModelConnectionWizardPanel
        token="operator-token"
        apiKey=""
        onOpenSetup={vi.fn()}
        onOpenWorkflowCatalog={vi.fn()}
        onResult={vi.fn()}
      />
    );

    await user.click(screen.getByRole("button", { name: /Ollama/ }));

    expect(await screen.findByText("Detected 2 local Ollama models.")).toBeInTheDocument();
    const detectedModels = within(screen.getByRole("group", { name: "Detected Ollama models" }));
    await user.click(detectedModels.getByRole("button", { name: /llama3.2:3b/ }));

    expect(screen.getByLabelText("Default model")).toHaveValue("ollama/llama3.2:3b");
    expect(apiRequestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        path: "/v1/ollama/status",
        query: { base_url: "http://localhost:11434" }
      })
    );
  });

  it("uses Ollama status for the local connection test", async () => {
    const user = userEvent.setup();
    render(
      <ModelConnectionWizardPanel
        token="operator-token"
        apiKey=""
        onOpenSetup={vi.fn()}
        onOpenWorkflowCatalog={vi.fn()}
        onResult={vi.fn()}
      />
    );

    await user.click(screen.getByRole("button", { name: /Ollama/ }));
    await screen.findByText("Detected 2 local Ollama models.");
    await user.click(screen.getByRole("button", { name: "Test connection" }));

    expect(await screen.findByText(/Ollama is ready at http:\/\/localhost:11434/)).toBeInTheDocument();
    await waitFor(() =>
      expect(apiRequestMock).not.toHaveBeenCalledWith(
        expect.objectContaining({ path: "/v1/openrouter/probe" })
      )
    );
  });

  it("shows capability labels on recommended models", () => {
    render(
      <ModelConnectionWizardPanel
        token=""
        apiKey=""
        onOpenSetup={vi.fn()}
        onOpenWorkflowCatalog={vi.fn()}
        onResult={vi.fn()}
      />
    );

    expect(screen.getAllByText("Best for coding").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Fast start").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Long context").length).toBeGreaterThan(0);
  });
});
