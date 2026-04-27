import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn()
}));

vi.mock("../../lib/api", () => ({
  apiRequest: apiRequestMock
}));

import { OnboardingPanel } from "./OnboardingPanel";

const completeStep = {
  step_id: "OB-01",
  category: "infrastructure",
  title: "Database configured",
  description: "PostgreSQL connection is established via DATABASE_URL.",
  completed: true,
  remediation: ""
};

const pendingStep = {
  step_id: "OB-02",
  category: "llm",
  title: "LLM provider set",
  description: "At least one LLM provider is registered in the model router.",
  completed: false,
  remediation: "Configure OLLAMA_BASE_URL or OPENAI_API_KEY."
};

function renderPanel(overrides: Partial<React.ComponentProps<typeof OnboardingPanel>> = {}) {
  return render(
    <OnboardingPanel
      token="token"
      apiKey=""
      onOpenSetup={vi.fn()}
      onOpenChat={vi.fn()}
      onOpenOperations={vi.fn()}
      onResult={vi.fn()}
      {...overrides}
    />
  );
}

describe("OnboardingPanel", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("prompts for credentials before reading setup state", () => {
    const onOpenSetup = vi.fn();

    renderPanel({ token: "", apiKey: "", onOpenSetup });

    expect(screen.getByText("Connect to the engine first")).toBeInTheDocument();
    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("renders progress and plain-language remediation for pending setup checks", async () => {
    apiRequestMock.mockResolvedValue({
      ok: true,
      status: 200,
      data: {
        steps: [completeStep, pendingStep],
        completed_count: 1,
        total_count: 2,
        overall_complete: false
      }
    });

    renderPanel();

    expect(await screen.findByText("50% ready")).toBeInTheDocument();
    expect(screen.getByText("LLM provider set")).toBeInTheDocument();
    expect(screen.getByText("Why it matters")).toBeInTheDocument();
    expect(screen.getByText("Configure OLLAMA_BASE_URL or OPENAI_API_KEY.")).toBeInTheDocument();
    expect(screen.getByText("OLLAMA_BASE_URL=http://localhost:11434")).toBeInTheDocument();
    expect(apiRequestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "GET",
        path: "/v1/operator/onboarding",
        token: "token"
      })
    );
  });

  it("shows completed checks only after the operator expands them", async () => {
    apiRequestMock.mockResolvedValue({
      ok: true,
      status: 200,
      data: {
        steps: [completeStep],
        completed_count: 1,
        total_count: 1,
        overall_complete: true
      }
    });

    const user = userEvent.setup();
    renderPanel();

    expect(await screen.findByText("Ready for operator workflows")).toBeInTheDocument();
    expect(screen.queryByText("Database configured")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Show completed checks" }));

    expect(screen.getByText("Database configured")).toBeInTheDocument();
  });

  it("surfaces onboarding API failures with a retry action", async () => {
    apiRequestMock.mockResolvedValue({
      ok: false,
      status: 503,
      data: null
    });

    renderPanel();

    expect(await screen.findByText("Onboarding status is unavailable")).toBeInTheDocument();
    expect(screen.getByText("Failed to load onboarding status (503)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });
});
