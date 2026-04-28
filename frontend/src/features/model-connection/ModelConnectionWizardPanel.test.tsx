import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ModelConnectionWizardPanel } from "./ModelConnectionWizardPanel";

describe("ModelConnectionWizardPanel provider setup v2", () => {
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

    expect(screen.getByRole("button", { name: /Ollama/ })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByLabelText("Base URL")).toHaveValue("http://localhost:11434/v1");
    expect(screen.getByLabelText("Default model")).toHaveValue("ollama/qwen2.5-coder:7b");
    expect(screen.getByText("Local path can run without a key")).toBeInTheDocument();
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
