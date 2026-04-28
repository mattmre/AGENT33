import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UnifiedConnectCenterPanel } from "./UnifiedConnectCenterPanel";

const { fetchOnboardingStatusMock } = vi.hoisted(() => ({
  fetchOnboardingStatusMock: vi.fn()
}));

vi.mock("../onboarding/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../onboarding/api")>();
  return {
    ...actual,
    fetchOnboardingStatus: fetchOnboardingStatusMock
  };
});

describe("UnifiedConnectCenterPanel", () => {
  beforeEach(() => {
    fetchOnboardingStatusMock.mockReset();
  });

  it("renders a unified setup checklist without credentials", () => {
    render(
      <UnifiedConnectCenterPanel token="" apiKey="" onNavigate={vi.fn()} onResult={vi.fn()} />
    );

    expect(screen.getByRole("heading", { name: "Connect the pieces AGENT-33 needs to work" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Can AGENT-33 call a model?" })).toBeInTheDocument();
    expect(screen.getByText("Add access to scan live status")).toBeInTheDocument();
  });

  it("routes setup actions through the app navigation callback", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    render(
      <UnifiedConnectCenterPanel token="" apiKey="" onNavigate={onNavigate} onResult={vi.fn()} />
    );

    await user.click(screen.getByRole("button", { name: "Open model setup" }));

    expect(onNavigate).toHaveBeenCalledWith("models");
  });

  it("loads live readiness when credentials exist", async () => {
    const onResult = vi.fn();
    fetchOnboardingStatusMock.mockResolvedValue({
      ok: true,
      status: 200,
      durationMs: 12,
      url: "/v1/operator/onboarding",
      data: {
        completed_count: 2,
        total_count: 3,
        overall_complete: false,
        steps: [
          {
            step_id: "OB-01",
            category: "runtime",
            title: "Database",
            description: "Runtime database",
            completed: true,
            remediation: ""
          },
          {
            step_id: "OB-02",
            category: "models",
            title: "Model",
            description: "Model provider",
            completed: true,
            remediation: ""
          },
          {
            step_id: "OB-08",
            category: "api",
            title: "API",
            description: "API protection",
            completed: false,
            remediation: "Review API safety."
          }
        ]
      }
    });

    render(<UnifiedConnectCenterPanel token="token" apiKey="" onNavigate={vi.fn()} onResult={onResult} />);

    expect(await screen.findByText("3 of 4 known checks ready")).toBeInTheDocument();
    expect(fetchOnboardingStatusMock).toHaveBeenCalledWith("token", "");
    expect(onResult).toHaveBeenCalledWith(
      "Connect Center - Readiness",
      expect.objectContaining({ ok: true, status: 200 })
    );
  });

  it("surfaces invalid readiness data separately from failed requests", async () => {
    fetchOnboardingStatusMock.mockResolvedValue({
      ok: true,
      status: 200,
      durationMs: 12,
      url: "/v1/operator/onboarding",
      data: { invalid: true }
    });

    render(<UnifiedConnectCenterPanel token="token" apiKey="" onNavigate={vi.fn()} onResult={vi.fn()} />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Received invalid readiness data.");
  });
});
